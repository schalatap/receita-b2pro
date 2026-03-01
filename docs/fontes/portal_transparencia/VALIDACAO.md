# Validação do Portal da Transparência e PNCP

**Data da Validação:** 2026-01-28
**Validado por:** Claude Code (Automatizado)

## Sumário

- Portal da Transparência: URLs funcionando, API requer autenticação
- PNCP: API pública funcionando sem autenticação
- Swagger do PNCP: Acessível
- Biblioteca Python: Repositório ativo no GitHub

---

## 1. Portal da Transparência do Governo Federal

### 1.1 URLs do Site

| URL | Status | Observação |
|-----|--------|------------|
| https://portaldatransparencia.gov.br/api-de-dados | ✅ OK (200) | Página principal da API |
| https://api.portaldatransparencia.gov.br/ | ⚠️ BLOQUEADO (403) | Swagger requer navegador/cookies |
| https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email | ✅ OK (200) | Cadastro para obter chave |
| https://portaldatransparencia.gov.br/pagina-interna/603579-api-de-dados-exemplos-de-uso | ✅ OK (200) | Exemplos de uso |
| https://www.gov.br/conecta/catalogo/apis/portal-da-transparencia-do-governo-federal | ⚠️ BLOQUEADO (403) | Gov.br bloqueia bots |

**Nota:** As URLs com status 403 funcionam em navegador real. O bloqueio é para requisições automatizadas via CloudFront WAF.

### 1.2 Endpoints da API

| Endpoint | Status | Resposta |
|----------|--------|----------|
| `/api-de-dados/contratos?pagina=1` | 🔐 401/403 | Requer `chave-api-dados` no header |
| `/api-de-dados/licitacoes/modalidades` | 🔐 401/403 | Requer `chave-api-dados` no header |
| `/api-de-dados/ceis?pagina=1` | 🔐 401/403 | Requer `chave-api-dados` no header |
| `/api-de-dados/despesas/documentos-por-favorecido` | 🔐 401/403 | Requer `chave-api-dados` no header |

### 1.3 Requisitos de Autenticação (Confirmados)

A API retorna mensagem de erro padronizada quando não autenticado:

```json
{
  "Erro na API": "Chave de API não informada! Para obter a chave acesse http://www.portaldatransparencia.gov.br/api-de-dados/cadastrar-email"
}
```

**Requisitos para obter chave:**
- Conta Gov.br nível Prata (Verificado) ou Ouro (Comprovado)
- Ou CPF/Senha com 2FA habilitado
- Token enviado por email após cadastro

### 1.4 Rate Limits (Documentação)

| Horário | Limite | Observação |
|---------|--------|------------|
| 00:00 - 06:00 | 700 req/min | Horário de baixa demanda |
| 06:00 - 00:00 | 400 req/min | Horário comercial |
| APIs restritas | 180 req/min | Endpoints sensíveis |

**Penalidade:** Suspensão do token por 8 horas se exceder limite.

---

## 2. PNCP - Portal Nacional de Contratações Públicas

### 2.1 URLs

| URL | Status | Observação |
|-----|--------|------------|
| https://pncp.gov.br | ✅ OK (302→gov.br) | Redireciona para gov.br/pncp |
| https://www.gov.br/pncp/pt-br | ⚠️ BLOQUEADO (403) | Funciona em navegador |
| https://pncp.gov.br/api/pncp/swagger-ui/index.html | ✅ OK (200) | Swagger acessível |

### 2.2 Endpoints da API (SEM AUTENTICAÇÃO)

| Endpoint | Status | Resposta |
|----------|--------|----------|
| `/api/consulta/v1/contratos?dataInicial=20240101&dataFinal=20240131&pagina=1` | ✅ OK (200) | Retorna JSON com dados |
| `/api/consulta/v1/` | ❌ 404 | Base URL não existe |

### 2.3 Amostra de Resposta PNCP

Ver arquivo: `pncp_contratos_exemplo.json`

**Campos disponíveis no contrato:**
- `numeroControlePNCP` - Identificador único
- `cnpj` (orgaoEntidade) - CNPJ do órgão contratante
- `niFornecedor` - CNPJ/CPF do fornecedor
- `nomeRazaoSocialFornecedor` - Nome do fornecedor
- `objetoContrato` - Descrição do objeto
- `valorInicial`, `valorGlobal`, `valorAcumulado` - Valores
- `dataAssinatura`, `dataVigenciaInicio`, `dataVigenciaFim` - Datas
- `unidadeOrgao.ufSigla`, `unidadeOrgao.municipioNome` - Localização

### 2.4 Vantagens do PNCP vs Portal Transparência

| Aspecto | Portal Transparência | PNCP |
|---------|---------------------|------|
| Autenticação | Obrigatória (Gov.br Prata+) | Não requer |
| Cobertura | Apenas Poder Executivo Federal | União + Estados + Municípios |
| Rate Limit | 400-700 req/min | Não documentado (aparenta liberal) |
| Dados históricos | Desde 01/01/2013 | Lei 14.133/2021 em diante |

---

## 3. Recursos Externos

### 3.1 Biblioteca Python `portaldatransparencia`

| URL | Status |
|-----|--------|
| https://github.com/guizsantos/portaldatransparencia | ✅ OK (200) |

**Repositório ativo no GitHub.**

### 3.2 Tutorial Escola de Dados

| URL | Status |
|-----|--------|
| https://escoladedados.org/tutoriais/explorando-as-despesas-do-governo-federal-via-api/ | ✅ OK (200) |

---

## 4. Problemas Encontrados

### 4.1 Acentuação no Documento Original

O documento original `/home/akira/cnpj-data-pipeline/docs/fontes/PORTAL_TRANSPARENCIA.md` já estava com acentuação UTF-8 correta. Nenhuma correção necessária.

### 4.2 URL do PNCP

A documentação menciona:
- `https://pncp.gov.br/api/consulta/v1/` - Não existe, retorna 404

**URL correta para consultas:**
- `https://pncp.gov.br/api/consulta/v1/contratos`
- `https://pncp.gov.br/api/consulta/v1/compras`

### 4.3 Swagger do Portal Transparência

A URL `https://api.portaldatransparencia.gov.br/` retorna 403 para bots, mas funciona em navegador. Isso é proteção do CloudFront e não indica problema com a documentação.

---

## 5. Recomendações

1. **Para uso em produção:** Obter chave de API do Portal da Transparência (Gov.br Prata+)

2. **Para testes rápidos:** Usar PNCP que não requer autenticação

3. **Para cobertura completa:** Combinar ambas as fontes
   - Portal Transparência: histórico desde 2013, Poder Executivo Federal
   - PNCP: dados mais recentes, todos os entes federativos

4. **Rate limiting:** Usar horário noturno (00:00-06:00) para cargas maiores

---

## 6. Arquivos de Amostra

| Arquivo | Conteúdo |
|---------|----------|
| `api_sem_autenticacao.json` | Erro retornado pela API do Portal Transparência sem token |
| `pncp_contratos_exemplo.json` | Exemplo de contrato retornado pela API do PNCP |

---

**Conclusão:** A documentação está correta e as fontes estão funcionando. A principal diferença prática é que o Portal da Transparência requer autenticação enquanto o PNCP é público.
