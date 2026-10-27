"""
Conexao com o DuckDB do projeto e utilitarios de schema.

Este modulo e o unico lugar que sabe o nome do arquivo do banco. As outras
etapas (ingestao, transformacao, marts) pedem a conexao aqui e nunca abrem o
arquivo por conta propria.
"""
from pathlib import Path

import duckdb

# O banco mora na raiz do projeto, ao lado das pastas pipeline/, raw/ e sql/.
RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "olist.duckdb"


def conectar():
    """Abre o olist.duckdb na raiz do projeto, criando o arquivo se faltar."""
    return duckdb.connect(str(BANCO))


def criar_schema(con, nome):
    """CREATE SCHEMA IF NOT EXISTS <nome>."""
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {nome}")
