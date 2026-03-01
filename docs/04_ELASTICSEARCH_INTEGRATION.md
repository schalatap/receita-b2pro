# Integração com Elasticsearch

> Sincronização PostgreSQL → Elasticsearch para busca full-text.

---

## Estratégia de Sincronização Híbrida

A plataforma tem **duas fontes de dados** com características diferentes:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ESTRATÉGIA HÍBRIDA                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  RECEITA FEDERAL (mensal)              ENRIQUECIMENTOS (contínuo)       │
│  ┌─────────────────────────┐          ┌─────────────────────────┐      │
│  │ 60M registros           │          │ Validação emails        │      │
│  │ UPSERT completo         │          │ Validação telefones     │      │
│  │ 1x por mês              │          │ WhatsApp check          │      │
│  └───────────┬─────────────┘          │ Decisores               │      │
│              │                         │ Tecnologias             │      │
│              ▼                         │ Redes sociais           │      │
│  ┌─────────────────────────┐          │ Vagas/Intent            │      │
│  │ Script Bulk Load        │          └───────────┬─────────────┘      │
│  │ (30-60 min)             │                      │                     │
│  └───────────┬─────────────┘                      ▼                     │
│              │                         ┌─────────────────────────┐      │
│              │                         │ PGSync CDC              │      │
│              │                         │ (tempo real)            │      │
│              │                         └───────────┬─────────────┘      │
│              │                                     │                     │
│              └──────────────┬──────────────────────┘                    │
│                             ▼                                            │
│                   ┌─────────────────────────┐                           │
│                   │     Elasticsearch       │                           │
│                   │     (22M documentos)    │                           │
│                   └─────────────────────────┘                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Quando usar cada método

| Evento | Método | Tempo | Frequência |
|--------|--------|-------|------------|
| Carga mensal RFB | Bulk Load (script) | 30-60min | 1x/mês |
| Validação de email | PGSync CDC | segundos | contínuo |
| Validação de telefone | PGSync CDC | segundos | contínuo |
| WhatsApp check | PGSync CDC | segundos | contínuo |
| Novo decisor | PGSync CDC | segundos | contínuo |
| Nova tecnologia detectada | PGSync CDC | segundos | contínuo |
| Nova vaga/intent | PGSync CDC | segundos | contínuo |

### Por que não usar PGSync para tudo?

PGSync é excelente para CDC incremental, mas **não é ideal para bulk load mensal**:

| Cenário | PGSync | Bulk Script |
|---------|--------|-------------|
| 60M UPSERTs | 8-24h (muito lento) | 30-60min |
| 1000 emails validados | segundos | overkill |
| Downtime | Perde DELETEs | N/A |

**Conclusão:** Usar **ambos** - bulk para RFB, PGSync para enriquecimentos.

---

## Por que Elasticsearch?

| Funcionalidade | PostgreSQL | Elasticsearch |
|----------------|------------|---------------|
| Busca exata | ✅ Excelente | ✅ Excelente |
| Busca LIKE | ⚠️ Lento para LIKE '%termo%' | ✅ Excelente |
| Busca fuzzy | ⚠️ pg_trgm (limitado) | ✅ Nativo |
| Relevância | ❌ Não tem | ✅ Scoring avançado |
| Agregações em texto | ❌ Limitado | ✅ Excelente |
| Autocomplete | ❌ Complexo | ✅ Nativo |

**Caso de uso:** Busca por razão social, nome fantasia, endereço, nome de sócio.

---

## Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │────▶│     PGSync      │────▶│  Elasticsearch  │
│   (Source)      │ CDC │   (Sync Tool)   │     │   (Search)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │      Redis      │
                        │  (Checkpoint)   │
                        └─────────────────┘
