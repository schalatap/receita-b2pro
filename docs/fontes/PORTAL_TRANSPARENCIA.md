# Portal da Transparência do Governo Federal - API de Dados

## Visão Geral

O Portal da Transparência do Governo Federal disponibiliza uma API REST pública para consulta de dados sobre gastos públicos, contratos, licitações, convênios, despesas e fornecedores do governo federal brasileiro.

**Valor para B2B:** Identificar empresas que vendem para o governo (B2G), estimar faturamento mínimo com setor público, mapear setores de atuação e validar histórico de contratos.

## URLs Oficiais

| Recurso | URL | Status (2026-01-28) |
|---------|-----|---------------------|
| Página principal da API | https://portaldatransparencia.gov.br/api-de-dados | OK |
| Documentação Swagger | https://api.portaldatransparencia.gov.br/ | OK (requer navegador) |
| Cadastro para obter chave | https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email | OK |
| Exemplos de uso | https://portaldatransparencia.gov.br/pagina-interna/603579-api-de-dados-exemplos-de-uso | OK |
| Catálogo Gov.br | https://www.gov.br/conecta/catalogo/apis/portal-da-transparencia-do-governo-federal | OK (requer navegador) |

> **Nota:** Algumas URLs retornam 403 para requisições automatizadas (bots/scripts) devido à proteção do CloudFront WAF, mas funcionam normalmente em navegadores.

## Como Obter Credenciais de Acesso

### Requisitos

1. **Conta Gov.br** com nível mínimo **Verificado (Prata)** ou **Comprovado (Ouro)**
2. Alternativamente: conta com CPF/Senha + **autenticação em dois fatores (2FA)** habilitada

### Passo a Passo

1. Acesse https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email
2. Autentique-se pelo Gov.br (Prata/Ouro ou CPF+2FA)
3. Cadastre seu e-mail para recebimento da chave
4. O token será enviado para o e-mail cadastrado na conta Gov.br
5. Use o token no header HTTP de todas as requisições

### Uso do Token

```http
GET /api-de-dados/contratos HTTP/1.1
Host: api.portaldatransparencia.gov.br
chave-api-dados: SEU_TOKEN_AQUI
```

## Limites de Requisições (Rate Limiting)

| Horário | Limite | Observação |
|---------|--------|------------|
| 00:00 - 06:00 | 700 req/min | Horário de baixa demanda |
| 06:00 - 00:00 | 400 req/min | Horário comercial |
| APIs restritas | 180 req/min | Endpoints específicos |

### APIs Restritas (180 req/min)

- `/api-de-dados/despesas/documentos-por-favorecido`
- `/api-de-dados/bolsa-familia-disponivel-por-cpf-ou-nis`
- `/api-de-dados/bolsa-familia-por-municipio`
- `/api-de-dados/auxilio-emergencial-beneficiario-por-municipio`

### Penalidade por Excesso

Se o limite for excedido, o token será **suspenso por 8 horas**.

## Endpoints Principais para B2B

### 1. Contratos do Poder Executivo Federal

```
GET /api-de-dados/contratos
```

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `codigoOrgao` | string | Não | Código do órgão contratante |
| `dataInicial` | date | Não | Data inicial (AAAA-MM-DD) |
| `dataFinal` | date | Não | Data final (AAAA-MM-DD) |
| `pagina` | int | Sim | Número da página |

**Endpoints relacionados:**

| Endpoint | Descrição |
|----------|-----------|
| `/api-de-dados/contratos/{id}` | Detalhes de um contrato |
| `/api-de-dados/contratos/numero` | Busca por número do contrato |
| `/api-de-dados/contratos/cpf-cnpj` | **Busca por CNPJ do fornecedor** |
| `/api-de-dados/contratos/{id}/apostilamento` | Apostilamentos do contrato |
| `/api-de-dados/contratos/{id}/termo-aditivo` | Termos aditivos |
| `/api-de-dados/contratos/{id}/documentos-relacionados` | Documentos vinculados |

### 2. Licitações do Poder Executivo Federal

```
GET /api-de-dados/licitacoes
```

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `codigoOrgao` | string | Não | Código do órgão |
| `dataInicial` | date | Não | Data inicial |
| `dataFinal` | date | Não | Data final |
| `pagina` | int | Sim | Número da página |

**Endpoints relacionados:**

