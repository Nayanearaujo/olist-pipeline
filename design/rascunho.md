# Rascunho da tela (o desenho antes do gráfico)

O desenho escrito em palavras, que vira a spec do `painel.py`/`app.py`. O PNG
exportado do Figma/Canva deve ser salvo aqui como `design/rascunho.png`.

## Quem lê e em que ordem

- **Quem lê:** a diretoria da Olist, uma vez por semana, sem tempo.
- **Primeiro olhar:** está tudo bem? → os 7 cartões, no topo.
- **Depois:** está subindo? (faturamento no tempo) · onde? (categoria, UF,
  pagamento) · por quê? (nota, concentração).

Leitura em Z: canto superior esquerdo é o lugar mais caro.

## As quatro faixas (grade de 12 colunas)

### Cabeçalho
`Olist · visão da operação` à esquerda; filtro de período à direita.

### Faixa 1 — está tudo bem? (7 cartões, cada um com a definição no rótulo)
| Cartão | Mart · coluna | Valor de referência |
|---|---|---|
| Ticket médio | kpis.ticket_medio | R$ 137,42 |
| Cancelados · % dos pedidos | kpis.pct_cancelados | 0,63% |
| Peso do frete | kpis.pct_frete | 14,2% |
| Recompra | 100 − recompra (1 pedido) | 3,04% |
| No prazo | entrega_no_prazo.pct_no_prazo | 93,2% |
| Dias até entregar | kpis.dias_entrega | 12,5 |
| Nota média | kpis.nota_media | 4,09 |

### Faixa 2 — está subindo? (largura inteira)
`01 · Faturamento mensal` — linha com marcadores, destaque em nov/2017.

### Faixa 3 — onde? (3 colunas)
`02 · Receita por categoria` (top 10, barras) · `07 · Mix de pagamento`
(barras) · `06 · Ticket por UF` (barras, PB em cima, SP embaixo).

### Faixa 4 — por quê? (3 colunas)
`12 · Clientes por UF` (barras) · `04 · Nota · 10 piores` (pontos, pior em
cima) · `09 · Vendedores · Pareto` (curva acumulada com linha de 80%).

## Regras de layout aplicadas
- Grade de 12 colunas: faixas de baixo em 4 + 4 + 4.
- Mais importante, maior e mais acima: faturamento ocupa a largura inteira.
- Uma cor só; destaque só onde o título comenta.
- Unidade e definição escritas no rótulo de cada cartão.
