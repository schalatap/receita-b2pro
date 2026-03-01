# PGFN - Lista de Devedores da Dívida Ativa da União

## Visão Geral

A **Procuradoria-Geral da Fazenda Nacional (PGFN)** é o órgão responsável pela cobrança da Dívida Ativa da União e do FGTS. A PGFN disponibiliza publicamente dados sobre devedores inscritos em dívida ativa, incluindo pessoas físicas e jurídicas com débitos junto à Fazenda Nacional.

**Valor para Inteligência B2B:** Identificação de empresas com dívidas ativas federais, fundamental para análise de risco de crédito, compliance e due diligence em operações comerciais.

---

## URLs Oficiais

| Recurso | URL | Status |
|---------|-----|--------|
| **Dados Abertos (Download CSV)** | https://www.gov.br/pgfn/pt-br/assuntos/divida-ativa-da-uniao/transparencia-fiscal-1/dados-abertos | OK |
| **Servidor de Arquivos** | https://dadosabertos.pgfn.gov.br/ | OK |
| **Portal dados.gov.br** | https://dados.gov.br/dados/conjuntos-dados/devedores-da-uniao-e-do-fgts1 | OK (requer JS) |
| **Lista de Devedores (Consulta Online)** | https://www.listadevedores.pgfn.gov.br/ | OK |
| **API SERPRO (Paga)** | https://www.gov.br/conecta/catalogo/apis/consulta-divida-ativa-da-uniao | Restrito |
| **Documentação API SERPRO** | https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-divida-ativa/pt/ | OK |

---

## Estrutura dos Dados

### Organização dos Arquivos

Os dados são disponibilizados em **formato CSV dentro de arquivos ZIP**, organizados por:

1. **Trimestre**: Publicação trimestral (ex: `2025_trimestre_04/`)
2. **Sistema de Origem**:
   - **Não Previdenciário** (SIDA) - Dívidas não previdenciárias (~1.1 GB)
   - **Previdenciário** - Dívidas previdenciárias (~89 MB)
   - **FGTS** - Dívidas do Fundo de Garantia (~17 MB)

**Padrão de URL:**
```
https://dadosabertos.pgfn.gov.br/{ANO}_trimestre_{N}/Dados_abertos_{TIPO}.zip
```

### Tipos de Arquivos ZIP

| Arquivo | Descrição | Tamanho Aproximado |
|---------|-----------|-------------------|
| `Dados_abertos_Nao_Previdenciario.zip` | Dívida Ativa Geral | 1.1 GB |
| `Dados_abertos_Previdenciario.zip` | Dívida Previdenciária | 89 MB |
| `Dados_abertos_FGTS.zip` | Dívidas do FGTS | 17 MB |

### Estrutura Interna dos ZIPs

Cada ZIP contém múltiplos CSVs numerados:
```
Dados_abertos_FGTS.zip
├── arquivo_lai_FGTS_1_YYYYMM.csv
├── arquivo_lai_FGTS_2_YYYYMM.csv
├── arquivo_lai_FGTS_3_YYYYMM.csv
├── arquivo_lai_FGTS_4_YYYYMM.csv
├── arquivo_lai_FGTS_5_YYYYMM.csv
├── arquivo_lai_FGTS_6_YYYYMM.csv
└── arquivo_lai_FGTS_NA_YYYYMM.csv
```

**Observação:** Os arquivos NÃO são separados por UF. A divisão é feita por particionamento numérico.

### Colunas por Tipo de Arquivo

#### FGTS (15 colunas)

