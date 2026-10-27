-- Grao do resultado: um numero de pedidos por cliente (1, 2, 3...).
-- Pergunta: quantas pessoas compraram uma vez, quantas duas, quantas tres?
-- Palavra fechada: cliente = a pessoa, cliente_unico_id, nunca o cliente_id,
-- que muda a cada pedido. Agrupar por cliente_id daria recompra zero sem erro
-- na tela. O grao muda duas vezes: de pedido para pessoa, de pessoa para
-- quantidade de pedidos.

WITH pedidos_por_pessoa AS (
    -- grao: uma pessoa, com quantos pedidos validos ela fez
    SELECT
        c.cliente_unico_id,
        COUNT(*) AS qtd_pedidos
    FROM refined.pedidos  AS p
    JOIN refined.clientes AS c ON c.cliente_id = p.cliente_id
    WHERE p.status NOT IN ('canceled', 'unavailable')
    GROUP BY c.cliente_unico_id
)

-- grao: uma quantidade de pedidos. pct sobre o total de pessoas (janela vazia).
SELECT
    qtd_pedidos                                           AS pedidos_por_cliente,
    COUNT(*)                                              AS clientes,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)    AS pct_clientes
FROM pedidos_por_pessoa
GROUP BY qtd_pedidos
ORDER BY qtd_pedidos;
