# Tabelas Auxiliares - Fontes e Documentação

Este diretório contém tabelas de lookup para enriquecer os dados do CNPJ com descrições.

## Resumo das Fontes

| Arquivo | Fonte | Versão | Oficial? | Cobertura |
|---------|-------|--------|----------|-----------|
| `cnae_ibge.csv` | IBGE/CONCLA | 2.2 (2015) | ✅ Sim | 98.6% |
| `cnae_adicional.csv` | Web scraping IBGE | 2024 | ⚠️ Manual | +1.4% |
| `natureza_juridica_2021.csv` | IBGE/CONCLA | 2021 | ✅ Sim | 100% |
| `qualificacao_socio_serpro_oficial.csv` | SERPRO/RFB | 2024 | ✅ Sim | ~95% |

---

## 1. CNAE - Classificação Nacional de Atividades Econômicas

### Fonte Oficial
- **URL**: https://concla.ibge.gov.br/classificacoes/download-concla.html
- **Arquivo**: `subclasses-cnae-2-2-estrutura.xls`
- **Versão**: CNAE-Subclasses 2.2 (vigência: janeiro/2015)
- **Registros**: 1.329 subclasses

### Problema Identificado
O arquivo XLS disponível para download está desatualizado (2015). Códigos mais recentes como:
- `5611204` - Bares sem entretenimento (128k empresas)
- `5611205` - Bares com entretenimento (82k empresas)
- `4541206` - Comércio peças motos (74k empresas)

**Estão disponíveis apenas na busca online do IBGE**, não no arquivo para download.

### Solução
Criamos `cnae_adicional.csv` com códigos obtidos via:
- Busca online IBGE: https://concla.ibge.gov.br/busca-online-cnae.html
- Consulta individual por código

### Arquivos
| Arquivo | Descrição |
|---------|-----------|
| `cnae_ibge.csv` | Fonte oficial (XLS convertido) - 1.329 códigos |
| `cnae_adicional.csv` | Adições manuais documentadas - ~20 códigos |

---

## 2. Natureza Jurídica

### Fonte Oficial
- **URL**: https://concla.ibge.gov.br/estrutura/natjur-estrutura/natureza-juridica-2021
- **Versão**: Tabela de Natureza Jurídica 2021
- **Registros**: 92 códigos
- **Legislação**: Ato Declaratório Executivo COCAD nº 8/2021

### Códigos Novos (2021)
| Código | Descrição |
|--------|-----------|
| 2348 | Empresa Simples de Inovação - Inova Simples |
| 2356 | Investidor Não Residente |
| 3328 | Plano de Benefícios de Previdência Complementar Fechada |

### Arquivos
| Arquivo | Descrição |
|---------|-----------|
| `natureza_juridica_ibge.csv` | Versão 2018 (obsoleto) |
| `natureza_juridica_2021.csv` | **Versão atual** - 92 códigos |

**Usar**: `natureza_juridica_2021.csv`

---

## 3. Qualificação de Sócios

### Fonte Oficial
- **URL**: https://bcadastros.serpro.gov.br/documentacao/dominios/pj/qualificacao_socio.csv
- **Mantenedor**: SERPRO (Serviço Federal de Processamento de Dados)
- **Legislação**: IN RFB nº 2.119/2022, Anexo V
- **Registros**: 49 códigos

### Arquivos
| Arquivo | Descrição |
|---------|-----------|
| `qualificacao_socio.csv` | Versão anterior (API SERPRO) |
| `qualificacao_socio_serpro_oficial.csv` | **Versão atual** - CSV direto do SERPRO |

**Usar**: `qualificacao_socio_serpro_oficial.csv`

---

## 4. Códigos Inválidos Identificados

Durante a análise, identificamos códigos no banco que não existem em nenhuma fonte oficial:

| Tabela | Código | Empresas | Status |
|--------|--------|----------|--------|
| CNAE | `8888888` | 10.231 | ❌ Código de teste/inválido |
| Natureza | `8885` | 1.406 | ❌ Código inválido |
| Qualificação | `50` | 18 | ⚠️ Possivelmente "Empresário" (antigo) |

**Recomendação**: Ignorar esses códigos ou mapear para "Não identificado".

---

## 5. Formato dos Arquivos

Todos os arquivos CSV seguem o padrão:
- **Encoding**: UTF-8
- **Separador**: `;` (ponto e vírgula)
- **Header**: Sim (`codigo;descricao`)

Exemplo:
```csv
codigo;descricao
0111301;Cultivo de arroz
0111302;Cultivo de milho
```

---

## 6. Como Atualizar as Tabelas de Lookup no Banco

```sql
-- 1. Criar tabela temporária
CREATE TEMP TABLE tmp_lookup (codigo VARCHAR(10), descricao TEXT);

-- 2. Importar CSV
\copy tmp_lookup FROM 'natureza_juridica_2021.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';');

-- 3. Atualizar descrições faltantes
UPDATE naturezas_juridicas nj
SET descricao = t.descricao
FROM tmp_lookup t
WHERE nj.codigo = t.codigo
  AND (nj.descricao IS NULL OR nj.descricao = '');

-- 4. Inserir códigos novos (se não existirem)
INSERT INTO naturezas_juridicas (codigo, descricao)
SELECT codigo, descricao FROM tmp_lookup t
WHERE NOT EXISTS (SELECT 1 FROM naturezas_juridicas WHERE codigo = t.codigo);
```

---

## 7. Links das Fontes Oficiais

### IBGE/CONCLA
- Download geral: https://concla.ibge.gov.br/classificacoes/download-concla.html
- CNAE busca online: https://concla.ibge.gov.br/busca-online-cnae.html
- Natureza Jurídica 2021: https://concla.ibge.gov.br/estrutura/natjur-estrutura/natureza-juridica-2021

### Receita Federal / SERPRO
- Qualificação sócios: https://bcadastros.serpro.gov.br/documentacao/dominios/pj/qualificacao_socio.csv
- Tabelas CNPJ: https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj/tabelas-utilizadas-pelo-programa-cnpj

---

## 8. Histórico de Atualizações

| Data | Alteração |
|------|-----------|
| 2026-01-22 | Criação inicial com CNAE 2.2, Natureza Jurídica 2021, Qualificação SERPRO |
| 2026-01-22 | Documentação das fontes e códigos faltantes |

---

## 9. Manutenção Futura

### Verificações Recomendadas (Trimestral)
1. Verificar se IBGE lançou nova versão do CNAE
2. Verificar atualizações na tabela de Natureza Jurídica
3. Re-baixar CSV do SERPRO para qualificações

### Quando Houver Novos Códigos no Banco
1. Pesquisar na busca online do IBGE/CONCLA
2. Documentar fonte e adicionar ao arquivo `*_adicional.csv`
3. Atualizar este README
