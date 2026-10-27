-- Grao do resultado: a operacao inteira, uma linha so.
-- Pergunta: quanto chegou no prazo?
-- Denominador: so pedido delivered com data de entrega (96.470). Os 8 entregues
-- sem data ficam de fora, pois nao da para dizer se chegaram no prazo.
-- Cuidado de tipo: comparo data_entrega::DATE <= data_entrega_prevista, senao
-- uma entrega no dia previsto, mas de tarde, viraria atraso (data_entrega e
-- TIMESTAMP e a prevista e DATE).

WITH entregas AS (
    -- grao: um pedido delivered com data, marcado como no prazo (1) ou nao (0)
    SELECT
        CASE WHEN data_entrega::DATE <= data_entrega_prevista THEN 1 ELSE 0 END AS no_prazo
    FROM refined.pedidos
    WHERE status = 'delivered'
      AND data_entrega IS NOT NULL
)

-- grao: a operacao inteira
SELECT
    COUNT(*)                                     AS entregues,
    SUM(no_prazo)                                AS no_prazo,
    COUNT(*) - SUM(no_prazo)                     AS atrasados,
    ROUND(100.0 * SUM(no_prazo) / COUNT(*), 1)   AS pct_no_prazo
FROM entregas;
