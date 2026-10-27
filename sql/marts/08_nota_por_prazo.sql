-- ============================================================================
-- Mart 08: A nota de quem recebeu atrasado
-- Grao final: uma linha por situacao de entrega ('no_prazo' ou 'atrasado').
-- Pergunta: o atraso derruba a nota do cliente?
-- Denominador: so pedido delivered com data de entrega, o mesmo do mart 03.
-- Este mart junta duas ideias ja vistas: a nota por pedido (mart 04) e a
-- classificacao de prazo com CASE (mart 03).
--
-- Dois cuidados que mudam o numero sem dar erro na tela:
--   Grao da nota: a nota e do pedido, nao da avaliacao. Um pedido com duas
--     avaliacoes nao pode pesar o dobro, entao tiro a media das notas por
--     pedido antes de classificar por prazo.
--   Tipo da data: data_entrega e TIMESTAMP e data_entrega_prevista e DATE.
--     Comparo data_entrega::DATE, senao uma entrega as 15h do dia previsto
--     viraria 'atrasado' por causa das horas.
-- ============================================================================

WITH media_de_nota_por_pedido AS (
    -- Mudanca de grao: de avaliacao para pedido. Media das avaliacoes do pedido.
    SELECT
        pedido_id,
        AVG(nota) AS nota_do_pedido
    FROM refined.avaliacoes
    GROUP BY pedido_id
),

entrega_classificada AS (
    -- Grao: um pedido entregue com data, ja rotulado como no_prazo ou atrasado.
    SELECT
        ped.pedido_id,
        CASE
            WHEN ped.data_entrega::DATE <= ped.data_entrega_prevista THEN 'no_prazo'
            ELSE 'atrasado'
        END AS situacao
    FROM refined.pedidos AS ped
    WHERE ped.status = 'delivered'
      AND ped.data_entrega IS NOT NULL
),

pedido_avaliado_e_classificado AS (
    -- Grao: um pedido entregue que tambem foi avaliado, com situacao e nota.
    SELECT
        ec.situacao,
        mn.nota_do_pedido
    FROM entrega_classificada       AS ec
    JOIN media_de_nota_por_pedido   AS mn ON mn.pedido_id = ec.pedido_id
)

-- Mudanca de grao: de pedido para situacao. pct_nota_baixa = % de pedidos da
-- situacao com nota media ate 2.
SELECT
    situacao,
    COUNT(*)                                                      AS pedidos_avaliados,
    ROUND(AVG(nota_do_pedido), 2)                                 AS nota_media,
    ROUND(100.0 * COUNT(*) FILTER (WHERE nota_do_pedido <= 2) / COUNT(*), 1) AS pct_nota_baixa
FROM pedido_avaliado_e_classificado
GROUP BY situacao
ORDER BY situacao;