| Endpoint | Descrição |
|----------|-----------|
| `/api-de-dados/licitacoes/{id}` | Detalhes da licitação |
| `/api-de-dados/licitacoes/por-ug-modalidade-numero` | Busca específica |
| `/api-de-dados/licitacoes/{...}/participantes` | **Empresas participantes** |
| `/api-de-dados/licitacoes/{...}/empenhos` | Empenhos da licitação |
| `/api-de-dados/licitacoes/{...}/contratos` | Contratos resultantes |
| `/api-de-dados/licitacoes/modalidades` | Lista de modalidades |
| `/api-de-dados/licitacoes/ugs` | Unidades gestoras |

### 3. Despesas Públicas (Empenhos, Liquidações, Pagamentos)

```
GET /api-de-dados/despesas/documentos
```

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `dataEmissao` | date | Sim | Data de emissão |
| `fase` | int | Sim | 1=Empenho, 2=Liquidação, 3=Pagamento |
| `pagina` | int | Sim | Número da página |
| `gestao` | string | Não | Código da gestão |
| `unidadeGestora` | string | Não | Código da UG |

### 4. Despesas por Favorecido (CNPJ) - API RESTRITA

```
GET /api-de-dados/despesas/documentos-por-favorecido
```

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `ano` | int | Sim | Ano de emissão |
| `codigoPessoa` | string | Sim | **CNPJ ou CPF do favorecido** |
| `fase` | int | Sim | 1=Empenho, 2=Liquidação, 3=Pagamento |
| `pagina` | int | Sim | Número da página |
| `gestao` | string | Não | Código da gestão |
| `ug` | string | Não | Unidade gestora |

**Este é o endpoint mais importante para B2B** - permite consultar todos os pagamentos recebidos por uma empresa do governo federal.

### 5. Notas Fiscais por Fornecedor

```
GET /api-de-dados/notas-fiscais/fornecedor
```

Permite consultar notas fiscais eletrônicas emitidas para o governo federal por CNPJ do fornecedor.

### 6. Cadastros de Sanções (CEIS, CNEP, CEPIM)

| Endpoint | Descrição |
|----------|-----------|
| `/api-de-dados/ceis` | Empresas Inidôneas e Suspensas |
| `/api-de-dados/cnep` | Empresas Punidas |
| `/api-de-dados/cepim` | Entidades Impedidas |

**Valor B2B:** Verificar se empresa tem restrições para contratar com o governo.

## Estrutura de Resposta JSON

### Exemplo: Contrato

```json
{
  "id": 12345678,
  "numero": "00001/2024",
  "dataAssinatura": "2024-01-15",
  "dataInicioVigencia": "2024-01-15",
  "dataFimVigencia": "2025-01-14",
  "valorInicial": 150000.00,
  "valorFinal": 150000.00,
  "objeto": "Prestação de serviços de tecnologia da informação",
  "unidadeGestora": {
    "codigo": "170001",
    "nome": "Ministério da Fazenda"
  },
  "fornecedor": {
    "tipo": "PJ",
    "cnpjCpf": "12345678000199",
    "nome": "EMPRESA EXEMPLO LTDA"
  },
  "modalidadeLicitacao": {
    "codigo": "6",
    "descricao": "Pregão"
  }
}
```

### Exemplo: Despesa por Favorecido

```json
{
  "id": 987654321,
  "documento": "2024NE000123",
  "fase": {
    "codigo": 3,
    "nome": "Pagamento"
  },
  "dataEmissao": "2024-06-15",
  "valor": 25000.00,
  "favorecido": {
    "codigo": "12345678000199",
    "nome": "EMPRESA EXEMPLO LTDA"
  },
  "unidadeGestora": {
    "codigo": "170001",
    "nome": "Ministério da Fazenda"
  },
  "planoOrcamentario": {
    "codigo": "0001",
    "descricao": "Administração"
  }
}
```

### Paginação

Todas as respostas paginadas incluem metadados:

```json
{
  "pagina": 1,
  "totalPaginas": 15,
  "totalRegistros": 742,
  "registrosPorPagina": 50,
  "dados": [...]
}
```

## Código Python de Exemplo

### Instalação

```bash
pip install requests
```

### Classe para Consumir a API

