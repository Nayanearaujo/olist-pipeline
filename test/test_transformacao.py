"""
Testes unitarios de pipeline/transformacao.py.

Monta um schema raw minimo com dado inventado em tmp_path e roda a
transformacao. Checa as regras que a spec promete: dedup exata, tipo de data e
dinheiro, e CEP mantendo o zero a esquerda. O valor esperado sai da entrada.
"""
import duckdb

from pipeline import db, transformacao


def _raw_minimo(con):
    """Cria as oito tabelas raw que a transformacao le, com poucas linhas."""
    con.execute("CREATE SCHEMA raw")
    # pedidos: 2 linhas, sendo a 2a uma copia exata da 1a (duplicata a remover)
    con.execute("""
        CREATE TABLE raw.pedidos AS SELECT * FROM (VALUES
            ('o1','c1','delivered','2017-05-01 10:00:00','2017-05-01 11:00:00',
             '2017-05-02 00:00:00','2017-05-05 15:00:00','2017-05-10'),
            ('o1','c1','delivered','2017-05-01 10:00:00','2017-05-01 11:00:00',
             '2017-05-02 00:00:00','2017-05-05 15:00:00','2017-05-10'),
            ('o2','c2','canceled','2017-06-01 10:00:00',NULL,NULL,NULL,'2017-06-10')
        ) AS t(order_id, customer_id, order_status, order_purchase_timestamp,
               order_approved_at, order_delivered_carrier_date,
               order_delivered_customer_date, order_estimated_delivery_date)
    """)
    con.execute("""
        CREATE TABLE raw.itens_pedido AS SELECT * FROM (VALUES
            ('o1','1','p1','s1','2017-05-02 00:00:00','99.90','10.00')
        ) AS t(order_id, order_item_id, product_id, seller_id,
               shipping_limit_date, price, freight_value)
    """)
    con.execute("""
        CREATE TABLE raw.pagamentos AS SELECT * FROM (VALUES
            ('o1','1','credit_card','3','109.90')
        ) AS t(order_id, payment_sequential, payment_type,
               payment_installments, payment_value)
    """)
    con.execute("""
        CREATE TABLE raw.avaliacoes AS SELECT * FROM (VALUES
            ('r1','o1','5',NULL,NULL,'2017-05-06 00:00:00','2017-05-07 00:00:00')
        ) AS t(review_id, order_id, review_score, review_comment_title,
               review_comment_message, review_creation_date, review_answer_timestamp)
    """)
    # clientes: CEP com zero a esquerda, para provar que sobrevive
    con.execute("""
        CREATE TABLE raw.clientes AS SELECT * FROM (VALUES
            ('c1','u1','01151','sao paulo','SP'),
            ('c2','u2','20010','rio de janeiro','RJ')
        ) AS t(customer_id, customer_unique_id, customer_zip_code_prefix,
               customer_city, customer_state)
    """)
    con.execute("""
        CREATE TABLE raw.vendedores AS SELECT * FROM (VALUES
            ('s1','04011','sao paulo','SP')
        ) AS t(seller_id, seller_zip_code_prefix, seller_city, seller_state)
    """)
    con.execute("""
        CREATE TABLE raw.produtos AS SELECT * FROM (VALUES
            ('p1','beleza_saude','40','200','3','300','20','10','15')
        ) AS t(product_id, product_category_name, product_name_lenght,
               product_description_lenght, product_photos_qty, product_weight_g,
               product_length_cm, product_height_cm, product_width_cm)
    """)
    con.execute("""
        CREATE TABLE raw.traducao_categorias AS SELECT * FROM (VALUES
            ('beleza_saude','health_beauty')
        ) AS t(product_category_name, product_category_name_english)
    """)


def _preparar(tmp_path, monkeypatch):
    banco = tmp_path / "olist.duckdb"
    con = duckdb.connect(str(banco))
    _raw_minimo(con)
    con.close()
    monkeypatch.setattr(db, "BANCO", banco)
    return banco


def test_duplicata_exata_sai(tmp_path, monkeypatch):
    banco = _preparar(tmp_path, monkeypatch)
    transformacao.main()
    con = duckdb.connect(str(banco))
    n = con.execute("SELECT count(*) FROM refined.pedidos").fetchone()[0]
    con.close()
    # entraram 3 linhas (uma delas copia exata); sai 2
    assert n == 2


def test_data_vira_timestamp_e_dinheiro_vira_decimal(tmp_path, monkeypatch):
    banco = _preparar(tmp_path, monkeypatch)
    transformacao.main()
    con = duckdb.connect(str(banco))
    tipos_ped = dict((r[0], r[1]) for r in con.execute("DESCRIBE refined.pedidos").fetchall())
    tipos_item = dict((r[0], r[1]) for r in con.execute("DESCRIBE refined.itens_pedido").fetchall())
    con.close()
    assert tipos_ped["data_compra"] == "TIMESTAMP"
    assert tipos_item["preco"].startswith("DECIMAL")


def test_cep_mantem_zero_a_esquerda(tmp_path, monkeypatch):
    banco = _preparar(tmp_path, monkeypatch)
    transformacao.main()
    con = duckdb.connect(str(banco))
    cep = con.execute(
        "SELECT cep_prefixo FROM refined.clientes WHERE cliente_id = 'c1'"
    ).fetchone()[0]
    con.close()
    assert cep == "01151"