| Coluna | Descrição | Tipo |
|--------|-----------|------|
| `CPF_CNPJ` | Número do CPF/CNPJ do devedor | VARCHAR |
| `TIPO_PESSOA` | "Pessoa física" ou "Pessoa jurídica" | VARCHAR |
| `TIPO_DEVEDOR` | Principal, Corresponsável ou Solidário | VARCHAR |
| `NOME_DEVEDOR` | Nome/Razão social do devedor | VARCHAR |
| `UF_DEVEDOR` | Unidade federativa do devedor | VARCHAR(2) |
| `UNIDADE_RESPONSAVEL` | Unidade da PGFN responsável | VARCHAR |
| `ENTIDADE_RESPONSAVEL` | Entidade responsável (PGFN) | VARCHAR |
| `UNIDADE_INSCRICAO` | Unidade onde foi inscrito | VARCHAR |
| `NUMERO_INSCRICAO` | Número da inscrição (ex: FGBA201900928) | VARCHAR |
| `TIPO_SITUACAO_INSCRICAO` | Tipo de situação (Em cobrança, Benefício Fiscal, Garantia) | VARCHAR |
| `SITUACAO_INSCRICAO` | Descrição da situação | VARCHAR |
| `RECEITA_PRINCIPAL` | Descrição da receita (Contribuições FGTS) | VARCHAR |
| `DATA_INSCRICAO` | Data de inscrição (DD/MM/YYYY) | VARCHAR |
| `INDICADOR_AJUIZADO` | Se foi ajuizado (SIM/NAO) | VARCHAR |
| `VALOR_CONSOLIDADO` | Valor total consolidado (formato: 1234.56) | VARCHAR |

#### Previdenciário e Não Previdenciário (13 colunas)

| Coluna | Descrição | Tipo |
|--------|-----------|------|
| `CPF_CNPJ` | Número do CPF/CNPJ do devedor | VARCHAR |
| `TIPO_PESSOA` | "Pessoa física" ou "Pessoa jurídica" | VARCHAR |
| `TIPO_DEVEDOR` | Principal, Corresponsável ou Solidário | VARCHAR |
| `NOME_DEVEDOR` | Nome/Razão social do devedor | VARCHAR |
| `UF_DEVEDOR` | Unidade federativa do devedor | VARCHAR(2) |
| `UNIDADE_RESPONSAVEL` | Unidade da PGFN responsável | VARCHAR |
| `NUMERO_INSCRICAO` | Número da inscrição | VARCHAR |
| `TIPO_SITUACAO_INSCRICAO` | Tipo de situação | VARCHAR |
| `SITUACAO_INSCRICAO` | Descrição da situação | VARCHAR |
| `TIPO_CREDITO` | Tipo de crédito (OUTROS, TRIBUTARIO, etc.) | VARCHAR |
| `DATA_INSCRICAO` | Data de inscrição (DD/MM/YYYY) | VARCHAR |
| `INDICADOR_AJUIZADO` | Se foi ajuizado (SIM/NAO) | VARCHAR |
| `VALOR_CONSOLIDADO` | Valor total consolidado | VARCHAR |

### Valores de SITUACAO_INSCRICAO

| Situação | Descrição |
|----------|-----------|
| `AJUIZADA` | Em execução fiscal judicial |
| `AJUIZ PARCELADA` | Ajuizada e em parcelamento |
| `EMBARGADA` | Com embargos à execução |
| `INSCRITA` | Inscrita em dívida ativa (não ajuizada) |
| `INSCR PARCELADA` | Inscrita e em parcelamento |
| `PARCELAMENTO PRÉ-FORMALIZADO` | Em processo de parcelamento |
| `PETICIONADA` | Com petição em andamento |
| `PROTESTADA` | Protestada em cartório |
| `TRANSFERIDA` | Transferida para outra unidade |

### Valores de TIPO_SITUACAO_INSCRICAO

| Tipo | Descrição |
|------|-----------|
| `Em cobrança` | Dívida ativa sendo cobrada (maioria) |
| `Benefício Fiscal` | Com benefício fiscal aplicado |
| `Garantia` | Dívida com garantia apresentada |

### Tipos de Devedor

| Tipo | Descrição |
|------|-----------|
| `Principal` | Devedor originário da dívida |
| `Corresponsável` | Responsável solidário pela dívida |
| `Solidário` | Responsável em conjunto |

> **Importante:** Para calcular o valor total da dívida ativa, considerar apenas devedores do tipo `Principal`, pois a mesma dívida pode estar atribuída a múltiplos devedores.

---

## Como Vincular ao CNPJ

### Formato do CPF/CNPJ nos Dados

| Tipo | Formato | Exemplo |
|------|---------|---------|
| CNPJ | Com pontuação | `10.496.760/0001-95` |
| CPF | Mascarado (LGPD) | `***.123.456-**` |

### Vinculação Direta

O campo `CPF_CNPJ` contém o número completo do CNPJ (14 dígitos + pontuação) para pessoas jurídicas:

