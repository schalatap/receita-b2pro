# Qualidade de Dados e Tratamentos

> Tratamentos de dados identificados nos repositórios analisados.

## Problemas Conhecidos nos Arquivos da Receita Federal

### 1. Encoding

**Problema:** Arquivos vêm em ISO-8859-1 (Latin1), não UTF-8.

**Sintomas:**
- Caracteres como "ç", "ã", "é" aparecem corrompidos
- Erros de decode ao ler com UTF-8

**Solução (já implementada no cnpj-data-pipeline):**

```python
# processor.py
def _convert_encoding(file_path: Path) -> Path:
    utf8_file = Path(tempfile.mktemp(suffix=".utf8.csv"))
    with open(file_path, "r", encoding="ISO-8859-1") as infile:
        with open(utf8_file, "w", encoding="UTF-8") as outfile:
            for chunk in iter(lambda: infile.read(50 * 1024 * 1024), ""):
                outfile.write(chunk)
    return utf8_file
```

**Solução otimizada (streaming):**

```python
import codecs

def stream_with_encoding(file_path: str, encoding: str = 'iso-8859-1'):
    with open(file_path, 'rb') as f:
        reader = codecs.getreader(encoding)(f)
        for line in reader:
            yield line
```

---

### 2. Datas Inválidas

**Problema:** Campos de data com valores "0", "00000000" ou vazios.

**Exemplos:**
```
data_situacao_cadastral: "0"
data_inicio_atividade: "00000000"
data_situacao_especial: ""
```

**Solução (já implementada):**

```python
# processor.py
date_cols = {
    "EMPRECSV": [],
    "ESTABELE": ["data_situacao_cadastral", "data_inicio_atividade", "data_situacao_especial"],
    "SOCIOCSV": ["data_entrada_sociedade"],
    "SIMPLES": ["data_opcao_simples", "data_exclusao_simples", "data_opcao_mei", "data_exclusao_mei"]
}

def _transform(df: pl.DataFrame, file_type: str) -> pl.DataFrame:
    if file_type in date_cols:
        for col in date_cols[file_type]:
            df = df.with_columns(
                pl.when((pl.col(col) == "0") | (pl.col(col) == "00000000") | (pl.col(col) == ""))
                .then(None)
                .otherwise(pl.col(col))
                .alias(col)
            )
    return df
```

---

### 3. Capital Social (Formato Brasileiro)

**Problema:** Capital social vem no formato brasileiro: "1.234.567,89"

**Solução:**

```python
# processor.py
if file_type == "EMPRECSV" and "capital_social" in df.columns:
    df = df.with_columns(
        pl.col("capital_social")
        .str.replace_all(r"\.", "")  # Remove pontos de milhar
        .str.replace(",", ".")       # Troca vírgula por ponto
        .cast(pl.Float64)
    )
```

---

### 4. CNPJs com Zero à Esquerda

**Problema:** CNPJ base pode começar com zeros que são perdidos se tratado como número.

**Exemplo:**
```
cnpj_basico: "00123456"  →  123456 (ERRADO!)
```

**Solução:**

```python
# Sempre tratar como string e fazer zfill
df = df.with_columns(
    pl.col("cnpj_basico").str.zfill(8),
    pl.col("cnpj_ordem").str.zfill(4),
    pl.col("cnpj_dv").str.zfill(2)
)

# Concatenar CNPJ completo
df = df.with_columns(
    (pl.col("cnpj_basico") + pl.col("cnpj_ordem") + pl.col("cnpj_dv")).alias("cnpj")
)
```

---

### 5. CEPs Inválidos

**Problema:** CEPs podem vir com caracteres especiais ou tamanho incorreto.

**Solução:**

```python
df = df.with_columns(
    pl.col("cep")
    .str.replace_all(r"[^0-9]", "")  # Remove não-numéricos
    .str.zfill(8)                     # Preenche com zeros
)
```

---

### 6. Emails em Maiúsculo e Inválidos

**Problema:** Emails vêm em MAIÚSCULO e podem conter valores inválidos.

