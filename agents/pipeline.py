"""
Pipeline multi-agente do NVIDIA Startup AI Radar.

Estado atual: 3 nos (Query Planner, Retriever, Extractor).
Os proximos dias adicionam Classifier, Evidence Validator, RAG, Recommendation e Briefing
como novos nos neste mesmo grafo.
"""

import os
import json
import time
from typing import TypedDict, List, Dict, Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_not_exception_type,
)
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

load_dotenv()

# Provedor de LLM abstraido atras da interface compativel com OpenAI.
# Trocar de provedor (Groq, NVIDIA NIM, outro) e so mudar o .env, nao o codigo.
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    temperature=0,
)

DB = os.getenv("DATABASE_URL")

# Enquanto estiver depurando, mantenha 1. Suba para 31 so quando a pipeline estabilizar.
LIMITE_STARTUPS = 1
PAUSA_ENTRE_CHAMADAS = 3  # segundos, para respeitar o limite de tokens/minuto do tier gratuito


class Estado(TypedDict):
    consulta: str                     # o que o usuario pediu, em linguagem natural
    filtros: Dict[str, Any]           # criterios de busca extraidos da consulta
    startups: List[Dict[str, Any]]    # empresas recuperadas do banco
    documentos: List[Dict[str, Any]]  # documentos das empresas recuperadas
    perfis: List[Dict[str, Any]]      # perfil estruturado de cada empresa


def conectar():
    return psycopg2.connect(DB, cursor_factory=psycopg2.extras.RealDictCursor)


class RespostaNaoEhJson(Exception):
    """O modelo respondeu algo que nao e JSON. Repetir a chamada igual nao resolve."""