```sql
-- JOIN direto com tabela de estabelecimentos
-- Nota: Remover pontuação do CPF_CNPJ antes do JOIN
SELECT
    e.cnpj,
    e.razao_social,
    p.valor_consolidado::decimal,
    p.situacao_inscricao,
    p.data_inscricao
FROM estabelecimentos e
INNER JOIN pgfn_devedores p ON REPLACE(REPLACE(REPLACE(p.cpf_cnpj, '.', ''), '/', ''), '-', '') = e.cnpj
WHERE p.tipo_pessoa = 'Pessoa jurídica'
  AND p.tipo_devedor = 'Principal';
```

### Vinculação por CNPJ Base

Para análise consolidada por empresa (matriz + filiais):

```sql
-- Agregar dívidas por CNPJ base (8 primeiros dígitos)
SELECT
    SUBSTRING(REPLACE(REPLACE(REPLACE(cpf_cnpj, '.', ''), '/', ''), '-', ''), 1, 8) AS cnpj_basico,
    COUNT(*) AS total_inscricoes,
    SUM(valor_consolidado::decimal) AS divida_total,
    MIN(TO_DATE(data_inscricao, 'DD/MM/YYYY')) AS inscricao_mais_antiga
FROM pgfn_devedores
WHERE tipo_pessoa = 'Pessoa jurídica'
  AND tipo_devedor = 'Principal'
  AND situacao_inscricao IN ('AJUIZADA', 'INSCRITA', 'PROTESTADA')
GROUP BY SUBSTRING(REPLACE(REPLACE(REPLACE(cpf_cnpj, '.', ''), '/', ''), '-', ''), 1, 8);
```

### Observações sobre CPF

- CPFs de pessoas físicas são **parcialmente mascarados** (3 primeiros dígitos e 2 dígitos verificadores ocultos)
- Formato: `***.123.456-**` (apenas dígitos centrais visíveis)
- Isso atende à LGPD (Lei nº 13.709/2018)

---

## Frequência de Atualização

| Aspecto | Detalhe |
|---------|---------|
| **Periodicidade** | Trimestral |
| **Disponibilização** | Até 45 dias após o fechamento do trimestre |
| **Histórico Disponível** | Desde 2020 |
| **Trimestres** | Q1 (jan-mar), Q2 (abr-jun), Q3 (jul-set), Q4 (out-dez) |

### Calendário de Publicação (Estimado)

| Trimestre | Dados de | Publicação Estimada |
|-----------|----------|---------------------|
| Q1 | Janeiro - Março | Maio |
| Q2 | Abril - Junho | Agosto |
| Q3 | Julho - Setembro | Novembro |
| Q4 | Outubro - Dezembro | Fevereiro (ano seguinte) |

### Trimestres Disponíveis (Janeiro 2026)

- 2020: Q1, Q2, Q3, Q4
- 2021: Q1, Q2, Q3, Q4
- 2022: Q1, Q2, Q3, Q4
- 2023: Q1, Q2, Q3, Q4
- 2024: Q1, Q2, Q3, Q4
- 2025: Q1, Q2, Q3, Q4

---

## Valor para Inteligência B2B

### Indicadores de Risco

| Indicador | Uso | Score de Risco |
|-----------|-----|----------------|
| **Presença na lista** | Empresa tem dívida ativa federal | Alto |
| **Valor consolidado** | Magnitude do passivo tributário | Proporcional |
| **Quantidade de inscrições** | Reincidência em inadimplência | Cumulativo |
| **Situação "AJUIZADA"** | Execução fiscal em andamento | Crítico |
| **Situação "PROTESTADA"** | Protestada em cartório | Alto |
| **Tempo de inscrição** | Dívida antiga não regularizada | Alto |
| **Tipo de crédito** | Tributário vs. Não tributário | Contextual |

### Aplicações Práticas

1. **Análise de Crédito B2B**
   - Verificar se fornecedor/cliente tem passivo tributário federal
   - Dimensionar risco de inadimplência

2. **Due Diligence (M&A)**
   - Identificar passivos ocultos em fusões e aquisições
   - Avaliar contingências tributárias

3. **Compliance e Cadastro de Fornecedores**
   - Validar regularidade fiscal de parceiros comerciais
   - Monitoramento contínuo de carteira

4. **Scoring de Risco Proprietário**
   - Compor score de risco combinando com dados da Receita Federal
   - Cruzar com situação cadastral (ativa/inapta/baixada)

### Exemplo de Score Simplificado

