# Roteiro da demonstração guiada (CI, CD e CT ao vivo)

Duração estimada: **80 a 90 minutos**. Pré-requisito: `docs/SETUP_GITHUB.md` concluído.
Projete duas janelas lado a lado: o terminal (ou editor) e a aba **Actions** do repositório.

Regra de condução: **antes de cada cenário, peça uma previsão** à turma ("o que vai falhar e em qual etapa?").
Depois mostre o resultado. A discussão vale mais do que o comando.

## Mapa

| Bloco | Tempo | Cenário | Resultado esperado |
|---|---|---|---|
| 0. Tour do projeto | 10 min | nenhum | a turma entende onde estão código, dados, testes, workflows e modelo |
| 1. CI verde | 8 min | base | todos os jobs passam |
| 2. Bug no pré-processamento | 12 min | 1 | CI vermelho em "Testes de código" |
| 3. Dados corrompidos | 8 min | 2 | CI vermelho em "Testes de dados" |
| 4. Hiperparâmetro ruim | 8 min | 3 | CI vermelho em "Testes de modelo" |
| 5. Lote com drift (CT) | 20 min | 4 | CI verde, CT dispara e propõe o novo campeão |
| 6. Portão reprova | 8 min | 5 | CI e portão do CT reprovam |
| 7. CD: tag e imagem | 12 min | tag `v1.0.0` | imagem publicada e API respondendo |
| 8. Fechamento | 5 min | nenhum | métricas DORA e discussão |

Se o tempo apertar, **corte os blocos 3 e 4**. Eles repetem a mesma ideia do bloco 2 com outra camada de teste.

---

## Bloco 0. Tour do projeto (10 min)

Abra o repositório e mostre, nesta ordem:

1. `src/mlops_demo/config.py`: os **limiares** (recall e precisão mínimos de 0,90). É o contrato do modelo.
2. `tests/`: quatro arquivos, quatro camadas (código, dados, modelo, API). Abra `test_modelo.py` e leia o nome de dois testes.
3. `.github/workflows/ci.yml`: gatilhos (`on:`), jobs e steps. Aponte que cada tipo de teste é um **step separado**, para ficar visível no log.
4. `models/champion/`: o modelo em produção está **versionado no Git**.
5. `dvc.yaml` e `params.yaml`: o pipeline da Aula 05 e os hiperparâmetros.

Pergunta de abertura: *"Se alguém mexer em um destes arquivos, o que deveria ser testado automaticamente?"*

Plano B local (sem internet): em qualquer bloco use `python demo/local.py ci` no lugar da aba Actions.
Ative o ambiente virtual antes (o `dvc repro` usa o `python` do PATH e falha se o pacote não estiver instalado nele).

---

## Bloco 1. CI verde (8 min)

Mostre o último workflow na `main` (aba **Actions**). Abra o job **Testes (Python 3.11)** e expanda os steps.

Pontos a destacar:
- a matriz roda **3.11 e 3.12 em paralelo**
- o step "Testes de modelo" **treina um modelo** com o código e o `params.yaml` deste commit
- o tempo total fica abaixo de 2 minutos (CI rápido é parte da prática, Fowler)

Pergunta: *"Por que o CI treina um modelo, se já existe um modelo versionado em `models/champion/`?"*
Resposta esperada: o modelo versionado prova o passado, o treino prova que o **código e os hiperparâmetros atuais** ainda geram um modelo aceitável.

---

## Bloco 2. Cenário 1: bug no pré-processamento (12 min)

Situação contada à turma: *"Alguém achou que a última coluna era inútil e a removeu."*

```bash
git switch -c cenario-1-bug
python demo/cenarios.py aplicar 1
git diff
git add -A
git commit -m "limpa coluna que parecia inutil"
git push -u origin cenario-1-bug
```

Abra o Pull Request. Peça a previsão e depois mostre o resultado:

- falha em **Testes de código**: `assert (300, 29) == (300, 30)`
- falha também em um teste de modelo, com `ValueError: The feature names should match those that were passed during fit`
- o botão de merge fica **bloqueado** (se a proteção da `main` estiver ativa)

Discussão:
- Sem CI, quando esse bug apareceria? (provavelmente em produção, quando a API recebesse 30 atributos)
- O que o log mostra que o código sozinho não mostra?

Para recuperar: feche o PR e volte para a main.

```bash
git switch main
git branch -D cenario-1-bug
```

---

## Bloco 3. Cenário 2: dados corrompidos (8 min)

Situação: *"O exportador do laboratório passou a gerar nulos e áreas negativas."*

```bash
git switch -c cenario-2-dados
python demo/cenarios.py aplicar 2
git add -A && git commit -m "atualiza base de treino" && git push -u origin cenario-2-dados
```

Resultado esperado:
- o step **Validar os dados brutos** já falha: `base_treino.csv: ['5 valores nulos', "valores negativos em ['mean area']"]`
- o teste de dados falha pela mesma razão
- vários testes de modelo falham com `ValueError: Input X contains NaN`

Ponto central: **a falha de dados foi pega antes do treino**. É mais barato e mais claro do que descobrir por uma métrica ruim.

```bash
git switch main && git branch -D cenario-2-dados
```

---

## Bloco 4. Cenário 3: hiperparâmetro ruim (8 min)

Situação: *"Alguém testou um valor de regularização muito forte e esqueceu na configuração."*

```bash
git switch -c cenario-3-hiperparametro
python demo/cenarios.py aplicar 3
git diff
git add -A && git commit -m "ajusta regularizacao" && git push -u origin cenario-3-hiperparametro
```

