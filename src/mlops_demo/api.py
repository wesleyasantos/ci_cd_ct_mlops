"""API de inferência (FastAPI) servindo o modelo campeão.

Local:   uvicorn mlops_demo.api:app --reload
Docker:  docker run -p 8000:8000 mlops-demo
"""

import json
import os
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from mlops_demo import __version__, config

CAMINHO_MODELO = Path(os.environ.get("MODEL_PATH", config.MODELO_CAMPEAO))
CAMINHO_METRICAS = CAMINHO_MODELO.with_name("metrics.json")

app = FastAPI(title="Triagem de tumores (demo CI/CD/CT)", version=__version__)
_modelo = joblib.load(CAMINHO_MODELO)


class Exame(BaseModel):
    """Os 30 atributos do exame, na mesma ordem do treino."""

    atributos: list[float] = Field(min_length=30, max_length=30)


class Predicao(BaseModel):
    classe: str
    probabilidade_maligno: float
    versao_codigo: str


@app.get("/health")
def saude() -> dict:
    metricas = {}
    if CAMINHO_METRICAS.exists():
        metricas = json.loads(CAMINHO_METRICAS.read_text(encoding="utf-8"))
    return {"status": "ok", "versao_codigo": __version__, "metricas_do_campeao": metricas}


@app.post("/predict", response_model=Predicao)
def prever(exame: Exame) -> Predicao:
    entrada = pd.DataFrame([exame.atributos], columns=config.FEATURES)
    previsto = int(_modelo.predict(entrada)[0])
    # a coluna da classe maligna (0) em predict_proba segue a ordem de classes_
    coluna = list(_modelo.classes_).index(config.CLASSE_MALIGNA)
    p_maligno = float(_modelo.predict_proba(entrada)[0][coluna])
    return Predicao(
        classe="maligno" if previsto == config.CLASSE_MALIGNA else "benigno",
        probabilidade_maligno=round(p_maligno, 4),
        versao_codigo=__version__,
    )