```python
def calcular_score_pgfn(empresa):
    """
    Score de 0 (sem risco) a 100 (risco máximo)
    """
    score = 0

    # Presença na lista
    if empresa['tem_divida_pgfn']:
        score += 30

    # Valor da dívida (faixas)
    if empresa['divida_total'] > 10_000_000:  # > R$ 10M
        score += 30
    elif empresa['divida_total'] > 1_000_000:  # > R$ 1M
        score += 20
    elif empresa['divida_total'] > 100_000:    # > R$ 100k
        score += 10

    # Situação
    if empresa['tem_inscricao_ajuizada']:
        score += 20
    elif empresa['tem_inscricao_protestada']:
        score += 15

    # Antiguidade (dívida > 5 anos)
    if empresa['anos_divida_mais_antiga'] > 5:
        score += 10

    # Quantidade de inscrições
    if empresa['qtd_inscricoes'] > 10:
        score += 10
    elif empresa['qtd_inscricoes'] > 5:
        score += 5

    return min(score, 100)
```

---

## Limitações e Considerações Legais

### Base Legal para Publicação

| Lei/Decreto | Descrição |
|-------------|-----------|
| **Lei nº 12.527/2011** | Lei de Acesso à Informação (LAI) |
| **Decreto nº 8.777/2016** | Política de Dados Abertos do Governo Federal |
| **Acórdão TCU nº 2497/2018** | Determinação de transparência da dívida ativa |
| **Portaria PGFN nº 636/2020** | Regulamenta divulgação de informações |
| **Lei nº 13.709/2018** | LGPD - Lei Geral de Proteção de Dados |

### Uso Permitido

- **Dados de PJ:** CNPJs são dados públicos, sem restrição de uso
- **Dados de PF:** CPFs mascarados; uso limitado para proteção de privacidade
- **Licença:** Dados abertos sob licença livre (reutilização permitida)
- **Uso comercial:** Permitido, conforme empresas do mercado já praticam

### Limitações Técnicas

| Limitação | Impacto |
|-----------|---------|
| **Defasagem temporal** | Dados podem estar 1-4 meses desatualizados |
| **Dívidas parceladas** | Na Lista de Devedores online, parcelados não aparecem; nos Dados Abertos, sim |
| **Sem valor atualizado** | Valor consolidado pode não refletir correções recentes |
| **CPF mascarado** | Impossível vincular PF diretamente |
| **Encoding ISO-8859-1** | Arquivos precisam de conversão de encoding |
| **CNPJ com pontuação** | Necessário remover pontuação para JOINs |

### Considerações para Uso

1. **Não substituir Certidão Negativa de Débitos (CND)**
   - Para fins oficiais, sempre exigir CND da própria empresa

2. **Atualização contínua**
   - Empresa pode quitar dívida após publicação
   - Monitorar trimestralmente

3. **Contexto é importante**
   - Dívida com garantia (EMBARGADA) não significa inadimplência
   - Suspensão judicial pode indicar contestação legítima

---

## API SERPRO (Acesso Pago)

Para consultas em tempo real e maior volume, a SERPRO oferece uma API paga:

### Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/inscricao/{numeroInscricao}` | Consulta por número de inscrição |
| GET | `/v1/devedor/{cpfCnpj}` | Consulta todas as dívidas de um CPF/CNPJ |

### Campos Retornados (JSON)

```json
{
  "inscricao": "9061700096419",
  "situacao": "ATIVA NAO PRIORIZADA PARA AJUIZAMENTO",
  "dataInscricao": "2017-05-15",
  "valorTotalInscritoMoeda": "15234.56",
  "valorTotalConsolidadoMoeda": "23456.78",
  "orgaoOrigem": "RECEITA FEDERAL DO BRASIL",
  "nomeNaturezaReceita": "TRIBUTARIA",
  "nomePFNResponsavel": "PFN/SP",
  "indicadorAjuizado": "N"
}
```

### Autenticação

```bash
# Obter token OAuth2
curl -X POST "https://gateway.apiserpro.serpro.gov.br/token" \
  -H "Authorization: Basic {base64(consumerKey:consumerSecret)}" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials"

# Consultar dívida
curl -X GET "https://gateway.apiserpro.serpro.gov.br/consulta-divida-ativa/api/v1/devedor/{cnpj}" \
  -H "Authorization: Bearer {access_token}" \
  -H "Accept: application/json"
```

