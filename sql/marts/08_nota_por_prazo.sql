-- Grao do resultado: uma linha por situacao de entrega (no_prazo ou atrasado).
-- Pergunta: o atraso derruba a nota?
-- Mesmo denominador do mart 03: so pedido delivered com data de entrega.
-- Combina duas ideias: a nota por pedido (como no mart 04) e o CASE de prazo
-- (como no mart 03).
-- Armadilha do grao: a nota e do pedido, nao da avaliacao. Um pedido com duas
-- avaliacoes nao pode pesar o dobro, entao tiramos a media das notas por pedido
-- antes de agrupar por situacao.
-- Armadilha do tipo: data_entrega e TIMESTAMP e data_entrega_prevista e DATE.
-- Comparar direto transforma a prevista em meia-noite, e uma entrega as 15h do
-- dia previsto viraria "atrasada". Por isso comparamos data_entrega::DATE.

WITH nota_por_pedido AS (
    -- grao: um pedido avaliado, com a media das suas avaliacoes
    SELECT
        pedido_id,
        AVG(nota) AS nota
    FROM refined.avaliacoes
    GROUP BY pedido_id
),

pedidos_entregues AS (
    -- grao: um pedido delivered com data de entrega, ja classificado por prazo
    SELECT
        p.pedido_id,
        CASE
            WHEN p.data_entrega::DATE <= p.data_entrega_prevista THEN 'no_prazo'
            ELSE 'atrasado'
        END AS situacao
    FROM refined.pedidos AS p
    WHERE p.status = 'delivered'
      AND p.data_entrega IS NOT NULL
),

pedido_situacao_nota AS (
    -- grao: um pedido, com situacao de prazo e a sua nota
    SELECT
        e.situacao,
        n.nota
    FROM pedidos_entregues AS e
    JOIN nota_por_pedido   AS n ON n.pedido_id = e.pedido_id
)

-- grao: uma situacao de entrega
SELECT
    situacao,
    COUNT(*)                                                      AS pedidos_avaliados,
    ROUND(AVG(nota), 2)                                           AS nota_media,
    ROUND(COUNT(*) FILTER (WHERE nota <= 2) * 100.0 / COUNT(*), 1) AS pct_nota_baixa
FROM pedido_situacao_nota
GROUP BY situacao
ORDER BY situacao;
