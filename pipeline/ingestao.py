"""
Etapa 1: ingestao.

Le os nove CSVs comprimidos de raw/ e grava cada um como uma tabela no schema
raw do olist.duckdb. Regra da camada raw: tudo entra como veio, todas as colunas
VARCHAR (texto), campo vazio virando NULL. Nada de tipo nem de limpeza aqui, isso
e trabalho da transformacao.

Idempotente: usa CREATE OR REPLACE TABLE, entao rodar de novo da o mesmo
resultado. Rodar com:
    uv run python -m pipeline.ingestao
"""
import sys
from pathlib import Path

from pipeline.db import conectar, criar_schema

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "raw"

# arquivo em raw/ -> nome da tabela no schema raw
ARQUIVOS = {
    "olist_orders_dataset.csv.gz": "pedidos",
    "olist_order_items_dataset.csv.gz": "itens_pedido",
    "olist_order_payments_dataset.csv.gz": "pagamentos",
    "olist_order_reviews_dataset.csv.gz": "avaliacoes",
    "olist_customers_dataset.csv.gz": "clientes",
    "olist_sellers_dataset.csv.gz": "vendedores",
    "olist_products_dataset.csv.gz": "produtos",
    "olist_geolocation_dataset.csv.gz": "geolocalizacao",
    "product_category_name_translation.csv.gz": "traducao_categorias",
}


def main():
    con = conectar()
    criar_schema(con, "raw")

    total = 0
    for arquivo, tabela in ARQUIVOS.items():
        caminho = RAW / arquivo
        if not caminho.exists():
            print(f"ERRO: nao encontrei {caminho}")
            sys.exit(1)
        # all_varchar=true garante a camada raw: toda coluna como texto.
        con.execute(f"""
            CREATE OR REPLACE TABLE raw.{tabela} AS
            SELECT * FROM read_csv_auto('{caminho.as_posix()}', all_varchar=true)
        """)
        n = con.execute(f"SELECT count(*) FROM raw.{tabela}").fetchone()[0]
        total += n
        print(f"  raw.{tabela:<22} {n:>9,} registros".replace(",", "."))

    print(f"  {'total':<22} {total:>9,} registros".replace(",", "."))
    con.close()


if __name__ == "__main__":
    main()
