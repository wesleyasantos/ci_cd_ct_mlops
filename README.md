# Projeto de demonstração: CI/CD/CT para ML

Projeto pequeno, mas completo, que mostra como um modelo de machine learning é testado, retreinado e entregue de forma
automática. Usa ferramentas reais: **GitHub Actions**, **pytest**, **ruff**, **DVC**, **FastAPI**, **Docker** e
**GitHub Container Registry**.

O modelo é uma regressão logística que classifica tumores de mama (dataset Breast Cancer do scikit-learn).
A classe de interesse é a **maligna** (rótulo `0`), então medimos **recall** e **precisão** dela.

## O que cada letra faz neste projeto

| Letra | Workflow | Quando dispara | O que faz |
|---|---|---|---|
| **CI** | `.github/workflows/ci.yml` | push na `main` e todo Pull Request | lint, testes de código, dados, modelo e API |
| **CT** | `.github/workflows/ct.yml` | agenda semanal e execução manual (sempre retreinam); lote novo ou `params.yaml` alterado (retreinam só se houver drift) | detecta drift, retreina com DVC, aplica o portão de qualidade e propõe o novo campeão em um PR |
| **CD** | `.github/workflows/cd.yml` | tag `v*.*.*` | roda o CI, constrói a imagem Docker, faz o teste de fumaça e publica no `ghcr.io` |

## Estrutura

```
projeto_ci_cd_ct/
  .github/workflows/     ci.yml, ct.yml, cd.yml
  src/mlops_demo/        config, data, features, evaluate, train, gate, monitor, api
  tests/                 test_codigo, test_dados, test_modelo, test_api
  data/raw/              base_treino.csv, base_holdout.csv e lotes/ (lotes novos chegam aqui)
  models/champion/       o modelo em produção (versionado no Git)
  params.yaml            hiperparâmetros (mudou aqui? o CI treina de novo e confere os limiares)
  dvc.yaml               pipeline: preparar e treinar
  Dockerfile             imagem da API com o modelo campeão
  demo/                  cenários de prática, gerador de lotes, teste de fumaça e execução local
```

## Contrato de qualidade

Definido em `src/mlops_demo/config.py`:

- recall da classe maligna **>= 0,90**
- precisão da classe maligna **>= 0,90** (sem ela, um modelo que chuta tudo como maligno teria recall 1,0)
- o candidato não pode ter recall menor que o do campeão, medido **no mesmo conjunto**

---

# Passo a passo

São três partes. A **Parte 1** roda tudo na sua máquina. A **Parte 2** leva o projeto para o seu GitHub. A **Parte 3**
é a prática com cinco cenários.

## Parte 1. Rodar na sua máquina (sem GitHub)

Pré-requisitos: Python 3.10 ou superior e Git. Docker é opcional.

**1. Crie e ative o ambiente virtual.**

```bash
python -m venv .venv
source .venv/Scripts/activate        # Git Bash no Windows
# PowerShell:  .venv\Scripts\Activate.ps1
# Linux e macOS: source .venv/bin/activate
```

**2. Instale o projeto.**

```bash
pip install -e ".[dev,ct]"
```

**3. Rode o CI inteiro.** Deve terminar com todos os passos `[ok]`.

```bash
python demo/local.py ci
```

**4. Rode o CT inteiro** (drift, retreino com DVC e portão de qualidade, sem abrir PR).

```bash
python demo/local.py ct
```

**5. Suba a API e teste.**

```bash
uvicorn mlops_demo.api:app --reload
# em outro terminal, com o ambiente ativo:
python demo/smoke_test.py http://localhost:8000
```

**6. (Opcional) Construa a imagem Docker.**

```bash
docker build -t mlops-demo .
docker run -p 8000:8000 mlops-demo
```

> O `dvc repro` usa o `python` do PATH. Se o ambiente virtual não estiver ativo, ele falha com
> `No module named 'mlops_demo'`.

## Parte 2. Colocar o projeto no seu GitHub

**1. Crie o repositório.** No GitHub, crie um repositório **público** e **vazio** (sem README). Repositório público
tem Actions gratuito.

**2. Configure o Git somente nesta pasta** (sem `--global`) e envie o projeto.

```bash
git init -b main
git config --local user.name  "Seu Nome"
git config --local user.email "seu-email@exemplo.com"
git config --local core.autocrlf false
git add -A
git commit -m "projeto inicial"
git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git
git push -u origin main
```

**3. Confirme o primeiro CI.** Abra a aba **Actions**. O CI roda sozinho e deve ficar verde nos três jobs
(`Lint e formatação (ruff)`, `Testes (Python 3.11)` e `Testes (Python 3.12)`).

**4. Libere o CT para abrir Pull Requests.** Em **Settings > Actions > General > Workflow permissions**:

- selecione **Read and write permissions**
- marque **Allow GitHub Actions to create and approve pull requests**
- clique em **Save**

Sem isso o CT cria a branch `ct/novo-campeao`, mas não abre o PR, e o resumo do run avisa o motivo.

**5. (Opcional) Proteja a `main`.** Em **Settings > Branches** (ou **Rulesets**), crie uma regra para `main`:

- marque **Require a pull request before merging**
- marque **Require status checks to pass before merging** e adicione os três checks do item 3
  (eles só aparecem na busca depois do primeiro CI)

Com a regra ativa, um CI vermelho bloqueia o merge.

## Parte 3. Prática com cinco cenários

Cada cenário muda uma coisa no projeto. **Antes de rodar, tente prever** o que vai falhar e em qual etapa.

O roteiro é o mesmo para todos. Troque `N` pelo número do cenário.

```bash
git switch main && git pull
git switch -c cenario-N
python demo/cenarios.py aplicar N
git add -A
git commit -m "cenario N"
git push -u origin cenario-N
```

Abra o Pull Request no GitHub e acompanhe a aba **Checks**. Ao terminar, feche o PR **sem fazer merge** e volte:

```bash
git switch main
git branch -D cenario-N
```

| N | O que muda | O que você deve observar |
|---|---|---|
| 1 | remove a última coluna das entradas do modelo | CI vermelho em **Testes de código** |
| 2 | nulos e áreas negativas na base de treino | CI vermelho em **Validar os dados brutos** (antes do treino) |
| 3 | regularização muito forte (`C: 0.00005`) | CI vermelho em **Testes de modelo**: recall abaixo de 0,90 |
| 4 | lote novo com drift (tamanhos 25% menores) | CI verde. Veja o CT na seção seguinte |
| 5 | `class_weight` extremo na classe maligna | CI vermelho: recall 1,0, mas precisão abaixo de 0,90 |

Para listar os cenários: `python demo/cenarios.py listar`.

### Cenário 4: o treinamento contínuo

O lote novo mostra que os dados mudaram. Aqui o CI fica verde, porque os dados são válidos. Quem reage é o **CT**.

1. No PR do cenário 4, abra o workflow **CT** e o **Summary** do run. Veja o relatório de drift e a tabela do portão
   (campeão x candidato).
2. Faça o merge desse PR na `main`. O CT roda de novo e, se o portão aprovar, abre um PR chamado
   **"ct: novo modelo campeão aprovado no portão de qualidade"**.
3. O CI desse PR aparece como **Action required**, porque o PR foi aberto pelo `GITHUB_TOKEN`. Abra o PR e clique em
   **Approve and run workflows**.
4. Revise o PR (só `models/champion/` muda) e faça o merge. O CT propõe, uma pessoa decide.

### Entrega (CD): tag e imagem

Com a `main` verde, crie uma tag de versão:

```bash
git switch main && git pull
git tag v1.0.0
git push origin v1.0.0
```

O workflow **CD** roda o CI, constrói a imagem, faz o teste de fumaça e só então publica no `ghcr.io`. Depois, em
**Packages**, abra o pacote e mude a visibilidade para **Public** (Package settings > Change visibility). Então:

```bash
docker run -p 8000:8000 ghcr.io/SEU_USUARIO/NOME_DO_REPOSITORIO:1.0.0
python demo/smoke_test.py http://localhost:8000
```

## Comandos úteis

| Comando | Para que serve |
|---|---|
| `python -m mlops_demo.data validar` | valida o esquema e os valores de todos os CSVs de `data/raw/` |
| `python -m mlops_demo.monitor` | compara os lotes novos com a base (teste KS) e diz se o gatilho dispara |
| `dvc repro` | roda `preparar` e `treinar`, refazendo só o que mudou |
| `python -m mlops_demo.gate` | compara candidato e campeão. Sai com código 1 se reprovar |
| `python -m mlops_demo.gate --promover` | copia o candidato para `models/champion/` |
| `python demo/cenarios.py listar` | lista os cenários de prática |
| `python demo/gerar_lote.py lote_02 --drift 0.75` | gera um lote novo de exames |

## Se algo der errado

| Sintoma | Causa provável | Solução |
|---|---|---|
| Jobs falham em 2 segundos, sem passos | conta do GitHub com problema de cobrança | corrija em Settings > Billing e reexecute |
| CT passa, mas não há PR | permissão do passo 4 da Parte 2 desligada | ligue a permissão e rode o CT de novo (Actions > CT > Run workflow) |
| CI do PR do campeão em "Action required" | PR aberto pelo `GITHUB_TOKEN` | clique em **Approve and run workflows** |
| `dvc repro` falha com "No module named" | ambiente virtual inativo | ative o ambiente e rode de novo |
| `dvc repro` falha com "is git-ignored" | `dvc.lock` no `.gitignore` | não ignore o `dvc.lock` |
| Cenário não aplica ("trecho não encontrado") | a mudança já foi aplicada nesta branch | volte à `main` e crie outra branch |
| Sem internet | rede | use `python demo/local.py ci` e `python demo/local.py ct` |

## Observações

- Os dados são pequenos e ficam no Git. Em um projeto real, use `dvc add` com um *remote* (S3, GCS, Azure ou outro).
- O modelo é simples de propósito, para o treino levar poucos segundos.
- O `GITHUB_TOKEN` padrão é suficiente aqui. Em produção, o PR de promoção costuma usar um *GitHub App* ou um token
  dedicado, para o CI rodar sozinho nele.
