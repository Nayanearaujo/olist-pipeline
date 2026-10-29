"""
Teste unitario de relatorio.py.

Monta um dict de marts inventado (sem banco), gera o HTML e confere que o
arquivo nasce em tmp_path e que rodar duas vezes muda so o rodape (a data).
"""
import re

import pandas as pd

import relatorio


def _dados_inventados():
    return {
        "vendas_mensais": pd.DataFrame({
            "mes": ["2017-01-01", "2017-02-01"], "pedidos": [10, 20], "receita": [100.0, 200.0],
        }),
        "top_categorias": pd.DataFrame({
            "categoria": ["health_beauty"], "pedidos": [5], "itens": [5], "receita": [100.0],
        }),
        "entrega_no_prazo": pd.DataFrame({
            "entregues": [10], "no_prazo": [9], "atrasados": [1], "pct_no_prazo": [90.0],
        }),
        "nota_por_categoria": pd.DataFrame({
            "categoria": ["office_furniture"], "nota_media": [3.6], "pedidos_avaliados": [120], "posicao": [1],
        }),
        "recompra": pd.DataFrame({
            "pedidos_por_cliente": [1, 2], "clientes": [90, 10], "pct_clientes": [90.0, 10.0],
        }),
        "ticket_medio_por_estado": pd.DataFrame({"uf": ["SP"], "pedidos": [5], "ticket_medio": [137.42]}),
        "mix_pagamento": pd.DataFrame({
            "tipo": ["credit_card"], "pagamentos": [5], "pedidos": [5], "valor": [100.0], "pct_valor": [78.5],
        }),
        "clientes_por_uf": pd.DataFrame({"uf": ["SP"], "clientes": [40302]}),
        "vendedores_pareto": pd.DataFrame({
            "vendedor_id": ["s1"], "uf": ["SP"], "receita": [100.0], "posicao": [1], "pct_acumulado": [100.0],
        }),
    }


def test_gera_arquivo_e_cartoes(tmp_path, monkeypatch):
    saida = tmp_path / "relatorio.html"
    monkeypatch.setattr(relatorio, "SAIDA", saida)
    monkeypatch.setattr(relatorio.painel, "ler", lambda *a, **k: _dados_inventados())
    relatorio.main()
    assert saida.exists()
    html = saida.read_text(encoding="utf-8")
    # o ticket medio inventado (137,42) aparece congelado no HTML
    assert "R$ 137,42" in html


def test_rodar_duas_vezes_muda_so_o_rodape(tmp_path, monkeypatch):
    saida = tmp_path / "relatorio.html"
    monkeypatch.setattr(relatorio, "SAIDA", saida)
    monkeypatch.setattr(relatorio.painel, "ler", lambda *a, **k: _dados_inventados())

    relatorio.main()
    primeiro = saida.read_text(encoding="utf-8")
    relatorio.main()
    segundo = saida.read_text(encoding="utf-8")

    # tira o rodape (a linha "Dados de ...") dos dois e compara o resto
    sem_rodape = lambda h: re.sub(r"Dados de [^<]+", "", h)
    assert sem_rodape(primeiro) == sem_rodape(segundo)
