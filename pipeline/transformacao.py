"""
Etapa 2: transformacao (raw -> refined).

Pega as oito tabelas de raw que o pipeline do curso usa, da a cada coluna o tipo
do que ela realmente e (data vira data, dinheiro vira numero), renomeia para
portugues em snake_case e remove duplicata exata. Nenhum nulo e preenchido nem
inventado: os nulos reais sao mantidos, so some a repeticao exata de linha.

A geolocalizacao fica de fora de proposito: nenhum mart do curso usa ela, e ela
e o desafio 2. A sua spec esta em specs/geolocalizacao.md.

Reexecucao: CREATE OR REPLACE TABLE, nunca append. Rodar com:
    uv run python -m pipeline.transformacao
"""
import sys

from pipeline.db import conectar, criar_schema

sys.stdout.reconfigure(encoding="utf-8")

# Cada entrada: nome da tabela refined -> SELECT que a constroi a partir de raw.
# Datas vem no formato 'YYYY-MM-DD HH:MM:SS'; TIMESTAMP onde a hora importa,
# DATE onde so o dia importa. Dinheiro em DECIMAL(10,2). Identificadores e
# codigos (ids, CEP) continuam VARCHAR.
TRANSFORMACOES = {
    "pedidos": """
        SELECT DISTINCT
            order_id                                           AS pedido_id,
            customer_id                                        AS cliente_id,
            order_status                                       AS status,
            order_purchase_timestamp::TIMESTAMP                AS data_compra,
            order_approved_at::TIMESTAMP                       AS data_aprovacao,
            order_delivered_carrier_date::TIMESTAMP            AS data_envio,
            order_delivered_customer_date::TIMESTAMP           AS data_entrega,
            order_estimated_delivery_date::DATE                AS data_entrega_prevista
        FROM raw.pedidos
    """,
    "itens_pedido": """
        SELECT DISTINCT
            order_id                        AS pedido_id,
            order_item_id::INTEGER          AS item_seq,
            product_id                      AS produto_id,
            seller_id                       AS vendedor_id,
            shipping_limit_date::TIMESTAMP  AS data_limite_envio,
            price::DECIMAL(10,2)            AS preco,
            freight_value::DECIMAL(10,2)    AS frete
        FROM raw.itens_pedido
    """,
    "pagamentos": """
        SELECT DISTINCT
            order_id                      AS pedido_id,
            payment_sequential::INTEGER   AS pagamento_seq,
            payment_type                  AS tipo,
            payment_installments::INTEGER AS parcelas,
            payment_value::DECIMAL(10,2)  AS valor
        FROM raw.pagamentos
    """,
    "avaliacoes": """
        SELECT DISTINCT
            review_id                        AS avaliacao_id,
            order_id                         AS pedido_id,
            review_score::INTEGER            AS nota,
            review_comment_title             AS titulo,
            review_comment_message           AS comentario,
            review_creation_date::TIMESTAMP  AS data_criacao,
            review_answer_timestamp::TIMESTAMP AS data_resposta
        FROM raw.avaliacoes
    """,
    "clientes": """
        SELECT DISTINCT
            customer_id               AS cliente_id,
            customer_unique_id        AS cliente_unico_id,
            customer_zip_code_prefix  AS cep_prefixo,
            customer_city             AS cidade,
            customer_state            AS uf
        FROM raw.clientes
    """,
    "vendedores": """
        SELECT DISTINCT
            seller_id               AS vendedor_id,
            seller_zip_code_prefix  AS cep_prefixo,
            seller_city             AS cidade,
            seller_state            AS uf
        FROM raw.vendedores
    """,
    "produtos": """
        SELECT DISTINCT
            product_id                   AS produto_id,
            product_category_name        AS categoria,
            product_name_lenght::INTEGER         AS tamanho_nome,
            product_description_lenght::INTEGER  AS tamanho_descricao,
            product_photos_qty::INTEGER          AS qtd_fotos,
            product_weight_g::INTEGER            AS peso_g,
            product_length_cm::INTEGER           AS comprimento_cm,
            product_height_cm::INTEGER           AS altura_cm,
            product_width_cm::INTEGER            AS largura_cm
        FROM raw.produtos
    """,
    "traducao_categorias": """
        SELECT DISTINCT
            product_category_name          AS categoria,
            product_category_name_english  AS categoria_en
        FROM raw.traducao_categorias
    """,
}


def main():
    con = conectar()
    criar_schema(con, "refined")

    total = 0
    for tabela, select in TRANSFORMACOES.items():
        origem = con.execute(
            f"SELECT count(*) FROM raw.{tabela}"
        ).fetchone()[0]
        con.execute(f"CREATE OR REPLACE TABLE refined.{tabela} AS {select}")
        destino = con.execute(
            f"SELECT count(*) FROM refined.{tabela}"
        ).fetchone()[0]
        dup = origem - destino
        total += destino
        marca = f"(-{dup:,} duplicatas)".replace(",", ".") if dup else "(0 duplicatas)"
        print(f"  refined.{tabela:<22} {destino:>9,} linhas  {marca}".replace(",", "."))

    print(f"  {'total':<22} {total:>9,} linhas".replace(",", "."))
    con.close()


if __name__ == "__main__":
    main()
