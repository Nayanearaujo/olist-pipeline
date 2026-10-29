-- ============================================================================
-- Mart 12: Clientes por estado
-- Grao final: uma UF.
-- Pergunta: quantas pessoas compram de cada estado?
-- Cliente e a pessoa (cliente_unico_id), nunca o cliente_id, que muda a cada
-- pedido. Por isso conto com DISTINCT cliente_unico_id.
-- A coluna clientes NAO soma entre UFs: 39 pessoas aparecem em mais de uma UF
-- (uma delas em tres), entao a soma da coluna da 96.136, nao as 96.096 pessoas
-- distintas do dataset. Esta certo para a pergunta "quantas pessoas compram de
-- la" e errado para qualquer total, igual a coluna pedidos do mart 02.
-- ============================================================================

SELECT
    uf,
    COUNT(DISTINCT cliente_unico_id) AS clientes
FROM refined.clientes
GROUP BY uf
ORDER BY clientes DESC;
