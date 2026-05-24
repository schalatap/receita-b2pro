#!/usr/bin/env python3
"""
Aplica descrições corretas do IBGE/CONCLA nas tabelas auxiliares da RFB.

A RFB entrega as tabelas `cnaes`, `naturezas_juridicas` e `qualificacoes_socios`
com descrições vazias ou corrompidas (encoding ISO-8859-1). Este script atualiza
as descrições usando CSVs de referência do IBGE/SERPRO + CSVs suplementares
para códigos antigos/especiais.

Deve ser executado APÓS cada ingestão RFB (main.py --initial-load).

Uso:
    python fix_cnae_descriptions.py
    python fix_cnae_descriptions.py --database-url postgres://user:pass@host:5432/db
"""

import argparse
import csv
import logging
import os
import tempfile
from pathlib import Path

import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
AUX = SCRIPT_DIR / "tabelas_auxiliares"

# (table, csv_files, delimiter) — ordem importa: primeiro CSV com header padrão "codigo;descricao"
FIXES = [
    ("cnaes", [AUX / "cnae_ibge.csv", AUX / "cnae_adicional.csv"], ";"),
    ("naturezas_juridicas", [AUX / "natureza_juridica_2021.csv", AUX / "natureza_juridica_extras.csv"], ";"),
    ("qualificacoes_socios", [AUX / "qualificacao_socio_serpro_oficial.csv", AUX / "qualificacoes_extras.csv"], ";"),
]


def load_csv_rows(paths: list[Path], delimiter: str) -> list[tuple[str, str]]:
    """Load (codigo, descricao) pairs from CSVs. Aceita headers 'codigo;descricao' ou 'Código;Descrição'."""
    rows = []
    for path in paths:
        if not path.exists():
            logger.warning(f"File not found: {path}")
            continue
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter=delimiter):
                keys = list(r.keys())
                codigo = (r[keys[0]] or "").strip()
                descricao = (r[keys[1]] or "").strip()
                if codigo and descricao:
                    rows.append((codigo, descricao))
    return rows


def apply_table(conn, table: str, rows: list[tuple[str, str]]) -> tuple[int, int]:
    """Apply descriptions to a single table. Returns (updated, inserted)."""
    if not rows:
        logger.warning(f"  {table}: sem dados pra aplicar")
        return (0, 0)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False, encoding="utf-8") as f:
        for codigo, descricao in rows:
            # Normalizar quebras de linha e tabs no texto
            descricao = descricao.replace("\n", " ").replace("\t", " ")
            f.write(f"{codigo}\t{descricao}\n")
        tsv_path = f.name

    try:
        with conn.cursor() as cur:
            tmp_name = f"tmp_{table}"
            cur.execute(f"CREATE TEMP TABLE {tmp_name} (codigo VARCHAR(20), descricao TEXT) ON COMMIT DROP")

            with open(tsv_path, "r", encoding="utf-8") as f:
                cur.copy_from(f, tmp_name, columns=("codigo", "descricao"))

            # Tabela cnaes tem coluna data_atualizacao; as outras não.
            data_set = ", data_atualizacao = now()" if table == "cnaes" else ""

            cur.execute(f"""
                UPDATE {table} SET descricao = t.descricao{data_set}
                FROM {tmp_name} t
                WHERE {table}.codigo = t.codigo
                  AND ({table}.descricao IS NULL OR {table}.descricao = '' OR {table}.descricao != t.descricao)
            """)
            updated = cur.rowcount

            cur.execute(f"""
                INSERT INTO {table} (codigo, descricao)
                SELECT codigo, descricao FROM {tmp_name} t
                WHERE NOT EXISTS (SELECT 1 FROM {table} WHERE codigo = t.codigo)
            """)
            inserted = cur.rowcount

            conn.commit()
            return (updated, inserted)
    finally:
        os.unlink(tsv_path)


def apply(database_url: str) -> dict:
    """Apply descriptions to all auxiliary tables. Returns stats dict."""
    conn = None
    stats = {}
    try:
        conn = psycopg2.connect(database_url)
        for table, csv_paths, delim in FIXES:
            rows = load_csv_rows(csv_paths, delim)
            updated, inserted = apply_table(conn, table, rows)
            logger.info(f"{table}: {updated} updated, {inserted} inserted (from {len(rows)} reference records)")
            stats[table] = {"updated": updated, "inserted": inserted, "reference_count": len(rows)}
        return stats
    finally:
        if conn:
            conn.close()


def main():
    parser = argparse.ArgumentParser(description="Apply IBGE/SERPRO descriptions to RFB auxiliary tables")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"), help="PostgreSQL connection URL")
    args = parser.parse_args()

    if not args.database_url:
        logger.error("DATABASE_URL not set. Use --database-url or set DATABASE_URL env var.")
        return

    apply(args.database_url)


if __name__ == "__main__":
    main()
