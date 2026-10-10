-- ============================================================================
-- DESAFIO 1: INDICADORES SOBRE O SCHEMA raw (OLIST)
-- Notebook do DuckDB: UMA CÉLULA POR BLOCO abaixo, com o banco "olist" selecionado.
-- Copie cada bloco, do primeiro "--" até o ";" final, para uma célula nova.
-- No raw tudo é texto (VARCHAR): por isso os TRY_CAST. Valor inválido vira NULL
-- em vez de derrubar a consulta. A conversão definitiva é a etapa 2 do curso.
-- ============================================================================


-- ===== CÉLULA A · Validação das contagens (ingestão x anexo do curso) =====
-- Todas as diferenças devem ser 0. Se não forem, pare e reveja a ingestão.
SELECT 'avaliacoes' AS tabela, COUNT(*) AS linhas, 99224 AS esperado, COUNT(*) - 99224 AS diferenca FROM raw.avaliacoes
UNION ALL SELECT 'clientes', COUNT(*), 99441, COUNT(*) - 99441 FROM raw.clientes
UNION ALL SELECT 'geolocalizacao', COUNT(*), 1000163, COUNT(*) - 1000163 FROM raw.geolocalizacao
UNION ALL SELECT 'itens_pedido', COUNT(*), 112650, COUNT(*) - 112650 FROM raw.itens_pedido
UNION ALL SELECT 'pagamentos', COUNT(*), 103886, COUNT(*) - 103886 FROM raw.pagamentos
UNION ALL SELECT 'pedidos', COUNT(*), 99441, COUNT(*) - 99441 FROM raw.pedidos
UNION ALL SELECT 'produtos', COUNT(*), 32951, COUNT(*) - 32951 FROM raw.produtos
UNION ALL SELECT 'traducao_categorias', COUNT(*), 71, COUNT(*) - 71 FROM raw.traducao_categorias
UNION ALL SELECT 'vendedores', COUNT(*), 3095, COUNT(*) - 3095 FROM raw.vendedores
ORDER BY 1;


-- ===== CÉLULA B · Conferência: valores distintos de customer_state =====
-- O painel lateral mostrou 28 (o Brasil tem 27 UFs). A estatística do painel é
-- aproximada; esta consulta mostra os valores reais.
SELECT customer_state, COUNT(*) AS clientes
FROM raw.clientes
GROUP BY 1
ORDER BY 1;


-- ===== INDICADOR 1 · Ticket médio de produtos por pedido =====
-- Tabela: itens_pedido (order_id, price). Soma por pedido e só depois tira a média.
-- Não inclui frete. Média direta de price daria o preço médio por item, que é outro indicador.
WITH por_pedido AS (
  SELECT order_id,
         SUM(TRY_CAST(price AS DOUBLE)) AS valor_produtos
  FROM raw.itens_pedido
  GROUP BY order_id
)
SELECT COUNT(*)                          AS pedidos,
       ROUND(AVG(valor_produtos), 2)     AS ticket_medio,
       ROUND(MEDIAN(valor_produtos), 2)  AS ticket_mediano
FROM por_pedido;


-- ===== INDICADOR 2 · Receita mensal de produtos =====
-- Tabelas: itens_pedido (order_id, price) + pedidos (order_id, order_purchase_timestamp, order_status).
-- Exclui cancelados e indisponíveis. Os meses das pontas (2016 e 2018) são incompletos.
SELECT date_trunc('month', TRY_CAST(p.order_purchase_timestamp AS TIMESTAMP)) AS mes,
       COUNT(DISTINCT p.order_id)                  AS pedidos,
       ROUND(SUM(TRY_CAST(i.price AS DOUBLE)), 2)  AS receita
FROM raw.itens_pedido i
JOIN raw.pedidos p ON p.order_id = i.order_id
WHERE p.order_status NOT IN ('canceled', 'unavailable')
GROUP BY 1
ORDER BY 1;


-- ===== INDICADOR 3 · Tempo médio de entrega (dias) =====
-- Tabela: pedidos (order_purchase_timestamp, order_delivered_customer_date).
-- Considera só pedidos com data de entrega ao cliente preenchida.
WITH entregas AS (
  SELECT date_diff('day',
           TRY_CAST(order_purchase_timestamp AS TIMESTAMP),
           TRY_CAST(order_delivered_customer_date AS TIMESTAMP)) AS dias
  FROM raw.pedidos
  WHERE TRY_CAST(order_delivered_customer_date AS TIMESTAMP) IS NOT NULL
)
SELECT COUNT(*)                AS pedidos_entregues,
       ROUND(AVG(dias), 1)     AS dias_medios,
       ROUND(MEDIAN(dias), 1)  AS dias_mediana
FROM entregas;


-- ===== INDICADOR 4 · Taxa de entregas atrasadas =====
-- Tabela: pedidos (order_delivered_customer_date, order_estimated_delivery_date).
-- Atrasado = entregue depois da data estimada. Só entra quem tem as duas datas.
WITH datas AS (
  SELECT TRY_CAST(order_delivered_customer_date AS TIMESTAMP) AS entrega,
         TRY_CAST(order_estimated_delivery_date AS TIMESTAMP) AS estimada
  FROM raw.pedidos
)
SELECT COUNT(*)                                                              AS entregues,
       SUM(CASE WHEN entrega > estimada THEN 1 ELSE 0 END)                   AS atrasados,
       ROUND(100.0 * AVG(CASE WHEN entrega > estimada THEN 1 ELSE 0 END), 2) AS pct_atraso
FROM datas
WHERE entrega IS NOT NULL AND estimada IS NOT NULL;


