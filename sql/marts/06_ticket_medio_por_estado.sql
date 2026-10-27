-- ============================================================================
-- Mart 06: Ticket medio por estado
-- Grao final: uma linha por UF do cliente.
-- Pergunta: quanto vale, em media, um pedido valido em cada estado?
-- Definicoes fechadas do curso usadas aqui:
--   pedido valido = status fora de ('canceled','unavailable')
--   receita       = soma de itens_pedido.preco, sem frete
-- Caminho entre as tabelas: o preco esta no item, a UF esta no cliente, e os
-- dois so se encontram passando por pedidos.
-- O grao muda duas vezes ao longo da consulta, e cada etapa abaixo diz o seu.
-- ============================================================================

WITH venda_de_cada_pedido AS (
    -- Mudanca de grao: de item (varias linhas por pedido) para pedido (uma linha).
    -- Somo o preco dos itens de cada pedido valido para ter a receita do pedido.
    SELECT
        ped.pedido_id,
        ped.cliente_id,
        SUM(item.preco) AS receita_do_pedido
    FROM refined.pedidos      AS ped
    JOIN refined.itens_pedido AS item ON item.pedido_id = ped.pedido_id
    WHERE ped.status NOT IN ('canceled', 'unavailable')
    GROUP BY ped.pedido_id, ped.cliente_id
),

pedido_com_estado AS (
    -- Mesmo grao (um pedido), agora trazendo a UF pelo cliente do pedido.
    SELECT
        cli.uf,
        venda.receita_do_pedido
    FROM venda_de_cada_pedido AS venda
    JOIN refined.clientes     AS cli ON cli.cliente_id = venda.cliente_id
)

-- Mudanca de grao: de pedido para UF. O ticket medio e a media da receita
-- entre os pedidos daquele estado, ja no grao de pedido, nunca de item.
SELECT
    uf,
    COUNT(*)                        AS pedidos,
    ROUND(AVG(receita_do_pedido), 2) AS ticket_medio
FROM pedido_com_estado
GROUP BY uf
ORDER BY ticket_medio;