**Exemplos de valores inválidos encontrados:**
```
"0"
"."
"@"
"EMAIL"
"NAO TEM"
"SEM EMAIL"
"email@email"
```

**Solução (normalização + validação básica):**

```python
import re

# Regex simples - não tenta validar RFC 5322 completo
EMAIL_REGEX = re.compile(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$')

def normalizar_email(email: str) -> str | None:
    """
    Normaliza e valida email.
    Retorna None se inválido para não poluir base de leads.
    """
    if email is None:
        return None

    email = email.strip().lower()

    # Valores conhecidos como inválidos
    invalidos = {'0', '.', '@', 'email', 'nao tem', 'sem email', 'n/a', '-'}
    if email in invalidos:
        return None

    # Validação básica de formato
    if not EMAIL_REGEX.match(email):
        return None

    return email

# Aplicar no DataFrame
df = df.with_columns(
    pl.col("email")
    .map_elements(normalizar_email, return_dtype=pl.Utf8)
)
```

> ⚠️ **Nota:** Não usar validação RFC 5322 completa - é complexa e muitos emails válidos falham. A regex simples cobre 99% dos casos reais.

---

### 7. Telefones com Formato Inconsistente

**Problema:** Telefones vêm em formatos variados nos arquivos.

**Exemplos encontrados:**
```
"1133334444"      # Sem DDD separado
"11 3333-4444"    # Com formatação
"(11)33334444"    # Parcialmente formatado
"33334444"        # Sem DDD
"0"               # Inválido
""                # Vazio
```

**Solução (normalização):**

```python
def normalizar_telefone(ddd: str, telefone: str) -> str | None:
    """
    Normaliza telefone para formato padronizado.
    Retorna apenas dígitos ou None se inválido.
    """
    if not telefone:
        return None

    # Remove tudo que não é dígito
    telefone = re.sub(r'[^0-9]', '', str(telefone))
    ddd = re.sub(r'[^0-9]', '', str(ddd)) if ddd else ''

    # Valores inválidos
    if telefone in ('0', '00000000', '99999999') or len(telefone) < 8:
        return None

    # Monta telefone completo
    if ddd and len(ddd) == 2:
        return f"{ddd}{telefone}"

    return telefone if len(telefone) >= 10 else None

# Aplicar
df = df.with_columns(
    pl.struct(["ddd_1", "telefone_1"])
    .map_elements(
        lambda x: normalizar_telefone(x["ddd_1"], x["telefone_1"]),
        return_dtype=pl.Utf8
    )
    .alias("telefone_1_normalizado")
)
```

---

### 8. Backslash nos Dados

**Problema:** Alguns campos contêm backslash `\` que quebra o COPY do PostgreSQL.

**Solução (preventiva - mais eficiente que try/catch):**

```python
# Remover backslashes ANTES do COPY, não depois de falhar
def limpar_backslash(df: pl.DataFrame) -> pl.DataFrame:
    """Remove backslashes de todas as colunas string."""
    for col in df.columns:
        if df[col].dtype == pl.Utf8:
            df = df.with_columns(
                pl.col(col).str.replace_all(r"\\", "")
            )
    return df
```

> ⚠️ **Nota:** O padrão try/catch do libercapital é ineficiente - força leitura dupla do arquivo em caso de erro.

---

### 9. Caracteres de Controle

**Problema:** Alguns campos podem conter caracteres de controle (tabs, newlines) que quebram CSV.

**Solução:**

```python
import re

def limpar_texto(texto: str) -> str:
    if texto is None:
        return None
    # Remove caracteres de controle exceto espaço
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texto)

df = df.with_columns([
    pl.col(col).map_elements(limpar_texto)
    for col in df.columns
    if df[col].dtype == pl.Utf8
])
```

---

### 10. Duplicatas nos Arquivos Fonte

**Problema:** Arquivos da Receita podem conter registros duplicados.

**Solução (já implementada via UPSERT):**

```sql
-- O ON CONFLICT DO UPDATE garante idempotência
INSERT INTO estabelecimentos (...)
SELECT DISTINCT ON (cnpj) * FROM temp_table
ON CONFLICT (cnpj) DO UPDATE SET ...
```

---

### 11. Sócio sem CPF/CNPJ

**Problema:** Alguns sócios não têm documento (campo vazio), mas é parte da PK.

**Solução:**

```python
# processor.py
if file_type == "SOCIOCSV":
    df = df.with_columns(
        pl.col("cpf_cnpj_socio").fill_null("00000000000000")
    )
