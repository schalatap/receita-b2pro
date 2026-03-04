#!/usr/bin/env python3
"""
Aplica descrições corretas do IBGE/CONCLA na tabela cnaes.

A RFB entrega CNAEs com descrições vazias ou corrompidas (encoding ISO-8859-1).
Este script atualiza as descrições usando cnae_ibge.csv + cnae_adicional.csv do IBGE.

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
CNAE_IBGE = SCRIPT_DIR / "tabelas_auxiliares" / "cnae_ibge.csv"
CNAE_ADICIONAL = SCRIPT_DIR / "tabelas_auxiliares" / "cnae_adicional.csv"


def load_cnaes() -> list[tuple[str, str]]:
    """Load CNAE descriptions from IBGE CSVs."""
    rows = []
    for path in [CNAE_IBGE, CNAE_ADICIONAL]:
        if not path.exists():
            logger.warning(f"File not found: {path}")
            continue
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter=";"):
                rows.append((r["codigo"], r["descricao"]))
    return rows


def apply(database_url: str) -> int:
    """Apply CNAE descriptions to database. Returns number of rows updated."""
    rows = load_cnaes()
    if not rows:
        logger.error("No CNAE data loaded")
        return 0

    # Write TSV (tab-delimited to avoid conflicts with ; in descriptions)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False, encoding="utf-8") as f:
        for codigo, descricao in rows:
            f.write(f"{codigo}\t{descricao}\n")
        tsv_path = f.name

    conn = None
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        cur.execute("CREATE TEMP TABLE tmp_cnae (codigo VARCHAR(10), descricao TEXT)")

        with open(tsv_path, "r", encoding="utf-8") as f:
            cur.copy_from(f, "tmp_cnae", columns=("codigo", "descricao"))

        cur.execute("""
            UPDATE cnaes SET descricao = t.descricao, data_atualizacao = now()
            FROM tmp_cnae t
            WHERE cnaes.codigo = t.codigo
              AND (cnaes.descricao IS NULL OR cnaes.descricao = '')
        """)
        updated = cur.rowcount

        cur.execute("""
            INSERT INTO cnaes (codigo, descricao)
            SELECT codigo, descricao FROM tmp_cnae t
            WHERE NOT EXISTS (SELECT 1 FROM cnaes WHERE codigo = t.codigo)
        """)
        inserted = cur.rowcount

        conn.commit()
        logger.info(f"CNAE descriptions: {updated} updated, {inserted} inserted (from {len(rows)} IBGE records)")
        return updated + inserted

    finally:
        if conn:
            conn.close()
        os.unlink(tsv_path)


def main():
    parser = argparse.ArgumentParser(description="Apply IBGE CNAE descriptions to database")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"), help="PostgreSQL connection URL")
    args = parser.parse_args()

    if not args.database_url:
        logger.error("DATABASE_URL not set. Use --database-url or set DATABASE_URL env var.")
        return

    apply(args.database_url)


if __name__ == "__main__":
    main()
