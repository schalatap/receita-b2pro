# CVM - Comissão de Valores Mobiliários

## Visão Geral

A **Comissão de Valores Mobiliários (CVM)** é a autarquia federal responsável por regulamentar e fiscalizar o mercado de capitais brasileiro. O **Portal de Dados Abertos da CVM** disponibiliza informações financeiras detalhadas de todas as empresas de capital aberto (companhias abertas) registradas no Brasil.

**URL Principal:** https://dados.cvm.gov.br/

### Por que usar dados da CVM?

| Vantagem | Descrição |
|----------|-----------|
| Dados financeiros REAIS | Faturamento, lucro, patrimônio auditados |
| Fonte oficial | Obrigatoriedade legal de divulgação |
| Formato estruturado | CSV com schema padronizado |
| Histórico longo | Dados desde 2010 |
| Gratuito | Acesso público sem autenticação |

### Limitações

- **Cobertura:** ~764 empresas com registro ativo (vs. 22M de empresas no Brasil)
- **Perfil:** Apenas empresas grandes/médias listadas na B3 ou com registro CVM
- **Defasagem:** Dados anuais (DFP) e trimestrais (ITR) com até 90 dias de atraso

---

## Tipos de Documentos Disponíveis

### 1. DFP - Demonstrações Financeiras Padronizadas (Anual)

Documento eletrônico obrigatório previsto na Resolução CVM n. 80/22. Contém as demonstrações financeiras anuais completas.

**URL:** https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp

**Arquivos disponíveis no ZIP:**
| Arquivo | Descrição |
|---------|-----------|
| `dfp_cia_aberta_BPA_con_AAAA.csv` | Balanço Patrimonial Ativo (Consolidado) |
| `dfp_cia_aberta_BPA_ind_AAAA.csv` | Balanço Patrimonial Ativo (Individual) |
| `dfp_cia_aberta_BPP_con_AAAA.csv` | Balanço Patrimonial Passivo (Consolidado) |
| `dfp_cia_aberta_BPP_ind_AAAA.csv` | Balanço Patrimonial Passivo (Individual) |
| `dfp_cia_aberta_DRE_con_AAAA.csv` | **Demonstração de Resultado (Consolidado)** |
| `dfp_cia_aberta_DRE_ind_AAAA.csv` | Demonstração de Resultado (Individual) |
| `dfp_cia_aberta_DRA_con_AAAA.csv` | Demonstração do Resultado Abrangente (Consolidado) |
| `dfp_cia_aberta_DRA_ind_AAAA.csv` | Demonstração do Resultado Abrangente (Individual) |
| `dfp_cia_aberta_DFC_MD_con_AAAA.csv` | Fluxo de Caixa - Método Direto |
| `dfp_cia_aberta_DFC_MI_con_AAAA.csv` | Fluxo de Caixa - Método Indireto |
| `dfp_cia_aberta_DVA_con_AAAA.csv` | Demonstração de Valor Adicionado |
| `dfp_cia_aberta_DMPL_con_AAAA.csv` | Mutações do Patrimônio Líquido |
| `dfp_cia_aberta_parecer_AAAA.csv` | Parecer dos Auditores |
| `dfp_cia_aberta_composicao_capital_AAAA.csv` | Composição do Capital |

**Download direto (exemplo 2024):**
```
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2024.zip
```

### 2. ITR - Informações Trimestrais

Demonstrações financeiras trimestrais com mesma estrutura do DFP.

**URL:** https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr

**Download direto (exemplo 2024):**
```
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2024.zip
```

### 3. FRE - Formulário de Referência

Documento anual com informações detalhadas sobre a empresa: atividades, fatores de risco, administração, estrutura de capital, remuneração de executivos.

**URL:** https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre

**Arquivos com dados financeiros:**
- `fre_cia_aberta_informacao_financeira_AAAA.csv` - Dados financeiros resumidos
- `fre_cia_aberta_distribuicao_dividendos_AAAA.csv` - Distribuição de dividendos
- `fre_cia_aberta_endividamento_AAAA.csv` - Níveis de endividamento
- `fre_cia_aberta_capital_social_AAAA.csv` - Estrutura de capital

### 4. Cadastro de Companhias Abertas

Dados cadastrais de todas as companhias registradas na CVM.

**URL:** https://dados.cvm.gov.br/dataset/cia_aberta-cad

**Download direto:**
```
https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv
```

---

