# Validação dos Dados CEIS e CNEP

**Data da validação:** 2026-01-28
**Responsável:** Claude (validação automatizada)

---

## 1. URLs Testadas

### CEIS (Cadastro Nacional de Empresas Inidôneas e Suspensas)

| URL | Status | Observação |
|-----|--------|------------|
| https://portaldatransparencia.gov.br/download-de-dados/ceis | OK (200) | Página de download funcional, requer JavaScript |
| https://portaldatransparencia.gov.br/download-de-dados/ceis/202601 | ERRO (403) | CloudFront bloqueia downloads automatizados |
| https://portaldatransparencia.gov.br/sancoes/consulta?cadastro=1 | OK (200) | Consulta online funcional |
| https://www.portaldatransparencia.gov.br/pagina-interna/603412-dicionario-de-dados-sancoes-ceis | ERRO (403) | Página existe mas bloqueada para crawlers |
| https://dados.gov.br/dados/conjuntos-dados/ceis | OK (200) | Requer JavaScript para exibir recursos |
| https://api.portaldatransparencia.gov.br/api-de-dados/ceis | ERRO (401) | Requer chave de API |

### CNEP (Cadastro Nacional de Empresas Punidas)

| URL | Status | Observação |
|-----|--------|------------|
| https://portaldatransparencia.gov.br/download-de-dados/cnep | OK (200) | Página de download funcional, requer JavaScript |
| https://portaldatransparencia.gov.br/download-de-dados/cnep/202601 | ERRO (403) | CloudFront bloqueia downloads automatizados |
| https://portaldatransparencia.gov.br/sancoes/consulta?cadastro=2 | OK (200) | Consulta online funcional |
| https://portaldatransparencia.gov.br/pagina-interna/603414-dicionario-de-dados-sancoes-cnep | ERRO (403) | Página existe mas bloqueada para crawlers |
| https://dados.gov.br/dados/conjuntos-dados/cnep | OK (200) | Requer JavaScript para exibir recursos |
| https://api.portaldatransparencia.gov.br/api-de-dados/cnep | ERRO (401) | Requer chave de API |

### Outros Cadastros

| URL | Status | Observação |
|-----|--------|------------|
| https://portaldatransparencia.gov.br/download-de-dados/cepim | OK (200) | CEPIM - Entidades sem fins lucrativos |
| https://portaldatransparencia.gov.br/download-de-dados/ceaf | OK (200) | CEAF - Expulsões da Administração Federal |
| https://bancodesancoes.cgu.gov.br/ | OK (200) | Portal CGU - Banco de Sanções |

---

## 2. Bloqueio de Downloads Automatizados

### Problema Identificado

O Portal da Transparência utiliza **CloudFront** da AWS com proteção anti-bot que bloqueia:

1. **Downloads via curl/wget**: Retorna XML com `<Error><Code>AccessDenied</Code></Error>`
2. **Requisições via Python requests**: Mesmo com headers de navegador, retorna 403
3. **Requisições sem sessão válida**: Cookies de sessão são obrigatórios

### Tentativas Realizadas

```bash
# Tentativa 1: curl básico
curl -sL "https://portaldatransparencia.gov.br/download-de-dados/ceis/202601"
# Resultado: 403 Forbidden (XML AccessDenied)

# Tentativa 2: curl com User-Agent
curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..." URL
# Resultado: 403 Forbidden

# Tentativa 3: Python requests com sessão
session = requests.Session()
session.get(main_page)  # Obtém cookie SESSION
session.get(download_url)  # Ainda retorna 403
# Resultado: 403 Forbidden

# Tentativa 4: wget com Referer
wget --referer="https://portaldatransparencia.gov.br/download-de-dados/ceis" URL
# Resultado: 403 Forbidden
```

### Solução Recomendada

Para downloads automatizados, usar a **API do Portal da Transparência**:

1. **Cadastrar email**: https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email
2. **Autenticar com Gov.br**: Nível Prata ou Ouro (ou 2FA habilitado)
3. **Receber token por email**
4. **Usar header**: `chave-api-dados: SEU_TOKEN`

