-- Grao do resultado: uma categoria de produto.
-- Pergunta: quanto cada categoria vendeu, com o nome em ingles?
-- Definicoes fechadas: pedido valido; receita = soma de preco, sem frete.
-- Uso LEFT JOIN na traducao e no produto para nao perder venda: 610 produtos
-- nao tem categoria e 2 categorias nao tem traducao. Com JOIN comum essas
-- vendas sumiriam do ranking sem aviso. Quando falta categoria, viram
-- 'sem_categoria'; quando falta traducao, fica o nome original em portugues.
-- A coluna pedidos nao soma entre categorias: um pedido com itens de duas
-- categorias conta em cada uma.

SELECT
    COALESCE(tr.categoria_en, pr.categoria, 'sem_categoria') AS categoria,
    COUNT(DISTINCT p.pedido_id)                              AS pedidos,
    COUNT(*)                                                 AS itens,
    ROUND(SUM(i.preco), 2)                                   AS receita
FROM refined.pedidos          AS p
JOIN refined.itens_pedido     AS i  ON i.pedido_id = p.pedido_id
LEFT JOIN refined.produtos    AS pr ON pr.produto_id = i.produto_id
LEFT JOIN refined.traducao_categorias AS tr ON tr.categoria = pr.categoria
WHERE p.status NOT IN ('canceled', 'unavailable')
GROUP BY COALESCE(tr.categoria_en, pr.categoria, 'sem_categoria')
ORDER BY receita DESC;