```

---

## PGSync: Sincronização Automática

### O que é

[PGSync](https://github.com/toluaina/pgsync) é uma ferramenta de Change Data Capture (CDC) que sincroniza PostgreSQL com Elasticsearch em tempo real.

### Características

- ✅ CDC automático (INSERT, UPDATE, DELETE)
- ✅ Baixo overhead no banco
- ✅ Fault tolerant com checkpoints
- ✅ Suporta documentos nested/denormalizados
- ✅ Sincronização inicial (bulk) + incremental

### ⚠️ Limitações Conhecidas do PGSync

| Problema | Severidade | Workaround |
|----------|------------|------------|
| Projeto com desenvolvedor único | MÉDIA | Monitorar repositório, ter plano B |
| Bug com nested INSERTs | ALTA | Testar exaustivamente com sócios |
| DELETEs durante downtime não sincronizam | MÉDIA | Resync periódico completo |

**Alternativa para produção:** [Debezium](https://debezium.io/) + Kafka Connect oferece maior robustez, mas é mais complexo de configurar.

**Recomendação:** Usar PGSync para MVP/desenvolvimento. Avaliar Debezium se encontrar problemas em produção.

### Requisitos

- Python 3.8+
- PostgreSQL 9.4+ (com logical replication)
- Elasticsearch 7.x / 8.x
- Redis 3.1+ (para checkpoints)

---

## Configuração do PGSync

### 1. Habilitar Logical Replication no PostgreSQL

```sql
-- postgresql.conf
wal_level = logical
max_replication_slots = 4
max_wal_senders = 4

-- Criar slot de replicação
SELECT pg_create_logical_replication_slot('pgsync_slot', 'pgoutput');
```

### 2. Instalar PGSync

```bash
pip install pgsync
```

### 3. Arquivo de Configuração: schema.json

O schema.json define quais tabelas o PGSync monitora. **Importante:** Configurar apenas tabelas de enriquecimento, não as tabelas base da RFB (que são atualizadas via bulk).

```json
[
  {
    "database": "cnpj_database",
    "index": "empresas",
    "nodes": {
      "table": "estabelecimentos",
      "columns": [
        "cnpj",
        "cnpj_basico"
      ],
      "children": [
        {
          "table": "contatos_validados",
          "label": "contatos",
          "columns": [
            "tipo",
            "valor",
            "status",
            "score"
          ],
          "relationship": {
            "variant": "object",
            "type": "one_to_many",
            "foreign_key": {
              "child": ["estabelecimento_id"],
              "parent": ["id"]
            }
          },
          "transform": {
            "mapping": {
              "tem_email_validado": {
                "type": "boolean",
                "value": "EXISTS(SELECT 1 FROM contatos_validados WHERE tipo='email' AND status='valid')"
              }
            }
          }
        },
        {
          "table": "decisores",
          "columns": [
            "nome",
            "cargo",
            "departamento",
            "nivel",
            "email_direto",
            "telefone_direto"
          ],
          "relationship": {
            "variant": "object",
            "type": "one_to_many",
            "foreign_key": {
              "child": ["estabelecimento_id"],
              "parent": ["id"]
            }
          }
        },
        {
          "table": "tecnologias_detectadas",
          "label": "tecnologias",
          "columns": [
            "nome",
            "categoria"
          ],
          "relationship": {
            "variant": "object",
            "type": "one_to_many",
            "foreign_key": {
              "child": ["estabelecimento_id"],
              "parent": ["id"]
            }
          }
        },
        {
          "table": "redes_sociais",
          "columns": [
            "rede",
            "url",
            "seguidores"
          ],
          "relationship": {
            "variant": "object",
            "type": "one_to_many",
            "foreign_key": {
              "child": ["estabelecimento_id"],
              "parent": ["id"]
            }
          }
        },
        {
          "table": "websites",
          "columns": [
            "dominio",
            "ativo",
            "ssl_valido"
          ],
          "relationship": {
            "variant": "object",
            "type": "one_to_many",
            "foreign_key": {
              "child": ["estabelecimento_id"],
              "parent": ["id"]
            }
          }
        },
        {
          "table": "vagas_abertas",
          "columns": [
            "titulo",
            "departamento",
            "nivel",
            "data_publicacao",
            "ativa"
          ],
          "relationship": {
            "variant": "object",
            "type": "one_to_many",
            "foreign_key": {
              "child": ["estabelecimento_id"],
              "parent": ["id"]
            }
          }
        },
        {
          "table": "sinais_intencao",
          "columns": [
            "tipo_sinal",
            "score_intencao",
            "data_sinal"
          ],
          "relationship": {
            "variant": "object",
            "type": "one_to_many",
            "foreign_key": {
              "child": ["estabelecimento_id"],
              "parent": ["id"]
            }
          }
        }
      ]
    }
  }
]
```

### Fluxo de Sincronização

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUXO PGSync (ENRIQUECIMENTOS)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Validador valida email                                          │
│     ↓                                                                │
│  2. INSERT/UPDATE em contatos_validados                             │
│     ↓                                                                │
│  3. PostgreSQL gera WAL (Write-Ahead Log)                           │
│     ↓                                                                │
│  4. PGSync lê WAL via logical replication                           │
│     ↓                                                                │
│  5. PGSync atualiza documento no Elasticsearch                      │
│     ↓                                                                │
│  6. Usuário vê "tem_email_validado: true" no filtro                 │
│                                                                      │
│  Latência total: ~1-5 segundos                                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4. Variáveis de Ambiente

```bash
# .env para PGSync
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DATABASE=cnpj_database

ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USER=elastic
ELASTICSEARCH_PASSWORD=your_es_password

