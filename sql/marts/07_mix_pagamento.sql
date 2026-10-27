-- ============================================================================
-- Mart 07: Mix de pagamento
-- Grao final: uma linha por tipo de pagamento.
-- Pergunta: quanto do dinheiro pago entra por cada forma (cartao, boleto,
-- voucher, debito), considerando so pedidos validos?
-- Definicao fechada: pedido valido = status fora de ('canceled','unavailable').
--
-- Por que a soma de valor passa da receita do mart 01:
--   O mart 01 soma itens_pedido.preco (R$ 13.494.400,74), que e so o produto.
--   Aqui eu somo pagamentos.valor (R$ 15.739.137,01), que inclui o frete e os
--   juros do parcelamento. Sao duas medidas diferentes do mesmo pedido, entao
--   e esperado que o valor pago seja maior que a receita do produto.
-- Por que a soma de pedidos por tipo passa dos pedidos validos:
--   um pedido pago com cartao e voucher aparece uma vez em cada tipo, logo a
--   soma das contagens por tipo e maior que o numero de pedidos distintos.
-- Observacao de grao: pagamentos tem grao (pedido_id, pagamento_seq), ou seja,
-- um pedido pode ter varias linhas de pagamento. Por isso somo valor por linha
-- de pagamento, e conto pedidos com DISTINCT.
-- ============================================================================

WITH pagamento_de_pedido_valido AS (
    -- Grao: uma linha de pagamento de um pedido valido.
    SELECT
        pag.tipo,
        pag.pedido_id,
        pag.valor
    FROM refined.pagamentos AS pag
    JOIN refined.pedidos    AS ped ON ped.pedido_id = pag.pedido_id
    WHERE ped.status NOT IN ('canceled', 'unavailable')
)

-- Grao: um tipo de pagamento. pct_valor e a fatia de cada tipo no valor total.
SELECT
    tipo,
    COUNT(*)                                                 AS pagamentos,
    COUNT(DISTINCT pedido_id)                                AS pedidos,
    ROUND(SUM(valor), 2)                                     AS valor,
    ROUND(100.0 * SUM(valor) / SUM(SUM(valor)) OVER (), 1)   AS pct_valor
FROM pagamento_de_pedido_valido
GROUP BY tipo
ORDER BY valor DESC;
