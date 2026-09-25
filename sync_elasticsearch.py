#!/usr/bin/env python3
"""
Sync PostgreSQL → Elasticsearch.

Otimizações aplicadas:
- Keyset pagination (sem OFFSET lento); o lote é montado antes dos enriquecimentos
- Sócios em batch com ANY()
- Multiprocessing: N workers dividem o keyspace do CNPJ
- Producer/consumer por worker: thread produtora busca no PG enquanto a
  principal envia ao ES (sobrepõe os dois I/Os sem worker extra)
- streaming_bulk com retry/backoff (429 e erros transientes)
- Batch sizes otimizados (20k PG, 3k ES)
- translog.durability=async durante bulk; force_merge ao final

Robustez:
- Worker sai com exit code 1 se qualquer doc falhar após retries
- Swap do alias abortado se um worker falhar ou empresas (_count) < 99,5% do esperado
"""

import logging
import os
import queue
import sys
import time
from datetime import datetime
from collections import defaultdict
from multiprocessing import Process, SimpleQueue, Value
from threading import Thread

import psycopg2
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
import urllib3

# O sync roda como script solto (não importa config.py), mas depende das mesmas
# variáveis do .env que o main.py: credenciais do ES — obrigatórias, sem default
# — e PGOPTIONS, que isenta a sessão de ETL do statement_timeout do papel.
load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('elastic_transport').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgres://cnpj_user:cnpj_pass@localhost:5432/cnpj')
ES_HOST = os.getenv('ES_HOST', 'https://localhost:9200')
ES_USER = os.getenv('ES_USER', 'elastic')
ES_PASS = os.getenv('ES_PASS', '')  # obrigatório — sem default por segurança
INDEX_NAME = 'empresas_b2b'

NUM_WORKERS = int(os.getenv('SYNC_WORKERS', '4'))
# Faixas pequenas numa fila comum: quem termina a sua pega a próxima. Com 4 faixas fixas, o custo
# desigual do keyspace deixava workers ociosos por mais de uma hora (25/09: 76 a 155 min).
NUM_FAIXAS = int(os.getenv('SYNC_FAIXAS', '64'))
LOTE_LENTO_S = 30  # lote de empresas acima disto é logado com o cursor, para achar o plano ruim
BATCH_SIZE = 20000
ES_CHUNK = 3000
PREFETCH_BATCHES = 2   # batches PG enfileirados à frente do envio ao ES
MIN_DOC_RATIO = 0.995  # swap abortado se docs indexados < 99,5% do esperado

PORTE = {'00': 'Não Informado', '01': 'Micro Empresa', '03': 'EPP', '05': 'Demais'}
SITUACAO = {'01': 'Nula', '02': 'Ativa', '03': 'Suspensa', '04': 'Inapta', '08': 'Baixada'}
TIPO_SOCIO = {'1': 'PJ', '2': 'PF', '3': 'Estrangeiro'}


def faixa_capital(v):
    if not v or v <= 0: return 'Não informado'
    if v < 10000: return 'Até 10k'
    if v < 100000: return '10k-100k'
    if v < 1000000: return '100k-1M'
    if v < 10000000: return '1M-10M'
    return 'Acima 10M'


def fmt_date(d):
    if not d: return None
    if isinstance(d, str) and len(d) == 8 and d.isdigit():
        return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    return d.isoformat() if hasattr(d, 'isoformat') else None


