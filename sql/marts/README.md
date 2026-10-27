# Desafio 3: marts 06 a 10

Cinco marts em SQL, um arquivo por pergunta de negócio, que o `pipeline.marts`
transforma em tabela no schema `marts`. Entram da camada `refined`, saem como
`marts.*`.

## As regras que valem para os cinco

1. A primeira linha de cada arquivo diz o grão do resultado, e cada CTE diz o seu.
2. As quatro palavras com definição fechada do curso:
   - pedido válido: `status NOT IN ('canceled', 'unavailable')`
   - receita: `SUM(preco)`, sem frete
   - cliente: a pessoa, `cliente_unico_id`, nunca o `cliente_id`
   - mês: o mês da compra, `date_trunc('month', data_compra)`
3. Os arquivos rodam pelo `pipeline.marts`, não só no notebook.

## Os cinco marts e os números de conferência

Os números abaixo foram conferidos contra o dado do curso. Cada mart bate com os
alvos do guia da aula 3.

| Arquivo | Grão | Conferência |
|---|---|---|
| `06_ticket_medio_por_estado.sql` | uma UF | 27 linhas, soma de pedidos 98.199, SP tem o menor ticket (R$ 125,57) |
| `07_mix_pagamento.sql` | um tipo de pagamento | 4 linhas, credit_card 78,5% do valor, soma de valor R$ 15.739.137,01 |
| `08_nota_por_prazo.sql` | uma situação de entrega | 2 linhas, soma de pedidos avaliados 95.824, nota dos atrasados 2,27 |
| `09_vendedores_pareto.sql` | um vendedor | 3.053 linhas, último acumulado 100,00, primeiro a passar de 80% na posição 540 |
| `10_tempo_entrega_por_estado.sql` | uma UF | 27 linhas, soma de entregues 96.470, SP o mais rápido (8,7), RR o mais lento (29,3) |

## Decisões que valem registrar

- Mart 06: o ticket médio soma a receita por pedido primeiro e só depois tira a
  média por pedido. Tirar a média sobre o item daria peso maior a pedido com mais
  itens, e o número ficaria errado sem nenhum erro na tela.
- Mart 07: a soma do valor (R$ 15.739.137,01) passa da receita do mart 01
  (R$ 13.494.400,74) porque valor pago inclui frete e parcelas, enquanto receita é
  só o preço dos itens. E a soma de pedidos passa dos válidos porque um pedido pago
  com cartão e voucher é contado em dois tipos. O mart tem 4 linhas, não 5: existe um
  tipo `not_defined`, mas os seus 3 pagamentos estão todos em pedidos não válidos, e
  o filtro de pedido válido os deixa de fora.
- Mart 08: a nota é por pedido, então tiro a média das avaliações de cada pedido
  antes de agrupar por prazo. E comparo `data_entrega::DATE <= data_entrega_prevista`,
  senão uma entrega no dia previsto, mas de tarde, viraria atraso.
- Mart 09: desempato o `ORDER BY` da janela por `vendedor_id`, porque há vendedores
  com receita idêntica e sem desempate a ordem não seria estável entre execuções.
- Mart 10: conto da compra até a entrega, que é o tempo que o cliente espera.
  Partir da data de envio mediria o tempo da transportadora, não o da loja.

## Como rodar

```bash
uv run python -m pipeline.ingestao
uv run python -m pipeline.transformacao
uv run python -m pipeline.marts
```

A saída esperada do `pipeline.marts` tem os dez marts (01 a 05 já existentes, mais
06 a 10 deste desafio).
