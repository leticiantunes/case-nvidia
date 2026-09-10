"""
Completa o que faltou na ultima execucao, sem refazer o que ja deu certo.

Motivo de existir: a rodada de ontem gastou 15 minutos e so salvou no final.
Quando a cota estourou no meio, o trabalho ja feito ficou preso na memoria do
processo. Este script trabalha em cima do JSON salvo, refaz apenas as empresas
sem recomendacao, e GRAVA A CADA EMPRESA. Se a cota acabar de novo, e so rodar
outra vez mais tarde que ele continua do ponto em que parou.

    python scripts/completar.py
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import pipeline as P

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQUIVO = os.path.join(RAIZ, "data", "resultado_completo.json")


def precisa_recomendacao(perfil):
    recs = perfil.get("recomendacoes")
    if not recs:
        return True
    if recs.get("recomendacoes"):
        return False
    # "sem_recomendacao" por decisao do agente e resultado valido e nao se refaz.
    # So se refaz o que falhou por erro tecnico.
    motivo = (recs.get("sem_recomendacao") or "").lower()
    return motivo.startswith("falha") or "rate limit" in motivo or "retryerror" in motivo


def salvar(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def main():
    dados = json.load(open(ARQUIVO, encoding="utf-8"))
    perfis = dados["perfis"]
    trechos = dados.get("trechos_nvidia", {})

    pendentes = [p for p in perfis if precisa_recomendacao(p)]
    print(f"{len(perfis)} perfis no arquivo | {len(pendentes)} sem recomendacao\n")

    for perfil in pendentes:
        sid = perfil["startup_id"]
        if not trechos.get(sid, {}).get("trechos"):
            print(f"  {perfil['nome']}: sem trechos do RAG, pulando")
            continue

        # roda o no com um perfil de cada vez, para poder gravar a cada empresa
        parcial = P.recommendation_agent(
            {
                "perfis": [perfil],
                "trechos_nvidia": trechos,
            }
        )
        atualizado = parcial["perfis"][0]
        for i, p in enumerate(perfis):
            if p["startup_id"] == sid:
                perfis[i] = atualizado
                break
        salvar(dados)  # <- grava agora, nao no fim

    briefing = dados.get("briefing", "")
    if not briefing or "nao gerado" in briefing.lower() or len(briefing) < 800:
        print("\ngerando briefing...")
        resultado = P.briefing_agent({"perfis": perfis})
        dados["briefing"] = resultado["briefing"]
        salvar(dados)

    com_rec = sum(1 for p in perfis if (p.get("recomendacoes") or {}).get("recomendacoes"))
    print(f"\nresumo: {com_rec}/{len(perfis)} empresas com recomendacao")
    print(f"briefing: {len(dados.get('briefing', ''))} caracteres")
    print("se ainda faltar alguma, rode de novo daqui a uns minutos")


if __name__ == "__main__":
    main()
