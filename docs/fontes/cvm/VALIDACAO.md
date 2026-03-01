# Validação da Fonte CVM

**Data da validação:** 2026-01-28
**Validado por:** Claude (automatizado)

---

## URLs Testadas

### Portal Principal

| URL | Status | Observação |
|-----|--------|------------|
| https://dados.cvm.gov.br/ | OK | Portal ativo, atualizado em 2024 |
| https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp | OK | DFP 2021-2025 disponíveis |
| https://dados.cvm.gov.br/dataset/cia_aberta-doc-itr | OK | ITR 2021-2025 disponíveis |
| https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre | OK | FRE 2021-2026 disponíveis |
| https://dados.cvm.gov.br/dataset/cia_aberta-cad | OK | Cadastro diário disponível |

### Downloads Diretos

| URL | Status | Tamanho |
|-----|--------|---------|
| https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv | OK | 1.4 MB |
| https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2025.zip | OK | 237 KB |
| https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_2025.zip | OK | 30 MB |
| https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_2026.zip | OK | 229 KB |
| https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/META/meta_dfp_cia_aberta_txt.zip | OK | 6.8 KB |
| https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/META/meta_cad_cia_aberta.txt | OK | 8.5 KB |

### Links de Referência

| URL | Status | Observação |
|-----|--------|------------|
| https://sistemas.cvm.gov.br/?CiaDoc= | REDIRECIONADO | Redireciona para cvmweb.cvm.gov.br (funciona) |

---

## Estrutura Real dos CSVs

### Cadastro de Companhias (cad_cia_aberta.csv)

**Encoding:** ISO-8859-1 (Latin-1)
**Separador:** ; (ponto e vírgula)
**Total de registros:** 2.654 empresas

**Colunas encontradas (47):**
```
1.  CNPJ_CIA           - CNPJ da companhia
2.  DENOM_SOCIAL       - Denominação Social (razão social)
3.  DENOM_COMERC       - Denominação Comercial (nome fantasia)
4.  DT_REG             - Data de registro na CVM
5.  DT_CONST           - Data de constituição
6.  DT_CANCEL          - Data de cancelamento
7.  MOTIVO_CANCEL      - Motivo de cancelamento
8.  SIT                - Situação (ATIVO, CANCELADA, SUSPENSO)
9.  DT_INI_SIT         - Data início da situação
10. CD_CVM             - Código CVM
11. SETOR_ATIV         - Setor de atividade
12. TP_MERC            - Tipo de mercado
13. CATEG_REG          - Categoria de registro (A, B)
14. DT_INI_CATEG       - Data início da categoria
15. SIT_EMISSOR        - Situação do emissor
16. DT_INI_SIT_EMISSOR - Data início situação emissor
17. CONTROLE_ACIONARIO - Tipo de controle
18. TP_ENDER           - Tipo de endereço
19. LOGRADOURO         - Logradouro
20. COMPL              - Complemento
21. BAIRRO             - Bairro
22. MUN                - Município
23. UF                 - UF
24. PAIS               - País
25. CEP                - CEP
26. DDD_TEL            - DDD telefone
27. TEL                - Telefone
28. DDD_FAX            - DDD fax
29. FAX                - Fax
30. EMAIL              - E-mail
31. TP_RESP            - Tipo de responsável
32. RESP               - Nome do responsável (DRI)
33. DT_INI_RESP        - Data início atuação responsável
34. LOGRADOURO_RESP    - Logradouro do responsável
35. COMPL_RESP         - Complemento responsável
36. BAIRRO_RESP        - Bairro responsável
37. MUN_RESP           - Município responsável
38. UF_RESP            - UF responsável
39. PAIS_RESP          - País responsável
40. CEP_RESP           - CEP responsável
41. DDD_TEL_RESP       - DDD telefone responsável
42. TEL_RESP           - Telefone responsável
43. DDD_FAX_RESP       - DDD fax responsável
44. FAX_RESP           - Fax responsável
45. EMAIL_RESP         - E-mail responsável
46. CNPJ_AUDITOR       - CNPJ do auditor
47. AUDITOR            - Nome do auditor
```

**Estatísticas por situação:**
| Situação | Quantidade |
|----------|------------|
| CANCELADA | 1.887 |
| ATIVO | 764 |
| SUSPENSO(A) - DECISÃO ADM | 3 |

### DRE Consolidado (dfp_cia_aberta_DRE_con_2025.csv)

**Encoding:** ISO-8859-1 (Latin-1)
**Separador:** ; (ponto e vírgula)
**Total de registros:** 600 linhas

**Colunas encontradas (15):**
```
1.  CNPJ_CIA       - CNPJ da companhia
2.  DT_REFER       - Data de referência
3.  VERSAO         - Versão do documento
4.  DENOM_CIA      - Nome da companhia
5.  CD_CVM         - Código CVM
6.  GRUPO_DFP      - Grupo da demonstração
7.  MOEDA          - Moeda (REAL)
8.  ESCALA_MOEDA   - Escala (UNIDADE ou MIL)
9.  ORDEM_EXERC    - Ordem do exercício (ÚLTIMO ou PENÚLTIMO)
10. DT_INI_EXERC   - Data início do exercício
11. DT_FIM_EXERC   - Data fim do exercício
12. CD_CONTA       - Código da conta contábil
13. DS_CONTA       - Descrição da conta
14. VL_CONTA       - Valor da conta
15. ST_CONTA_FIXA  - Conta fixa (S/N)
```

