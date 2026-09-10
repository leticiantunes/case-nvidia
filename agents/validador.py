"""
Evidence Validator Agent.

Confere, sem usar LLM nenhum, se cada evidencia produzida pelo Extractor
realmente existe nos documentos citados. Duas checagens por evidencia:

  1. a url_fonte esta entre os documentos daquela startup?
  2. o trecho citado aparece de fato dentro do texto daquele documento?

A comparacao normaliza caixa, acentuacao e espacos antes de comparar. Sem isso,
uma citacao legitima seria rejeitada por um acento de diferenca, gerando falso
negativo justamente no agente responsavel pela confiabilidade do sistema.

A escolha por verificacao deterministica em vez de "pedir para outro modelo
julgar" e proposital: nao gasta cota de API, e sempre reproduzivel, e nao
corre o risco de um segundo modelo alucinar ao avaliar o primeiro.
"""

import re
import unicodedata
from typing import Dict, Any, List


def normaliza(texto: str) -> str:
    """Deixa o texto comparavel: minusculas, sem acento, espacos colapsados."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.split())


def validar_evidencia(evidencia: Dict[str, Any], docs_da_startup: List[Dict[str, Any]]):
    """Devolve (valida: bool, motivo: str)."""
    url = (evidencia.get("url_fonte") or "").strip()
    trecho = (evidencia.get("trecho") or "").strip()

    if not url:
        return False, "evidencia sem url_fonte"
    if not trecho:
        return False, "evidencia sem trecho citado"

    doc = next((d for d in docs_da_startup if d["url_fonte"].strip() == url), None)
    if doc is None:
        return False, f"url nao pertence aos documentos desta startup: {url}"

    texto_doc = normaliza(doc["conteudo_texto"])

    # Modelos generativos frequentemente citam com reticencias ("...trecho..." ou
    # "inicio ... fim"). A citacao continua verificavel: basta conferir cada
    # fragmento separadamente, que e o que um checador humano faria. Fragmentos
    # muito curtos sao ignorados porque casariam por acaso em qualquer texto.
    fragmentos = [f.strip() for f in re.split(r"\.{3,}|\u2026", trecho)]
    fragmentos = [f for f in fragmentos if len(f) >= 25]

    if not fragmentos:
        return False, "trecho curto demais para ser verificavel"

    faltando = [f for f in fragmentos if normaliza(f) not in texto_doc]
    if not faltando:
        sufixo = (
            " (citacao com reticencias, validada por fragmentos)" if len(fragmentos) > 1 else ""
        )
        return True, "ok" + sufixo
    return (
        False,
        f"trecho nao encontrado no documento citado ({len(faltando)} de {len(fragmentos)} fragmentos)",
    )


def evidence_validator(estado: Dict[str, Any]) -> Dict[str, Any]:
    """No do grafo: valida as evidencias de cada perfil produzido pelo Extractor."""
    perfis_validados = []

    for perfil in estado["perfis"]:
        docs = [d for d in estado["documentos"] if d["startup_id"] == perfil["startup_id"]]
        validadas, rejeitadas = [], []

        for ev in perfil.get("evidencias", []):
            ok, motivo = validar_evidencia(ev, docs)
            if ok:
                validadas.append(ev)
            else:
                rejeitadas.append({**ev, "motivo_rejeicao": motivo})

        total = len(validadas) + len(rejeitadas)
        perfil["evidencias"] = validadas
        perfil["evidencias_rejeitadas"] = rejeitadas
        perfil["taxa_validacao"] = round(len(validadas) / total, 2) if total else 0.0
        perfis_validados.append(perfil)

        print(f"[validator] {perfil['nome']}: {len(validadas)}/{total} evidencias validadas")
        for r in rejeitadas:
            print(f"            rejeitada: {r['motivo_rejeicao']}")

    return {"perfis": perfis_validados}
