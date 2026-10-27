# Spec: transformação de raw.geolocalizacao para refined.geolocalizacao

## Resumo

- Transforma `raw.geolocalizacao` em `refined.geolocalizacao`: tipa e trata, sem mudar o significado do dado.
- O grão é a observação de GPS: uma linha é um ponto coletado, com prefixo de CEP, coordenada, cidade e UF.
- A tabela não tem chave única natural: nenhum candidato de coluna chega ao total de linhas.
- Não há agregação aqui; agregar por CEP, cidade ou estado é trabalho da camada mart.
- Contagens: 1.000.163 linhas de entrada, 738.332 distintas, 261.831 duplicatas removidas.

## Contexto

Estou construindo um pipeline de dados em Python sobre o dataset público da Olist,
o e-commerce brasileiro, com dados de 2016 a 2018. Trabalho com spec-driven
development: esta spec é a fonte da verdade, e o código vem depois dela. Não
acrescente nada que não esteja escrito aqui. Se algo ficar ambíguo, pergunte antes
de escrever qualquer linha de código.

Esta spec transforma uma tabela da camada raw para a camada refined. Refined quer
dizer dado tipado e tratado: tipos de dados corretos, sem duplicata e sem valor
inválido. Refined NÃO agrega, NÃO junta tabela e NÃO calcula métrica. Agregação por
CEP, por cidade ou por estado é trabalho da camada mart, não desta.

Todos os números citados abaixo foram contados por mim, direto na tabela
`raw.geolocalizacao`, usando apenas consultas de leitura. Nada foi gravado, nada em
raw foi alterado.

## Stack

- Python 3.13, dependências com uv
- DuckDB, arquivo olist.duckdb na raiz do projeto
- Sem orquestrador. Script rodado pela linha de comando.

## O que já existe (usar, não reescrever)

`pipeline/db.py` já oferece:

- `conectar()`: abre o olist.duckdb e cria o arquivo se faltar
- `criar_schema(con, nome)`: CREATE SCHEMA IF NOT EXISTS

O schema raw veio da etapa de ingestão: nove tabelas, todas as colunas em VARCHAR,
campo vazio virando NULL.

## Artefato que esta spec descreve

Uma transformação de `raw.geolocalizacao` para `refined.geolocalizacao`. A
geolocalização não entra no pipeline do curso e nenhum mart usa ela, então aqui eu
entrego só a spec. A implementação futura, se acontecer, seria
`pipeline/geolocalizacao.py`.

## 0. O grão: o que uma linha representa

Antes de qualquer decisão, a pergunta que define tudo: o que é uma linha desta tabela?

Uma linha é uma observação de GPS de um ponto, com o prefixo de CEP, a coordenada
(latitude e longitude), a cidade e a UF daquele ponto. Não é um CEP, não é uma
cidade, não é um endereço. É um registro de coleta de um ponto no mapa.

Isso importa porque a tabela não tem chave única natural. Testei cada candidato,
contando os valores distintos e comparando com o total de 1.000.163 linhas:

| Candidato | Valores distintos | É chave? |
|---|---|---|
| cep_prefixo | 19.015 | Não (cada prefixo cobre uma área) |
| coordenada (lat, lng) | 718.463 | Não |
| cep + coordenada | 720.154 | Não |
| cep + cidade + uf | 27.912 | Não |
| linha inteira | 738.332 | Não (sobram 261.831 repetições) |

Nenhum candidato chega perto do total de linhas. Nem a linha inteira é única, porque
a mesma observação completa se repete. Então o grão de trabalho desta transformação
é a linha inteira distinta: cada ponto de GPS único, com o seu prefixo, cidade e UF.
A dedup remove só a repetição exata da linha inteira. Não escolho uma linha por CEP
nem uma por coordenada, porque isso seria agregar, e agregar é camada mart.

## 1. Escopo

Lê de `raw.geolocalizacao` e escreve em `refined.geolocalizacao`. Nunca escreve em
raw. Só essa tabela entra nesta spec. As outras oito tabelas do schema raw ficam de
fora porque já têm as suas próprias specs de transformação. Aqui eu trato a tabela
que ficou pendente, que é a de maior volume do projeto: 1.000.163 linhas, contra
99.441 da segunda maior. É por isso que ela merece uma spec só dela.

## 2. Nomes das colunas

Renomear tudo para português, em snake_case, pelo mapa abaixo. É literal e completo:
nenhuma coluna fica de fora, nenhuma é descartada. O motivo é prático: esse é o
vocabulário que eu vou digitar de cabeça nos JOINs das próximas aulas, então ele
precisa ser previsível.

| Coluna no raw | Coluna no refined |
|---|---|
| geolocation_zip_code_prefix | cep_prefixo |
| geolocation_lat | latitude |
| geolocation_lng | longitude |
| geolocation_city | cidade |
| geolocation_state | uf |

