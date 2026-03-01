# Validação dos Dados PGFN

**Data da Validação:** 2026-01-28
**Validado por:** Claude (automação)

---

## 1. URLs Testadas

| URL | Status | Observação |
|-----|--------|------------|
| https://dadosabertos.pgfn.gov.br/ | OK | Servidor de arquivos funcionando |
| https://www.gov.br/pgfn/pt-br/assuntos/divida-ativa-da-uniao/transparencia-fiscal-1/dados-abertos | OK | Página informativa |
| https://dados.gov.br/dados/conjuntos-dados/devedores-da-uniao-e-do-fgts1 | OK | Requer JavaScript |
| https://www.listadevedores.pgfn.gov.br/ | OK | Consulta online funcionando |
| https://www.gov.br/conecta/catalogo/apis/consulta-divida-ativa-da-uniao | ERRO 403 | Acesso bloqueado (possivelmente requer autenticação) |
| https://apicenter.estaleiro.serpro.gov.br/documentacao/consulta-divida-ativa/pt/ | OK | Documentação da API |
| https://www.loja.serpro.gov.br/consulta-divida-ativa | REDIRECT | Redireciona para /product/consulta-divida-ativa |
| https://basedosdados.org/dataset/lista-de-devedores-da-pgfn | OK | Dados tratados disponíveis |

---

## 2. Estrutura do Servidor de Arquivos

### Trimestres Disponíveis (dadosabertos.pgfn.gov.br)

- 2020: Q1, Q2, Q3, Q4
- 2021: Q1, Q2, Q3, Q4
- 2022: Q1, Q2, Q3, Q4
- 2023: Q1, Q2, Q3, Q4
- 2024: Q1, Q2, Q3, Q4
- 2025: Q1, Q2, Q3, Q4

**Diretório adicional:** `Portal_da_Cidadania_Tributaria/` (PDFs de atos declaratórios)

### Padrão Real de URL

```
https://dadosabertos.pgfn.gov.br/{ANO}_trimestre_{N}/Dados_abertos_{TIPO}.zip
```

**Tipos disponíveis:**
- `Dados_abertos_FGTS.zip`
- `Dados_abertos_Nao_Previdenciario.zip`
- `Dados_abertos_Previdenciario.zip`

---

## 3. Estrutura Real dos Arquivos

### Diferença da Documentação Original

A documentação original indicava arquivos separados por UF:
```
Dados_abertos_Nao_Previdenciario_{UF}.csv  ❌ INCORRETO
```

**Formato Real:** Os arquivos são ZIPs contendo CSVs numerados:
```
Dados_abertos_FGTS.zip
├── arquivo_lai_FGTS_1_202512.csv
├── arquivo_lai_FGTS_2_202512.csv
├── arquivo_lai_FGTS_3_202512.csv
├── arquivo_lai_FGTS_4_202512.csv
├── arquivo_lai_FGTS_5_202512.csv
├── arquivo_lai_FGTS_6_202512.csv
└── arquivo_lai_FGTS_NA_202512.csv
```

### Tamanhos dos ZIPs (Q4 2025)

| Arquivo | Tamanho Compactado | Data |
|---------|-------------------|------|
| Dados_abertos_FGTS.zip | 17 MB | 2026-01-19 |
| Dados_abertos_Previdenciario.zip | 89 MB | 2026-01-19 |
| Dados_abertos_Nao_Previdenciario.zip | 1.1 GB | 2026-01-19 |

---

## 4. Colunas Encontradas nos CSVs

### FGTS (15 colunas)

| # | Coluna | Exemplo |
|---|--------|---------|
| 1 | CPF_CNPJ | 10.496.760/0001-95 |
| 2 | TIPO_PESSOA | Pessoa jurídica |
| 3 | TIPO_DEVEDOR | Principal |
| 4 | NOME_DEVEDOR | ALESSANDRO RIBEIRO DA SILVA |
| 5 | UF_DEVEDOR | BA |
| 6 | UNIDADE_RESPONSAVEL | ACRE |
| 7 | ENTIDADE_RESPONSAVEL | PGFN |
| 8 | UNIDADE_INSCRICAO | ACRE |
| 9 | NUMERO_INSCRICAO | FGBA201900928 |
| 10 | TIPO_SITUACAO_INSCRICAO | Em cobrança |
| 11 | SITUACAO_INSCRICAO | INSCRITA |
| 12 | RECEITA_PRINCIPAL | Contribuições FGTS |
| 13 | DATA_INSCRICAO | 30/07/2019 |
| 14 | INDICADOR_AJUIZADO | NAO |
| 15 | VALOR_CONSOLIDADO | 5042.26 |

### Previdenciário (13 colunas)