QUERY_EMPRESAS = """
WITH pagina AS MATERIALIZED (
    SELECT
        e.cnpj_basico, e.cnpj_ordem, e.cnpj_dv, e.nome_fantasia, e.situacao_cadastral,
        e.data_situacao_cadastral, e.data_inicio_atividade, e.cnae_fiscal_principal,
        e.cnae_fiscal_secundaria, e.tipo_logradouro, e.logradouro, e.numero, e.complemento,
        e.bairro, e.cep, e.municipio, e.uf, e.ddd_1, e.telefone_1, e.ddd_2, e.telefone_2,
        e.correio_eletronico, e.identificador_matriz_filial,
        emp.razao_social, emp.natureza_juridica, emp.porte, emp.capital_social
    FROM estabelecimentos e
    JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
    WHERE (e.situacao_cadastral IN ('02', '03', '04')
       OR (e.situacao_cadastral = '08'
           AND e.data_situacao_cadastral >= CURRENT_DATE - INTERVAL '2 years'))
      AND e.cnpj_basico >= %(inicio)s AND e.cnpj_basico < %(teto)s
      AND (e.cnpj_basico, e.cnpj_ordem, e.cnpj_dv) > (%(last_basico)s, %(last_ordem)s, %(last_dv)s)
    ORDER BY e.cnpj_basico, e.cnpj_ordem, e.cnpj_dv
    LIMIT %(limite)s
)
SELECT
    p.cnpj_basico || p.cnpj_ordem || p.cnpj_dv as cnpj,
    p.cnpj_basico,
    p.razao_social,
    p.nome_fantasia,
    p.situacao_cadastral,
    p.data_situacao_cadastral,
    p.data_inicio_atividade,
    p.cnae_fiscal_principal,
    c.descricao as cnae_descricao,
    LEFT(p.cnae_fiscal_principal, 2) as cnae_divisao,
    p.cnae_fiscal_secundaria,
    p.natureza_juridica,
    nj.descricao as natureza_descricao,
    p.porte,
    p.capital_social,
    p.tipo_logradouro,
    p.logradouro,
    p.numero,
    p.complemento,
    p.bairro,
    p.cep,
    p.municipio,
    COALESCE(ibge.nome, m.descricao) as municipio_nome,
    p.uf,
    CASE WHEN p.ddd_1 IS NOT NULL AND p.telefone_1 IS NOT NULL
         THEN p.ddd_1 || p.telefone_1 END as telefone_1,
    CASE WHEN p.ddd_2 IS NOT NULL AND p.telefone_2 IS NOT NULL
         THEN p.ddd_2 || p.telefone_2 END as telefone_2,
    p.correio_eletronico as email,
    p.identificador_matriz_filial,
    ds.opcao_pelo_simples,
    ds.opcao_pelo_mei,
    ds.data_opcao_pelo_simples,
    ds.data_opcao_pelo_mei,
    -- Dados IBGE
    ibge.populacao as municipio_populacao,
    ibge.regiao_nome as municipio_regiao,
    ibge.mesorregiao_nome as municipio_mesorregiao,
    ibge.microrregiao_nome as municipio_microrregiao,
    ibge.capital as municipio_capital,
    ibge.latitude as municipio_lat,
    ibge.longitude as municipio_lon,
    -- PGFN (Dívida Ativa)
    pgfn.divida_total as pgfn_divida_total,
    pgfn.qtd_inscricoes as pgfn_qtd_inscricoes,
    pgfn.qtd_ajuizadas as pgfn_qtd_ajuizadas,
    -- CVM (Capital Aberto)
    cvm_ind.cnpj_basico IS NOT NULL as cvm_capital_aberto,
    cvm_ind.setor_atividade as cvm_setor,
    cvm_ind.receita_liquida as cvm_receita,
    cvm_ind.lucro_liquido as cvm_lucro
FROM pagina p
LEFT JOIN cnaes c ON p.cnae_fiscal_principal = c.codigo
LEFT JOIN naturezas_juridicas nj ON p.natureza_juridica = nj.codigo
LEFT JOIN municipios m ON p.municipio = m.codigo
LEFT JOIN enrich.ibge_municipios ibge ON ibge.codigo_ibge = m.codigo_ibge
LEFT JOIN dados_simples ds ON ds.cnpj_basico = p.cnpj_basico
LEFT JOIN enrich.pgfn_empresas_mat pgfn ON pgfn.cnpj_basico = p.cnpj_basico
LEFT JOIN enrich.cvm_lookup cvm_ind ON cvm_ind.cnpj_basico = p.cnpj_basico
ORDER BY p.cnpj_basico, p.cnpj_ordem, p.cnpj_dv
"""
# O lote (estabelecimentos + empresa, com LIMIT) é montado ANTES dos enriquecimentos. Com os
# LEFT JOINs no mesmo nível do LIMIT, o planner ou fazia Merge Join lendo dados_simples desde o
# primeiro CNPJ a cada lote (~10 s/lote) ou, com a faixa repetida nos JOINs, subestimava o lote
# e escolhia hash/sort sobre o resto da faixa (lotes de minutos no worker 3, sync de 25/09).
# Os enriquecimentos são 1:1 por cnpj_basico/código, então aplicar o LIMIT antes não muda o
# resultado; o JOIN com empresas fica dentro do lote porque ele exclui linhas (INNER).

