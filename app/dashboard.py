"""Dashboard executivo do Nivra.

O Nivra transforma os resultados da pipeline em uma fila de oportunidades
com contexto, evidências e próximos passos para o time NVIDIA.

Rodar: python -m streamlit run app/dashboard.py
"""

import json
import os
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTADO = os.path.join(RAIZ, "data", "resultado_completo.json")

AZUL_CLARO = "#6CA7F0"
INDIGO = "#6A93C6"
CEU = "#5497E9"
ATENCAO = "#1D5CA9"
ORDEM_CLS = ["AI-native", "AI-enabled", "non-AI", "indeterminado"]
ORDEM_CONF = ["alta", "media", "baixa"]
CORES_CLASSE = {
    "AI-native": CEU,
    "AI-enabled": INDIGO,
    "non-AI": "#A2BFE2",
    "indeterminado": "#90A2B7",
}

st.set_page_config(
    page_title="Nivra", page_icon="✦", layout="wide", initial_sidebar_state="collapsed"
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
      /* :root definitivo fica mais abaixo, no bloco "Tema Nivra": este e o unico
         motivo de nao redeclarar as variaveis aqui tambem. */
      .stApp { background:radial-gradient(circle at 82% -10%,rgba(45,126,255,.24),transparent 31rem),radial-gradient(circle at -8% 32%,rgba(56,189,248,.10),transparent 25rem),var(--page); color:var(--text); }
      html,body,[class*="css"],.stMarkdown,p,span,div,button,input,label { font-family:'Manrope',ui-sans-serif,system-ui,sans-serif; }
      [data-testid*="Icon"],.material-symbols-rounded { font-family:'Material Symbols Rounded' !important; }
      .block-container { max-width:1360px; padding-top:2.25rem; padding-bottom:3rem; }
      #MainMenu,footer,header { visibility:hidden; }
      h1,h2,h3 { letter-spacing:-.04em; color:var(--text); }
      h2 { font-size:1.28rem !important; margin-top:1.8rem !important; }
      h3 { font-size:1rem !important; }
      [data-testid="stMetric"] { background:linear-gradient(145deg,rgba(22,49,80,.88),rgba(12,29,50,.9)); border:1px solid var(--line); border-radius:16px; padding:1rem 1.15rem; min-height:116px; box-shadow:0 12px 24px rgba(0,0,0,.12); }
      [data-testid="stMetricLabel"] { color:var(--muted); font-weight:600; font-size:.78rem; }
      [data-testid="stMetricValue"] { color:var(--text); font-family:'DM Mono',ui-monospace,monospace; font-size:1.6rem; }
      [data-testid="stMetricDelta"] { font-size:.73rem; }
      [data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--line) !important; border-radius:16px !important; background:rgba(13,31,53,.72); box-shadow:0 10px 30px rgba(0,0,0,.10); }
      [data-testid="stVerticalBlockBorderWrapper"] > div { padding:.35rem .45rem; }
      div[data-baseweb="tab-list"] { gap:.4rem; border-bottom:1px solid var(--line); }
      button[data-baseweb="tab"] { color:var(--muted); font-size:.86rem; font-weight:700; padding:.72rem .85rem; }
      button[data-baseweb="tab"][aria-selected="true"] { color:var(--sky); }
      button[data-baseweb="tab"]:focus-visible,button:focus-visible,summary:focus-visible,[role="combobox"]:focus-visible { outline:2px solid var(--sky) !important; outline-offset:3px; }
      [data-testid="stExpander"] { background:rgba(13,31,53,.78); border:1px solid var(--line) !important; border-radius:14px !important; margin-bottom:.6rem; overflow:hidden; }
      [data-testid="stExpander"] summary { padding:.85rem 1rem; font-weight:700; }
      [data-testid="stExpander"] summary:hover { color:var(--sky); }
      [data-baseweb="select"] > div,[data-baseweb="input"] > div { background:#0A1A2E !important; border-color:var(--line) !important; border-radius:10px !important; }
      .stTextInput input { background:#0A1A2E !important; border-color:var(--line) !important; }
      .stButton > button,[data-testid="stDownloadButton"] > button { background:#337ED9; border:0; border-radius:10px; color:white; font-weight:700; }
      .stButton > button:hover,[data-testid="stDownloadButton"] > button:hover { filter:brightness(1.08); }
      [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; }
      hr { border-color:var(--line); margin:1.5rem 0; }
      .hero { position:relative; overflow:hidden; padding:1.6rem 1.7rem 1.5rem; border:1px solid rgba(120,196,255,.22); border-radius:22px; background:linear-gradient(118deg,rgba(16,48,83,.98),rgba(10,27,48,.88)); box-shadow:0 20px 48px rgba(0,0,0,.16); margin-bottom:1.15rem; }
      .hero:after { content:''; position:absolute; width:18rem; height:18rem; right:-5rem; top:-13rem; border:1px solid rgba(120,196,255,.20); border-radius:50%; box-shadow:0 0 0 28px rgba(120,196,255,.035),0 0 0 56px rgba(120,196,255,.025); }
      .brand-row { display:flex; align-items:center; gap:.72rem; margin-bottom:.85rem; }
      .brand-mark { display:grid; place-items:center; width:2.1rem; height:2.1rem; border-radius:9px; color:white; font-family:'DM Mono',monospace; font-weight:500; background:linear-gradient(145deg,#60A5FA,#1D4ED8); box-shadow:0 8px 22px rgba(37,99,235,.38); }
      .brand-name { color:#F7FBFF; font-size:1.02rem; font-weight:800; letter-spacing:-.04em; }
      .brand-sub { color:var(--sky); font-size:.69rem; font-weight:800; letter-spacing:.11em; text-transform:uppercase; }
      .hero h1 { margin:0; max-width:700px; font-size:clamp(2rem,4vw,3.35rem); line-height:1.04; }
      .hero h1 em { color:var(--sky); font-style:normal; }
      .hero p { margin:.7rem 0 0; max-width:620px; color:#B6C8DF; font-size:.95rem; line-height:1.55; }
      .section-copy { color:var(--muted); font-size:.87rem; margin-top:-.5rem; }
      .insight-card { height:100%; box-sizing:border-box; padding:1.15rem; border:1px solid var(--line); border-radius:14px; background:linear-gradient(155deg,rgba(19,46,77,.72),rgba(11,27,47,.72)); }
      .insight-card .kicker { color:var(--sky); font-size:.7rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; }
      .insight-card .value { color:#F3F8FF; font-size:1.72rem; line-height:1.1; font-weight:800; letter-spacing:-.06em; margin:.35rem 0; }
      .insight-card p { margin:0; color:var(--muted); font-size:.82rem; line-height:1.45; }
      .filter-title { font-weight:800; font-size:.94rem; color:var(--text); margin:.2rem 0 .7rem; }
      .results-bar { display:flex; justify-content:space-between; align-items:center; gap:1rem; padding:.9rem 1rem; margin:.9rem 0; border:1px solid var(--line); border-radius:12px; background:rgba(12,33,57,.66); }
      .results-bar strong { color:#F1F7FF; font-size:.92rem; } .results-bar span { color:var(--muted); font-size:.8rem; }
      .badge { display:inline-block; margin:0 .35rem .35rem 0; padding:.25rem .58rem; border-radius:999px; font-size:.71rem; font-weight:800; letter-spacing:.01em; }
      .badge-native { color:#C9EEFF; background:rgba(56,189,248,.17); border:1px solid rgba(56,189,248,.28); }
      .badge-enabled { color:#E0E5FF; background:rgba(129,140,248,.16); border:1px solid rgba(129,140,248,.28); }
      .badge-non-ai,.badge-neutral { color:#C6D5E8; background:rgba(100,116,139,.2); border:1px solid rgba(148,163,184,.22); }
      .badge-high { color:#CFE9FF; background:rgba(77,163,255,.17); border:1px solid rgba(77,163,255,.30); }
      .badge-medium { color:#DFE4FF; background:rgba(129,140,248,.16); border:1px solid rgba(129,140,248,.28); }
      .badge-low { color:#B5D5FC; background:rgba(36,133,251,.13); border:1px solid rgba(36,133,251,.25); }
      .source { color:var(--muted); font-size:.76rem; word-break:break-word; }
      @media (max-width:680px) { .block-container { padding:1rem .9rem 2.2rem; } .hero { padding:1.25rem; border-radius:17px; } .hero h1 { font-size:2rem; } [data-testid="stMetric"] { min-height:auto; } .results-bar { align-items:flex-start; flex-direction:column; } }

      /* Identidade Nivra: um atlas de sinais, não um dashboard de cards. */
      :root { --page:#050D18; --surface:#091827; --line:rgba(133,195,255,.19); --text:#E8F4FF; --muted:#8CA8C4; --blue:#2678FF; --sky:#51CDFF; }
      .stApp {
        background-color:var(--page) !important;
        background-image:linear-gradient(rgba(105,169,230,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(105,169,230,.045) 1px,transparent 1px) !important;
        background-size:32px 32px !important;
      }
      html,body,[class*="css"],.stMarkdown,p,span,div,button,input,label { font-family:'Space Grotesk',ui-sans-serif,system-ui,sans-serif; }
      .block-container { max-width:1400px; padding-top:1.35rem; }
      h1,h2,h3 { font-family:'Space Grotesk',ui-sans-serif,sans-serif; }
      [data-testid="stMetric"] { min-height:auto; border-radius:0; border-width:0 0 1px 0; padding:.7rem 0; background:transparent; box-shadow:none; }
      [data-testid="stMetricValue"] { font-family:'IBM Plex Mono',ui-monospace,monospace; font-size:1.4rem; }
      [data-testid="stVerticalBlockBorderWrapper"] { border-radius:0 !important; background:rgba(6,18,32,.73); box-shadow:none; }
      [data-testid="stExpander"] { border-radius:0 !important; background:rgba(6,18,32,.76); margin-bottom:.48rem; }
      [data-testid="stExpander"] summary { padding:.9rem .1rem; }
      [data-baseweb="select"] > div,[data-baseweb="input"] > div,.stTextInput input { border-radius:0 !important; }
      .hero {
        display:grid; grid-template-columns:minmax(0,1.12fr) minmax(250px,.88fr); gap:2rem; align-items:center;
        overflow:visible; min-height:290px; padding:1.15rem 0 1.45rem !important; margin:0 0 1.2rem;
        border-width:1px 0 !important; border-radius:0 !important; border-color:rgba(133,195,255,.28) !important;
        background:transparent !important; box-shadow:none !important;
      }
      .hero:after { display:none; }
      .brand-row { gap:.58rem; margin-bottom:1.7rem; }
      .brand-mark { width:1.8rem; height:1.8rem; border-radius:0; background:#2678FF; box-shadow:4px 4px 0 #0E3159; font-family:'IBM Plex Mono',monospace; }
      .brand-name { font-size:.94rem; letter-spacing:.02em; text-transform:uppercase; }
      .brand-sub { color:#8CA8C4; font-family:'IBM Plex Mono',monospace; font-size:.62rem; letter-spacing:.08em; }
      .hero h1 { max-width:720px; font-size:clamp(2.35rem,5vw,4.65rem); line-height:.94; letter-spacing:-.075em; }
      .hero h1 em { color:#51CDFF; }
      .hero p { max-width:560px; margin:1.1rem 0 0; color:#AAC1D8; font-size:1rem; }
      .atlas-orbit { position:relative; width:min(100%,300px); aspect-ratio:1; justify-self:end; border:1px solid rgba(81,205,255,.45); border-radius:50%; background:radial-gradient(circle at 50% 50%,rgba(38,120,255,.18) 0 5%,transparent 6%); }
      .atlas-orbit:before,.atlas-orbit:after { content:''; position:absolute; inset:16%; border:1px solid rgba(81,205,255,.24); border-radius:50%; }
      .atlas-orbit:after { inset:33%; border-color:rgba(81,205,255,.38); }
      .axis { position:absolute; background:rgba(81,205,255,.25); }
      .axis-h { width:124%; height:1px; left:-12%; top:50%; } .axis-v { height:124%; width:1px; top:-12%; left:50%; }
      .orbit-dot { position:absolute; width:10px; height:10px; border-radius:50%; background:#51CDFF; box-shadow:0 0 0 4px rgba(81,205,255,.12),0 0 18px rgba(81,205,255,.72); }
      .dot-a { left:24%; top:26%; } .dot-b { right:20%; top:37%; width:7px; height:7px; background:#95A4FF; } .dot-c { left:37%; bottom:17%; width:6px; height:6px; background:#2678FF; }
      .orbit-copy { position:absolute; right:-.4rem; bottom:7%; color:#9EC9EF; font-family:'IBM Plex Mono',monospace; font-size:.61rem; letter-spacing:.07em; text-align:right; line-height:1.55; }
      .signal-strip { display:grid; grid-template-columns:repeat(4,1fr); border-top:1px solid var(--line); border-bottom:1px solid var(--line); margin:1.1rem 0 1.2rem; }
      .signal { min-height:105px; padding:1rem 1.1rem; border-left:1px solid var(--line); } .signal:first-child { border-left:0; }
      .signal span { display:block; color:#78BEEB; font-family:'IBM Plex Mono',monospace; font-size:.61rem; letter-spacing:.08em; }
      .signal strong { display:block; margin:.28rem 0 .12rem; color:#EFF8FF; font-family:'IBM Plex Mono',monospace; font-size:1.8rem; font-weight:500; letter-spacing:-.08em; }
      .signal p { margin:0; color:#91A9C2; font-size:.74rem; }
      .section-header { display:grid; grid-template-columns:3rem minmax(0,1fr); gap:.75rem; align-items:start; margin:2.5rem 0 1.2rem; }
      .section-header > span { color:#51CDFF; font-family:'IBM Plex Mono',monospace; font-size:.72rem; padding-top:.38rem; }
      .section-header h2 { margin:0 !important; font-size:1.55rem !important; letter-spacing:-.055em; }
      .section-header p { margin:.22rem 0 0; color:#91A9C2; font-size:.88rem; }
      .insight-card { border:0; border-top:1px solid var(--line); border-radius:0; padding:1rem 0; background:transparent; }
      .insight-card .kicker { font-family:'IBM Plex Mono',monospace; color:#6EBDF2; font-size:.62rem; }
      .insight-card .value { font-family:'IBM Plex Mono',monospace; font-size:1.55rem; letter-spacing:-.075em; }
      .filter-title { font-family:'IBM Plex Mono',monospace; color:#6EBDF2; font-size:.68rem; letter-spacing:.07em; text-transform:uppercase; }
      .results-bar { border-radius:0; background:rgba(8,27,46,.6); }
      .badge { border-radius:0; font-family:'IBM Plex Mono',monospace; font-size:.65rem; }
      @media (max-width:800px) {
        .hero { grid-template-columns:1fr; min-height:auto; } .atlas-orbit { width:205px; justify-self:start; margin-top:.35rem; }
        .signal-strip { grid-template-columns:repeat(2,1fr); } .signal:nth-child(3) { border-left:0; border-top:1px solid var(--line); } .signal:nth-child(4) { border-top:1px solid var(--line); }
      }
      @media (max-width:500px) { .signal-strip { grid-template-columns:1fr; } .signal { border-left:0; border-top:1px solid var(--line); } .signal:first-child { border-top:0; } .hero h1 { font-size:2.55rem; } }

      /* Tema Nivra: branco frio, azuis em camadas escurecendo do fundo ao texto. */
      :root { --page:#F8FBFF; --surface:#FFFFFF; --line:rgba(45,109,187,.19); --text:#142A46; --muted:#536C8B; --blue:#337ED9; --sky:#236BC4; }
      .stApp { background-color:var(--page) !important; background-image:linear-gradient(rgba(51,126,217,.055) 1px,transparent 1px),linear-gradient(90deg,rgba(51,126,217,.055) 1px,transparent 1px) !important; }
      html,body,[class*="css"],.stMarkdown,p,span,div,button,input,label { color:var(--text); }
      h1,h2,h3 { color:var(--text); }
      [data-testid="stVerticalBlockBorderWrapper"] { background:rgba(255,255,255,.82); border-color:var(--line) !important; }
      [data-testid="stExpander"] { background:rgba(255,255,255,.88); border-color:var(--line) !important; }
      [data-testid="stExpander"] summary:hover { color:#236BC4; }
      [data-baseweb="select"] > div,[data-baseweb="input"] > div,.stTextInput input { background:#FDFEFF !important; border-color:rgba(45,109,187,.25) !important; color:#142A46 !important; }
      [data-testid="stMetricValue"] { color:#174D8E; }
      .hero { border-color:rgba(45,109,187,.33) !important; }
      .brand-mark { background:#337ED9; box-shadow:4px 4px 0 #B7D2F4; }
      .brand-name { color:#1B3D67; } .brand-sub { color:#3A6BA7; }
      .hero h1 { color:#142A46; } .hero h1 em { color:#236BC4; } .hero p { color:#536C8B; }
      .atlas-orbit { border-color:rgba(35,107,196,.45); background:radial-gradient(circle at 50% 50%,rgba(51,126,217,.16) 0 5%,transparent 6%); }
      .atlas-orbit:before,.atlas-orbit:after { border-color:rgba(35,107,196,.22); } .atlas-orbit:after { border-color:rgba(35,107,196,.36); }
      .axis { background:rgba(35,107,196,.22); }
      .orbit-dot { background:#337ED9; box-shadow:0 0 0 4px rgba(51,126,217,.12),0 0 18px rgba(51,126,217,.44); }
      .dot-b { background:#A9CAF3; } .dot-c { background:#1D5CA9; }
      .orbit-copy { color:#3A6BA7; }
      .signal-strip { border-color:var(--line); } .signal { border-color:var(--line); }
      .signal span,.section-header > span,.filter-title { color:#2D6AB5; }
      .signal strong,.insight-card .value { color:#1B467A; }
      .signal p,.section-header p,.insight-card p,.results-bar span,.source { color:#536C8B; }
      .section-header h2 { color:#142A46; }
      .insight-card { border-color:var(--line); }
      .insight-card .kicker { color:#2D6AB5; }
      .results-bar { background:#F1F7FF; border-color:var(--line); } .results-bar strong { color:#1B3D67; }
      .stButton > button,[data-testid="stDownloadButton"] > button { background:#337ED9; }
      .badge-native { color:#174D8E; background:#E0EDFC; border-color:#B5D1F3; }
      .badge-enabled { color:#254C7C; background:#E4EDF8; border-color:#B5CCE9; }
      .badge-non-ai,.badge-neutral { color:#58677A; background:#F0F4F8; border-color:#D1DBE7; }
      .badge-high { color:#FFF; background:#236BC4; border-color:#236BC4; }
      .badge-medium { color:#254C7C; background:#C5DBF7; border-color:#A3C3EA; }
      .badge-low { color:#58677A; background:#EAF2FB; border-color:#CEDCED; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def carregar():
    if not os.path.exists(RESULTADO):
        return None
    with open(RESULTADO, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def classificacao(perfil):
    return (perfil.get("classificacao") or {}).get("classificacao", "indeterminado")


def confianca(perfil):
    return (perfil.get("classificacao") or {}).get("confianca", "baixa")


def recomendacoes(perfil):
    return (perfil.get("recomendacoes") or {}).get("recomendacoes", [])


def prioridade_empresa(perfil):
    pesos = {"alta": 0, "media": 1, "baixa": 2}
    return min((pesos.get(item.get("prioridade"), 3) for item in recomendacoes(perfil)), default=4)


def rotulo_classe(valor):
    return {
        "AI-native": "IA nativa",
        "AI-enabled": "IA habilitada",
        "non-AI": "Sem IA central",
        "indeterminado": "Indeterminado",
    }.get(valor, valor)


def badge(texto, estilo):
    return f"<span class='badge badge-{estilo}'>{escape(str(texto))}</span>"


def badge_classe(valor):
    estilo = {"AI-native": "native", "AI-enabled": "enabled", "non-AI": "non-ai"}.get(
        valor, "neutral"
    )
    return badge(rotulo_classe(valor), estilo)


def badge_nivel(tipo, nivel):
    estilo = {"alta": "high", "media": "medium", "baixa": "low"}.get(nivel, "neutral")
    return badge(f"{tipo} {nivel}", estilo)


def titulo_secao(indice, titulo, descricao):
    return (
        f"<div class='section-header'><span>{escape(indice)}</span><div>"
        f"<h2>{escape(titulo)}</h2><p>{escape(descricao)}</p></div></div>"
    )


def tema_chart(chart):
    return (
        chart.configure_view(strokeWidth=0)
        .configure(background="transparent")
        .configure_axis(
            labelColor="#3B526E",
            titleColor="#536C8B",
            gridColor="rgba(45,109,187,.12)",
            domainColor="rgba(45,109,187,.18)",
            tickColor="rgba(45,109,187,.18)",
            labelFont="Manrope",
            titleFont="Manrope",
            labelFontSize=11,
            titleFontSize=11,
        )
        .configure_legend(labelColor="#3B526E", titleColor="#536C8B", labelFont="Manrope")
        .configure_text(font="Manrope")
    )


dados = carregar()
if dados is None:
    st.error("Nenhum resultado disponível. Rode a pipeline antes de abrir o Nivra.")
    st.code("python scripts/rodar_todas.py --com-rag")
    st.stop()

perfis = dados.get("perfis", [])
contagem = {classe: sum(classificacao(p) == classe for p in perfis) for classe in ORDEM_CLS}
total_recs = sum(len(recomendacoes(p)) for p in perfis)
taxas = [p.get("taxa_validacao", 0) for p in perfis]
validacao_media = sum(taxas) / len(taxas) if taxas else 0
prioridade_alta = sum(
    1 for perfil in perfis for rec in recomendacoes(perfil) if rec.get("prioridade") == "alta"
)

st.markdown(
    """
  <section class="hero">
    <div>
      <div class="brand-row"><div class="brand-mark">N</div><div><div class="brand-name">Nivra</div><div class="brand-sub">Signal atlas / BR-01</div></div></div>
      <h1>Leia o mercado.<br><em>Encontre o sinal.</em></h1>
      <p>Um atlas de startups para transformar evidência dispersa em pontos de entrada claros para a NVIDIA.</p>
    </div>
    <div class="atlas-orbit" aria-label="Mapa orbital decorativo de sinais">
      <i class="axis axis-h"></i><i class="axis axis-v"></i>
      <i class="orbit-dot dot-a"></i><i class="orbit-dot dot-b"></i><i class="orbit-dot dot-c"></i>
      <div class="orbit-copy">SIGNAL MAP<br>ACTIVE / BR</div>
    </div>
  </section>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
  <section class="signal-strip">
    <div class="signal"><span>01 // BASE</span><strong>{len(perfis):02d}</strong><p>startups mapeadas</p></div>
    <div class="signal"><span>02 // NÚCLEO</span><strong>{contagem.get('AI-native', 0):02d}</strong><p>com IA no centro do produto</p></div>
    <div class="signal"><span>03 // ABERTURA</span><strong>{total_recs:02d}</strong><p>oportunidades NVIDIA</p></div>
    <div class="signal"><span>04 // LASTRO</span><strong>{validacao_media:.0%}</strong><p>evidências verificadas</p></div>
  </section>
""",
    unsafe_allow_html=True,
)
st.caption(
    f"Atualizado em {dados.get('gerado_em', '—')} · modelo {dados.get('modelo', '—')} · análise em {dados.get('duracao_segundos', '—')}s"
)

aba_visao, aba_radar, aba_briefing, aba_qualidade = st.tabs(
    ["Visão executiva", "Radar de startups", "Briefing", "Confiabilidade"]
)

with aba_visao:
    st.markdown(
        titulo_secao(
            "01 / LEITURA",
            "Visão executiva",
            "O que merece atenção agora, sem atravessar uma parede de indicadores.",
        ),
        unsafe_allow_html=True,
    )
    mais_recomendadas = sorted(
        perfis, key=lambda p: (-len(recomendacoes(p)), prioridade_empresa(p))
    )
    lider = mais_recomendadas[0].get("nome", "—") if mais_recomendadas else "—"
    cobertura = sum(1 for p in perfis if recomendacoes(p)) / len(perfis) if perfis else 0
    leitura_1, leitura_2, leitura_3 = st.columns(3)
    with leitura_1:
        st.markdown(
            f"<div class='insight-card'><div class='kicker'>Prioridade imediata</div><div class='value'>{prioridade_alta}</div><p>recomendações de alta prioridade para iniciar a abordagem.</p></div>",
            unsafe_allow_html=True,
        )
    with leitura_2:
        st.markdown(
            f"<div class='insight-card'><div class='kicker'>Maior densidade</div><div class='value'>{escape(lider)}</div><p>lidera em volume de tecnologias sugeridas pela análise.</p></div>",
            unsafe_allow_html=True,
        )
    with leitura_3:
        st.markdown(
            f"<div class='insight-card'><div class='kicker'>Cobertura comercial</div><div class='value'>{cobertura:.0%}</div><p>das startups têm pelo menos uma oportunidade mapeada.</p></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        titulo_secao(
            "02 / MAPA",
            "Mapa de oportunidades",
            "Comparações diretas para situar a maturidade do mercado e a confiança da base.",
        ),
        unsafe_allow_html=True,
    )
    esquerda, direita = st.columns([1, 1.15], gap="large")
    df_maturidade = pd.DataFrame(
        [
            {"classificacao": rotulo_classe(c), "empresas": contagem[c], "cor": CORES_CLASSE[c]}
            for c in ORDEM_CLS
            if contagem.get(c, 0)
        ]
    )
    with esquerda, st.container(border=True):
        st.markdown("**Maturidade em IA**")
        st.caption("Comparação direta de contagens por perfil.")
        base = alt.Chart(df_maturidade).encode(
            y=alt.Y("classificacao:N", sort="-x", title=None),
            x=alt.X("empresas:Q", title="startups", axis=alt.Axis(tickMinStep=1)),
        )
        barras = base.mark_bar(cornerRadiusEnd=6, height=28).encode(
            color=alt.Color("cor:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("classificacao:N", title="Perfil"),
                alt.Tooltip("empresas:Q", title="Startups"),
            ],
        )
        textos = base.mark_text(align="left", dx=7, color="#1B3D67", fontWeight=700).encode(
            text="empresas:Q"
        )
        st.altair_chart(
            tema_chart((barras + textos).properties(height=175)), use_container_width=True
        )

    df_validacao = pd.DataFrame(
        [
            {
                "empresa": p.get("nome", "—"),
                "taxa": p.get("taxa_validacao", 0),
                "faixa": "Atenção" if p.get("taxa_validacao", 0) < 0.5 else "Confiável",
            }
            for p in perfis
        ]
    ).sort_values("taxa", ascending=False)
    with direita, st.container(border=True):
        st.markdown("**Base para decisão**")
        st.caption("A linha marca o limiar de 50% de evidências verificadas.")
        base = alt.Chart(df_validacao).encode(
            y=alt.Y("empresa:N", sort="-x", title=None),
            x=alt.X(
                "taxa:Q",
                title="evidências verificadas",
                axis=alt.Axis(format="%"),
                scale=alt.Scale(domain=[0, 1]),
            ),
        )
        referencia = (
            alt.Chart(pd.DataFrame({"limiar": [0.5]}))
            .mark_rule(color="#849EBD", strokeDash=[5, 5])
            .encode(x="limiar:Q")
        )
        pontos = base.mark_circle(size=95, stroke="#F8FBFF", strokeWidth=2).encode(
            color=alt.Color(
                "faixa:N",
                scale=alt.Scale(domain=["Confiável", "Atenção"], range=[AZUL_CLARO, ATENCAO]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("empresa:N", title="Startup"),
                alt.Tooltip("taxa:Q", title="Validação", format=".0%"),
            ],
        )
        rotulos = base.mark_text(
            align="left", dx=10, color="#1B3D67", fontSize=11, fontWeight=700
        ).encode(text=alt.Text("taxa:Q", format=".0%"))
        st.altair_chart(
            tema_chart(
                (referencia + pontos + rotulos).properties(height=max(190, len(df_validacao) * 25))
            ),
            use_container_width=True,
        )

    tecnologias = {}
    for perfil in perfis:
        for rec in recomendacoes(perfil):
            tecnologia = rec.get("tecnologia", "Tecnologia não informada").removeprefix("NVIDIA ")
            tecnologias[tecnologia] = tecnologias.get(tecnologia, 0) + 1
    if tecnologias:
        st.markdown(
            titulo_secao(
                "03 / VETOR",
                "Onde a conversa começa",
                "Tecnologias com maior recorrência na análise atual.",
            ),
            unsafe_allow_html=True,
        )
        df_tecnologias = (
            pd.DataFrame([{"tecnologia": t, "recomendacoes": q} for t, q in tecnologias.items()])
            .sort_values("recomendacoes", ascending=False)
            .head(8)
        )
        maior_volume = df_tecnologias["recomendacoes"].max()
        df_tecnologias["destaque"] = (
            df_tecnologias["recomendacoes"]
            .eq(maior_volume)
            .map({True: "Destaque", False: "Demais"})
        )
        with st.container(border=True):
            st.caption(
                "Ranking das tecnologias mais recorrentes; o azul claro destaca a maior oportunidade."
            )
            base = alt.Chart(df_tecnologias).encode(
                y=alt.Y("tecnologia:N", sort="-x", title=None, axis=alt.Axis(labelLimit=280)),
                x=alt.X("recomendacoes:Q", title="recomendações", axis=alt.Axis(tickMinStep=1)),
            )
            barras = base.mark_bar(cornerRadiusEnd=6, height=24).encode(
                color=alt.Color(
                    "destaque:N",
                    scale=alt.Scale(domain=["Destaque", "Demais"], range=[AZUL_CLARO, "#A9BFD9"]),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("tecnologia:N", title="Tecnologia"),
                    alt.Tooltip("recomendacoes:Q", title="Recomendações"),
                ],
            )
            texto = base.mark_text(align="left", dx=7, color="#1B3D67", fontWeight=700).encode(
                text="recomendacoes:Q"
            )
            st.altair_chart(
                tema_chart((barras + texto).properties(height=max(190, len(df_tecnologias) * 32))),
                use_container_width=True,
            )

with aba_radar:
    st.markdown(
        titulo_secao(
            "01 / RADAR",
            "Radar de startups",
            "Filtre a base, priorize oportunidades e abra apenas o contexto necessário para a próxima conversa.",
        ),
        unsafe_allow_html=True,
    )
    opcoes_cls = [c for c in ORDEM_CLS if contagem.get(c, 0)]
    with st.container(border=True):
        st.markdown("<div class='filter-title'>Refine a fila</div>", unsafe_allow_html=True)
        filtro_1, filtro_2, filtro_3, filtro_4 = st.columns([1.25, 1.2, 0.9, 1.2])
        with filtro_1:
            filtro_cls = st.multiselect(
                "Perfil de IA", opcoes_cls, default=opcoes_cls, format_func=rotulo_classe
            )
        with filtro_2:
            filtro_conf = st.multiselect("Confiança", ORDEM_CONF, default=ORDEM_CONF)
        with filtro_3:
            somente_recs = st.checkbox(
                "Com oportunidade",
                value=False,
                help="Exibe startups com ao menos uma tecnologia sugerida.",
            )
        with filtro_4:
            ordenacao = st.selectbox(
                "Ordenar por", ["Prioridade NVIDIA", "Evidências validadas", "Nome"]
            )
        busca = st.text_input("Buscar startup", placeholder="Ex.: Arvo, saúde, crédito")

    visiveis = []
    for perfil in perfis:
        nome = perfil.get("nome", "")
        if classificacao(perfil) not in filtro_cls or confianca(perfil) not in filtro_conf:
            continue
        if somente_recs and not recomendacoes(perfil):
            continue
        if busca and busca.lower() not in nome.lower():
            continue
        visiveis.append(perfil)
    if ordenacao == "Prioridade NVIDIA":
        visiveis.sort(
            key=lambda p: (prioridade_empresa(p), -p.get("taxa_validacao", 0), p.get("nome", ""))
        )
    elif ordenacao == "Evidências validadas":
        visiveis.sort(key=lambda p: (-p.get("taxa_validacao", 0), p.get("nome", "")))
    else:
        visiveis.sort(key=lambda p: p.get("nome", ""))

    total_filtrado = sum(len(recomendacoes(p)) for p in visiveis)
    st.markdown(
        f"<div class='results-bar'><strong>{len(visiveis)} startups na fila</strong><span>{total_filtrado} oportunidades NVIDIA encontradas nos filtros atuais</span></div>",
        unsafe_allow_html=True,
    )
    if not visiveis:
        st.info(
            "Nenhuma startup corresponde aos filtros atuais. Amplie um dos critérios para voltar à base completa."
        )

    for perfil in visiveis:
        classe, nivel_conf, recs = classificacao(perfil), confianca(perfil), recomendacoes(perfil)
        nome = perfil.get("nome", "Startup")
        with st.expander(f"{nome}  ·  {rotulo_classe(classe)}  ·  {len(recs)} oportunidade(s)"):
            st.markdown(
                badge_classe(classe) + badge_nivel("confiança", nivel_conf), unsafe_allow_html=True
            )
            kpi_1, kpi_2, kpi_3 = st.columns(3)
            kpi_1.metric("Oportunidades", len(recs))
            kpi_2.metric("Evidências", len(perfil.get("evidencias", [])))
            kpi_3.metric("Validação", f"{perfil.get('taxa_validacao', 0):.0%}")
            diagnostico, oportunidades, fontes = st.tabs(
                ["Diagnóstico", f"Oportunidades ({len(recs)})", "Evidências"]
            )
            detalhada = perfil.get("classificacao") or {}
            with diagnostico:
                st.markdown("**Leitura da análise**")
                st.write(detalhada.get("justificativa", "Sem justificativa disponível."))
                favor, validar = st.columns(2)
                with favor:
                    st.markdown("**Sinais encontrados**")
                    for sinal in detalhada.get("sinais_a_favor", []) or [
                        "Nenhum sinal adicional registrado."
                    ]:
                        st.markdown(f"- {sinal}")
                with validar:
                    st.markdown("**Pontos a validar**")
                    for sinal in detalhada.get("sinais_contra", []) or [
                        "Nenhuma ressalva registrada."
                    ]:
                        st.markdown(f"- {sinal}")
            with oportunidades:
                if not recs:
                    motivo = (perfil.get("recomendacoes") or {}).get("sem_recomendacao")
                    st.info(
                        motivo
                        or "A análise não encontrou uma oportunidade NVIDIA clara para este perfil."
                    )
                for rec in recs:
                    tecnologia = rec.get("tecnologia", "Tecnologia NVIDIA")
                    st.markdown(
                        f"**{escape(tecnologia)}**<br>"
                        + badge_nivel("prioridade", rec.get("prioridade", "baixa"))
                        + badge(f"complexidade {rec.get('complexidade', '—')}", "neutral"),
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Motivo técnico.** {rec.get('justificativa_tecnica', '—')}")
                    st.markdown(f"**Impacto de negócio.** {rec.get('justificativa_negocio', '—')}")
                    st.markdown(f"**Próximo passo.** {rec.get('proxima_acao', '—')}")
                    st.divider()
            with fontes:
                validadas, rejeitadas = perfil.get("evidencias", []), perfil.get(
                    "evidencias_rejeitadas", []
                )
                st.caption(
                    f"{len(validadas)} fontes validadas · {len(rejeitadas)} evidências rejeitadas"
                )
                for evidencia in validadas:
                    st.markdown(f"> {evidencia.get('trecho', '')[:280]}")
                    st.markdown(
                        f"<div class='source'>Fonte: {escape(evidencia.get('url_fonte', 'Não informada'))}</div>",
                        unsafe_allow_html=True,
                    )
                for evidencia in rejeitadas:
                    st.markdown(
                        f"- ~~{evidencia.get('afirmacao', '')}~~ · {evidencia.get('motivo_rejeicao', 'rejeitada na validação')}"
                    )

with aba_briefing:
    st.markdown(
        titulo_secao(
            "01 / SÍNTESE",
            "Briefing executivo",
            "Uma leitura pronta para compartilhar o panorama, as oportunidades e as ressalvas da análise.",
        ),
        unsafe_allow_html=True,
    )
    briefing = dados.get("briefing", "")
    if briefing:
        with st.container(border=True):
            st.markdown(briefing)
        st.download_button(
            "Baixar briefing em Markdown",
            briefing,
            file_name="briefing-nivra.md",
            mime="text/markdown",
        )
    else:
        st.info(
            "O briefing ainda não foi gerado nesta execução. Rode a pipeline com RAG para criá-lo."
        )

with aba_qualidade:
    st.markdown(
        titulo_secao(
            "01 / LASTRO",
            "Confiabilidade da análise",
            "Uma afirmação só avança para recomendação depois que o trecho correspondente é localizado na fonte original.",
        ),
        unsafe_allow_html=True,
    )
    linhas = [
        {
            "Startup": p.get("nome", "—"),
            "Perfil de IA": rotulo_classe(classificacao(p)),
            "Confiança": confianca(p).capitalize(),
            "Validadas": len(p.get("evidencias", [])),
            "Rejeitadas": len(p.get("evidencias_rejeitadas", [])),
            "Taxa de validação": p.get("taxa_validacao", 0),
            "Oportunidades": len(recomendacoes(p)),
        }
        for p in perfis
    ]
    tabela = pd.DataFrame(linhas).sort_values("Taxa de validação")
    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Taxa de validação": st.column_config.ProgressColumn(
                "Taxa de validação", format="%.0f%%", min_value=0, max_value=1
            )
        },
    )
    baixas = tabela[tabela["Taxa de validação"] < 0.5]
    if len(baixas):
        st.warning(
            f"{len(baixas)} startup(s) têm menos de 50% das evidências verificadas. Trate suas recomendações como hipóteses para validação manual."
        )
