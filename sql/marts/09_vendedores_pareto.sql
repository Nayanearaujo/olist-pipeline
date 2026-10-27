-- Grao do resultado: uma linha por vendedor com venda valida.
-- Pergunta: que fracao dos vendedores faz 80% da receita? (curva de Pareto)
-- Do maior para o menor, com a receita acumulada ate cada vendedor.
-- O passo novo e a janela com ordem: SUM(...) OVER (ORDER BY ...) soma da
-- primeira linha ate a atual, por isso o acumulado.
-- Desempate: ha vendedores com receita identica. Sem um criterio de desempate
-- no ORDER BY, eles receberiam o mesmo acumulado e rodar duas vezes poderia dar
-- ordem diferente. Desempatamos por vendedor_id, que e unico, para a saida ser
-- sempre a mesma.
-- Palavras fechadas: pedido valido = status NOT IN ('canceled','unavailable');
-- receita = soma de preco, sem frete.

WITH receita_por_vendedor AS (
    -- grao: um vendedor, com a receita dos seus itens em pedidos validos
    SELECT
        i.vendedor_id,
        SUM(i.preco)  AS receita
    FROM refined.itens_pedido AS i
    JOIN refined.pedidos      AS p ON p.pedido_id = i.pedido_id
    WHERE p.status NOT IN ('canceled', 'unavailable')
    GROUP BY i.vendedor_id
),

vendedor_uf AS (
    -- grao: um vendedor, com a sua receita e a sua UF
    SELECT
        r.vendedor_id,
        v.uf,
        r.receita
    FROM receita_por_vendedor AS r
    JOIN refined.vendedores   AS v ON v.vendedor_id = r.vendedor_id
)

-- grao: um vendedor, ordenado do maior para o menor, com posicao e acumulado
SELECT
    vendedor_id,
    uf,
    ROUND(receita, 2) AS receita,
    ROW_NUMBER() OVER (ORDER BY receita DESC, vendedor_id)                       AS posicao,
    ROUND(SUM(receita) OVER (ORDER BY receita DESC, vendedor_id)
          * 100.0 / SUM(receita) OVER (), 2)                                     AS pct_acumulado
FROM vendedor_uf
ORDER BY posicao;