Chamo de cep_prefixo, e não de cep, de propósito: a coluna guarda só os cinco
primeiros dígitos do CEP, não o CEP completo de oito. Conferi e todas as 1.000.163
linhas têm exatamente cinco caracteres, com 19.015 valores distintos. O nome tem
que deixar claro que é prefixo.

## 3. Tipos de dados

| Coluna | Tipo |
|---|---|
| cep_prefixo | continua VARCHAR |
| latitude | vira DOUBLE |
| longitude | vira DOUBLE |
| cidade | continua VARCHAR |
| uf | continua VARCHAR |

cep_prefixo fica como texto porque é um identificador, não um número para fazer
conta. Ninguém soma CEP. Contei 245.733 linhas com zero à esquerda, e o menor valor é
01001. Se eu convertesse para inteiro, esses zeros sumiriam e o prefixo passaria a
mentir, deixando de casar com as outras tabelas.

latitude e longitude viram DOUBLE porque são coordenadas de GPS, do tipo que entra em
cálculo de distância, nunca somadas como dinheiro. DOUBLE é o tipo do número com
vírgula aproximado, certo para medida contínua e para média, errado para dinheiro.
Testei a conversão linha a linha: zero valores não numéricos nas duas colunas, ou
seja, as 1.000.163 convertem sem falha. O texto tem de 3 a 20 casas decimais na
latitude e de 3 a 16 na longitude, variação que é ruído de captura do GPS e não
precisão real de medição, então não faz sentido fixar uma escala exata com DECIMAL.
Registro a alternativa: dá para argumentar DECIMAL(38,20) para preservar o texto
original casa por casa. Escolhi DOUBLE porque o uso futuro é cálculo de distância, e
ali a aproximação binária não muda a resposta.

cidade e uf continuam texto porque são nome e sigla.

A conversão é feita em SQL pelo DuckDB com CAST, disparado pelo Python.

## 4. Conversão que falha

Usar CAST puro, que para tudo e estoura erro na hora se um valor não converter. Nada
de TRY_CAST, que transformaria a falha em NULL silencioso. Converter falha em nulo é
a forma mais calada de perder dado: os nulos que já existem no dado se misturariam
com nulos que eu fabriquei na conversão, e ninguém separaria os dois depois. Se
falhar, a mensagem tem que dizer a tabela, a coluna e o valor problemático, e o
script encerra com sys.exit(1).

Hoje esse caminho não dispara, porque contei zero falhas de conversão em latitude e
longitude. A regra existe para a próxima carga: se amanhã chegar uma coordenada
escrita errada, eu quero o erro na cara, não um nulo inventado escondido no meio de
um milhão de linhas.

## 5. Duplicatas

Chave de deduplicação: a linha inteira, ou seja, as cinco colunas juntas
(cep_prefixo, latitude, longitude, cidade, uf). Quando a linha inteira se repete,
mantenho uma só ocorrência com SELECT DISTINCT e conto quantas joguei fora.

Os números: 1.000.163 linhas no total, 738.332 linhas distintas e 261.831
excedentes a remover (conferência: 738.332 + 261.831 = 1.000.163). Existem 128.174
grupos de linhas repetidas, e o maior deles tem 314 cópias da mesma linha. Isso é
redundância de coleta: o mesmo ponto de GPS registrado várias vezes. Tirar a
repetição exata não perde informação nenhuma.

O que eu não faço, e isto é decisão, não esquecimento: não reduzo por cep_prefixo nem
por par de coordenadas. Como provei na seção do grão, nenhum dos dois é chave. Um
prefixo cobre uma área inteira com vários pontos legítimos, e o mesmo par de
coordenadas aparece ligado a prefixos diferentes. Reduzir por qualquer um deles
jogaria fora ponto de verdade, e além disso seria agregação, que não é trabalho de
refined.

## 6. Nulos

Nenhuma linha é apagada por ter nulo, e nenhum nulo é preenchido.

Motivo: contei zero nulos nas cinco colunas, então hoje não há o que tratar. A regra
está escrita para a próxima carga. Se um dia faltar uma coordenada, preencher com
qualquer coisa, como o centro da cidade ou o ponto vizinho, seria inventar uma
localização que não foi medida. Prefiro deixar nulo e saber que falta, a inventar um
valor que parece certo e não é.

## 7. Anomalias que eu vi, e a decisão fechada sobre cada uma

Estas coisas apareceram na investigação. Não deixo nenhuma em aberto para a IA
decidir: a decisão, nos três casos, é manter o dado como está e registrar que eu vi.
Manter é uma decisão legítima aqui, porque corrigir sem uma referência externa
confiável seria inventar valor, e inventar é pior que manter o fato torto.