```python
"""
Cliente Python para a API do Portal da Transparência do Governo Federal.
Foco em identificação de fornecedores B2G (Business to Government).
"""

import requests
import time
from typing import Optional, Generator, Any
from dataclasses import dataclass
from datetime import date


@dataclass
class RateLimiter:
    """Controla rate limiting da API."""
    requests_per_minute: int = 400  # Horário comercial
    last_request: float = 0
    request_count: int = 0
    window_start: float = 0

    def wait_if_needed(self):
        """Aguarda se necessário para respeitar rate limit."""
        current = time.time()

        # Reset contador a cada minuto
        if current - self.window_start >= 60:
            self.window_start = current
            self.request_count = 0

        # Se atingiu limite, aguarda
        if self.request_count >= self.requests_per_minute:
            sleep_time = 60 - (current - self.window_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.window_start = time.time()
            self.request_count = 0

        self.request_count += 1


class PortalTransparenciaAPI:
    """
    Cliente para API do Portal da Transparência.

    Uso:
        api = PortalTransparenciaAPI("SEU_TOKEN_AQUI")

        # Buscar contratos por CNPJ
        contratos = api.contratos_por_cnpj("12345678000199")

        # Buscar despesas pagas para uma empresa
        despesas = api.despesas_por_favorecido(
            cnpj="12345678000199",
            ano=2024,
            fase=3  # Pagamentos
        )
    """

    BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"

    def __init__(self, token: str, requests_per_minute: int = 400):
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "chave-api-dados": token,
            "Accept": "application/json"
        })
        self.rate_limiter = RateLimiter(requests_per_minute=requests_per_minute)

    def _request(self, endpoint: str, params: dict = None) -> dict:
        """Executa requisição com rate limiting."""
        self.rate_limiter.wait_if_needed()

        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        return response.json()

    def _paginate(self, endpoint: str, params: dict = None) -> Generator[dict, None, None]:
        """Itera por todas as páginas de um endpoint."""
        params = params or {}
        params["pagina"] = 1

        while True:
            data = self._request(endpoint, params)

            # Retorna cada registro
            if isinstance(data, list):
                if not data:
                    break
                for item in data:
                    yield item
                params["pagina"] += 1
            else:
                # Resposta com metadados de paginação
                registros = data.get("dados", data.get("registros", []))
                if not registros:
                    break
                for item in registros:
                    yield item

                total_paginas = data.get("totalPaginas", 1)
                if params["pagina"] >= total_paginas:
                    break
                params["pagina"] += 1

    # ==================== CONTRATOS ====================

    def contratos(
        self,
        codigo_orgao: Optional[str] = None,
        data_inicial: Optional[date] = None,
        data_final: Optional[date] = None,
        pagina: int = 1
    ) -> list[dict]:
        """Lista contratos do Poder Executivo Federal."""
        params = {"pagina": pagina}
        if codigo_orgao:
            params["codigoOrgao"] = codigo_orgao
        if data_inicial:
            params["dataInicial"] = data_inicial.isoformat()
        if data_final:
            params["dataFinal"] = data_final.isoformat()

        return self._request("contratos", params)

    def contratos_por_cnpj(self, cnpj: str, pagina: int = 1) -> list[dict]:
        """
        Busca contratos por CNPJ do fornecedor.

        Args:
            cnpj: CNPJ do fornecedor (apenas números)
            pagina: Número da página

        Returns:
            Lista de contratos do fornecedor
        """
        return self._request("contratos/cpf-cnpj", {
            "cpfCnpj": cnpj.replace(".", "").replace("/", "").replace("-", ""),
            "pagina": pagina
        })

    def contrato_detalhes(self, contrato_id: int) -> dict:
        """Retorna detalhes de um contrato específico."""
        return self._request(f"contratos/{contrato_id}")

    def todos_contratos_cnpj(self, cnpj: str) -> Generator[dict, None, None]:
        """Itera por todos os contratos de um CNPJ."""
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
        return self._paginate("contratos/cpf-cnpj", {"cpfCnpj": cnpj_limpo})

    # ==================== LICITAÇÕES ====================

    def licitacoes(
        self,
        codigo_orgao: Optional[str] = None,
        data_inicial: Optional[date] = None,
        data_final: Optional[date] = None,
        pagina: int = 1
    ) -> list[dict]:
        """Lista licitações do Poder Executivo Federal."""
        params = {"pagina": pagina}
        if codigo_orgao:
            params["codigoOrgao"] = codigo_orgao
        if data_inicial:
            params["dataInicial"] = data_inicial.isoformat()
        if data_final:
            params["dataFinal"] = data_final.isoformat()

        return self._request("licitacoes", params)

    def licitacao_participantes(
        self,
        codigo_ug: str,
        codigo_modalidade: str,
        numero: str,
        pagina: int = 1
    ) -> list[dict]:
        """
        Lista empresas participantes de uma licitação.

        Útil para identificar empresas que participam de licitações
        mesmo que não vençam.
        """
        return self._request("licitacoes/participantes", {
            "codigoUG": codigo_ug,
            "codigoModalidade": codigo_modalidade,
            "numero": numero,
            "pagina": pagina
        })

    # ==================== DESPESAS ====================

    def despesas_por_favorecido(
        self,
        cnpj: str,
        ano: int,
        fase: int = 3,
        pagina: int = 1
    ) -> list[dict]:
        """
        Busca despesas (empenhos/liquidações/pagamentos) por CNPJ.

        ATENÇÃO: Este endpoint tem rate limit restrito (180 req/min).

        Args:
            cnpj: CNPJ do favorecido (fornecedor)
            ano: Ano de emissão do documento
            fase: 1=Empenho, 2=Liquidação, 3=Pagamento
            pagina: Número da página

        Returns:
            Lista de documentos de despesa
        """
        return self._request("despesas/documentos-por-favorecido", {
            "codigoPessoa": cnpj.replace(".", "").replace("/", "").replace("-", ""),
            "ano": ano,
            "fase": fase,
            "pagina": pagina
        })

    def todas_despesas_cnpj(
        self,
        cnpj: str,
        ano: int,
        fase: int = 3
    ) -> Generator[dict, None, None]:
        """Itera por todas as despesas de um CNPJ em um ano."""
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
        return self._paginate("despesas/documentos-por-favorecido", {
            "codigoPessoa": cnpj_limpo,
            "ano": ano,
            "fase": fase
        })

    def total_recebido_governo(
        self,
        cnpj: str,
        ano_inicial: int,
        ano_final: int
    ) -> dict:
        """
        Calcula total recebido do governo federal por um CNPJ.

        Args:
            cnpj: CNPJ da empresa
            ano_inicial: Ano inicial da consulta
            ano_final: Ano final da consulta

        Returns:
            Dict com totais por ano e total geral
        """
        resultado = {
            "cnpj": cnpj,
            "por_ano": {},
            "total_geral": 0.0
        }

        for ano in range(ano_inicial, ano_final + 1):
            total_ano = 0.0
            for despesa in self.todas_despesas_cnpj(cnpj, ano, fase=3):
                valor = despesa.get("valor", 0) or 0
                total_ano += float(valor)

            resultado["por_ano"][ano] = total_ano
            resultado["total_geral"] += total_ano

        return resultado

    # ==================== SANÇÕES ====================

    def verificar_sancoes(self, cnpj: str) -> dict:
        """
        Verifica se empresa possui sanções (CEIS, CNEP, CEPIM).

        Importante para due diligence antes de contratar fornecedores.
        """
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")

        return {
            "cnpj": cnpj,
            "ceis": self._request("ceis", {"cnpjSancionado": cnpj_limpo}),
            "cnep": self._request("cnep", {"cnpjSancionado": cnpj_limpo}),
            "cepim": self._request("cepim", {"cnpjSancionado": cnpj_limpo})
        }


# ==================== EXEMPLO DE USO ====================

if __name__ == "__main__":
    # Substitua pelo seu token
    TOKEN = "SEU_TOKEN_AQUI"

    api = PortalTransparenciaAPI(TOKEN)

    # Exemplo: Buscar contratos de uma empresa
    cnpj_exemplo = "00000000000191"  # Banco do Brasil (exemplo)

    print(f"Buscando contratos do CNPJ {cnpj_exemplo}...")
    contratos = api.contratos_por_cnpj(cnpj_exemplo)

    for contrato in contratos[:5]:  # Primeiros 5
        print(f"""
        Contrato: {contrato.get('numero')}
        Objeto: {contrato.get('objeto', 'N/A')[:100]}...
        Valor: R$ {contrato.get('valorInicial', 0):,.2f}
        Órgão: {contrato.get('unidadeGestora', {}).get('nome', 'N/A')}
        """)

    # Exemplo: Total recebido do governo em 3 anos
    print(f"\nCalculando total recebido do governo (2022-2024)...")
    totais = api.total_recebido_governo(cnpj_exemplo, 2022, 2024)

    print(f"Total geral: R$ {totais['total_geral']:,.2f}")
    for ano, valor in totais["por_ano"].items():
        print(f"  {ano}: R$ {valor:,.2f}")

    # Exemplo: Verificar sanções
    print(f"\nVerificando sanções...")
    sancoes = api.verificar_sancoes(cnpj_exemplo)

    tem_sancao = any([
        sancoes["ceis"],
        sancoes["cnep"],
        sancoes["cepim"]
    ])
    print(f"Possui sanções: {'SIM - ATENÇÃO!' if tem_sancao else 'Não'}")
```

