"""PostgreSQL database operations with Polars for fast bulk loading."""

import io
import logging
import os
import time
from pathlib import Path
from typing import List, Set

import polars as pl
import psycopg2

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL database handler with temp table upsert."""

    def __init__(
        self,
        database_url: str,
        pre_truncated: set | None = None,
        retry_attempts: int = 3,
        retry_delay: int = 5,
        fast_load: bool = False,
    ):
        self.database_url = database_url
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        # fast_load=True (apenas recarga completa "replace") relaxa a durabilidade
        # (synchronous_commit=off) — seguro porque um crash é recuperado re-truncando.
        # Em "upsert" fica off=False para não arriscar perda silenciosa no resume.
        self.fast_load = fast_load
        self._pk_cache: dict = {}
        self._index_cache: dict = {}
        self._truncated_tables: set = set(pre_truncated) if pre_truncated else set()
        self.conn = None

    def connect(self):
        """Establish database connection with retry.

        Passes DATABASE_URL through to libpq verbatim so query-string
        parameters (sslmode, options, application_name, connect_timeout,
        multi-host URIs, etc.) reach the driver.
        """
        if self.conn is not None:
            return

        for attempt in range(self.retry_attempts):
            try:
                self.conn = psycopg2.connect(self.database_url)
                self.conn.autocommit = False
                # Tuning de carga — aplicado em TODA conexão (inclui workers paralelos).
                # maintenance_work_mem acelera criação de índice e é inofensivo sempre.
                # synchronous_commit=off só na recarga completa (fast_load), p/ não
                # arriscar perda silenciosa de durabilidade no modo upsert/incremental.
                with self.conn.cursor() as cur:
                    cur.execute("SET maintenance_work_mem = '1GB'")
                    if self.fast_load:
                        cur.execute("SET synchronous_commit = off")
                self.conn.commit()
                return
            except psycopg2.OperationalError:
                if attempt == self.retry_attempts - 1:
                    raise
                time.sleep(2**attempt)

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    # ------------------------------------------------------------------
    # Otimizações de carga em massa (portadas do fork receita-b2pro).
    # O tuning de sessão (synchronous_commit/maintenance_work_mem) já é
    # aplicado em connect(); estes métodos são chamados no main para
    # clareza/explícito e para o drop/recreate de índices das tabelas grandes.
    # ------------------------------------------------------------------
    def set_bulk_load_config(self):
        """Reaplica tuning de sessão para carga (idempotente; connect() já aplica)."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("SET maintenance_work_mem = '1GB'")
            cur.execute("SET synchronous_commit = off")
        self.conn.commit()
        logger.info("PostgreSQL bulk load configuration applied")

    def reset_bulk_load_config(self):
        """Restaura configuração de sessão ao padrão."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("RESET maintenance_work_mem")
            cur.execute("RESET synchronous_commit")
        self.conn.commit()
        logger.info("PostgreSQL configuration reset to defaults")

    def get_table_indexes(self, table_name: str) -> List[dict]:
        """Lista índices não-PK de uma tabela (com cache)."""
        if table_name in self._index_cache:
            return self._index_cache[table_name]
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = %s
                AND indexname NOT LIKE '%%_pkey'
                """,
                (table_name,),
            )
            indexes = [{"indexname": row[0], "indexdef": row[1]} for row in cur.fetchall()]
        self._index_cache[table_name] = indexes
        return indexes

    _PENDING_TBL = "_index_recreate_pending"

    def _persist_pending_indexes(self, saved_indexes: dict):
        """Grava as defs de índice numa tabela de metadados ANTES de dropar.

        Sobrevive a crash do processo E a recreate de container Docker → as defs
        nunca ficam só em memória, garantindo recuperação no próximo run.
        """
        with self.conn.cursor() as cur:
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {self._PENDING_TBL} "
                "(indexname text PRIMARY KEY, indexdef text NOT NULL)"
            )
            # Upsert (sem TRUNCATE): pendências de um run anterior que falharam na
            # recuperação sobrevivem e são retentadas ao final desta carga.
            for indexes in saved_indexes.values():
                for idx in indexes:
                    cur.execute(
                        f"INSERT INTO {self._PENDING_TBL} (indexname, indexdef) VALUES (%s, %s) "
                        "ON CONFLICT (indexname) DO UPDATE SET indexdef = EXCLUDED.indexdef",
                        (idx["indexname"], idx["indexdef"]),
                    )
        self.conn.commit()

    def _clear_pending_indexes(self):
        with self.conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {self._PENDING_TBL}")
        self.conn.commit()

    @staticmethod
    def _already_exists(exc: psycopg2.Error) -> bool:
        """42P07 = índice/tabela já existe; 42710 = constraint já existe."""
        return exc.pgcode in ("42P07", "42710")

    def recover_pending_indexes(self) -> int:
        """Recupera índices de um run anterior interrompido entre drop e recreate.

        Idempotente e seguro de chamar sempre no início. Retorna nº recriado.
        """
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("SELECT to_regclass(%s)", (self._PENDING_TBL,))
            if cur.fetchone()[0] is None:
                return 0
            cur.execute(f"SELECT indexname, indexdef FROM {self._PENDING_TBL}")
            pending = cur.fetchall()
        if not pending:
            self._clear_pending_indexes()
            return 0
        logger.warning(f"Recuperando {len(pending)} índices de um run interrompido...")
        recovered = 0
        for indexname, indexdef in pending:
            with self.conn.cursor() as cur:
                try:
                    cur.execute(indexdef)
                    cur.execute(f"DELETE FROM {self._PENDING_TBL} WHERE indexname = %s", (indexname,))
                    self.conn.commit()
                    recovered += 1
                    logger.info(f"  Recriado {indexname}")
                except psycopg2.Error as e:
                    self.conn.rollback()
                    if self._already_exists(e):
                        with self.conn.cursor() as cur2:
                            cur2.execute(f"DELETE FROM {self._PENDING_TBL} WHERE indexname = %s", (indexname,))
                        self.conn.commit()
                        recovered += 1
                        logger.info(f"  {indexname} já existia — pendência descartada")
                    else:
                        # Mantém a pendência (ex.: PK que falha por duplicatas pré-dedupe);
                        # create_all_indexes_after_bulk_load retentará após a próxima carga.
                        logger.warning(f"  Falhou {indexname} (mantido como pendência): {e}")
        if recovered == len(pending):
            self._clear_pending_indexes()
        return recovered

    def _get_pk_constraint(self, table_name: str) -> dict | None:
        """Retorna a constraint de PK como statement executável + colunas, ou None."""
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE contype = 'p' AND conrelid = %s::regclass
                """,
                (table_name,),
            )
            row = cur.fetchone()
        if not row:
            return None
        conname, condef = row  # condef: "PRIMARY KEY (col1, col2)"
        columns = [c.strip() for c in condef[condef.index("(") + 1 : condef.rindex(")")].split(",")]
        return {
            "indexname": conname,
            "indexdef": f"ALTER TABLE {table_name} ADD CONSTRAINT {conname} {condef}",
            "pk_table": table_name,
            "pk_columns": columns,
        }

    def drop_all_indexes_for_bulk_load(self) -> dict:
        """Dropa índices não-PK E a constraint de PK das tabelas grandes.

        Sem a PK, todos os batches entram por COPY direto (bulk_insert) — sem
        temp table, sort ou ON CONFLICT. As raras duplicatas cross-shard da RFB
        são removidas no dedupe de create_all_indexes_after_bulk_load, antes de
        recriar a PK. Persiste as defs em tabela de metadados ANTES de dropar
        (crash-safe). Retorna {table_name: [definições]} (PK primeiro).
        """
        large_tables = ["empresas", "estabelecimentos", "socios", "dados_simples"]
        saved_indexes = {}
        self.connect()
        for table in large_tables:
            entries = []
            pk = self._get_pk_constraint(table)
            if pk:
                entries.append(pk)
            entries.extend(self.get_table_indexes(table))
            if entries:
                saved_indexes[table] = entries
        if not saved_indexes:
            return {}
        # 1) Persistir defs ANTES de dropar (recuperável mesmo se o processo morrer).
        self._persist_pending_indexes(saved_indexes)
        # 2) Dropar (PK via DROP CONSTRAINT; demais via DROP INDEX).
        for table, entries in saved_indexes.items():
            with self.conn.cursor() as cur:
                for idx in entries:
                    if "pk_columns" in idx:
                        cur.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {idx['indexname']}")
                    else:
                        cur.execute(f"DROP INDEX IF EXISTS {idx['indexname']}")
            self.conn.commit()
            logger.info(f"Dropped {len(entries)} indexes/PK from {table}")
        self._index_cache.clear()
        self._pk_cache.clear()  # bulk_insert passa a ver a tabela sem PK → COPY direto
        return saved_indexes

    def _dedupe_table(self, table_name: str, pk_columns: List[str]):
        """Remove duplicatas cross-shard da RFB antes de recriar a PK.

        Mantém uma ocorrência arbitrária (as duplicatas são linhas idênticas ou
        lixo da fonte). Um passo de sort sobre a tabela — mesma ordem de custo da
        criação da PK que vem em seguida.
        """
        pk_str = ", ".join(f'"{c}"' for c in pk_columns)
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                DELETE FROM {table_name} WHERE ctid IN (
                    SELECT ctid FROM (
                        SELECT ctid, row_number() OVER (PARTITION BY {pk_str} ORDER BY ctid) AS rn
                        FROM {table_name}
                    ) d WHERE d.rn > 1
                )
                """
            )
            removed = cur.rowcount
        self.conn.commit()
        if removed:
            logger.warning(f"  {table_name}: {removed} duplicata(s) de PK removida(s) antes da recriação")

    def create_all_indexes_after_bulk_load(self, saved_indexes: dict):
        """Dedupe + recriação de PK e índices após a carga."""
        if not saved_indexes:
            return
        self.connect()
        with self.conn.cursor() as cur:
            # Paraleliza o sort/build de cada índice (o servidor limita ao pool
            # de max_parallel_workers; inofensivo onde não houver folga).
            cur.execute("SET max_parallel_maintenance_workers = 4")
        self.conn.commit()
        total = sum(len(idxs) for idxs in saved_indexes.values())
        logger.info(f"Creating {total} indexes...")
        created = set()
        for table, entries in saved_indexes.items():
            logger.info(f"Creating {len(entries)} indexes on {table}...")
            for idx in entries:
                with self.conn.cursor() as cur:
                    try:
                        if "pk_columns" in idx:
                            self._dedupe_table(table, idx["pk_columns"])
                        cur.execute(idx["indexdef"])
                        cur.execute(
                            f"DELETE FROM {self._PENDING_TBL} WHERE indexname = %s",
                            (idx["indexname"],),
                        )
                        self.conn.commit()
                        created.add(idx["indexname"])
                        logger.info(f"  Created {idx['indexname']}")
                    except psycopg2.Error as e:
                        self.conn.rollback()
                        logger.warning(f"  Failed {idx['indexname']}: {e}")
        # Retenta pendências herdadas de runs anteriores (ex.: PK que o recover não
        # conseguiu recriar por duplicatas — os dados agora estão limpos).
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT indexname, indexdef FROM {self._PENDING_TBL}")
            leftovers = [r for r in cur.fetchall() if r[0] not in created]
        for indexname, indexdef in leftovers:
            with self.conn.cursor() as cur:
                try:
                    cur.execute(indexdef)
                    cur.execute(f"DELETE FROM {self._PENDING_TBL} WHERE indexname = %s", (indexname,))
                    self.conn.commit()
                    logger.info(f"  Recuperado (pendência antiga): {indexname}")
                except psycopg2.Error as e:
                    self.conn.rollback()
                    if self._already_exists(e):
                        with self.conn.cursor() as cur:
                            cur.execute(f"DELETE FROM {self._PENDING_TBL} WHERE indexname = %s", (indexname,))
                        self.conn.commit()
                        logger.info(f"  Pendência antiga {indexname} já existia — descartada")
                    else:
                        logger.warning(f"  Pendência antiga ainda falhando {indexname}: {e}")
        logger.info("All indexes created!")
        # Só descarta a tabela de pendências se nada ficou para trás.
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {self._PENDING_TBL}")
            remaining = cur.fetchone()[0]
        if remaining == 0:
            self._clear_pending_indexes()
        else:
            logger.warning(f"{remaining} índice(s)/PK ainda pendente(s) — mantidos para o próximo run")

    def ensure_schema(self):
        """Apply initial.sql if the schema tables don't exist yet.

        Lets the published Docker image target a fresh managed Postgres
        (Railway, RDS, etc.) without a separate init step.
        """
        self.connect()
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT to_regclass('processed_files')")
                if cur.fetchone()[0] is not None:
                    return

                sql_path = Path(__file__).parent / "initial.sql"
                cur.execute(sql_path.read_text())
                self.conn.commit()
                logger.info("Applied schema from initial.sql")
        except Exception:
            self.conn.rollback()
            raise

    def get_processed_files(self, directory: str) -> Set[str]:
        """Get all processed filenames for a directory."""
        self.connect()
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT filename FROM processed_files WHERE directory = %s",
                    (directory,),
                )
                return {row[0] for row in cur.fetchall()}
        except Exception as e:
            logger.error(f"Failed to get processed files: {e}")
            raise

    def mark_processed(self, directory: str, filename: str):
        """Mark a file as processed."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO processed_files (directory, filename)
                   VALUES (%s, %s)
                   ON CONFLICT (directory, filename) DO NOTHING""",
                (directory, filename),
            )
            self.conn.commit()

    def clear_processed_files(self, directory: str):
        """Clear all processed file records for a directory (for force re-processing)."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM processed_files WHERE directory = %s",
                (directory,),
            )
            self.conn.commit()

    def truncate_table(self, table_name: str):
        """Truncate a table. Used before parallel processing with replace strategy."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
            self.conn.commit()
        self._truncated_tables.add(table_name)

    def bulk_upsert(self, df: pl.DataFrame, table_name: str, columns: List[str]):
        """Bulk upsert using temp table + COPY."""
        if df.is_empty():
            return

        self.connect()
        temp_table = f"temp_{table_name}_{id(df)}"

        try:
            with self.conn.cursor() as cur:
                # 1. Create temp table
                cur.execute(
                    f"CREATE TEMP TABLE {temp_table} "
                    f"(LIKE {table_name} INCLUDING DEFAULTS INCLUDING STORAGE) ON COMMIT DROP"
                )

                # 2. COPY to temp
                self._copy_to_temp(cur, df, temp_table, columns)

                # 3. Upsert from temp to main
                primary_keys = self._get_primary_keys(cur, table_name)
                self._upsert_from_temp(cur, temp_table, table_name, columns, primary_keys)

                self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error: {table_name}: {e}")
            raise

    def bulk_insert(self, df: pl.DataFrame, table_name: str, columns: List[str]):
        """Bulk insert under LOADING_STRATEGY=replace.

        First batch per table: TRUNCATE then COPY directly into the target
        (fast path; target is guaranteed empty).

        Subsequent batches: COPY into a temp table and merge via the
        existing upsert helper. RFB occasionally ships the same
        (cnpj_basico, cnpj_ordem, cnpj_dv) across two sharded ZIPs of the
        same source table (e.g. Estabelecimentos0.zip and Estabelecimentos5.zip);
        without the temp-table path the second batch's direct COPY crashes
        on the PK constraint.
        """
        if df.is_empty():
            return

        self.connect()

        try:
            with self.conn.cursor() as cur:
                first_batch = table_name not in self._truncated_tables
                if first_batch:
                    cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
                    self._truncated_tables.add(table_name)
                    logger.info(f"Truncated {table_name}")
                    # Target is empty - direct COPY is safe and fastest.
                    self._copy_to_temp(cur, df, table_name, columns)
                else:
                    primary_keys = self._get_primary_keys(cur, table_name)
                    if not primary_keys:
                        # PK dropada para a carga (drop_all_indexes_for_bulk_load):
                        # COPY direto — duplicatas cross-shard são removidas no
                        # dedupe antes da recriação da PK.
                        self._copy_to_temp(cur, df, table_name, columns)
                    else:
                        # Cross-batch PK overlap path. Same temp-then-upsert
                        # pattern as bulk_upsert.
                        temp_table = f"{table_name}_tmp_{os.getpid()}"
                        cur.execute(
                            f"CREATE TEMP TABLE IF NOT EXISTS {temp_table} "
                            f"(LIKE {table_name} INCLUDING DEFAULTS INCLUDING STORAGE) ON COMMIT DROP"
                        )
                        cur.execute(f"TRUNCATE {temp_table}")
                        self._copy_to_temp(cur, df, temp_table, columns)
                        self._upsert_from_temp(cur, temp_table, table_name, columns, primary_keys)

                self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error: {table_name}: {e}")
            raise

    def _copy_to_temp(self, cur, df: pl.DataFrame, temp_table: str, columns: List[str]):
        """COPY DataFrame to temp table using Polars CSV."""
        columns_str = ", ".join([f'"{col}"' for col in columns])
        csv_bytes = df.write_csv(include_header=False).encode("utf-8", errors="replace")
        csv_bytes = csv_bytes.replace(b"\x00", b"")

        cur.copy_expert(
            f"COPY {temp_table} ({columns_str}) FROM STDIN WITH CSV ENCODING 'UTF8'",
            io.BytesIO(csv_bytes),
        )

    def _get_primary_keys(self, cur, table_name: str) -> List[str]:
        """Get primary key columns for a table with caching."""
        if table_name in self._pk_cache:
            return self._pk_cache[table_name]

        cur.execute(
            """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary
            ORDER BY array_position(i.indkey, a.attnum)
            """,
            (table_name,),
        )

        primary_keys = [row[0] for row in cur.fetchall()]
        self._pk_cache[table_name] = primary_keys
        return primary_keys

    def _upsert_from_temp(self, cur, temp_table: str, target_table: str, columns: List[str], primary_keys: List[str]):
        """Upsert from temp to target table."""
        columns_str = ", ".join([f'"{col}"' for col in columns])
        pk_str = ", ".join([f'"{pk}"' for pk in primary_keys])

        update_cols = [c for c in columns if c not in primary_keys]
        update_clause = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in update_cols])
        if update_clause:
            update_clause += ", data_atualizacao = CURRENT_TIMESTAMP"

        sql = f"""
            INSERT INTO {target_table} ({columns_str})
            SELECT DISTINCT ON ({pk_str}) {columns_str} FROM {temp_table} ORDER BY {pk_str}
            ON CONFLICT ({pk_str}) {"DO UPDATE SET " + update_clause if update_clause else "DO NOTHING"}
        """
        cur.execute(sql)
