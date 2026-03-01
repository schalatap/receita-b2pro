# Validação das Fontes RAIS e CAGED

**Data da validação:** 2026-01-28

**Validado por:** Claude (assistente de IA)

---

## 1. URLs Testadas

### 1.1 Portais Oficiais

| URL | Status | Observação |
|-----|--------|------------|
| https://www.rais.gov.br/sitio/sobre.jsf | ✅ OK | Portal oficial RAIS |
| https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/rais | ✅ OK | Estatísticas RAIS 2024 |
| https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged | ✅ OK | Acesso aos microdados |
| https://caged.maisemprego.mte.gov.br/portalcaged/ | ✅ OK | Portal CAGED |
| https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho | ✅ OK | PDET - Estatísticas do Trabalho |

### 1.2 Solicitação de Dados Identificados

| URL | Status | Observação |
|-----|--------|------------|
| https://www.gov.br/pt-br/servicos/solicitar-acesso-aos-dados-identificados-rais-e-caged | ✅ OK | Instruções para solicitar dados identificados |
| estatisticastrabalho@trabalho.gov.br | ✅ Válido | Email de contato |

### 1.3 eSocial e Transição

| URL | Status | Observação |
|-----|--------|------------|
| https://www.gov.br/esocial/pt-br/noticias/substituicao-de-obrigacoes-dados-do-esocial-passaram-a-alimentar-o-caged-e-a-rais-para-obrigados | ✅ OK | Notícia sobre substituição (06/12/2022) |

### 1.4 Base dos Dados (BigQuery)

| URL | Status | Observação |
|-----|--------|------------|
| https://basedosdados.org/dataset/3e7c4d58-96ba-448e-b053-d385a829ef00 | ✅ OK | RAIS no BigQuery (sem CNPJ) |

### 1.5 Referências e Metadados

| URL | Status | Observação |
|-----|--------|------------|
| https://ces.ibge.gov.br/base-de-dados/metadados/mte/relacao-anual-de-informacoes-sociais-rais | ✅ OK | Metadados IBGE |
| https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos | ✅ OK | Dados abertos RFB |
| https://repositorio.ipea.gov.br/handle/11058/10212 | ✅ OK | Nota técnica IPEA |
| https://repositorio.ipea.gov.br/entities/publication/759e1aba-6a03-48a1-9cf9-b671dc497275 | ✅ OK | Publicação IPEA |

### 1.6 Tutoriais e Análises

| URL | Status | Observação |
|-----|--------|------------|
| https://guilhermejacob.github.io/2017/11/rais-caged-r/ | ✅ OK | Tutorial com R |
| http://cemin.wikidot.com/raisr | ✅ OK | Tutorial RAIS com R |
| https://medium.com/basedosdados/bigquery-101-8b39da1ce52b | ⚠️ 403 | Bloqueio por bot - acessível via navegador |

---

## 2. Estrutura do FTP

### 2.1 Conexão

```
Host: ftp.mtps.gov.br
Protocolo: FTP (anônimo)
Encoding: latin-1 (ISO-8859-1)
Status: ✅ ONLINE
```

