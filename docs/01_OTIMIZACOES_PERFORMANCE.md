# Otimizações de Performance

> Baseado nas melhores práticas do **minha-receita** (Go) e outros repositórios analisados.

## 1. UNLOGGED Tables Durante Carga

### O que é
PostgreSQL permite desabilitar o WAL (Write-Ahead Log) temporariamente, eliminando o overhead de durabilidade durante bulk inserts.

### Impacto
- **2-3x mais rápido** para bulk inserts (literatura indica este range realista)
- Reduz I/O significativamente

### ⚠️ Problema com ALTER TABLE SET UNLOGGED

A abordagem de usar `ALTER TABLE ... SET UNLOGGED/LOGGED` na tabela principal tem um **custo oculto crítico**:

> Quando uma tabela é alterada de UNLOGGED para LOGGED, o PostgreSQL **reescreve a tabela inteira** no WAL. Isso significa que você não elimina o custo de escrever no WAL - apenas o adia e adiciona um ciclo extra de I/O.
>
> — [PostgreSQL Wiki](https://wiki.postgresql.org/wiki/Improve_the_performance_of_ALTER_TABLE_SET_LOGGED_UNLOGGED_statement)

### Implementação Recomendada: Staging Tables

Em vez de alterar a tabela principal, usar **tabelas de staging UNLOGGED**:

```python
# database.py - Abordagem com staging tables

def bulk_load_with_staging(self, df: pl.DataFrame, target_table: str):
    """
    Carrega dados usando staging table UNLOGGED.
    Evita o custo de reescrever a tabela principal.
    """
    staging_table = f"staging_{target_table}_{id(df)}"

    try:
        # 1. Criar staging UNLOGGED (não reescreve tabela existente)
        self.execute(f"""
            CREATE UNLOGGED TABLE {staging_table}
            (LIKE {target_table} INCLUDING DEFAULTS)
        """)

        # 2. COPY para staging (rápido, sem WAL)
        csv_buffer = df.write_csv(file=None).encode('utf-8')
        with self.conn.cursor() as cur:
            cur.copy_expert(
                f"COPY {staging_table} FROM STDIN WITH CSV",
                io.BytesIO(csv_buffer)
            )

        # 3. UPSERT para tabela final (com WAL, mas otimizado)
        pk_cols = self._get_primary_keys(target_table)
        self.execute(f"""
            INSERT INTO {target_table}
            SELECT DISTINCT ON ({', '.join(pk_cols)}) * FROM {staging_table}
            ON CONFLICT ({', '.join(pk_cols)}) DO UPDATE SET
                {', '.join(f'{col} = EXCLUDED.{col}' for col in df.columns if col not in pk_cols)}
        """)
        self.conn.commit()

    finally:
        # 4. Drop staging (sempre, mesmo com erro)
        self.execute(f"DROP TABLE IF EXISTS {staging_table}")
```

### Por que Staging Tables?

| Abordagem | Prós | Contras |
|-----------|------|---------|
| ALTER TABLE SET UNLOGGED | Simples | Reescreve tabela inteira ao voltar para LOGGED |
| Staging UNLOGGED | Sem reescrita, permite UPSERT atômico | Ligeiramente mais código |

### Riscos
- ⚠️ Dados no staging são perdidos se PostgreSQL crashar durante carga
- ✅ Tabela principal permanece íntegra (dados antigos preservados)
- ✅ Aceitável para ETL mensal (podemos reprocessar)

---

## 2. Deferred Index Creation

### O que é
Remover índices antes da carga e recriá-los depois. Índices durante INSERT causam overhead significativo.

### Impacto
- **3-5x mais rápido** para bulk inserts
- Criação de índice em batch é mais eficiente

### Implementação

```python
# database.py - Adicionar métodos

def get_table_indexes(self, table_name: str) -> list[dict]:
    """Retorna todos os índices de uma tabela."""
    sql = """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = %s
        AND indexname NOT LIKE '%_pkey'
    """
    return self.execute(sql, [table_name]).fetchall()

def drop_indexes(self, table_name: str) -> list[dict]:
    """Remove índices e retorna definições para recriação."""
    indexes = self.get_table_indexes(table_name)
    for idx in indexes:
        self.execute(f"DROP INDEX IF EXISTS {idx['indexname']}")
    return indexes

def create_indexes(self, indexes: list[dict]):
    """Recria índices a partir das definições salvas."""
    for idx in indexes:
        self.execute(idx['indexdef'])
```

### Uso no Pipeline

```python
async def load_table(table_name: str, data: pl.DataFrame):
    # 1. Salvar e remover índices
    indexes = db.drop_indexes(table_name)

    # 2. Desabilitar WAL
    await db.pre_load(table_name)

    try:
        # 3. Carregar dados
        await db.bulk_upsert(data, table_name)
    finally:
        # 4. Reabilitar WAL
        await db.post_load(table_name)

    # 5. Recriar índices
    db.create_indexes(indexes)
```

---

## 3. Leitura Eficiente de CSVs com Polars

### ⚠️ Problema Crítico no Código Atual

O código atual do cnpj-data-pipeline usa `skip_rows` + `n_rows` para paginação:

```python
# ❌ PROBLEMÁTICO: Complexidade O(n²)
df = pl.read_csv(..., skip_rows=offset, n_rows=batch_size)
```

Este padrão força o Polars a **ler e descartar** `offset` linhas para cada batch:
- Batch 1: lê 500k linhas
- Batch 2: lê 500k + 500k = 1M linhas (descarta 500k)
- Batch 10: lê 4.5M + 500k = 5M linhas (descarta 4.5M)

**Para 10M de linhas em batches de 500k = ~105M de linhas lidas no total!**

### Limitações do Polars com ZIP

Polars **não suporta arquivos ZIP nativamente** (apenas .gz, .zstd). Conforme [issue #19447](https://github.com/pola-rs/polars/issues/19447), `read_csv` não lê .zip diretamente.

Além disso, Polars descomprime arquivos comprimidos **completamente em memória** antes de processar, negando benefícios de lazy evaluation para arquivos comprimidos.

### Solução Recomendada: Extração + scan_csv com Streaming

A abordagem mais eficiente é extrair para arquivo temporário e usar `scan_csv` com streaming:

```python
import zipfile
import tempfile
from pathlib import Path
from typing import Generator
import polars as pl

def process_csv_from_zip(
    zip_path: str,
    columns: list[str],
    batch_size: int = 500_000
) -> Generator[pl.DataFrame, None, None]:
    """
    Extrai CSV para temp e processa com Polars streaming.
    Complexidade O(n) - cada linha é lida apenas uma vez.
    """
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.endswith('/') or not name.endswith('.csv'):
                continue

            # Extrair para arquivo temporário
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
                tmp_path = Path(tmp.name)

                # Streaming write em chunks (não carrega tudo em memória)
                with zf.open(name) as src:
                    while chunk := src.read(64 * 1024 * 1024):  # 64MB chunks
                        tmp.write(chunk)

            try:
                # Polars scan_csv com lazy evaluation
                lf = pl.scan_csv(
                    tmp_path,
                    separator=';',
                    has_header=False,
                    new_columns=columns,
                    encoding='iso-8859-1',
                    infer_schema_length=0,
                    null_values=[""],
                    ignore_errors=True,
                )

                # Coletar com streaming engine (processa em batches internamente)
                df = lf.collect(engine="streaming")

                # Yield em batches para o banco de dados
                for i in range(0, len(df), batch_size):
                    yield df.slice(i, batch_size)

            finally:
                # Sempre limpar arquivo temporário
                tmp_path.unlink(missing_ok=True)
```

### Alternativa: read_csv_batched (Polars 0.20+)

Para Polars 0.20+, existe `read_csv_batched` que é ainda mais eficiente:

```python
def process_csv_batched(
    csv_path: str,
    columns: list[str],
    batch_size: int = 500_000
) -> Generator[pl.DataFrame, None, None]:
    """
    Usa read_csv_batched para leitura verdadeiramente incremental.
    """
    reader = pl.read_csv_batched(
        csv_path,
        separator=';',
        has_header=False,
        new_columns=columns,
        encoding='iso-8859-1',
        infer_schema_length=0,
        batch_size=batch_size,
    )

    while True:
        batches = reader.next_batches(1)
        if not batches:
            break
        yield batches[0]
```

### Comparativo de Performance

| Abordagem | Complexidade | Memória | Tempo (10M linhas) |
|-----------|-------------|---------|-------------------|
| skip_rows + n_rows | O(n²) | Baixa | ~10 min |
| scan_csv + collect | O(n) | Média | ~2 min |
| read_csv_batched | O(n) | Baixa | ~2 min |

### Recomendação

1. **Manter extração para temp**: Overhead de ~5 min para 20GB é aceitável
2. **Usar scan_csv ou read_csv_batched**: Evita leitura O(n²)
3. **Remover conversão manual de encoding**: Polars lê ISO-8859-1 nativamente

---

## 4. Download com HTTP Range (Resume Capability)

### O que é
Baixar arquivos em chunks usando HTTP Range headers, permitindo retomar downloads interrompidos.

### Impacto
- Downloads podem ser retomados após falha
- Mais resiliente a falhas de rede

### Implementação Robusta

```python
import aiohttp
import asyncio
import random
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ChunkedDownloader:
    def __init__(
        self,
        chunk_size: int = 1_048_576,  # 1MB
        max_retries: int = 5,         # 5 tentativas é suficiente
        timeout: int = 300            # 5 min para arquivos grandes
    ):
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def download_file(
        self,
        url: str,
        output_path: Path,
        session: aiohttp.ClientSession
    ) -> bool:
        """
        Download com suporte a resume.
        Retorna True se completou, False se precisa retry.
        """
        # 1. Verificar metadados do arquivo remoto
        async with session.head(url) as resp:
            total_size = int(resp.headers.get('content-length', 0))
            accepts_range = resp.headers.get('accept-ranges') == 'bytes'

        # 2. Verificar arquivo local existente
        start_byte = 0
        if output_path.exists():
            start_byte = output_path.stat().st_size
            if start_byte >= total_size:
                logger.info(f"Arquivo já completo: {output_path.name}")
                return True

        # 3. Preparar headers para resume (se servidor suporta)
        headers = {}
        if start_byte > 0 and accepts_range:
            headers['Range'] = f'bytes={start_byte}-'
            logger.info(f"Resumindo de {start_byte}/{total_size} bytes")
        elif start_byte > 0 and not accepts_range:
            # Servidor não suporta Range, recomeçar do zero
            logger.warning(f"Servidor não suporta Range, reiniciando download")
            start_byte = 0

        # 4. Download
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            mode = 'ab' if start_byte > 0 else 'wb'
            with open(output_path, mode) as f:
                async for chunk in resp.content.iter_chunked(self.chunk_size):
                    f.write(chunk)

        # 5. Validar tamanho final
        final_size = output_path.stat().st_size
        if final_size != total_size:
            logger.error(f"Tamanho incorreto: {final_size} != {total_size}")
            return False

        return True

    async def download_with_retry(self, url: str, output_path: Path):
        """Download com retry exponencial + jitter."""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for attempt in range(self.max_retries):
                try:
                    if await self.download_file(url, output_path, session):
                        return
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    # Exponential backoff com jitter (evita thundering herd)
                    base_wait = min(2 ** attempt, 60)
                    jitter = random.uniform(0, base_wait * 0.1)
                    wait_time = base_wait + jitter

                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} em {wait_time:.1f}s: {e}"
                    )
                    await asyncio.sleep(wait_time)

            raise Exception(f"Falha após {self.max_retries} tentativas: {url}")
```

### Melhorias em Relação à Versão Original

| Aspecto | Original | Melhorado |
|---------|----------|-----------|
| max_retries | 32 (excessivo) | 5 (suficiente) |
| Jitter | Não tinha | Evita thundering herd |
| Accept-Ranges | Não verificava | Verifica suporte do servidor |
| Validação | Não validava | Verifica tamanho final |
| Logging | print() | logger estruturado |

---

## 5. Configuração do PostgreSQL para Bulk Load

### Nota sobre o Código Atual

O código atual do cnpj-data-pipeline usa **psycopg2 (síncrono)**, não asyncpg. Para ETL de carga mensal, conexão síncrona é adequada - o gargalo é I/O de disco, não latência de rede.

### Configurações PostgreSQL Recomendadas (Durante ETL)

```sql
-- Executar ANTES do ETL (aumenta performance de INSERT/COPY)
SET maintenance_work_mem = '2GB';          -- Mais memória para índices
SET max_parallel_workers_per_gather = 4;   -- Paralelismo
SET checkpoint_completion_target = 0.9;    -- Checkpoints mais suaves
SET wal_buffers = '64MB';                  -- Buffer de WAL maior

-- APENAS durante ETL (reverte após)
SET synchronous_commit = off;              -- Não espera flush do WAL
```

### Conexão psycopg2 Otimizada

```python
import psycopg2
from psycopg2 import pool

# Pool simples para ETL (não precisa de muitas conexões)
connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=4,  # ETL não precisa de muitas conexões paralelas
    dsn=os.environ['DATABASE_URL'],
    options='-c statement_timeout=3600000'  # 1h para COPY grandes
)

def get_connection():
    return connection_pool.getconn()

def release_connection(conn):
    connection_pool.putconn(conn)
```

### Se Migrar para asyncpg (Futuro)

```python
import asyncpg

async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=os.environ['DATABASE_URL'],
        min_size=1,
        max_size=4,               # ETL não precisa de muitas conexões
        command_timeout=3600,     # 1h para COPY de milhões de linhas
        statement_cache_size=50,
    )
```

---

## 6. Parallel Processing

### Producer-Consumer Pattern

```python
import asyncio
from asyncio import Queue

async def etl_pipeline(files: list[str], db_pool: asyncpg.Pool):
    queue = Queue(maxsize=10)  # Backpressure

    # Producer: lê arquivos
    async def producer():
        for file in files:
            async for batch in read_csv_from_zip_polars(file):
                await queue.put(batch)
        await queue.put(None)  # Sinaliza fim

    # Consumer: insere no banco
    async def consumer():
        while True:
            batch = await queue.get()
            if batch is None:
                break
            await bulk_insert(db_pool, batch)

    # Executar em paralelo
    await asyncio.gather(
        producer(),
        *[consumer() for _ in range(4)]  # 4 consumers
    )
```

---

## Checklist de Implementação

- [ ] Adicionar `pre_load()` e `post_load()` para UNLOGGED tables
- [ ] Implementar `drop_indexes()` e `create_indexes()`
- [ ] Criar `stream_csv_from_zip()` para leitura direta
- [ ] Adicionar `ChunkedDownloader` com HTTP Range
- [ ] Configurar connection pool otimizado
- [ ] Implementar producer-consumer para paralelismo

---

## Benchmark Esperado (Realista)

Baseado em literatura e benchmarks de projetos similares:

| Operação | Antes | Depois | Notas |
|----------|-------|--------|-------|
| Download 20GB | 60 min | 30-40 min | Depende da conexão e servidores da RF |
| Processamento CSV | 30 min | 5-10 min | scan_csv vs skip_rows |
| Carga PostgreSQL | 60 min | 20-30 min | Staging UNLOGGED + COPY |
| Criação índices | 30 min | 40-50 min | Depende de RAM disponível |
| **TOTAL** | **180 min** | **95-130 min** | - |

**Redução realista: 40-50% do tempo total**

### Referências de Benchmark

- [CyberTec PostgreSQL](https://www.cybertec-postgresql.com/en/bulk-load-performance-in-postgresql/): ~500k rows/s com COPY
- [EDB Best Practices](https://www.enterprisedb.com/blog/7-best-practice-tips-postgresql-bulk-data-loading): UNLOGGED = 2-3x mais rápido (não 10-50x)
- 60M registros teórico: 60-120 segundos de COPY puro
- 60M registros prático: 20-40 minutos (com transformações e network I/O)
