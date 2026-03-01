# Discussão: Infraestrutura e Custos

Resumo das decisões técnicas do projeto cnpj-data-pipeline.

---

## 1. Otimizações do ETL (após fork)

| Melhoria | O que é | Impacto |
|----------|---------|---------|
| **Leitura ISO-8859-1 direta** | Dados da RFB vêm em Latin-1. Antes convertia para UTF-8; agora lê direto. | -50% I/O |
| **StringIO em vez de BytesIO** | COPY do PostgreSQL espera texto. StringIO evita conversão extra. | -30% overhead |
| **Batch 50k → 500k** | Menos commits = menos overhead de transação. | -90% commits |
| **DROP índices antes, CREATE depois** | Índices ativos atrasam INSERT. Recriar no final é mais rápido. | -80% tempo INSERT |
| **Flag --initial-load** | INSERT direto (sem verificar duplicatas) vs UPSERT. | +150% velocidade |
| **Remoção de \x00** | Bytes nulos da RFB corrompem COPY. | Evita erros |

**Resultado:** 208M registros ingeridos, 37 arquivos, 37GB no banco.

---

## 2. Elasticsearch

### O que é
Motor de busca especializado em texto. PostgreSQL é bom para filtros exatos; Elasticsearch brilha em:

- **Busca fuzzy** — encontra "RESTAURANTE" mesmo digitando "RESTURANTE"
- **Relevância** — ordena por quão bem combina com a busca
- **Aggregations** — conta empresas por UF/CNAE em milissegundos

### Arquitetura

```
PostgreSQL (fonte da verdade)     Elasticsearch (busca rápida)
┌───────────────────────────┐     ┌───────────────────────────┐
│ 208M registros            │────▸│ 22M empresas ativas       │
│ (normalizado)             │sync │ (desnormalizado)          │
└───────────────────────────┘     └───────────────────────────┘
```

### Por que não só PostgreSQL?
- `WHERE razao_social ILIKE '%padaria%'` = full scan (lento)
- Elasticsearch: índice invertido, busca em milissegundos
- Aggregations em 200M rows: PostgreSQL lento, ES instantâneo

---

## 3. AWS: Serviços Equivalentes

| Local | AWS | Observação |
|-------|-----|------------|
| PostgreSQL 17 | **RDS for PostgreSQL** | 100% compatível, mesmo engine |
| Elasticsearch | **OpenSearch** | Fork, 99% compatível |
| Redis | **ElastiCache** | 100% compatível |
| FastAPI + React | **ECS Fargate** ou **EC2** | Containers ou VMs |

---

## 4. Amazon RDS: Como Funciona

### É uma VM dedicada
```
┌─────────────────────────────────────┐
│           Amazon RDS                │
│  ┌───────────────────────────────┐  │
│  │      EC2 (VM dedicada)        │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │     PostgreSQL 17       │  │  │
│  │  └─────────────────────────┘  │  │
│  │  • CPU/RAM só pra você        │  │
│  │  • Sem acesso SSH             │  │
│  │  • AWS gerencia o SO          │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Como cobra

| Item | Cobrança | Exemplo |
|------|----------|---------|
| Instância | Por hora ligada | db.t3.large = $0.136/h |
| Storage | Por GB/mês | gp3 = $0.115/GB |
| IOPS | Por IOPS provisionado | $0.005/IOPS |
| Transfer OUT | Por GB saindo da AWS | $0.09/GB |

**Não cobra por transação/query.**

### O que faz por você
- Backups automáticos (35 dias)
- Updates de segurança
- Failover automático (Multi-AZ)
- Monitoramento (CloudWatch)
- Escala sem downtime

---

## 5. Custos: AWS vs VPS

### Cenário: Staging + Produção

**AWS RDS (duas instâncias)**
```
Staging:  db.t3.large (2 vCPU, 8GB)  = $120/mês
Produção: db.t3.large (2 vCPU, 8GB)  = $120/mês
Storage:  200GB cada                  = $46/mês
──────────────────────────────────────────────────
Total: ~$286/mês (~R$1.600)
```

**AWS otimizado (staging sob demanda)**
```
Staging:  Liga só na semana do ETL (~48h/mês) = $8/mês
Produção: 24/7                                = $143/mês
──────────────────────────────────────────────────
Total: ~$151/mês (~R$850)
```

**Hetzner VPS**
```
Staging:  CPX11 (2 vCPU, 4GB)   = €4/mês
Produção: CPX41 (8 vCPU, 32GB)  = €36/mês
──────────────────────────────────────────────────
Total: €40/mês (~R$223)
```

### Comparativo

| Solução | Custo/mês | Fator |
|---------|-----------|-------|
| Hetzner VPS | R$223 | 1x |
| AWS otimizado | R$850 | 3.8x |
| AWS 24/7 | R$1.600 | 7.2x |

---

## 6. Quando usar cada opção

| Fase | Recomendação | Custo |
|------|--------------|-------|
| **Validação/MVP** | Hetzner CPX21 (tudo junto) | R$100/mês |
| **Primeiros clientes** | Hetzner separado (stag + prod) | R$223/mês |
| **Faturando R$10k+/mês** | AWS RDS (staging sob demanda) | R$850/mês |
| **Enterprise/Compliance** | AWS Multi-AZ + suporte | R$2.500+/mês |

---

## 7. Decisão Atual

**Para começar:** Hetzner ou servidor local.

**Migrar para AWS quando:**
- Custo de infra < 5% do faturamento
- Cliente enterprise exigir compliance
- Precisar de SLA 99.99%
- Tiver time de DevOps

---

## 8. Referências de Preço (Jan/2026)

### Hetzner Cloud
| Plano | Config | Preço |
|-------|--------|-------|
| CPX11 | 2 vCPU, 4GB, 40GB | €4/mês |
| CPX21 | 3 vCPU, 8GB, 80GB | €8/mês |
| CPX41 | 8 vCPU, 32GB, 240GB | €36/mês |

### AWS RDS PostgreSQL (us-east-1)
| Instância | Config | Preço |
|-----------|--------|-------|
| db.t3.medium | 2 vCPU, 4GB | $0.068/h (~$50/mês) |
| db.t3.large | 2 vCPU, 8GB | $0.136/h (~$100/mês) |
| db.r6g.large | 2 vCPU, 16GB | $0.192/h (~$140/mês) |
| db.r6g.xlarge | 4 vCPU, 32GB | $0.384/h (~$280/mês) |

*Multi-AZ dobra o preço da instância.*