```python
import requests

headers = {"chave-api-dados": "SEU_TOKEN"}
response = requests.get(
    "https://api.portaldatransparencia.gov.br/api-de-dados/ceis",
    headers=headers
)
```

---

## 3. Formato dos Arquivos CSV (Confirmado via Documentação)

### Formato Geral

| Característica | Valor |
|----------------|-------|
| Separador | Ponto e vírgula (;) |
| Encoding | Latin-1 (ISO-8859-1) |
| Formato de data | DD/MM/AAAA |
| Valores nulos | Campo vazio ou "-" |

### Colunas do CEIS (conforme dicionário de dados oficial)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| CÓDIGO DA SANÇÃO | numérico | Código único da sanção no Banco de Sanções |
| TIPO DE PESSOA | texto | "Pessoa Física" ou "Pessoa Jurídica" |
| CPF OU CNPJ DO SANCIONADO | texto | Documento do sancionado (mascarado para PF) |
| NOME DO SANCIONADO | texto | Nome/Razão social |
| NOME FANTASIA | texto | Nome fantasia (se PJ) |
| NÚMERO DO PROCESSO | texto | Número do processo administrativo |
| TIPO SANÇÃO | texto | Tipo da penalidade aplicada |
| DATA INÍCIO SANÇÃO | data | Início da vigência da sanção |
| DATA FIM SANÇÃO | data | Fim da vigência (se aplicável) |
| ÓRGÃO SANCIONADOR | texto | Nome do órgão que aplicou a sanção |
| UF ÓRGÃO SANCIONADOR | texto | UF do órgão sancionador |
| FUNDAMENTAÇÃO LEGAL | texto | Base legal da sanção |
| DATA ORIGEM DA INFORMAÇÃO | data | Data do registro no sistema |
| DATA PUBLICAÇÃO | data | Data de publicação oficial |
| PUBLICAÇÃO | texto | Veículo de publicação |
| DETALHAMENTO | texto | Observações adicionais |
| ABRANGÊNCIA DEFINIDA EM DECISÃO JUDICIAL | texto | Se há restrição de abrangência |
| MOTIVO (somente sanções extintas) | texto | Motivo do término da sanção |

### Colunas do CNEP (conforme dicionário de dados oficial)

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| CÓDIGO DA SANÇÃO | numérico | Código único da sanção |
| TIPO DE PESSOA | texto | Sempre "Pessoa Jurídica" |
| CNPJ DO SANCIONADO | texto | CNPJ da empresa punida |
| RAZÃO SOCIAL | texto | Razão social da empresa |
| NOME FANTASIA | texto | Nome fantasia |
| NÚMERO DO PROCESSO | texto | Número do processo |
| TIPO SANÇÃO | texto | Tipo da penalidade (Lei 12.846/2013) |
| DATA INÍCIO SANÇÃO | data | Início da vigência |
| DATA FIM SANÇÃO | data | Fim da vigência |
| ÓRGÃO SANCIONADOR | texto | Órgão responsável |
| UF ÓRGÃO SANCIONADOR | texto | UF do órgão |
| FUNDAMENTAÇÃO LEGAL | texto | Base legal |
| VALOR DA MULTA | numérico | Valor da multa aplicada (formato BR: "1.234,56") |
| ACORDO DE LENIÊNCIA | texto | Se houve acordo |
| SITUAÇÃO DO ACORDO | texto | Status do acordo (se aplicável) |
| DATA DO ACORDO | data | Data do acordo de leniência |
| DATA PUBLICAÇÃO | data | Data de publicação |
| PUBLICAÇÃO | texto | Veículo de publicação |
| DETALHAMENTO | texto | Observações |

---

## 4. Quantidade de Registros (Estimativa)

| Cadastro | Registros Estimados | Fonte |
|----------|---------------------|-------|
| CEIS | ~15.000 a 20.000 | Portal da Transparência (01/2026) |
| CNEP | ~500 a 1.000 | Portal da Transparência (01/2026) |
| CEPIM | ~5.000 a 10.000 | SIAFI |
| CEAF | ~15.000 a 20.000 | DOU (desde 2003) |