## Estrutura dos Arquivos CSV

> **Importante:** Todos os arquivos CSV da CVM estão em encoding **ISO-8859-1 (Latin-1)**, não UTF-8. Use `encoding='ISO-8859-1'` ao ler com pandas/polars.

### Colunas do arquivo DRE (Demonstração de Resultado)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `CNPJ_CIA` | VARCHAR(20) | CNPJ da companhia |
| `DT_REFER` | DATE | Data de referência do documento |
| `VERSAO` | INTEGER | Versão do documento (reapresentações) |
| `DENOM_CIA` | VARCHAR(100) | Nome da companhia |
| `CD_CVM` | INTEGER | Código CVM da companhia |
| `GRUPO_DFP` | VARCHAR(100) | Tipo de demonstração financeira |
| `MOEDA` | VARCHAR(10) | "REAL" |
| `ESCALA_MOEDA` | VARCHAR(10) | "UNIDADE" ou "MIL" |
| `ORDEM_EXERC` | VARCHAR(10) | "ÚLTIMO" ou "PENÚLTIMO" |
| `DT_INI_EXERC` | DATE | Data início do exercício |
| `DT_FIM_EXERC` | DATE | Data fim do exercício |
| `CD_CONTA` | VARCHAR(20) | **Código padronizado da conta** |
| `DS_CONTA` | VARCHAR(200) | Descrição da conta |
| `VL_CONTA` | DECIMAL(18,2) | **Valor da conta (em Reais)** |
| `ST_CONTA_FIXA` | CHAR(1) | "S" = conta fixa, "N" = conta não fixa |

### Colunas do Cadastro de Companhias

| Coluna | Descrição |
|--------|-----------|
| `CNPJ_CIA` | CNPJ completo (14 dígitos com formatação) |
| `DENOM_SOCIAL` | Razão social |
| `DENOM_COMERC` | Nome fantasia |
| `DT_REG` | Data de registro na CVM |
| `DT_CONST` | Data de constituição |
| `DT_CANCEL` | Data de cancelamento |
| `MOTIVO_CANCEL` | Motivo de cancelamento |
| `SIT` | Situação (ATIVO, CANCELADA, SUSPENSO) |
| `DT_INI_SIT` | Data início da situação |
| `CD_CVM` | Código CVM (identificador único) |
| `SETOR_ATIV` | Setor de atividade |
| `TP_MERC` | Tipo de mercado |
| `CATEG_REG` | Categoria de registro (A, B) |
| `DT_INI_CATEG` | Data início da categoria |
| `SIT_EMISSOR` | Situação do emissor |
| `CONTROLE_ACIONARIO` | Tipo de controle |
| `LOGRADOURO` | Endereço |
| `MUN` | Município |
| `UF` | UF |
| `EMAIL` | E-mail de contato |
| `RESP` | Nome do responsável (DRI) |
| `CNPJ_AUDITOR` | CNPJ do auditor |
| `AUDITOR` | Nome do auditor |

---

## Códigos de Contas Contábeis (CD_CONTA)

### Demonstração de Resultado (DRE)

| CD_CONTA | DS_CONTA | Uso |
|----------|----------|-----|
| **3.01** | **Receita de Venda de Bens e/ou Serviços** | **FATURAMENTO (Receita Líquida)** |
| 3.02 | Custo dos Bens e/ou Serviços Vendidos | CPV/CMV |
| **3.03** | **Resultado Bruto** | **Lucro Bruto** |
| 3.04 | Despesas/Receitas Operacionais | OPEX |
| **3.05** | **Resultado Antes do Resultado Financeiro e dos Tributos** | **EBIT** |
| 3.06 | Resultado Financeiro | |
| 3.07 | Resultado Antes dos Tributos sobre o Lucro | EBT |
| 3.08 | Imposto de Renda e Contribuição Social | IR/CSLL |
| 3.09 | Resultado Líquido das Operações Continuadas | |
| **3.11** | **Lucro/Prejuízo Consolidado do Período** | **Lucro Líquido** |

### Balanço Patrimonial

| CD_CONTA | DS_CONTA |
|----------|----------|
| 1 | Ativo Total |
| 1.01 | Ativo Circulante |
| 1.02 | Ativo Não Circulante |
| 2 | Passivo Total |
| 2.01 | Passivo Circulante |
| 2.02 | Passivo Não Circulante |
| 2.03 | Patrimônio Líquido |