### 2.2 Estrutura de Diretórios

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
│   ├── 2007 a 2019 (CAGED antigo)
│   └── EEC/
├── NOVO CAGED/
│   ├── 2020 a 2025 (por ano/mês)
│   ├── Legado/
│   └── Documentação (PDFs, layouts)
├── CAGED_AJUSTES/
│   └── 2002 a 2020
├── TRABALHO_DOMESTICO/
│   └── 2015 a 2024
├── COMUNICADO_microdados.pdf
└── NOTA_TECNICA_microdados.pdf
```

### 2.3 Arquivos RAIS 2024

| Arquivo | Tamanho | Descrição |
|---------|---------|-----------|
| RAIS_ESTAB_PUB.7z | 126,69 MB | Estabelecimentos (público) |
| RAIS_VINC_PUB_SP.7z | 1.001,76 MB | Vínculos São Paulo |
| RAIS_VINC_PUB_MG_ES_RJ.7z | - | Vínculos MG/ES/RJ |
| RAIS_VINC_PUB_SUL.7z | - | Vínculos Sul |
| RAIS_VINC_PUB_NORDESTE.7z | - | Vínculos Nordeste |
| RAIS_VINC_PUB_NORTE.7z | - | Vínculos Norte |
| RAIS_VINC_PUB_CENTRO_OESTE.7z | - | Vínculos Centro-Oeste |
| RAIS_VINC_PUB_NI.7z | - | Vínculos Não Identificados |

### 2.4 Layouts Disponíveis

| Arquivo | Período |
|---------|---------|
| RAIS_vinculos_layout.xls | Layout base |
| RAIS_vinculos_layout1985a1993.xls | 1985-1993 |
| RAIS_vinculos_layout2015.xls | 2015 |
| RAIS_vinculos_layout2016.xls | 2016 |
| RAIS_vinculos_layout2017.xls | 2017 |
| RAIS_vinculos_layout2018e2019.xls | 2018-2019 |
| RAIS_vinculos_layout2020.xls | 2020+ |

---

## 3. Confirmação das Restrições de Acesso

### 3.1 Dados Públicos (Microdados Não Identificados)

**Disponíveis livremente via FTP:**
- ✅ UF e Município (código IBGE)
- ✅ CNAE (subclasse 7 dígitos)
- ✅ Natureza Jurídica
- ✅ Porte do Estabelecimento (por faixas)
- ✅ Tamanho do Estabelecimento (faixas de funcionários)
- ✅ Remuneração
- ✅ Dados demográficos do trabalhador

**NÃO disponíveis nos microdados públicos:**
- ❌ CNPJ
- ❌ CPF / PIS do trabalhador
- ❌ Razão Social / Nome Fantasia
- ❌ Endereço completo
- ❌ Nome do trabalhador

### 3.2 Dados Identificados (Acesso Restrito)

**Quem pode solicitar:**
1. Órgãos públicos (federal, estadual, municipal) via ACT
2. Entidades da sociedade civil sem fins lucrativos via AC
3. Pesquisadores vinculados a instituições elegíveis

**Quem NÃO pode solicitar:**
- ❌ Empresas privadas com fins comerciais
- ❌ Pessoas físicas sem vínculo institucional

**Requisitos documentais:**
- CNPJ e contrato social da instituição
- Ofício formal de solicitação
- Documento de nomeação do responsável
- Minuta de Instrumento de Cooperação com Plano de Trabalho
- Termo de Compromisso e Manutenção de Sigilo

**Base legal:**
- Lei 12.527/2011 (Lei de Acesso à Informação)
- Lei 13.709/2018 (LGPD)
- Portaria MTP 671/2021 (Arts. 163-178-B)
- Portaria SEPRT 24.445/2020

---

## 4. Alternativas Viáveis para Número de Funcionários

### 4.1 Alternativas Disponíveis

| Alternativa | Viabilidade | Precisão | Custo |
|-------------|-------------|----------|-------|
| Porte da RFB (já nos dados CNPJ) | ✅ Imediata | Baixa (faixas amplas) | Gratuito |
| Capital Social + CNAE (modelo) | ✅ Imediata | Média | Gratuito |
| LinkedIn API oficial | ⚠️ Viável | Alta | ~$10k/mês |
| LinkedIn scraping (terceiros) | ⚠️ Viável | Alta | Médio |
| Vagas abertas (proxy) | ⚠️ Viável | Baixa | Gratuito-Médio |

### 4.2 Recomendação

Para a plataforma B2B:
1. **Usar porte da RFB** como proxy inicial (campo já disponível nos dados CNPJ)
2. **Criar modelo de estimativa** combinando CNAE + Capital Social + Porte
3. **Enriquecer com LinkedIn** quando orçamento permitir
4. **Validar com dados reais** de clientes/parceiros

---

## 5. Problemas Encontrados

### 5.1 Problemas Técnicos

| Problema | Impacto | Solução |
|----------|---------|---------|
| Encoding latin-1 no FTP | Baixo | Usar `encoding='latin-1'` na conexão |
| Medium retorna 403 para bots | Baixo | Acessar via navegador |
| Gov.br retorna 403 para curl | Baixo | Funciona via WebFetch/navegador |

### 5.2 Limitações dos Dados

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| CNPJ não disponível publicamente | Alto | Usar alternativas (porte, estimativas) |
| Apenas emprego CLT | Médio | Complementar com outras fontes |
| Defasagem de ~9 meses | Médio | Usar CAGED para dados mais recentes |
| Faixas em vez de números exatos | Médio | Usar modelos de estimativa |

---

## 6. Conclusões

### 6.1 O que FUNCIONA

- ✅ FTP do MTE está online e acessível
- ✅ Todas as URLs oficiais estão funcionando
- ✅ Microdados estão disponíveis de 1985 a 2024
- ✅ Layouts e documentação estão atualizados
- ✅ Base dos Dados oferece acesso via BigQuery

### 6.2 O que NÃO FUNCIONA para nossa necessidade

- ❌ Obter número exato de funcionários por CNPJ via RAIS/CAGED públicos
- ❌ Cruzar microdados com dados do CNPJ da Receita Federal
- ❌ Solicitar dados identificados para uso comercial

### 6.3 Próximos Passos

1. **Implementar estimativa de funcionários** usando modelo com Capital Social + CNAE + Porte
2. **Avaliar custo-benefício** de APIs comerciais (LinkedIn, Glassdoor)
3. **Monitorar vagas abertas** como proxy de tamanho/crescimento
4. **Documentar limitações** para usuários da plataforma

---

## Histórico de Validação

| Data | Ação |
|------|------|
| 2026-01-28 | Validação inicial completa |
