# Projeto de demonstração: CI/CD/CT para ML

Projeto completo da **Aula 08** (MLOps, IA 26.2, Prof. Wesley Andrade). Ele é pequeno de propósito, mas usa
ferramentas reais: **GitHub Actions**, **pytest**, **ruff**, **DVC**, **FastAPI**, **Docker** e **GitHub Container Registry**.

O modelo é uma regressão logística que classifica tumores de mama (dataset Breast Cancer do scikit-learn).
A classe de interesse é a **maligna** (rótulo `0`), então medimos **recall** e **precisão** dela.

## O que cada letra faz neste projeto

| Letra | Workflow | Quando dispara | O que faz |
|---|---|---|---|
| **CI** | `.github/workflows/ci.yml` | push na `main` e todo Pull Request | lint, testes de código, dados, modelo e API |
| **CT** | `.github/workflows/ct.yml` | agenda semanal, lote novo de dados, `params.yaml` alterado ou execução manual | detecta drift, retreina com DVC, aplica o portão de qualidade e propõe o novo campeão em um PR |
| **CD** | `.github/workflows/cd.yml` | tag `v*.*.*` | roda o CI, constrói a imagem Docker, faz o teste de fumaça e publica no `ghcr.io` |

## Estrutura

```
projeto_ci_cd_ct/
  .github/workflows/     ci.yml, ct.yml, cd.yml
  src/mlops_demo/        config, data, features, evaluate, train, gate, monitor, api
  tests/                 test_codigo, test_dados, test_modelo, test_api
  data/raw/              base_treino.csv, base_holdout.csv e lotes/ (lotes novos chegam aqui)
  models/champion/       o modelo em produção (versionado no Git)
  params.yaml           hiperparâmetros (mudou aqui? o CI treina de novo e confere os limiares)
  dvc.yaml              pipeline: preparar e treinar
  Dockerfile            imagem da API com o modelo campeão
  demo/                 cenários da aula, gerador de lotes, teste de fumaça e plano B local
  docs/                 SETUP_GITHUB.md e ROTEIRO_DEMO.md
```

## Contrato de qualidade

Definido em `src/mlops_demo/config.py`:

- recall da classe maligna **>= 0,90**
- precisão da classe maligna **>= 0,90** (sem ela, um modelo que chuta tudo como maligno teria recall 1,0)
- o candidato não pode ter recall menor que o do campeão, medido **no mesmo conjunto**

## Como rodar localmente

Pré-requisitos: Python 3.10 ou superior e Git. Docker é opcional.

```bash
python -m venv .venv
# Windows (Git Bash):  source .venv/Scripts/activate
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# Linux e macOS:        source .venv/bin/activate

pip install -e ".[dev,ct]"

python demo/local.py ci      # os mesmos passos do CI
python demo/local.py ct      # os mesmos passos do CT (sem abrir PR)
```

A API local:

```bash
uvicorn mlops_demo.api:app --reload
# em outro terminal
python demo/smoke_test.py http://localhost:8000
```

A imagem Docker:

```bash
docker build -t mlops-demo .
docker run -p 8000:8000 mlops-demo
```

## Comandos úteis

| Comando | Para que serve |
|---|---|
| `python -m mlops_demo.data validar` | valida o esquema e os valores de todos os CSVs de `data/raw/` |
| `python -m mlops_demo.monitor` | compara os lotes novos com a base (teste KS) e diz se o gatilho dispara |
| `dvc repro` | roda `preparar` e `treinar`, refazendo só o que mudou |
| `python -m mlops_demo.gate` | compara candidato e campeão. Sai com código 1 se reprovar |
| `python -m mlops_demo.gate --promover` | copia o candidato para `models/champion/` |
| `python demo/cenarios.py listar` | lista os cenários da aula |
| `python demo/gerar_lote.py lote_02 --drift 0.75` | gera um lote novo de exames |

## Para o professor

Comece por `docs/SETUP_GITHUB.md` (configuração única do repositório) e siga `docs/ROTEIRO_DEMO.md`
(passo a passo da aula, com os comandos e o que a turma deve observar).

## Observações honestas

- Os dados são pequenos e ficam no Git. Em um projeto real, use `dvc add` com um *remote* (S3, GCS, Azure ou outro).
- O modelo é simples de propósito, para o treino levar poucos segundos e a aula não esperar a máquina.
- Pull Requests criados com o `GITHUB_TOKEN` padrão **não disparam outros workflows**. Por isso o PR de promoção do
  campeão não roda o CI sozinho. Em produção, use um *GitHub App* ou um token pessoal para esse passo.
