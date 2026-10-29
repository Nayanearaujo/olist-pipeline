"""
Testes unitarios de pipeline/db.py.

Banco novo dentro de tmp_path, nunca o olist.duckdb do projeto. Uso monkeypatch
na constante BANCO do modulo para apontar para o tmp_path.
"""
import duckdb

from pipeline import db


def test_conectar_cria_arquivo_que_faltava(tmp_path, monkeypatch):
    alvo = tmp_path / "olist.duckdb"
    monkeypatch.setattr(db, "BANCO", alvo)
    assert not alvo.exists()
    con = db.conectar()
    con.close()
    assert alvo.exists()


def test_criar_schema_e_idempotente(tmp_path):
    con = duckdb.connect(str(tmp_path / "s.duckdb"))
    db.criar_schema(con, "refined")
    db.criar_schema(con, "refined")  # roda duas vezes sem erro
    achou = con.execute(
        "SELECT count(*) FROM information_schema.schemata WHERE schema_name = 'refined'"
    ).fetchone()[0]
    con.close()
    assert achou == 1
