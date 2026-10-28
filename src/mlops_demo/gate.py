"""Portão de qualidade (quality gate): decide se o candidato pode substituir o campeão.

Uso:
    python -m mlops_demo.gate              # avalia candidato x campeão e escreve reports/gate.*
    python -m mlops_demo.gate --promover   # copia o candidato para models/champion/

Código de saída: 0 = aprovado, 1 = reprovado (o workflow do GitHub Actions fica vermelho).
"""

import json
import shutil
import sys

import joblib
import pandas as pd

from mlops_demo import config
from mlops_demo.evaluate import avaliar


def decidir(candidato: dict, campeao: dict) -> dict:
    """Aplica as regras do portão a duas dicts de métricas e devolve o veredito."""
    verificacoes = [
        {
            "regra": f"recall maligno do candidato >= {config.RECALL_MINIMO:.2f}",
            "ok": candidato["recall_maligno"] >= config.RECALL_MINIMO,
            "valor": round(candidato["recall_maligno"], 4),
        },
        {
            "regra": f"precisão maligna do candidato >= {config.PRECISAO_MINIMA:.2f}",
            "ok": candidato["precisao_maligna"] >= config.PRECISAO_MINIMA,
            "valor": round(candidato["precisao_maligna"], 4),
        },
        {
            "regra": "recall maligno do candidato >= recall do campeão (mesmo conjunto)",
            "ok": candidato["recall_maligno"]
            >= campeao["recall_maligno"] - config.TOLERANCIA_CAMPEAO,
            "valor": f"{candidato['recall_maligno']:.4f} x {campeao['recall_maligno']:.4f}",
        },
    ]
    return {
        "aprovado": all(v["ok"] for v in verificacoes),
        "verificacoes": verificacoes,
        "candidato": candidato,
        "campeao": campeao,
    }


def resumo_markdown(resultado: dict) -> str:
    """Texto em Markdown, usado no GITHUB_STEP_SUMMARY e no corpo do PR."""
    selo = "APROVADO: o candidato pode virar campeão" if resultado["aprovado"] else "REPROVADO"
    linhas = [f"## Portão de qualidade: {selo}", ""]
    linhas += ["| Modelo | Recall maligno | Precisão maligna | Amostras |", "|---|---|---|---|"]
    for nome in ("campeao", "candidato"):
        m = resultado[nome]
        celulas = [nome, f"{m['recall_maligno']:.3f}", f"{m['precisao_maligna']:.3f}"]
        linhas.append("| " + " | ".join([*celulas, str(m["n_amostras"])]) + " |")
    linhas += ["", "| Regra | Resultado | Valor |", "|---|---|---|"]
    for v in resultado["verificacoes"]:
        linhas.append(f"| {v['regra']} | {'passou' if v['ok'] else 'FALHOU'} | {v['valor']} |")
    return "\n".join(linhas) + "\n"


def executar() -> int:
    avaliacao = pd.read_csv(config.AVALIACAO_PROCESSADA)
    candidato = avaliar(joblib.load(config.MODELO_CANDIDATO), avaliacao)
    campeao = avaliar(joblib.load(config.MODELO_CAMPEAO), avaliacao)
    resultado = decidir(candidato, campeao)

    config.RELATORIO_GATE.parent.mkdir(parents=True, exist_ok=True)
    with open(config.RELATORIO_GATE, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, indent=2, ensure_ascii=False)
    texto = resumo_markdown(resultado)
    config.RESUMO_GATE.write_text(texto, encoding="utf-8")
    print(texto)
    return 0 if resultado["aprovado"] else 1


def promover() -> None:
    """Candidato vira campeão. Em produção, isso vai para um PR revisado por uma pessoa."""
    with open(config.RELATORIO_GATE, encoding="utf-8") as arquivo:
        resultado = json.load(arquivo)
    if not resultado["aprovado"]:
        raise SystemExit("O candidato foi reprovado no portão: promoção bloqueada.")
    config.MODELO_CAMPEAO.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config.MODELO_CANDIDATO, config.MODELO_CAMPEAO)
    metricas = dict(resultado["candidato"], origem="treinamento contínuo (CT)")
    with open(config.METRICAS_CAMPEAO, "w", encoding="utf-8") as arquivo:
        json.dump(metricas, arquivo, indent=2, ensure_ascii=False)
    print("Campeão atualizado em", config.MODELO_CAMPEAO)


if __name__ == "__main__":
    if "--promover" in sys.argv:
        promover()
    else:
        sys.exit(executar())
