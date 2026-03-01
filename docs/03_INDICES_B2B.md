# Índices Otimizados para B2B

> Estratégia de indexação para queries de plataforma de inteligência comercial.

## Queries Mais Comuns em Plataformas B2B

### 1. Busca por Segmento (CNAE + UF + Situação)

```sql
-- "Empresas de TI ativas em São Paulo"
SELECT e.*, emp.razao_social, emp.porte_descricao
FROM estabelecimentos e
JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
WHERE e.situacao_cadastral = 2
  AND e.uf = 'SP'
  AND e.cnae_fiscal_principal LIKE '62%'
LIMIT 100;
```

### 2. Busca por Porte + Localização

```sql
-- "Micro e pequenas empresas ativas no Brasil"
SELECT e.*, emp.razao_social
FROM estabelecimentos e
JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
WHERE e.situacao_cadastral = 2
  AND emp.porte_codigo IN ('01', '03')
  AND e.uf = 'RJ'
LIMIT 100;
```

### 3. Leads com Contato (Email)

```sql
-- "Empresas com email cadastrado"
SELECT e.cnpj, e.nome_fantasia, e.email, emp.razao_social
FROM estabelecimentos e
JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
WHERE e.situacao_cadastral = 2
  AND e.email IS NOT NULL
  AND e.email != ''
  AND e.cnae_fiscal_principal LIKE '47%'  -- Varejo
LIMIT 100;
```

### 4. Busca por Sócio

```sql
-- "Empresas onde João Silva é sócio"
SELECT DISTINCT e.cnpj, emp.razao_social, s.nome_socio, s.qualificacao_socio_descricao
FROM socios s
JOIN empresas emp ON s.cnpj_basico = emp.cnpj_basico
JOIN estabelecimentos e ON s.cnpj_basico = e.cnpj_basico
WHERE s.nome_socio ILIKE '%JOAO SILVA%'
  AND e.matriz_filial = 1;  -- Só matriz
```

### 5. Empresas Optantes Simples/MEI

```sql
-- "MEIs de alimentação em Curitiba"
SELECT e.*, emp.razao_social
FROM estabelecimentos e
JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
JOIN dados_simples ds ON e.cnpj_basico = ds.cnpj_basico
WHERE ds.opcao_mei = 'S'
  AND e.situacao_cadastral = 2
  AND e.municipio_codigo = '4106902'  -- Curitiba
  AND e.cnae_fiscal_principal LIKE '56%'  -- Alimentação
LIMIT 100;
```

### 6. Agregações para Dashboard

```sql
-- "Quantidade de empresas por CNAE e UF"
SELECT
    LEFT(e.cnae_fiscal_principal, 2) as divisao_cnae,
    e.uf,
    COUNT(*) as total
FROM estabelecimentos e
WHERE e.situacao_cadastral = 2
GROUP BY LEFT(e.cnae_fiscal_principal, 2), e.uf
ORDER BY total DESC;
```

---

## Estratégia de Índices

### Princípios

1. **Índices compostos** para queries multi-coluna
2. **Partial indexes** para filtrar só registros relevantes (ativas)
3. **Covering indexes** para evitar table access
4. **GIN/GiST** para busca textual
5. **BRIN** para colunas com correlação física (datas)

---

## Índices Recomendados

### Tabela: estabelecimentos

```sql
-- ===========================================
-- ÍNDICES BÁSICOS (já existem)
-- ===========================================

CREATE INDEX idx_estab_cnpj_basico ON estabelecimentos(cnpj_basico);
CREATE INDEX idx_estab_uf ON estabelecimentos(uf);
CREATE INDEX idx_estab_municipio ON estabelecimentos(municipio_codigo);
CREATE INDEX idx_estab_situacao ON estabelecimentos(situacao_cadastral);
CREATE INDEX idx_estab_cnae ON estabelecimentos(cnae_fiscal_principal);

-- ===========================================
-- ÍNDICES B2B OTIMIZADOS (NOVOS)
-- ===========================================

-- ⚠️ NOTA SOBRE SELETIVIDADE:
-- Em teoria, colunas com MAIOR seletividade devem vir PRIMEIRO.
-- Seletividade: cnae (1300+ valores) > uf (27) > situacao (4)
--
-- PORÉM, como 99% das queries filtram situacao_cadastral = 2,
-- é MELHOR usar PARTIAL INDEX que elimina essa coluna do índice.

-- 1. Índice composto SEM partial (para queries que variam situação)
-- Usar apenas se precisar filtrar por situação diferente de 2
CREATE INDEX idx_estab_b2b_main ON estabelecimentos(
    cnae_fiscal_principal,  -- Alta seletividade primeiro
    uf,
    situacao_cadastral
);

-- 2. Partial index para empresas ATIVAS (RECOMENDADO para queries B2B)
-- Este é o índice principal - 99% das queries usam situacao_cadastral = 2
-- Partial index é ~60% menor e mais rápido que índice completo
CREATE INDEX idx_estab_ativas_uf_cnae ON estabelecimentos(
    cnae_fiscal_principal,  -- Alta seletividade primeiro
    uf
) WHERE situacao_cadastral = 2;

-- 3. Índice para busca por prefixo de CNAE (LIKE '62%')
CREATE INDEX idx_estab_cnae_prefix ON estabelecimentos(cnae_fiscal_principal text_pattern_ops)
WHERE situacao_cadastral = 2;

-- 4. Índice para leads com email
CREATE INDEX idx_estab_leads_email ON estabelecimentos(uf, cnae_fiscal_principal)
WHERE situacao_cadastral = 2
  AND email IS NOT NULL
  AND email != '';

-- 5. Índice para matrizes (evita filiais em algumas buscas)
CREATE INDEX idx_estab_matrizes ON estabelecimentos(cnpj_basico, uf)
WHERE matriz_filial = 1
  AND situacao_cadastral = 2;

-- 6. Índice BRIN para data (eficiente para ranges)
CREATE INDEX idx_estab_data_inicio_brin ON estabelecimentos
USING BRIN(data_inicio_atividade);

-- 7. Covering index para query comum (evita table access)
-- ⚠️ CUIDADO: Covering indexes aumentam storage e custo de UPDATE
--
-- Análise de trade-off:
-- - Incluir nome_fantasia (VARCHAR 200) em 51M linhas = +10GB
-- - Cada UPDATE nesses campos requer atualização do índice
--
-- RECOMENDAÇÃO: Incluir apenas PKs e campos pequenos
CREATE INDEX idx_estab_covering_b2b ON estabelecimentos(
    cnae_fiscal_principal,
    uf
) INCLUDE (cnpj, cnpj_basico)  -- Apenas PKs, não campos grandes
WHERE situacao_cadastral = 2;

-- Para queries que precisam de nome_fantasia/email com frequência,
-- o heap access de ~15ms é aceitável vs overhead de storage
```

