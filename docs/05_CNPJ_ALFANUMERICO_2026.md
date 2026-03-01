# CNPJ Alfanumérico (2026)

> ⚠️ ALERTA: A partir de **julho de 2026**, o CNPJ incluirá letras além de números.

## Anúncio Oficial

A Receita Federal anunciou que o CNPJ passará a ter formato **alfanumérico** a partir de **julho de 2026** (data atualizada).

**Fontes:**
- [Receita Federal - Anúncio Oficial](https://www.gov.br/receitafederal/pt-br/assuntos/noticias/2024/outubro/cnpj-tera-letras-e-numeros-a-partir-de-julho-de-2026)
- [Nota Técnica COCAD/SUARA/RFB nº 49/2024](https://www.nfe.fazenda.gov.br/)

---

## Mudanças no Formato

### Formato Atual (até 2025)

```
CNPJ: 12.345.678/0001-95
      ^^^^^^^^ ^^^^ ^^
      Base     Ordem DV

- Base: 8 dígitos numéricos (00.000.000 a 99.999.999)
- Ordem: 4 dígitos numéricos (0001 a 9999)
- DV: 2 dígitos verificadores numéricos
```

### Formato Novo (a partir de julho/2026)

```
CNPJ: 12.ABC.678/0001-95
      ^^^^^^^^ ^^^^ ^^
      Base     Ordem DV

- Base: 8 caracteres ALFANUMÉRICOS (letras + números)
- Ordem: 4 caracteres ALFANUMÉRICOS
- DV: 2 dígitos NUMÉRICOS (permanece apenas números!)
```

**Caracteres permitidos:** 0-9 e **TODAS as letras de A-Z** (incluindo vogais)

> ⚠️ **CORREÇÃO:** Informações anteriores diziam que vogais seriam excluídas. A Receita Federal confirmou que **todas as 26 letras** são permitidas.

---

## Impacto no Sistema

### 1. Schema do Banco de Dados

```sql
-- ANTES: VARCHAR funcionava, mas validação assumia numérico
cnpj VARCHAR(14)

-- DEPOIS: Continua VARCHAR, mas validação muda
cnpj VARCHAR(14)  -- OK, não precisa mudar tipo
```

**Ação:** Nenhuma mudança no tipo de coluna necessária.

### 2. Validação de CNPJ

```python
# ANTES: Validação numérica
def validar_cnpj(cnpj: str) -> bool:
    cnpj = re.sub(r'[^0-9]', '', cnpj)  # ❌ Remove letras!
    if len(cnpj) != 14:
        return False
    # ... cálculo de DV numérico

# DEPOIS: Validação alfanumérica
def validar_cnpj_alfanumerico(cnpj: str) -> bool:
    cnpj = re.sub(r'[^0-9A-Z]', '', cnpj.upper())  # ✅ Mantém letras
    if len(cnpj) != 14:
        return False
    # ... novo cálculo de DV (a ser definido pela RF)
```

### 3. Máscaras de Input

```javascript
// ANTES
mask: "99.999.999/9999-99"

// DEPOIS
mask: "AA.AAA.AAA/AAAA-AA"  // A = alfanumérico
```

### 4. Índices do Banco

```sql
-- Índices em VARCHAR continuam funcionando normalmente
-- Não precisa alterar
CREATE INDEX idx_cnpj ON estabelecimentos(cnpj);
```

### 5. Elasticsearch

```json
// ANTES
"cnpj": { "type": "keyword" }

// DEPOIS (sem mudança)
"cnpj": { "type": "keyword" }  // keyword aceita alfanumérico
```

---

## Algoritmo de Validação (Oficial)

A Receita Federal publicou o algoritmo na **Nota Técnica COCAD/SUARA/RFB nº 49/2024**. A conversão de caracteres usa **ASCII - 48**:

```python
def char_to_value(char: str) -> int:
    """
    Converte caractere para valor de cálculo do DV.
    Algoritmo oficial: subtrair 48 do código ASCII.

    Exemplos:
    - '0' (ASCII 48) → 0
    - '9' (ASCII 57) → 9
    - 'A' (ASCII 65) → 17
    - 'Z' (ASCII 90) → 42
    """
    return ord(char.upper()) - 48


def validar_cnpj_alfanumerico(cnpj: str) -> bool:
    """
    Validação de CNPJ alfanumérico (julho/2026+).
    Baseado na Nota Técnica COCAD/SUARA/RFB nº 49/2024.
    """
    import re

    # Limpar formatação
    cnpj = re.sub(r'[^0-9A-Z]', '', cnpj.upper())

    if len(cnpj) != 14:
        return False

    # DV é sempre numérico (últimos 2 caracteres)
    if not cnpj[12:14].isdigit():
        return False

    # Separar base + ordem + dv
    base_ordem = cnpj[:12]
    dv_informado = cnpj[12:14]

    # Converter para valores numéricos usando ASCII - 48
    valores = [char_to_value(c) for c in base_ordem]

    # Cálculo DV1 (pesos: 5,4,3,2,9,8,7,6,5,4,3,2)
    pesos_dv1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_dv1 = sum(v * p for v, p in zip(valores, pesos_dv1))
    resto_dv1 = soma_dv1 % 11
    dv1 = 0 if resto_dv1 < 2 else 11 - resto_dv1

    # Cálculo DV2 (pesos: 6,5,4,3,2,9,8,7,6,5,4,3,2)
    valores_dv2 = valores + [dv1]
    pesos_dv2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma_dv2 = sum(v * p for v, p in zip(valores_dv2, pesos_dv2))
    resto_dv2 = soma_dv2 % 11
    dv2 = 0 if resto_dv2 < 2 else 11 - resto_dv2

    # Comparar
    dv_calculado = f"{dv1}{dv2}"
    return dv_informado == dv_calculado


# Exemplo de uso
assert validar_cnpj_alfanumerico("11.222.333/0001-81")  # CNPJ numérico válido
# assert validar_cnpj_alfanumerico("AA.BBB.CCC/0001-XX")  # Testar com alfanumérico quando disponível
```

---

## Plano de Migração

### Fase 1: Preparação (Agora - 2025)

- [ ] Garantir que colunas são VARCHAR(14) - não BIGINT
- [ ] Remover validações que assumem só números
- [ ] Atualizar máscaras de input para aceitar letras
- [ ] Testar com CNPJs fictícios alfanuméricos

### Fase 2: Monitoramento (Q4 2025)

- [ ] Acompanhar publicações da Receita Federal
- [ ] Implementar algoritmo oficial de validação quando publicado
- [ ] Testar com primeiros CNPJs alfanuméricos reais

### Fase 3: Adaptação (Julho 2026)

- [ ] Atualizar bibliotecas de validação
- [ ] Verificar se ETL processa corretamente
- [ ] Monitorar erros de parsing

---

## Bibliotecas Atualizadas

### Node.js

```javascript
// cnpj-cpf-validator - JÁ SUPORTA alfanumérico
const { validate } = require('cnpj-cpf-validator');
validate('12.ABC.678/0001-XY');  // ✅
```

### Python

```python
# Verificar se biblioteca suporta alfanumérico
# Muitas ainda não suportam - usar validação customizada
```

### PHP

```php
// Verificar pacotes Laravel para CNPJ
// Provavelmente precisará atualização
```

---

## Código Defensivo

Enquanto aguardamos o algoritmo oficial, use validação permissiva:

```python
def validar_cnpj_defensivo(cnpj: str) -> bool:
    """
    Validação defensiva que aceita tanto formato
    numérico quanto alfanumérico.
    """
    # Limpar formatação
    cnpj = re.sub(r'[^0-9A-Z]', '', cnpj.upper())

    # Verificar tamanho
    if len(cnpj) != 14:
        return False

    # Se for só numérico, usar validação tradicional
    if cnpj.isdigit():
        return validar_cnpj_numerico(cnpj)

    # Se tiver letras, aceitar por enquanto (até RF publicar regra)
    # Validação básica: só caracteres permitidos
    caracteres_permitidos = set('0123456789BCDFGHJKLMNPQRSTVWXYZ')
    if not all(c in caracteres_permitidos for c in cnpj):
        return False

    return True  # Aceitar provisoriamente
```

---

## Impacto no ETL

### Download

Sem impacto - arquivos continuam CSV.

### Parsing

```python
# processor.py - garantir que não force numérico

# ❌ ERRADO
df['cnpj'] = df['cnpj'].astype(int)  # Vai quebrar com letras!

# ✅ CORRETO
df['cnpj'] = df['cnpj'].astype(str).str.strip()
```

### Validação no ETL

```python
# Adicionar validação permissiva
def processar_cnpj(valor: str) -> str:
    """Processa CNPJ permitindo alfanumérico."""
    valor = re.sub(r'[^0-9A-Z]', '', valor.upper())
    if len(valor) != 14:
        raise ValueError(f"CNPJ inválido: {valor}")
    return valor
```

---

## Checklist de Preparação

- [ ] Auditar código que assume CNPJ numérico
- [ ] Atualizar regex de validação
- [ ] Atualizar máscaras de input
- [ ] Testar com CNPJs fictícios alfanuméricos
- [ ] Documentar para equipe de desenvolvimento
- [ ] Monitorar publicações da Receita Federal
- [ ] Planejar atualização de bibliotecas

---

## Referências

- [TabNews - CNPJ Alfanumérico](https://www.tabnews.com.br/NewsletterOficial/receita-federal-anuncia-que-cnpj-passara-a-incluir-letras-e-numeros-a-partir-de-janeiro-de-2026)
- [Receita Federal - Portal](https://www.gov.br/receitafederal/)
- [cnpj-cpf-validator (Node.js)](https://github.com/FredericoSFerreira/cnpj-cpf-validator)
