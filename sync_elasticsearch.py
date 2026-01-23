#!/usr/bin/env python3
"""
Sync PostgreSQL → Elasticsearch.

Otimizações aplicadas:
- Keyset pagination (sem OFFSET lento)
- Sócios em batch com ANY()
- Batch sizes otimizados
"""

import logging
import os
import sys
from datetime import datetime
from collections import defaultdict

import psycopg2
from psycopg2.extras import RealDictCursor
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('elastic_transport').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL', 'postgres://cnpj_user:cnpj_pass@localhost:5432/cnpj')
ES_HOST = os.getenv('ES_HOST', 'https://localhost:9200')
ES_USER = os.getenv('ES_USER', 'elastic')
ES_PASS = os.getenv('ES_PASS', '=6npk3H78C+OWEfpyd1u')
INDEX_NAME = 'empresas_b2b'

BATCH_SIZE = 15000
ES_CHUNK = 2500

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
SELECT
    e.cnpj_basico || e.cnpj_ordem || e.cnpj_dv as cnpj,
    e.cnpj_basico,
    emp.razao_social,
    e.nome_fantasia,
    e.situacao_cadastral,
    e.data_situacao_cadastral,
    e.data_inicio_atividade,
    e.cnae_fiscal_principal,
    c.descricao as cnae_descricao,
    LEFT(e.cnae_fiscal_principal, 2) as cnae_divisao,
    e.cnae_fiscal_secundaria,
    emp.natureza_juridica,
    nj.descricao as natureza_descricao,
    emp.porte,
    emp.capital_social,
    e.tipo_logradouro,
    e.logradouro,
    e.numero,
    e.complemento,
    e.bairro,
    e.cep,
    e.municipio,
    m.descricao as municipio_nome,
    e.uf,
    CASE WHEN e.ddd_1 IS NOT NULL AND e.telefone_1 IS NOT NULL
         THEN e.ddd_1 || e.telefone_1 END as telefone_1,
    CASE WHEN e.ddd_2 IS NOT NULL AND e.telefone_2 IS NOT NULL
         THEN e.ddd_2 || e.telefone_2 END as telefone_2,
    e.correio_eletronico as email,
    ds.opcao_pelo_simples,
    ds.opcao_pelo_mei,
    ds.data_opcao_pelo_simples,
    ds.data_opcao_pelo_mei
FROM estabelecimentos e
JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
LEFT JOIN cnaes c ON e.cnae_fiscal_principal = c.codigo
LEFT JOIN naturezas_juridicas nj ON emp.natureza_juridica = nj.codigo
LEFT JOIN municipios m ON e.municipio = m.codigo
LEFT JOIN dados_simples ds ON e.cnpj_basico = ds.cnpj_basico
WHERE e.situacao_cadastral = '02'
  AND e.identificador_matriz_filial = '1'
  AND e.cnpj_basico > %s
ORDER BY e.cnpj_basico
LIMIT %s
"""

QUERY_SOCIOS = """
SELECT s.cnpj_basico, s.nome_socio, s.identificador_de_socio,
       s.qualificacao_do_socio, qs.descricao, s.data_entrada_sociedade
