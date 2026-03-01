# Validação das Fontes de Dados IBGE

**Data da Validação:** 2026-01-28
**Validador:** Automatizado via Claude Code

---

## 1. URLs Testadas e Status

### FTP IBGE - Censo 2022 (População)

| URL | Status | Observação |
|-----|--------|------------|
| https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Populacao_e_domicilios_Primeiros_resultados/Resultados_da_2a_apuracao_20231027/ | **OK** | Diretório acessível |
| CD2022_Populacao_Coletada_Imputada_e_Total_Municipio_e_UF_20231222.xlsx | **OK** | 316 KB, download confirmado |
| CD2022_Populacao_Coletada_Imputada_e_Total_Municipio_e_UF_20231222.ods | **OK** | 302 KB |
| CD2022_Populacao_2010_Compatibilizada_20231222.xlsx | **OK** | 313 KB |

### FTP IBGE - PIB Municipal

| URL | Status | Observação |
|-----|--------|------------|
| https://ftp.ibge.gov.br/Pib_Municipios/2022_2023/xlsx/ | **OK** | Diretório acessível |
| tabelas_completas_2022.xlsx | **OK** | 93 KB, atualizado 2025-12-23 |
| tabelas_completas_2023.xlsx | **OK** | 93 KB, atualizado 2025-12-23 |
| https://ftp.ibge.gov.br/Pib_Municipios/2021/base/ | **OK** | Dados históricos 2002-2021 disponíveis |

### GeoFTP IBGE - Localidades

| URL | Status | Observação |
|-----|--------|------------|
| https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/Localidades_do_Brasil/2022/ | **OK** | Diretório acessível |
| Localidades_Brasil_gpkg.zip | **OK** | 6.2 MB (GeoPackage) |
| Localidades_Brasil_shp.zip | **OK** | 4.3 MB (Shapefile) |
| Localidades_Municipios_kml.zip | **OK** | 181 MB (KML) |

### APIs IBGE

| URL | Status | Observação |
|-----|--------|------------|
| https://servicodados.ibge.gov.br/api/v1/localidades/municipios | **OK** | Retorna 5.570 municípios |
| https://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios | **OK** | Testado com SP |
| https://apisidra.ibge.gov.br/values/t/9514/n6/all/v/93/p/last%201 | **OK** | População Censo 2022 |
| https://servicodados.ibge.gov.br/api/v3/malhas/estados/{UF}?formato=application/vnd.geo+json | **OK** | GeoJSON válido |

### Fontes Externas

| URL | Status | Observação |
|-----|--------|------------|
| https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv | **OK** | CSV com 5.570 municípios |
| https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/15761-areas-dos-municipios.html | **OK** | Página acessível |
| https://dados.gov.br/dados/conjuntos-dados/atlasbrasil | **PARCIAL** | Requer JavaScript |
| http://www.atlasbrasil.org.br/ | **ERRO** | Connection refused |
| https://basedosdados.org/dataset/cbfc7253-089b-44e2-8825-755e1419efc8 | **OK** | IDHM 1991-2010 disponível |

---

## 2. Formatos Verificados

### API Localidades IBGE (JSON)

```json
{
  "id": 3500105,
  "nome": "Adamantina",
  "microrregiao": {
    "id": 35035,
    "nome": "Adamantina",
    "mesorregiao": {...}
  },
  "regiao-imediata": {...},
  "regiao-intermediaria": {...}
}
```

### API SIDRA - População (JSON)

```json
{
  "NC": "6",
  "NN": "Município",
  "MN": "Pessoas",
  "V": "11451999",
  "D1C": "3550308",
  "D1N": "São Paulo (SP)",
  "D2N": "População residente",
  "D3N": "2022"
}
```
- **São Paulo (SP):** 11.451.999 habitantes (Censo 2022)

### CSV Municípios Brasileiros (GitHub)

```csv
codigo_ibge,nome,latitude,longitude,capital,codigo_uf,siafi_id,ddd,fuso_horario
5200050,Abadia de Goiás,-16.7573,-49.4412,0,52,1050,62,America/Sao_Paulo
```

**Campos confirmados:**
- codigo_ibge (7 dígitos)
- nome
- latitude/longitude (decimal)
- capital (0/1)
- codigo_uf (2 dígitos)
- siafi_id (código SIAFI)
- ddd
- fuso_horario

### API Malhas (GeoJSON)

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "geometry": {
      "type": "MultiPolygon",
      "coordinates": [[[-46.6907, -21.8376], ...]]
    },
    "properties": {"codarea": "35"}
  }]
}
```

---

## 3. Amostras Baixadas

| Arquivo | Tamanho | Descrição |
|---------|---------|-----------|
| `municipios_amostra.csv` | ~300 KB | CSV completo com 5.570 municípios |
| `api_municipios_sp_amostra.json` | ~3 KB | Municípios de SP via API |
| `api_sidra_populacao_sp_amostra.json` | ~800 B | População de São Paulo/SP |
| `malha_sp_amostra.geojson` | ~2 KB | Contorno geográfico de SP (truncado) |

---

## 4. Problemas Encontrados

### 4.1 Atlas Brasil (atlasbrasil.org.br)

- **Problema:** Site retorna `ECONNREFUSED` (conexão recusada)
- **Impacto:** Não é possível acessar IDHM diretamente pelo site oficial
- **Alternativa:** Usar Base dos Dados (https://basedosdados.org) que possui os mesmos dados

### 4.2 Portal Dados Abertos (dados.gov.br)

- **Problema:** Página requer JavaScript para funcionar
- **Impacto:** Não é possível validar via fetch simples
- **Alternativa:** Acessar via navegador ou usar APIs diretas do IBGE

### 4.3 IDHM Desatualizado

- **Problema:** Dados mais recentes são de 2010 (baseados no Censo 2010)
- **Impacto:** 15+ anos de defasagem para análises atuais
- **Observação:** IDHM baseado no Censo 2022 ainda não foi publicado

### 4.4 Documentação Original

- **Problema:** Alguns caracteres com acentuação incorreta
- **Correção:** Aplicada no arquivo IBGE.md atualizado

---

## 5. Resumo da Validação

| Categoria | Total | OK | Erro | Taxa |
|-----------|-------|----|----|------|
| URLs FTP IBGE | 8 | 8 | 0 | 100% |
| APIs IBGE | 4 | 4 | 0 | 100% |
| Fontes Externas | 5 | 3 | 2 | 60% |
| **Total** | **17** | **15** | **2** | **88%** |

### Conclusão

As fontes principais do IBGE (FTP, APIs) estão **100% funcionais**. As únicas falhas são:
1. Site atlasbrasil.org.br (offline ou bloqueando requisições)
2. dados.gov.br (requer JavaScript)

Ambos têm alternativas funcionais via Base dos Dados e APIs diretas do IBGE.

---

## 6. Recomendações

1. **Para População:** Usar API SIDRA (tabela 9514) ou download direto do FTP
2. **Para PIB:** Usar FTP IBGE (tabelas_completas_2022/2023.xlsx)
3. **Para Coordenadas:** Usar repositório GitHub kelvins/municipios-brasileiros
4. **Para IDHM:** Usar Base dos Dados (BigQuery) ou aceitar defasagem de 2010
5. **Para Malhas:** Usar API de Malhas IBGE (GeoJSON nativo)

---

*Validação realizada em 2026-01-28*
