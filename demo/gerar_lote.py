"""Gera um lote novo de exames em data/raw/lotes/ (com ou sem drift).

Exemplos:
    python demo/gerar_lote.py lote_02                      # sem drift
    python demo/gerar_lote.py lote_03 --drift 0.75 --n 120
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mlops_demo.data import gerar_lote  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("nome", help="nome do arquivo, sem extensão")
    ap.add_argument("--n", type=int, default=120, help="quantidade de linhas (padrão: 120)")
    ap.add_argument("--drift", type=float, default=1.0, help="fator de escala (1.0 = sem drift)")
    ap.add_argument("--semente", type=int, default=1)
    args = ap.parse_args()
    print("criado:", gerar_lote(args.nome, args.n, args.drift, args.semente))