REDIS_HOST=localhost
REDIS_PORT=6379

SCHEMA=/path/to/schema.json
```

### 5. Executar Sincronização

```bash
# Sincronização inicial (bulk)
pgsync --config schema.json

# Modo daemon (CDC contínuo)
pgsync --config schema.json --daemon
```

---

## Mapping do Elasticsearch

### Index: empresas

```json
{
  "mappings": {
    "properties": {
      "cnpj": {
        "type": "keyword"
      },
      "cnpj_basico": {
        "type": "keyword"
      },
      "nome_fantasia": {
        "type": "text",
        "analyzer": "brazilian",
        "fields": {
          "keyword": { "type": "keyword" },
          "autocomplete": {
            "type": "text",
            "analyzer": "autocomplete",
            "search_analyzer": "autocomplete_search"
          }
        }
      },
      "razao_social": {
        "type": "text",
        "analyzer": "brazilian",
        "fields": {
          "keyword": { "type": "keyword" },
          "autocomplete": {
            "type": "text",
            "analyzer": "autocomplete",
            "search_analyzer": "autocomplete_search"
          }
        }
      },
      "situacao_cadastral": {
        "type": "integer"
      },
      "situacao_cadastral_descricao": {
        "type": "keyword"
      },
      "uf": {
        "type": "keyword"
      },
      "municipio_nome": {
        "type": "keyword"
      },
      "cnae_fiscal_principal": {
        "type": "keyword"
      },
      "cnae_fiscal_principal_descricao": {
        "type": "text",
        "analyzer": "brazilian"
      },
      "porte_codigo": {
        "type": "keyword"
      },
      "porte_descricao": {
        "type": "keyword"
      },
      "capital_social": {
        "type": "float"
      },
      "email": {
        "type": "keyword"
      },
      "logradouro": {
        "type": "text",
        "analyzer": "brazilian"
      },
      "bairro": {
        "type": "keyword"
      },
      "cep": {
        "type": "keyword"
      },
      "socios": {
        "type": "object",
        "properties": {
          "nome_socio": {
            "type": "text",
            "analyzer": "brazilian",
            "fields": {
              "keyword": { "type": "keyword" }
            }
          },
          "qualificacao_socio_descricao": {
            "type": "keyword"
          }
        }
      },
      "opcao_simples": {
        "type": "keyword"
      },
      "opcao_mei": {
        "type": "keyword"
      }
    }
  },
  "settings": {
    "analysis": {
      "analyzer": {
        "brazilian": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "asciifolding",
            "brazilian_stop",
            "brazilian_stemmer"
          ]
        },
        "autocomplete": {
          "type": "custom",
          "tokenizer": "autocomplete_tokenizer",
          "filter": ["lowercase", "asciifolding"]
        },
        "autocomplete_search": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "asciifolding"]
        }
      },
      "tokenizer": {
        "autocomplete_tokenizer": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 20,
          "token_chars": ["letter", "digit"]
        }
      },
      "filter": {
        "brazilian_stemmer": {
          "type": "stemmer",
          "language": "brazilian"
        },
        "brazilian_stop": {
          "type": "stop",
          "stopwords": "_brazilian_"
        }
      }
    },
    "number_of_shards": 3,
    "number_of_replicas": 1
  }
}
```

### Notas sobre o Mapping

#### Nested vs Object para Sócios

Usamos `"type": "object"` em vez de `"type": "nested"` para sócios. Trade-offs:

| Tipo | Prós | Contras |
|------|------|---------|
| **nested** | Correlação entre campos (nome + qualificação do mesmo sócio) | +1 documento Lucene por sócio, queries mais lentas |
| **object** | Simples, rápido | Perde correlação entre campos |

**Decisão:** Para buscas como "empresas onde JOÃO SILVA é sócio", `object` é suficiente. Use `nested` apenas se precisar de queries como "empresas onde JOÃO SILVA é ADMINISTRADOR" (correlação de campos).

#### Ordem dos Filtros no Analyzer

A ordem `asciifolding` → `brazilian_stop` → `brazilian_stemmer` é importante:
1. `asciifolding` primeiro converte "café" para "cafe"
2. `brazilian_stop` remove stopwords
3. `brazilian_stemmer` aplica stemming ao texto já normalizado

#### search_analyzer para Autocomplete

O campo autocomplete usa analyzers diferentes para indexação e busca:
- **Index:** `edge_ngram` gera tokens como "CO", "COM", "COME", "COMER", "COMERC"...
- **Search:** `standard` busca pelo termo exato digitado

Sem `search_analyzer`, uma busca por "COMERCIO" geraria também "CO", "COM", etc., causando resultados incorretos.

---

## Queries no Elasticsearch

### 1. Busca por Razão Social

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "multi_match": {
            "query": "COMERCIO ALIMENTOS",
            "fields": ["razao_social^2", "nome_fantasia"],
            "type": "best_fields",
            "fuzziness": "AUTO"
          }
        }
      ],
      "filter": [
        { "term": { "situacao_cadastral": 2 } },
        { "term": { "uf": "SP" } }
      ]
    }
  },
  "size": 100
}
```

