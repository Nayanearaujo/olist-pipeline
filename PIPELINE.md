# Pipeline Olist: do CSV ao mart

Pipeline de dados em Python sobre o dataset público da Olist, com DuckDB. Três
etapas, três comandos, sem nenhum passo manual no meio.

## Camadas

| Camada | O que é | Como sai |
|---|---|---|
| `raw` | os CSVs como vieram, tudo texto | `pipeline/ingestao.py` |
| `refined` | dado tipado e sem duplicata | `pipeline/transformacao.py` |
| `marts` | uma tabela por pergunta de negócio | `pipeline/marts.py` + `sql/marts/*.sql` |

## Como rodar

Com [uv](https://docs.astral.sh/uv/) instalado, na raiz do projeto:

```bash
uv run python -m pipeline.ingestao
uv run python -m pipeline.transformacao
uv run python -m pipeline.marts
```

Na primeira execução o uv instala as dependências sozinho (estão em `pyproject.toml`).

### Dashboard e relatório (aula 4)

```bash
uv run streamlit run app.py     # painel interativo em http://localhost:8501
uv run python relatorio.py      # gera relatorio.html, abre sem servidor
```

A tela nunca calcula: todo número sai pronto de um mart. `painel.py` lê os
marts e desenha; `app.py` só arruma na tela; `relatorio.py` congela o mesmo
painel num HTML.

### Testes

```bash
uv run pytest --cov
```

Testes unitários com dado inventado (nunca o banco do projeto), meta de 60% de
cobertura. Ficam em `test/`.

## O que esperar na tela

A ingestão termina em 1.550.922 registros nas nove tabelas. A transformação
termina em 550.759 linhas nas oito tabelas da refined. O `pipeline.marts`
imprime os dez marts:

```
  marts.vendas_mensais             24 linhas
  marts.top_categorias             74 linhas
  marts.entrega_no_prazo            1 linha
  marts.nota_por_categoria         52 linhas
  marts.recompra                    9 linhas
  marts.ticket_medio_por_estado    27 linhas
  marts.mix_pagamento               4 linhas
  marts.nota_por_prazo              2 linhas
  marts.vendedores_pareto       3.053 linhas
  marts.tempo_entrega_por_estado   27 linhas
  marts.kpis                        1 linha
  marts.clientes_por_uf            27 linhas
```

## Estrutura

```
olist-pipeline/
├── pipeline/
│   ├── db.py             conexão com o olist.duckdb e criar_schema
│   ├── ingestao.py       raw: lê os 9 CSVs como texto
│   ├── transformacao.py  refined: tipa e deduplica 8 tabelas
│   └── marts.py          marts: executa cada sql/marts/*.sql
├── sql/marts/
│   ├── 01_vendas_mensais.sql ... 05_recompra.sql   (marts base, aula 3)
│   ├── 06_...sql ... 10_...sql                      (desafio da aula 3)
│   └── 11_kpis.sql, 12_clientes_por_uf.sql          (aula 4)
├── painel.py            leitura dos marts, formato e gráficos (sem cálculo)
├── app.py               dashboard Streamlit (só arruma na tela)
├── relatorio.py         gera relatorio.html com os mesmos gráficos
├── design/rascunho.md   o desenho da tela antes do código
├── test/                testes unitários com pytest (dado inventado)
├── raw/                 os 9 CSVs comprimidos
└── pyproject.toml
```

A geolocalização não entra no pipeline (nenhum mart usa). A spec dela, do
desafio 2, está em `specs/geolocalizacao.md`.
