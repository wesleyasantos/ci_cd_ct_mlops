"""Configuração central do projeto: caminhos, nomes de colunas e limiares de qualidade."""

from pathlib import Path

import yaml
from sklearn.datasets import load_breast_cancer

RAIZ = Path(__file__).resolve().parents[2]

# dados
DADOS_BRUTOS = RAIZ / "data" / "raw"
DADOS_LOTES = DADOS_BRUTOS / "lotes"
DADOS_PROCESSADOS = RAIZ / "data" / "processed"
BASE_TREINO = DADOS_BRUTOS / "base_treino.csv"
BASE_HOLDOUT = DADOS_BRUTOS / "base_holdout.csv"
TREINO_PROCESSADO = DADOS_PROCESSADOS / "treino.csv"
AVALIACAO_PROCESSADA = DADOS_PROCESSADOS / "avaliacao.csv"

# modelos e relatórios
MODELO_CAMPEAO = RAIZ / "models" / "champion" / "model.joblib"
METRICAS_CAMPEAO = RAIZ / "models" / "champion" / "metrics.json"
MODELO_CANDIDATO = RAIZ / "models" / "candidate" / "model.joblib"
METRICAS_CANDIDATO = RAIZ / "reports" / "candidate_metrics.json"
RELATORIO_GATE = RAIZ / "reports" / "gate.json"
RESUMO_GATE = RAIZ / "reports" / "gate.md"
RELATORIO_DRIFT = RAIZ / "reports" / "drift.md"
PARAMS = RAIZ / "params.yaml"

# esquema dos dados
FEATURES = [str(nome) for nome in load_breast_cancer().feature_names]  # str puro, não numpy.str_
ALVO = "target"
# ATENÇÃO: no Breast Cancer do scikit-learn, 0 = MALIGNO e 1 = BENIGNO.
CLASSE_MALIGNA = 0
COLUNAS_TAMANHO = [c for c in FEATURES if any(p in c for p in ("radius", "perimeter", "area"))]

# limiares de qualidade (o "contrato" do modelo). Mudar aqui exige revisão em PR.
RECALL_MINIMO = 0.90
PRECISAO_MINIMA = 0.90
TOLERANCIA_CAMPEAO = 0.0  # o candidato não pode ter recall menor que o campeão
LIMITE_DRIFT_P = 0.01  # p-valor do teste KS
MIN_FEATURES_DRIFT = 3  # gatilho do CT: quantos atributos com drift disparam o retreino


def carregar_params() -> dict:
    """Lê o params.yaml (hiperparâmetros e semente)."""
    with open(PARAMS, encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)
