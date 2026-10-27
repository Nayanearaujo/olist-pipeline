-- ============================================================================
-- Mart 10: Tempo de entrega por estado
-- Grao final: uma linha por UF do cliente.
-- Pergunta: quantos dias, da compra ate a entrega, em cada estado?
-- Denominador: so pedido delivered com data de entrega, o mesmo do mart 03.
-- O passo novo sao duas funcoes: date_diff('day', inicio, fim), que conta dias
-- de calendario, e median(), a mediana dos dias.
--
-- Decisao de inicio da contagem: conto da data_compra ate a data_entrega, que
-- e o tempo que o cliente de fato espera. Se eu partisse da data de envio,
-- estaria medindo o tempo da transportadora, nao o da loja, que e outra
-- pergunta. Conferi tambem que nenhum pedido entregue tem data de entrega
-- anterior a de compra, entao nao ha dia negativo e os 96.470 entregues ficam
-- todos no calculo.
-- ============================================================================

WITH espera_de_cada_entrega AS (
    -- Grao: um pedido entregue, com os dias ate chegar e a UF do cliente.
    SELECT
        cli.uf,
        date_diff('day', ped.data_compra, ped.data_entrega) AS dias
    FROM refined.pedidos  AS ped
    JOIN refined.clientes AS cli ON cli.cliente_id = ped.cliente_id
    WHERE ped.status = 'delivered'
      AND ped.data_entrega IS NOT NULL
)

-- Mudanca de grao: de pedido para UF. Media e mediana dos dias de espera.
SELECT
    uf,
    COUNT(*)            AS entregues,
    ROUND(AVG(dias), 1) AS dias_medio,
    median(dias)        AS dias_mediana
FROM espera_de_cada_entrega
GROUP BY uf
ORDER BY dias_medio DESC;
