# CNPJ Data Pipeline

ETL para ingestão de dados de empresas brasileiras da Receita Federal em PostgreSQL.

## Objetivo

Este projeto faz parte de uma **plataforma de Inteligência Comercial B2B** para competir com Speedio, Econodata e Leads2b. O pipeline é responsável por:

1. Download dos dados abertos da Receita Federal (~7GB/mês compactados) via WebDAV
2. Processamento e transformação com Polars
3. Carga em PostgreSQL com estratégia de UPSERT
4. Base para enriquecimentos futuros (validação de contatos, decisores, tecnologias)

## Stack

- **Python 3.11+** com Polars (10-100x mais rápido que Pandas)
- **PostgreSQL 17** (banco principal)
- **Elasticsearch 8.x** (busca full-text - a implementar)
- **Redis 7.x** (cache - a implementar)

## Estrutura do Projeto

```
cnpj-data-pipeline/
├── main.py              # Orquestrador principal
├── downloader.py        # Download e extração de ZIPs da RFB
├── processor.py         # Processamento de CSVs com Polars
├── database.py          # Operações PostgreSQL (COPY + UPSERT)
├── config.py            # Configurações via env vars
├── initial.sql          # Schema do banco
├── docs/                # Documentação de melhorias planejadas
│   ├── 00_ROADMAP.md
│   ├── 01_OTIMIZACOES_PERFORMANCE.md
│   ├── 02_SCHEMA_NORMALIZADO.md
│   ├── 03_INDICES_B2B.md
│   ├── 04_ELASTICSEARCH_INTEGRATION.md
│   ├── 05_CNPJ_ALFANUMERICO_2026.md
│   └── 06_QUALIDADE_DADOS.md
└── tests/               # Testes pytest
```

## Fluxo de Execução

```
1. main.py recebe argumentos (--list, --month, --force)
2. Downloader busca meses disponíveis na RFB
3. Database verifica arquivos já processados (idempotência)
4. Download em paralelo (4 workers) com retry
5. Processamento em batches (500k linhas) com Polars
6. UPSERT via COPY + UNLOGGED staging table + ON CONFLICT
7. Marca arquivo como processado
```

## Ordem de Processamento (FK Dependencies)

```python
PROCESSING_ORDER = [
    "CNAECSV",      # 1. Tabelas de referência (lookup)
    "MOTICSV",
    "MUNICCSV",
    "NATJUCSV",
    "PAISCSV",
    "QUALSCSV",
    "EMPRECSV",     # 2. Empresas (raiz CNPJ 8 dígitos)
    "ESTABELE",     # 3. Estabelecimentos (CNPJ 14 dígitos)
    "SOCIOCSV",     # 4. Sócios
    "SIMPLESCSV",   # 5. Simples Nacional / MEI
]
```

## Arquivos Principais

### main.py (146 linhas)
- `main()` - Orquestra pipeline completo
- `parse_args()` - CLI arguments
- `get_file_priority()` - Ordenação por dependências FK

### downloader.py (~220 linhas)
- `_propfind()` - WebDAV PROPFIND no Nextcloud da RFB (substituiu scraping HTML)
- `get_available_directories()` - Lista meses via WebDAV XML parsing
- `get_directory_files()` - Lista ZIPs de um mês via WebDAV
- `download_files()` - Download paralelo com ThreadPoolExecutor (auth por share token)
- `_download_and_extract()` - Download com retry + extração ZIP

### processor.py (209 linhas)
- `get_file_type()` - Identifica tipo pelo nome do arquivo
- `process_file()` - Lê CSV em batches, aplica transformações
- `_convert_encoding()` - ISO-8859-1 → UTF-8
- `_transform()` - Transformações específicas (datas, capital social)

### database.py (167 linhas)
- `connect()` - Conexão com retry exponencial
- `bulk_upsert()` - COPY + temp table + INSERT...ON CONFLICT
- `get_processed_files()` - Rastreamento de progresso
- `mark_processed()` - Marca arquivo como concluído

## Schema do Banco

### Tabelas de Lookup
- `cnaes` - Classificação de atividades
- `motivos` - Motivos de situação cadastral
- `municipios` - Municípios brasileiros
- `naturezas_juridicas` - Tipos de empresa
- `paises` - Países
- `qualificacoes_socios` - Papéis de sócios

