# Validação de APIs de Geocodificação

**Data da validação:** 2026-01-28
**Validador:** Pipeline ETL automatizado

---

## Resumo Executivo

| API/Serviço | Status | Retorna Coordenadas | Observações |
|-------------|--------|---------------------|-------------|
| **AwesomeAPI** | OK | Sim | Melhor opção gratuita para coordenadas |
| **BrasilAPI v2** | OK | Parcial* | Coordenadas vazias em muitos CEPs |
| **ViaCEP** | OK | Não | Apenas dados de endereço |
| **Nominatim** | OK | Sim | Rate limit 1 req/s |
| **geocodebr** | OK | Sim | Somente R, sem Python |
| **CNEFE/IBGE** | OK | Sim | 106M endereços georreferenciados |
| **CEPAberto** | OK | Sim | Requer registro |
| **OpenCage** | OK | Sim | Pago após tier gratuito |
| **LocationIQ** | OK | Sim | Pago após tier gratuito |
| **Geoapify** | OK | Sim | Pago após tier gratuito |
| **HERE** | OK | Sim | Pago após tier gratuito |
| **Google** | OK | Sim | Pago após tier gratuito |
| **Pelias** | OK | Sim | Self-hosted |

*BrasilAPI: O endpoint v2 deveria retornar coordenadas do OpenStreetMap, mas na prática retorna objetos vazios `"coordinates": {}` para a maioria dos CEPs testados.

---

## Testes Detalhados por API

### 1. AwesomeAPI CEP

**URL testada:** `https://cep.awesomeapi.com.br/json/{cep}`
**Status:** OK
**Retorna coordenadas:** SIM

#### Exemplos de Resposta

**CEP 01310-100 (Av. Paulista, São Paulo):**
```json
{
    "cep": "01310100",
    "address_type": "Avenida",
    "address_name": "Paulista",
    "address": "Avenida Paulista",
    "state": "SP",
    "district": "Bela Vista",
    "lat": "-23.5632188",
    "lng": "-46.6542596",
    "city": "São Paulo",
    "city_ibge": "3550308",
    "ddd": "11"
}
```

**CEP 22041-080 (Copacabana, Rio de Janeiro):**
```json
{
    "cep": "22041080",
    "address_type": "Rua",
    "address_name": "Anita Garibaldi",
    "address": "Rua Anita Garibaldi",
    "state": "RJ",
    "district": "Copacabana",
    "lat": "-22.9684524",
    "lng": "-43.1885849",
    "city": "Rio de Janeiro",
    "city_ibge": "3304557",
    "ddd": "21"
}
```

**CEP 30130-000 (Av. Afonso Pena, Belo Horizonte):**
```json
{
    "cep": "30130000",
    "address_type": "Avenida",
    "address_name": "Afonso Pena",
    "address": "Avenida Afonso Pena",
    "state": "MG",
    "district": "Centro",
    "lat": "-19.9322263",
    "lng": "-43.930588",
    "city": "Belo Horizonte",
    "city_ibge": "3106200",
    "ddd": "31"
}
```

**CEP 01001-000 (Praça da Sé, São Paulo):**
```json
{
    "cep": "01001000",
    "address_type": "Praça",
    "address_name": "da Sé",
    "address": "Praça da Sé",
    "state": "SP",
    "district": "Sé",
    "lat": "-23.5500806",
    "lng": "-46.6340827",
    "city": "São Paulo",
    "city_ibge": "3550308",
    "ddd": "11"
}
```

---

### 2. BrasilAPI CEP v2

**URL testada:** `https://brasilapi.com.br/api/cep/v2/{cep}`
**Status:** OK
**Retorna coordenadas:** PARCIAL (problema identificado)

#### Problema Identificado

A documentação oficial afirma que o endpoint v2 retorna coordenadas via OpenStreetMap. Porém, nos testes realizados, o campo `coordinates` retorna vazio:

**CEP 01310-100 (Av. Paulista):**
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

**CEP 22041-080 (Copacabana):**
```json
{
    "cep": "22041080",
    "state": "RJ",
    "city": "Rio de Janeiro",
    "neighborhood": "Copacabana",
    "street": "Rua Anita Garibaldi",
    "service": "open-cep",
    "location": {
        "type": "Point",
        "coordinates": {}
    }
}
```

**Causa provável:** Os dados do OpenStreetMap não estão mapeados para a maioria dos CEPs brasileiros, resultando em objetos vazios.

---

### 3. ViaCEP

**URL testada:** `https://viacep.com.br/ws/{cep}/json/`
**Status:** OK
**Retorna coordenadas:** NÃO

#### Exemplo de Resposta

**CEP 01310-100 (Av. Paulista):**
```json
{
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "complemento": "de 612 a 1510 - lado par",
    "unidade": "",
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

**Observação:** ViaCEP é excelente para dados de endereço (inclui código IBGE, DDD, região), mas não retorna latitude/longitude.

---

### 4. Nominatim (OpenStreetMap)

**URL testada:** `https://nominatim.openstreetmap.org/search`
**Status:** OK
**Retorna coordenadas:** SIM

#### Exemplo de Resposta

**Busca: "Avenida Paulista, 1000, São Paulo, SP, Brazil"**
```json
[
    {
        "place_id": 8128695,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0",
        "osm_type": "node",
        "osm_id": 4947759379,
        "lat": "-23.5648865",
        "lon": "-46.6519180",
        "class": "place",
        "type": "house",
        "place_rank": 30,
        "importance": 7.861829556720863e-05,
        "addresstype": "place",
        "name": "Edifício Paulista Mil",
        "display_name": "Edifício Paulista Mil, 1000, Avenida Paulista, Morro dos Ingleses, Bela Vista, São Paulo, Região Imediata de São Paulo, Região Metropolitana de São Paulo, São Paulo, Região Sudeste, 01310-100, Brasil",
        "boundingbox": [
            "-23.5649365",
            "-23.5648365",
            "-46.6519680",
            "-46.6518680"
        ]
    }
]
```