```

---

### 12. Verificação de Integridade dos ZIPs

**Problema:** Downloads podem corromper, especialmente com conexões instáveis ou uso de HTTP Range.

**Solução:**

```python
import zipfile
import hashlib
from pathlib import Path

def verificar_integridade_zip(arquivo: Path) -> bool:
    """
    Verifica se ZIP está íntegro.
    Retorna True se válido, False se corrompido.
    """
    try:
        with zipfile.ZipFile(arquivo, 'r') as zf:
            # Testa CRC de todos os arquivos
            resultado = zf.testzip()
            if resultado is not None:
                print(f"Arquivo corrompido dentro do ZIP: {resultado}")
                return False
        return True
    except zipfile.BadZipFile:
        print(f"ZIP corrompido: {arquivo}")
        return False
    except Exception as e:
        print(f"Erro ao verificar ZIP: {e}")
        return False

def verificar_tamanho_minimo(arquivo: Path, tamanho_min_mb: int = 1) -> bool:
    """
    Verifica se arquivo tem tamanho mínimo esperado.
    Downloads interrompidos geralmente resultam em arquivos pequenos.
    """
    tamanho_mb = arquivo.stat().st_size / (1024 * 1024)
    if tamanho_mb < tamanho_min_mb:
        print(f"Arquivo muito pequeno ({tamanho_mb:.1f}MB): {arquivo}")
        return False
    return True

# Uso no ETL
def download_com_verificacao(url: str, destino: Path, tentativas: int = 3) -> bool:
    for tentativa in range(tentativas):
        download_arquivo(url, destino)
        if verificar_tamanho_minimo(destino) and verificar_integridade_zip(destino):
            return True
        print(f"Tentativa {tentativa + 1} falhou, tentando novamente...")
        destino.unlink(missing_ok=True)
    return False
```

---

### 13. Validação de Mudança de Schema

**Problema:** A Receita Federal pode alterar o formato dos arquivos sem aviso prévio (adicionar/remover colunas, mudar ordem).

**Histórico de mudanças:**
- 2023: Adição de campos de regime tributário
- 2024: Alteração na codificação de alguns campos
- 2026: CNPJ alfanumérico (previsto)

**Solução:**

```python
# Schema esperado por tipo de arquivo
SCHEMAS_ESPERADOS = {
    "EMPRECSV": [
        "cnpj_basico", "razao_social", "natureza_juridica", "qualificacao_responsavel",
        "capital_social", "porte_empresa", "ente_federativo_responsavel"
    ],
    "ESTABELE": [
        "cnpj_basico", "cnpj_ordem", "cnpj_dv", "matriz_filial", "nome_fantasia",
        "situacao_cadastral", "data_situacao_cadastral", "motivo_situacao_cadastral",
        "nome_cidade_exterior", "pais", "data_inicio_atividade", "cnae_fiscal_principal",
        "cnae_fiscal_secundaria", "tipo_logradouro", "logradouro", "numero", "complemento",
        "bairro", "cep", "uf", "municipio", "ddd_1", "telefone_1", "ddd_2", "telefone_2",
        "ddd_fax", "fax", "email", "situacao_especial", "data_situacao_especial"
    ],
    "SOCIOCSV": [
        "cnpj_basico", "identificador_socio", "nome_socio", "cpf_cnpj_socio",
        "qualificacao_socio", "data_entrada_sociedade", "pais", "representante_legal",
        "nome_representante", "qualificacao_representante", "faixa_etaria"
    ],
    "SIMPLES": [
        "cnpj_basico", "opcao_simples", "data_opcao_simples", "data_exclusao_simples",
        "opcao_mei", "data_opcao_mei", "data_exclusao_mei"
    ]
}

