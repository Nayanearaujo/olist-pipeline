-- Grao do resultado: um mes de compra.
-- Pergunta: quantos pedidos validos e quanta receita em cada mes?
-- Definicoes fechadas: pedido valido = status fora de ('canceled','unavailable');
-- receita = soma de itens_pedido.preco, sem frete; mes = mes da data de compra.
-- Ja neste primeiro mart ha um JOIN que muda o grao de pedido para item, por
-- isso conto pedidos com DISTINCT.

SELECT
    date_trunc('month', p.data_compra)      AS mes,
    COUNT(DISTINCT p.pedido_id)             AS pedidos,
    ROUND(SUM(i.preco), 2)                  AS receita
FROM refined.pedidos      AS p
JOIN refined.itens_pedido AS i ON i.pedido_id = p.pedido_id
WHERE p.status NOT IN ('canceled', 'unavailable')
GROUP BY mes
ORDER BY mes;