### 2. Autocomplete

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "razao_social.autocomplete": {
              "query": "COME"
            }
          }
        }
      ],
      "filter": [
        { "term": { "situacao_cadastral": 2 } }
      ]
    }
  },
  "size": 10
}
```

### 3. Busca por Sócio (Nested)

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "nested": {
            "path": "socios",
            "query": {
              "match": {
                "socios.nome_socio": "JOAO SILVA"
              }
            }
          }
        }
      ],
      "filter": [
        { "term": { "situacao_cadastral": 2 } }
      ]
    }
  }
}
```

### 4. Agregações para Dashboard

```json
{
  "size": 0,
  "query": {
    "term": { "situacao_cadastral": 2 }
  },
  "aggs": {
    "por_uf": {
      "terms": {
        "field": "uf",
        "size": 27
      }
    },
    "por_porte": {
      "terms": {
        "field": "porte_descricao",
        "size": 10
      }
    },
    "por_cnae": {
      "terms": {
        "field": "cnae_fiscal_principal",
        "size": 20
      }
    }
  }
}
```

---

## Integração com Laravel

### Scout Driver para Elasticsearch

```php
// config/scout.php
'driver' => 'elasticsearch',

'elasticsearch' => [
    'hosts' => [
        env('ELASTICSEARCH_HOST', 'localhost:9200'),
    ],
    'index' => env('ELASTICSEARCH_INDEX', 'empresas'),
],
```

### Model Searchable

```php
// app/Models/Estabelecimento.php
use Laravel\Scout\Searchable;

class Estabelecimento extends Model
{
    use Searchable;

    public function searchableAs(): string
    {
        return 'empresas';
    }

    public function toSearchableArray(): array
    {
        // PGSync já sincroniza, não precisa definir aqui
        return [];
    }
}
```

### Controller de Busca