### Tabelas Principais
- `empresas` - Dados raiz (CNPJ 8 dígitos) - ~47M registros
- `estabelecimentos` - Matriz/filiais (CNPJ 14 dígitos) - ~51M registros
- `socios` - Quadro societário - ~22M registros
- `dados_simples` - Simples Nacional / MEI - ~30M registros
- `processed_files` - Rastreamento de arquivos processados

## Configuração

```bash
# .env
DATABASE_URL=postgres://user:pass@localhost:5432/cnpj
BATCH_SIZE=500000
TEMP_DIR=./temp
DOWNLOAD_WORKERS=4
RETRY_ATTEMPTS=3
KEEP_DOWNLOADED_FILES=false
```

## Comandos

```bash
# Listar meses disponíveis
uv run python main.py --list

# Processar mês mais recente
uv run python main.py

# Processar mês específico
uv run python main.py --month 2024-11

# Forçar reprocessamento
uv run python main.py --month 2024-11 --force

# Via justfile
just run
just run --list
just run --month 2024-11
```

## Transformações de Dados

| Tipo | Transformação |
|------|---------------|
| Capital social | "1.234,56" → "1234.56" |
| Datas nulas | "0", "00000000" → NULL |
| País | "3" → "003" (zfill) |
| CNPJ sócio | NULL → "00000000000000" |
| Encoding | ISO-8859-1 → UTF-8 |

## Melhorias Planejadas (docs/)

1. **Performance** - UNLOGGED staging tables, deferred indexes, streaming ZIP
2. **Schema** - Campos de descrição desnormalizados, regime tributário
3. **Índices B2B** - Compostos, parciais, GIN para texto
4. **Elasticsearch** - PGSync CDC + bulk load híbrido
5. **Qualidade** - Validações, integridade referencial
6. **CNPJ 2026** - Suporte a CNPJ alfanumérico (julho/2026)

## Relacionamento com Upstream

