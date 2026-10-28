# Configuração única do repositório no GitHub

Faça isso **antes da aula**, de preferência no dia anterior. Leva cerca de 15 minutos.

## 1. Criar o repositório e enviar o projeto

1. No GitHub, crie um repositório **vazio** (sem README), por exemplo `mlops-aula08`. Pode ser público ou privado.
2. Na pasta `projeto_ci_cd_ct`:

```bash
git init -b main
git add -A
git commit -m "projeto inicial da aula 08"
git remote add origin https://github.com/SEU_USUARIO/mlops-aula08.git
git push -u origin main
```

3. Abra a aba **Actions**. O CI roda sozinho no primeiro push e deve ficar verde.

> Se o seu Git avisar sobre fim de linha (CRLF), pode ignorar. O arquivo `.gitattributes` do projeto força LF.

## 2. Permissões do Actions (necessárias para o CT abrir o PR de promoção)

Em **Settings > Actions > General**, na seção **Workflow permissions**:

- selecione **Read and write permissions**
- marque **Allow GitHub Actions to create and approve pull requests**

Sem isso o passo "Abrir Pull Request com o novo campeão" falha. Ele está marcado como `continue-on-error`,
então o restante do CT continua válido.

## 3. Proteger a `main` (o momento "o CI vermelho bloqueia o merge")

Em **Settings > Branches > Add branch protection rule** (ou **Rulesets**, conforme a interface do seu GitHub):

- Branch name pattern: `main`
- marque **Require a pull request before merging**
- marque **Require status checks to pass before merging** e adicione os checks que aparecem depois do primeiro CI:
  `Lint e formatação (ruff)`, `Testes (Python 3.11)` e `Testes (Python 3.12)`

Os nomes só aparecem na busca depois que o workflow rodou ao menos uma vez.

> Repositórios privados em plano gratuito podem não oferecer proteção de branch. Nesse caso use um repositório
> público para a aula ou mostre o bloqueio apenas pela marca vermelha no PR.

## 4. Publicação da imagem (CD)

O CD publica em `ghcr.io/SEU_USUARIO/mlops-aula08`. Não precisa de segredo extra, o `GITHUB_TOKEN` basta.

Depois da primeira publicação, para puxar a imagem sem login, abra o pacote em **Packages** e mude a
visibilidade para **Public** (Package settings > Danger Zone > Change visibility).

## 5. Ambiente local do professor

```bash
python -m venv .venv
source .venv/Scripts/activate        # Git Bash no Windows
pip install -e ".[dev,ct]"
python demo/local.py ci              # deve terminar com todos os passos [ok]
```

## 6. Ensaio geral (recomendado)

1. Crie uma branch `ensaio`, aplique `python demo/cenarios.py aplicar 1`, faça commit e push.
2. Abra o PR e confirme que o CI fica vermelho.
3. Apague a branch.

Isso garante que as permissões, a proteção da `main` e os nomes dos checks estão certos antes da turma chegar.

## Problemas conhecidos

| Sintoma | Causa provável | Solução |
|---|---|---|
| O passo "Abrir Pull Request" falha | permissão do Actions | item 2 |
| O PR do campeão não dispara o CI | limitação do `GITHUB_TOKEN` | rodar `python demo/local.py ci` ou usar um token pessoal |
| `dvc repro` falha com "is git-ignored" | `dvc.lock` ou saídas no `.gitignore` | não ignore `dvc.lock` |
| O CD falha em "Publicar a imagem" | permissão de pacotes | confirme `packages: write` no job `publicar` |
| Sem internet na sala | rede | use o plano B: `python demo/local.py ci` e `python demo/local.py ct` |