QUERY_SOCIOS = """
SELECT s.cnpj_basico, s.nome_socio, s.identificador_de_socio,
       s.qualificacao_do_socio, qs.descricao, s.data_entrada_sociedade
FROM socios s
LEFT JOIN qualificacoes_socios qs ON s.qualificacao_do_socio = qs.codigo
WHERE s.cnpj_basico = ANY(%s)
ORDER BY s.cnpj_basico, s.data_entrada_sociedade DESC, s.socio_id
"""
# socio_id desempata sócios com a mesma data de entrada: fetch_socios guarda só os 10 primeiros,
# e sem desempate o 10º mudava conforme a ordem física da tabela (o CLUSTER expôs isso).


def fetch_socios(conn, cnpjs):
    if not cnpjs:
        return {}
    result = defaultdict(list)
    with conn.cursor() as cur:
        cur.execute(QUERY_SOCIOS, (cnpjs,))
        for row in cur:
            cnpj = row[0]
            if len(result[cnpj]) < 10:
                result[cnpj].append({
                    'nome': row[1],
                    'tipo': TIPO_SOCIO.get(row[2], row[2]),
                    'qualificacao': row[3],
                    'qualificacao_descricao': row[4],
                    'data_entrada': fmt_date(row[5])
                })
    return dict(result)


def transform(row, socios, index_name):
    capital = float(row.capital_social) if row.capital_social else 0

    location = None
    if row.municipio_lat and row.municipio_lon:
        location = {
            'lat': float(row.municipio_lat),
            'lon': float(row.municipio_lon)
        }

    return {
        '_index': index_name,
        '_id': row.cnpj,
        '_source': {
            'cnpj': row.cnpj,
            'cnpj_basico': row.cnpj_basico,
            'razao_social': row.razao_social,
            'nome_fantasia': row.nome_fantasia,
            'situacao_cadastral': row.situacao_cadastral,
            'situacao_descricao': SITUACAO.get(row.situacao_cadastral),
            'data_situacao': fmt_date(row.data_situacao_cadastral),
            'data_inicio_atividade': fmt_date(row.data_inicio_atividade),
            'cnae_principal': row.cnae_fiscal_principal,
            'cnae_descricao': row.cnae_descricao,
            'cnae_divisao': row.cnae_divisao,
            'cnaes_secundarios': row.cnae_fiscal_secundaria.split(',') if row.cnae_fiscal_secundaria else [],
            'natureza_juridica': row.natureza_juridica,
            'natureza_descricao': row.natureza_descricao,
            'porte': row.porte,
            'porte_descricao': PORTE.get(row.porte),
            'capital_social': capital,
            'faixa_capital': faixa_capital(capital),
            'matriz_filial': 'Matriz' if str(row.identificador_matriz_filial) == '1' else 'Filial',
            'endereco': {
                'logradouro': f"{row.tipo_logradouro or ''} {row.logradouro or ''}".strip(),
                'numero': row.numero,
                'complemento': row.complemento,
                'bairro': row.bairro,
                'cep': row.cep,
                'municipio': row.municipio,
                'municipio_nome': row.municipio_nome,
                'uf': row.uf
            },
            'contato': {
                'telefone_1': row.telefone_1,
                'telefone_2': row.telefone_2,
                'email': row.email.lower() if row.email else None,
                'tem_email': bool(row.email),
                'tem_telefone': bool(row.telefone_1)
            },
            'simples': {
                'optante_simples': row.opcao_pelo_simples,
                'optante_mei': row.opcao_pelo_mei,
                'data_opcao_simples': fmt_date(row.data_opcao_pelo_simples),
                'data_opcao_mei': fmt_date(row.data_opcao_pelo_mei)
            },
            'socios': socios,
            'qtd_socios': len(socios),
            'municipio_populacao': row.municipio_populacao,
            'municipio_regiao': row.municipio_regiao,
            'municipio_mesorregiao': row.municipio_mesorregiao,
            'municipio_microrregiao': row.municipio_microrregiao,
            'municipio_capital': row.municipio_capital or False,
            'location': location,
            'tem_divida_ativa': bool(row.pgfn_divida_total and float(row.pgfn_divida_total) > 0),
            'divida_total': float(row.pgfn_divida_total) if row.pgfn_divida_total else None,
            'qtd_inscricoes_pgfn': row.pgfn_qtd_inscricoes or 0,
            'qtd_ajuizadas_pgfn': row.pgfn_qtd_ajuizadas or 0,
            'empresa_capital_aberto': bool(row.cvm_capital_aberto),
            'setor_cvm': row.cvm_setor,
            'receita_liquida': float(row.cvm_receita) if row.cvm_receita else None,
            'lucro_liquido': float(row.cvm_lucro) if row.cvm_lucro else None,
        }
    }


