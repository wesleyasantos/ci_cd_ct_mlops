"""Treino do candidato: lê data/processed/, treina, avalia e salva o modelo e as métricas.

Uso:
    python -m mlops_demo.train                # treina o CANDIDATO (etapa do pipeline DVC)
    python -m mlops_demo.train --campeao      # treina direto sobre a base e grava o CAMPEÃO
                                              # (uso único, para criar o primeiro campeão)
"""

import json
import sys

import joblib
import pandas as pd

from mlops_demo import config
from mlops_demo.evaluate import avaliar
from mlops_demo.features import construir_pipeline, separar_xy


def treinar(df_treino: pd.DataFrame, params: dict):
    """Treina o pipeline com os hiperparâmetros do params.yaml."""
    X, y = separar_xy(df_treino)
    modelo = construir_pipeline(params)
    modelo.fit(X, y)
    return modelo


def salvar(modelo, metricas: dict, caminho_modelo, caminho_metricas) -> None:
    caminho_modelo.parent.mkdir(parents=True, exist_ok=True)
    caminho_metricas.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, caminho_modelo)
    with open(caminho_metricas, "w", encoding="utf-8") as arquivo:
        json.dump(metricas, arquivo, indent=2, ensure_ascii=False)


def treinar_candidato() -> dict:
    params = config.carregar_params()
    modelo = treinar(pd.read_csv(config.TREINO_PROCESSADO), params)
    metricas = avaliar(modelo, pd.read_csv(config.AVALIACAO_PROCESSADA))
    salvar(modelo, metricas, config.MODELO_CANDIDATO, config.METRICAS_CANDIDATO)
    print("candidato:", json.dumps(metricas, ensure_ascii=False))
    return metricas


def treinar_campeao_inicial() -> dict:
    params = config.carregar_params()
    modelo = treinar(pd.read_csv(config.BASE_TREINO), params)
    metricas = avaliar(modelo, pd.read_csv(config.BASE_HOLDOUT))
    metricas["origem"] = "base_treino.csv"
    salvar(modelo, metricas, config.MODELO_CAMPEAO, config.METRICAS_CAMPEAO)
    print("campeão inicial:", json.dumps(metricas, ensure_ascii=False))
    return metricas


if __name__ == "__main__":
    if "--campeao" in sys.argv:
        treinar_campeao_inicial()
    else:
        treinar_candidato()
