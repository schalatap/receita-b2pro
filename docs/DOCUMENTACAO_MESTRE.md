# Documentação Mestre - Plataforma Leddo B2B

> **Última atualização:** 2026-01-28
> **Versão:** 1.0.0
> **Status:** Demo funcional + Fontes de enriquecimento validadas

---

## 1. Visão Geral do Projeto

### 1.1 Objetivo

Desenvolver uma **plataforma de inteligência comercial B2B** para competir com Speedio, Econodata e Leads2b. O sistema indexa ~26 milhões de empresas ativas brasileiras com dados da Receita Federal, permitindo filtros avançados por CNAE, UF, porte, situação cadastral, sócios, regime tributário, etc.

### 1.2 Diferenciais Planejados

- Base completa da Receita Federal (66M empresas, 69M estabelecimentos)
- Enriquecimento com fontes públicas gratuitas (IBGE, PGFN, Portal da Transparência)
- Busca full-text com Elasticsearch
- Geocodificação para busca por proximidade
- Interface moderna (design Vercel/Linear)

### 1.3 Nome Comercial

**Leddo B2B** - Inteligência Comercial

---

## 2. Stack Tecnológica

### 2.1 Infraestrutura

| Componente | Tecnologia | Versão | Status |
|------------|------------|--------|--------|
| **SO** | Ubuntu | 24.04 | OK |
| **Banco Principal** | PostgreSQL | 17 | OK |
| **Busca Full-text** | Elasticsearch | 8.19 | OK |
| **Cache** | Redis | 7.0 | Instalado |
| **Web Server** | Nginx | 1.24 | Instalado |

### 2.2 Backend

| Componente | Tecnologia | Status |
|------------|------------|--------|
| **ETL Pipeline** | Python 3.11 + Polars | OK |
| **API Demo** | FastAPI | OK |
| **API Produção** | Laravel/PHP (planejado) | Pendente |

### 2.3 Frontend

| Componente | Tecnologia | Status |
|------------|------------|--------|
| **Framework** | React + Vite | OK |
| **Linguagem** | TypeScript | OK |
| **Estilo** | Tailwind CSS v4 | OK |

### 2.4 Credenciais

```
PostgreSQL:
  Host: localhost:5432
  Database: cnpj
  User: cnpj_user
  Password: cnpj_pass

Elasticsearch:
  Host: https://localhost:9200
  User: elastic
  Password: =6npk3H78C+OWEfpyd1u
```

---

## 3. Estado Atual do Sistema

### 3.1 Dados Ingeridos (PostgreSQL)

| Tabela | Registros | Descrição |
|--------|-----------|-----------|
| `empresas` | 66.011.325 | Dados raiz (CNPJ 8 dígitos) |
| `estabelecimentos` | 69.200.268 | Matriz/filiais (CNPJ 14 dígitos) |
| `socios` | 26.906.117 | Quadro societário |
| `dados_simples` | 46.506.776 | Simples Nacional / MEI |
| `cnaes` | 1.359 | Classificação de atividades |
| `municipios` | 5.572 | Municípios brasileiros |
| `naturezas_juridicas` | 91 | Tipos de empresa |
| `qualificacoes_socios` | 68 | Papéis de sócios |
| **TOTAL** | **208.624.486** | - |

**Tamanho do banco:** 37 GB
**Mês de referência:** 2026-01

### 3.2 Índice Elasticsearch

| Índice | Documentos | Tamanho |
|--------|------------|---------|
| `empresas_b2b` | 26.400.000 | ~15 GB |

**Campos indexados:**
- Razão social, nome fantasia (analyzer brazilian, fuzzy)
- CNPJ, CNPJ básico
- CNAE principal e secundários
- Endereço completo (UF, município, bairro, CEP)
- Contatos (telefone, email, flags tem_telefone/tem_email)
- Sócios (nested, nome com analyzer brazilian)
- Simples Nacional (optante_simples, optante_mei)
- Capital social, porte, natureza jurídica
- Situação cadastral, data de abertura

### 3.3 Demo Funcional

**URL:** http://192.168.1.7:5173 (frontend) / http://192.168.1.7:8000 (API)

**Funcionalidades implementadas:**
- Busca por razão social/nome fantasia (fuzzy search)
- Autocomplete de CNAE com contagem de empresas (via Elasticsearch)
- Filtros: UF, Cidade, Bairro (cascata)
- Filtros: tem email, tem telefone
- Seleção múltipla de CNAEs
- Tabela de resultados com paginação
- Modal de detalhes da empresa (3 abas: Info, Contato, Sócios)
- Navegação entre empresas relacionadas (mesmo sócio)
- Botão voltar no histórico de navegação
- Exportação CSV
- Formatação de CNPJ, telefone, CEP, datas, moeda

