"""
Testes unitarios das funcoes puras de formato e dos graficos de painel.py.

Dado inventado, sem banco: as funcoes de formato nao tocam o DuckDB, e as de
grafico recebem um DataFrame montado a mao. O valor esperado sai da conta sobre
a entrada, nunca de um numero medido no dado da Olist.
"""
import pandas as pd

import painel


def test_reais_usa_ponto_de_milhar_e_virgula_decimal():
    # 1003862.14 tem milhar e centavos: vira R$ 1.003.862,14
    assert painel.reais(1003862.14) == "R$ 1.003.862,14"


def test_reais_valor_pequeno():
    assert painel.reais(137.42) == "R$ 137,42"


def test_pct_uma_casa():
    assert painel.pct(93.2) == "93,2%"


def test_numero_sem_casas_tem_separador_de_milhar():
    assert painel.numero(96470) == "96.470"


def test_numero_com_uma_casa():
    assert painel.numero(12.5, 1) == "12,5"


def test_formato_nao_depende_de_locale_milhar_e_decimal_juntos():
    # 1234.5 -> milhar com ponto, decimal com virgula, sem trocar um pelo outro
    assert painel.numero(1234.5, 1) == "1.234,5"


def test_fig_faturamento_tem_um_ponto_por_linha():
    df = pd.DataFrame({"mes": ["2017-01-01", "2017-02-01"], "receita": [10.0, 20.0]})
    fig = painel.fig_faturamento(df)
    # a figura de linha tem um y por linha do DataFrame
    assert len(fig.data[0].y) == 2


def test_fig_top_categorias_corta_em_dez():
    df = pd.DataFrame({
        "categoria": [f"cat_{i}" for i in range(15)],
        "receita": list(range(15, 0, -1)),
    })
    fig = painel.fig_top_categorias(df)
    assert len(fig.data[0].y) == 10


def test_fig_pareto_desenha_todas_as_linhas():
    df = pd.DataFrame({"posicao": [1, 2, 3], "pct_acumulado": [40.0, 70.0, 100.0]})
    fig = painel.fig_pareto_vendedores(df)
    assert len(fig.data[0].x) == 3
