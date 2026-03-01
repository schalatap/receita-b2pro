# IBGE - Instituto Brasileiro de Geografia e Estatística

## Visão Geral

O IBGE é a principal fonte de dados demográficos, geográficos e econômicos do Brasil. Para uma plataforma de inteligência comercial B2B, os dados do IBGE são fundamentais para:

- **Segmentação geográfica**: filtrar empresas por municípios com determinado perfil demográfico
- **Análise de mercado**: identificar potencial de consumo por região (PIB, população, renda)
- **Enriquecimento de leads**: adicionar contexto territorial (área, coordenadas, IDH)
- **Scoring de oportunidades**: priorizar regiões com maior potencial econômico

---

## Código do Município (Chave de Ligação)

O código IBGE é a chave padrão para relacionar dados municipais entre diferentes fontes.

### Estrutura do Código

```
Código IBGE: 7 dígitos
|__|__|__|__|__|__|__|
 UF    Município
 (2)      (5)

Exemplo: 3550308 = São Paulo/SP
- 35 = Código da UF (São Paulo)
- 50308 = Código do município dentro da UF
```

### Correspondência com Código RFB

A Receita Federal utiliza o **mesmo código IBGE de 7 dígitos** na tabela de municípios:

| Fonte | Campo | Exemplo |
|-------|-------|---------|
| RFB (estabelecimentos) | `municipio` | 3550308 |
| IBGE | `codigo_municipio` | 3550308 |

