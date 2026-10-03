"""Universo do índice de busca: uma definição só (enrich.no_universo_da_busca, cnpj-demo/scripts/enrich/gap_ddl.sql)."""

import inspect
from datetime import date
from types import SimpleNamespace

import pytest

import sync_elasticsearch
from sync_elasticsearch import QUERY_EMPRESAS, referencia_do_universo


def _conexao(referencia):
    cursor = SimpleNamespace(execute=lambda _sql: None, fetchone=lambda: (referencia,))
    return SimpleNamespace(cursor=lambda: _Contexto(cursor))


class _Contexto:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, *_):
        return False


def test_consultas_usam_a_definicao_comum_com_a_referencia_do_lote():
    fonte = inspect.getsource(sync_elasticsearch)
    assert "CURRENT_DATE" not in fonte
    assert fonte.count("enrich.no_universo_da_busca(") == 3
    chamada = "enrich.no_universo_da_busca(e.situacao_cadastral, e.data_situacao_cadastral, %(referencia)s)"
    assert chamada in QUERY_EMPRESAS


def test_referencia_vem_do_lote_carregado():
    assert referencia_do_universo(_conexao(date(2026, 9, 1))) == date(2026, 9, 1)


def test_sem_lote_carregado_o_sync_nao_comeca():
    with pytest.raises(RuntimeError, match="processed_files sem lote"):
        referencia_do_universo(_conexao(None))