**Nota:** Não foi possível confirmar os números exatos devido ao bloqueio de downloads automatizados.

---

## 5. Problemas Encontrados

### 5.1 Bloqueio Anti-Bot (Crítico)

**Problema:** O CloudFront da AWS bloqueia todas as tentativas de download automatizado.

**Impacto:** Impossível baixar os arquivos CSV sem intervenção manual ou uso da API autenticada.

**Solução:**
1. Usar API com chave (requer cadastro Gov.br)
2. Download manual via navegador
3. Usar ferramenta com suporte a JavaScript (Selenium/Playwright)

### 5.2 Dependência de JavaScript

**Problema:** As páginas do dados.gov.br e Portal da Transparência requerem JavaScript para exibir links de download.

**Impacto:** WebFetch e curl não conseguem obter os links diretos.

**Solução:** Usar URLs documentadas ou API.

### 5.3 Limite de 20.000 Registros

**Problema:** O download via interface web é limitado a 20.000 registros.

**Impacto:** Para datasets maiores (CEIS pode exceder), dados serão truncados.

**Solução:** Usar API paginada ou acessar dados abertos completos.

---

## 6. Recomendações

### Para ETL Automatizado

1. **Registrar na API do Portal da Transparência**
   - URL: https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email
   - Requer conta Gov.br (Prata ou Ouro)

2. **Implementar cliente API com paginação**
   ```python
   def baixar_ceis_completo(token):
       dados = []
       pagina = 1
       while True:
           response = requests.get(
               f"https://api.portaldatransparencia.gov.br/api-de-dados/ceis",
               headers={"chave-api-dados": token},
               params={"pagina": pagina}
           )
           lote = response.json()
           if not lote:
               break
           dados.extend(lote)
           pagina += 1
       return dados
   ```

3. **Alternativamente: Download manual + processamento**
   - Baixar manualmente via navegador
   - Processar com script Python/Polars

### Para Integração com PostgreSQL

```sql
-- Tabela sugerida para CEIS
CREATE TABLE sancoes_ceis (
    codigo_sancao BIGINT PRIMARY KEY,
    tipo_pessoa VARCHAR(20),
    cpf_cnpj VARCHAR(18),
    nome_sancionado VARCHAR(500),
    nome_fantasia VARCHAR(500),
    numero_processo VARCHAR(100),
    tipo_sancao VARCHAR(200),
    data_inicio DATE,
    data_fim DATE,
    orgao_sancionador VARCHAR(500),
    uf_orgao VARCHAR(2),
    fundamentacao_legal TEXT,
    data_origem DATE,
    data_publicacao DATE,
    publicacao VARCHAR(200),
    detalhamento TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ceis_cpf_cnpj ON sancoes_ceis(cpf_cnpj);
CREATE INDEX idx_ceis_nome ON sancoes_ceis USING gin(to_tsvector('portuguese', nome_sancionado));
CREATE INDEX idx_ceis_vigente ON sancoes_ceis(data_fim) WHERE data_fim >= CURRENT_DATE;
```

---

## 7. Fontes Consultadas

- [Portal da Transparência - CEIS](https://portaldatransparencia.gov.br/download-de-dados/ceis)
- [Portal da Transparência - CNEP](https://portaldatransparencia.gov.br/download-de-dados/cnep)
- [Dicionário de Dados CEIS](https://www.portaldatransparencia.gov.br/pagina-interna/603412-dicionario-de-dados-sancoes-ceis)
- [Dicionário de Dados CNEP](https://portaldatransparencia.gov.br/pagina-interna/603414-dicionario-de-dados-sancoes-cnep)
- [API do Portal da Transparência](https://api.portaldatransparencia.gov.br/)
- [Banco de Sanções CGU](https://bancodesancoes.cgu.gov.br/)
- [Dados Abertos - CEIS](https://dados.gov.br/dados/conjuntos-dados/ceis)
- [Dados Abertos - CNEP](https://dados.gov.br/dados/conjuntos-dados/cnep)

---

*Documento gerado em: 2026-01-28*
*Última atualização: 2026-01-28*
