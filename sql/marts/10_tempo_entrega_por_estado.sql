-- Grao do resultado: uma linha por UF do cliente.
-- Pergunta: quantos dias, da compra ate a entrega, por estado?
-- Mesmo denominador do mart 03: so pedido delivered com data de entrega.
-- O passo novo sao duas funcoes: date_diff('day', inicio, fim), que conta dias
-- de calendario, e median().
-- Importante: contamos da data_compra ate a data_entrega, que e o tempo que o
-- cliente espera. Partir da data_envio mediria o tempo da transportadora, nao
-- o da loja.
-- Conferi: nenhum pedido entregue tem data de entrega anterior a de compra (zero
-- dias negativos), entao nao preciso de filtro para isso e os 96.470 entregues
-- continuam todos no denominador.

WITH entregas AS (
    -- grao: um pedido delivered com data de entrega, com os dias ate chegar e a UF
    SELECT
        c.uf,
        date_diff('day', p.data_compra, p.data_entrega) AS dias
    FROM refined.pedidos  AS p
    JOIN refined.clientes AS c ON c.cliente_id = p.cliente_id
    WHERE p.status = 'delivered'
      AND p.data_entrega IS NOT NULL
)

-- grao: uma UF
SELECT
    uf,
    COUNT(*)               AS entregues,
    ROUND(AVG(dias), 1)    AS dias_medio,
    median(dias)           AS dias_mediana
FROM entregas
GROUP BY uf
ORDER BY dias_medio DESC;