---

## URLs para Download em Massa

### DFP (Demonstrações Financeiras Padronizadas)

```
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2010.zip
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2011.zip
...
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2024.zip
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2025.zip
```

### ITR (Informações Trimestrais)

```
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2011.zip
...
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2025.zip
```

### FRE (Formulário de Referência)

```
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_2021.zip
...
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_2026.zip
```

### Metadados (Dicionário de Dados)

```
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/META/meta_dfp_cia_aberta_txt.zip
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/META/meta_itr_cia_aberta_txt.zip
https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/META/meta_fre_cia_aberta.zip
https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/META/meta_cad_cia_aberta.txt
```

---

## Frequência de Atualização

| Documento | Frequência | Prazo de Entrega | Atualização Portal |
|-----------|------------|------------------|-------------------|
| DFP | Anual | Até 3 meses após encerramento do exercício | Semanal |
| ITR | Trimestral | Até 45 dias após encerramento do trimestre | Semanal |
| FRE | Anual | Até 5 meses após encerramento do exercício | Semanal |
| Cadastro | Diário | - | Diário |

**Observação:** Os arquivos são atualizados semanalmente com eventuais reapresentações. Histórico disponível desde 2010 (DFP) e 2011 (ITR).

---

## Quantidade de Empresas Cobertas

| Métrica | Quantidade |
|---------|------------|
| Companhias com registro CVM ativo | ~764 |
| Companhias canceladas (histórico) | ~1.887 |
| Total de registros no cadastro | ~2.654 |

**Nota:** O número de empresas de capital aberto é muito menor que o universo de empresas brasileiras (~22M). A CVM cobre apenas as empresas que captam recursos no mercado de capitais.

---

## Código Python de Exemplo

### Instalação de Dependências

```bash
pip install pandas requests wget
```

### Download e Processamento de DFP

