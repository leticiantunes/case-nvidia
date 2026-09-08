"""
Interface web do NVIDIA Startup AI Radar.

Le o resultado ja processado (data/resultado_completo.json) em vez de rodar a
pipeline ao vivo. A razao e pratica e vale ser dita na apresentacao: processar 31
empresas leva ~20 minutos e consome cota de API, entao a interface consome o
artefato salvo. A pipeline e o que produz; a interface e o que apresenta.

Rodar:  python -m streamlit run app/dashboard.py
"""

import os
import json

import pandas as pd
import streamlit as st

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTADO = os.path.join(RAIZ, "data", "resultado_completo.json")

CORES = {"AI-native": "#76b900", "AI-enabled": "#f0a500", "non-AI": "#8c8c8c",
         "indeterminado": "#c94f4f"}

st.set_page_config(page_title="NVIDIA Startup AI Radar", page_icon="🟩", layout="wide")


@st.cache_data
def carregar():
    if not os.path.exists(RESULTADO):
        return None
    with open(RESULTADO, encoding="utf-8") as f:
        return json.load(f)


def selo(classificacao):
    cor = CORES.get(classificacao, "#8c8c8c")
    return (f"<span style='background:{cor};color:#fff;padding:2px 10px;"
            f"border-radius:12px;font-size:0.8em;font-weight:600'>{classificacao}</span>")


dados = carregar()

st.title("NVIDIA Startup AI Radar")
st.caption("Analise de maturidade em IA de startups brasileiras e recomendacao de tecnologias NVIDIA")

if dados is None:
    st.warning(
        "Nenhum resultado encontrado. Rode primeiro:\n\n"
        "`python scripts/rodar_todas.py --com-rag`"
    )
    st.stop()

perfis = dados["perfis"]

# ---------------------------------------------------------------- cabecalho
c1, c2, c3, c4 = st.columns(4)
c1.metric("Empresas analisadas", len(perfis))

contagem = {}
for p in perfis:
    c = (p.get("classificacao") or {}).get("classificacao", "indeterminado")
    contagem[c] = contagem.get(c, 0) + 1
c2.metric("AI-native", contagem.get("AI-native", 0))
c3.metric("AI-enabled", contagem.get("AI-enabled", 0))

taxas = [p.get("taxa_validacao", 0) for p in perfis]
c4.metric("Validacao media das evidencias", f"{sum(taxas) / len(taxas):.0%}" if taxas else "-")

st.caption(
    f"Processado em {dados.get('gerado_em', '?')} | modelo {dados.get('modelo', '?')} | "
    f"duracao {dados.get('duracao_segundos', '?')}s"
)

aba_empresas, aba_briefing, aba_qualidade = st.tabs(
    ["Empresas", "Briefing executivo", "Qualidade da analise"]
)

# ---------------------------------------------------------------- empresas
with aba_empresas:
    esquerda, direita = st.columns([1, 3])

    with esquerda:
        filtro_cls = st.multiselect(
            "Classificacao", sorted(contagem.keys()), default=sorted(contagem.keys())
        )
        so_com_rec = st.checkbox("Somente com recomendacao", value=False)
        busca = st.text_input("Buscar empresa")

    visiveis = []
    for p in perfis:
        cls = (p.get("classificacao") or {}).get("classificacao", "indeterminado")
        recs = (p.get("recomendacoes") or {}).get("recomendacoes", [])
        if cls not in filtro_cls:
            continue
        if so_com_rec and not recs:
            continue
        if busca and busca.lower() not in p.get("nome", "").lower():
            continue
        visiveis.append(p)

    with direita:
        st.write(f"**{len(visiveis)} empresas**")

        for p in visiveis:
            cls = p.get("classificacao") or {}
            recs = (p.get("recomendacoes") or {}).get("recomendacoes", [])
            titulo = f"{p['nome']}  ·  {cls.get('classificacao', '?')}  ·  confianca {cls.get('confianca', '?')}"

            with st.expander(titulo):
                st.markdown(selo(cls.get("classificacao", "?")), unsafe_allow_html=True)
                st.markdown(f"**Justificativa da classificacao**  \n{cls.get('justificativa', '-')}")

                a, b = st.columns(2)
                a.markdown("**Sinais a favor**")
                for s in cls.get("sinais_a_favor", []) or ["-"]:
                    a.markdown(f"- {s}")
                b.markdown("**Sinais contra**")
                for s in cls.get("sinais_contra", []) or ["-"]:
                    b.markdown(f"- {s}")

                st.divider()
                st.markdown(f"**Recomendacoes NVIDIA** ({len(recs)})")
                if not recs:
                    motivo = (p.get("recomendacoes") or {}).get("sem_recomendacao")
                    st.info(motivo or "sem recomendacao")
                for r in recs:
                    st.markdown(
                        f"**{r.get('tecnologia')}**  ·  prioridade {r.get('prioridade')}  ·  "
                        f"complexidade {r.get('complexidade')}"
                    )
                    st.markdown(f"- Tecnica: {r.get('justificativa_tecnica')}")
                    st.markdown(f"- Negocio: {r.get('justificativa_negocio')}")
                    st.markdown(f"- Proxima acao: {r.get('proxima_acao')}")
                    for e in r.get("evidencias", []):
                        st.caption(f"fonte: {e.get('url_fonte')}")

                st.divider()
                st.markdown(
                    f"**Evidencias verificadas** ({len(p.get('evidencias', []))} validadas, "
                    f"{len(p.get('evidencias_rejeitadas', []))} rejeitadas)"
                )
                for e in p.get("evidencias", []):
                    st.markdown(f"- \"{e.get('trecho', '')[:220]}\"")
                    st.caption(e.get("url_fonte", ""))
                for e in p.get("evidencias_rejeitadas", []):
                    st.markdown(f"- ~~{e.get('afirmacao', '')}~~  ({e.get('motivo_rejeicao', '')})")

# ---------------------------------------------------------------- briefing
with aba_briefing:
    briefing = dados.get("briefing", "")
    if briefing:
        st.markdown(briefing)
        st.download_button("Baixar briefing.md", briefing, file_name="briefing.md")
    else:
        st.info("Briefing nao gerado nesta execucao. Rode com --com-rag.")

# ---------------------------------------------------------------- qualidade
with aba_qualidade:
    st.markdown(
        "O sistema nao afirma nada sem evidencia verificada. Cada trecho citado pelo "
        "Extractor e conferido contra o documento original antes de a empresa ser "
        "classificada. Esta aba mostra o resultado dessa verificacao."
    )

    linhas = []
    for p in perfis:
        cls = p.get("classificacao") or {}
        linhas.append({
            "empresa": p.get("nome"),
            "classificacao": cls.get("classificacao"),
            "confianca": cls.get("confianca"),
            "evidencias_validadas": len(p.get("evidencias", [])),
            "evidencias_rejeitadas": len(p.get("evidencias_rejeitadas", [])),
            "taxa_validacao": p.get("taxa_validacao", 0),
            "recomendacoes": len((p.get("recomendacoes") or {}).get("recomendacoes", [])),
        })
    tabela = pd.DataFrame(linhas).sort_values("taxa_validacao")

    st.dataframe(tabela, use_container_width=True, hide_index=True)

    baixas = tabela[tabela["taxa_validacao"] < 0.5]
    if len(baixas):
        st.warning(
            f"{len(baixas)} empresa(s) com menos de 50% das evidencias verificadas. "
            "Sobre elas o sistema tem menos certeza, e isso aparece no briefing como ressalva."
        )
