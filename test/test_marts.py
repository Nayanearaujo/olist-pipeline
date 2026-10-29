"""
Testes unitarios de pipeline/marts.py (o executor) e dos marts 01 e 03 em SQL.

O executor roda sobre uma pasta de marts inventada em tmp_path e um refined
minimo. Os marts 01 e 03 rodam sobre tabelas montadas a mao, para provar as
regras de grao com entrada conhecida.
"""
import duckdb
import pytest

from pipeline import db, marts

RAIZ_MARTS_SQL = None  # resolvido no primeiro uso


def _refined_minimo(con):
    """Cria as oito tabelas refined (vazias bastam para o executor achar)."""
    con.execute("CREATE SCHEMA refined")
    for t, cols in {
        "pedidos": "pedido_id VARCHAR",
        "itens_pedido": "pedido_id VARCHAR",
        "pagamentos": "pedido_id VARCHAR",
        "avaliacoes": "pedido_id VARCHAR",
        "clientes": "cliente_id VARCHAR",
        "vendedores": "vendedor_id VARCHAR",
        "produtos": "produto_id VARCHAR",
        "traducao_categorias": "categoria VARCHAR",
    }.items():
        con.execute(f"CREATE TABLE refined.{t} ({cols})")


def _preparar_executor(tmp_path, monkeypatch):
    banco = tmp_path / "olist.duckdb"
    con = duckdb.connect(str(banco))
    _refined_minimo(con)
    con.close()
    pasta = tmp_path / "marts"
    pasta.mkdir()
    monkeypatch.setattr(db, "BANCO", banco)
    monkeypatch.setattr(marts, "PASTA_MARTS", pasta)
    return banco, pasta


def test_arquivo_vira_tabela(tmp_path, monkeypatch):
    banco, pasta = _preparar_executor(tmp_path, monkeypatch)
    (pasta / "00_teste.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    marts.main()
    con = duckdb.connect(str(banco))
    n = con.execute("SELECT count(*) FROM marts.teste").fetchone()[0]
    con.close()
    assert n == 1


def test_arquivo_apagado_faz_o_mart_sumir(tmp_path, monkeypatch):
    banco, pasta = _preparar_executor(tmp_path, monkeypatch)
    arq = pasta / "00_teste.sql"
    arq.write_text("SELECT 1 AS x", encoding="utf-8")
    marts.main()
    arq.unlink()
    (pasta / "01_outro.sql").write_text("SELECT 2 AS y", encoding="utf-8")
    marts.main()
    con = duckdb.connect(str(banco))
    sobrou = con.execute(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'marts' AND table_name = 'teste'"
    ).fetchone()[0]
    con.close()
    assert sobrou == 0


def test_arquivo_sem_prefixo_para_antes_de_executar(tmp_path, monkeypatch):
    banco, pasta = _preparar_executor(tmp_path, monkeypatch)
    (pasta / "teste.sql").write_text("SELECT 1 AS x", encoding="utf-8")
    with pytest.raises(SystemExit):
        marts.main()


def test_mart_vazio_encerra(tmp_path, monkeypatch):
    banco, pasta = _preparar_executor(tmp_path, monkeypatch)
    # refined.pedidos esta vazio, entao este SELECT volta 0 linhas
    (pasta / "00_vazio.sql").write_text("SELECT pedido_id FROM refined.pedidos", encoding="utf-8")
    with pytest.raises(SystemExit):
        marts.main()


# --- marts 01 e 03 em SQL, sobre tabelas inventadas ------------------------
def _ler_sql(nome: str) -> str:
    from pathlib import Path
    raiz = Path(__file__).resolve().parent.parent
    return (raiz / "sql" / "marts" / nome).read_text(encoding="utf-8").strip().rstrip(";")


def _refined_para_01_03(con):
    con.execute("CREATE SCHEMA refined")
    # pedido o1 valido com 2 itens; o2 cancelado (fica fora da receita)
    con.execute("""
        CREATE TABLE refined.pedidos AS SELECT * FROM (VALUES
            ('o1','c1','delivered',TIMESTAMP '2017-05-01 10:00:00',
             TIMESTAMP '2017-05-05 15:00:00', DATE '2017-05-05'),
            ('o2','c2','canceled', TIMESTAMP '2017-05-01 10:00:00',
             NULL, DATE '2017-05-10'),
            ('o3','c3','delivered',TIMESTAMP '2017-05-01 10:00:00',
             TIMESTAMP '2017-05-20 09:00:00', DATE '2017-05-10')
        ) AS t(pedido_id, cliente_id, status, data_compra,
               data_entrega, data_entrega_prevista)
    """)
    # o1 tem dois itens de R$ 100 cada; o2 (cancelado) tem um item de R$ 500
    con.execute("""
        CREATE TABLE refined.itens_pedido AS SELECT * FROM (VALUES
            ('o1', 1, 100.00), ('o1', 2, 100.00), ('o2', 1, 500.00)
        ) AS t(pedido_id, item_seq, preco)
    """)


def test_mart01_cancelado_fica_fora_e_pedido_conta_uma_vez(tmp_path):
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    _refined_para_01_03(con)
    r = con.execute(_ler_sql("01_vendas_mensais.sql")).df()
    con.close()
    # so o1 e valido e tem itens: 1 pedido, receita 200 (2 itens de 100)
    assert len(r) == 1
    assert int(r.iloc[0]["pedidos"]) == 1
    assert float(r.iloc[0]["receita"]) == 200.0


def test_mart03_entrega_no_dia_previsto_de_tarde_esta_no_prazo(tmp_path):
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    _refined_para_01_03(con)
    r = con.execute(_ler_sql("03_entrega_no_prazo.sql")).df()
    con.close()
    # o1 entregue dia 05 (previsto 05): no prazo mesmo as 15h. o3 dia 20 (prev 10): atrasado.
    assert int(r.iloc[0]["entregues"]) == 2
    assert int(r.iloc[0]["no_prazo"]) == 1
    assert int(r.iloc[0]["atrasados"]) == 1