```php
// app/Http/Controllers/SearchController.php
use Elastic\Elasticsearch\ClientBuilder;

class SearchController extends Controller
{
    private $elasticsearch;

    public function __construct()
    {
        $this->elasticsearch = ClientBuilder::create()
            ->setHosts([config('scout.elasticsearch.hosts')])
            ->build();
    }

    public function search(Request $request)
    {
        $query = $request->input('q');
        $uf = $request->input('uf');
        $cnae = $request->input('cnae');

        $body = [
            'query' => [
                'bool' => [
                    'must' => [],
                    'filter' => [
                        ['term' => ['situacao_cadastral' => 2]]
                    ]
                ]
            ],
            'size' => 100
        ];

        if ($query) {
            $body['query']['bool']['must'][] = [
                'multi_match' => [
                    'query' => $query,
                    'fields' => ['razao_social^2', 'nome_fantasia'],
                    'fuzziness' => 'AUTO'
                ]
            ];
        }

        if ($uf) {
            $body['query']['bool']['filter'][] = ['term' => ['uf' => $uf]];
        }

        if ($cnae) {
            $body['query']['bool']['filter'][] = ['prefix' => ['cnae_fiscal_principal' => $cnae]];
        }

        $response = $this->elasticsearch->search([
            'index' => 'empresas',
            'body' => $body
        ]);

        return response()->json($response['hits']['hits']);
    }
}
```

---

## Bulk Load Mensal (Carga RFB)

Script otimizado para reindexar todo o Elasticsearch após carga mensal da Receita Federal.

### Script de Bulk Load

