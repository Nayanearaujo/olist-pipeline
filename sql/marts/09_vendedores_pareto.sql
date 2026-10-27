-- ============================================================================
-- Mart 09: Concentracao de vendedores (curva de Pareto)
-- Grao final: uma linha por vendedor com venda valida.
-- Pergunta: que fracao dos vendedores faz 80% da receita?
-- Definicoes fechadas: pedido valido = status fora de ('canceled','unavailable');
-- receita = soma de itens_pedido.preco, sem frete.
--
-- O passo novo e a janela ordenada: SUM(receita) OVER (ORDER BY ...) soma da
-- primeira linha ate a linha atual, dando a receita acumulada da curva.
-- Desempate: ha vendedores com receita identica. Sem um criterio de desempate
-- no ORDER BY da janela, eles receberiam o mesmo acumulado e a ordem poderia
-- mudar entre execucoes. Desempato por vendedor_id, que e unico, para a saida
-- ser sempre a mesma.
-- ============================================================================

WITH receita_de_cada_vendedor AS (
    -- Mudanca de grao: de item para vendedor. Receita de cada vendedor em
    -- pedidos validos, com a sua UF.
    SELECT
        item.vendedor_id,
        vnd.uf,
        SUM(item.preco) AS receita
    FROM refined.itens_pedido AS item
    JOIN refined.pedidos      AS ped ON ped.pedido_id = item.pedido_id
    JOIN refined.vendedores   AS vnd ON vnd.vendedor_id = item.vendedor_id
    WHERE ped.status NOT IN ('canceled', 'unavailable')
    GROUP BY item.vendedor_id, vnd.uf
),

curva AS (
    -- Mesmo grao (um vendedor), agora com posicao no ranking e receita acumulada.
    -- O frame da janela acumulada e escrito por extenso para nao depender do padrao.
    SELECT
        vendedor_id,
        uf,
        receita,
        ROW_NUMBER() OVER (ORDER BY receita DESC, vendedor_id) AS posicao,
        SUM(receita) OVER (
            ORDER BY receita DESC, vendedor_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS receita_ate_aqui,
        SUM(receita) OVER () AS receita_total
    FROM receita_de_cada_vendedor
)

-- Grao: um vendedor, do maior para o menor. pct_acumulado vai ate 100,00 na
-- ultima linha.
SELECT
    vendedor_id,
    uf,
    ROUND(receita, 2)                                   AS receita,
    posicao,
    ROUND(100.0 * receita_ate_aqui / receita_total, 2)  AS pct_acumulado
FROM curva
ORDER BY posicao;
