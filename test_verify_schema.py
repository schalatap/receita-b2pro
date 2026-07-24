"""Testes do pré-voo de schema (`Database.verify_schema`).

Contexto: em 2026-07-24 o v1.38 rodou contra uma base v1.28 em produção. O
`ensure_schema` não migra base já inicializada, então `socios` continuou com o
`id` serial antigo enquanto a carga escrevia `socio_id`. O erro só apareceu no
meio da ingestão — depois do TRUNCATE — e a tabela ficou vazia (27,8M linhas).

O pré-voo existe para transformar esse cenário em um abort limpo, antes de
qualquer TRUNCATE. Os testes usam o banco real (sem mock): criam um schema
temporário, apontam a checagem para ele e conferem os dois desfechos.
"""
import os
import unittest

import psycopg2

from database import Database
from processor import expected_table_columns


DSN = os.getenv("DATABASE_URL", "postgres://cnpj_user:cnpj_pass@localhost:5432/cnpj")


class VerifySchemaTests(unittest.TestCase):
    """Exercita a query real de information_schema contra tabelas de teste."""

    @classmethod
    def setUpClass(cls):
        cls.conn = psycopg2.connect(DSN)
        cls.conn.autocommit = True
        with cls.conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS _preflight_test")
            cur.execute("SET search_path TO _preflight_test, public")

    @classmethod
    def tearDownClass(cls):
        with cls.conn.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS _preflight_test CASCADE")
        cls.conn.close()

    def setUp(self):
        self.db = Database(DSN)

    def tearDown(self):
        self.db.disconnect()

    def test_base_real_e_compativel(self):
        """O banco de desenvolvimento tem que passar — se não passar, o pré-voo
        bloquearia carga legítima, que é pior que o problema que ele resolve."""
        self.assertEqual(self.db.verify_schema(expected_table_columns()), [])

    def test_detecta_coluna_ausente(self):
        """O caso real de 24/07: socios sem socio_id."""
        problemas = self.db.verify_schema({"socios": ["socio_id", "cnpj_basico"]})
        self.assertEqual(problemas, [])  # dev tem socio_id
        problemas = self.db.verify_schema({"socios": ["coluna_que_nao_existe"]})
        self.assertEqual(len(problemas), 1)
        self.assertIn("colunas ausentes", problemas[0])
        self.assertIn("coluna_que_nao_existe", problemas[0])

    def test_detecta_tabela_ausente(self):
        """O segundo erro de 24/07: a tabela deixou de existir."""
        problemas = self.db.verify_schema({"tabela_inexistente_xyz": ["a"]})
        self.assertEqual(problemas, ["tabela_inexistente_xyz: tabela ausente"])

    def test_coluna_extra_na_tabela_nao_e_problema(self):
        """Coluna a mais (legado, default) não impede o COPY — não pode abortar."""
        self.assertEqual(self.db.verify_schema({"socios": ["cnpj_basico"]}), [])

    def test_relata_todos_os_problemas_de_uma_vez(self):
        """Abortar mostrando um problema por vez faria o operador descobrir a
        divergência em rodadas sucessivas."""
        problemas = self.db.verify_schema({
            "tabela_inexistente_xyz": ["a"],
            "socios": ["outra_que_nao_existe"],
        })
        self.assertEqual(len(problemas), 2)


if __name__ == "__main__":
    unittest.main()