**Rate limit:** 1 requisição/segundo (API pública)
**Precisão:** Endereço exato (encontrou o edifício no número 1000)

---

### 5. geocodebr (IPEA)

**URL documentação:** `https://ipeagit.github.io/geocodebr/`
**URL GitHub:** `https://github.com/ipeaGIT/geocodebr`
**Status:** OK (atualizado em 27/01/2026 - versão 0.6.1)
**Retorna coordenadas:** SIM

**Características validadas:**
- Disponível apenas em R (sem versão Python)
- Base de dados: CNEFE com 106+ milhões de endereços
- Consultas ilimitadas e gratuitas
- Processa milhões de endereços em minutos
- Usado pelo IBGE, Banco Central e Ministério do Desenvolvimento Social

---

### 6. CNEFE/IBGE (Dados Brutos)

**URL FTP:** `https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/`
**URL página:** `https://www.ibge.gov.br/estatisticas/sociais/populacao/38734-cadastro-nacional-de-enderecos-para-fins-estatisticos.html`
**Status:** OK
**Retorna coordenadas:** SIM

**Características validadas:**
- 106,8 milhões de endereços (22,8% sem número)
- 100% georreferenciado (Censo 2022)
- Formato: CSV/KML
- Última atualização: 14/06/2024

---

### 7. CEPAberto

**URL:** `https://www.cepaberto.com/`
**Status:** OK
**Retorna coordenadas:** SIM (requer token)

**Características validadas:**
- 1,1+ milhão de CEPs
- 10.663 municípios
- Retorna: latitude, longitude, altitude, DDD
- Requer registro gratuito para API
- Projeto colaborativo ativo há 12+ anos

---

## Comparativo de Precisão

| API | Nível de Precisão | Margem de Erro Estimada |
|-----|------------------|------------------------|
| **Nominatim** | Endereço exato | < 10 metros |
| **geocodebr/CNEFE** | Endereço exato | < 10 metros |
| **AwesomeAPI** | Centroide CEP | 200-2000 metros |
| **BrasilAPI** | Centroide CEP* | 200-2000 metros |
| **ViaCEP** | N/A | N/A (sem coordenadas) |
| **CEPAberto** | Centroide CEP | 200-2000 metros |

*Quando disponível (frequentemente vazio)

---

## Problemas Encontrados

### 1. BrasilAPI v2 - Coordenadas Vazias

**Problema:** O endpoint CEP v2 retorna `"coordinates": {}` para a maioria dos CEPs testados.

**Impacto:** A documentação original afirmava que BrasilAPI retornaria coordenadas via OpenStreetMap, mas isso não é confiável na prática.

**Recomendação:** Usar AwesomeAPI como alternativa para obter coordenadas de CEP.

### 2. ViaCEP - Sem Coordenadas

**Problema:** ViaCEP não retorna latitude/longitude.

**Impacto:** Não pode ser usado para geocodificação, apenas para validação/enriquecimento de endereços.

### 3. geocodebr - Somente R

**Problema:** Não existe versão Python oficial do geocodebr.

**Impacto:** Necessário usar rpy2 ou subprocess para integrar com pipeline Python.

---

## Recomendações Atualizadas

### Para Geocodificação em Massa (70M endereços)

1. **Primeira opção:** geocodebr/CNEFE (gratuito, ~80-90% cobertura)
2. **Segunda opção:** Nominatim self-hosted (gratuito, fallback ~70%)
3. **Terceira opção:** AwesomeAPI (gratuito, centroide CEP)
4. **Última opção:** APIs pagas (HERE, Google) para casos críticos

### Para Consultas Pontuais

1. **AwesomeAPI:** Melhor opção gratuita com coordenadas
2. **ViaCEP:** Melhor para dados de endereço sem coordenadas
3. **BrasilAPI v2:** Usar apenas se coordenadas retornarem (verificar antes)

---

## URLs Validadas

| URL | Status | Última Verificação |
|-----|--------|-------------------|
| https://cep.awesomeapi.com.br/json/{cep} | OK | 2026-01-28 |
| https://brasilapi.com.br/api/cep/v2/{cep} | OK | 2026-01-28 |
| https://viacep.com.br/ws/{cep}/json/ | OK | 2026-01-28 |
| https://nominatim.openstreetmap.org/search | OK | 2026-01-28 |
| https://ipeagit.github.io/geocodebr/ | OK | 2026-01-28 |
| https://github.com/ipeaGIT/geocodebr | OK | 2026-01-28 |
| https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/ | OK | 2026-01-28 |
| https://www.ibge.gov.br/.../38734-cadastro-nacional-de-enderecos-para-fins-estatisticos.html | OK | 2026-01-28 |
| https://www.cepaberto.com/ | OK | 2026-01-28 |
| https://opencagedata.com/pricing | OK | 2026-01-28 |
| https://locationiq.com/pricing | OK | 2026-01-28 |
| https://www.geoapify.com/pricing/ | OK | 2026-01-28 |
| https://www.here.com/get-started/pricing | OK | 2026-01-28 |
| https://developers.google.com/maps/documentation/geocoding | OK | 2026-01-28 |
| https://www.pelias.io/ | OK | 2026-01-28 |

---

## Changelog

| Data | Alteração |
|------|-----------|
| 2026-01-28 | Documento de validação inicial criado |
