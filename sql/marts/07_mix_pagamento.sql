-- Grao do resultado: uma linha por tipo de pagamento.
-- Pergunta: quanto do dinheiro pago entra por cartao, boleto, voucher e debito,
-- nos pedidos validos?
-- A tabela pagamentos tem grao (pedido_id, pagamento_seq): um pedido pago com
-- dois vouchers e um cartao aparece em tres linhas. Por isso somamos o valor
-- de cada linha de pagamento, nao o valor por pedido.
-- Palavra fechada: pedido valido = status NOT IN ('canceled','unavailable').
--
-- Por que a soma de valor (R$ 15.739.137,01) passa da receita do mart 01
-- (R$ 13.494.400,74): receita e a soma do preco dos itens, sem frete. O valor
-- pago inclui frete, parcelas e o que o cliente pagou alem do item, entao e
-- naturalmente maior. Sao duas medidas diferentes do mesmo pedido.
-- Por que a soma de pedidos passa dos 98.206 validos com pagamento: um pedido
-- pago com cartao e voucher e contado uma vez em cada tipo, entao a soma das
-- contagens por tipo e maior que o numero de pedidos distintos.

WITH pagamentos_validos AS (
    -- grao: um pagamento (pedido_id, pagamento_seq) de um pedido valido
    SELECT
        pg.tipo,
        pg.pedido_id,
        pg.valor
    FROM refined.pagamentos AS pg
    JOIN refined.pedidos    AS p ON p.pedido_id = pg.pedido_id
    WHERE p.status NOT IN ('canceled', 'unavailable')
)

-- grao: um tipo de pagamento
SELECT
    tipo,
    COUNT(*)                                                 AS pagamentos,
    COUNT(DISTINCT pedido_id)                                AS pedidos,
    ROUND(SUM(valor), 2)                                     AS valor,
    ROUND(SUM(valor) * 100.0 / SUM(SUM(valor)) OVER (), 1)   AS pct_valor
FROM pagamentos_validos
GROUP BY tipo
ORDER BY valor DESC;