```python
#!/usr/bin/env python3
"""
bulk_load_elasticsearch.py

Reindexação completa do Elasticsearch após carga mensal da Receita Federal.
Usa estratégia de índice alias para zero-downtime.
"""

import os
import json
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk
import psycopg2
import psycopg2.extras

# Configuração
ES_HOST = os.environ.get('ELASTICSEARCH_HOST', 'localhost:9200')
ES_USER = os.environ.get('ELASTICSEARCH_USER', 'elastic')
ES_PASSWORD = os.environ.get('ELASTICSEARCH_PASSWORD')
PG_DSN = os.environ.get('DATABASE_URL')
INDEX_ALIAS = 'empresas'
BATCH_SIZE = 5000
THREAD_COUNT = 4


def get_elasticsearch_client():
    """Cria cliente Elasticsearch."""
    return Elasticsearch(
        [ES_HOST],
        basic_auth=(ES_USER, ES_PASSWORD) if ES_PASSWORD else None,
        request_timeout=60
    )


def get_postgres_connection():
    """Cria conexão PostgreSQL."""
    return psycopg2.connect(PG_DSN)


def create_new_index(es, index_name):
    """Cria novo índice com mapping completo."""
    mapping = {
        "settings": {
            "number_of_shards": 3,
            "number_of_replicas": 0,  # Zero durante bulk, aumentar depois
            "refresh_interval": "-1",  # Desabilitar durante bulk
            "analysis": {
                "analyzer": {
                    "brazilian": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding", "brazilian_stop", "brazilian_stemmer"]
                    },
                    "autocomplete": {
                        "type": "custom",
                        "tokenizer": "autocomplete_tokenizer",
                        "filter": ["lowercase", "asciifolding"]
                    },
                    "autocomplete_search": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding"]
                    }
                },
                "tokenizer": {
                    "autocomplete_tokenizer": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 20,
                        "token_chars": ["letter", "digit"]
                    }
                },
                "filter": {
                    "brazilian_stemmer": {"type": "stemmer", "language": "brazilian"},
                    "brazilian_stop": {"type": "stop", "stopwords": "_brazilian_"}
                }
            }
        },
        "mappings": {
            "properties": {
                # Identificação
                "cnpj": {"type": "keyword"},
                "cnpj_basico": {"type": "keyword"},

                # Nomes (busca full-text)
                "razao_social": {
                    "type": "text",
                    "analyzer": "brazilian",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "autocomplete": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"}
                    }
                },
                "nome_fantasia": {
                    "type": "text",
                    "analyzer": "brazilian",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "autocomplete": {"type": "text", "analyzer": "autocomplete", "search_analyzer": "autocomplete_search"}
                    }
                },

                # Filtros básicos
                "situacao_cadastral": {"type": "integer"},
                "uf": {"type": "keyword"},
                "municipio_nome": {"type": "keyword"},
                "cnae_fiscal_principal": {"type": "keyword"},
                "cnae_fiscal_principal_descricao": {"type": "text", "analyzer": "brazilian"},
                "porte_codigo": {"type": "keyword"},
                "capital_social": {"type": "float"},
                "data_abertura": {"type": "date"},

                # Simples/MEI
                "opcao_simples": {"type": "boolean"},
                "opcao_mei": {"type": "boolean"},

                # Contatos RFB
                "email": {"type": "keyword"},
                "telefone_1": {"type": "keyword"},
                "telefone_2": {"type": "keyword"},

                # Endereço
                "logradouro": {"type": "text", "analyzer": "brazilian"},
                "bairro": {"type": "keyword"},
                "cep": {"type": "keyword"},

                # Sócios (array de objetos)
                "socios": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "text", "analyzer": "brazilian", "fields": {"keyword": {"type": "keyword"}}},
                        "qualificacao": {"type": "keyword"}
                    }
                },

                # ========================================
                # CAMPOS DE ENRIQUECIMENTO
                # ========================================

                # Contatos validados
                "tem_email_validado": {"type": "boolean"},
                "tem_telefone_validado": {"type": "boolean"},
                "tem_whatsapp": {"type": "boolean"},
                "score_contato": {"type": "integer"},

                # Decisores
                "decisores": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "text", "analyzer": "brazilian"},
                        "cargo": {"type": "keyword"},
                        "departamento": {"type": "keyword"},
                        "nivel": {"type": "keyword"},
                        "tem_email": {"type": "boolean"},
                        "tem_telefone": {"type": "boolean"}
                    }
                },

                # Tecnologias
                "tecnologias": {"type": "keyword"},

                # Redes sociais
                "tem_linkedin": {"type": "boolean"},
                "tem_instagram": {"type": "boolean"},
                "tem_facebook": {"type": "boolean"},
                "tem_website": {"type": "boolean"},

                # Intent/Sinais
                "vagas_abertas": {"type": "integer"},
                "ultimo_sinal_intencao": {"type": "date"},
                "score_intencao": {"type": "integer"},

                # Governo
                "fornecedor_governo": {"type": "boolean"},
                "valor_contratos_governo": {"type": "float"},

                # Metadados
                "ultima_atualizacao": {"type": "date"},
                "fontes_enriquecimento": {"type": "keyword"}
            }
        }
    }

    es.indices.create(index=index_name, body=mapping)
    print(f"Índice {index_name} criado")


def generate_documents(pg_conn):
    """
    Generator que lê do PostgreSQL em batches.
    Usa cursor server-side para não carregar tudo em memória.
    """
    with pg_conn.cursor(name='bulk_cursor', cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.itersize = BATCH_SIZE

        # Query com JOINs para dados denormalizados + enriquecimentos
        cur.execute("""
            SELECT
                e.cnpj,
                e.cnpj_basico,
                e.nome_fantasia,
                e.situacao_cadastral,
                e.uf,
                m.nome as municipio_nome,
                e.cnae_fiscal_principal,
                c.descricao as cnae_fiscal_principal_descricao,
                e.data_inicio_atividade as data_abertura,
                e.email,
                CONCAT(e.ddd_1, e.telefone_1) as telefone_1,
                CONCAT(e.ddd_2, e.telefone_2) as telefone_2,
                e.logradouro,
                e.bairro,
                e.cep,
                emp.razao_social,
                emp.porte_codigo,
                emp.capital_social,
                ds.opcao_simples,
                ds.opcao_mei,

                -- Enriquecimentos agregados
                (SELECT COUNT(*) > 0 FROM contatos_validados cv
                 WHERE cv.estabelecimento_id = e.id AND cv.tipo = 'email' AND cv.status = 'valid') as tem_email_validado,
                (SELECT COUNT(*) > 0 FROM contatos_validados cv
                 WHERE cv.estabelecimento_id = e.id AND cv.tipo IN ('telefone_fixo', 'telefone_movel') AND cv.status = 'valid') as tem_telefone_validado,
                (SELECT COUNT(*) > 0 FROM contatos_validados cv
                 WHERE cv.estabelecimento_id = e.id AND cv.tipo = 'whatsapp' AND cv.status = 'valid') as tem_whatsapp,
                (SELECT COUNT(*) FROM decisores d WHERE d.estabelecimento_id = e.id) as total_decisores,
                (SELECT array_agg(DISTINCT td.nome) FROM tecnologias_detectadas td
                 WHERE td.estabelecimento_id = e.id) as tecnologias,
                (SELECT COUNT(*) > 0 FROM redes_sociais rs
                 WHERE rs.estabelecimento_id = e.id AND rs.rede = 'linkedin') as tem_linkedin,
                (SELECT COUNT(*) > 0 FROM websites w
                 WHERE w.estabelecimento_id = e.id AND w.ativo = true) as tem_website,
                (SELECT COUNT(*) FROM vagas_abertas va
                 WHERE va.estabelecimento_id = e.id AND va.ativa = true) as vagas_abertas

            FROM estabelecimentos e
            JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
            LEFT JOIN municipios m ON e.municipio_codigo = m.codigo
            LEFT JOIN cnaes c ON e.cnae_fiscal_principal = c.codigo
            LEFT JOIN dados_simples ds ON e.cnpj_basico = ds.cnpj_basico
            WHERE e.situacao_cadastral = 2  -- Apenas ativas
        """)

        count = 0
        for row in cur:
            doc = {
                "_id": row['cnpj'],
                "_source": {
                    "cnpj": row['cnpj'],
                    "cnpj_basico": row['cnpj_basico'],
                    "razao_social": row['razao_social'],
                    "nome_fantasia": row['nome_fantasia'],
                    "situacao_cadastral": row['situacao_cadastral'],
                    "uf": row['uf'],
                    "municipio_nome": row['municipio_nome'],
                    "cnae_fiscal_principal": row['cnae_fiscal_principal'],
                    "cnae_fiscal_principal_descricao": row['cnae_fiscal_principal_descricao'],
                    "porte_codigo": row['porte_codigo'],
                    "capital_social": float(row['capital_social']) if row['capital_social'] else None,
                    "data_abertura": row['data_abertura'].isoformat() if row['data_abertura'] else None,
                    "email": row['email'],
                    "telefone_1": row['telefone_1'],
                    "telefone_2": row['telefone_2'],
                    "logradouro": row['logradouro'],
                    "bairro": row['bairro'],
                    "cep": row['cep'],
                    "opcao_simples": row['opcao_simples'] == 'S' if row['opcao_simples'] else False,
                    "opcao_mei": row['opcao_mei'] == 'S' if row['opcao_mei'] else False,

                    # Enriquecimentos
                    "tem_email_validado": row['tem_email_validado'],
                    "tem_telefone_validado": row['tem_telefone_validado'],
                    "tem_whatsapp": row['tem_whatsapp'],
                    "tecnologias": row['tecnologias'] or [],
                    "tem_linkedin": row['tem_linkedin'],
                    "tem_website": row['tem_website'],
                    "vagas_abertas": row['vagas_abertas'] or 0,

                    "ultima_atualizacao": datetime.now().isoformat()
                }
            }

            yield doc
            count += 1

            if count % 100000 == 0:
                print(f"Processados: {count:,}")

        print(f"Total processado: {count:,}")


def bulk_load():
    """Executa bulk load completo."""
    es = get_elasticsearch_client()
    pg_conn = get_postgres_connection()

    # Criar novo índice com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_index = f"{INDEX_ALIAS}_{timestamp}"

    print(f"Criando índice: {new_index}")
    create_new_index(es, new_index)

    print("Iniciando bulk load...")
    success_count = 0
    error_count = 0

    for ok, result in parallel_bulk(
        es,
        ({'_index': new_index, **doc} for doc in generate_documents(pg_conn)),
        chunk_size=BATCH_SIZE,
        thread_count=THREAD_COUNT,
        raise_on_error=False
    ):
        if ok:
            success_count += 1
        else:
            error_count += 1
            if error_count <= 10:  # Log primeiros 10 erros
                print(f"Erro: {result}")

    print(f"Bulk load concluído: {success_count:,} sucessos, {error_count:,} erros")

    # Restaurar configurações de produção
    print("Otimizando índice...")
    es.indices.put_settings(index=new_index, body={
        "index": {
            "refresh_interval": "1s",
            "number_of_replicas": 1
        }
    })

    # Force merge para otimizar segmentos
    es.indices.forcemerge(index=new_index, max_num_segments=5)

    # Trocar alias (zero-downtime)
    print("Trocando alias...")
    old_indices = list(es.indices.get_alias(name=INDEX_ALIAS).keys()) if es.indices.exists_alias(name=INDEX_ALIAS) else []

    actions = [{"add": {"index": new_index, "alias": INDEX_ALIAS}}]
    for old_index in old_indices:
        actions.append({"remove": {"index": old_index, "alias": INDEX_ALIAS}})

    es.indices.update_aliases(body={"actions": actions})

    # Deletar índices antigos (manter último como backup)
    for old_index in old_indices[:-1] if len(old_indices) > 1 else []:
        print(f"Deletando índice antigo: {old_index}")
        es.indices.delete(index=old_index)

    print(f"Concluído! Alias '{INDEX_ALIAS}' agora aponta para '{new_index}'")

    pg_conn.close()


if __name__ == '__main__':
    bulk_load()
```

