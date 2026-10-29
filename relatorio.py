"""
relatorio.py: o mesmo painel num arquivo HTML, para quem nao roda Streamlit.

Le os marts com painel.ler(), formata com painel.reais/pct/numero e monta os
graficos com as mesmas funcoes de painel.py. Nao importa streamlit e nao desenha
nada que nao esteja em painel.py. Escreve relatorio.html na raiz, com as mesmas
quatro faixas do app.py. Rodar com:
    uv run python relatorio.py

Decisoes (spec):
- A lib do plotly vem do CDN uma vez so (primeiro grafico), os outros sem ela.
- Cada grafico tem div_id fixo (g01, g02...), senao o plotly sorteia um id novo
  a cada execucao e o arquivo muda sem o dado mudar.
- Sem filtro: faturamento no periodo padrao jan/2017 a ago/2018.
- Rodape com a data e hora de geracao, porque o arquivo nao fala com o banco.
"""
import sys
from datetime import datetime
from pathlib import Path

import painel

sys.stdout.reconfigure(encoding="utf-8")

SAIDA = Path(__file__).resolve().parent / "relatorio.html"


def _grafico(fig, div_id: str, primeiro: bool) -> str:
    """Converte uma figura plotly em HTML; a lib do CDN so no primeiro."""
    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn" if primeiro else False,
        div_id=div_id,
    )


def gerar_html(dados: dict) -> str:
    kpis = dados["kpis"].iloc[0]
    recompra_df = dados["recompra"]
    uma_vez = recompra_df.loc[recompra_df["pedidos_por_cliente"] == 1, "pct_clientes"]
    pct_recompra = 100 - float(uma_vez.iloc[0]) if len(uma_vez) else 0.0

    cartoes = [
        ("Ticket médio", painel.reais(kpis["ticket_medio"])),
        ("Cancelados · % dos pedidos", painel.pct(kpis["pct_cancelados"], 2)),
        ("Peso do frete", painel.pct(kpis["pct_frete"], 1)),
        ("Recompra", painel.pct(pct_recompra, 2)),
        ("No prazo", painel.pct(dados["entrega_no_prazo"].iloc[0]["pct_no_prazo"], 1)),
        ("Dias até entregar", painel.numero(kpis["dias_entrega"], 1)),
        ("Nota média", painel.numero(kpis["nota_media"], 2)),
    ]
    cartoes_html = "".join(
        f'<div class="card"><div class="rot">{rot}</div><div class="val">{val}</div></div>'
        for rot, val in cartoes
    )

    # Faturamento no periodo padrao, sem filtro.
    vm = dados["vendas_mensais"].copy()
    vm["mes_txt"] = vm["mes"].astype(str)
    recorte = vm[
        (vm["mes_txt"] >= painel.MES_INICIO_PADRAO)
        & (vm["mes_txt"] <= painel.MES_FIM_PADRAO)
    ]

    graficos = [
        (painel.fig_faturamento(recorte), "g01"),
        (painel.fig_top_categorias(dados["top_categorias"]), "g02"),
        (painel.fig_mix_pagamento(dados["mix_pagamento"]), "g07"),
        (painel.fig_ticket_uf(dados["ticket_medio_por_estado"]), "g06"),
        (painel.fig_clientes_uf(dados["clientes_por_uf"]), "g12"),
        (painel.fig_nota_categoria(dados["nota_por_categoria"]), "g04"),
        (painel.fig_pareto_vendedores(dados["vendedores_pareto"]), "g09"),
    ]
    blocos = [_grafico(fig, div_id, i == 0) for i, (fig, div_id) in enumerate(graficos)]

    gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<title>Olist · visão da operação</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 24px; color: #10171a; }}
  h1 {{ font-size: 26px; }}
  .cards {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 12px; margin: 16px 0; }}
  .card {{ border: 1px solid #cdd6cf; border-radius: 10px; padding: 12px; }}
  .rot {{ font-size: 12px; color: #6b7b7c; }}
  .val {{ font-size: 22px; font-weight: 600; margin-top: 4px; }}
  .full {{ margin: 16px 0; }}
  .linha {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 16px 0; }}
  footer {{ margin-top: 24px; padding-top: 12px; border-top: 1px solid #cdd6cf;
            font-size: 13px; color: #6b7b7c; }}
</style></head><body>
<h1>Olist · visão da operação</h1>
<p>Faturamento de jan/2017 a ago/2018. Cartões valem para o período inteiro.</p>
<div class="cards">{cartoes_html}</div>
<div class="full">{blocos[0]}</div>
<div class="linha">{blocos[1]}{blocos[2]}{blocos[3]}</div>
<div class="linha">{blocos[4]}{blocos[5]}{blocos[6]}</div>
<footer>Dados de {gerado_em}</footer>
</body></html>
"""


def main():
    dados = painel.ler()
    html = gerar_html(dados)
    SAIDA.write_text(html, encoding="utf-8")
    kb = SAIDA.stat().st_size / 1024
    print(f"  {SAIDA}  ({kb:.1f} KB)")


if __name__ == "__main__":
    main()
