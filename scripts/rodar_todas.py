"""
Roda a pipeline sobre TODAS as startups da base e salva o resultado em disco.

Diferenca para agents/pipeline.py: nao passa pelo Query Planner. O planner existe
para traduzir uma pergunta em filtros, e aqui o objetivo e o oposto, processar a
base inteira sem filtro nenhum.

Por padrao NAO roda o no de RAG. A medicao de acuracia do classificador nao
precisa dele, e pular economiza 31 chamadas de API e alguns minutos. Use
--com-rag quando quiser o resultado completo para o motor de recomendacao.

    python scripts/rodar_todas.py
    python scripts/rodar_todas.py --com-rag
"""

import os
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import pipeline as P
from agents.validador import evidence_validator

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "resultado_completo.json")


def main():
    com_rag = "--com-rag" in sys.argv
    inicio = time.time()

    estado = {
        "consulta": "todas as startups da base",
        # setor None e palavras vazias fazem o retriever devolver a base inteira
        "filtros": {"setor": None, "palavras_chave": []},
        "startups": [], "documentos": [], "perfis": [], "trechos_nvidia": {},
    }

    print("=== retriever ===")
    estado.update(P.retriever(estado))

    print("\n=== extractor ===")
    estado.update(P.extractor(estado))

    print("\n=== evidence validator ===")
    estado.update(evidence_validator(estado))

    print("\n=== classifier ===")
    estado.update(P.startup_classifier(estado))

    if com_rag:
        print("\n=== nvidia rag ===")
        estado.update(P.nvidia_rag(estado))

        print("\n=== recommendation ===")
        estado.update(P.recommendation_agent(estado))

        print("\n=== briefing ===")
        estado.update(P.briefing_agent(estado))

    saida = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "modelo": os.getenv("LLM_MODEL"),
        "com_rag": com_rag,
        "duracao_segundos": round(time.time() - inicio),
        "perfis": estado["perfis"],
        "trechos_nvidia": estado.get("trechos_nvidia", {}),
        "briefing": estado.get("briefing", ""),
    }

    caminho = os.path.abspath(SAIDA)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    falhas = [p["nome"] for p in estado["perfis"] if p.get("erro_extracao")]
    print(f"\n{len(estado['perfis'])} perfis salvos em {caminho}")
    print(f"duracao: {saida['duracao_segundos']}s")
    print(f"falhas de extracao: {falhas or 'nenhuma'}")


if __name__ == "__main__":
    main()
