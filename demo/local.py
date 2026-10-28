"""Roda na sua máquina os mesmos passos dos workflows (sem GitHub e sem internet).

Uso (na raiz do projeto, com o ambiente virtual ativo):
    python demo/local.py ci     # o mesmo que .github/workflows/ci.yml
    python demo/local.py ct     # o mesmo que .github/workflows/ct.yml (sem abrir PR)
"""

import subprocess
import sys

PY = sys.executable

PASSOS = {
    "ci": [
        ("Lint (ruff check)", [PY, "-m", "ruff", "check", "."]),
        ("Formatação (ruff format --check)", [PY, "-m", "ruff", "format", "--check", "."]),
        ("Validar os dados brutos", [PY, "-m", "mlops_demo.data", "validar"]),
        ("Testes de código", [PY, "-m", "pytest", "-m", "codigo", "-q"]),
        ("Testes de dados", [PY, "-m", "pytest", "-m", "dados", "-q"]),
        ("Testes de modelo", [PY, "-m", "pytest", "-m", "modelo", "-q"]),
        ("Testes de contrato da API", [PY, "-m", "pytest", "-m", "api", "-q"]),
    ],
    "ct": [
        ("Detectar drift", [PY, "-m", "mlops_demo.monitor"]),
        ("Reproduzir o pipeline (dvc repro)", [PY, "-m", "dvc", "repro"]),
        ("Portão de qualidade", [PY, "-m", "mlops_demo.gate"]),
    ],
}


def executar(nome: str) -> int:
    resultados = []
    for titulo, comando in PASSOS[nome]:
        print(f"\n=== {titulo}")
        codigo = subprocess.run(comando).returncode
        resultados.append((titulo, codigo))
        if codigo != 0:
            print(f"--- FALHOU: {titulo}")
            if nome == "ct":
                break  # no CT, passo que falha interrompe o fluxo
    print("\n=== Resumo")
    for titulo, codigo in resultados:
        print(f"  [{'ok' if codigo == 0 else 'FALHOU'}] {titulo}")
    return 0 if all(c == 0 for _, c in resultados) else 1


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in PASSOS:
        print(__doc__)
        sys.exit(2)
    sys.exit(executar(sys.argv[1]))