FROM socios s
LEFT JOIN qualificacoes_socios qs ON s.qualificacao_do_socio = qs.codigo
WHERE s.cnpj_basico = ANY(%s)
ORDER BY s.cnpj_basico, s.data_entrada_sociedade DESC
"""


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


def transform(row, socios):
    capital = float(row['capital_social']) if row['capital_social'] else 0
    return {
        '_index': INDEX_NAME,
        '_id': row['cnpj'],
        '_source': {
            'cnpj': row['cnpj'],
            'cnpj_basico': row['cnpj_basico'],
            'razao_social': row['razao_social'],
            'nome_fantasia': row['nome_fantasia'],
            'situacao_cadastral': row['situacao_cadastral'],
            'situacao_descricao': SITUACAO.get(row['situacao_cadastral']),
            'data_situacao': fmt_date(row['data_situacao_cadastral']),
            'data_inicio_atividade': fmt_date(row['data_inicio_atividade']),
            'cnae_principal': row['cnae_fiscal_principal'],
            'cnae_descricao': row['cnae_descricao'],
            'cnae_divisao': row['cnae_divisao'],
            'cnaes_secundarios': row['cnae_fiscal_secundaria'].split(',') if row['cnae_fiscal_secundaria'] else [],
            'natureza_juridica': row['natureza_juridica'],
            'natureza_descricao': row['natureza_descricao'],
            'porte': row['porte'],
            'porte_descricao': PORTE.get(row['porte']),
            'capital_social': capital,
            'faixa_capital': faixa_capital(capital),
            'matriz_filial': 'Matriz',
            'endereco': {
                'logradouro': f"{row['tipo_logradouro'] or ''} {row['logradouro'] or ''}".strip(),
                'numero': row['numero'],
                'complemento': row['complemento'],
                'bairro': row['bairro'],
                'cep': row['cep'],
                'municipio': row['municipio'],
                'municipio_nome': row['municipio_nome'],
                'uf': row['uf']
            },
            'contato': {
                'telefone_1': row['telefone_1'],
                'telefone_2': row['telefone_2'],
                'email': row['email'].lower() if row['email'] else None,
                'tem_email': bool(row['email']),
                'tem_telefone': bool(row['telefone_1'])
            },
            'simples': {
                'optante_simples': row['opcao_pelo_simples'],
                'optante_mei': row['opcao_pelo_mei'],
                'data_opcao_simples': fmt_date(row['data_opcao_pelo_simples']),
                'data_opcao_mei': fmt_date(row['data_opcao_pelo_mei'])
            },
            'socios': socios,
            'qtd_socios': len(socios),
        }
    }


def generate_docs(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM estabelecimentos
            WHERE situacao_cadastral = '02' AND identificador_matriz_filial = '1'
        """)
        total = cur.fetchone()[0]

    logger.info(f"Total: {total:,} empresas")

    last_cnpj = ''
    processed = 0

    while True:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(QUERY_EMPRESAS, (last_cnpj, BATCH_SIZE))
            rows = cur.fetchall()

        if not rows:
            break

        cnpjs = [r['cnpj_basico'] for r in rows]
        socios_map = fetch_socios(conn, cnpjs)

        for row in rows:
            socios = socios_map.get(row['cnpj_basico'], [])
            yield transform(row, socios)
            processed += 1

        last_cnpj = rows[-1]['cnpj_basico']

        if processed % 100000 == 0:
            pct = 100 * processed / total
            logger.info(f"Processados: {processed:,} / {total:,} ({pct:.1f}%)")

    logger.info(f"Total: {processed:,}")


def create_index(es):
    mapping = {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 0,
            "refresh_interval": "-1",
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
                "qtd_socios": {"type": "integer"}
            }
        }
    }
    es.indices.create(index=INDEX_NAME, body=mapping)
    logger.info(f"Índice '{INDEX_NAME}' criado")


def main():
    logger.info("=" * 60)
    logger.info("Sync PostgreSQL → Elasticsearch")
    logger.info("=" * 60)

    es = Elasticsearch(ES_HOST, basic_auth=(ES_USER, ES_PASS), verify_certs=False)
    if not es.ping():
        logger.error("Elasticsearch indisponível")
        sys.exit(1)
    logger.info(f"Elasticsearch {es.info()['version']['number']}")

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
    create_index(es)

    conn = psycopg2.connect(DATABASE_URL)
    conn.set_session(readonly=True)
    logger.info("PostgreSQL conectado")

    logger.info("Indexando...")
    start = datetime.now()
    success, failed = 0, 0

    for ok, result in streaming_bulk(
        es, generate_docs(conn),
        chunk_size=ES_CHUNK,
        raise_on_error=False,
        raise_on_exception=False
    ):
        if ok:
            success += 1
        else:
            failed += 1
            if failed <= 5:
                logger.warning(f"Erro: {result}")

    elapsed = datetime.now() - start

    es.indices.refresh(index=INDEX_NAME)
    es.indices.put_settings(index=INDEX_NAME, body={"refresh_interval": "30s"})

    stats = es.indices.stats(index=INDEX_NAME)['indices'][INDEX_NAME]['primaries']

    logger.info("=" * 60)
    logger.info("CONCLUÍDO")
    logger.info(f"Docs: {stats['docs']['count']:,}")
    logger.info(f"Size: {stats['store']['size_in_bytes']/1024/1024/1024:.2f} GB")
    logger.info(f"Time: {elapsed}")
    logger.info(f"Speed: {success/elapsed.total_seconds():.0f} docs/s")
    if failed:
        logger.warning(f"Failed: {failed:,}")
    logger.info("=" * 60)

    conn.close()


if __name__ == '__main__':
    main()