---

## 4. Arquitetura do Sistema

### 4.1 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FONTES DE DADOS                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Receita Federal    IBGE    PGFN    CVM    Portal Transparência     │
│      (mensal)      (anual) (trim)  (trim)      (diário)             │
└──────────┬──────────┬────────┬───────┬────────────┬─────────────────┘
           │          │        │       │            │
           ▼          ▼        ▼       ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     ETL PIPELINE (Python + Polars)                   │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │
│  │ downloader  │  │  processor  │  │         database            │  │
│  │   .py       │→ │    .py      │→ │           .py               │  │
│  │ (downloads) │  │ (transform) │  │ (COPY + UPSERT PostgreSQL)  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        POSTGRESQL 17                                 │
│                                                                      │
│  ┌──────────────────────┐    ┌──────────────────────────────────┐   │
│  │   SCHEMA: public     │    │      SCHEMA: enrich (futuro)     │   │
│  │   (dados RFB)        │    │      (dados enriquecimento)      │   │
│  │                      │    │                                  │   │
│  │  - empresas          │    │  - ibge_municipios               │   │
│  │  - estabelecimentos  │◄───│  - pgfn_dividas                  │   │
│  │  - socios            │JOIN│  - cvm_faturamento               │   │
│  │  - dados_simples     │    │  - portal_transparencia          │   │
│  │  - cnaes             │    │  - ceis_cnep                     │   │
│  │  - municipios        │    │  - geocodificacao                │   │
│  └──────────────────────┘    └──────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               │ sync_elasticsearch.py
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ELASTICSEARCH 8.19                              │
│                                                                      │
│  Índice: empresas_b2b                                               │
│  - Documento desnormalizado (empresa + estabelecimento + sócios)    │
│  - Campos de enriquecimento inline (população, tem_divida, etc)     │
│  - Analyzers: brazilian (stemming português)                        │
│  - Busca fuzzy, agregações, geo_distance (futuro)                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API (FastAPI)                                │
│                                                                      │
│  Endpoints:                                                         │
│  - GET /search          → Busca com filtros                         │
│  - GET /cnaes           → Autocomplete CNAE (ES aggregations)       │
│  - GET /empresa/{cnpj}  → Detalhes de uma empresa                   │
│  - GET /empresas-por-socio → Empresas de um sócio                   │
│  - GET /municipios/{uf} → Lista municípios                          │
│  - GET /bairros/{uf}/{mun} → Lista bairros                          │
│  - GET /export/csv      → Exportação                                │
│  - GET /stats/total     → Total de empresas                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                           │
│                                                                      │
│  - Interface moderna (design Vercel/Linear)                         │
│  - Busca com autocomplete                                           │
│  - Filtros dinâmicos                                                │
│  - Modal de detalhes com navegação                                  │
│  - Responsivo                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Estratégia de Reingestão Mensal

```
Opção escolhida: TRUNCATE + INSERT com Schema Swap

1. Schema rfb_staging: recebe novos dados
2. DROP índices → INSERT → CREATE índices
3. SWAP schemas (ALTER SCHEMA RENAME) ~100ms downtime
4. Schema enrich: NUNCA é apagado (dados de enriquecimento persistem)
```

---

## 5. Fontes de Enriquecimento

### 5.1 Fontes Validadas e Prontas

| Fonte | Valor | Dados | Status |
|-------|-------|-------|--------|
| **IBGE** | Alto | População, PIB, coordenadas (5.570 municípios) | Amostras baixadas |
| **PGFN** | Alto | Dívida ativa da União (5M+ devedores) | 123k registros baixados |
| **CVM** | Médio | Faturamento real S.A. (764 empresas ativas) | Cadastro completo baixado |
| **Geocodificação** | Alto | Lat/Long via AwesomeAPI (gratuito) | Testado e funcionando |

### 5.2 Fontes que Requerem Cadastro

| Fonte | Valor | Requisito | Dados |
|-------|-------|-----------|-------|
| **Portal Transparência** | Alto | Conta Gov.br (Prata/Ouro) | Fornecedores do governo |
| **CEIS/CNEP** | Médio | Token API (via Gov.br) | Empresas sancionadas |

### 5.3 Fontes Descartadas