def validar_schema(df: pl.DataFrame, tipo_arquivo: str) -> tuple[bool, list[str]]:
    """
    Valida se colunas do DataFrame correspondem ao schema esperado.
    Retorna (válido, lista_de_diferenças).
    """
    esperado = set(SCHEMAS_ESPERADOS.get(tipo_arquivo, []))
    recebido = set(df.columns)

    colunas_faltando = esperado - recebido
    colunas_extras = recebido - esperado

    diferencas = []
    if colunas_faltando:
        diferencas.append(f"Colunas faltando: {colunas_faltando}")
    if colunas_extras:
        diferencas.append(f"Colunas extras: {colunas_extras}")

    return len(diferencas) == 0, diferencas

# Uso no ETL
def processar_arquivo_com_validacao(arquivo: Path, tipo: str):
    df = carregar_arquivo(arquivo)

    valido, diferencas = validar_schema(df, tipo)
    if not valido:
        # Logar mudança mas continuar (pode ser coluna nova legítima)
        print(f"⚠️ ALERTA: Schema alterado para {tipo}")
        for diff in diferencas:
            print(f"   - {diff}")
        # Enviar alerta por email/Slack se configurado

    return df
```

> ⚠️ **Importante:** Não abortar ETL por mudança de schema - a Receita pode ter adicionado campo útil. Logar e alertar para revisão humana.

---

### 14. Integridade Referencial

**Problema:** Após carga, podem existir registros órfãos (FK sem PK correspondente).

**Causas comuns:**
- Arquivos processados fora de ordem
- Falha parcial no ETL
- Dados inconsistentes na fonte

**Validação pós-carga:**

```sql
-- Estabelecimentos sem empresa correspondente
SELECT COUNT(*)
FROM estabelecimentos e
LEFT JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
WHERE emp.cnpj_basico IS NULL;

-- Sócios sem empresa correspondente
SELECT COUNT(*)
FROM socios s
LEFT JOIN empresas emp ON s.cnpj_basico = emp.cnpj_basico
WHERE emp.cnpj_basico IS NULL;

-- Dados Simples sem empresa correspondente
SELECT COUNT(*)
FROM dados_simples ds
LEFT JOIN empresas emp ON ds.cnpj_basico = emp.cnpj_basico
WHERE emp.cnpj_basico IS NULL;

-- Municípios referenciados mas não existentes na tabela de lookup
SELECT DISTINCT e.municipio_codigo
FROM estabelecimentos e
LEFT JOIN municipios m ON e.municipio_codigo = m.codigo
WHERE m.codigo IS NULL
  AND e.municipio_codigo IS NOT NULL
  AND e.municipio_codigo != '';
```

**Solução (ordem de carga garantida):**

```python
# Ordem correta de processamento para garantir integridade
ORDEM_PROCESSAMENTO = [
    # 1. Tabelas de lookup (sem dependências)
    "CNAECSV",      # CNAEs
    "MOTICSV",      # Motivos situação
    "MUNICCSV",     # Municípios
    "NATJUCSV",     # Naturezas jurídicas
    "PAISCSV",      # Países
    "QUALSCSV",     # Qualificações de sócio

    # 2. Tabelas principais (dependem de lookup)
    "EMPRECSV",     # Empresas - deve vir antes de estabelecimentos/sócios

    # 3. Tabelas que dependem de empresas
    "ESTABELE",     # Estabelecimentos
    "SOCIOCSV",     # Sócios
    "SIMPLES",      # Simples Nacional
]
```

> ⚠️ **FK Deferrable:** Se usar FKs no PostgreSQL, defina como `DEFERRABLE INITIALLY DEFERRED` para permitir carga em qualquer ordem dentro da mesma transação.

---

## Validações Recomendadas

### Pós-Carga

```sql
-- Verificar duplicatas (não deveria ter com UPSERT)
SELECT cnpj, COUNT(*)
FROM estabelecimentos
GROUP BY cnpj
HAVING COUNT(*) > 1;

-- Verificar CNPJs inválidos (tamanho errado)
SELECT cnpj
FROM estabelecimentos
WHERE LENGTH(cnpj) != 14;

