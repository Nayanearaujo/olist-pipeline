"""
Testes unitarios de pipeline/ingestao.py.

CSVs .csv.gz pequenos escritos pelo proprio teste, DuckDB em tmp_path. Nunca le
raw/ nem olist.duckdb do projeto. O valor esperado sai da entrada inventada.
"""
import gzip

import duckdb
import pytest

from pipeline import db, ingestao


def _escrever_csv_gz(caminho, conteudo: str):
    with gzip.open(caminho, "wt", encoding="utf-8") as f:
        f.write(conteudo)


def _montar_raw(tmp_path, monkeypatch):
    """Cria raw/ com os nove arquivos minimos e aponta o pipeline para tmp_path."""
    raw = tmp_path / "raw"
    raw.mkdir()
    # cada arquivo recebe 2 linhas de dado, com um cabecalho qualquer
    for arquivo in ingestao.ARQUIVOS:
        _escrever_csv_gz(raw / arquivo, "col_a,col_b\nx,1\ny,2\n")
    monkeypatch.setattr(ingestao, "RAW", raw)
    monkeypatch.setattr(db, "BANCO", tmp_path / "olist.duckdb")


def test_csv_vira_tabela_com_as_mesmas_linhas(tmp_path, monkeypatch):
    _montar_raw(tmp_path, monkeypatch)
    ingestao.main()
    con = duckdb.connect(str(tmp_path / "olist.duckdb"))
    # cada um dos 9 arquivos tinha 2 linhas de dado
    n = con.execute("SELECT count(*) FROM raw.pedidos").fetchone()[0]
    con.close()
    assert n == 2


def test_tudo_entra_como_texto(tmp_path, monkeypatch):
    _montar_raw(tmp_path, monkeypatch)
    ingestao.main()
    con = duckdb.connect(str(tmp_path / "olist.duckdb"))
    tipos = [r[1] for r in con.execute("DESCRIBE raw.pedidos").fetchall()]
    con.close()
    assert set(tipos) == {"VARCHAR"}


def test_arquivo_faltando_encerra(tmp_path, monkeypatch):
    _montar_raw(tmp_path, monkeypatch)
    # apaga um arquivo: a ingestao tem que parar
    (tmp_path / "raw" / "olist_orders_dataset.csv.gz").unlink()
    with pytest.raises(SystemExit):
        ingestao.main()