### Contratação

- **URL:** https://www.loja.serpro.gov.br/product/consulta-divida-ativa
- **Modelo:** Pay-per-use (por consulta)
- **Trial:** Disponível para testes com dados fictícios

---

## Código Python para Download e Processamento

### Download dos Dados Abertos

```python
"""
Download e processamento dos dados abertos da PGFN
Dívida Ativa da União e FGTS
"""

import os
import requests
import zipfile
import polars as pl
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import logging
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
BASE_URL = "https://dadosabertos.pgfn.gov.br"
TIPOS_DIVIDA = [
    "Dados_abertos_Nao_Previdenciario",  # Dívida Geral (~1.1GB)
    "Dados_abertos_Previdenciario",       # Dívida Previdenciária (~89MB)
    "Dados_abertos_FGTS"                  # FGTS (~17MB)
]


def get_latest_trimester() -> tuple[int, int]:
    """
    Retorna o trimestre mais recente disponível (estimativa).
    Dados são publicados ~45 dias após o fim do trimestre.
    """
    today = datetime.now()
    year = today.year
    month = today.month

    # Estimar trimestre disponível (com 2 meses de atraso)
    if month <= 2:
        return year - 1, 3  # Q3 do ano anterior
    elif month <= 5:
        return year - 1, 4  # Q4 do ano anterior
    elif month <= 8:
        return year, 1      # Q1
    elif month <= 11:
        return year, 2      # Q2
    else:
        return year, 3      # Q3


def download_and_extract(
    year: int,
    trimester: int,
    output_dir: str = "./data/pgfn",
    tipos: Optional[List[str]] = None
) -> List[Path]:
    """
    Baixa e extrai os arquivos ZIP de um trimestre específico.

    Args:
        year: Ano (ex: 2025)
        trimester: Trimestre (1-4)
        output_dir: Diretório de saída
        tipos: Lista de tipos de dívida (None = todos)

    Returns:
        Lista de paths dos arquivos CSV extraídos
    """
    tipos = tipos or TIPOS_DIVIDA
    output_path = Path(output_dir) / f"{year}_Q{trimester}"
    output_path.mkdir(parents=True, exist_ok=True)

    extracted_files = []
    base_dir = f"{year}_trimestre_{trimester:02d}"

    for tipo in tipos:
        zip_filename = f"{tipo}.zip"
        url = f"{BASE_URL}/{base_dir}/{zip_filename}"

        try:
            logger.info(f"Baixando: {zip_filename}")
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()

            # Extrair ZIP em memória
            with zipfile.ZipFile(BytesIO(response.content)) as zf:
                for csv_name in zf.namelist():
                    if csv_name.endswith('.csv'):
                        local_path = output_path / csv_name

                        if local_path.exists():
                            logger.info(f"Já existe: {csv_name}")
                        else:
                            zf.extract(csv_name, output_path)
                            logger.info(f"Extraído: {csv_name}")

                        extracted_files.append(local_path)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Não encontrado: {zip_filename}")
            else:
                logger.error(f"Erro ao baixar {zip_filename}: {e}")
        except Exception as e:
            logger.error(f"Erro ao processar {zip_filename}: {e}")

    return extracted_files


def process_csv(filepath: Path, only_pj: bool = True) -> pl.DataFrame:
    """
    Processa um arquivo CSV da PGFN.

    Args:
        filepath: Caminho do arquivo CSV
        only_pj: Se True, filtra apenas pessoas jurídicas

    Returns:
        DataFrame Polars com os dados processados
    """
    # Arquivos estão em ISO-8859-1
    df = pl.read_csv(
        filepath,
        separator=";",
        encoding="iso-8859-1",
        infer_schema_length=10000,
        ignore_errors=True
    )

    # Normalizar nomes de colunas
    df = df.rename({col: col.upper().strip() for col in df.columns})

    # Filtrar apenas PJ se solicitado
    if only_pj and "TIPO_PESSOA" in df.columns:
        df = df.filter(pl.col("TIPO_PESSOA") == "Pessoa jurídica")

    # Limpar CNPJ (remover pontuação)
    if "CPF_CNPJ" in df.columns:
        df = df.with_columns([
            pl.col("CPF_CNPJ")
            .str.replace_all(r"[.\-/]", "")
            .alias("CNPJ_LIMPO")
        ])

    # Converter valor para numérico
    if "VALOR_CONSOLIDADO" in df.columns:
        df = df.with_columns([
            pl.col("VALOR_CONSOLIDADO")
            .cast(pl.Float64)
            .alias("VALOR_CONSOLIDADO")
        ])

    # Converter data
    if "DATA_INSCRICAO" in df.columns:
        df = df.with_columns([
            pl.col("DATA_INSCRICAO")
            .str.to_date("%d/%m/%Y", strict=False)
            .alias("DATA_INSCRICAO_DT")
        ])

    return df


def consolidate_by_cnpj(df: pl.DataFrame) -> pl.DataFrame:
    """
    Consolida dados por CNPJ, agregando valores e contando inscrições.
    Considera apenas devedores PRINCIPAL para evitar duplicação.
    """
    return (
        df.filter(pl.col("TIPO_DEVEDOR") == "Principal")
        .group_by("CNPJ_LIMPO")
        .agg([
            pl.col("NOME_DEVEDOR").first().alias("RAZAO_SOCIAL"),
            pl.col("UF_DEVEDOR").first().alias("UF"),
            pl.col("VALOR_CONSOLIDADO").sum().alias("DIVIDA_TOTAL"),
            pl.col("NUMERO_INSCRICAO").count().alias("QTD_INSCRICOES"),
            pl.col("DATA_INSCRICAO_DT").min().alias("INSCRICAO_MAIS_ANTIGA"),
            pl.col("SITUACAO_INSCRICAO")
            .filter(pl.col("SITUACAO_INSCRICAO").str.contains("AJUIZ"))
            .count()
            .alias("QTD_AJUIZADAS"),
            pl.col("SITUACAO_INSCRICAO")
            .filter(pl.col("SITUACAO_INSCRICAO") == "PROTESTADA")
            .count()
            .alias("QTD_PROTESTADAS"),
        ])
        .with_columns([
            pl.col("CNPJ_LIMPO").str.slice(0, 8).alias("CNPJ_BASICO")
        ])
        .sort("DIVIDA_TOTAL", descending=True)
    )


def load_to_postgres(
    df: pl.DataFrame,
    table_name: str = "pgfn_devedores",
    connection_string: str = "postgresql://user:pass@localhost/cnpj"
):
    """
    Carrega dados para PostgreSQL usando COPY (bulk insert).
    """
    import psycopg2
    from io import StringIO

    # Preparar CSV em memória
    csv_buffer = StringIO()
    df.write_csv(csv_buffer, separator="\t", null_value="\\N")
    csv_buffer.seek(0)

    conn = psycopg2.connect(connection_string)
    cursor = conn.cursor()

    try:
        # Criar tabela staging
        cursor.execute(f"""
            CREATE TEMP TABLE staging_{table_name} (LIKE {table_name});
        """)

        # COPY para staging
        cursor.copy_from(
            csv_buffer,
            f"staging_{table_name}",
            sep="\t",
            null="\\N"
        )

        # UPSERT para tabela final
        cursor.execute(f"""
            INSERT INTO {table_name}
            SELECT * FROM staging_{table_name}
            ON CONFLICT (cpf_cnpj, numero_inscricao)
            DO UPDATE SET
                valor_consolidado = EXCLUDED.valor_consolidado,
                tipo_situacao_inscricao = EXCLUDED.tipo_situacao_inscricao,
                situacao_inscricao = EXCLUDED.situacao_inscricao,
                updated_at = NOW();
        """)

        conn.commit()
        logger.info(f"Carregados {len(df)} registros para {table_name}")

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


# Schema SQL para a tabela
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS pgfn_devedores (
    id SERIAL,
    cpf_cnpj VARCHAR(18) NOT NULL,          -- Com pontuação original
    cnpj_limpo VARCHAR(14),                  -- Sem pontuação (para JOINs)
    tipo_pessoa VARCHAR(20),
    tipo_devedor VARCHAR(20),
    nome_devedor VARCHAR(255),
    uf_devedor VARCHAR(2),
    unidade_responsavel VARCHAR(100),
    entidade_responsavel VARCHAR(50),        -- Apenas FGTS
    unidade_inscricao VARCHAR(100),          -- Apenas FGTS
    numero_inscricao VARCHAR(20) NOT NULL,
    tipo_situacao_inscricao VARCHAR(50),
    situacao_inscricao VARCHAR(100),
    receita_principal VARCHAR(255),          -- Apenas FGTS
    tipo_credito VARCHAR(50),                -- Apenas Previdenciário/Não Prev
    data_inscricao DATE,
    indicador_ajuizado VARCHAR(3),
    valor_consolidado DECIMAL(18,2),
    origem_arquivo VARCHAR(100),
    trimestre_referencia VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (cpf_cnpj, numero_inscricao)
);

-- Índices para queries B2B
CREATE INDEX IF NOT EXISTS idx_pgfn_cnpj_limpo ON pgfn_devedores(cnpj_limpo);
CREATE INDEX IF NOT EXISTS idx_pgfn_cnpj_basico ON pgfn_devedores(LEFT(cnpj_limpo, 8));
CREATE INDEX IF NOT EXISTS idx_pgfn_situacao ON pgfn_devedores(situacao_inscricao);
CREATE INDEX IF NOT EXISTS idx_pgfn_tipo_situacao ON pgfn_devedores(tipo_situacao_inscricao);
CREATE INDEX IF NOT EXISTS idx_pgfn_valor ON pgfn_devedores(valor_consolidado DESC);
CREATE INDEX IF NOT EXISTS idx_pgfn_uf ON pgfn_devedores(uf_devedor);
CREATE INDEX IF NOT EXISTS idx_pgfn_data ON pgfn_devedores(data_inscricao);

-- View consolidada por empresa
CREATE OR REPLACE VIEW vw_pgfn_empresas AS
SELECT
    LEFT(cnpj_limpo, 8) AS cnpj_basico,
    MAX(nome_devedor) AS razao_social,
    MAX(uf_devedor) AS uf,
    SUM(valor_consolidado) FILTER (WHERE tipo_devedor = 'Principal') AS divida_total,
    COUNT(*) FILTER (WHERE tipo_devedor = 'Principal') AS qtd_inscricoes,
    COUNT(*) FILTER (WHERE situacao_inscricao ILIKE '%AJUIZ%') AS qtd_ajuizadas,
    COUNT(*) FILTER (WHERE situacao_inscricao = 'PROTESTADA') AS qtd_protestadas,
    MIN(data_inscricao) AS inscricao_mais_antiga,
    MAX(updated_at) AS ultima_atualizacao
FROM pgfn_devedores
WHERE tipo_pessoa = 'Pessoa jurídica'
GROUP BY LEFT(cnpj_limpo, 8);
"""


if __name__ == "__main__":
    # Exemplo de uso
    year, trimester = get_latest_trimester()
    print(f"Baixando dados do Q{trimester}/{year}...")

    # Baixar apenas FGTS como teste (menor arquivo)
    files = download_and_extract(
        year=year,
        trimester=trimester,
        output_dir="./data/pgfn",
        tipos=["Dados_abertos_FGTS"]
    )

    # Processar arquivos
    all_data = []
    for f in files:
        if f.exists():
            df = process_csv(f, only_pj=True)
            all_data.append(df)
            print(f"Processado {f.name}: {len(df)} registros")

    if all_data:
        # Concatenar e consolidar
        df_full = pl.concat(all_data)
        df_consolidated = consolidate_by_cnpj(df_full)

        print(f"\nTotal de empresas únicas: {len(df_consolidated)}")
        print(f"Dívida total: R$ {df_consolidated['DIVIDA_TOTAL'].sum():,.2f}")

        # Top 10 devedores
        print("\nTop 10 maiores devedores:")
        print(df_consolidated.head(10))
```

