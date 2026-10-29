# Pipeline Olist · do CSV ao dashboard

Pipeline de dados de ponta a ponta sobre as vendas reais do e-commerce
brasileiro **Olist** (2016 a 2018), em **Python + DuckDB**. Parte de nove CSVs
soltos e chega a um dashboard que responde perguntas de negócio, passando por
três camadas: dado bruto, dado confiável e indicadores.

> Projeto do curso **Pipeline Olist**, 4 aulas. Guia do curso:
> [ckoliveiraa.github.io/pipeline-olist](https://ckoliveiraa.github.io/pipeline-olist/).
> Dados públicos da Olist via Kaggle, sob licença CC BY-NC-SA 4.0.

---

## Arquitetura: três camadas

```
raw/ (9 CSVs)  ──ingestao.py──▶  raw.*      espelho fiel do CSV, tudo texto
                                   │
                              transformacao.py
                                   ▼
                                refined.*   tipado, sem duplicata, 1 linha = 1 evento
                                   │
                                marts.py + sql/marts/*.sql
                                   ▼
                                marts.*     uma tabela por pergunta de negócio
                                   │
                              painel.py ──▶ app.py (Streamlit) · relatorio.html
```

| Camada | O que é | Quem constrói |
|---|---|---|
| **raw** | Os 9 CSVs como vieram, todas as colunas `VARCHAR`, nada alterado | `pipeline/ingestao.py` |
| **refined** | Dado tipado (data vira data, dinheiro vira `DECIMAL`), sem duplicata exata, renomeado para português | `pipeline/transformacao.py` |
| **marts** | Uma tabela por pergunta: vendas por mês, nota por categoria, Pareto de vendedores... | `pipeline/marts.py` + `sql/marts/*.sql` |
| **dashboard** | A camada de consumo. A tela nunca calcula: todo número sai pronto de um mart | `painel.py`, `app.py`, `relatorio.py` |

Regra que vale para as três: qualquer etapa pode ser rodada de novo do zero sem
quebrar (idempotente, `CREATE OR REPLACE`).

---

## Como rodar

Pré-requisitos: [uv](https://docs.astral.sh/uv/) e Git.

```bash
# 1. clonar e instalar
git clone https://github.com/Nayanearaujo/olist-pipeline.git
cd olist-pipeline
uv sync

# 2. os dados (9 CSVs) já vêm em raw/. O pipeline, do zero:
uv run python -m pipeline.ingestao        # CSV  -> raw     (1.550.922 registros)
uv run python -m pipeline.transformacao   # raw  -> refined (550.759 linhas)
uv run python -m pipeline.marts           # refined -> marts (12 marts)

# 3. o dashboard
uv run streamlit run app.py               # painel interativo em localhost:8501
uv run python relatorio.py                # gera relatorio.html, abre sem servidor

# 4. os testes
uv run pytest --cov                        # unitários, dado inventado, cobertura >= 60%
```

---

## O que uma linha representa (grão de cada tabela)

O conceito central do projeto: antes de qualquer `JOIN`, o que é uma linha?

| Tabela refined | Uma linha é… | Chave |
|---|---|---|
| `pedidos` | um pedido | `pedido_id` |
| `itens_pedido` | um item de um pedido | `pedido_id, item_seq` |
| `pagamentos` | um pagamento de um pedido | `pedido_id, pagamento_seq` |
| `avaliacoes` | uma avaliação de um pedido | `avaliacao_id, pedido_id` |
| `clientes` | um cliente por pedido (a pessoa é `cliente_unico_id`) | `cliente_id` |
| `produtos` | um produto | `produto_id` |
| `vendedores` | um vendedor | `vendedor_id` |

Quatro definições fechadas, iguais no projeto inteiro: **pedido válido** =
`status NOT IN ('canceled','unavailable')`; **receita** = soma de `preco`, sem
frete; **cliente** = `cliente_unico_id`; **mês** = mês da compra.

---

## Indicadores (camada marts)

12 marts, cada um com o grão declarado na primeira linha do `.sql`.

| Mart | Pergunta | Referência |
|---|---|---|
| `vendas_mensais` | Quanto vendemos por mês? | 24 meses · R$ 13.494.400,74 |
| `top_categorias` | Quais categorias mais vendem? | health_beauty R$ 1.255.695,13 |
| `entrega_no_prazo` | Quanto chegou no prazo? | 93,2% |
| `nota_por_categoria` | Que nota cada categoria recebe? | pior: office_furniture 3,62 |
| `recompra` | Quantos clientes voltaram? | recompra 3,04% |
| `ticket_medio_por_estado` | Ticket médio por UF | PB R$ 216,34 · SP R$ 125,57 |
| `mix_pagamento` | Mix de pagamento | cartão 78,5% do valor |
| `nota_por_prazo` | O atraso derruba a nota? | atrasado 2,27 · no prazo 4,29 |
| `vendedores_pareto` | Concentração de vendedores | 80% em 540 de 3.053 |
| `tempo_entrega_por_estado` | Dias até a entrega por UF | SP 8,7 · RR 29,3 |
| `kpis` | Os 7 cartões do dashboard | ticket R$ 137,42 · nota 4,09 |
| `clientes_por_uf` | Clientes por estado | SP 40.302 · RJ 12.384 |

---

## Estrutura do projeto

```
olist-pipeline/
├── pipeline/
│   ├── db.py                conexão DuckDB + criar_schema
│   ├── ingestao.py          raw: lê os 9 CSVs como texto
│   ├── transformacao.py     refined: tipa e deduplica 8 tabelas
│   └── marts.py             marts: executa cada sql/marts/*.sql
├── sql/marts/               12 arquivos .sql, grão no topo de cada um
├── painel.py                lê os marts, formata e desenha (sem cálculo)
├── app.py                   dashboard Streamlit
├── relatorio.py             gera relatorio.html
├── design/rascunho.md       o desenho da tela antes do código
├── test/                    testes pytest com dado inventado
├── raw/                     os 9 CSVs comprimidos (fonte da verdade)
└── pyproject.toml
```

---

## Decisões de dado e o papel da IA

As decisões de transformação e de grão estão escritas, com o motivo e o número
que as sustenta, nas specs (`specs/geolocalizacao.md`) e nos comentários de cada
`.sql`. A geolocalização fica fora do pipeline de propósito: nenhum mart a usa.

A IA (via MCP, em somente leitura sobre o DuckDB) foi usada em todas as etapas
para escrever o encanamento a partir de uma spec, e conferida contra os números
contados à mão. O erro típico dela em SQL não estoura: acerta a sintaxe e erra o
grão. Por isso cada mart declara o grão, e cada `JOIN` foi conferido contando
linhas antes e depois, que foi como os desvios foram pegos.

---

## Fonte e licença

Dados públicos da Olist Store, via Kaggle:
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
sob [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Veja
[LICENSE](LICENSE). Nunca edite nada em `raw/`: é a fonte da verdade.