Este repositório é um fork de [`caiopizzol/cnpj-data-pipeline`](https://github.com/caiopizzol/cnpj-data-pipeline).

**Ponto de divergência:** commit `29dfeb8` (chore: long lived container).

### Nossas modificações (preservar sempre)

| Arquivo | O que fizemos | Por que |
|---------|--------------|---------|
| `main.py` | `--initial-load`, DROP/CREATE índices, `set_bulk_load_config()`, `raise` em erros | Performance 2-3x melhor que upstream |
| `database.py` | `bulk_insert()`, UNLOGGED staging, StringIO, null byte fix, gerenciamento de índices | Carga em massa otimizada |
| `processor.py` | Leitura ISO-8859-1 nativa (sem conversão UTF-8), batch 500k | -50% I/O, -90% commits |
| `sync_elasticsearch.py` | Arquivo nosso (não existe no upstream) | Sync PG -> ES com alias swap |
| `scripts/enrich/` | Diretório nosso (não existe no upstream) | Scripts de enriquecimento |

### Commits cherry-picked do upstream

| Data | Commit | Descrição |
|------|--------|-----------|
| 2026-02-09 | `b1cd64a` | fix: adjust downloader to new url (WebDAV) |

### Como sincronizar com upstream

```bash
cd /home/akira/cnpj-data-pipeline
git fetch upstream
# Avaliar novos commits:
git log --oneline upstream/main..HEAD   # nossos commits
git log --oneline HEAD..upstream/main   # commits novos do upstream
# Cherry-pick seletivo (NÃO merge/rebase — upstream reverte nossas otimizações):
git cherry-pick <commit-sha>
```

> **NUNCA fazer merge ou rebase do upstream inteiro.** O upstream não tem nossas otimizações
> de performance (`bulk_insert`, UNLOGGED staging, `--initial-load`, DROP índices).
> Fazer merge/rebase reverteria essas mudanças. Usar sempre **cherry-pick seletivo**.

---

## Limitações Conhecidas

- **Memória**: `low_memory=False` no Polars pode consumir muita RAM
- **Sem checkpoint por batch**: Falha em batch N reprocessa arquivo inteiro
- **Share token frágil**: Se a RFB mudar o token Nextcloud, o download quebra (verificar mirror Casa dos Dados)
- **Processamento sequencial**: Download paralelo, mas processamento é serial

## Contexto da Plataforma B2B

Este ETL alimenta uma plataforma que terá:

- **22M empresas ativas** indexadas
- **Filtros avançados**: CNAE, UF, porte, situação, sócios
- **Enriquecimentos**: emails validados, telefones, WhatsApp, decisores
- **Busca full-text**: Elasticsearch com analyzers para português
- **Intent data**: vagas abertas, sinais de compra

Ver documentação completa em `/home/akira/CLAUDE.md` (projeto global).

## Fonte de Dados

- **Portal gov.br**: https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj
- **Repositório oficial (Nextcloud/SERPRO+)**: https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9
- **Mirror rápido (Casa dos Dados/Cloudflare)**: https://dados-abertos-rf-cnpj.casadosdados.com.br/arquivos/
- **Metadados dos arquivos**: https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf
- **Atualização**: Mensal (~2ª semana do mês)
- **Volume**: ~7 GB compactados (37 ZIPs), ~21 GB descomprimidos, ~60M CNPJs
- **Latência**: 30-45 dias entre alteração na empresa e publicação

### Migração da URL da RFB (Fev/2026)

Em janeiro/2026 a RFB migrou os arquivos de uma listagem de diretório HTTP para um
**compartilhamento Nextcloud (SERPRO+)**. A URL antiga parou de funcionar:

```
ANTES (quebrado): https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/
AGORA (funciona): https://arquivos.receitafederal.gov.br/public.php/webdav/  (via WebDAV)
```

O acesso programático é feito via **WebDAV PROPFIND** com autenticação por share token:
- `base_url`: `https://arquivos.receitafederal.gov.br/public.php/webdav`
- `auth`: `(share_token, "")` onde `share_token = "YggdBLfdninEJX9"`

**Abordagem adotada:** Cherry-pick do commit `b1cd64a` do upstream (`caiopizzol/cnpj-data-pipeline`
v1.3.2) que migra `config.py` e `downloader.py` de scraping HTML para WebDAV. Os demais commits
do upstream (docs, versão, lefthook) foram ignorados por não serem relevantes. Nossas otimizações
de performance em `main.py`, `database.py` e `processor.py` foram preservadas intactas.

> **ATENÇÃO:** A RFB muda a URL dos dados periodicamente sem aviso. Se o download quebrar,
> verificar: (1) se o share token mudou no portal gov.br, (2) se a Casa dos Dados tem mirror atualizado.

---

## Ingestão Realizada (2026-01-22)

### Métricas da Ingestão Final (E2E validado)

| Tabela | Registros |
|--------|-----------|
| empresas | 66.011.325 |
| estabelecimentos | 69.200.268 |
| socios | 26.906.117 |
| dados_simples | 46.506.776 |
| **Total** | **208.624.486** |

- **Arquivos processados:** 37/37 ✅
- **Tamanho do banco:** 37 GB
- **Status:** Ingestão completa sem erros

### Otimizações de Performance Implementadas

| Otimização | Arquivo | Impacto |
|------------|---------|---------|
| Leitura ISO-8859-1 direta (sem conversão para UTF-8) | processor.py | -50% tempo I/O |
| StringIO em vez de BytesIO | database.py | -30% overhead |
| Batch size 500k (era 50k) | config.py | -90% commits |
| DROP índices antes, CREATE depois | main.py | -80% tempo INSERT |
| Flag `--initial-load` (INSERT direto) | main.py | +150% vs UPSERT |

### Bugs Corrigidos Durante Desenvolvimento

| Bug | Causa | Solução |
|-----|-------|---------|
| Chave duplicada em `socios` | PK composta não era única quando CPF nulo | Alterado para `id SERIAL` como PK |
| Byte nulo (0x00) corrompendo COPY | Dados da RFB contêm bytes nulos | `csv_data.replace('\x00', '')` no bulk_insert |
| Erro silencioso continuava execução | `except` só logava erro | Adicionado `raise` para parar execução |
| UPSERT lento na carga inicial | Sempre usava UPSERT | Flag `--initial-load` usa INSERT direto |

### Alterações no Schema

```sql
-- Tabela socios: PK alterada de composta para id SERIAL
-- Antes: PRIMARY KEY (cnpj_basico, identificador_de_socio, cnpj_cpf_do_socio)
-- Depois: PRIMARY KEY (id) com id SERIAL

-- Isso permite inserir todos os registros, mesmo com CPF nulo duplicado
```

### Comandos Disponíveis

```bash
# Carga inicial (tabelas vazias) - RÁPIDO
~/.local/bin/uv run python main.py --initial-load

# Atualização mensal (com dados existentes) - SEGURO
~/.local/bin/uv run python main.py

# Forçar reprocessamento completo
~/.local/bin/uv run python main.py --force --initial-load

# Listar meses disponíveis
~/.local/bin/uv run python main.py --list

# Rodar em background
nohup ~/.local/bin/uv run python main.py --initial-load > ingestao.log 2>&1 &
```

### Estado Atual do Banco

- **Dados:** 208M+ registros do mês 2026-01 ✅
- **Arquivos:** 37/37 processados ✅
- **Índices:** Apenas PKs (índices B2B a criar conforme necessidade)
- **Integridade:** Validada E2E

### Atualização Mensal (fluxo completo)

A RFB publica dados novos ~2ª semana de cada mês. O fluxo completo tem 4 etapas:

```bash
cd /home/akira/cnpj-data-pipeline
source .venv/bin/activate 2>/dev/null || true

# 1. TRUNCATE + ingestão (NUNCA tocar no schema enrich!)
PGPASSWORD=cnpj_pass psql -h localhost -U cnpj_user -d cnpj -c "
TRUNCATE TABLE estabelecimentos, empresas, socios, dados_simples,
               cnaes, motivos, municipios, naturezas_juridicas,
               paises, qualificacoes_socios, processed_files CASCADE;
ALTER SEQUENCE socios_id_seq RESTART WITH 1;"

~/.local/bin/uv run python main.py --initial-load
# ~2-4 horas para 37 arquivos, 208M+ registros

# 2. Pós-ingestão: restaurar mapeamento IBGE nos municípios
cd /home/akira/cnpj-demo
source backend/.venv/bin/activate
python scripts/enrich/mapear_municipios.py
# Restaura codigo_ibge e uf na tabela municipios (perdidos pelo TRUNCATE)

# 3. Sync ES (zero-downtime via alias swap)
cd /home/akira/cnpj-data-pipeline
~/.local/bin/uv run python sync_elasticsearch.py
# Automaticamente: popula pgfn_empresas_mat + cvm_lookup,
# VACUUM ANALYZE, indexa em índice novo, swap alias, deleta antigo.
# ~1-2 horas, API continua servindo durante todo o processo.

# 4. Verificar
curl -sk -u elastic:'=6npk3H78C+OWEfpyd1u' \
  'https://localhost:9200/empresas_b2b/_count' | python3 -m json.tool
```

> **ATENÇÃO:** O TRUNCATE apaga dados do schema `public` mas NUNCA do schema `enrich` (IBGE, PGFN, CVM).
> O step 2 (mapear_municipios) é OBRIGATÓRIO — sem ele, o sync ES não tem coordenadas nem população.

> **ATENÇÃO:** O `sync_elasticsearch.py` usa alias swap. Na primeira execução após a migração,
> ele detecta que `empresas_b2b` é um índice (não alias) e faz a migração automaticamente.

### Índices B2B Criados (2026-01-22)

| Índice | Tabela | Tamanho | Uso |
|--------|--------|---------|-----|
| idx_estab_ativas_uf_cnae | estabelecimentos | 189 MB | UF + CNAE (ativas) |
| idx_estab_ativas_uf | estabelecimentos | 184 MB | Filtro por UF (ativas) |
| idx_estab_ativas_cnae_uf | estabelecimentos | 189 MB | CNAE + UF (ativas) |
| idx_estab_cnae_prefix | estabelecimentos | 184 MB | Prefixo CNAE (LIKE) |
| idx_estab_cnpj_basico | estabelecimentos | 2.0 GB | JOINs com empresas |
| idx_empresas_porte | empresas | 436 MB | Filtro por porte |
| idx_empresas_capital | empresas | 1.0 GB | Filtro por capital |
| idx_socios_nome_trgm | socios | 1.0 GB | Busca fuzzy por nome (GIN) |
| idx_simples_mei | dados_simples | 487 MB | Filtro MEI |

**Total de índices: ~14 GB** (extensão pg_trgm habilitada)

**Dica de performance:** Usar range ao invés de LIKE para CNAE:
```sql
-- ❌ Lento: WHERE cnae_fiscal_principal LIKE '62%'
-- ✅ Rápido: WHERE cnae_fiscal_principal >= '6200000' AND cnae_fiscal_principal < '6300000'
```

---

## Tabelas Auxiliares - Fontes Externas (2026-01-22)

### Problema Identificado

As tabelas de lookup da RFB vieram com descrições incompletas:

| Tabela | Total | Com Descrição | Cobertura |
|--------|-------|---------------|-----------|
| cnaes | 1.359 | 145 | 11% ❌ |
| municipios | 5.572 | 5.572 | 100% ✅ |
| naturezas_juridicas | 91 | 21 | 23% ❌ |
| paises | 255 | 244 | 96% ✅ |
| qualificacoes_socios | 68 | 23 | 34% ❌ |
| motivos | 63 | 63 | 100% ✅ |

### Tabelas Baixadas de Fontes Oficiais

Arquivos salvos em `/home/akira/cnpj-data-pipeline/tabelas_auxiliares/`:

| Arquivo | Registros | Fonte | Confiabilidade |
|---------|-----------|-------|----------------|
| `cnae_ibge.csv` | 1.329 | [IBGE/CONCLA](https://concla.ibge.gov.br/classificacoes/download-concla.html) | ⭐⭐⭐⭐⭐ Oficial |
| `natureza_juridica_ibge.csv` | 89 | [IBGE/CONCLA](https://concla.ibge.gov.br/estrutura/natjur-estrutura/natureza-juridica-2018) | ⭐⭐⭐⭐⭐ Oficial |
| `qualificacao_socio.csv` | 46 | [SERPRO/RFB API](http://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-cnpj/pt/tipos_qualificacao_socio/) | ⭐⭐⭐⭐⭐ Oficial |

### Cobertura Final (2026-01-22) ✅

| Tabela | Cobertura Real* |
|--------|-----------------|
| CNAEs | **99.3%** |
| Municípios | **100%** |
| Naturezas Jurídicas | **97.8%** |
| Qualificações Sócio | **98.0%** |

*Cobertura real = % dos códigos efetivamente usados nas tabelas principais

**Arquivos fonte:** `tabelas_auxiliares/README.md`

---

## Decisões de Arquitetura

### Colunas `*_descricao` nas Tabelas Principais

**Decisão:** NÃO usar colunas de descrição desnormalizadas.

**Motivo:**
- Para API Laravel: JOIN com lookup é instantâneo e mais limpo
- Para Elasticsearch: desnormalizar no momento do sync
- Mapeamentos fixos (porte, situação): usar Enum no Laravel

**Alternativa para exports:** Criar Materialized View com JOINs pré-computados.

### Mapeamentos Fixos (usar no Laravel)

```php
// Porte: 00=Não Informado, 01=Micro, 03=EPP, 05=Demais
// Situação: 01=Nula, 02=Ativa, 03=Suspensa, 04=Inapta, 08=Baixada
// Matriz/Filial: 1=Matriz, 2=Filial
// Tipo Sócio: 1=PJ, 2=PF, 3=Estrangeiro
```

---

## Próximos Passos

1. ~~**Explorar dados**~~ ✅ Feito
2. ~~**Definir índices**~~ ✅ Criados (14 GB)
3. ~~**Tabelas auxiliares**~~ ✅ Baixadas e documentadas
4. ~~**Atualizar lookup**~~ ✅ Cobertura 97-100%
5. **Integração Elasticsearch** - Ver `docs/07_ELASTICSEARCH_SETUP.md`
6. **API Laravel** - Pendente
