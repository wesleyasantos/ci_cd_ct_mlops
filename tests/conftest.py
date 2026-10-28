import joblib
import pandas as pd
import pytest

from mlops_demo import config
from mlops_demo.features import separar_xy
from mlops_demo.train import treinar


@pytest.fixture(scope="session")
def base_treino() -> pd.DataFrame:
    return pd.read_csv(config.BASE_TREINO)


@pytest.fixture(scope="session")
def base_holdout() -> pd.DataFrame:
    return pd.read_csv(config.BASE_HOLDOUT)


@pytest.fixture(scope="session")
def params() -> dict:
    return config.carregar_params()


@pytest.fixture(scope="session")
def campeao():
    return joblib.load(config.MODELO_CAMPEAO)


@pytest.fixture(scope="session")
def modelo_atual(base_treino, params):
    """Modelo treinado AGORA, com o código e o params.yaml deste commit."""
    return treinar(base_treino, params)


@pytest.fixture(scope="session")
def xy_holdout(base_holdout):
    return separar_xy(base_holdout)
