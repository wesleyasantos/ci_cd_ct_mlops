"""Testes de contrato da API: formato de entrada e de saída do /predict."""

import pytest
from fastapi.testclient import TestClient

from mlops_demo import config
from mlops_demo.api import app

pytestmark = pytest.mark.api

cliente = TestClient(app)


def test_health_responde_ok():
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_predict_devolve_o_formato_combinado(base_holdout):
    exame = base_holdout[config.FEATURES].iloc[0].tolist()
    resposta = cliente.post("/predict", json={"atributos": exame})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert set(corpo) == {"classe", "probabilidade_maligno", "versao_codigo"}
    assert corpo["classe"] in {"maligno", "benigno"}
    assert 0.0 <= corpo["probabilidade_maligno"] <= 1.0


def test_predict_rejeita_quantidade_errada_de_atributos():
    resposta = cliente.post("/predict", json={"atributos": [1.0, 2.0]})
    assert resposta.status_code == 422


def test_predict_acerta_um_caso_maligno_e_um_benigno_claros(base_holdout, campeao):
    """Escolhe os casos mais claros (maior confiança do campeão) de cada classe."""
    X = base_holdout[config.FEATURES]
    coluna = list(campeao.classes_).index(config.CLASSE_MALIGNA)
    p_maligno = campeao.predict_proba(X)[:, coluna]
    i_maligno = int(p_maligno.argmax())
    i_benigno = int(p_maligno.argmin())
    for indice, esperado in ((i_maligno, "maligno"), (i_benigno, "benigno")):
        resposta = cliente.post("/predict", json={"atributos": X.iloc[indice].tolist()})
        assert resposta.json()["classe"] == esperado