Resultado esperado: o **único** step vermelho é "Testes de modelo", com
`assert 0.8648 >= 0.9` (recall maligno abaixo do mínimo). O código não mudou, só o `params.yaml`.

Discussão: *"Um teste de código comum detectaria isso?"* Não. Esse é o tipo de teste que só existe em ML.

```bash
git switch main && git branch -D cenario-3-hiperparametro
```

---

## Bloco 5. Cenário 4: lote com drift e o CT (20 min)

Situação: *"O hospital trocou o equipamento de imagem. Os tumores parecem 25% menores nos exames."*

```bash
git switch -c cenario-4-drift
python demo/cenarios.py aplicar 4
python -m mlops_demo.monitor
```

Mostre a saída do `monitor` antes de subir: **9 de 30 atributos com drift**, gatilho **DISPARADO**.

```bash
git add -A && git commit -m "adiciona lote_01 do novo equipamento" && git push -u origin cenario-4-drift
```

Abra o PR e mostre **dois workflows** disparados:

1. **CI**: verde. Os dados são válidos (esquema correto, sem nulos). Drift não é erro de dados.
2. **CT**: roda `monitor`, `dvc repro` e o portão. Abra o **Summary** do run e mostre a tabela.

Valores de referência no resumo do portão (160 amostras de avaliação):

| | Recall maligno | Precisão maligna |
|---|---|---|
| Campeão | 0,895 | 0,962 |
| Candidato | 0,965 | 0,932 |

Peça à turma para interpretar:
- O campeão caiu **abaixo do contrato** (0,90). O drift degradou o modelo em produção.
- O candidato recuperou o recall e manteve a precisão acima de 0,90.
- Por que comparamos os dois **no mesmo conjunto**? (justiça da comparação, e o campeão nunca viu esse conjunto)

Faça o merge do PR. Na `main`, o CT roda de novo e **abre um PR** chamado "ct: novo modelo campeão aprovado no portão de qualidade".

Pontos a destacar no PR de promoção:
- só `models/champion/` muda
- o corpo do PR traz a tabela do portão
- **uma pessoa revisa e aprova a promoção**: o CT propõe e o humano decide

> Atenção: PRs criados pelo `GITHUB_TOKEN` não disparam o CI. Diga isso à turma, é uma pegadinha real. Rode
> `python demo/local.py ci` na branch do PR para mostrar que o CI passaria com o novo campeão.

Merge do PR de promoção, e volte à `main`:

```bash
git switch main && git pull
```

---

## Bloco 6. Cenário 5: o portão reprova (8 min)

Situação: *"Alguém quis garantir que nenhum câncer escapasse e deu peso 50 para a classe maligna."*

```bash
git switch -c cenario-5-portao
python demo/cenarios.py aplicar 5
python demo/local.py ct
```

O `local.py ct` mostra o portão reprovando: recall **1,000** e precisão **0,860** (abaixo de 0,90). Suba a branch e mostre também o CI vermelho.

Ponto central (liga com a Aula 07): **recall sozinho é enganável**. Sem a trava de precisão, esse modelo seria promovido por ter o maior recall possível, mas mandaria muitas pacientes saudáveis para exames desnecessários.

```bash
git switch main && git branch -D cenario-5-portao
```

---

## Bloco 7. CD: tag e imagem (12 min)

```bash
git tag v1.0.0
git push origin v1.0.0
```

Aba **Actions**, workflow **CD**. Mostre a sequência:

1. job `ci` (workflow reutilizado) roda primeiro
2. `publicar` só começa se o CI passou (`needs: ci`)
3. build da imagem, **teste de fumaça** no container (`/health` e `/predict`) e só então o push para o `ghcr.io`

Depois de publicado, rode a imagem direto do registro:

```bash
docker run -p 8000:8000 ghcr.io/SEU_USUARIO/NOME_DO_REPOSITORIO:1.0.0
python demo/smoke_test.py http://localhost:8000
```

Discussão: *"Por que testar o container antes de publicar?"* (uma imagem que não sobe é pior do que nenhuma imagem)
Sugestão para a turma: em produção, o job de publicação poderia usar um **environment** com aprovação manual obrigatória.

---

## Bloco 8. Fechamento (5 min)

Ligue o que foi visto às quatro métricas do relatório **DORA** (Forsgren, Humble e Kim, 2018):
frequência de deploy, tempo de entrega de mudanças, taxa de falha de mudanças e tempo de recuperação.

Perguntas de fechamento:
- Qual cenário seria mais caro descobrir em produção? Por quê?
- Que teste vocês adicionariam ao projeto do grupo?
- Qual limiar de recall vocês defenderiam para o modelo de câncer de pulmão, e quem aprova a mudança desse limiar?

## Atividade para a turma (opcional, 15 min)

Em duplas, escrevam **um teste novo** em `tests/test_modelo.py` (por exemplo, um teste de invariância ou um teste de
latência de predição) e rodem `python demo/local.py ci`. Quem quiser, abre um PR de verdade.

## Se algo der errado

| Situação | O que fazer |
|---|---|
| GitHub lento ou fora do ar | `python demo/local.py ci` e `python demo/local.py ct` fazem os mesmos passos |
| Workflow não dispara | confira se o push foi para a branch certa e se o Actions está habilitado em Settings |
| Cenário não aplica ("trecho não encontrado") | a mudança já foi aplicada nesta branch. Volte à `main` e crie outra branch |
| PR de promoção não abre | permissão do Actions (item 2 do `SETUP_GITHUB.md`). Mostre o resumo do portão assim mesmo |
| Docker não sobe na sua máquina | mostre o `Dockerfile` e rode a API com `uvicorn mlops_demo.api:app` |