@retry(
    wait=wait_exponential(min=5, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_not_exception_type(RespostaNaoEhJson),
)
def chamar_llm(prompt: str) -> str:
    """Chamada crua ao modelo, com retry para falha de rede e limite de taxa (429)."""
    return llm.invoke(prompt).content.strip()


def pedir_json(prompt: str) -> Any:
    """Chama o LLM e devolve JSON.

    O retry cobre apenas falha de rede e erro 429. Resposta que nao e JSON nao e
    repetida de proposito: o problema esta no prompt, nao na chamada, e repetir
    so gastaria cota do tier gratuito.
    """
    bruto = chamar_llm(prompt)
    if bruto.startswith("```"):
        bruto = bruto.split("```")[1]
        if bruto.startswith("json"):
            bruto = bruto[4:]
    bruto = bruto.strip()
    try:
        return json.loads(bruto)
    except json.JSONDecodeError:
        print("\n--- o modelo respondeu isto, que nao e JSON ---")
        print(bruto[:600])
        print("--- ajuste o prompt para exigir JSON puro ---\n")
        raise RespostaNaoEhJson(bruto[:200])


# ------------------------------------------------------------------ NO 1
def query_planner(estado: Estado) -> Dict[str, Any]:
    """Transforma a consulta em linguagem natural em criterios de busca estruturados."""

    setores = [
        "acessibilidade", "agtech", "contabilidade", "CX e atendimento",
        "dados e IA", "ecommerce", "edtech", "fintech", "healthtech",
        "hrtech", "insurtech", "legaltech", "logtech", "mobilidade",
        "proptech", "retailtech",
    ]

    prompt = f"""Voce e um planejador de consultas de um sistema que analisa startups brasileiras.
Sua unica tarefa e converter a pergunta de um usuario em criterios de busca estruturados.

A base de startups so aceita estes setores:
{", ".join(setores)}

Pergunta do usuario:
{estado['consulta']}

Responda EXATAMENTE neste formato JSON:
{{"setor": "um setor identico a um da lista, ou null",
  "palavras_chave": ["termo1", "termo2"],
  "justificativa": "uma frase curta explicando a escolha"}}

Regras:
- o campo "setor" so pode conter um valor identico a um item da lista, ou null
- se a pergunta nao indicar setor com clareza, use null e confie nas palavras_chave
- "palavras_chave" deve ter de 2 a 5 termos em portugues
- nunca invente um setor que nao esteja na lista

Responda apenas com o JSON, sem texto antes ou depois, sem cerca de markdown."""

    filtros = pedir_json(prompt)
    print(f"[query_planner] filtros: {filtros}")
    return {"filtros": filtros}

# ------------------------------------------------------------------ NO 2
def retriever(estado: Estado) -> Dict[str, Any]:
    """Busca no Postgres as empresas que batem com os filtros do planner."""
    filtros = estado["filtros"]
    setor = filtros.get("setor")
    palavras = [p for p in (filtros.get("palavras_chave") or []) if len(p) >= 4]

    conn = conectar()
    cur = conn.cursor()

    # Uma lista por trecho da query. No fim elas sao concatenadas na MESMA ordem
    # em que os %s aparecem na string: SELECT, depois WHERE, depois LIMIT.
    val_select, val_where = [], []

    if palavras:
        partes = []
        for termo in palavras:
            partes.append(
                "(CASE WHEN descricao_curta ILIKE %s OR setor_detalhado ILIKE %s "
                "THEN 1 ELSE 0 END)"
            )
            val_select.extend([f"%{termo}%"] * 2)
        relevancia = " + ".join(partes)
    else:
        relevancia = "0"

    if setor:
        where = "setor = %s"
        val_where.append(setor)
    else:
        where = "TRUE"

    sql = (f"SELECT *, ({relevancia}) AS relevancia FROM startups "
           f"WHERE {where} ORDER BY relevancia DESC LIMIT %s")
    valores = val_select + val_where + [LIMITE_STARTUPS]

    cur.execute(sql, valores)
    startups = [dict(r) for r in cur.fetchall()]

    ids = [s["id"] for s in startups]
    documentos = []
    if ids:
        cur.execute("SELECT * FROM documentos WHERE startup_id = ANY(%s)", (ids,))
        documentos = [dict(r) for r in cur.fetchall()]

    cur.close()
    conn.close()
    print(f"[retriever] {len(startups)} startups: {[s['nome'] for s in startups]}")
    return {"startups": startups, "documentos": documentos}
# ------------------------------------------------------------------ NO 3
def extractor(estado: Estado) -> Dict[str, Any]:
    perfis = []

    for s in estado["startups"]:
        docs = [d for d in estado["documentos"] if d["startup_id"] == s["id"]]
        textos = "\n\n".join(
            f"[{d['tipo']} | fonte: {d['url_fonte']}]\n{d['conteudo_texto']}"
            for d in docs
        )

        prompt = f"""### BLOCO 1 - PAPEL E TAREFA
Voce e um analista que le documentos publicos sobre empresas e organiza o que esta escrito neles.
Voce nao classifica a empresa, nao recomenda tecnologia e nao opina. Voce apenas relata o conteudo dos documentos.

### BLOCO 2 - CONTEXTO
Empresa: {s['nome']}
Setor: {s['setor']}
Descricao: {s['descricao_curta']}

Documentos disponiveis:
{textos}

### BLOCO 3 - SCHEMA
Responda EXATAMENTE neste formato JSON:
{{"tecnologias_citadas": ["..."],
  "sinais_de_uso_de_ia": ["..."],
  "dados_proprietarios": ["..."],
  "possiveis_gargalos_tecnicos": ["..."],
  "evidencias": [{{"afirmacao": "...", "trecho": "citacao literal copiada do documento", "url_fonte": "..."}}]}}

### BLOCO 4 - REGRAS
- toda url em "evidencias" precisa ser uma das urls que aparecem nos documentos acima
- se um campo nao tiver informacao nos documentos, devolva lista vazia
- so inclua uma tecnologia em "tecnologias_citadas" se o nome dela aparecer escrito nos documentos; nao complete com tecnologias que voce conhece do mercado
- quando nao houver sinais claros de uso de IA, deixe a lista vazia e registre a ausencia em observacoes
- toda inferencia de possiveis gargalos tecnicos deve ser baseada em informacoes que aparecem nos documentos, nao em opiniao sua e deve ser indicado o trecho que sustenta a suspeita de gargalo em "evidencias"
- em "tecnologias_citadas" liste apenas tecnologias, ferramentas, frameworks ou tecnicas com nome proprio (ex: OCR, LLM, visao computacional, Kubernetes, AWS). Nao inclua termos genericos como "dados", "tecnologia", "software" ou "inovacao", e nao repita o mesmo conceito com nomes diferentes.
- "trecho" deve ser uma citacao LITERAL copiada do documento, de 10 a 40 palavras, sem parafrasear. Se voce nao conseguir copiar um trecho literal que sustente a afirmacao, remova a afirmacao inteira.

### BLOCO 5 - FORMATO
Responda apenas com o JSON, sem texto antes ou depois, sem cerca de markdown."""

        perfil = pedir_json(prompt)
        perfil["startup_id"] = s["id"]
        perfil["nome"] = s["nome"]
        perfis.append(perfil)
        print(f"[extractor] perfil montado: {s['nome']}")
        time.sleep(PAUSA_ENTRE_CHAMADAS)

    return {"perfis": perfis}


# ------------------------------------------------------------------ GRAFO
grafo = StateGraph(Estado)
grafo.add_node("query_planner", query_planner)
grafo.add_node("retriever", retriever)
grafo.add_node("extractor", extractor)

grafo.add_edge(START, "query_planner")
grafo.add_edge("query_planner", "retriever")
grafo.add_edge("retriever", "extractor")
grafo.add_edge("extractor", END)

pipeline = grafo.compile()


if __name__ == "__main__":
    resultado = pipeline.invoke({
        "consulta": "startups de saude que usam IA no diagnostico",
        "filtros": {},
        "startups": [],
        "documentos": [],
        "perfis": [],
    })
    print("\n===== PERFIS =====")
    print(json.dumps(resultado["perfis"], indent=2, ensure_ascii=False))
