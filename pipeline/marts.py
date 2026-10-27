"""
Etapa 3: marts (refined -> marts).

Encanamento puro: le cada arquivo sql/marts/*.sql e o transforma numa tabela no
schema marts. A regra de negocio mora inteira nos arquivos .sql; este script so
os executa, na ordem alfabetica, sem alterar o SQL.

Nome da tabela = nome do arquivo sem a extensao e sem o prefixo numerico:
    sql/marts/06_ticket_medio_por_estado.sql -> marts.ticket_medio_por_estado

Reexecucao: o schema marts e apagado e recriado a cada execucao, entao um mart
cujo arquivo foi apagado deixa de existir. Tudo roda numa transacao: se algo
falhar, o schema volta ao estado anterior. Rodar com:
    uv run python -m pipeline.marts
"""
import re
import sys
from pathlib import Path

from pipeline.db import conectar, criar_schema

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
PASTA_MARTS = RAIZ / "sql" / "marts"

# As oito tabelas que a refined precisa ter para os marts rodarem.
REFINED_ESPERADO = [
    "pedidos", "itens_pedido", "pagamentos", "avaliacoes",
    "clientes", "vendedores", "produtos", "traducao_categorias",
]

PREFIXO = re.compile(r"^\d+_")


def nome_tabela(arquivo: Path) -> str:
    """06_ticket_medio_por_estado.sql -> ticket_medio_por_estado"""
    base = arquivo.stem
    if not PREFIXO.match(base):
        print(f"ERRO: arquivo sem prefixo NN_: {arquivo.name}")
        sys.exit(1)
    return PREFIXO.sub("", base)


def main():
    con = conectar()

    # Pre-requisito: a refined tem que existir inteira.
    existentes = {
        r[0] for r in con.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'refined'
        """).fetchall()
    }
    faltando = [t for t in REFINED_ESPERADO if t not in existentes]
    if faltando:
        print("ERRO: faltam tabelas em refined:", ", ".join(faltando))
        print('Rode antes: uv run python -m pipeline.transformacao')
        sys.exit(1)

    arquivos = sorted(PASTA_MARTS.glob("*.sql"))
    if not arquivos:
        print(f"ERRO: nenhum .sql em {PASTA_MARTS}")
        sys.exit(1)

    # Checa nomes duplicados antes de executar qualquer SQL.
    nomes = {}
    for arq in arquivos:
        nome = nome_tabela(arq)
        if nome in nomes:
            print(f"ERRO: {arq.name} e {nomes[nome]} geram a mesma tabela marts.{nome}")
            sys.exit(1)
        nomes[nome] = arq.name

    # Tudo numa transacao: ou todos os marts entram, ou nenhum muda.
    try:
        con.execute("BEGIN")
        con.execute("DROP SCHEMA IF EXISTS marts CASCADE")
        criar_schema(con, "marts")

        total = 0
        resultados = []
        for arq in arquivos:
            nome = nome_tabela(arq)
            sql = arq.read_text(encoding="utf-8").strip().rstrip(";").strip()
            try:
                con.execute(f"CREATE TABLE marts.{nome} AS {sql}")
            except Exception as e:
                print(f"ERRO em {arq.name}: {e}")
                con.execute("ROLLBACK")
                sys.exit(1)
            n = con.execute(f"SELECT count(*) FROM marts.{nome}").fetchone()[0]
            if n == 0:
                print(f"ERRO: marts.{nome} voltou com 0 linhas (JOIN que nao casou?)")
                con.execute("ROLLBACK")
                sys.exit(1)
            resultados.append((nome, n))
            total += n
        con.execute("COMMIT")
    except SystemExit:
        raise
    except Exception as e:
        con.execute("ROLLBACK")
        print("ERRO:", e)
        sys.exit(1)

    for nome, n in resultados:
        unidade = "linha" if n == 1 else "linhas"
        print(f"  marts.{nome:<28} {n:>6,} {unidade}".replace(",", "."))
    print(f"  {len(resultados)} marts {' ' * 23} {total:>6,} linhas".replace(",", "."))
    con.close()


if __name__ == "__main__":
    main()