-- Verificar datas futuras
SELECT cnpj, data_inicio_atividade
FROM estabelecimentos
WHERE data_inicio_atividade > CURRENT_DATE;

-- Verificar UFs inválidas
SELECT DISTINCT uf
FROM estabelecimentos
WHERE uf NOT IN ('AC','AL','AP','AM','BA','CE','DF','ES','GO','MA',
                  'MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN',
                  'RS','RO','RR','SC','SP','SE','TO');

-- Verificar situação cadastral inválida
SELECT DISTINCT situacao_cadastral
FROM estabelecimentos
WHERE situacao_cadastral NOT IN (1, 2, 3, 4, 8);

-- Verificar integridade referencial
SELECT 'estabelecimentos_orfaos' as tipo, COUNT(*) as total
FROM estabelecimentos e
LEFT JOIN empresas emp ON e.cnpj_basico = emp.cnpj_basico
WHERE emp.cnpj_basico IS NULL
UNION ALL
SELECT 'socios_orfaos', COUNT(*)
FROM socios s
LEFT JOIN empresas emp ON s.cnpj_basico = emp.cnpj_basico
WHERE emp.cnpj_basico IS NULL;
```

### Relatório de Qualidade

```python
def gerar_relatorio_qualidade(conn) -> dict:
    """Gera relatório de qualidade dos dados."""
    relatorio = {}

    # Total de registros
    relatorio['total_empresas'] = conn.execute(
        "SELECT COUNT(*) FROM empresas"
    ).fetchone()[0]

    relatorio['total_estabelecimentos'] = conn.execute(
        "SELECT COUNT(*) FROM estabelecimentos"
    ).fetchone()[0]

    # Empresas ativas
    relatorio['estabelecimentos_ativos'] = conn.execute(
        "SELECT COUNT(*) FROM estabelecimentos WHERE situacao_cadastral = 2"
    ).fetchone()[0]

    # Com email
    relatorio['com_email'] = conn.execute(
        "SELECT COUNT(*) FROM estabelecimentos WHERE email IS NOT NULL AND email != ''"
    ).fetchone()[0]

    # Por UF
    relatorio['por_uf'] = dict(conn.execute(
        "SELECT uf, COUNT(*) FROM estabelecimentos GROUP BY uf ORDER BY COUNT(*) DESC"
    ).fetchall())

    # Por situação
    relatorio['por_situacao'] = dict(conn.execute(
        "SELECT situacao_cadastral, COUNT(*) FROM estabelecimentos GROUP BY situacao_cadastral"
    ).fetchall())

    return relatorio
```

---

## Checklist de Qualidade

### Pré-Download

- [ ] Verificar disponibilidade dos arquivos no portal dados.gov.br
- [ ] Verificar espaço em disco suficiente (~25GB para ZIPs + ~100GB extraído)

### Durante Download

- [ ] Verificar integridade dos ZIPs após download
- [ ] Verificar tamanho mínimo dos arquivos
- [ ] Retentar downloads corrompidos automaticamente

### Durante ETL

- [ ] Validar schema dos arquivos (alertar se mudou)
- [ ] Converter encoding ISO-8859-1 → UTF-8
- [ ] Tratar datas inválidas (0, 00000000)
- [ ] Converter capital social (formato BR → decimal)
- [ ] Padronizar CNPJs com zfill
- [ ] Limpar CEPs
- [ ] Validar e normalizar emails
- [ ] Normalizar telefones
- [ ] Remover backslashes
- [ ] Remover caracteres de controle
- [ ] Preencher CPF/CNPJ de sócio vazio
- [ ] Processar arquivos na ordem correta (lookup → empresas → dependentes)

### Pós-Carga

- [ ] Verificar ausência de duplicatas
- [ ] Verificar tamanho de CNPJs
- [ ] Verificar UFs válidas
- [ ] Verificar situações cadastrais válidas
- [ ] Verificar integridade referencial (registros órfãos)
- [ ] Gerar relatório de qualidade
- [ ] Comparar totais com carga anterior
- [ ] Alertar se totais divergirem >5% da carga anterior