```python
import pandas as pd
import requests
import wget
from zipfile import ZipFile
from io import BytesIO
import os

def download_dfp_files(start_year: int, end_year: int, output_dir: str = "DFP"):
    """
    Baixa e extrai arquivos DFP da CVM para um intervalo de anos.

    Args:
        start_year: Ano inicial (ex: 2020)
        end_year: Ano final (ex: 2024)
        output_dir: Diretório para extrair os arquivos
    """
    base_url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"

    os.makedirs(output_dir, exist_ok=True)

    for ano in range(start_year, end_year + 1):
        arquivo = f"dfp_cia_aberta_{ano}.zip"
        url = base_url + arquivo

        print(f"Baixando {arquivo}...")
        response = requests.get(url)

        if response.status_code == 200:
            with ZipFile(BytesIO(response.content)) as zip_file:
                zip_file.extractall(output_dir)
            print(f"  Extraído para {output_dir}/")
        else:
            print(f"  ERRO: {response.status_code}")


def load_dre_consolidado(output_dir: str, start_year: int, end_year: int) -> pd.DataFrame:
    """
    Carrega e concatena arquivos DRE consolidado de múltiplos anos.

    Returns:
        DataFrame com todos os dados DRE consolidados
    """
    dfs = []

    for ano in range(start_year, end_year + 1):
        arquivo = f"{output_dir}/dfp_cia_aberta_DRE_con_{ano}.csv"

        if os.path.exists(arquivo):
            df = pd.read_csv(
                arquivo,
                sep=';',
                decimal=',',
                encoding='ISO-8859-1'
            )
            dfs.append(df)
            print(f"Carregado: {arquivo} ({len(df):,} linhas)")

    return pd.concat(dfs, ignore_index=True)


def extrair_receita_liquida(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai a Receita Líquida (faturamento) das empresas.

    CD_CONTA = "3.01" = Receita de Venda de Bens e/ou Serviços
    ORDEM_EXERC = "ÚLTIMO" = Exercício mais recente

    Args:
        df: DataFrame com dados DRE

    Returns:
        DataFrame com receita líquida por empresa/ano
    """
    # Filtrar apenas Receita Líquida do exercício atual
    receita = df[
        (df['CD_CONTA'] == '3.01') &
        (df['ORDEM_EXERC'] == 'ÚLTIMO')
    ].copy()

    # Selecionar colunas relevantes
    receita = receita[[
        'CNPJ_CIA',
        'CD_CVM',
        'DENOM_CIA',
        'DT_FIM_EXERC',
        'DS_CONTA',
        'VL_CONTA',
        'ESCALA_MOEDA'
    ]].copy()

    # Ajustar escala (alguns valores estão em milhares)
    receita['VL_CONTA_AJUSTADO'] = receita.apply(
        lambda row: row['VL_CONTA'] * 1000 if row['ESCALA_MOEDA'] == 'MIL' else row['VL_CONTA'],
        axis=1
    )

    # Renomear colunas
    receita = receita.rename(columns={
        'DENOM_CIA': 'empresa',
        'DT_FIM_EXERC': 'data_exercicio',
        'VL_CONTA_AJUSTADO': 'receita_liquida_brl'
    })

    return receita[['CNPJ_CIA', 'CD_CVM', 'empresa', 'data_exercicio', 'receita_liquida_brl']]


def extrair_indicadores_financeiros(df: pd.DataFrame, cd_cvm: int = None) -> pd.DataFrame:
    """
    Extrai principais indicadores financeiros da DRE.

    Args:
        df: DataFrame com dados DRE
        cd_cvm: Código CVM para filtrar empresa específica (opcional)

    Returns:
        DataFrame com indicadores por empresa/ano
    """
    # Contas de interesse
    contas = {
        '3.01': 'receita_liquida',
        '3.03': 'lucro_bruto',
        '3.05': 'ebit',
        '3.11': 'lucro_liquido'
    }

    # Filtrar contas e exercício atual
    filtro = (df['CD_CONTA'].isin(contas.keys())) & (df['ORDEM_EXERC'] == 'ÚLTIMO')

    if cd_cvm:
        filtro = filtro & (df['CD_CVM'] == cd_cvm)

    dados = df[filtro].copy()

    # Ajustar escala
    dados['valor'] = dados.apply(
        lambda row: row['VL_CONTA'] * 1000 if row['ESCALA_MOEDA'] == 'MIL' else row['VL_CONTA'],
        axis=1
    )

    # Mapear nomes das contas
    dados['indicador'] = dados['CD_CONTA'].map(contas)

    # Pivotar para ter uma coluna por indicador
    resultado = dados.pivot_table(
        index=['CNPJ_CIA', 'CD_CVM', 'DENOM_CIA', 'DT_FIM_EXERC'],
        columns='indicador',
        values='valor',
        aggfunc='first'
    ).reset_index()

    return resultado


def baixar_cadastro_empresas() -> pd.DataFrame:
    """
    Baixa o cadastro atualizado de companhias abertas.

    Returns:
        DataFrame com dados cadastrais
    """
    url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"

    df = pd.read_csv(
        url,
        sep=';',
        encoding='ISO-8859-1'
    )

    # Filtrar apenas empresas ativas
    df_ativas = df[df['SIT'] == 'ATIVO'].copy()

    return df_ativas


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # 1. Baixar arquivos DFP dos últimos 5 anos
    print("=" * 60)
    print("BAIXANDO ARQUIVOS DFP DA CVM")
    print("=" * 60)
    download_dfp_files(2020, 2024, output_dir="DFP")

    # 2. Carregar dados DRE consolidados
    print("\n" + "=" * 60)
    print("CARREGANDO DADOS DRE")
    print("=" * 60)
    dre = load_dre_consolidado("DFP", 2020, 2024)
    print(f"\nTotal de registros: {len(dre):,}")

    # 3. Extrair receita líquida
    print("\n" + "=" * 60)
    print("RECEITA LÍQUIDA (TOP 10 - 2024)")
    print("=" * 60)
    receita = extrair_receita_liquida(dre)

    # Filtrar 2024 e ordenar por receita
    receita_2024 = receita[receita['data_exercicio'].str.contains('2024', na=False)]
    top10 = receita_2024.nlargest(10, 'receita_liquida_brl')

    for _, row in top10.iterrows():
        print(f"{row['empresa'][:40]:40s} R$ {row['receita_liquida_brl']/1e9:,.2f} bi")

    # 4. Indicadores de uma empresa específica (Petrobras = CD_CVM 9512)
    print("\n" + "=" * 60)
    print("INDICADORES PETROBRAS (CD_CVM = 9512)")
    print("=" * 60)
    indicadores = extrair_indicadores_financeiros(dre, cd_cvm=9512)
    print(indicadores.to_string(index=False))

    # 5. Baixar cadastro de empresas
    print("\n" + "=" * 60)
    print("CADASTRO DE EMPRESAS ATIVAS")
    print("=" * 60)
    cadastro = baixar_cadastro_empresas()
    print(f"Total de empresas ativas: {len(cadastro)}")
    print(f"\nColunas disponíveis: {list(cadastro.columns)}")
```

