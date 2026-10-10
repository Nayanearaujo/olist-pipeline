# Desafio 1: o que esse dado é capaz de responder

Nome: Nayane

## Os dez indicadores

1. Ticket médio de produtos por pedido - itens_pedido (order_id, price) - mostra quanto um cliente gasta em produtos numa compra típica, somando os itens de cada pedido antes de tirar a média e deixando o frete de fora.
2. Receita mensal de produtos - itens_pedido (order_id, price) + pedidos (order_id, order_purchase_timestamp, order_status) - mostra como as vendas crescem e variam ao longo dos meses, sem contar pedidos cancelados.
3. Tempo médio de entrega em dias - pedidos (order_purchase_timestamp, order_delivered_customer_date) - mede quantos dias o cliente espera entre comprar e receber.
4. Taxa de entregas atrasadas - pedidos (order_delivered_customer_date, order_estimated_delivery_date) - mede quantos pedidos chegaram depois da data prometida.
5. Nota média de avaliação por categoria de produto - avaliacoes (order_id, review_score) + itens_pedido (order_id, product_id) + produtos (product_id, product_category_name) - mostra quais categorias deixam o cliente mais ou menos satisfeito.
6. Ticket médio de produtos por estado do cliente - itens_pedido (order_id, price) + pedidos (order_id, customer_id) + clientes (customer_id, customer_state) - mostra em quais estados o pedido típico vale mais.
7. ? Taxa de recompra - pedidos (customer_id, order_status) + clientes (customer_id, customer_unique_id) - mede que parte das pessoas voltam a comprar, usando customer_unique_id porque customer_id muda a cada pedido.
8. Parcelamento médio por forma de pagamento - pagamentos (payment_type, payment_installments, payment_value) - mostra como o cliente prefere pagar e em quantas parcelas financia a compra.
9. Impacto do atraso na nota de avaliação - pedidos (order_id, order_delivered_customer_date, order_estimated_delivery_date) + avaliacoes (order_id, review_score) - mostra se atrasar a entrega altera a satisfação do cliente.
10. Peso do frete na receita por estado do vendedor - itens_pedido (seller_id, price, freight_value) + vendedores (seller_id, seller_state) - mostra de quais estados o frete pesa mais sobre o valor vendido.

## O que o dado NÃO sustenta

- Margem de lucro: o dado só tem o preço de venda e o frete. Não há custo do produto, impostos, comissão da plataforma nem custo logístico, então não dá para saber quanto sobra em cada venda.
- Taxa de conversão e custo de aquisição de cliente: não existem dados de visitas, tráfego ou marketing, só de quem já comprou.
- Giro de estoque: não há nenhuma tabela de estoque.
- NPS ou satisfação oficial: só temos review_score de 1 a 5 de quem respondeu, então a nota tem viés de resposta.

## Onde travou / dúvidas

- Indicador 7: pedidos cancelados entram ou não na recompra? Excluí os cancelados e indisponíveis. Só 3,04% das pessoas compraram mais de uma vez (2.888 de 94.990), o que me fez checar se customer_unique_id estava sendo usado certo.
- Indicador 9: um pedido pode ter mais de uma avaliação, então a unidade é a avaliação, não o pedido. Mesmo assim a diferença é grande: nota média 2,57 para pedidos atrasados contra 4,29 para os entregues no prazo.
- O painel lateral mostrava 28 valores em customer_state, mas a consulta retornou 27 estados. A estatística do painel é aproximada.

As consultas de cada indicador estão em `indicadores.sql`, uma célula por indicador no notebook do DuckDB.