def produce_range(conn, range_start, range_end, out_queue, tempos):
    """Busca uma faixa em batches no PG (empresas + sócios) e enfileira cada batch."""
    last_basico, last_ordem, last_dv = '', '', ''
    while True:
        params = {
            'inicio': range_start, 'teto': range_end,
            'last_basico': last_basico, 'last_ordem': last_ordem, 'last_dv': last_dv,
            'limite': BATCH_SIZE,
        }
        t0 = time.monotonic()
        with conn.cursor(cursor_factory=NamedTupleCursor) as cur:
            cur.execute(QUERY_EMPRESAS, params)
            rows = cur.fetchall()
        duracao = time.monotonic() - t0
        tempos['pg_empresas'] += duracao
        if duracao > LOTE_LENTO_S:
            logger.warning(
                f"Lote lento: {duracao:.0f} s, faixa [{range_start}, {range_end}), "
                f"cursor ({last_basico}, {last_ordem}, {last_dv})"
            )

        if not rows:
            return

        t0 = time.monotonic()
        cnpjs_basicos = list({r.cnpj_basico for r in rows})
        socios_map = fetch_socios(conn, cnpjs_basicos)
        tempos['pg_socios'] += time.monotonic() - t0

        t0 = time.monotonic()
        out_queue.put((rows, socios_map))
        tempos['fila_cheia'] += time.monotonic() - t0

        last_row = rows[-1]
        last_basico = last_row.cnpj_basico
        last_ordem = last_row.cnpj[8:12]
        last_dv = last_row.cnpj[12:14]


def batch_producer(conn, faixas, out_queue, tempos):
    """Thread produtora: consome faixas da fila comum até a sentinela e enfileira os batches.

    Todo acesso psycopg2 acontece aqui — a conexão nunca cruza threads.
    Sentinela: None = fim do trabalho; Exception = falha a propagar no consumidor.
    """
    try:
        for range_start, range_end in iter(faixas.get, None):
            produce_range(conn, range_start, range_end, out_queue, tempos)
            tempos['faixas'] += 1
        out_queue.put(None)
    except Exception as exc:
        out_queue.put(exc)


def generate_docs(batch_queue, index_name, counter, tempos):
    """Consome batches da fila e gera documentos ES (prefetch: PG e ES sobrepostos)."""
    while True:
        t0 = time.monotonic()
        item = batch_queue.get()
        tempos['espera_pg'] += time.monotonic() - t0
        if item is None:
            return
        if isinstance(item, Exception):
            raise item

        rows, socios_map = item
        t0 = time.monotonic()
        docs = [transform(row, socios_map.get(row.cnpj_basico, []), index_name) for row in rows]
        tempos['transformacao'] += time.monotonic() - t0
        yield from docs

        with counter.get_lock():
            counter.value += len(rows)