| Fonte | Motivo |
|-------|--------|
| **RAIS/CAGED** | Dados identificados por CNPJ são restritos a órgãos públicos |
| **Comex Stat** | Não tem CNPJ (dados agregados por município) |

### 5.4 Tabela de Enriquecimento Planejada

```sql
-- Schema separado para dados de enriquecimento
CREATE SCHEMA enrich;

-- IBGE: dados demográficos por município
CREATE TABLE enrich.ibge_municipios (
    codigo_municipio VARCHAR(7) PRIMARY KEY,
    nome VARCHAR(100),
    uf VARCHAR(2),
    populacao INTEGER,
    pib BIGINT,
    pib_per_capita DECIMAL(12,2),
    area_km2 DECIMAL(10,2),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    capital BOOLEAN,
    ddd VARCHAR(2),
    atualizado_em DATE
);

-- PGFN: empresas com dívida ativa
CREATE TABLE enrich.pgfn_dividas (
    cnpj_basico VARCHAR(8) PRIMARY KEY,
    valor_total DECIMAL(15,2),
    qtd_inscricoes INTEGER,
    tipo_divida VARCHAR(50),  -- FGTS, Previdenciário, Não-Previdenciário
    situacao VARCHAR(50),     -- AJUIZADA, INSCRITA, PROTESTADA, etc
    data_inscricao_mais_antiga DATE,
    atualizado_em DATE
);

-- CVM: faturamento real de S.A.
CREATE TABLE enrich.cvm_faturamento (
    cnpj VARCHAR(14) PRIMARY KEY,
    cd_cvm VARCHAR(10),
    razao_social VARCHAR(200),
    receita_liquida DECIMAL(18,2),
    lucro_liquido DECIMAL(18,2),
    patrimonio_liquido DECIMAL(18,2),
    ano_exercicio INTEGER,
    atualizado_em DATE
);

-- Portal Transparência: fornecedores do governo
CREATE TABLE enrich.fornecedores_governo (
    cnpj_basico VARCHAR(8) PRIMARY KEY,
    valor_total_recebido DECIMAL(18,2),
    qtd_contratos INTEGER,
    orgaos_clientes TEXT[],
    primeiro_contrato DATE,
    ultimo_contrato DATE,
    atualizado_em DATE
);

-- CEIS/CNEP: empresas sancionadas
CREATE TABLE enrich.sancoes (
    cnpj VARCHAR(14) PRIMARY KEY,
    tipo_sancao VARCHAR(10),  -- CEIS, CNEP, CEPIM
    descricao_sancao TEXT,
    orgao_sancionador VARCHAR(200),
    data_inicio DATE,
    data_fim DATE,
    atualizado_em DATE
);

-- Geocodificação: coordenadas por CEP
CREATE TABLE enrich.geocodificacao (
    cep VARCHAR(8) PRIMARY KEY,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    precisao VARCHAR(20),  -- EXATO, CENTROIDE_CEP, CENTROIDE_BAIRRO
    fonte VARCHAR(50),     -- AWESOMEAPI, NOMINATIM, CNEFE
    atualizado_em DATE
);
```

---

## 6. Localização dos Arquivos

### 6.1 Projeto ETL Pipeline

