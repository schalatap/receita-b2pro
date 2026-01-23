"""PostgreSQL database operations with Polars for fast bulk loading."""

import io
import logging
import time
from typing import List, Set, Optional
from urllib.parse import urlparse

import polars as pl
import psycopg2

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL database handler with UNLOGGED staging tables for fast upsert."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pk_cache: dict = {}
        self._index_cache: dict = {}
        self.conn = None

    def _parse_url(self) -> dict:
        """Parse DATABASE_URL into connection parameters."""
        parsed = urlparse(self.database_url)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "database": parsed.path[1:],
            "user": parsed.username,
            "password": parsed.password,
        }

    def connect(self):
        """Establish database connection with retry."""
        if self.conn is not None:
            return

        params = self._parse_url()
        for attempt in range(4):
            try:
                self.conn = psycopg2.connect(**params)
                self.conn.autocommit = False
                return
            except psycopg2.OperationalError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

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
        except Exception:
            return set()

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

    def set_bulk_load_config(self):
        """Set PostgreSQL configuration for bulk loading performance."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("SET maintenance_work_mem = '512MB'")
            cur.execute("SET synchronous_commit = off")
            # checkpoint_completion_target requires superuser, skip
            logger.info("PostgreSQL bulk load configuration applied")

    def reset_bulk_load_config(self):
        """Reset PostgreSQL configuration to defaults."""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute("RESET maintenance_work_mem")
            cur.execute("RESET synchronous_commit")
            logger.info("PostgreSQL configuration reset to defaults")

    def get_table_indexes(self, table_name: str) -> List[dict]:
        """Get all non-PK indexes for a table."""
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

    def drop_indexes(self, table_name: str) -> List[dict]:
        """Drop all non-PK indexes and return definitions for recreation."""
        indexes = self.get_table_indexes(table_name)
        if not indexes:
            return []

        self.connect()
        with self.conn.cursor() as cur:
            for idx in indexes:
                cur.execute(f"DROP INDEX IF EXISTS {idx['indexname']}")
            self.conn.commit()

        logger.info(f"Dropped {len(indexes)} indexes from {table_name}")
        return indexes

    def create_indexes(self, indexes: List[dict]):
        """Recreate indexes from saved definitions."""
        if not indexes:
            return

        self.connect()
        with self.conn.cursor() as cur:
            for idx in indexes:
                try:
                    cur.execute(idx["indexdef"])
                except psycopg2.Error as e:
                    logger.warning(f"Failed to create index {idx['indexname']}: {e}")
            self.conn.commit()

        logger.info(f"Created {len(indexes)} indexes")

    def drop_all_indexes_for_bulk_load(self) -> dict:
        """Drop all non-PK indexes from large tables for bulk loading.

        Returns dict of {table_name: [index_definitions]} for recreation.
        """
        large_tables = ["empresas", "estabelecimentos", "socios", "dados_simples"]
        saved_indexes = {}

        self.connect()
        for table in large_tables:
            indexes = self.get_table_indexes(table)
            if indexes:
                saved_indexes[table] = indexes
                with self.conn.cursor() as cur:
                    for idx in indexes:
                        cur.execute(f"DROP INDEX IF EXISTS {idx['indexname']}")
                    self.conn.commit()
                logger.info(f"Dropped {len(indexes)} indexes from {table}")

        # Clear cache since we dropped indexes
        self._index_cache.clear()
        return saved_indexes

    def create_all_indexes_after_bulk_load(self, saved_indexes: dict):
        """Recreate all indexes after bulk loading (with CONCURRENTLY option)."""
        self.connect()
        total = sum(len(idxs) for idxs in saved_indexes.values())
        logger.info(f"Creating {total} indexes...")

        for table, indexes in saved_indexes.items():
            logger.info(f"Creating {len(indexes)} indexes on {table}...")
            with self.conn.cursor() as cur:
                for idx in indexes:
                    try:
                        # Use regular CREATE INDEX (CONCURRENTLY requires autocommit)
                        cur.execute(idx["indexdef"])
                        self.conn.commit()
                        logger.info(f"  Created {idx['indexname']}")
                    except psycopg2.Error as e:
                        self.conn.rollback()
                        logger.warning(f"  Failed {idx['indexname']}: {e}")

        logger.info("All indexes created!")

    def bulk_insert(self, df: pl.DataFrame, table_name: str, columns: List[str]):
        """Ultra-fast bulk insert using COPY directly to table.

        Use this for initial load when table is empty. No conflict handling.
        Expected: 100k-200k rows/second.
        """
        if df.is_empty():
            return

        self.connect()
        try:
            with self.conn.cursor() as cur:
                columns_str = ", ".join([f'"{col}"' for col in columns])

                # Write CSV and remove null bytes (0x00) that corrupt PostgreSQL COPY
                csv_data = df.write_csv(include_header=False)
                csv_data = csv_data.replace('\x00', '')  # Remove null bytes
                buffer = io.StringIO(csv_data)

                cur.copy_expert(
                    f"COPY {table_name} ({columns_str}) FROM STDIN WITH CSV",
                    buffer,
                )
                self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error bulk_insert {table_name}: {e}")
            raise

    def bulk_upsert(self, df: pl.DataFrame, table_name: str, columns: List[str], use_unlogged: bool = True):
        """Bulk upsert using UNLOGGED staging table + COPY.

        Use this for incremental updates when table has existing data.
        Slower than bulk_insert due to conflict handling.
        """
        if df.is_empty():
            return

        self.connect()
        staging_table = f"staging_{table_name}_{id(df)}"

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"CREATE UNLOGGED TABLE {staging_table} "
                    f"(LIKE {table_name} INCLUDING DEFAULTS)"
                )

                # COPY to staging (usando StringIO - mais rápido que BytesIO + encode)
                columns_str = ", ".join([f'"{col}"' for col in columns])
                buffer = io.StringIO()
                df.write_csv(buffer, include_header=False)
                buffer.seek(0)
                cur.copy_expert(
                    f"COPY {staging_table} ({columns_str}) FROM STDIN WITH CSV",
                    buffer,
                )

                # Upsert from staging to main
                primary_keys = self._get_primary_keys(cur, table_name)
                self._upsert_from_temp(cur, staging_table, table_name, columns, primary_keys)

                self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error: {table_name}: {e}")
            raise
        finally:
            try:
                with self.conn.cursor() as cur:
                    cur.execute(f"DROP TABLE IF EXISTS {staging_table}")
                    self.conn.commit()
            except Exception:
                pass

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