### Uso com a Biblioteca `portaldatransparencia`

Existe uma biblioteca Python de terceiros que simplifica o acesso:

```bash
pip install portaldatransparencia
```

```python
from portaldatransparencia import DespesasPublicas, ContratosPEF, LicitacoesPEF

token = "SEU_TOKEN_AQUI"

# Despesas
despesas = DespesasPublicas(token)
docs = despesas.documentos_por_favorecido(
    ano=2024,
    codigoPessoa="12345678000199",
    fase=3,
    pagina=1
)

# Contratos
contratos = ContratosPEF(token)
lista = contratos.cpf_cnpj(cpfCnpj="12345678000199", pagina=1)

# Licitações
licitacoes = LicitacoesPEF(token)
participantes = licitacoes.participantes(
    codigoUG="170001",
    codigoModalidade="6",
    numero="00001/2024",
    pagina=1
)
```

**Repositório:** https://github.com/guizsantos/portaldatransparencia

## Valor para Inteligência Comercial B2B

### Casos de Uso

| Caso de Uso | Endpoint | Valor |
|-------------|----------|-------|
| Identificar fornecedores B2G | `/contratos/cpf-cnpj` | Segmentar empresas que vendem para o governo |
| Estimar faturamento mínimo | `/despesas/documentos-por-favorecido` | Soma de pagamentos = receita mínima garantida |
| Analisar concorrentes | `/licitacoes/.../participantes` | Ver quem participa das mesmas licitações |
| Due diligence | `/ceis`, `/cnep`, `/cepim` | Verificar sanções antes de fechar negócio |
| Mapear setores | Análise de objetos contratuais | Entender áreas de atuação da empresa |