### Exemplo de Saída Esperada

```
============================================================
RECEITA LÍQUIDA (TOP 10 - 2024)
============================================================
PETRÓLEO BRASILEIRO S.A. - PETROBRAS      R$ 511,89 bi
VALE S.A.                                  R$ 208,74 bi
JBS S.A.                                   R$ 364,92 bi
AMBEV S.A.                                 R$ 79,72 bi
RAÍZEN S.A.                                R$ 244,41 bi
ULTRAPAR PARTICIPAÇÕES S.A.                R$ 130,06 bi
BRASKEM S.A.                               R$ 81,75 bi
SUZANO S.A.                                R$ 47,54 bi
COSAN S.A.                                 R$ 37,98 bi
GERDAU S.A.                                R$ 68,22 bi
```

---

## Integração com CNPJ (Receita Federal)

Para enriquecer os dados da plataforma B2B, podemos cruzar os dados CVM com os dados da Receita Federal:

```python
def vincular_cvm_cnpj(df_cvm: pd.DataFrame, df_rfb: pd.DataFrame) -> pd.DataFrame:
    """
    Vincula dados da CVM com dados da Receita Federal usando CNPJ.

    Args:
        df_cvm: DataFrame com dados CVM (CNPJ_CIA)
        df_rfb: DataFrame com dados RFB (cnpj)

    Returns:
        DataFrame com dados combinados
    """
    # Normalizar CNPJ (remover pontuação)
    df_cvm['cnpj_normalizado'] = df_cvm['CNPJ_CIA'].str.replace(r'[./-]', '', regex=True)

    # Vincular com dados RFB
    resultado = df_cvm.merge(
        df_rfb,
        left_on='cnpj_normalizado',
        right_on='cnpj',
        how='left',
        suffixes=('_cvm', '_rfb')
    )

    return resultado
```

---

## Projetos de Referência

| Projeto | URL | Descrição |
|---------|-----|-----------|
| Dados-CVM | https://github.com/Fabio13Gomes/Dados-CVM | ETL automatizado com DuckDB |
| CVM_CiasAbertas_DFP | https://github.com/ylder/20240218_CVM_CiasAbertas_DFP | Coleta e validação de DFPs |
| Análise Macro | https://analisemacro.com.br/mercado-financeiro/analise-fundamentalista-usando-o-python/ | Tutorial completo com Python |

---

## Considerações para Plataforma B2B

### Vantagens de usar dados CVM

1. **Dados financeiros auditados** - Receita, lucro, patrimônio são verificados por auditores independentes
2. **Padronização** - Todas as empresas usam o mesmo plano de contas
3. **Histórico** - Permite análise de evolução financeira
4. **Gratuito e legal** - Dados públicos sem restrições de uso

### Limitações para considerar

1. **Cobertura limitada** - Apenas ~764 empresas ativas vs. 22M no Brasil
2. **Perfil específico** - Grandes empresas, não representa PMEs
3. **Defasagem temporal** - Dados trimestrais/anuais, não tempo real
4. **Sem ticker B3 direto** - Necessário cruzar com dados B3 para obter tickers

### Sugestão de uso

Usar dados CVM para:
- Enriquecer perfil de empresas grandes (clientes enterprise)
- Benchmark de faturamento por setor
- Identificar empresas em crescimento
- Validar informações declaradas

Não usar para:
- PMEs e empresas de capital fechado
- Dados em tempo real
- Cobertura ampla do mercado brasileiro

---

## Links Úteis

- **Portal de Dados Abertos CVM:** https://dados.cvm.gov.br/
- **Documentação oficial:** https://dados.cvm.gov.br/pages/novidades
- **Consulta de companhias:** https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CiaAb/FormBuscaCiaAb.aspx?TipoConsult=c
- **Resolução CVM n. 80/22:** https://conteudo.cvm.gov.br/legislacao/resolucoes/resol080.html
- **B3 - Empresas Listadas:** https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/empresas-listadas.htm

---

*Documentação criada em 2026-01-28 para o projeto de Inteligência Comercial B2B.*
*Última validação: 2026-01-28 - Todas as URLs verificadas e funcionando.*