**Importante**: O código SIAFI (4 dígitos) usado pelo Tesouro Nacional é diferente. Para conversão, use:
- [Tabela Tesouro Transparente](https://www.tesourotransparente.gov.br/publicacoes/codigos-siafi-dos-municipios/2018/26)

---

## 1. População Municipal (Censo 2022)

### Fonte Oficial

- **Pesquisa**: Censo Demográfico 2022
- **Periodicidade**: Decenal (último: 2022, próximo: 2032)
- **Cobertura**: 5.570 municípios
- **Referência**: Contagem realizada em agosto/2022

### URLs de Download

**FTP IBGE (arquivos brutos)**:
```
https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Populacao_e_domicilios_Primeiros_resultados/Resultados_da_2a_apuracao_20231027/
```

> **Validado em 2026-01-28**: URL acessível, todos os arquivos confirmados.

**Arquivos disponíveis**:
| Arquivo | Formato | Tamanho |
|---------|---------|---------|
| CD2022_Populacao_Coletada_Imputada_e_Total_Municipio_e_UF_20231222.xlsx | Excel | 316 KB |
| CD2022_Populacao_Coletada_Imputada_e_Total_Municipio_e_UF_20231222.ods | ODS | 302 KB |
| CD2022_Populacao_2010_Compatibilizada_20231222.xlsx | Excel | 313 KB |

### API SIDRA (Tabela 9514)

Para acesso programático, use a API SIDRA com a tabela 9514:

```
https://apisidra.ibge.gov.br/values/t/9514/n6/all/v/93/p/last%201
```

**Parâmetros**:
- `t/9514` - Tabela do Censo 2022
- `n6/all` - Nível municipal, todos os municípios
- `v/93` - Variável: população residente
- `p/last%201` - Período: último disponível

### Estrutura dos Dados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| codigo_uf | VARCHAR(2) | Código da UF |
| codigo_municipio | VARCHAR(7) | Código IBGE completo |
| nome_municipio | VARCHAR(100) | Nome do município |
| populacao_total | INTEGER | População residente total |
| populacao_homens | INTEGER | População masculina |
| populacao_mulheres | INTEGER | População feminina |

### Código Python de Exemplo

```python
import sidrapy
import pandas as pd

def baixar_populacao_censo_2022():
    """
    Baixa população do Censo 2022 para todos os municípios.
    Usa a biblioteca sidrapy para acessar a API SIDRA.

    Instalação: pip install sidrapy
    """
    # Tabela 9514 - Censo 2022 - População por sexo
    data = sidrapy.get_table(
        table_code="9514",
        territorial_level="6",      # Município
        ibge_territorial_code="all", # Todos
        variable="93",              # População residente
        period="last 1"
    )

    # Converter para DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])

    # Limpar e renomear colunas
    df = df.rename(columns={
        'Cód.': 'codigo_municipio',
        'Município': 'nome_municipio',
        'Valor': 'populacao'
    })

    # Converter tipos
    df['populacao'] = pd.to_numeric(df['populacao'], errors='coerce')

    return df[['codigo_municipio', 'nome_municipio', 'populacao']]

# Uso
df_pop = baixar_populacao_censo_2022()
print(f"Municípios carregados: {len(df_pop)}")
df_pop.to_csv('populacao_censo_2022.csv', index=False)
```

### Alternativa: Download Direto

```python
import pandas as pd
import requests
from io import BytesIO

def baixar_populacao_xlsx():
    """
    Baixa arquivo XLSX diretamente do FTP IBGE.
    """
    url = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Populacao_e_domicilios_Primeiros_resultados/Resultados_da_2a_apuracao_20231027/CD2022_Populacao_Coletada_Imputada_e_Total_Municipio_e_UF_20231222.xlsx"

    response = requests.get(url)
    df = pd.read_excel(BytesIO(response.content), skiprows=5)

    return df

df = baixar_populacao_xlsx()
```

---

## 2. PIB Municipal

### Fonte Oficial

- **Pesquisa**: Produto Interno Bruto dos Municípios
- **Periodicidade**: Anual (defasagem de ~2 anos)
- **Última disponível**: 2022-2023
- **Cobertura**: 5.570 municípios

### URLs de Download

**FTP IBGE**:
```
https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/xlsx/
```

> **Validado em 2026-01-28**: URL acessível, arquivos atualizados em dez/2025.

**Arquivos disponíveis (2022-2023)**:
| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| tabelas_completas_2022.xlsx | 93 KB | PIB e PIB per capita 2022 |
| tabelas_completas_2023.xlsx | 93 KB | PIB e PIB per capita 2023 |

**Página oficial**:
```
https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9088-produto-interno-bruto-dos-municipios.html
```

### Estrutura dos Dados (2022-2023)

> **Nota**: A partir de 2022, o IBGE não divulga mais a abertura por setores (agropecuária, indústria, serviços). Apenas PIB total e PIB per capita.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| codigo_municipio | VARCHAR(7) | Código IBGE |
| nome_municipio | VARCHAR(100) | Nome do município |
| ano | INTEGER | Ano de referência |
| pib | DECIMAL(15,2) | PIB a preços correntes (R$ mil) |
| pib_per_capita | DECIMAL(10,2) | PIB per capita (R$) |

### Dados Históricos (2002-2021)

Para dados com abertura setorial, use os arquivos históricos:
```
https://ftp.ibge.gov.br/Pib_Municipios/2021/base/
```

Campos adicionais disponíveis até 2021:
- `va_agropecuaria` - Valor adicionado agropecuária
- `va_industria` - Valor adicionado indústria
- `va_servicos` - Valor adicionado serviços
- `impostos` - Impostos líquidos sobre produtos

### Código Python de Exemplo

```python
import pandas as pd
import requests
from io import BytesIO

def baixar_pib_municipal(ano: int = 2023):
    """
    Baixa PIB municipal do FTP IBGE.

    Args:
        ano: 2022 ou 2023 (dados mais recentes)
    """
    url = f"https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/xlsx/tabelas_completas_{ano}.xlsx"

    response = requests.get(url)
    response.raise_for_status()

    df = pd.read_excel(
        BytesIO(response.content),
        sheet_name=0,
        skiprows=3  # Pular cabeçalho
    )

    # Padronizar nomes de colunas
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    return df

# Uso
df_pib = baixar_pib_municipal(2023)
print(f"Municípios: {len(df_pib)}")
print(f"PIB total Brasil: R$ {df_pib['pib'].sum():,.0f} mil")
```

---

## 3. Coordenadas Geográficas (Sedes Municipais)

### Fonte Oficial

- **Produto**: Localidades do Brasil (Censo 2022)
- **Periodicidade**: Atualizado com cada Censo
- **Cobertura**: 21.304 localidades (incluindo sedes municipais, vilas, aldeias)

### URLs de Download

**FTP IBGE (Shapefile/GeoPackage)**:
```
https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/Localidades_do_Brasil/2022/
```

> **Validado em 2026-01-28**: URL acessível. Arquivos disponíveis: Localidades_Brasil_gpkg.zip (6.2 MB), Localidades_Brasil_shp.zip (4.3 MB), Localidades_Municipios_kml.zip (181 MB).

**Formatos disponíveis**:
| Formato | Extensão | Uso |
|---------|----------|-----|
| Shapefile | .shp | SIGs (QGIS, ArcGIS) |
| GeoPackage | .gpkg | SIGs modernos |
| KML | .kml | Google Earth |

### Alternativa Simplificada (GitHub) - **RECOMENDADO**

Para uso rápido sem processar shapefiles, use o repositório consolidado:

```
https://github.com/kelvins/municipios-brasileiros
```

> **Validado em 2026-01-28**: CSV acessível com 5.570 municípios. Estrutura confirmada: codigo_ibge, nome, latitude, longitude, capital, codigo_uf, siafi_id, ddd, fuso_horario.

**Arquivos**:
- `csv/municipios.csv` - CSV com todos os dados
- `json/municipios.json` - JSON estruturado
- `sql/municipios.sql` - Script SQL para PostgreSQL

### Estrutura dos Dados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| codigo_ibge | VARCHAR(7) | Código IBGE do município |
| nome | VARCHAR(100) | Nome do município |
| uf | VARCHAR(2) | Sigla da UF |
| latitude | DECIMAL(10,7) | Latitude da sede (decimal) |
| longitude | DECIMAL(10,7) | Longitude da sede (decimal) |
| capital | BOOLEAN | Se é capital estadual |
| codigo_siafi | VARCHAR(4) | Código SIAFI (Tesouro) |
| ddd | VARCHAR(2) | Código DDD |
| fuso_horario | VARCHAR(50) | Timezone (America/Sao_Paulo) |

### Código Python de Exemplo

```python
import pandas as pd

def baixar_coordenadas_municipios():
    """
    Baixa coordenadas das sedes municipais do GitHub.
    Fonte: kelvins/municipios-brasileiros
    """
    url = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"

    df = pd.read_csv(url)

    # Selecionar colunas relevantes
    df = df[[
        'codigo_ibge', 'nome', 'codigo_uf', 'uf',
        'latitude', 'longitude', 'capital', 'ddd'
    ]]

    return df

# Uso
df_coords = baixar_coordenadas_municipios()
print(f"Municípios: {len(df_coords)}")

# Exemplo: encontrar capitais
capitais = df_coords[df_coords['capital'] == 1]
print(f"Capitais: {len(capitais)}")
```

### Carregamento via API IBGE

```python
import requests

def listar_municipios_api():
    """
    Lista municípios via API de Localidades do IBGE.
    Não inclui coordenadas - use shapefile para isso.
    """
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

    response = requests.get(url)
    municipios = response.json()

    # Estrutura: id, nome, microrregiao, mesorregiao, UF
    return municipios

municipios = listar_municipios_api()
print(f"Total de municípios: {len(municipios)}")
```

---

## 4. Área Territorial

### Fonte Oficial

- **Produto**: Áreas Territoriais dos Municípios
- **Periodicidade**: Anual (atualizado em julho)
- **Última disponível**: 2024
- **Cobertura**: 5.569 municípios + DF + Fernando de Noronha

### URLs de Download

**Página oficial**:
```
https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/15761-areas-dos-municipios.html
```

**Formatos disponíveis**: XLS, ODS

> **Validado em 2026-01-28**: Página acessível e funcional.

### Estrutura dos Dados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| codigo_uf | VARCHAR(2) | Código da UF |
| nome_uf | VARCHAR(50) | Nome da UF |
| codigo_municipio | VARCHAR(7) | Código IBGE |
| nome_municipio | VARCHAR(100) | Nome do município |
| area_km2 | DECIMAL(12,3) | Área em km² |

### Valores de Referência (2024)

- **Área total do Brasil**: 8.509.379,576 km²
- **Total de municípios**: 5.569
- **Maior município**: Altamira/PA (159.533 km²)
- **Menor município**: Santa Cruz de Minas/MG (3,5 km²)

---

## 5. IDH Municipal (IDHM)

### Fonte Oficial

- **Produto**: Atlas do Desenvolvimento Humano no Brasil
- **Responsáveis**: PNUD, IPEA, Fundação João Pinheiro
- **Periodicidade**: Decenal (baseado no Censo)
- **Última disponível**: Censo 2010 (IDHM 2022 ainda não publicado)

### URLs de Download

**Portal de Dados Abertos**:
```
https://dados.gov.br/dados/conjuntos-dados/atlasbrasil
```

**Site oficial**:
```
http://www.atlasbrasil.org.br/
```

> **Aviso (2026-01-28)**: O site atlasbrasil.org.br pode estar temporariamente indisponível. Use a alternativa Base dos Dados abaixo.

**Base dos Dados** (BigQuery/API) - **RECOMENDADO**:
```
https://basedosdados.org/dataset/cbfc7253-089b-44e2-8825-755e1419efc8
```

> **Validado em 2026-01-28**: Contém IDHM para todos os municípios (1991-2010). Acesso via SQL, Python, R ou CSV.

### Estrutura dos Dados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| codigo_municipio | VARCHAR(7) | Código IBGE |
| nome_municipio | VARCHAR(100) | Nome do município |
| ano | INTEGER | Ano de referência (1991, 2000, 2010) |
| idhm | DECIMAL(5,3) | IDHM geral (0-1) |
| idhm_renda | DECIMAL(5,3) | Componente renda |
| idhm_longevidade | DECIMAL(5,3) | Componente saúde |
| idhm_educacao | DECIMAL(5,3) | Componente educação |

### Classificação do IDHM

| Faixa | Classificação |
|-------|---------------|
| 0.800 - 1.000 | Muito Alto |
| 0.700 - 0.799 | Alto |
| 0.600 - 0.699 | Médio |
| 0.500 - 0.599 | Baixo |
| 0.000 - 0.499 | Muito Baixo |

### Limitação Importante

> **ATENÇÃO**: Os dados de IDHM municipal mais recentes são de 2010. O IDHM baseado no Censo 2022 ainda não foi publicado (previsão: 2025-2026). Para estimativas mais recentes, use o "Radar IDHM" que atualiza anualmente para UFs e RMs (não para municípios).

### Código Python de Exemplo

```python
import pandas as pd
from basedosdados import read_table

def baixar_idhm_basedosdados():
    """
    Baixa IDHM via Base dos Dados (requer autenticação BigQuery).
    Instalar: pip install basedosdados
    """
    df = read_table(
        dataset_id='br_pnud_atlas',
        table_id='municipio',
        billing_project_id='seu-projeto-gcp'
    )

    return df

# Alternativa: download direto do CSV
def baixar_idhm_csv():
    """
    Baixa IDHM de fonte alternativa consolidada.
    """
    # Fonte: IPEA Data ou dados.gov.br
    # O download requer navegação no portal - não há URL direta
    pass
```

---

## 6. APIs do IBGE

### API de Localidades

**Base URL**: `https://servicodados.ibge.gov.br/api/v1/localidades`

| Endpoint | Descrição |
|----------|-----------|
| `/municipios` | Lista todos os municípios |
| `/estados/{UF}/municipios` | Municípios de uma UF |
| `/regioes` | Grandes regiões |
| `/mesorregioes` | Mesorregiões |
| `/microrregioes` | Microrregiões |

**Exemplo**:
```bash
curl "https://servicodados.ibge.gov.br/api/v1/localidades/estados/SP/municipios"
```

### API SIDRA (Dados Agregados)

**Base URL**: `https://apisidra.ibge.gov.br/values`

**Estrutura**:
```
/values/t/{tabela}/n{nivel}/{localidade}/v/{variavel}/p/{periodo}/c{classificacao}/{categoria}
```

**Níveis territoriais**:
| Código | Nível |
|--------|-------|
| n1 | Brasil |
| n2 | Grande Região |
| n3 | UF |
| n6 | Município |
| n9 | Mesorregião |
| n10 | Microrregião |

**Tabelas úteis**:
| Tabela | Conteúdo |
|--------|----------|
| 9514 | População Censo 2022 |
| 200 | População Censos históricos |
| 4709 | Estimativas populacionais |

### API de Malhas (GeoJSON)

**Base URL**: `https://servicodados.ibge.gov.br/api/v3/malhas`

**Formatos**:
- `?formato=application/vnd.geo+json` - GeoJSON
- `?formato=application/json` - TopoJSON
- `?formato=image/svg+xml` - SVG

**Exemplo**:
```bash
curl "https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json"
```

---

## 7. Uso para B2B - Exemplos Práticos

### Segmentação por Potencial de Mercado

```sql
-- Municípios com alto PIB per capita e população relevante
SELECT
    e.cnpj_basico,
    e.razao_social,
    m.nome as municipio,
    p.populacao,
    pib.pib_per_capita
FROM estabelecimentos est
JOIN empresas e ON e.cnpj_basico = est.cnpj_basico
JOIN municipios_ibge m ON m.codigo = est.municipio
JOIN populacao_censo_2022 p ON p.codigo_municipio = est.municipio
JOIN pib_municipal pib ON pib.codigo_municipio = est.municipio
WHERE est.situacao_cadastral = '02'  -- Ativas
  AND p.populacao >= 100000           -- Cidades médias+
  AND pib.pib_per_capita >= 40000     -- Alto PIB per capita
  AND est.cnae_fiscal_principal LIKE '62%'  -- TI
ORDER BY pib.pib_per_capita DESC;
```

### Enriquecimento de Leads com Coordenadas

```sql
-- Adicionar lat/long para mapeamento
SELECT
    e.razao_social,
    est.logradouro,
    m.nome as municipio,
    c.latitude,
    c.longitude
FROM estabelecimentos est
JOIN empresas e ON e.cnpj_basico = est.cnpj_basico
JOIN coordenadas_municipios c ON c.codigo_ibge = est.municipio
WHERE est.situacao_cadastral = '02';
```

### Score de Oportunidade Regional

```python
def calcular_score_regional(codigo_municipio: str) -> float:
    """
    Calcula score de oportunidade baseado em indicadores IBGE.

    Peso:
    - PIB per capita: 40%
    - População: 30%
    - IDHM: 20%
    - Densidade empresarial: 10%
    """
    # Buscar indicadores
    pib_pc = get_pib_per_capita(codigo_municipio)
    pop = get_populacao(codigo_municipio)
    idhm = get_idhm(codigo_municipio)
    densidade = get_densidade_empresarial(codigo_municipio)

    # Normalizar (0-100)
    score_pib = min(pib_pc / 800, 100)  # 80k = 100%
    score_pop = min(pop / 5000000 * 100, 100)  # 5M = 100%
    score_idhm = idhm * 100  # já está em 0-1
    score_dens = min(densidade / 50, 100)  # 50 emp/1000 hab = 100%

    # Calcular score final
    score = (
        score_pib * 0.4 +
        score_pop * 0.3 +
        score_idhm * 0.2 +
        score_dens * 0.1
    )

    return round(score, 2)
```

---

## 8. Limitações Conhecidas

### Defasagem dos Dados

| Dado | Última atualização | Próxima prevista |
|------|-------------------|------------------|
| População (Censo) | 2022 | 2032 |
| PIB Municipal | 2023 | 2024 (dez/2025) |
| IDHM | 2010 | 2025-2026 |
| Áreas | 2024 | 2025 |

> **Validado em 2026-01-28**: PIB 2022/2023 confirmado disponível no FTP IBGE.

### Incompletude do IDHM

O IDHM municipal mais recente é de **2010**. Para análises atuais, considere:
- Usar o IDHM 2010 como proxy (correlação alta com desenvolvimento atual)
- Combinar com PIB per capita recente para ajustar
- Usar Radar IDHM (UF/RM) para tendências

### Mudanças de Limites Municipais

- Novos municípios são criados (ex: Boa Esperança do Norte/MT em 2024)
- Códigos antigos podem não corresponder a dados novos
- Sempre use a tabela de municípios do mesmo ano dos dados

### Volume de Dados

| Fonte | Registros | Tamanho aprox. |
|-------|-----------|----------------|
| População | 5.570 | 500 KB |
| PIB | 5.570 x 22 anos | 5 MB |
| Coordenadas | 5.570 | 300 KB |
| IDHM | 5.570 x 3 anos | 2 MB |
| Shapefiles | 5.570 | 150 MB |

---

## 9. Referências e Links Oficiais

### Portais Principais

| Portal | URL | Conteúdo |
|--------|-----|----------|
| IBGE Estatísticas | https://www.ibge.gov.br/estatisticas | Portal principal |
| FTP IBGE | https://ftp.ibge.gov.br | Downloads diretos |
| SIDRA | https://sidra.ibge.gov.br | Tabelas agregadas |
| API IBGE | https://servicodados.ibge.gov.br/api/docs | Documentação APIs |
| Cidades IBGE | https://cidades.ibge.gov.br | Perfil municipal |

### Dados Complementares

| Fonte | URL | Uso |
|-------|-----|-----|
| Atlas Brasil | http://www.atlasbrasil.org.br | IDHM e indicadores sociais |
| Base dos Dados | https://basedosdados.org | Dados tratados e padronizados |
| Portal Dados Abertos | https://dados.gov.br | Catálogo governamental |
| GitHub Municípios | https://github.com/kelvins/municipios-brasileiros | Coordenadas consolidadas |

### Documentação Técnica

- [API SIDRA - Documentação](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3)
- [API Localidades](https://servicodados.ibge.gov.br/api/docs/localidades)
- [Códigos de Municípios IBGE](https://www.ibge.gov.br/explica/codigos-dos-municipios.php)

---

## 10. Script de Carga Completa

```python
"""
Script para baixar e consolidar dados do IBGE para enriquecimento B2B.

Dependências:
    pip install pandas requests sidrapy openpyxl
"""

import pandas as pd
import requests
from io import BytesIO
import sidrapy

class IBGEDataLoader:
    """Carregador de dados IBGE para plataforma B2B."""

    def __init__(self, output_dir: str = "./data/ibge"):
        self.output_dir = output_dir

    def baixar_populacao(self) -> pd.DataFrame:
        """Baixa população do Censo 2022 via SIDRA."""
        print("Baixando população Censo 2022...")

        data = sidrapy.get_table(
            table_code="9514",
            territorial_level="6",
            ibge_territorial_code="all",
            variable="93",
            period="last 1"
        )

        df = pd.DataFrame(data[1:], columns=data[0])
        df = df[['Cód.', 'Município', 'Valor']].copy()
        df.columns = ['codigo_municipio', 'nome', 'populacao']
        df['populacao'] = pd.to_numeric(df['populacao'], errors='coerce')

        return df

    def baixar_pib(self, ano: int = 2023) -> pd.DataFrame:
        """Baixa PIB municipal do FTP IBGE."""
        print(f"Baixando PIB municipal {ano}...")

        url = f"https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/xlsx/tabelas_completas_{ano}.xlsx"
        response = requests.get(url)
        df = pd.read_excel(BytesIO(response.content), skiprows=3)

        return df

    def baixar_coordenadas(self) -> pd.DataFrame:
        """Baixa coordenadas das sedes municipais."""
        print("Baixando coordenadas municipais...")

        url = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"
        df = pd.read_csv(url)

        return df[[
            'codigo_ibge', 'nome', 'uf',
            'latitude', 'longitude', 'capital', 'ddd'
        ]]

    def consolidar(self) -> pd.DataFrame:
        """Consolida todos os dados em uma única tabela."""
        pop = self.baixar_populacao()
        pib = self.baixar_pib()
        coords = self.baixar_coordenadas()

        # Merge
        df = coords.merge(
            pop[['codigo_municipio', 'populacao']],
            left_on='codigo_ibge',
            right_on='codigo_municipio',
            how='left'
        )

        # Adicionar PIB (requer ajuste de colunas conforme arquivo real)
        # df = df.merge(pib, ...)

        return df

    def salvar(self, df: pd.DataFrame, nome: str = "municipios_enriquecidos"):
        """Salva dados em CSV e PostgreSQL-ready."""
        import os
        os.makedirs(self.output_dir, exist_ok=True)

        # CSV
        csv_path = f"{self.output_dir}/{nome}.csv"
        df.to_csv(csv_path, index=False)
        print(f"Salvo: {csv_path}")

        # SQL COPY format
        sql_path = f"{self.output_dir}/{nome}.sql"
        with open(sql_path, 'w') as f:
            f.write(f"-- Tabela de municípios enriquecida com dados IBGE\n")
            f.write(f"-- Gerado automaticamente\n\n")
            f.write(f"COPY municipios_ibge FROM '{csv_path}' WITH CSV HEADER;\n")

        print(f"Salvo: {sql_path}")


if __name__ == "__main__":
    loader = IBGEDataLoader()

    # Baixar individualmente
    pop = loader.baixar_populacao()
    coords = loader.baixar_coordenadas()

    print(f"\nResumo:")
    print(f"- População: {len(pop)} municípios")
    print(f"- Coordenadas: {len(coords)} municípios")
    print(f"- População Brasil: {pop['populacao'].sum():,.0f} habitantes")
```

---

## 11. Registro de Validação

> Este documento foi validado em **2026-01-28**. Ver detalhes completos em:
> `/home/akira/cnpj-data-pipeline/docs/fontes/ibge/VALIDACAO.md`

### Resumo da Validação

| Categoria | Status |
|-----------|--------|
| URLs FTP IBGE | 100% OK |
| APIs IBGE | 100% OK |
| GitHub (coordenadas) | OK |
| Atlas Brasil (atlasbrasil.org.br) | OFFLINE |
| Base dos Dados (IDHM) | OK |

**Amostras baixadas em:** `/home/akira/cnpj-data-pipeline/docs/fontes/ibge/`

---

*Documentação atualizada em: 2026-01-28*
*Autor: Equipe B2Pro*
*Validação: Claude Code*
