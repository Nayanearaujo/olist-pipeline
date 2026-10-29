"""
Painel da Olist: leitura dos marts, formatacao e graficos.

Spec (fonte da verdade; o codigo e consequencia dela):

1. LEITURA
   ler(marts) devolve um dict nome -> DataFrame, rodando apenas
   SELECT * FROM marts.<nome>. Nenhuma outra SQL. A conexao e aberta com
   read_only=True e fechada dentro de ler(). Motivo: conexao aberta segura o
   arquivo, e o pipeline.marts nao grava com o painel de pe.

2. NENHUM CALCULO
   Este modulo nao faz groupby, sum, mean, count, merge nem pivot, e nenhuma
   conta entre colunas. So ordena, filtra linha, head(n), renomeia e formata.
   Motivo: numero novo na tela exige um .sql novo em marts. Se faltar numero,
   falta mart.

4. FORMATO
   reais, pct e numero sao funcoes puras (sem streamlit e sem banco): milhar com
   ponto, decimal com virgula, SEMPRE, sem usar o locale do sistema. Motivo: o
   resultado nao pode depender da maquina de quem roda.
   Ha uma funcao por grafico, recebendo o DataFrame e devolvendo a figura
   plotly. Motivo: o relatorio HTML reaproveita as mesmas funcoes.

O que eu assumi e nao estava na spec:
- Paleta de uma cor so (COR) e uma cor de destaque (DESTAQUE), porque a regra de
  layout da aula pede "uma cor, e o destaque com motivo".
- MESES_PADRAO (jan/2017 a ago/2018) exposto aqui para app.py e relatorio.py
  usarem o mesmo periodo padrao sem repetir a constante.
"""
from __future__ import annotations

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

BANCO = "olist.duckdb"

# As doze tabelas que o painel le. Faltando qualquer uma, a tela avisa.
MARTS = [
    "vendas_mensais",
    "top_categorias",
    "entrega_no_prazo",
    "nota_por_categoria",
    "recompra",
    "ticket_medio_por_estado",
    "mix_pagamento",
    "nota_por_prazo",
    "vendedores_pareto",
    "tempo_entrega_por_estado",
    "kpis",
    "clientes_por_uf",
]

# Periodo padrao do grafico de faturamento (primeiro dia de cada mes).
MES_INICIO_PADRAO = "2017-01-01"
MES_FIM_PADRAO = "2018-08-01"

# Uma cor so para tudo; o destaque aparece so onde o titulo comenta.
COR = "#1a6b52"
DESTAQUE = "#a86e05"


# ---------------------------------------------------------------------------
# 1. LEITURA
# ---------------------------------------------------------------------------
def ler(marts: list[str] | None = None, banco: str = BANCO) -> dict[str, pd.DataFrame]:
    """Le cada mart como DataFrame. So SELECT *; conexao read-only aberta e
    fechada aqui dentro."""
    nomes = marts if marts is not None else MARTS
    con = duckdb.connect(banco, read_only=True)
    try:
        return {nome: con.execute(f"SELECT * FROM marts.{nome}").df() for nome in nomes}
    finally:
        con.close()


# ---------------------------------------------------------------------------
# 4. FORMATO (funcoes puras, sem streamlit e sem banco)
# ---------------------------------------------------------------------------
def _br(texto: str) -> str:
    """Troca os separadores para o padrao brasileiro sem depender do locale.
    Usa um marcador temporario para nao confundir ponto e virgula."""
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def reais(valor: float, casas: int = 2) -> str:
    """1003862.14 -> 'R$ 1.003.862,14'"""
    return "R$ " + _br(f"{valor:,.{casas}f}")


def pct(valor: float, casas: int = 1) -> str:
    """93.2 -> '93,2%'"""
    return _br(f"{valor:,.{casas}f}") + "%"


def numero(valor: float, casas: int = 0) -> str:
    """96470 -> '96.470'"""
    return _br(f"{valor:,.{casas}f}")


# ---------------------------------------------------------------------------
# Graficos: uma funcao por grafico, recebe DataFrame e devolve figura plotly.
# Nenhuma delas agrega: o dado ja vem pronto do mart. So ordena/corta/renomeia.
# ---------------------------------------------------------------------------
def _barh(df: pd.DataFrame, x: str, y: str, titulo: str, cor: str = COR) -> go.Figure:
    """Barras horizontais, maior em cima. O dado ja vem ordenado do mart."""
    fig = px.bar(df, x=x, y=y, orientation="h", title=titulo)
    fig.update_traces(marker_color=cor)
    fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=8, r=8, t=48, b=8))
    return fig


def fig_faturamento(vendas_mensais: pd.DataFrame) -> go.Figure:
    """01 - Faturamento mensal (linha com marcadores). Destaque em nov/2017."""
    df = vendas_mensais.sort_values("mes")
    fig = px.line(df, x="mes", y="receita", markers=True, title="01 · Faturamento mensal")
    fig.update_traces(line_color=COR, marker_color=COR)
    fig.update_layout(
        xaxis_title="mês da compra", yaxis_title="receita (R$)",
        margin=dict(l=8, r=8, t=48, b=8),
    )
    return fig


def fig_top_categorias(top_categorias: pd.DataFrame) -> go.Figure:
    """02 - Receita por categoria, top 10, maior em cima."""
    df = top_categorias.sort_values("receita", ascending=False).head(10)
    return _barh(df, x="receita", y="categoria", titulo="02 · Receita por categoria (top 10)")


def fig_mix_pagamento(mix_pagamento: pd.DataFrame) -> go.Figure:
    """07 - Mix de pagamento por participacao no valor."""
    df = mix_pagamento.sort_values("pct_valor", ascending=False)
    return _barh(df, x="pct_valor", y="tipo", titulo="07 · Mix de pagamento (% do valor)")


def fig_ticket_uf(ticket_medio_por_estado: pd.DataFrame) -> go.Figure:
    """06 - Ticket medio por UF, maior em cima."""
    df = ticket_medio_por_estado.sort_values("ticket_medio", ascending=False)
    return _barh(df, x="ticket_medio", y="uf", titulo="06 · Ticket médio por UF")


def fig_clientes_uf(clientes_por_uf: pd.DataFrame) -> go.Figure:
    """12 - Clientes por UF, maior em cima."""
    df = clientes_por_uf.sort_values("clientes", ascending=False)
    return _barh(df, x="clientes", y="uf", titulo="12 · Clientes por UF")


def fig_nota_categoria(nota_por_categoria: pd.DataFrame) -> go.Figure:
    """04 - Nota por categoria: as 10 piores, em pontos (nao barras), pior em
    cima. Ponto porque a diferenca de nota e pequena e barra comeca no zero."""
    df = nota_por_categoria.sort_values("posicao").head(10)
    fig = px.scatter(df, x="nota_media", y="categoria", title="04 · Nota · 10 piores")
    fig.update_traces(marker=dict(color=COR, size=11))
    fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=8, r=8, t=48, b=8))
    return fig


def fig_pareto_vendedores(vendedores_pareto: pd.DataFrame) -> go.Figure:
    """09 - Concentracao de vendedores: curva acumulada com a linha de 80%."""
    df = vendedores_pareto.sort_values("posicao")
    fig = px.line(df, x="posicao", y="pct_acumulado", title="09 · Vendedores · Pareto")
    fig.update_traces(line_color=COR)
    fig.add_hline(y=80, line_dash="dash", line_color=DESTAQUE, annotation_text="80%")
    fig.update_layout(
        xaxis_title="posição do vendedor", yaxis_title="% acumulada da receita",
        margin=dict(l=8, r=8, t=48, b=8),
    )
    return fig
