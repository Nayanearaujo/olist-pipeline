-- Grao do resultado: uma linha por UF do cliente.
-- Pergunta: qual o ticket medio (receita por pedido valido) em cada estado?
-- Ticket medio tem definicao fechada: somar a receita de cada pedido primeiro,
-- depois tirar a media por pedido. Nunca a media do item.
-- O valor esta no item, a UF no cliente, e os dois so se encontram passando por
-- pedidos. O grao muda duas vezes: de item para pedido, de pedido para UF.
-- Palavras fechadas: pedido valido = status NOT IN ('canceled','unavailable');
-- receita = soma de preco, sem frete.

WITH receita_por_pedido AS (
    -- grao: um pedido valido, com a receita somada dos seus itens (sem frete)
    SELECT
        p.pedido_id,
        c.uf,
        SUM(i.preco) AS receita_pedido
    FROM refined.pedidos AS p
    JOIN refined.itens_pedido AS i ON i.pedido_id = p.pedido_id
    JOIN refined.clientes     AS c ON c.cliente_id = p.cliente_id
    WHERE p.status NOT IN ('canceled', 'unavailable')
    GROUP BY p.pedido_id, c.uf
)

-- grao: uma UF. media da receita entre os pedidos daquela UF.
SELECT
    uf,
    COUNT(*)                                   AS pedidos,
    ROUND(AVG(receita_pedido), 2)              AS ticket_medio
FROM receita_por_pedido
GROUP BY uf
ORDER BY ticket_medio DESC;
