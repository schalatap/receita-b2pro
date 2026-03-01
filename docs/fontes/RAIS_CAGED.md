# RAIS e CAGED - Dados de Emprego Formal no Brasil

## Visão Geral

Este documento descreve as fontes de dados de emprego formal do Ministério do Trabalho e Emprego (MTE), com foco na possibilidade de obter o número de funcionários por empresa (CNPJ) para estimativa de faturamento em plataformas de inteligência comercial B2B.

**Conclusão Antecipada:** Os microdados públicos da RAIS e CAGED **não contêm CNPJ identificado**. Para obter número de funcionários por empresa específica, é necessário:
1. Solicitar acesso aos dados identificados (restrito a pesquisa acadêmica/governamental)
2. Usar fontes alternativas (LinkedIn, estimativas por porte, APIs comerciais)

> **Validação:** URLs e FTP verificados em 2026-01-28. Ver detalhes em [rais_caged/VALIDACAO.md](./rais_caged/VALIDACAO.md).

---

## 1. RAIS - Relação Anual de Informações Sociais

### O que é

A RAIS é um registro administrativo de periodicidade anual, instituída pelo Decreto nº 76.900/1975. Contém informações sobre todos os vínculos empregatícios formais no Brasil.

### Objetivos Oficiais

- Controle da atividade trabalhista no país
- Provimento de dados para estatísticas do trabalho
- Informações para o Seguro-Desemprego e Abono Salarial
- Base para estudos e pesquisas sobre mercado de trabalho

### Cobertura

| Incluídos | Não Incluídos |
|-----------|---------------|
| Celetistas (CLT) | Trabalhadores informais |
| Servidores públicos | Autônomos |
| Trabalhadores avulsos | Estagiários |
| Aprendizes | Trabalho doméstico informal |
| Dirigentes sindicais | MEI sem empregados |

### Volume de Dados (2024)

- **46,3 milhões** de vínculos empregatícios ativos
- Remuneração média: R$ 3.706,90
- Crescimento de +4,0% em relação a 2023

### URLs Oficiais

| Recurso | URL |
|---------|-----|
| Portal RAIS | https://www.rais.gov.br/sitio/sobre.jsf |
| Estatísticas | https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/rais |
| Microdados | https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged |

---

## 2. CAGED - Cadastro Geral de Empregados e Desempregados

### O que é

O CAGED registra admissões e desligamentos de empregados sob o regime CLT. Foi criado em 1965 para acompanhar e fiscalizar o processo de admissão e dispensa de trabalhadores.

### Novo CAGED

Desde janeiro de 2020, o "Novo CAGED" substituiu o antigo sistema para empresas obrigadas ao eSocial. A coleta passou a ser feita automaticamente via eventos do eSocial.

### Diferença entre RAIS e CAGED

| Característica | RAIS | CAGED |
|----------------|------|-------|
| Periodicidade | Anual | Mensal |
| Foco | Estoque de empregos | Fluxo (admissões/demissões) |
| Dados | Posição em 31/12 | Movimentações mensais |
| Uso principal | Pesquisas, abono salarial | Seguro-desemprego, conjuntura |

### URLs Oficiais

| Recurso | URL |
|---------|-----|
| Portal CAGED | https://caged.maisemprego.mte.gov.br/portalcaged/ |
| Estatísticas | https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho |

---

## 3. eSocial e Impactos nos Dados

### O que mudou

O eSocial unificou a prestação de informações trabalhistas, previdenciárias e fiscais. A RAIS e o CAGED não deixaram de existir, mas a forma de coleta mudou.

### Cronograma de Substituição

| Obrigação | Data de Substituição | Grupos Afetados |
|-----------|---------------------|-----------------|
| CAGED | Janeiro/2020 | Grupos 1, 2 e 3 |
| RAIS | Ano-base 2019 | Grupos 1 e 2 |
| RAIS | Ano-base 2024 | Todos (grupos 1-4) |

### Benefícios da Unificação

- Integração com outras bases (CNPJ, CPF, NIS)
- Dados mais detalhados sobre segurança e saúde no trabalho
- Redução de inconsistências
- Série histórica preservada

### Fonte