-- ===== INDICADOR 5 · Nota média de avaliação por categoria de produto =====
-- Tabelas: avaliacoes (order_id, review_score) + itens_pedido (order_id, product_id)
--          + produtos (product_id, product_category_name).
-- DISTINCT em (pedido, categoria) evita repetir a nota de pedidos com vários itens
-- da mesma categoria. Produtos sem categoria entram como 'sem_categoria'.
-- Categorias com menos de 30 avaliações ficam de fora (amostra pequena demais).
WITH base AS (
  SELECT DISTINCT i.order_id,
         COALESCE(NULLIF(TRIM(pr.product_category_name), ''), 'sem_categoria') AS categoria
  FROM raw.itens_pedido i
  JOIN raw.produtos pr ON pr.product_id = i.product_id
)
SELECT b.categoria,
       COUNT(*)                                          AS avaliacoes,
       ROUND(AVG(TRY_CAST(a.review_score AS DOUBLE)), 2) AS nota_media
FROM base b
JOIN raw.avaliacoes a ON a.order_id = b.order_id
GROUP BY 1
HAVING COUNT(*) >= 30
ORDER BY nota_media DESC;


-- ===== INDICADOR 6 · Ticket médio de produtos por estado do cliente =====
-- Tabelas: itens_pedido (order_id, price) + pedidos (order_id, customer_id)
--          + clientes (customer_id, customer_state).
-- Soma por pedido primeiro, depois média por estado. Sem frete.
WITH por_pedido AS (
  SELECT order_id,
         SUM(TRY_CAST(price AS DOUBLE)) AS valor
  FROM raw.itens_pedido
  GROUP BY order_id
)
SELECT c.customer_state,
       COUNT(*)                  AS pedidos,
       ROUND(AVG(pp.valor), 2)   AS ticket_medio
FROM por_pedido pp
JOIN raw.pedidos  p ON p.order_id    = pp.order_id
JOIN raw.clientes c ON c.customer_id = p.customer_id
GROUP BY 1
ORDER BY ticket_medio DESC;


-- ===== INDICADOR 7 · Taxa de recompra (?) =====
-- Tabelas: pedidos (customer_id, order_id, order_status) + clientes (customer_id, customer_unique_id).
-- Usa customer_unique_id (a pessoa); customer_id muda a cada pedido.
-- Dúvida em aberto: filtrar ou não pedidos cancelados. Aqui eles ficam de fora.
WITH compras AS (
  SELECT c.customer_unique_id,
         COUNT(*) AS pedidos
  FROM raw.pedidos p
  JOIN raw.clientes c ON c.customer_id = p.customer_id
  WHERE p.order_status NOT IN ('canceled', 'unavailable')
  GROUP BY 1
)
SELECT COUNT(*)                                                           AS clientes,
       SUM(CASE WHEN pedidos > 1 THEN 1 ELSE 0 END)                       AS recompraram,
       ROUND(100.0 * AVG(CASE WHEN pedidos > 1 THEN 1 ELSE 0 END), 2)     AS pct_recompra
FROM compras;


-- ===== INDICADOR 8 · Parcelamento médio por forma de pagamento =====
-- Tabela: pagamentos (payment_type, payment_installments, payment_value).
-- Conta pagamentos, não pedidos: um pedido pode ter mais de um registro.
SELECT payment_type,
       COUNT(*)                                                     AS pagamentos,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)           AS pct_pagamentos,
       ROUND(AVG(TRY_CAST(payment_installments AS DOUBLE)), 2)      AS parcelas_medias,
       ROUND(SUM(TRY_CAST(payment_value AS DOUBLE)), 2)             AS valor_total
FROM raw.pagamentos
GROUP BY 1
ORDER BY pagamentos DESC;


-- ===== INDICADOR 9 · Impacto do atraso na nota de avaliação (?) =====
-- Tabelas: pedidos (order_id, datas de entrega) + avaliacoes (order_id, review_score).
-- Dúvida em aberto: um pedido pode ter mais de uma avaliação e nem todo pedido tem alguma.
-- A unidade aqui é a avaliação, não o pedido.
WITH ped AS (
  SELECT order_id,
         CASE
           WHEN TRY_CAST(order_delivered_customer_date AS TIMESTAMP)
              > TRY_CAST(order_estimated_delivery_date AS TIMESTAMP)
           THEN 'Atrasado'
           ELSE 'No prazo'
         END AS situacao_entrega
  FROM raw.pedidos
  WHERE TRY_CAST(order_delivered_customer_date AS TIMESTAMP) IS NOT NULL
)
SELECT p.situacao_entrega,
       COUNT(*)                                          AS avaliacoes,
       ROUND(AVG(TRY_CAST(a.review_score AS DOUBLE)), 2) AS nota_media
FROM ped p
JOIN raw.avaliacoes a ON a.order_id = p.order_id
GROUP BY 1
ORDER BY 1;


-- ===== INDICADOR 10 · Peso do frete na receita por estado do vendedor =====
-- Tabelas: itens_pedido (seller_id, price, freight_value) + vendedores (seller_id, seller_state).
-- Divide a soma do frete pela soma do preço, não a média das razões por item.
SELECT v.seller_state,
       COUNT(*)                                             AS itens,
       ROUND(SUM(TRY_CAST(i.freight_value AS DOUBLE)), 2)   AS frete,
       ROUND(SUM(TRY_CAST(i.price AS DOUBLE)), 2)           AS receita,
       ROUND(100.0 * SUM(TRY_CAST(i.freight_value AS DOUBLE))
             / NULLIF(SUM(TRY_CAST(i.price AS DOUBLE)), 0), 2) AS pct_frete
FROM raw.itens_pedido i
JOIN raw.vendedores v ON v.seller_id = i.seller_id
GROUP BY 1
ORDER BY pct_frete DESC;
