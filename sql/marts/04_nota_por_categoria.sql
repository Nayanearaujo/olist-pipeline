-- Grao do resultado: uma categoria com 100 pedidos avaliados ou mais.
-- Pergunta: que nota cada categoria recebe?
-- A nota e do pedido e a categoria e do item. Juntar direto daria peso maior a
-- quem comprou mais itens, por isso ajusto o grao em degraus (CTEs) antes de
-- tirar a media por categoria. So fica quem tem 100 pedidos avaliados ou mais,
-- senao categorias minusculas dominam o ranking por acaso.

WITH nota_pedido AS (
    -- grao: um pedido avaliado, com a media das suas avaliacoes
    SELECT pedido_id, AVG(nota) AS nota
    FROM refined.avaliacoes
    GROUP BY pedido_id
),

categoria_pedido AS (
    -- grao: um par (pedido, categoria); pedido com varios itens da mesma
    -- categoria vira uma linha so
    SELECT DISTINCT
        i.pedido_id,
        COALESCE(tr.categoria_en, pr.categoria, 'sem_categoria') AS categoria
    FROM refined.itens_pedido AS i
    LEFT JOIN refined.produtos AS pr ON pr.produto_id = i.produto_id
    LEFT JOIN refined.traducao_categorias AS tr ON tr.categoria = pr.categoria
),

por_categoria AS (
    -- grao: uma categoria; media das notas dos pedidos daquela categoria
    SELECT
        cp.categoria,
        AVG(np.nota)   AS nota_media,
        COUNT(*)       AS pedidos_avaliados
    FROM categoria_pedido AS cp
    JOIN nota_pedido      AS np ON np.pedido_id = cp.pedido_id
    GROUP BY cp.categoria
    HAVING COUNT(*) >= 100
)

-- grao: uma categoria, da pior nota para a melhor
SELECT
    categoria,
    ROUND(nota_media, 2) AS nota_media,
    pedidos_avaliados,
    RANK() OVER (ORDER BY nota_media) AS posicao
FROM por_categoria
ORDER BY nota_media;