| # | Coluna | Exemplo |
|---|--------|---------|
| 1 | CPF_CNPJ | 02.990.231/0001-15 |
| 2 | TIPO_PESSOA | Pessoa jurídica |
| 3 | TIPO_DEVEDOR | Principal |
| 4 | NOME_DEVEDOR | RAINERIO FRANCISCO SOUZA DA SILVA |
| 5 | UF_DEVEDOR | BA |
| 6 | UNIDADE_RESPONSAVEL | BAHIA |
| 7 | NUMERO_INSCRICAO | 194991504 |
| 8 | TIPO_SITUACAO_INSCRICAO | Em cobrança |
| 9 | SITUACAO_INSCRICAO | INSCRICAO DE CREDITO EM DIVIDA ATIVA |
| 10 | TIPO_CREDITO | OUTROS |
| 11 | DATA_INSCRICAO | 19/07/2025 |
| 12 | INDICADOR_AJUIZADO | NAO |
| 13 | VALOR_CONSOLIDADO | 1699.68 |

### Diferenças Entre Tipos

| Coluna | FGTS | Previdenciário | Não Previdenciário |
|--------|------|----------------|-------------------|
| ENTIDADE_RESPONSAVEL | Sim | Não | Não |
| UNIDADE_INSCRICAO | Sim | Não | Não |
| RECEITA_PRINCIPAL | Sim | Não | Não |
| TIPO_CREDITO | Não | Sim | Sim |

---

## 5. Valores Encontrados nos Campos

### TIPO_PESSOA
- `Pessoa física` (CPF mascarado)
- `Pessoa jurídica` (CNPJ completo)

### TIPO_DEVEDOR
- `Principal` (maioria)
- `Corresponsável`
- `Solidário`

### TIPO_SITUACAO_INSCRICAO
- `Em cobrança` (maioria)
- `Benefício Fiscal`
- `Garantia`

### SITUACAO_INSCRICAO
- `AJUIZADA`
- `AJUIZ PARCELADA`
- `EMBARGADA`
- `INSCRITA`
- `INSCR PARCELADA`
- `OUTROS AJUIZADA`
- `OUTROS INSCRITA`
- `PARCELAMENTO PRÉ-FORMALIZADO`
- `PETICIONADA`
- `PROTESTADA`
- `TRANSFERIDA`

### INDICADOR_AJUIZADO
- `SIM`
- `NAO`

---

## 6. Formato do CPF/CNPJ

### CNPJ (Pessoa Jurídica)
- Formato: `XX.XXX.XXX/XXXX-XX` (com pontuação)
- Exemplo: `10.496.760/0001-95`

### CPF (Pessoa Física)
- Formato mascarado: `***.XXX.XXX-**`
- Somente dígitos centrais visíveis (LGPD)
- Exemplo: `***.123.456-**`

---

## 7. Amostras Baixadas

| Arquivo | Registros | Tamanho | Descrição |
|---------|-----------|---------|-----------|
| arquivo_lai_FGTS_1_202512.csv | 76.862 | 14 MB | Amostra FGTS parte 1 |
| arquivo_lai_FGTS_2_202512.csv | 46.429 | 8.4 MB | Amostra FGTS parte 2 |

**Total FGTS (todos os arquivos):** 516.796 registros

---

## 8. Problemas Encontrados

### 8.1 Estrutura de Arquivos Diferente
A documentação original indicava arquivos separados por UF (ex: `Dados_abertos_FGTS_SP.csv`), mas na realidade são arquivos numerados dentro de um ZIP único por tipo de dívida.

### 8.2 URL do Conecta Bloqueada
A URL `https://www.gov.br/conecta/catalogo/apis/consulta-divida-ativa-da-uniao` retorna erro 403 (Forbidden).

### 8.3 Colunas Variam por Tipo de Arquivo
Os três tipos de arquivo (FGTS, Previdenciário, Não Previdenciário) têm estruturas de colunas diferentes.

### 8.4 Encoding ISO-8859-1
Os arquivos estão em encoding ISO-8859-1, não UTF-8. Caracteres acentuados aparecem corrompidos se lidos como UTF-8.

### 8.5 Valores de Situação Diferentes da Documentação
A documentação listava:
- `ATIVO EM COBRANÇA`, `GARANTIDO`, `SUSPENSO`, `PARCELADO`, `AJUIZADO`, `EXTINTO`

Os valores reais encontrados são:
- `AJUIZADA`, `INSCRITA`, `PROTESTADA`, `EMBARGADA`, `PARCELADA`, etc.

### 8.6 Padrão de URL da Loja SERPRO
A URL da loja SERPRO redireciona para `/product/consulta-divida-ativa` (não é erro, apenas redirecionamento).

---

## 9. Recomendações

1. **Atualizar documentação** com estrutura correta de arquivos (ZIPs numerados, não por UF)
2. **Corrigir lista de colunas** separando por tipo de arquivo
3. **Adicionar tratamento de encoding** ISO-8859-1 no código Python
4. **Atualizar valores de situação** com valores reais encontrados
5. **Remover ou marcar URL do Conecta** como potencialmente restrita

---

*Validação concluída em 2026-01-28*