```
/home/akira/cnpj-data-pipeline/
├── main.py                    # Orquestrador principal
├── downloader.py              # Download de arquivos RFB
├── processor.py               # Processamento com Polars
├── database.py                # Operações PostgreSQL
├── sync_elasticsearch.py      # Sync para Elasticsearch
├── config.py                  # Configurações
├── initial.sql                # Schema do banco
├── pyproject.toml             # Dependências (uv)
│
├── docs/
│   ├── DOCUMENTACAO_MESTRE.md # ← ESTE ARQUIVO
│   ├── 00_ROADMAP.md
│   ├── 01_OTIMIZACOES_PERFORMANCE.md
│   ├── 02_SCHEMA_NORMALIZADO.md
│   ├── 03_INDICES_B2B.md
│   ├── 04_ELASTICSEARCH_INTEGRATION.md
│   ├── 05_CNPJ_ALFANUMERICO_2026.md
│   ├── 06_QUALIDADE_DADOS.md
│   ├── 07_ELASTICSEARCH_SETUP.md
│   │
│   └── fontes/                # Documentação de fontes de enriquecimento
│       ├── IBGE.md            # Dados demográficos IBGE
│       ├── PGFN.md            # Dívida ativa
│       ├── CVM.md             # Empresas capital aberto
│       ├── PORTAL_TRANSPARENCIA.md
│       ├── CEIS_CNEP.md       # Empresas sancionadas
│       ├── RAIS_CAGED.md      # (descartado - restrito)
│       ├── GEOCODIFICACAO.md  # APIs de coordenadas
│       │
│       ├── ibge/              # Amostras e validação IBGE
│       │   ├── VALIDACAO.md
│       │   ├── municipios_amostra.csv
│       │   └── *.json
│       │
│       ├── pgfn/              # Amostras PGFN
│       │   ├── VALIDACAO.md
│       │   └── arquivo_lai_FGTS_*.csv
│       │
│       ├── cvm/               # Dados CVM
│       │   ├── VALIDACAO.md
│       │   ├── cad_cia_aberta.csv
│       │   └── dfp_cia_aberta_*.csv
│       │
│       ├── portal_transparencia/
│       │   ├── VALIDACAO.md
│       │   └── *.json
│       │
│       ├── ceis_cnep/
│       │   └── VALIDACAO.md
│       │
│       ├── rais_caged/
│       │   └── VALIDACAO.md
│       │
│       └── geocodificacao/
│           ├── VALIDACAO.md
│           └── exemplo_*.json
│
└── tabelas_auxiliares/        # CNAEs, naturezas jurídicas do IBGE
    ├── cnae_ibge.csv
    ├── natureza_juridica_ibge.csv
    └── README.md
```

### 6.2 Projeto Demo (Frontend + API)

```
/home/akira/cnpj-demo/
├── backend/
│   ├── main.py                # FastAPI app
│   ├── search.py              # Lógica de busca Elasticsearch
│   ├── models.py              # Pydantic models
│   ├── export.py              # Exportação CSV
│   └── .venv/                 # Ambiente virtual (uv)
│
└── frontend/
    ├── src/
    │   ├── App.tsx            # Componente principal
    │   ├── api.ts             # Cliente da API
    │   ├── types.ts           # TypeScript types
    │   └── index.css          # Estilos Tailwind
    ├── index.html
    ├── package.json
    └── vite.config.ts
```

### 6.3 Instruções Globais

```
/home/akira/CLAUDE.md          # Instruções gerais do projeto
/home/akira/cnpj-data-pipeline/CLAUDE.md  # Instruções específicas do ETL
```

---

## 7. Comandos Úteis

### 7.1 Serviços

```bash
# Verificar status
sudo systemctl status postgresql elasticsearch redis nginx

# Logs do Elasticsearch
sudo journalctl -u elasticsearch -f

# Acessar PostgreSQL
PGPASSWORD=cnpj_pass psql -h localhost -U cnpj_user -d cnpj
```

### 7.2 ETL Pipeline

```bash
cd /home/akira/cnpj-data-pipeline

# Listar meses disponíveis na RFB
~/.local/bin/uv run python main.py --list

# Carga inicial (tabelas vazias)
~/.local/bin/uv run python main.py --initial-load

# Atualização mensal
~/.local/bin/uv run python main.py

# Forçar reprocessamento
~/.local/bin/uv run python main.py --force --initial-load
```

### 7.3 Demo

```bash
# Backend
cd /home/akira/cnpj-demo/backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd /home/akira/cnpj-demo/frontend
npm run dev
```

### 7.4 Elasticsearch

```bash
# Testar conexão
curl -s -k -u elastic:'=6npk3H78C+OWEfpyd1u' https://localhost:9200/

# Ver índices
curl -s -k -u elastic:'=6npk3H78C+OWEfpyd1u' https://localhost:9200/_cat/indices?v

# Contar documentos
curl -s -k -u elastic:'=6npk3H78C+OWEfpyd1u' https://localhost:9200/empresas_b2b/_count
```

---

## 8. Próximos Passos (Implementação)

### 8.1 Fase 1: Integrar Fontes Validadas (Prioridade Alta)

| # | Tarefa | Tempo Est. | Dependência |
|---|--------|------------|-------------|
| 1 | Criar schema `enrich` no PostgreSQL | 15 min | - |
| 2 | Integrar IBGE (municípios + coordenadas) | 1h | #1 |
| 3 | Integrar PGFN (dívida ativa) | 1h | #1 |
| 4 | Integrar CVM (faturamento S.A.) | 1h | #1 |
| 5 | Integrar AwesomeAPI (geocodificação em batch) | 2h | #1 |
| 6 | Atualizar sync_elasticsearch.py com enriquecimento | 2h | #2-5 |
| 7 | Adicionar novos filtros na API | 2h | #6 |
| 8 | Adicionar novos filtros no frontend | 2h | #7 |

