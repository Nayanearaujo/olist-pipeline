-- ============================================================================
-- Mart 11: KPIs da operacao (os cartoes do dashboard)
-- Grao final: a operacao inteira, uma linha so.
-- Pergunta: quais os numeros de topo que a diretoria olha primeiro?
-- Junta numa linha so os cartoes que vem de tabelas diferentes: ticket e frete
-- de itens_pedido, cancelamento de pedidos, prazo/dias de entrega de pedidos e
-- nota de avaliacoes. Cada fonte vira uma CTE de uma linha, e o SELECT final
-- junta as CTEs com virgula (CROSS JOIN sem ON). So e seguro porque 1x1x1x1 = 1:
-- se qualquer CTE voltasse com duas linhas, o mart dobraria calado.
-- Definicoes fechadas do curso:
--   pedido valido = status fora de ('canceled','unavailable')
--   receita       = soma de itens_pedido.preco, sem frete
-- O ticket e a receita por pedido somada primeiro, media por pedido depois,
-- nunca a media do preco do item.
-- ============================================================================

WITH receita_pedido AS (
    -- Grao: um pedido valido com item. Receita e frete somados por pedido.
    SELECT
        p.pedido_id,
        SUM(i.preco) AS receita,
        SUM(i.frete) AS frete
    FROM refined.pedidos      AS p
    JOIN refined.itens_pedido AS i ON i.pedido_id = p.pedido_id
    WHERE p.status NOT IN ('canceled', 'unavailable')
    GROUP BY p.pedido_id
),

venda AS (
    -- Grao: uma linha. Ticket medio/mediana no grao de pedido e peso do frete.
    -- Peso do frete = frete sobre o que o cliente pagou em item (preco + frete).
    SELECT
        ROUND(AVG(receita), 2)                                     AS ticket_medio,
        ROUND(MEDIAN(receita), 2)                                  AS ticket_mediana,
        ROUND(100.0 * SUM(frete) / (SUM(receita) + SUM(frete)), 1) AS pct_frete
    FROM receita_pedido
),

cancelamento AS (
    -- Grao: uma linha. Cancelados sobre TODOS os pedidos, nao so os validos.
    SELECT
        ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'canceled') / COUNT(*), 2) AS pct_cancelados
    FROM refined.pedidos
),

entrega AS (
    -- Grao: uma linha. Mesmo denominador do mart 03: delivered com data.
    SELECT
        ROUND(AVG(date_diff('day', data_compra, data_entrega)), 1) AS dias_entrega,
        MEDIAN(date_diff('day', data_compra, data_entrega))        AS dias_entrega_mediana
    FROM refined.pedidos
    WHERE status = 'delivered'
      AND data_entrega IS NOT NULL
),

satisfacao AS (
    -- Grao: uma linha. Nota media de todas as avaliacoes, sem passar por pedido.
    SELECT ROUND(AVG(nota), 2) AS nota_media
    FROM refined.avaliacoes
)

-- Grao: a operacao inteira. 1x1x1x1 = 1 linha.
SELECT *
FROM venda, cancelamento, entrega, satisfacao;
