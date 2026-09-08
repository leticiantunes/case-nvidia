"""
Compara a saida do Startup Classifier com a hipotese registrada em
docs/perfil_hipotese.md e calcula a acuracia.

Rodar depois de scripts/rodar_todas.py:
    python scripts/medir_acuracia.py

Importante para o video: o gabarito NAO e verdade absoluta. Ele e uma leitura
humana dos mesmos documentos, feita antes de o classificador existir. Divergencia
nao significa automaticamente que o agente errou; significa que aquele caso merece
ser lido. Alguns dos casos de fronteira foram marcados como discutiveis de proposito.
"""

import os
import re
import json
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
RESULTADO = os.path.join(RAIZ, "data", "resultado_completo.json")
GABARITO = os.path.join(RAIZ, "docs", "perfil_hipotese.md")

CATEGORIAS = ["AI-native", "AI-enabled", "non-AI"]


def ler_gabarito():
    """Le a tabela markdown de docs/perfil_hipotese.md."""
    texto = open(GABARITO, encoding="utf-8").read()
    padrao = re.compile(
        r"^\|\s*(startup-\d+)\s*\|\s*([^|]+?)\s*\|\s*(AI-native|AI-enabled|non-AI)[^|]*\|",
        re.M,
    )
    return {m.group(1): {"nome": m.group(2).strip(), "hipotese": m.group(3)}
            for m in padrao.finditer(texto)}


def main():
    dados = json.load(open(RESULTADO, encoding="utf-8"))
    gabarito = ler_gabarito()

    print(f"gabarito: {len(gabarito)} empresas | resultado: {len(dados['perfis'])} perfis\n")

    acertos, divergencias, sem_gabarito = 0, [], []
    matriz = Counter()
    por_confianca = Counter()

    for perfil in dados["perfis"]:
        sid = perfil.get("startup_id")
        predito = (perfil.get("classificacao") or {}).get("classificacao", "indeterminado")
        confianca = (perfil.get("classificacao") or {}).get("confianca", "?")

        if sid not in gabarito:
            sem_gabarito.append(perfil.get("nome"))
            continue

        esperado = gabarito[sid]["hipotese"]
        matriz[(esperado, predito)] += 1
        bateu = (predito == esperado)
        por_confianca[(confianca, "acerto" if bateu else "erro")] += 1

        if bateu:
            acertos += 1
        else:
            divergencias.append({
                "nome": perfil.get("nome"), "esperado": esperado, "predito": predito,
                "confianca": confianca, "taxa_validacao": perfil.get("taxa_validacao"),
                "justificativa": (perfil.get("classificacao") or {}).get("justificativa", "")[:220],
            })

    total = acertos + len(divergencias)
    print("=" * 70)
    print(f"ACURACIA: {acertos}/{total} = {acertos / total:.0%}" if total else "sem dados")
    print("=" * 70)

    print("\nMATRIZ DE CONFUSAO (linha = gabarito, coluna = classificador)")
    largura = max(len(c) for c in CATEGORIAS) + 2
    print(" " * largura + "".join(c.rjust(largura) for c in CATEGORIAS))
    for esperado in CATEGORIAS:
        linha = esperado.ljust(largura)
        for predito in CATEGORIAS:
            linha += str(matriz[(esperado, predito)]).rjust(largura)
        print(linha)

    print("\nACERTO POR NIVEL DE CONFIANCA DECLARADO")
    for nivel in ["alta", "media", "baixa"]:
        a = por_confianca[(nivel, "acerto")]
        e = por_confianca[(nivel, "erro")]
        if a + e:
            print(f"  {nivel:6s}: {a}/{a + e} = {a / (a + e):.0%}")

    if divergencias:
        print(f"\nDIVERGENCIAS ({len(divergencias)}) - leia cada uma antes de concluir que o agente errou\n")
        for d in divergencias:
            print(f"  {d['nome']}")
            print(f"    gabarito: {d['esperado']}  |  agente: {d['predito']} "
                  f"(confianca {d['confianca']}, validacao {d['taxa_validacao']})")
            print(f"    {d['justificativa']}...\n")

    if sem_gabarito:
        print(f"sem entrada no gabarito: {sem_gabarito}")


if __name__ == "__main__":
    main()