def worker_process(worker_id, faixas, index_name, counter):
    """Worker: indexa faixas da fila comum até esvaziá-la. Sai com código 1 se perder docs."""

    conn = psycopg2.connect(DATABASE_URL)
    conn.set_session(readonly=True)
    es = Elasticsearch(ES_HOST, basic_auth=(ES_USER, ES_PASS), verify_certs=False)

    # Produtora (PG) e consumidora (transformação + envio ao ES) rodam sobrepostas:
    # - pg_empresas/pg_socios: tempo da produtora no PG; fila_cheia: produtora parada porque a
    #   consumidora está atrás (alto = o lado do ES limita).
    # - espera_pg: consumidora parada sem batch (alto = o PG limita); transformacao: montar docs;
    #   envio_es (derivado): o resto da consumidora — serialização, bulk HTTP e resposta do ES.
    tempos = {'faixas': 0, 'pg_empresas': 0.0, 'pg_socios': 0.0, 'fila_cheia': 0.0,
              'espera_pg': 0.0, 'transformacao': 0.0}
    inicio = time.monotonic()

    batch_queue = queue.Queue(maxsize=PREFETCH_BATCHES)
    producer = Thread(
        target=batch_producer,
        args=(conn, faixas, batch_queue, tempos),
        daemon=True,
    )
    producer.start()

    success, failed = 0, 0
    for ok, result in streaming_bulk(
        es, generate_docs(batch_queue, index_name, counter, tempos),
        chunk_size=ES_CHUNK,
        max_retries=8,
        initial_backoff=2,
        max_backoff=60,
        raise_on_error=False,
        raise_on_exception=False,
    ):
        if ok:
            success += 1
        else:
            failed += 1
            if failed <= 3:
                logger.warning(f"Worker {worker_id} erro: {result}")

    producer.join()
    conn.close()
    logger.info(f"Worker {worker_id}: {success:,} OK, {failed:,} erros")
    total = time.monotonic() - inicio
    envio_es = total - tempos['espera_pg'] - tempos['transformacao']
    logger.info(
        f"Worker {worker_id} tempos (s): total {total:.0f} · envio_es {envio_es:.0f} · "
        + " · ".join(f"{nome} {valor:.0f}" for nome, valor in tempos.items())
    )

    if failed:
        # Perda definitiva após retries — o processo pai aborta o swap do alias.
        sys.exit(1)


def compute_ranges(num_ranges):
    """Divide o keyspace em faixas de tamanho igual pelos percentis reais do banco."""
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as cur:
        fractions = [i / num_ranges for i in range(1, num_ranges)]
        percentiles = ', '.join(str(f) for f in fractions)
        cur.execute(f"""
            SELECT percentile_disc(ARRAY[{percentiles}]) WITHIN GROUP (ORDER BY cnpj_basico)
            FROM estabelecimentos
            WHERE (situacao_cadastral IN ('02', '03', '04')
               OR (situacao_cadastral = '08'
                   AND data_situacao_cadastral >= CURRENT_DATE - INTERVAL '2 years'))
        """)
        boundaries = cur.fetchone()[0]  # lista de cnpj_basico nos percentis
    conn.close()

    ranges = []
    starts = ['00000000'] + list(boundaries)
    ends = list(boundaries) + ['A']  # 'A' > '99999999' em collation locale-aware
    for s, e in zip(starts, ends):
        ranges.append((s, e))

    logger.info(f"{len(ranges)} faixas: {ranges[0]} … {ranges[-1]}")
    return ranges