**Observação:** A coluna `COLUNA_DF` mencionada na documentação original NÃO existe no arquivo real. A coluna equivalente é `GRUPO_DFP`.

### Arquivos no ZIP DFP 2025

| Arquivo | Tamanho | Descrição |
|---------|---------|-----------|
| dfp_cia_aberta_2025.csv | 1.9 KB | Índice com links para documentos |
| dfp_cia_aberta_BPA_con_2025.csv | 241 KB | Balanço Patrimonial Ativo (Consolidado) |
| dfp_cia_aberta_BPA_ind_2025.csv | 247 KB | Balanço Patrimonial Ativo (Individual) |
| dfp_cia_aberta_BPP_con_2025.csv | 398 KB | Balanço Patrimonial Passivo (Consolidado) |
| dfp_cia_aberta_BPP_ind_2025.csv | 398 KB | Balanço Patrimonial Passivo (Individual) |
| dfp_cia_aberta_composicao_capital_2025.csv | 1.0 KB | Composição do Capital |
| dfp_cia_aberta_DFC_MD_con_2025.csv | 151 B | Fluxo de Caixa - Método Direto (Consolidado) |
| dfp_cia_aberta_DFC_MD_ind_2025.csv | 151 B | Fluxo de Caixa - Método Direto (Individual) |
| dfp_cia_aberta_DFC_MI_con_2025.csv | 242 KB | Fluxo de Caixa - Método Indireto (Consolidado) |
| dfp_cia_aberta_DFC_MI_ind_2025.csv | 234 KB | Fluxo de Caixa - Método Indireto (Individual) |
| dfp_cia_aberta_DMPL_con_2025.csv | 1.1 MB | Mutações do Patrimônio Líquido (Consolidado) |
| dfp_cia_aberta_DMPL_ind_2025.csv | 865 KB | Mutações do Patrimônio Líquido (Individual) |
| dfp_cia_aberta_DRA_con_2025.csv | 31 KB | Demonstração do Resultado Abrangente (Consolidado) |
| dfp_cia_aberta_DRA_ind_2025.csv | 22 KB | Demonstração do Resultado Abrangente (Individual) |
| dfp_cia_aberta_DRE_con_2025.csv | 124 KB | Demonstração do Resultado (Consolidado) |
| dfp_cia_aberta_DRE_ind_2025.csv | 113 KB | Demonstração do Resultado (Individual) |
| dfp_cia_aberta_DVA_con_2025.csv | 175 KB | Demonstração de Valor Adicionado (Consolidado) |
| dfp_cia_aberta_DVA_ind_2025.csv | 168 KB | Demonstração de Valor Adicionado (Individual) |
| dfp_cia_aberta_parecer_2025.csv | 233 KB | Parecer dos Auditores |

**Total:** 19 arquivos

---

## Problemas Encontrados

### 1. Coluna COLUNA_DF inexistente

**Documentação original:** Menciona coluna `COLUNA_DF` na estrutura do DRE.
**Realidade:** A coluna não existe. O campo equivalente é `GRUPO_DFP`.

### 2. Quantidade de empresas ativas desatualizada

**Documentação original:** Cita "~400-450 empresas de capital aberto".
**Realidade:** 764 empresas com status ATIVO no cadastro (incluindo todas as categorias).

### 3. Encoding dos arquivos

Todos os arquivos CSV estão em **ISO-8859-1 (Latin-1)**, não UTF-8. Isso está documentado no código Python de exemplo, mas não explicitamente na documentação.

### 4. Arquivos DRA não documentados

O ZIP do DFP contém arquivos `dfp_cia_aberta_DRA_*` (Demonstração do Resultado Abrangente) que não estão listados na tabela de arquivos da documentação.

### 5. URL de consulta de companhias

A URL `https://sistemas.cvm.gov.br/?CiaDoc=` redireciona para:
`https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/CiaAb/FormBuscaCiaAb.aspx?TipoConsult=c`

---

## Arquivos Baixados para Validação

| Arquivo | Tamanho | Descrição |
|---------|---------|-----------|
| cad_cia_aberta.csv | 1.4 MB | Cadastro completo de companhias |
| dfp_cia_aberta_2025.zip | 237 KB | DFP 2025 (compactado) |
| meta_cad_cia_aberta.txt | 8.5 KB | Dicionário de dados do cadastro |
| dfp_cia_aberta_*.csv | ~4.6 MB | Arquivos extraídos do ZIP |

---

## Conclusão

A fonte CVM está **operacional e confiável**. As URLs funcionam corretamente e os dados estão atualizados. Foram identificadas pequenas discrepâncias na documentação original que devem ser corrigidas:

1. Atualizar quantidade de empresas ativas (764, não 400-450)
2. Corrigir nome da coluna COLUNA_DF para GRUPO_DFP
3. Adicionar arquivos DRA na lista de arquivos do ZIP
4. Documentar encoding ISO-8859-1 explicitamente
5. Atualizar URL de consulta de companhias

---

*Validação realizada em 2026-01-28*
