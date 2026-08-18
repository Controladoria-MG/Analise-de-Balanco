"""Orquestrador do pipeline completo — roda os dois robôs, junta as bases
com `resumo.py` e gera os JSONs que o portal lê via `fetch`.

Equivalente ao `executar()` único do Radar Fiscal, mas aqui os dois robôs
são tecnologias diferentes (pywinauto para o MGApps, selenium para a
Intranet) e cada um já expõe seu próprio `executar(log=None) -> Path`.
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

import radar_fechamento
import resumo
import retorno_checklist

RAIZ = Path(__file__).parent.parent
PASTA_DESTINO = RAIZ / "data" / "analise_balanco"
ARQUIVO_RESUMO = PASTA_DESTINO / "resumo.xlsx"
ARQUIVO_STATUS = PASTA_DESTINO / "status.json"
ARQUIVO_DADOS_PORTAL = PASTA_DESTINO / "analise_balanco_dados.json"

# Subconjunto de colunas que o portal de fato usa hoje (KPIs, busca e
# tabela) — ver static/script.js. Mais colunas do resumo (Grupo, Gerente,
# Unidade, Segmento, Tributacao) existem e podem entrar aqui quando o
# portal ganhar cards/filtros por essas dimensões.
COLUNAS_PORTAL = ["Cliente", "Documentação"]


def _log(msg, log=None):
    if log:
        log(msg)


def _gerar_json_portal(df: pd.DataFrame) -> None:
    """Gera um JSON enxuto (subconjunto de colunas) para o portal web ler via
    fetch — o portal não faz parsing de .xlsx no navegador."""
    subset = df[COLUNAS_PORTAL].copy()
    registros = subset.to_dict(orient="records")
    # pandas usa NaN para valores ausentes mesmo em colunas de texto — NaN não
    # é JSON válido (JS trava no fetch), então troca por None (vira null) aqui.
    registros = [
        {chave: (None if isinstance(valor, float) and pd.isna(valor) else valor) for chave, valor in reg.items()}
        for reg in registros
    ]
    ARQUIVO_DADOS_PORTAL.write_text(
        json.dumps(registros, ensure_ascii=False, indent=None),
        encoding="utf-8",
    )


def executar(log=None) -> pd.DataFrame:
    arquivo_radar = radar_fechamento.executar(log)
    arquivo_checklist = retorno_checklist.executar(log)

    df = resumo.gerar_resumo(arquivo_radar, arquivo_checklist, ARQUIVO_RESUMO)
    _log(f"Resumo: {len(df)} empresas.", log)

    _gerar_json_portal(df)

    ARQUIVO_STATUS.write_text(
        json.dumps(
            {
                "ultima_execucao": datetime.now().isoformat(timespec="seconds"),
                "registros": len(df),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _log(f"Portal atualizado: {ARQUIVO_DADOS_PORTAL} + {ARQUIVO_STATUS}", log)
    return df


if __name__ == "__main__":
    executar(log=print)