### Enriquecimento de Dados

Para cada CNPJ do banco de empresas, é possível:

1. **Flag B2G:** Marcar se empresa vende para o governo federal
2. **Faturamento B2G:** Soma de pagamentos recebidos nos últimos 3-5 anos
3. **Score de Relacionamento:** Quantidade de contratos ativos
4. **Sanções:** Flag se empresa está impedida de contratar
5. **Órgãos Clientes:** Lista de órgãos que contratam a empresa

### Limitações

- **Cobertura:** Apenas Poder Executivo Federal (não inclui estados, municípios, legislativo, judiciário)
- **Latência:** Dados podem ter atraso de 30-60 dias
- **Volume:** Rate limit dificulta enriquecimento em massa (usar em horário noturno)
- **Histórico:** Contratos desde 01/01/2013

### Alternativa para Maior Cobertura: PNCP

O **Portal Nacional de Contratações Públicas (PNCP)** centraliza dados de contratações de todos os entes federativos (União, estados, municípios):

- **URL:** https://pncp.gov.br (redireciona para https://www.gov.br/pncp/)
- **API Base:** https://pncp.gov.br/api/consulta/v1/contratos (não existe endpoint raiz `/v1/`)
- **Swagger:** https://pncp.gov.br/api/pncp/swagger-ui/index.html
- **Vantagem:** Não requer autenticação
- **Cobertura:** Lei 14.133/2021 (Nova Lei de Licitações)

> **Nota (Validação 2026-01-28):** A API do PNCP foi testada e está funcionando. O Swagger está acessível. Diferente do Portal da Transparência, o PNCP não exige chave de API.

Exemplo de consulta ao PNCP:

```python
import requests

# Consultar contratos por período
url = "https://pncp.gov.br/api/consulta/v1/contratos"
params = {
    "dataInicial": "20240101",
    "dataFinal": "20240131",
    "pagina": 1
}

response = requests.get(url, params=params)
data = response.json()
```

## Referências

- [API de Dados - Portal da Transparência](https://portaldatransparencia.gov.br/api-de-dados)
- [Documentação Swagger](https://api.portaldatransparencia.gov.br/)
- [Catálogo de APIs Gov.br](https://www.gov.br/conecta/catalogo/apis/portal-da-transparencia-do-governo-federal)
- [Biblioteca Python portaldatransparencia](https://github.com/guizsantos/portaldatransparencia)
- [Tutorial Escola de Dados](https://escoladedados.org/tutoriais/explorando-as-despesas-do-governo-federal-via-api/)
- [PNCP - Portal Nacional de Contratações Públicas](https://www.gov.br/pncp/pt-br)

---

**Última atualização:** Janeiro 2026

---

## Validação Automatizada

Este documento foi validado automaticamente em **2026-01-28**. Para detalhes completos da validação, consulte:
- `/docs/fontes/portal_transparencia/VALIDACAO.md` - Relatório completo de validação
- `/docs/fontes/portal_transparencia/pncp_contratos_exemplo.json` - Exemplo de resposta da API PNCP
- `/docs/fontes/portal_transparencia/api_sem_autenticacao.json` - Resposta da API Portal Transparência sem token
