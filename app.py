"""
app.py: o dashboard da Olist em Streamlit.

So arruma na tela o que painel.py entrega. Nenhum calculo aqui (sem groupby,
sum, mean, count, merge): numero novo exige mart novo. Rodar com:
    uv run streamlit run app.py

Layout (de cima para baixo, em quatro faixas), conforme o rascunho de
design/rascunho.png:
  Cabecalho: titulo + filtro de periodo
  Faixa 1: sete cartoes (esta tudo bem?)
  Faixa 2: faturamento mensal, largura inteira (esta subindo?)
  Faixa 3: receita por categoria | mix de pagamento | ticket por UF (onde?)
  Faixa 4: clientes por UF | nota 10 piores | Pareto de vendedores (por que?)
"""
import streamlit as st

import painel

st.set_page_config(page_title="Olist · visão da operação", layout="wide")


@st.cache_data
def carregar():
    return painel.ler()


def main():
    # 6. ERRO: sem banco ou faltando mart, avisa e para.
    try:
        dados = carregar()
    except Exception as e:  # noqa: BLE001
        st.error(
            "Não consegui ler os marts do olist.duckdb.\n\n"
            f"Detalhe: {e}\n\n"
            "Rode antes: `uv run python -m pipeline.marts`"
        )
        st.stop()

    faltando = [m for m in painel.MARTS if m not in dados or dados[m].empty]
    if faltando:
        st.error(
            "Faltam marts: " + ", ".join(faltando) + "\n\n"
            "Rode: `uv run python -m pipeline.marts`"
        )
        st.stop()

    # ---- Cabecalho + filtro ------------------------------------------------
    col_titulo, col_filtro = st.columns([2, 1])
    with col_titulo:
        st.title("Olist · visão da operação")
    with col_filtro:
        if st.button("Recarregar dados"):
            st.cache_data.clear()
            st.rerun()
        meses = sorted(dados["vendas_mensais"]["mes"].astype(str).unique())
        padrao_ini = painel.MES_INICIO_PADRAO if painel.MES_INICIO_PADRAO in meses else meses[0]
        padrao_fim = painel.MES_FIM_PADRAO if painel.MES_FIM_PADRAO in meses else meses[-1]
        ini, fim = st.select_slider(
            "Período (afeta só o faturamento)",
            options=meses, value=(padrao_ini, padrao_fim),
        )
        st.caption("os cartões valem para o período inteiro")

    kpis = dados["kpis"].iloc[0]
    # Unica conta permitida pela spec: o mart 05 guarda quem comprou 1 vez.
    recompra_df = dados["recompra"]
    uma_vez = recompra_df.loc[recompra_df["pedidos_por_cliente"] == 1, "pct_clientes"]
    pct_recompra = 100 - float(uma_vez.iloc[0]) if len(uma_vez) else 0.0

    # ---- Faixa 1: sete cartoes --------------------------------------------
    c = st.columns(7)
    c[0].metric("Ticket médio", painel.reais(kpis["ticket_medio"]))
    c[1].metric("Cancelados · % dos pedidos", painel.pct(kpis["pct_cancelados"], 2))
    c[2].metric("Peso do frete", painel.pct(kpis["pct_frete"], 1))
    c[3].metric("Recompra", painel.pct(pct_recompra, 2))
    c[4].metric("No prazo", painel.pct(dados["entrega_no_prazo"].iloc[0]["pct_no_prazo"], 1))
    c[5].metric("Dias até entregar", painel.numero(kpis["dias_entrega"], 1))
    c[6].metric("Nota média", painel.numero(kpis["nota_media"], 2))

    # ---- Faixa 2: faturamento (largura inteira, recortado pelo periodo) ----
    vm = dados["vendas_mensais"].copy()
    vm["mes_txt"] = vm["mes"].astype(str)
    recorte = vm[(vm["mes_txt"] >= ini) & (vm["mes_txt"] <= fim)]
    st.plotly_chart(painel.fig_faturamento(recorte), width="stretch")

    # ---- Faixa 3: onde? ----------------------------------------------------
    f3 = st.columns(3)
    with f3[0]:
        st.plotly_chart(painel.fig_top_categorias(dados["top_categorias"]), width="stretch")
    with f3[1]:
        st.plotly_chart(painel.fig_mix_pagamento(dados["mix_pagamento"]), width="stretch")
    with f3[2]:
        st.plotly_chart(painel.fig_ticket_uf(dados["ticket_medio_por_estado"]), width="stretch")

    # ---- Faixa 4: por que? -------------------------------------------------
    f4 = st.columns(3)
    with f4[0]:
        st.plotly_chart(painel.fig_clientes_uf(dados["clientes_por_uf"]), width="stretch")
    with f4[1]:
        st.plotly_chart(painel.fig_nota_categoria(dados["nota_por_categoria"]), width="stretch")
    with f4[2]:
        st.plotly_chart(painel.fig_pareto_vendedores(dados["vendedores_pareto"]), width="stretch")


if __name__ == "__main__":
    main()