### 8.2 Fase 2: Fontes com Autenticação (Prioridade Média)

| # | Tarefa | Tempo Est. | Dependência |
|---|--------|------------|-------------|
| 9 | Criar conta Gov.br (nível Prata/Ouro) | 30 min | - |
| 10 | Obter token API Portal Transparência | 30 min | #9 |
| 11 | Integrar fornecedores do governo | 2h | #10 |
| 12 | Integrar CEIS/CNEP (sanções) | 1h | #10 |

### 8.3 Fase 3: Melhorias de UX (Prioridade Baixa)

| # | Tarefa | Tempo Est. |
|---|--------|------------|
| 13 | Busca por proximidade (geo_distance) | 3h |
| 14 | Visualização em mapa | 4h |
| 15 | Dashboard com agregações | 4h |
| 16 | Buscas salvas (persistência) | 2h |

---

## 9. Aprendizados e Decisões Técnicas

### 9.1 Decisões de Arquitetura

1. **Elasticsearch para busca, PostgreSQL para dados**
   - ES é otimizado para full-text search e agregações
   - PG é a fonte de verdade, ES é derivado

2. **Desnormalização no Elasticsearch**
   - Documento contém empresa + estabelecimento + sócios
   - Enriquecimento é inline (não precisa de JOIN em tempo de busca)

3. **Schema separado para enriquecimento**
   - Dados RFB podem ser truncados na reingestão
   - Dados de enriquecimento persistem

4. **Geocodificação por demanda**
   - Não geocodificar 70M endereços de uma vez
   - Usar AwesomeAPI para CEPs únicos (~900k CEPs)

### 9.2 Problemas Resolvidos

| Problema | Solução |
|----------|---------|
| UPSERT lento na carga inicial | Flag `--initial-load` usa INSERT direto |
| Byte nulo (0x00) corrompendo COPY | `csv_data.replace('\x00', '')` |
| Chave duplicada em sócios | PK alterada para `id SERIAL` |
| RAIS/CAGED para número de funcionários | Descartado (dados restritos) |
| BrasilAPI não retorna coordenadas | Usar AwesomeAPI como alternativa |
| Portal Transparência bloqueia downloads | Usar API autenticada |

### 9.3 Fontes Descartadas

| Fonte | Motivo |
|-------|--------|
| RAIS/CAGED | Dados identificados por CNPJ são restritos a órgãos públicos |
| Comex Stat | Dados agregados por município, não por CNPJ |
| Google Maps (em escala) | Custo proibitivo (~R$ 1.7M para 70M endereços) |

---

## 10. Referências

### 10.1 Repositórios

- **ETL Base:** [caiopizzol/cnpj-data-pipeline](https://github.com/caiopizzol/cnpj-data-pipeline)
- **Referência Schema:** [libercapital](https://github.com/libercapital)
- **Referência Performance:** [minha-receita](https://github.com/cuducos/minha-receita)

### 10.2 Dados Oficiais

- **Receita Federal:** https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj
- **IBGE:** https://www.ibge.gov.br/estatisticas/downloads-estatisticas.html
- **PGFN:** https://dadosabertos.pgfn.gov.br/
- **CVM:** https://dados.cvm.gov.br/
- **Portal Transparência:** https://api.portaldatransparencia.gov.br/

### 10.3 APIs Úteis

- **IBGE Localidades:** https://servicodados.ibge.gov.br/api/v1/localidades/municipios
- **AwesomeAPI CEP:** https://cep.awesomeapi.com.br/json/{cep}
- **PNCP (sem auth):** https://pncp.gov.br/api/consulta/v1/contratos

---

## 11. Contato e Git

```
Git User: Akira
Git Email: schalatap@gmail.com
GitHub: github.com/schalatap/receita-b2pro
SSH Key: ~/.ssh/id_ed25519
```

---

## Changelog

| Data | Versão | Descrição |
|------|--------|-----------|
| 2026-01-28 | 1.0.0 | Documentação mestre inicial |
| 2026-01-22 | - | Ingestão completa RFB (208M registros) |
| 2026-01-23 | - | Demo funcional com busca ES |
| 2026-01-28 | - | Validação de 7 fontes de enriquecimento |

---

> **Nota:** Este documento deve ser atualizado após cada sessão de desenvolvimento significativa.