### Executar Bulk Load

```bash
# Após carga mensal da RFB no PostgreSQL
python bulk_load_elasticsearch.py
```

### Performance Esperada

| Volume | Threads | Tempo |
|--------|---------|-------|
| 22M docs | 1 | 2-4h |
| 22M docs | 4 | 30-60min |
| 22M docs | 8 | 15-30min |

---

## PGSync: Sincronização de Enriquecimentos

PGSync é usado **apenas para enriquecimentos**, não para carga mensal.

---

## Fluxo Operacional Mensal

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUXO OPERACIONAL MENSAL                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  DIA 1-2: Carga RFB                                                 │
│  ├── Download ZIPs da Receita Federal                               │
│  ├── ETL Python → PostgreSQL (UPSERT)                              │
│  └── ~2-3 horas                                                     │
│                                                                      │
│  DIA 2: Reindex Elasticsearch                                       │
│  ├── Pausar PGSync daemon                                           │
│  ├── Executar bulk_load_elasticsearch.py                            │
│  ├── Alias troca para novo índice (zero-downtime)                   │
│  ├── Reiniciar PGSync daemon                                        │
│  └── ~30-60 minutos                                                 │
│                                                                      │
│  DIA 3-30: Enriquecimentos                                          │
│  ├── PGSync CDC sincroniza em tempo real                            │
│  ├── Validações de email/telefone/WhatsApp                          │
│  ├── Crawling de websites                                           │
│  ├── Detecção de tecnologias                                        │
│  └── Coleta de vagas/intent                                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Checklist de Implementação

### Infraestrutura

- [ ] Habilitar logical replication no PostgreSQL
- [ ] Instalar Elasticsearch 8.x
- [ ] Instalar Redis (para checkpoints PGSync)
- [ ] Criar index template no Elasticsearch
- [ ] Configurar analyzers para português

### Bulk Load (Carga Mensal)

- [ ] Criar script bulk_load_elasticsearch.py
- [ ] Testar com subconjunto de dados
- [ ] Configurar cron/agendamento mensal
- [ ] Documentar procedimento de rollback

### PGSync (Enriquecimentos)

- [ ] Instalar PGSync
- [ ] Criar schema.json com tabelas de enriquecimento
- [ ] Testar sincronização de contatos_validados
- [ ] Testar sincronização de decisores
- [ ] Configurar PGSync como daemon (systemd)
- [ ] Configurar monitoramento de lag

### Integração Laravel

- [ ] Instalar cliente Elasticsearch PHP
- [ ] Criar SearchController
- [ ] Implementar endpoints de busca
- [ ] Implementar autocomplete
- [ ] Testar filtros combinados

### Monitoramento

- [ ] Dashboard de lag de sincronização
- [ ] Alertas se PGSync parar
- [ ] Métricas de queries lentas
- [ ] Backup de índices
