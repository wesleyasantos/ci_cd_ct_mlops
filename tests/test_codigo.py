"""Testes de código: funções e pipeline se comportam como o contrato diz."""

import pandas as pd
import pytest
from sklearn.pipeline import Pipeline

from mlops_demo import config
from mlops_demo.evaluate import calcular_metricas
from mlops_demo.features import construir_pipeline, separar_xy
from mlops_demo.gate import decidir

pytestmark = pytest.mark.codigo


def test_separar_xy_devolve_30_atributos_e_alvo(base_treino):
    X, y = separar_xy(base_treino)
    assert X.shape == (len(base_treino), 30)
    assert len(y) == len(base_treino)


def test_separar_xy_impoe_a_ordem_das_colunas(base_treino):
    embaralhado = base_treino[list(reversed(base_treino.columns))]
    X, _ = separar_xy(embaralhado)
    assert list(X.columns) == config.FEATURES


def test_separar_xy_falha_quando_falta_coluna(base_treino):
    sem_coluna = base_treino.drop(columns=["mean radius"])
    with pytest.raises(ValueError, match="Colunas ausentes"):
        separar_xy(sem_coluna)


def test_separar_xy_nao_altera_o_dataframe_original(base_treino):
    antes = base_treino.copy()
    separar_xy(base_treino)
    pd.testing.assert_frame_equal(base_treino, antes)


def test_pipeline_tem_padronizacao_e_classificador(params):
    pipeline = construir_pipeline(params)
    assert isinstance(pipeline, Pipeline)
    assert [nome for nome, _ in pipeline.steps] == ["padronizar", "classificador"]


def test_metricas_usam_a_classe_maligna_como_positiva():
    # modelo que chuta tudo como maligno (0): recall 1.0 e precisão = proporção real de malignos
    y_real = [0, 0, 1, 1]
    metricas = calcular_metricas(y_real, [0, 0, 0, 0])
    assert metricas["recall_maligno"] == 1.0
    assert metricas["precisao_maligna"] == pytest.approx(0.5)


# --- o próprio portão de qualidade precisa ser testado ---------------------------------------


def _metricas(recall, precisao):
    return {"recall_maligno": recall, "precisao_maligna": precisao, "n_amostras": 100}


def test_gate_aprova_candidato_melhor_e_dentro_dos_limiares():
    assert decidir(_metricas(0.97, 0.95), _metricas(0.95, 0.95))["aprovado"]


def test_gate_reprova_recall_abaixo_do_limiar():
    assert not decidir(_metricas(0.85, 0.99), _metricas(0.80, 0.99))["aprovado"]


def test_gate_reprova_precisao_abaixo_do_limiar():
    # recall perfeito não compensa uma precisão ruim
    assert not decidir(_metricas(1.0, 0.70), _metricas(0.95, 0.95))["aprovado"]


def test_gate_reprova_candidato_pior_que_o_campeao():
    assert not decidir(_metricas(0.92, 0.95), _metricas(0.97, 0.95))["aprovado"]