def create_index(es, index_name=INDEX_NAME):
    mapping = {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 0,
            "refresh_interval": "-1",
            "index.codec": "best_compression",
            "index.translog.durability": "async",
            "index.translog.flush_threshold_size": "1gb",
            "analysis": {
                "analyzer": {
                    "brazilian": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "brazilian_stemmer", "asciifolding"]
                    }
                },
                "filter": {
                    "brazilian_stemmer": {"type": "stemmer", "language": "brazilian"}
                }
            }
        },
        "mappings": {
            "properties": {
                "cnpj": {"type": "keyword"},
                "cnpj_basico": {"type": "keyword"},
                "razao_social": {"type": "text", "analyzer": "brazilian", "fields": {"keyword": {"type": "keyword"}}},
                "nome_fantasia": {"type": "text", "analyzer": "brazilian", "fields": {"keyword": {"type": "keyword"}}},
                "situacao_cadastral": {"type": "keyword"},
                "situacao_descricao": {"type": "keyword"},
                "data_situacao": {"type": "date", "format": "yyyy-MM-dd"},
                "data_inicio_atividade": {"type": "date", "format": "yyyy-MM-dd"},
                "cnae_principal": {"type": "keyword"},
                "cnae_descricao": {"type": "text", "analyzer": "brazilian", "fields": {"keyword": {"type": "keyword"}}},
                "cnae_divisao": {"type": "keyword"},
                "cnaes_secundarios": {"type": "keyword"},
                "natureza_juridica": {"type": "keyword"},
                "natureza_descricao": {"type": "keyword"},
                "porte": {"type": "keyword"},
                "porte_descricao": {"type": "keyword"},
                "capital_social": {"type": "double"},
                "faixa_capital": {"type": "keyword"},
                "matriz_filial": {"type": "keyword"},
                "endereco": {
                    "properties": {
                        "logradouro": {"type": "text"},
                        "numero": {"type": "keyword"},
                        "complemento": {"type": "text"},
                        "bairro": {"type": "text"},
                        "cep": {"type": "keyword"},
                        "municipio": {"type": "keyword"},
                        "municipio_nome": {"type": "keyword"},
                        "uf": {"type": "keyword"}
                    }
                },
                "contato": {
                    "properties": {
                        "telefone_1": {"type": "keyword"},
                        "telefone_2": {"type": "keyword"},
                        "email": {"type": "keyword"},
                        "tem_email": {"type": "boolean"},
                        "tem_telefone": {"type": "boolean"}
                    }
                },
                "simples": {
                    "properties": {
                        "optante_simples": {"type": "keyword"},
                        "optante_mei": {"type": "keyword"},
                        "data_opcao_simples": {"type": "date", "format": "yyyy-MM-dd"},
                        "data_opcao_mei": {"type": "date", "format": "yyyy-MM-dd"}
                    }
                },
                "socios": {
                    "type": "nested",
                    "properties": {
                        "nome": {"type": "text", "analyzer": "brazilian", "fields": {"keyword": {"type": "keyword"}}},
                        "tipo": {"type": "keyword"},
                        "qualificacao": {"type": "keyword"},
                        "qualificacao_descricao": {"type": "keyword"},
                        "data_entrada": {"type": "date", "format": "yyyy-MM-dd"}
                    }
                },
                "qtd_socios": {"type": "integer"},
                "municipio_populacao": {"type": "integer"},
                "municipio_regiao": {"type": "keyword"},
                "municipio_mesorregiao": {"type": "keyword"},
                "municipio_microrregiao": {"type": "keyword"},
                "municipio_capital": {"type": "boolean"},
                "location": {"type": "geo_point"},
                "tem_divida_ativa": {"type": "boolean"},
                "divida_total": {"type": "double"},
                "qtd_inscricoes_pgfn": {"type": "integer"},
                "qtd_ajuizadas_pgfn": {"type": "integer"},
                "empresa_capital_aberto": {"type": "boolean"},
                "setor_cvm": {"type": "keyword"},
                "receita_liquida": {"type": "double"},
                "lucro_liquido": {"type": "double"}
            }
        }
    }
    es.indices.create(index=index_name, body=mapping)
    logger.info(f"Índice '{index_name}' criado")


ALIAS_NAME = INDEX_NAME


def prepare_enrich_tables(conn):
    """Popula tabelas materializadas de enriquecimento usadas nos JOINs do sync."""
    logger.info("Populando tabelas de enriquecimento...")
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE enrich.pgfn_empresas_mat")
        cur.execute("""
            INSERT INTO enrich.pgfn_empresas_mat
            SELECT * FROM enrich.pgfn_empresas
        """)
        pgfn_count = cur.rowcount
        conn.commit()
        logger.info(f"  pgfn_empresas_mat: {pgfn_count:,} rows")

        cur.execute("TRUNCATE TABLE enrich.cvm_lookup")
        cur.execute("""
            INSERT INTO enrich.cvm_lookup (cnpj_basico, setor_atividade, receita_liquida, lucro_liquido)
            SELECT
                LEFT(c.cnpj_limpo, 8) AS cnpj_basico,
                c.setor_atividade,
                i.receita_liquida,
                i.lucro_liquido
            FROM enrich.cvm_companhias c
            LEFT JOIN enrich.cvm_indicadores i ON i.codigo_cvm = c.codigo_cvm
                AND i.ano_exercicio = (
                    SELECT MAX(ano_exercicio) FROM enrich.cvm_indicadores ci
                    WHERE ci.codigo_cvm = c.codigo_cvm
                )
        """)
        cvm_count = cur.rowcount
        conn.commit()
        logger.info(f"  cvm_lookup: {cvm_count:,} rows")


