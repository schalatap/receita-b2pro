# Geocodificação de Endereços Brasileiros

Documentação técnica sobre APIs e ferramentas de geocodificação para endereços brasileiros, com foco em soluções gratuitas ou de baixo custo para processar 70 milhões de estabelecimentos.

**Última atualização:** Janeiro 2026
**Validação das APIs:** 2026-01-28 (ver `geocodificacao/VALIDACAO.md`)

---

## Índice

1. [Resumo Executivo](#resumo-executivo)
2. [Comparativo das Opções](#comparativo-das-opções)
3. [Análise Detalhada](#análise-detalhada)
   - [geocodebr (IPEA/IBGE)](#1-geocodebr-ipeaibge)
   - [CNEFE (IBGE)](#2-cnefe-ibge---dados-brutos)
   - [Nominatim (OpenStreetMap)](#3-nominatim-openstreetmap)
   - [AwesomeAPI](#4-awesomeapi-cep)
   - [BrasilAPI](#5-brasilapi)
   - [ViaCEP](#6-viacep)
   - [CEPAberto](#7-cepaberto)
   - [Google Geocoding API](#8-google-geocoding-api)
   - [HERE Geocoding API](#9-here-geocoding-api)
   - [Geoapify](#10-geoapify)
   - [OpenCage](#11-opencage)
   - [LocationIQ](#12-locationiq)
   - [Pelias (Self-hosted)](#13-pelias-self-hosted)
4. [Recomendação Final](#recomendação-final)
5. [Exemplos de Código Python](#exemplos-de-código-python)
6. [Referências](#referências)

---

## Resumo Executivo

Para geocodificar **70 milhões de estabelecimentos** brasileiros, a melhor estratégia é:

| Prioridade | Solução | Custo | Cobertura Esperada |
|------------|---------|-------|-------------------|
| 1 | **geocodebr** (IPEA) | Gratuito | ~80-90% endereços |
| 2 | **CNEFE direto** (IBGE) | Gratuito | Complementar |
| 3 | **Nominatim self-hosted** | Infra apenas | Fallback ~70% |
| 4 | APIs pagas (HERE/Google) | $$$ | Últimos 5-10% |

**Custo estimado total:** R$ 0 a R$ 50.000 (dependendo da cobertura desejada)

---

## Comparativo das Opções

### Tabela Comparativa

| Serviço | Tier Gratuito | Precisão | Cobertura BR | Self-hosted | Custo 70M |
|---------|---------------|----------|--------------|-------------|-----------|
| **geocodebr** | Ilimitado | Endereço exato | Excelente (CNEFE) | Sim (R) | R$ 0 |
| **CNEFE** | Ilimitado | Endereço exato | 106M endereços | Sim | R$ 0 |
| **Nominatim** | 1 req/s | Variável | Boa (OSM) | Sim | Infra |
| **AwesomeAPI** | Ilimitado* | Centroide CEP | Boa | Não | R$ 0 |
| **BrasilAPI** | Ilimitado* | Centroide CEP | Parcial** | Não | R$ 0 |
| **ViaCEP** | Ilimitado | N/A | Boa | Não | R$ 0 |
| **CEPAberto** | Limitado | Centroide CEP | 1.1M CEPs | Não | ? |
| **Google** | 10k/mês | Excelente | Excelente | Não | ~R$ 1.750.000 |
| **HERE** | 250k/mês | Muito boa | Muito boa | Não | ~R$ 350.000 |
| **Geoapify** | 90k/mês | Boa (OSM) | Boa | Não | ~R$ 175.000 |
| **OpenCage** | 2.5k/dia | Boa (OSM) | Boa | Não | ~R$ 385.000 |
| **LocationIQ** | 5k/dia | Boa (OSM) | Boa | Não | ~R$ 560.000 |
| **Pelias** | Ilimitado | Boa (OSM) | Boa | Sim | Infra |

*AwesomeAPI: Retorna coordenadas consistentemente
**BrasilAPI: Coordenadas via OSM frequentemente retornam vazias (validado 2026-01-28)

### Níveis de Precisão

| Nível | Descrição | Margem de Erro |
|-------|-----------|----------------|
| **Endereço exato** | Ponto no número do imóvel | < 10 metros |
| **Interpolação** | Estimativa na rua | 10-50 metros |
| **Centroide rua** | Centro da rua | 50-200 metros |
| **Centroide CEP** | Centro da área do CEP | 200-2000 metros |
| **Centroide bairro** | Centro do bairro | 1-5 km |
| **Centroide cidade** | Centro da cidade | 5-50 km |

---

## Análise Detalhada

### 1. geocodebr (IPEA/IBGE)

**A MELHOR OPÇÃO PARA O BRASIL**

O [geocodebr](https://ipeagit.github.io/geocodebr/) é um pacote desenvolvido pelo IPEA (Instituto de Pesquisa Econômica Aplicada) que utiliza dados do CNEFE/IBGE para geocodificar endereços brasileiros.

#### Características

| Aspecto | Detalhe |
|---------|---------|
| **Base de dados** | CNEFE - 106+ milhões de endereços |
| **Limite de consultas** | Ilimitado |
| **Custo** | Gratuito |
| **Precisão** | 6 níveis (endereço exato até município) |
| **Performance** | Milhões de endereços em minutos |
| **Linguagem** | R (sem versão Python oficial) |
| **Versão atual** | v0.6.1 (atualizado 27/01/2026) |

#### Níveis de Precisão Retornados

1. **numero** - Endereço exato com número
2. **logradouro** - Rua encontrada sem número exato
3. **cep** - Apenas CEP encontrado
4. **localidade** - Bairro/localidade
5. **municipio** - Apenas cidade
6. **nao_encontrado** - Sem correspondência

Cada resultado inclui `desvio_metros` estimando a incerteza.

#### Limitações

- Disponível apenas em R (sem pacote Python oficial)
- Requer download da base CNEFE (~20GB)
- Dados do Censo 2022 (pode haver endereços novos não cobertos)

#### Instalação

```r
# Via CRAN (versão estável)
install.packages("geocodebr")

# Via GitHub (versão desenvolvimento)
remotes::install_github("ipeaGIT/geocodebr")
```

#### Adoção Institucional

Utilizado por: IBGE, Banco Central do Brasil, Ministério do Desenvolvimento Social.

---

### 2. CNEFE (IBGE) - Dados Brutos

O [Cadastro Nacional de Endereços para Fins Estatísticos](https://www.ibge.gov.br/estatisticas/sociais/populacao/38734-cadastro-nacional-de-enderecos-para-fins-estatisticos.html) é a fonte de dados do geocodebr e pode ser usado diretamente.

#### Características

| Aspecto | Detalhe |
|---------|---------|
| **Total de endereços** | 106.814.877 (22,8% sem número) |
| **Cobertura** | 100% do território nacional |
| **Campos** | UF, município, logradouro, número, CEP, lat, lon |
| **Formato** | CSV/KML |
| **Atualização** | Censo 2022 (publicado 14/06/2024) |
| **Georreferenciamento** | 100% (primeiro censo totalmente georreferenciado) |

#### URL de Download

```
https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/
```

#### Vantagens para nosso caso

- Podemos criar nossa própria tabela de lookup no PostgreSQL
- JOIN direto com estabelecimentos por endereço normalizado
- Sem dependência de APIs externas

---

### 3. Nominatim (OpenStreetMap)

[Nominatim](https://nominatim.org/) é o geocoder oficial do OpenStreetMap.

#### API Pública

| Aspecto | Detalhe |
|---------|---------|
| **Rate limit** | 1 requisição/segundo |
| **Máximo diário** | ~86.400 (prática: evitar > 50.000) |
| **Custo** | Gratuito |
| **Restrições** | Proibido bulk geocoding |

**NÃO RECOMENDADO** para 70M de endereços na API pública.

#### Self-hosted

| Aspecto | Detalhe |
|---------|---------|
| **RAM mínima** | 2GB (64GB+ recomendado para planeta) |
| **Disco** | 1TB+ SSD para planeta, ~50GB para Brasil |
| **Tempo import Brasil** | 1-3 dias |
| **Performance** | ~10 req/s por servidor |

##### Requisitos para Brasil

```
RAM: 32GB recomendado
Disco: 100GB SSD
CPU: 8+ cores
Tempo de importação: 1-2 dias
```

##### Configuração PostgreSQL Recomendada

```ini
shared_buffers = 2GB
maintenance_work_mem = 10GB
autovacuum_work_mem = 2GB
work_mem = 50MB
effective_cache_size = 24GB
synchronous_commit = off
```

#### Exemplo de Resposta (validado 2026-01-28)

Busca: "Avenida Paulista, 1000, São Paulo, SP, Brazil"
```json
{
    "lat": "-23.5648865",
    "lon": "-46.6519180",
    "display_name": "Edifício Paulista Mil, 1000, Avenida Paulista, Bela Vista, São Paulo...",
    "type": "house"
}
```

---

### 4. AwesomeAPI CEP

[AwesomeAPI](https://cep.awesomeapi.com.br/) oferece consulta de CEP com coordenadas.

**RECOMENDADO** - Melhor opção gratuita para coordenadas de CEP (validado 2026-01-28).

#### Endpoint

```
GET https://cep.awesomeapi.com.br/json/{cep}
```

#### Resposta (validado 2026-01-28)

```json
{
  "cep": "01310100",
  "address_type": "Avenida",
  "address_name": "Paulista",
  "address": "Avenida Paulista",
  "district": "Bela Vista",
  "city": "São Paulo",
  "state": "SP",
  "lat": "-23.5632188",
  "lng": "-46.6542596",
  "ddd": "11",
  "city_ibge": "3550308"
}
```

#### Características

| Aspecto | Detalhe |
|---------|---------|
| **Formatos** | JSON, XML |
| **Base** | IBGE |
| **Coordenadas** | Sim, consistentes |
| **Precisão** | Centroide CEP |

---

### 5. BrasilAPI

[BrasilAPI](https://brasilapi.com.br/) é um gateway open source que agrega várias fontes.

**ATENÇÃO:** Coordenadas frequentemente retornam vazias (validado 2026-01-28).

#### Endpoint CEP v2

```
GET https://brasilapi.com.br/api/cep/v2/{cep}
```

#### Resposta (validado 2026-01-28)

```json
{
  "cep": "01310100",
  "state": "SP",
  "city": "São Paulo",
  "neighborhood": "Bela Vista",
  "street": "Avenida Paulista",
  "service": "open-cep",
  "location": {
    "type": "Point",
    "coordinates": {}
  }
}
```

#### Limitações

| Aspecto | Detalhe |
|---------|---------|
| **Coordenadas** | Via OpenStreetMap (frequentemente vazias) |
| **Precisão** | Centroide do CEP (quando disponível) |
| **Rate limit** | Não documentado oficialmente |
| **Cobertura** | Parcial para coordenadas |

**Recomendação:** Usar AwesomeAPI como alternativa para obter coordenadas.

---

### 6. ViaCEP

[ViaCEP](https://viacep.com.br/) é uma API gratuita para consulta de CEPs.

**NÃO RETORNA COORDENADAS** - Apenas dados de endereço.

#### Endpoint

```
GET https://viacep.com.br/ws/{cep}/json/
```

#### Resposta (validado 2026-01-28)

```json
{
  "cep": "01310-100",
  "logradouro": "Avenida Paulista",
  "complemento": "de 612 a 1510 - lado par",
  "bairro": "Bela Vista",
  "localidade": "São Paulo",
  "uf": "SP",
  "estado": "São Paulo",
  "regiao": "Sudeste",
  "ibge": "3550308",
  "gia": "1004",
  "ddd": "11",
  "siafi": "7107"
}
```

#### Características

| Aspecto | Detalhe |
|---------|---------|
| **Coordenadas** | Não |
| **Código IBGE** | Sim |
| **DDD** | Sim |
| **Região** | Sim |

**Uso recomendado:** Validação e enriquecimento de endereços (sem geocodificação).

---

### 7. CEPAberto

[CEPAberto](https://www.cepaberto.com/) é uma base colaborativa de CEPs geolocalizados.

#### Características

| Aspecto | Detalhe |
|---------|---------|
| **CEPs cadastrados** | 1.137.196 |
| **Cidades** | 10.663 |
| **Campos** | lat, lon, altitude, DDD |
| **API** | V3 com token |
| **Licença** | ODbL |
| **Tempo de atividade** | 12+ anos |

#### Endpoint

```
GET https://www.cepaberto.com/api/v3/cep?cep={cep}
Header: Authorization: Token token={seu_token}
```

#### Limitações

- Limite de requisições não documentado publicamente
- Precisão: centroide do CEP
- Requer registro para obter token

---

### 8. Google Geocoding API

[Google Geocoding API](https://developers.google.com/maps/documentation/geocoding) é o padrão da indústria.

#### Pricing (2025+)

| Aspecto | Detalhe |
|---------|---------|
| **Tier gratuito** | 10.000 req/mês |
| **Preço base** | $5 / 1.000 requisições |
| **Rate limit** | 3.000 req/min |
| **Desconto volume** | Até ~35% para milhões |

#### Cálculo para 70M endereços

```
70.000.000 requisições
- 10.000 gratuitas
= 69.990.000 pagas

69.990.000 * $5 / 1.000 = $349.950
Com descontos volume: ~$280.000 USD (~R$ 1.400.000)
```

**Proibitivo para nosso volume.**

---

### 9. HERE Geocoding API

[HERE](https://www.here.com/get-started/pricing) oferece um tier gratuito generoso.

#### Pricing

| Plano | Limite | Custo |
|-------|--------|-------|
| **Freemium** | 250.000/mês | Gratuito |
| **Adicional** | - | $1 / 1.000 |
| **Pro** | 1M/mês | $449/mês |

#### Cálculo para 70M endereços

```
70.000.000 requisições
- 250.000 gratuitas/mês (3M/ano)
= 67.000.000 pagas

67.000.000 * $1 / 1.000 = $67.000 USD (~R$ 335.000)
```

#### Restrição Importante

Planos padrão **não permitem armazenamento permanente** dos resultados. Licença Enterprise necessária para caching.

---

### 10. Geoapify

[Geoapify](https://www.geoapify.com/pricing/) oferece tier gratuito com batch geocoding.

#### Pricing

| Aspecto | Detalhe |
|---------|---------|
| **Tier gratuito** | 3.000/dia (90.000/mês) |
| **Batch** | 0.5 crédito por endereço |
| **Servidor dedicado** | 700 EUR/mês |

#### Cálculo para 70M endereços

```
Usando batch (0.5 crédito):
70.000.000 * 0.5 = 35.000.000 créditos

Tier gratuito: 90.000/mês = 1.080.000/ano
Tempo para 35M créditos gratuitos: ~32 anos

Preço pago: ~$0.50 / 1.000 créditos
35.000.000 * $0.50 / 1.000 = $17.500 USD (~R$ 87.500)
```

---

### 11. OpenCage

[OpenCage](https://opencagedata.com/pricing) usa dados do OpenStreetMap.

#### Pricing

| Plano | Limite | Custo/mês |
|-------|--------|-----------|
| **Trial** | 2.500/dia | Gratuito |
| **X-Small** | 10.000/dia | $50 |
| **Small** | 20.000/dia | $100 |
| **Large** | 300.000/dia | $1.000 |

#### Cálculo para 70M endereços

```
Plano Large: 300.000/dia = 9M/mês
Tempo para 70M: ~8 meses
Custo: 8 * $1.000 = $8.000 USD (~R$ 40.000)

Ou com plano menor (mais tempo):
Small (20.000/dia): ~10 anos
```

#### Vantagem

Permite armazenamento permanente dos resultados, mesmo após cancelar assinatura.

---

### 12. LocationIQ

[LocationIQ](https://locationiq.com/pricing) baseado em OpenStreetMap.

#### Pricing

| Plano | Limite | Custo/mês |
|-------|--------|-----------|
| **Free** | 5.000/dia | Gratuito |
| **Starter** | 10.000/dia | $49 |
| **Growth** | 50.000/dia | $149 |

#### Cálculo para 70M endereços

```
Plano Growth: 50.000/dia = 1.5M/mês
Tempo para 70M: ~47 meses (~4 anos)
Custo: 47 * $149 = $7.003 USD (~R$ 35.000)
```

---

### 13. Pelias (Self-hosted)

[Pelias](https://www.pelias.io/) é um geocoder open source baseado em Elasticsearch.

#### Requisitos

| Aspecto | Detalhe |
|---------|---------|
| **RAM** | 8GB+ |
| **Disco** | 300GB+ |
| **Build planeta** | < 1 dia (32 cores) |
| **Performance** | 500+ req/s |

#### Vantagens

- Completamente gratuito
- Alta performance
- Suporta OpenStreetMap, OpenAddresses, Who's on First
- Parte da Linux Foundation

#### Desvantagens

- Complexo de configurar
- Requer manutenção de infraestrutura
- Cobertura Brasil limitada pelo OSM

---

## Recomendação Final

### Estratégia em Camadas

```
Camada 1: geocodebr/CNEFE (gratuito, ~80-90% cobertura)
    │
    v
Camada 2: Nominatim self-hosted (gratuito, fallback ~70%)
    │
    v
Camada 3: AwesomeAPI (gratuito, centroide CEP)
    │
    v
Camada 4: APIs pagas para casos críticos (<5%)
```

### Implementação Sugerida

#### Fase 1: Preparação (2 semanas)

1. Download e importação do CNEFE no PostgreSQL
2. Normalização de endereços (padronização de logradouros)
3. Criação de índices para matching

#### Fase 2: Geocodificação Massiva (1-2 semanas)

1. Executar geocodebr via R para todos os estabelecimentos
2. Classificar resultados por nível de confiança
3. Armazenar lat/lon no banco

#### Fase 3: Refinamento (contínuo)

1. Nominatim self-hosted para endereços não encontrados
2. AwesomeAPI para fallback de CEP
3. APIs pagas apenas para clientes premium

### Custos Estimados

| Item | Custo |
|------|-------|
| Infraestrutura Nominatim | R$ 500-2.000/mês |
| APIs pagas (5% = 3.5M) | R$ 15.000-50.000 (one-time) |
| **Total primeiro ano** | **R$ 20.000-75.000** |

Compare com Google (R$ 1.4M) ou HERE (R$ 335.000).

---

## Exemplos de Código Python

### 1. Usando geocodebr via rpy2

```python
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
import pandas as pd

# Ativar conversão automática pandas <-> R
pandas2ri.activate()

# Carregar geocodebr no R
ro.r('''
library(geocodebr)

geocodificar_enderecos <- function(df_enderecos) {
    campos <- definir_campos(
        logradouro = "logradouro",
        numero = "numero",
        cep = "cep",
        localidade = "bairro",
        municipio = "municipio",
        estado = "uf"
    )

    resultado <- geocode(
        enderecos = df_enderecos,
        campos_endereco = campos,
        resultado_completo = TRUE,
        verboso = TRUE
    )

    return(resultado)
}
''')

# Função Python wrapper
def geocodificar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Geocodifica DataFrame de endereços usando geocodebr.

    Colunas esperadas: logradouro, numero, cep, bairro, municipio, uf
    """
    r_func = ro.globalenv['geocodificar_enderecos']
    resultado_r = r_func(df)
    return pandas2ri.rpy2py(resultado_r)

# Exemplo de uso
enderecos = pd.DataFrame({
    'logradouro': ['Avenida Paulista', 'Rua Augusta'],
    'numero': ['1000', '500'],
    'cep': ['01310100', '01305000'],
    'bairro': ['Bela Vista', 'Consolação'],
    'municipio': ['São Paulo', 'São Paulo'],
    'uf': ['SP', 'SP']
})

resultado = geocodificar(enderecos)
print(resultado[['lat', 'lon', 'precisao', 'desvio_metros']])
```

### 2. Usando AwesomeAPI (Recomendado para CEP)

```python
import httpx
import asyncio
from typing import Optional
from dataclasses import dataclass

@dataclass
class Coordenadas:
    latitude: Optional[float]
    longitude: Optional[float]
    precisao: str  # 'cep', 'nao_encontrado'

async def buscar_coordenadas_cep(cep: str) -> Coordenadas:
    """
    Busca coordenadas de um CEP via AwesomeAPI.
    Retorna centroide do CEP (precisão ~500m).
    """
    cep_limpo = cep.replace('-', '').replace('.', '')

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f'https://cep.awesomeapi.com.br/json/{cep_limpo}',
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            lat = data.get('lat')
            lng = data.get('lng')

            if lat and lng:
                return Coordenadas(
                    latitude=float(lat),
                    longitude=float(lng),
                    precisao='cep'
                )

        except Exception as e:
            print(f"Erro ao buscar CEP {cep}: {e}")

    return Coordenadas(None, None, 'nao_encontrado')

async def buscar_batch(ceps: list[str], max_concurrent: int = 10) -> list[Coordenadas]:
    """
    Busca coordenadas de múltiplos CEPs em paralelo.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def buscar_com_limite(cep):
        async with semaphore:
            return await buscar_coordenadas_cep(cep)

    tasks = [buscar_com_limite(cep) for cep in ceps]
    return await asyncio.gather(*tasks)

# Exemplo de uso
async def main():
    ceps = ['01310100', '22041080', '30130000']
    resultados = await buscar_batch(ceps)

    for cep, coord in zip(ceps, resultados):
        print(f"{cep}: {coord.latitude}, {coord.longitude} ({coord.precisao})")

asyncio.run(main())
```

### 3. Usando Nominatim (self-hosted ou público)

```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
from typing import Optional, Tuple

class GeocoderNominatim:
    def __init__(self,
                 user_agent: str = "cnpj-pipeline/1.0",
                 domain: str = "nominatim.openstreetmap.org",
                 timeout: int = 10):
        """
        Inicializa geocoder Nominatim.

        Para self-hosted, passar domain='seu-servidor.com'
        """
        self.geolocator = Nominatim(
            user_agent=user_agent,
            domain=domain,
            timeout=timeout
        )
        # Rate limiter: 1 req/s para API pública
        self.geocode = RateLimiter(
            self.geolocator.geocode,
            min_delay_seconds=1.0
        )

    def geocodificar(self,
                     logradouro: str,
                     numero: str,
                     cidade: str,
                     estado: str,
                     pais: str = "Brasil") -> Optional[Tuple[float, float]]:
        """
        Geocodifica um endereço.
        Retorna (latitude, longitude) ou None.
        """
        endereco = f"{logradouro}, {numero}, {cidade}, {estado}, {pais}"

        try:
            location = self.geocode(endereco, country_codes='br')
            if location:
                return (location.latitude, location.longitude)
        except Exception as e:
            print(f"Erro: {e}")

        return None

    def geocodificar_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Geocodifica DataFrame de endereços.

        Colunas esperadas: logradouro, numero, cidade, estado
        """
        df = df.copy()
        df['lat'] = None
        df['lon'] = None

        for idx, row in df.iterrows():
            coords = self.geocodificar(
                row['logradouro'],
                str(row.get('numero', '')),
                row['cidade'],
                row['estado']
            )
            if coords:
                df.at[idx, 'lat'] = coords[0]
                df.at[idx, 'lon'] = coords[1]

        return df

# Exemplo de uso
geocoder = GeocoderNominatim()
coords = geocoder.geocodificar(
    "Avenida Paulista",
    "1000",
    "São Paulo",
    "SP"
)
print(f"Coordenadas: {coords}")
```

### 4. Usando Google Geocoding API

```python
import googlemaps
from typing import Optional, Dict, Any
import time

class GeocoderGoogle:
    def __init__(self, api_key: str):
        self.client = googlemaps.Client(key=api_key)
        self.requests_count = 0

    def geocodificar(self, endereco: str) -> Optional[Dict[str, Any]]:
        """
        Geocodifica endereço via Google.
        Retorna dict com lat, lon, precisao, endereco_formatado.
        """
        try:
            result = self.client.geocode(
                endereco,
                region='br',
                language='pt-BR'
            )

            self.requests_count += 1

            if result:
                location = result[0]['geometry']['location']
                return {
                    'lat': location['lat'],
                    'lon': location['lng'],
                    'precisao': result[0]['geometry']['location_type'],
                    'endereco_formatado': result[0]['formatted_address']
                }

        except Exception as e:
            print(f"Erro Google API: {e}")

        return None

    def geocodificar_com_fallback(self,
                                   logradouro: str,
                                   numero: str,
                                   bairro: str,
                                   cidade: str,
                                   estado: str,
                                   cep: str) -> Optional[Dict[str, Any]]:
        """
        Tenta geocodificar com níveis decrescentes de precisão.
        """
        # Nível 1: Endereço completo
        endereco = f"{logradouro}, {numero}, {bairro}, {cidade} - {estado}, {cep}, Brasil"
        result = self.geocodificar(endereco)
        if result and result['precisao'] in ['ROOFTOP', 'RANGE_INTERPOLATED']:
            return result

        # Nível 2: Sem número
        endereco = f"{logradouro}, {bairro}, {cidade} - {estado}, Brasil"
        result = self.geocodificar(endereco)
        if result:
            result['precisao'] = 'APPROXIMATE_STREET'
            return result

        # Nível 3: Apenas CEP
        result = self.geocodificar(f"{cep}, Brasil")
        if result:
            result['precisao'] = 'CEP_CENTROID'
            return result

        return None

# Exemplo de uso
# geocoder = GeocoderGoogle(api_key="SUA_API_KEY")
# result = geocoder.geocodificar_com_fallback(
#     "Avenida Paulista", "1000", "Bela Vista",
#     "São Paulo", "SP", "01310100"
# )
```

### 5. Usando HERE Geocoding API

```python
import httpx
from typing import Optional, Dict, Any
import os

class GeocoderHERE:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('HERE_API_KEY')
        self.base_url = "https://geocode.search.hereapi.com/v1/geocode"

    async def geocodificar(self, endereco: str) -> Optional[Dict[str, Any]]:
        """
        Geocodifica endereço via HERE API.
        """
        params = {
            'q': endereco,
            'in': 'countryCode:BRA',
            'lang': 'pt-BR',
            'apiKey': self.api_key
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get('items'):
                    item = data['items'][0]
                    position = item['position']
                    return {
                        'lat': position['lat'],
                        'lon': position['lng'],
                        'precisao': item.get('resultType', 'unknown'),
                        'endereco_formatado': item.get('title', ''),
                        'score': item.get('scoring', {}).get('queryScore', 0)
                    }

            except Exception as e:
                print(f"Erro HERE API: {e}")

        return None

# Exemplo de uso
# import asyncio
# geocoder = GeocoderHERE(api_key="SUA_API_KEY")
# result = asyncio.run(geocoder.geocodificar("Avenida Paulista, 1000, São Paulo, SP"))
```

### 6. Pipeline Completo com Múltiplas Fontes

```python
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import pandas as pd

class FonteGeocoding(Enum):
    GEOCODEBR = "geocodebr"
    NOMINATIM = "nominatim"
    AWESOMEAPI = "awesomeapi"
    HERE = "here"
    GOOGLE = "google"

@dataclass
class ResultadoGeocodificacao:
    latitude: Optional[float]
    longitude: Optional[float]
    precisao: str
    fonte: FonteGeocoding
    confianca: float  # 0.0 a 1.0

class PipelineGeocodificacao:
    """
    Pipeline de geocodificação em camadas.
    Tenta fontes gratuitas primeiro, APIs pagas como fallback.
    """

    def __init__(self,
                 usar_geocodebr: bool = True,
                 usar_nominatim: bool = True,
                 usar_apis_pagas: bool = False,
                 here_api_key: str = None,
                 google_api_key: str = None):
        self.usar_geocodebr = usar_geocodebr
        self.usar_nominatim = usar_nominatim
        self.usar_apis_pagas = usar_apis_pagas

        # Inicializar geocoders conforme configuração
        if usar_nominatim:
            self.nominatim = GeocoderNominatim()

        if usar_apis_pagas and here_api_key:
            self.here = GeocoderHERE(api_key=here_api_key)

    async def geocodificar_endereco(self,
                                     logradouro: str,
                                     numero: str,
                                     bairro: str,
                                     cidade: str,
                                     estado: str,
                                     cep: str) -> ResultadoGeocodificacao:
        """
        Tenta geocodificar usando fontes em ordem de prioridade.
        """

        # 1. Tentar geocodebr (melhor para Brasil)
        if self.usar_geocodebr:
            result = self._tentar_geocodebr(
                logradouro, numero, bairro, cidade, estado, cep
            )
            if result and result.confianca > 0.8:
                return result

        # 2. Tentar AwesomeAPI (centroide CEP)
        result = await self._tentar_awesomeapi(cep)
        if result:
            return result

        # 3. Tentar Nominatim (self-hosted ou público)
        if self.usar_nominatim:
            result = self._tentar_nominatim(
                logradouro, numero, cidade, estado
            )
            if result:
                return result

        # 4. APIs pagas como último recurso
        if self.usar_apis_pagas:
            endereco = f"{logradouro}, {numero}, {bairro}, {cidade} - {estado}, Brasil"
            result = await self.here.geocodificar(endereco)
            if result:
                return ResultadoGeocodificacao(
                    latitude=result['lat'],
                    longitude=result['lon'],
                    precisao=result['precisao'],
                    fonte=FonteGeocoding.HERE,
                    confianca=result.get('score', 0.7)
                )

        # Não encontrado
        return ResultadoGeocodificacao(
            latitude=None,
            longitude=None,
            precisao='nao_encontrado',
            fonte=FonteGeocoding.GEOCODEBR,
            confianca=0.0
        )

    def _tentar_geocodebr(self, *args) -> Optional[ResultadoGeocodificacao]:
        """Placeholder - implementar via rpy2"""
        pass

    async def _tentar_awesomeapi(self, cep: str) -> Optional[ResultadoGeocodificacao]:
        coords = await buscar_coordenadas_cep(cep)
        if coords.latitude:
            return ResultadoGeocodificacao(
                latitude=coords.latitude,
                longitude=coords.longitude,
                precisao='centroide_cep',
                fonte=FonteGeocoding.AWESOMEAPI,
                confianca=0.5
            )
        return None

    def _tentar_nominatim(self, logradouro, numero, cidade, estado) -> Optional[ResultadoGeocodificacao]:
        coords = self.nominatim.geocodificar(logradouro, numero, cidade, estado)
        if coords:
            return ResultadoGeocodificacao(
                latitude=coords[0],
                longitude=coords[1],
                precisao='nominatim',
                fonte=FonteGeocoding.NOMINATIM,
                confianca=0.7
            )
        return None
```

---

## Referências

### Documentação Oficial

- [geocodebr - Documentação](https://ipeagit.github.io/geocodebr/)
- [geocodebr - GitHub](https://github.com/ipeaGIT/geocodebr)
- [CNEFE - IBGE](https://www.ibge.gov.br/estatisticas/sociais/populacao/38734-cadastro-nacional-de-enderecos-para-fins-estatisticos.html)
- [Nominatim - Manual](https://nominatim.org/release-docs/latest/)
- [Nominatim - Política de Uso](https://operations.osmfoundation.org/policies/nominatim/)
- [AwesomeAPI CEP](https://cep.awesomeapi.com.br/)
- [BrasilAPI - GitHub](https://github.com/BrasilAPI/BrasilAPI)
- [ViaCEP](https://viacep.com.br/)
- [CEPAberto](https://www.cepaberto.com/)
- [Google Geocoding API](https://developers.google.com/maps/documentation/geocoding)
- [HERE Geocoding API](https://www.here.com/get-started/pricing)
- [Geoapify](https://www.geoapify.com/pricing/)
- [OpenCage](https://opencagedata.com/pricing)
- [LocationIQ](https://locationiq.com/pricing)
- [Pelias](https://www.pelias.io/)

### Pacotes Python

- [geopy](https://pypi.org/project/geopy/) - Biblioteca Python para geocodificação
- [cep-to-coords](https://pypi.org/project/cep-to-coords/) - Converter CEP em coordenadas
- [httpx](https://www.python-httpx.org/) - Cliente HTTP async

### Artigos e Comparativos

- [Guide to Geocoding API Pricing (MapScaping)](https://mapscaping.com/guide-to-geocoding-api-pricing/)
- [Geocoding APIs Compared](https://www.bitoff.org/geocoding-apis-comparison/)
- [geocodebr - Geocracia](https://geocracia.com/geocodebr-novo-pacote-r-simplifica-geolocalizacao-de-enderecos-no-brasil/)

---

## Changelog

| Data | Alteração |
|------|-----------|
| 2026-01-28 | Documento inicial |
| 2026-01-28 | Validação das APIs - coordenadas BrasilAPI retornam vazias |
| 2026-01-28 | Correção de acentuação (UTF-8) |
| 2026-01-28 | Adicionado AwesomeAPI como opção recomendada para CEP |
| 2026-01-28 | Adicionado ViaCEP (sem coordenadas) |
| 2026-01-28 | Reorganização do índice por ordem de recomendação |