### Consulta via API SERPRO

```python
"""
Consulta à API SERPRO de Dívida Ativa
Requer contratação: https://www.loja.serpro.gov.br/product/consulta-divida-ativa
"""

import requests
import base64
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class SerproDividaAtivaAPI:
    """
    Cliente para API SERPRO de Consulta Dívida Ativa.
    """

    BASE_URL = "https://gateway.apiserpro.serpro.gov.br"
    TOKEN_URL = f"{BASE_URL}/token"
    API_PATH = "/consulta-divida-ativa/api/v1"

    def __init__(self, consumer_key: str, consumer_secret: str):
        """
        Inicializa o cliente com credenciais OAuth2.

        Args:
            consumer_key: Chave do consumidor (obtida no portal SERPRO)
            consumer_secret: Segredo do consumidor
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self._access_token = None

    def _get_token(self) -> str:
        """Obtém ou renova o token de acesso OAuth2."""
        if self._access_token:
            return self._access_token

        # Codificar credenciais em Base64
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        response = requests.post(
            self.TOKEN_URL,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data="grant_type=client_credentials",
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        self._access_token = data["access_token"]
        return self._access_token

    def _request(self, endpoint: str) -> Dict:
        """Faz requisição autenticada à API."""
        token = self._get_token()

        response = requests.get(
            f"{self.BASE_URL}{self.API_PATH}{endpoint}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            },
            timeout=30
        )

        if response.status_code == 401:
            # Token expirado, renovar
            self._access_token = None
            return self._request(endpoint)

        response.raise_for_status()
        return response.json()

    def consultar_por_inscricao(self, numero_inscricao: str) -> Dict:
        """
        Consulta dívida por número de inscrição.

        Args:
            numero_inscricao: Número da inscrição na dívida ativa

        Returns:
            Dict com dados da dívida
        """
        return self._request(f"/inscricao/{numero_inscricao}")

    def consultar_por_cnpj(self, cnpj: str) -> List[Dict]:
        """
        Consulta todas as dívidas de um CNPJ.

        Args:
            cnpj: CNPJ (apenas números, 14 dígitos)

        Returns:
            Lista de dívidas associadas ao CNPJ
        """
        # Limpar CNPJ
        cnpj = "".join(filter(str.isdigit, cnpj))

        return self._request(f"/devedor/{cnpj}")

    def verificar_situacao(self, cnpj: str) -> Dict:
        """
        Verifica situação consolidada de um CNPJ.

        Args:
            cnpj: CNPJ da empresa

        Returns:
            Dict com situação consolidada
        """
        dividas = self.consultar_por_cnpj(cnpj)

        if not dividas:
            return {
                "cnpj": cnpj,
                "tem_divida": False,
                "divida_total": 0,
                "qtd_inscricoes": 0,
                "situacoes": []
            }

        # Agregar dados
        total = sum(
            float(d.get("valorTotalConsolidadoMoeda", 0) or 0)
            for d in dividas
        )
        situacoes = list(set(d.get("situacao", "") for d in dividas))

        return {
            "cnpj": cnpj,
            "tem_divida": True,
            "divida_total": total,
            "qtd_inscricoes": len(dividas),
            "situacoes": situacoes,
            "detalhes": dividas
        }


# Exemplo de uso
if __name__ == "__main__":
    # Credenciais de exemplo (substituir pelas reais)
    api = SerproDividaAtivaAPI(
        consumer_key="SUA_CONSUMER_KEY",
        consumer_secret="SEU_CONSUMER_SECRET"
    )

    # Consultar empresa
    cnpj = "00000000000191"  # CNPJ de exemplo
    resultado = api.verificar_situacao(cnpj)

    print(f"CNPJ: {resultado['cnpj']}")
    print(f"Tem dívida: {resultado['tem_divida']}")
    print(f"Valor total: R$ {resultado['divida_total']:,.2f}")
    print(f"Inscrições: {resultado['qtd_inscricoes']}")
```

---

## Referências

- [Dados Abertos PGFN](https://www.gov.br/pgfn/pt-br/assuntos/divida-ativa-da-uniao/transparencia-fiscal-1/dados-abertos) - Portal oficial
- [Lista de Devedores PGFN](https://www.listadevedores.pgfn.gov.br/) - Consulta online
- [Portal dados.gov.br - Devedores da União](https://dados.gov.br/dados/conjuntos-dados/devedores-da-uniao-e-do-fgts1) - Catálogo nacional
- [API SERPRO - Documentação](https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-divida-ativa/pt/) - Referência técnica
- [Base dos Dados - Lista de Devedores](https://basedosdados.org/dataset/lista-de-devedores-da-pgfn) - Dados tratados

---

## Contato

Para dúvidas sobre os dados abertos da PGFN:
- **E-mail:** inovadau@pgfn.gov.br
- **Site:** https://www.gov.br/pgfn

---

*Documento criado em: Janeiro/2026*
*Última atualização: 2026-01-28*
*Validado em: 2026-01-28 (ver pgfn/VALIDACAO.md)*