def vacuum_analyze(database_url):
    """Executa VACUUM ANALYZE nas tabelas principais (requer autocommit)."""
    logger.info("Executando VACUUM ANALYZE...")
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    tables = ['empresas', 'estabelecimentos', 'socios', 'dados_simples', 'municipios']
    with conn.cursor() as cur:
        for table in tables:
            logger.info(f"  VACUUM ANALYZE {table}...")
            cur.execute(f"VACUUM ANALYZE {table}")
    conn.close()
    logger.info("VACUUM ANALYZE concluído")


def main():
    if not ES_PASS:
        logger.error("ES_PASS não definido — exporte a senha do Elasticsearch antes de rodar")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Sync PostgreSQL → Elasticsearch")
    logger.info(
        f"Workers: {NUM_WORKERS}, Faixas: {NUM_FAIXAS}, Batch PG: {BATCH_SIZE}, "
        f"Chunk ES: {ES_CHUNK}, Prefetch: {PREFETCH_BATCHES}"
    )
    logger.info("=" * 60)

    es = Elasticsearch(ES_HOST, basic_auth=(ES_USER, ES_PASS), verify_certs=False)
    if not es.ping():
        logger.error("Elasticsearch indisponível")
        sys.exit(1)
    logger.info(f"Elasticsearch {es.info()['version']['number']}")

    # 1. Preparar tabelas de enriquecimento
    prep_conn = psycopg2.connect(DATABASE_URL)
    prepare_enrich_tables(prep_conn)
    prep_conn.close()

    # 2. VACUUM ANALYZE para estatísticas atualizadas
    vacuum_analyze(DATABASE_URL)

    # 3. Contar total para progresso
    count_conn = psycopg2.connect(DATABASE_URL)
    with count_conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM estabelecimentos e
            WHERE (e.situacao_cadastral IN ('02', '03', '04')
               OR (e.situacao_cadastral = '08'
                   AND e.data_situacao_cadastral >= CURRENT_DATE - INTERVAL '2 years'))
        """)
        total = cur.fetchone()[0]
    count_conn.close()
    logger.info(f"Total a indexar: {total:,} estabelecimentos")

    # 4. Criar índice temporário
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_index = f"{ALIAS_NAME}_{timestamp}"
    create_index(es, new_index)
    logger.info(f"Índice temporário: {new_index}")

    # 5. Dividir o keyspace em faixas pequenas numa fila comum e spawnar os workers
    ranges = compute_ranges(NUM_FAIXAS)
    faixas = SimpleQueue()
    counter = Value('i', 0)
    start = datetime.now()

    # Workers sobem ANTES de a fila ser alimentada: put() escreve num pipe de capacidade finita
    # e, sem consumidores, bloquearia o pai com muitas faixas (reproduzido com 2.048).
    workers = []
    for i in range(NUM_WORKERS):
        p = Process(target=worker_process, args=(i, faixas, new_index, counter))
        p.start()
        workers.append(p)
    for faixa in ranges:
        faixas.put(faixa)
    for _ in range(NUM_WORKERS):
        faixas.put(None)  # uma sentinela por worker
    logger.info(f"{NUM_WORKERS} workers iniciados")

    # 6. Monitorar progresso
    while any(p.is_alive() for p in workers):
        time.sleep(30)
        current = counter.value
        pct = 100 * current / total if total else 0
        elapsed_s = (datetime.now() - start).total_seconds()
        speed = current / elapsed_s if elapsed_s > 0 else 0
        eta_min = (total - current) / speed / 60 if speed > 0 else 0
        logger.info(f"Progresso: {current:,} / {total:,} ({pct:.1f}%) — {speed:.0f} docs/s — ETA {eta_min:.0f} min")

    for p in workers:
        p.join()

    elapsed = datetime.now() - start
    logger.info(f"Workers concluídos em {elapsed}")

    # 7. Worker com falha (crash ou docs perdidos após retries) → abortar SEM swap.
    #    O alias continua no índice antigo; só o índice parcial novo é descartado.
    failed_workers = [p for p in workers if p.exitcode != 0]
    if failed_workers:
        for p in failed_workers:
            logger.error(f"Worker PID {p.pid} saiu com código {p.exitcode}")
        logger.error("Abortando: alias preservado no índice atual, removendo índice parcial")
        es.indices.delete(index=new_index)
        sys.exit(1)

    # 8. Finalizar índice (refresh + settings de produção)
    es.indices.refresh(index=new_index)
    es.indices.put_settings(index=new_index, body={
        "refresh_interval": "30s",
        "index.translog.durability": "request",
    })

    stats = es.indices.stats(index=new_index)['indices'][new_index]['primaries']
    # _count conta só docs de topo (empresas). _stats.docs.count inclui os sócios nested e
    # inflaria a contagem em ~50%, mascarando empresas ausentes na guarda abaixo.
    doc_count = es.count(index=new_index)['count']

    # 9. Validar contra o total real ANTES do swap (protege contra perda silenciosa)
    min_expected = int(total * MIN_DOC_RATIO)
    if doc_count < min_expected:
        logger.error(
            f"Empresas indexadas ({doc_count:,}) abaixo do mínimo esperado "
            f"({min_expected:,} = {MIN_DOC_RATIO:.1%} de {total:,}) — abortando swap"
        )
        es.indices.delete(index=new_index)
        sys.exit(1)

    # 9b. force_merge: índice fica estático por 1 mês — menos segmentos = busca
    #     mais rápida e menos heap. Roda antes do swap (alias antigo ainda serve).
    logger.info("force_merge (max_num_segments=1) — pode levar dezenas de minutos...")
    merge_start = datetime.now()
    es.options(request_timeout=7200).indices.forcemerge(index=new_index, max_num_segments=1)
    logger.info(f"force_merge concluído em {datetime.now() - merge_start}")

    # 10. Alias swap atômico
    old_indices = []
    if es.indices.exists_alias(name=ALIAS_NAME):
        alias_info = es.indices.get_alias(name=ALIAS_NAME)
        old_indices = list(alias_info.keys())

    actions = [{"add": {"index": new_index, "alias": ALIAS_NAME}}]
    for old_idx in old_indices:
        actions.append({"remove": {"index": old_idx, "alias": ALIAS_NAME}})

    if not es.indices.exists_alias(name=ALIAS_NAME) and es.indices.exists(index=ALIAS_NAME):
        logger.info(f"Migrando de índice direto para alias: deletando índice '{ALIAS_NAME}'")
        old_indices = [ALIAS_NAME]
        es.indices.delete(index=ALIAS_NAME)
        actions = [{"add": {"index": new_index, "alias": ALIAS_NAME}}]

    es.indices.update_aliases(body={"actions": actions})
    logger.info(f"Alias '{ALIAS_NAME}' → '{new_index}'")

    # 11. Limpar índices antigos
    for old_idx in old_indices:
        if old_idx != new_index:
            try:
                es.indices.delete(index=old_idx)
                logger.info(f"Índice antigo '{old_idx}' removido")
            except Exception as e:
                logger.warning(f"Falha ao remover índice antigo '{old_idx}': {e}")

    logger.info("=" * 60)
    logger.info("CONCLUÍDO")
    logger.info(f"Empresas: {doc_count:,} (docs Lucene com sócios: {stats['docs']['count']:,})")
    logger.info(f"Size: {stats['store']['size_in_bytes']/1024/1024/1024:.2f} GB")
    logger.info(f"Time: {elapsed}")
    logger.info(f"Speed: {doc_count/elapsed.total_seconds():.0f} empresas/s")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