Grafia de cidade. São 8.011 nomes distintos de cidade. Caindo para minúsculas e
tirando espaços sobra 8.010, e tirando acento sobra 5.968. Ou seja, a mesma cidade
aparece escrita de jeitos diferentes: "sao paulo" com 135.799 linhas e "são paulo"
com 24.917, "brasilia" com 10.470 e "brasília" com 2.180, "niteroi" e "niterói", e
assim por diante. Tem 73.441 linhas com acento e 1 linha com espaço sobrando no fim
("salvador "). Decisão: mantenho a cidade exatamente como está, sem padronizar
grafia nem tirar acento. Não tenho um cadastro oficial de municípios para dizer qual
é a forma certa, e tirar acento no braço juntaria cidades que talvez não sejam a
mesma. Padronização de cidade, se for preciso, é outra etapa com fonte externa.

Coordenadas fora do Brasil. As faixas globais estão todas certas: zero latitude fora
de [-90, 90] e zero longitude fora de [-180, 180]. Atenção a um ponto que parece
anomalia e não é: latitude positiva, sozinha, não é erro. O norte do Brasil fica
acima da linha do Equador, então Roraima, Amapá e parte do Pará têm latitude
positiva de verdade. Por isso as 1.336 latitudes positivas não são, por si só,
suspeitas. O que de fato não cabe no país são as 3 longitudes positivas, impossíveis
em território brasileiro, e as 31 linhas que caem fora de uma janela aproximada do
Brasil (latitude entre -34 e 6, longitude entre -74 e -28). Um exemplo é o CEP 28155,
em santa maria, RJ, que aparece com coordenada lá na Itália. Decisão: mantenho essas
linhas como estão, sem apagar e sem corrigir. A janela que usei é só triagem, não é
o limite oficial do Brasil, e sem uma malha geográfica de verdade eu não sei qual é
o valor certo. Apagar seria perder dado; corrigir seria chutar.

CEP em mais de uma UF. Oito prefixos de CEP aparecem ligados a duas UFs diferentes.
Em todos os oito o padrão é o mesmo: uma UF com quase todas as linhas e a outra com
uma ou poucas. Por exemplo, o 04011 tem 178 linhas em SP e 1 em AC. Além desses, 550
prefixos têm mais de uma grafia de cidade mesmo depois de normalizar. Decisão:
mantenho tudo como está. Parece erro de digitação da sigla, mas eu não elejo a UF da
maioria de forma automática, porque isso de novo seria decidir sem fonte oficial, e
porque não é papel da refined resolver conflito de cadastro.

## 8. Saída na tela

Uma linha por tabela, com o nome qualificado e o total gravado formatado com ponto
de milhar:

```
refined.geolocalizacao: 1.000.163 -> 738.332 linhas (261.831 duplicatas removidas)
```

A linha de nulos é omitida, porque não há nulos. A saída padrão é reconfigurada para
utf-8, para os acentos dos nomes de cidade saírem certos.

## 9. Reexecução

CREATE OR REPLACE TABLE, nunca append. Rodar dez vezes dá o mesmo resultado que rodar
uma. Conferência: duas execuções seguidas imprimem exatamente as mesmas 738.332
linhas e as mesmas 261.831 duplicatas.

## 10. Erro de pré-requisito

Antes de transformar, verificar se `raw.geolocalizacao` existe. Se não existir, a
mensagem manda rodar "uv run python -m pipeline.ingestao" e o script encerra com
sys.exit(1). É mais honesto do que estourar um erro de tabela inexistente no meio da
conversão.

## Critérios de aceite

- [ ] refined.geolocalizacao criada com 738.332 linhas.
- [ ] 261.831 duplicatas removidas, e 738.332 + 261.831 confere com as 1.000.163 de entrada.
- [ ] DESCRIBE mostra DOUBLE em latitude e longitude, e VARCHAR em cep_prefixo, cidade e uf.
- [ ] cep_prefixo mantém o zero à esquerda, por exemplo 01001, e todas as linhas seguem com cinco dígitos.
- [ ] Zero nulos continuam zero depois da transformação.
- [ ] latitude sempre entre -90 e 90, longitude sempre entre -180 e 180.
- [ ] Nenhuma agregação na saída: a tabela continua no grão de ponto de GPS, não uma linha por CEP nem por cidade.
- [ ] Rodar duas vezes seguidas imprime exatamente a mesma coisa.

## O que eu assumi e não estava na fonte

Lista vazia. Toda decisão desta spec, inclusive a de manter as anomalias, está
escrita com o seu motivo e o seu número. Não deixei nada para a IA decidir sozinha.

---

Repositório: https://github.com/Nayanearaujo/olist-pipeline
