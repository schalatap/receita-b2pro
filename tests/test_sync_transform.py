"""Contrato PGFN do documento indexado (transform em sync_elasticsearch.py)."""

from decimal import Decimal
from types import SimpleNamespace

from sync_elasticsearch import transform


def _linha(**pgfn):
    base = dict(
        cnpj="01489385000165",
        cnpj_basico="01489385",
        razao_social="DIRETRIZ FEIRAS E EVENTOS LTDA",
        nome_fantasia=None,
        situacao_cadastral="02",
        data_situacao_cadastral=None,
        data_inicio_atividade=None,
        cnae_fiscal_principal="8230001",
        cnae_descricao=None,
        cnae_divisao="82",
        cnae_fiscal_secundaria=None,
        natureza_juridica="2062",
        natureza_descricao=None,
        porte="05",
        capital_social=None,
        tipo_logradouro=None,
        logradouro=None,
        numero=None,
        complemento=None,
        bairro=None,
        cep=None,
        municipio="7535",
        municipio_nome="CURITIBA",
        uf="PR",
        telefone_1=None,
        telefone_2=None,
        email=None,
        identificador_matriz_filial="1",
        opcao_pelo_simples=None,
        opcao_pelo_mei=None,
        data_opcao_pelo_simples=None,
        data_opcao_pelo_mei=None,
        municipio_populacao=None,
        municipio_regiao=None,
        municipio_mesorregiao=None,
        municipio_microrregiao=None,
        municipio_capital=None,
        municipio_lat=None,
        municipio_lon=None,
        cvm_capital_aberto=False,
        cvm_setor=None,
        cvm_receita=None,
        cvm_lucro=None,
        pgfn_divida_total=None,
        pgfn_qtd_inscricoes=None,
        pgfn_cobranca_total=None,
        pgfn_cobranca_qtd=None,
        pgfn_suspensa_total=None,
        pgfn_suspensa_qtd=None,
        pgfn_qtd_ajuizadas=None,
    )
    base.update(pgfn)
    return SimpleNamespace(**base)


def _pgfn(doc):
    fonte = doc["_source"]
    return {
        k: fonte[k]
        for k in (
            "tem_divida_ativa",
            "tem_divida_em_cobranca",
            "divida_total",
            "qtd_inscricoes_pgfn",
            "pgfn_cobranca_total",
            "pgfn_cobranca_qtd",
            "pgfn_suspensa_total",
            "pgfn_suspensa_qtd",
            "qtd_ajuizadas_pgfn",
            "pgfn_referencia",
        )
    }


def test_divida_so_suspensa_nao_conta_como_em_cobranca():
    linha = _linha(
        pgfn_divida_total=Decimal("5564001.11"),
        pgfn_qtd_inscricoes=74,
        pgfn_cobranca_total=Decimal("0"),
        pgfn_cobranca_qtd=0,
        pgfn_suspensa_total=Decimal("5564001.11"),
        pgfn_suspensa_qtd=74,
        pgfn_qtd_ajuizadas=11,
    )
    assert _pgfn(transform(linha, [], "idx", "2026-06")) == {
        "tem_divida_ativa": True,
        "tem_divida_em_cobranca": False,
        "divida_total": 5564001.11,
        "qtd_inscricoes_pgfn": 74,
        "pgfn_cobranca_total": 0.0,
        "pgfn_cobranca_qtd": 0,
        "pgfn_suspensa_total": 5564001.11,
        "pgfn_suspensa_qtd": 74,
        "qtd_ajuizadas_pgfn": 11,
        "pgfn_referencia": "2026-06",
    }


def test_divida_em_cobranca_marca_a_empresa():
    linha = _linha(
        pgfn_divida_total=Decimal("1000"),
        pgfn_qtd_inscricoes=2,
        pgfn_cobranca_total=Decimal("400"),
        pgfn_cobranca_qtd=1,
        pgfn_suspensa_total=Decimal("600"),
        pgfn_suspensa_qtd=1,
        pgfn_qtd_ajuizadas=0,
    )
    doc = _pgfn(transform(linha, [], "idx", "2026-06"))
    assert doc["tem_divida_em_cobranca"] is True
    assert doc["pgfn_cobranca_total"] == 400.0


def test_sem_inscricao_tem_zeros_e_a_referencia_da_base():
    assert _pgfn(transform(_linha(), [], "idx", "2026-06")) == {
        "tem_divida_ativa": False,
        "tem_divida_em_cobranca": False,
        "divida_total": 0.0,
        "qtd_inscricoes_pgfn": 0,
        "pgfn_cobranca_total": 0.0,
        "pgfn_cobranca_qtd": 0,
        "pgfn_suspensa_total": 0.0,
        "pgfn_suspensa_qtd": 0,
        "qtd_ajuizadas_pgfn": 0,
        "pgfn_referencia": "2026-06",
    }