- [eSocial - Substituição de Obrigações](https://www.gov.br/esocial/pt-br/noticias/substituicao-de-obrigacoes-dados-do-esocial-passaram-a-alimentar-o-caged-e-a-rais-para-obrigados)

---

## 4. Dados Disponíveis Publicamente

### Microdados Não Identificados (Público)

O MTE disponibiliza microdados **anonimizados** via FTP:

```
ftp://ftp.mtps.gov.br/pdet/microdados/
```

**Estrutura do FTP (validada em 2026-01-28):**
```
/pdet/microdados/
├── RAIS/
│   ├── 1985 a 2024 (40 pastas anuais)
│   ├── 2023 Parcial/
│   ├── 2024 Parcial/
│   └── Layouts/
│       ├── estabelecimento/
│       └── vínculos/
├── CAGED/
│   └── 2007 a 2019 (CAGED antigo)
├── NOVO CAGED/
│   └── 2020 a 2025 (por ano/mês)
├── CAGED_AJUSTES/
│   └── 2002 a 2020
├── TRABALHO_DOMESTICO/
│   └── 2015 a 2024
├── COMUNICADO_microdados.pdf
└── NOTA_TECNICA_microdados.pdf
```

> **Nota:** O FTP usa encoding latin-1 (ISO-8859-1). Ao conectar via Python, use `ftplib.FTP(host, encoding='latin-1')`.

### O que ESTÁ disponível nos microdados públicos

| Variável | Disponível | Observação |
|----------|------------|------------|
| UF | Sim | Código IBGE |
| Município | Sim | Código IBGE |
| CNAE | Sim | Subclasse (7 dígitos) |
| Natureza Jurídica | Sim | Código |
| Porte | Sim | Faixas (micro, pequena, etc.) |
| Quantidade de funcionários | Sim | **Por faixas**, não exato |
| Remuneração | Sim | Valores individuais |
| Sexo, idade, escolaridade | Sim | Do trabalhador |
| Tempo de emprego | Sim | Em meses |

### O que NÃO está disponível nos microdados públicos

| Variável | Motivo |
|----------|--------|
| CNPJ | LGPD / Sigilo |
| CPF/PIS do trabalhador | LGPD / Sigilo |
| Razão Social | LGPD / Sigilo |
| Endereço completo | LGPD / Sigilo |
| Nome do trabalhador | LGPD / Sigilo |

### Arquivos Disponíveis - RAIS 2024 (validado em 2026-01-28)

| Arquivo | Tamanho | Descrição |
|---------|---------|-----------|
| RAIS_ESTAB_PUB.7z | 127 MB | Estabelecimentos (todas UFs) |
| RAIS_VINC_PUB_SP.7z | 1.002 MB | Vínculos - São Paulo |
| RAIS_VINC_PUB_MG_ES_RJ.7z | - | Vínculos - MG, ES, RJ |
| RAIS_VINC_PUB_SUL.7z | - | Vínculos - Sul |
| RAIS_VINC_PUB_NORDESTE.7z | - | Vínculos - Nordeste |
| RAIS_VINC_PUB_NORTE.7z | - | Vínculos - Norte |
| RAIS_VINC_PUB_CENTRO_OESTE.7z | - | Vínculos - Centro-Oeste |
| RAIS_VINC_PUB_NI.7z | - | Vínculos - Não Identificados |

### Faixas de Tamanho de Estabelecimento (RAIS)

Os microdados públicos incluem a variável `TAMESTAB` com faixas:

| Código | Faixa de Funcionários |
|--------|----------------------|
| 1 | 0 funcionários |
| 2 | 1 a 4 |
| 3 | 5 a 9 |
| 4 | 10 a 19 |
| 5 | 20 a 49 |
| 6 | 50 a 99 |
| 7 | 100 a 249 |
| 8 | 250 a 499 |
| 9 | 500 a 999 |
| 10 | 1000 ou mais |

---

## 5. Dados Identificados (Acesso Restrito)

### Quem Pode Solicitar

- Órgãos públicos (federal, estadual, municipal)
- Entidades da sociedade civil (sem fins lucrativos)
- Sistema "S" (SENAI, SEBRAE, etc.)
- Pesquisadores vinculados a instituições elegíveis

**Empresas privadas com fins comerciais NÃO têm acesso.**

### Documentos Necessários

1. CNPJ e contrato social da instituição
2. Ofício formal de solicitação
3. Documento de nomeação do responsável
4. Minuta de Instrumento de Cooperação com Plano de Trabalho
5. Termo de Compromisso e Manutenção de Sigilo

### Tipos de Acordo

| Tipo | Público-Alvo |
|------|--------------|
| ACT (Acordo de Cooperação Técnica) | Órgãos públicos |
| AC (Acordo de Cooperação) | Entidades da sociedade civil |

### Contato para Solicitação

- **Email:** estatisticastrabalho@trabalho.gov.br
- **Portal:** https://www.gov.br/pt-br/servicos/solicitar-acesso-aos-dados-identificados-rais-e-caged

### Base Legal

- Lei 12.527/2011 (Lei de Acesso à Informação)
- Lei 13.709/2018 (LGPD)
- Portaria MTP 671/2021 (Arts. 163-178-B)
- Portaria SEPRT 24.445/2020

---

## 6. Base dos Dados (BigQuery)

A organização [Base dos Dados](https://basedosdados.org) disponibiliza os microdados da RAIS tratados e prontos para consulta via Google BigQuery.

### Características

| Item | Valor |
|------|-------|
| Período | 1985-2024 |
| Tamanho | +350 GB |
| Formato | BigQuery (SQL) |
| Custo | Gratuito (até 1 TB/mês) |
| CNPJ | **Não disponível** |

### Tabelas Disponíveis

1. `br_me_rais.microdados_vinculos` - Vínculos empregatícios
2. `br_me_rais.microdados_estabelecimentos` - Dados de estabelecimentos
3. `br_me_rais.dicionario` - Dicionário de variáveis

### Limitação Importante

> Os microdados da Base dos Dados **não contêm CNPJ ou CPF**, impossibilitando cruzamento direto com outras bases.

### Exemplo de Consulta SQL

```sql
-- Contagem de vínculos por UF e CNAE (seção) em 2023
SELECT
  sigla_uf,
  SUBSTR(cnae_2, 1, 2) AS cnae_secao,
  COUNT(*) AS total_vinculos
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano = 2023
  AND vinculo_ativo_3112 = 1  -- Ativos em 31/12
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 20;
```

### Acesso via Python

```python
import basedosdados as bd

# Configurar billing (conta Google Cloud)
bd.set_billing_project_id("seu-projeto-gcp")

# Consultar dados
query = """
SELECT sigla_uf, COUNT(*) as total
FROM `basedosdados.br_me_rais.microdados_vinculos`
WHERE ano = 2023
GROUP BY 1
"""

df = bd.read_sql(query)
print(df)
```

### Instalação

```bash
pip install basedosdados
```

---

## 7. Alternativas para Estimar Número de Funcionários

Como os dados identificados da RAIS/CAGED são restritos, existem alternativas para estimar o número de funcionários por empresa:

### 7.1. Porte da Empresa (Receita Federal)

A Receita Federal disponibiliza o campo `porte` nos dados abertos do CNPJ:

| Código | Porte | Estimativa de Funcionários |
|--------|-------|---------------------------|
| 00 | Não informado | - |
| 01 | Micro Empresa (ME) | 1-9 |
| 03 | Empresa de Pequeno Porte (EPP) | 10-49 |
| 05 | Demais | 50+ |

**Limitação:** Classificação baseada em faturamento, não em funcionários.

### 7.2. Capital Social + CNAE (Estimativa)

Combinar capital social declarado com o setor de atividade para estimar:

```python
def estimar_funcionarios(capital_social: float, cnae: str) -> tuple[int, int]:
    """
    Retorna faixa estimada (min, max) de funcionários.
    Lógica simplificada - ajustar com dados reais.
    """
    # Setores intensivos em mão de obra
    setores_intensivos = ['47', '56', '86', '85']  # Varejo, alimentação, saúde, educação

    # Setores intensivos em capital
    setores_capital = ['35', '06', '19']  # Energia, petróleo, refinarias

    cnae_secao = cnae[:2]

    if capital_social < 50_000:
        base = (1, 5)
    elif capital_social < 500_000:
        base = (5, 20)
    elif capital_social < 5_000_000:
        base = (20, 100)
    else:
        base = (100, 500)

    # Ajuste por setor
    if cnae_secao in setores_intensivos:
        return (base[0] * 2, base[1] * 3)
    elif cnae_secao in setores_capital:
        return (base[0] // 2, base[1] // 2)

    return base
```

### 7.3. LinkedIn (Dados de Empresa)

O LinkedIn exibe o número de funcionários em páginas de empresas. Opções:

| Método | Custo | Confiabilidade | Legalidade |
|--------|-------|----------------|------------|
| API oficial LinkedIn | Alto (~$10k/mês) | Alta | Legal |
| Web scraping | Médio | Média | Zona cinza |
| Serviços terceiros (Bright Data, ScrapIn) | Médio | Alta | Delegada |

**Exemplo com ScrapIn API:**

```python
import requests

def get_linkedin_employees(company_url: str, api_key: str) -> int:
    """Obtém número de funcionários via ScrapIn API."""
    response = requests.get(
        "https://api.scrapin.io/company",
        params={"url": company_url},
        headers={"Authorization": f"Bearer {api_key}"}
    )
    data = response.json()
    return data.get("employee_count", 0)
```

### 7.4. Plataformas Comerciais

Concorrentes como Speedio, Econodata e Leads2b já oferecem esses dados. Possíveis fontes que utilizam:

- LinkedIn (scraping ou API)
- Glassdoor
- Indeed (vagas abertas)
- Dados proprietários de parceiros
- Modelos de machine learning

### 7.5. Vagas Abertas (Proxy)

Empresas com muitas vagas abertas tendem a ser maiores ou estar em crescimento:

```python
def estimar_por_vagas(vagas_abertas: int) -> tuple[int, int]:
    """
    Estima funcionários baseado em vagas abertas.
    Taxa típica de turnover/crescimento: 5-15% ao ano.
    """
    if vagas_abertas == 0:
        return (1, 50)  # Empresa estável ou pequena
    elif vagas_abertas < 5:
        return (20, 100)
    elif vagas_abertas < 20:
        return (100, 500)
    else:
        return (500, 5000)
```

---

## 8. Limitações e Considerações

### Limitações da RAIS/CAGED

1. **Apenas emprego formal (CLT)** - Não inclui sócios, PJ, autônomos
2. **Defasagem temporal** - RAIS final sai ~9 meses após ano-base
3. **Dados identificados restritos** - Não disponíveis para uso comercial
4. **Agregação por faixas** - Microdados públicos não têm número exato

### Considerações LGPD

A Lei Geral de Proteção de Dados (Lei 13.709/2018) impõe restrições ao uso de dados pessoais. Mesmo que os dados sejam obtidos:

- Número de funcionários por si só não é dado pessoal
- Cruzamento com outras bases pode identificar pessoas
- Uso comercial de dados públicos tem limitações

### Recomendação para Plataforma B2B

Para uma plataforma de inteligência comercial, recomendamos:

1. **Usar porte da RFB** como proxy inicial (já disponível nos dados do CNPJ)
2. **Enriquecer com LinkedIn** via API ou serviço terceiro
3. **Criar modelo de estimativa** usando CNAE + Capital Social + Porte
4. **Validar com dados reais** quando disponíveis (clientes, parceiros)

---

## 9. Código de Exemplo - Download de Microdados

### Baixar RAIS do FTP

```python
import ftplib
import os
from pathlib import Path

def download_rais_microdados(
    ano: int,
    tipo: str = "vinculos",
    destino: str = "./data/rais"
) -> list[Path]:
    """
    Baixa microdados da RAIS do FTP do MTE.

    Args:
        ano: Ano dos dados (ex: 2022)
        tipo: "vinculos" ou "estabelecimentos"
        destino: Pasta de destino

    Returns:
        Lista de arquivos baixados
    """
    FTP_HOST = "ftp.mtps.gov.br"
    FTP_PATH = f"/pdet/microdados/RAIS/{ano}"

    destino_path = Path(destino)
    destino_path.mkdir(parents=True, exist_ok=True)

    arquivos_baixados = []

    try:
        # IMPORTANTE: usar encoding latin-1 para nomes de arquivos com acentos
        ftp = ftplib.FTP(FTP_HOST, encoding='latin-1')
        ftp.login()  # Anonymous
        ftp.cwd(FTP_PATH)

        arquivos = ftp.nlst()

        for arquivo in arquivos:
            if tipo.lower() in arquivo.lower():
                local_path = destino_path / arquivo
                print(f"Baixando {arquivo}...")

                with open(local_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {arquivo}', f.write)

                arquivos_baixados.append(local_path)
                print(f"  Salvo em {local_path}")

        ftp.quit()

    except ftplib.all_errors as e:
        print(f"Erro FTP: {e}")
        raise

    return arquivos_baixados


# Uso
if __name__ == "__main__":
    arquivos = download_rais_microdados(2022, "vinculos")
    print(f"\n{len(arquivos)} arquivos baixados")
```

### Processar Microdados com Polars

```python
import polars as pl
from pathlib import Path

def processar_rais_vinculos(arquivo: Path) -> pl.DataFrame:
    """
    Processa arquivo de vínculos da RAIS.

    O layout pode variar por ano - consultar:
    ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/Layouts/
    """
    # Colunas principais (layout 2022)
    colunas = {
        "Município": pl.Utf8,
        "CNAE 2.0 Classe": pl.Utf8,
        "CNAE 2.0 Subclasse": pl.Utf8,
        "Vínculo Ativo 31/12": pl.Int8,
        "Qtd Hora Contrat": pl.Int16,
        "Sexo Trabalhador": pl.Int8,
        "Idade": pl.Int8,
        "Escolaridade após 2005": pl.Int8,
        "Tempo Emprego": pl.Float32,
        "Tamanho Estabelecimento": pl.Int8,
        "Natureza Jurídica": pl.Utf8,
        "Ind Simples": pl.Int8,
        "Vl Remun Média Nom": pl.Float64,
        "Vl Remun Dezembro Nom": pl.Float64,
    }

    df = pl.read_csv(
        arquivo,
        separator=";",
        encoding="latin1",
        dtypes=colunas,
        ignore_errors=True,
        low_memory=False
    )

    return df


def agregar_por_municipio_cnae(df: pl.DataFrame) -> pl.DataFrame:
    """
    Agrega vínculos por município e CNAE.
    """
    return (
        df.filter(pl.col("Vínculo Ativo 31/12") == 1)
        .group_by(["Município", "CNAE 2.0 Subclasse"])
        .agg([
            pl.count().alias("total_vinculos"),
            pl.col("Vl Remun Média Nom").mean().alias("remuneracao_media"),
            pl.col("Tempo Emprego").mean().alias("tempo_medio_emprego"),
        ])
        .sort("total_vinculos", descending=True)
    )


# Uso
if __name__ == "__main__":
    arquivo = Path("./data/rais/RAIS_VINC_PUB_SUL.txt")

    if arquivo.exists():
        df = processar_rais_vinculos(arquivo)
        print(f"Total de registros: {len(df):,}")

        agregado = agregar_por_municipio_cnae(df)
        print(agregado.head(20))
```

---

## 10. Referências

### Documentação Oficial

- [RAIS - Portal Oficial](https://www.rais.gov.br/sitio/sobre.jsf)
- [Microdados RAIS e CAGED - MTE](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged)
- [eSocial - Substituição de Obrigações](https://www.gov.br/esocial/pt-br/noticias/substituicao-de-obrigacoes-dados-do-esocial-passaram-a-alimentar-o-caged-e-a-rais-para-obrigados)
- [Solicitar Dados Identificados](https://www.gov.br/pt-br/servicos/solicitar-acesso-aos-dados-identificados-rais-e-caged)

### Bases de Dados

- [Base dos Dados - RAIS](https://basedosdados.org/dataset/3e7c4d58-96ba-448e-b053-d385a829ef00)
- [IBGE - Metadados RAIS](https://ces.ibge.gov.br/base-de-dados/metadados/mte/relacao-anual-de-informacoes-sociais-rais)
- [Dados Abertos da Receita Federal](https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos)

### Tutoriais e Análises

- [Analisando RAIS e CAGED com R](https://guilhermejacob.github.io/2017/11/rais-caged-r/)
- [Tutorial RAIS com R](http://cemin.wikidot.com/raisr)
- [BigQuery 101 - Base dos Dados](https://medium.com/basedosdados/bigquery-101-8b39da1ce52b)

### Estudos e Notas Técnicas

- [IPEA - Substituição CAGED pelo eSocial](https://repositorio.ipea.gov.br/handle/11058/10212)
- [IPEA - RAIS e CAGED a partir do eSocial](https://repositorio.ipea.gov.br/entities/publication/759e1aba-6a03-48a1-9cf9-b671dc497275)

---

## Histórico de Atualizações

| Data | Alteração |
|------|-----------|
| 2026-01-28 | Documento criado |
| 2026-01-28 | URLs validadas, estrutura FTP atualizada, arquivo de validação criado |