### Tabela: empresas

```sql
-- Índice por porte (filtro B2B comum)
CREATE INDEX idx_empresas_porte ON empresas(porte_codigo);

-- Índice por capital social (ranges)
CREATE INDEX idx_empresas_capital ON empresas(capital_social);

-- Índice composto porte + capital
CREATE INDEX idx_empresas_porte_capital ON empresas(porte_codigo, capital_social);

-- Covering index para JOIN comum
-- ⚠️ razao_social é grande - avaliar se o ganho justifica o overhead
-- Para JOINs simples, o heap access é rápido o suficiente
CREATE INDEX idx_empresas_covering ON empresas(cnpj_basico)
INCLUDE (porte_codigo, capital_social);  -- Sem razao_social para economizar storage
```

### Tabela: socios

```sql
-- Índice para JOIN
CREATE INDEX idx_socios_cnpj_basico ON socios(cnpj_basico);

-- Índice para busca por CPF/CNPJ do sócio
CREATE INDEX idx_socios_documento ON socios(cpf_cnpj_socio);

-- Índice para busca por qualificação
CREATE INDEX idx_socios_qualificacao ON socios(qualificacao_socio);

-- ===========================================
-- BUSCA TEXTUAL POR NOME (requer pg_trgm)
-- ===========================================

-- Habilitar extensão
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Índice GIN para busca fuzzy por nome
CREATE INDEX idx_socios_nome_trgm ON socios
USING gin(nome_socio gin_trgm_ops);

-- Exemplo de uso:
-- SELECT * FROM socios WHERE nome_socio % 'JOAO SILVA';  -- Similaridade
-- SELECT * FROM socios WHERE nome_socio ILIKE '%SILVA%'; -- Substring
```

### Tabela: dados_simples

```sql
-- Índice para filtro Simples Nacional
CREATE INDEX idx_simples_opcao ON dados_simples(opcao_simples)
WHERE opcao_simples = 'S';

-- Índice para filtro MEI
CREATE INDEX idx_simples_mei ON dados_simples(opcao_mei)
WHERE opcao_mei = 'S';

-- Índice composto para queries combinadas
CREATE INDEX idx_simples_opcoes ON dados_simples(opcao_simples, opcao_mei);
```

---

## Análise de Performance dos Índices

### Query: Empresas de TI ativas em SP

**Sem índice otimizado:**
```
Seq Scan on estabelecimentos
  Filter: (situacao_cadastral = 2 AND uf = 'SP' AND cnae LIKE '62%')
  Rows: 150,000
  Time: ~8 seconds
```

**Com idx_estab_ativas_uf_cnae:**
```
Index Scan using idx_estab_ativas_uf_cnae
  Index Cond: (uf = 'SP' AND cnae >= '62' AND cnae < '63')
  Rows: 150,000
  Time: ~200ms
```

**Melhoria: 40x mais rápido**

---

## Manutenção de Índices

### Após Carga Mensal

```sql
-- Reindexar para eliminar bloat
REINDEX INDEX CONCURRENTLY idx_estab_b2b_main;
REINDEX INDEX CONCURRENTLY idx_estab_ativas_uf_cnae;

-- Atualizar estatísticas
ANALYZE estabelecimentos;
ANALYZE empresas;
ANALYZE socios;
ANALYZE dados_simples;
```

### Monitoramento

```sql
-- Verificar uso dos índices
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Índices não utilizados (candidatos a remoção)
SELECT
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public';
```

---

## Estimativa de Tamanho dos Índices

| Índice | Tamanho Estimado |
|--------|------------------|
| idx_estab_b2b_main | ~2 GB |
| idx_estab_ativas_uf_cnae | ~800 MB (partial) |
| idx_estab_cnae_prefix | ~1.5 GB |
| idx_estab_leads_email | ~300 MB (partial) |
| idx_socios_nome_trgm | ~1.5 GB |
| **Total índices** | **~8-10 GB** |

---

## Checklist de Implementação

- [ ] Criar extensão pg_trgm
- [ ] Criar índices básicos
- [ ] Criar índices compostos B2B
- [ ] Criar partial indexes para empresas ativas
- [ ] Criar índice GIN para busca por nome de sócio
- [ ] Configurar ANALYZE automático após carga
- [ ] Configurar monitoramento de uso de índices
