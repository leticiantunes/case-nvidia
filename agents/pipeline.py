"""
Pipeline multi-agente do NVIDIA Startup AI Radar.

Estado atual: 3 nos (Query Planner, Retriever, Extractor).
Os proximos dias adicionam Classifier, Evidence Validator, RAG, Recommendation e Briefing
como novos nos neste mesmo grafo.
"""

import os
import sys
import json
import time
from typing import TypedDict, List, Dict, Any

# pipeline.py mora em agents/, mas importa de rag/. Colocar a raiz do projeto no
# sys.path faz "python agents/pipeline.py" enxergar os dois pacotes.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

from agents.validador import evidence_validator
from rag.busca import BuscaHibrida

load_dotenv()

# O console do Windows nao usa UTF-8 por padrao, o que faz acento virar caractere
# invalido no print. Sem isso, a saida do pipeline aparece quebrada na demonstracao.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Provedor de LLM abstraido atras da interface compativel com OpenAI.
# Trocar de provedor (Groq, NVIDIA NIM, outro) e so mudar o .env, nao o codigo.
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    temperature=0,
    # Modelos da familia gpt-oss gastam tokens de raciocinio ANTES de escrever a
    # resposta, e esses tokens contam dentro do teto. Com teto baixo, o raciocinio
    # consome o orcamento e o JSON sai vazio ou cortado no meio de uma string.
    # Duas medidas: teto maior e esforco de raciocinio reduzido. Esta tarefa e de
    # extracao estruturada, nao de raciocinio profundo, entao "low" nao prejudica.
    max_tokens=8000,
    # ATENCAO: reasoning_effort PRECISA ir dentro de model_kwargs.
    # Passar como parametro de primeira classe faz o langchain-openai traduzir para
    # o formato da API de reasoning da OpenAI, que o endpoint do Groq rejeita, e
    # TODAS as chamadas passam a falhar. O UserWarning que aparece no console por
    # causa disso e cosmetico: deixe como esta.
    model_kwargs={"reasoning_effort": os.getenv("LLM_REASONING_EFFORT", "low")},
)

DB = os.getenv("DATABASE_URL")

# Enquanto estiver depurando, mantenha 1. Suba para 31 so quando a pipeline estabilizar.
LIMITE_STARTUPS = 10
PAUSA_ENTRE_CHAMADAS = 3  # segundos, para respeitar o limite de tokens/minuto do tier gratuito


class Estado(TypedDict):
    consulta: str                     # o que o usuario pediu, em linguagem natural
    filtros: Dict[str, Any]           # criterios de busca extraidos da consulta
    startups: List[Dict[str, Any]]    # empresas recuperadas do banco
    documentos: List[Dict[str, Any]]  # documentos das empresas recuperadas
    perfis: List[Dict[str, Any]]      # perfil estruturado, classificado e validado
    trechos_nvidia: Dict[str, Any]    # trechos da base NVIDIA recuperados por startup
    briefing: str                     # relatorio executivo final em markdown


def conectar():
    return psycopg2.connect(DB, cursor_factory=psycopg2.extras.RealDictCursor)


class RespostaVazia(Exception):
    """O modelo devolveu conteudo vazio. E transitorio, vale repetir."""


class RespostaNaoEhJson(Exception):
    """O modelo respondeu algo que nao e JSON. Repetir a chamada igual nao resolve."""


@retry(
    wait=wait_exponential(min=5, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_not_exception_type(RespostaNaoEhJson),
)
def chamar_llm(prompt: str) -> str:
    """Chamada crua ao modelo, com retry para falha de rede, 429 e resposta vazia.

    Resposta vazia acontece quando o modelo gasta o orcamento de tokens no
    raciocinio interno e nao sobra nada para o conteudo, ou quando o provedor
    corta a resposta por limite de taxa sem devolver erro HTTP. E transitorio,
    entao vale repetir, ao contrario de resposta malformada.
    """
    resposta = llm.invoke(prompt)
    texto = (resposta.content or "").strip()
    if not texto:
        motivo = resposta.response_metadata.get("finish_reason", "desconhecido")
        raise RespostaVazia(f"modelo devolveu conteudo vazio (finish_reason={motivo})")
    return texto


def causa_real(erro: Exception) -> str:
    """Desembrulha o RetryError do tenacity para mostrar o erro que de fato ocorreu.

    Sem isso, toda falha aparece como "RetryError", que nao diz nada: pode ser
    limite de taxa, chave invalida, parametro rejeitado pela API ou timeout.
    """
    interno = getattr(erro, "last_attempt", None)
    if interno is not None and interno.failed:
        real = interno.exception()
        return f"{type(real).__name__}: {str(real)[:300]}"
    return f"{type(erro).__name__}: {str(erro)[:300]}"


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
- copie o trecho inteiro e continuo, sem cortar com reticencias e sem juntar pedacos separados do documento

### BLOCO 5 - FORMATO
Responda apenas com o JSON, sem texto antes ou depois, sem cerca de markdown."""

        # Uma empresa que falha nao pode derrubar a execucao inteira. Numa rodada
        # de 31 empresas, perder tudo no item 28 por causa de um JSON malformado
        # custaria a rodada toda. Registra a falha, segue para a proxima.
        try:
            perfil = pedir_json(prompt)
        except Exception as erro:
            print(f"[extractor] FALHOU em {s['nome']}: {causa_real(erro)}")
            perfil = {
                "tecnologias_citadas": [], "sinais_de_uso_de_ia": [],
                "dados_proprietarios": [], "possiveis_gargalos_tecnicos": [],
                "evidencias": [], "erro_extracao": f"{type(erro).__name__}",
            }
        perfil["startup_id"] = s["id"]
        perfil["nome"] = s["nome"]
        perfis.append(perfil)
        print(f"[extractor] perfil montado: {s['nome']}")
        time.sleep(PAUSA_ENTRE_CHAMADAS)

    return {"perfis": perfis}

# ------------------------------------------------------------------ NO 5
def startup_classifier(estado: Estado) -> Dict[str, Any]:
    """Classifica cada empresa como AI-native, AI-enabled ou non-AI."""
    perfis = []

    for perfil in estado["perfis"]:
        # O classificador NAO pode ver evidencia reprovada pelo validador.
        # Antes, json.dumps(perfil) entregava o perfil inteiro, incluindo o campo
        # evidencias_rejeitadas, e o modelo usava aquelas afirmacoes como se
        # fossem validas. Isso anulava o proposito de validar antes de classificar.
        perfil_para_julgar = {
            k: v for k, v in perfil.items()
            if k not in ("evidencias_rejeitadas", "startup_id")
        }
        perfil_para_julgar["nota_sobre_evidencias"] = (
            f"{len(perfil.get('evidencias', []))} evidencias foram verificadas contra "
            f"os documentos originais; {len(perfil.get('evidencias_rejeitadas', []))} "
            f"foram descartadas por nao serem confirmaveis. Considere apenas as "
            f"afirmacoes sustentadas pelas evidencias listadas."
        )

        prompt = f"""### BLOCO 1 - PAPEL E TAREFA
{{Voce e um analista que classifica empresas em tres niveis de maturidade em IA:
AI-native (a IA e o mecanismo central do produto), AI-enabled (a IA e uma camada
sobre um produto que existiria sem ela) e non-AI (nao ha evidencia de uso de IA).
Voce decide com base exclusivamente no perfil tecnico recebido.}}

### BLOCO 2 - CONTEXTO
Empresa: {perfil['nome']}
Perfil tecnico extraido dos documentos:
{json.dumps(perfil_para_julgar, ensure_ascii=False, indent=2)}

### BLOCO 3 - SCHEMA
Responda EXATAMENTE neste formato JSON:
{{{{"classificacao": "AI-native | AI-enabled | non-AI",
  "confianca": "alta | media | baixa",
  "justificativa": "por que essa classificacao, citando o que no perfil sustenta",
  "sinais_a_favor": ["..."],
  "sinais_contra": ["..."]}}}}

### BLOCO 4 - REGRAS
{{
- classifique como AI-native quando o perfil indicar que sem o modelo de IA nao
  existiria produto: modelo proprio, dado proprietario alimentando o modelo, ou
  a saida da IA sendo o proprio entregavel vendido ao cliente
- classifique como AI-enabled quando o produto principal existiria sem a IA e ela
  aparece como recurso adicional, melhoria de fluxo ou camada de atendimento
- classifique como non-AI quando nao houver evidencia de uso de IA no perfil
- se o perfil tiver menos de dois sinais de uso de IA e menos de duas tecnologias
  citadas, use confianca "baixa" e diga na justificativa que a limitacao vem da
  escassez dos documentos disponiveis, nao necessariamente da empresa
  - afirmacao de posicionamento institucional (ex: "somos AI first", "plataforma de IA")
  e sinal FRACO. Ela so sustenta AI-native se houver no mesmo perfil evidencia de
  mecanismo que a corrobore: modelo proprio, dado proprietario ou pipeline descrito.
  Sozinha, registre em sinais_a_favor mas nao deixe que ela mude a classificacao
  - use exclusivamente o conteudo do perfil recebido. Se voce reconhece a empresa e
  sabe de algo que nao esta no perfil, ignore. Nao preencha lacuna com conhecimento
  proprio nem com suposicao sobre o setor
  - preencha sinais_contra com pelo menos um item, sempre. Se nao encontrar nenhum
  argumento contra a classificacao escolhida, escreva o que faltaria no perfil para
  tornar a decisao mais segura
  - aplique a regra de desempate conservadora APENAS quando a confianca for baixa.
  Com confianca alta ou media, comprometa-se com a categoria que a evidencia sustenta
  - basta UM dos tres criterios a seguir para classificar como AI-native, nao os tres:
  (a) modelo proprio, (b) dado proprietario alimentando o modelo, (c) a saida da IA
  e o entregavel vendido ao cliente
- o criterio (b) so esta atendido quando dados_proprietarios indicar um ativo que JA
  EXISTE: volume declarado, historico acumulado, base de registros propria ou dado
  gerado pela operacao. Intencao de construir ("vamos estruturar dados", "investimento
  sera direcionado a organizar dados") NAO atende o criterio (b): registre em
  sinais_a_favor como sinal fraco e nao deixe que sozinha mude a classificacao
- aplique a regra de desempate conservadora APENAS quando a confianca for baixa;
  com confianca alta, comprometa-se com a categoria que a evidencia sustenta
  - considere como dado proprietario: bases historicas da propria empresa, volume de
  registros acumulados, dados de clientes usados para treinar ou calibrar modelo,
  e integracoes que geram dado exclusivo
  - o campo "trecho" so pode ser copiado do texto que aparece sob "Documentos
  disponiveis". Nunca cite os campos Empresa, Setor ou Descricao do Bloco 2,
  eles vem do banco de dados e nao de um documento com fonte
  - nao inclua em "tecnologias_citadas": nomes de parceiros ou clientes, normas e
  regulacoes (HIPAA, GDPR, LGPD), nem certificacoes
  }}

### BLOCO 5 - FORMATO
Responda apenas com o JSON, sem texto antes ou depois, sem cerca de markdown."""

        try:
            resultado = pedir_json(prompt)
        except Exception as erro:
            print(f"[classifier] FALHOU em {perfil['nome']}: {causa_real(erro)}")
            resultado = {
                "classificacao": "indeterminado", "confianca": "baixa",
                "justificativa": f"falha na chamada ao modelo: {type(erro).__name__}",
                "sinais_a_favor": [], "sinais_contra": [],
            }
        perfil["classificacao"] = resultado
        perfis.append(perfil)
        print(f"[classifier] {perfil['nome']}: {resultado.get('classificacao')} "
              f"(confianca {resultado.get('confianca')})")
        time.sleep(PAUSA_ENTRE_CHAMADAS)

    return {"perfis": perfis}

# ------------------------------------------------------------------ NO 6
# Instancia unica: carregar o Chroma e montar o indice BM25 a cada chamada seria
# desperdicio, entao a busca e criada uma vez e reaproveitada por todas as startups.
_busca = None


def nvidia_rag(estado: Estado) -> Dict[str, Any]:
    """Recupera, para cada empresa, os trechos da base NVIDIA que respondem aos gargalos dela."""
    global _busca
    if _busca is None:
        _busca = BuscaHibrida()

    trechos_por_startup = {}

    for perfil in estado["perfis"]:
        # A consulta e gerada em INGLES de proposito: 26 dos 33 documentos da base
        # sao documentacao tecnica em ingles, e o embedding padrao do Chroma e
        # monolingue. Ver a docstring de rag.busca.buscar.
        prompt_consulta = f"""Voce monta consultas de busca para uma base tecnica em ingles.

Perfil da empresa:
- setor: {perfil.get('nome')}
- tecnologias citadas: {perfil.get('tecnologias_citadas')}
- sinais de uso de IA: {perfil.get('sinais_de_uso_de_ia')}
- possiveis gargalos tecnicos: {perfil.get('possiveis_gargalos_tecnicos')}

Escreva UMA consulta de busca em ingles, de 8 a 15 palavras, descrevendo o problema
tecnico que essa empresa provavelmente enfrenta (inferencia, dados, voz, seguranca,
simulacao, governanca). Nao cite nomes de produtos NVIDIA na consulta.

Responda apenas com o JSON: {{{{"consulta_en": "..."}}}}"""

        try:
            consulta_en = pedir_json(prompt_consulta)["consulta_en"]
        except Exception as erro:
            print(f"[rag] FALHOU ao montar consulta de {perfil['nome']}: {causa_real(erro)}")
            consulta_en = " ".join(perfil.get("tecnologias_citadas") or []) or perfil["nome"]
        consulta_pt = " ".join(perfil.get("possiveis_gargalos_tecnicos") or []) or perfil["nome"]

        resultados = _busca.buscar(consulta_pt, consulta_en=consulta_en, k_final=5)
        trechos_por_startup[perfil["startup_id"]] = {
            "consulta_en": consulta_en,
            "trechos": resultados,
        }
        tecnologias = sorted({r["tecnologia"] for r in resultados})
        print(f"[rag] {perfil['nome']}: {tecnologias}")
        time.sleep(PAUSA_ENTRE_CHAMADAS)

    return {"trechos_nvidia": trechos_por_startup}



# ------------------------------------------------------------------ NO 7
def recommendation_agent(estado: Estado) -> Dict[str, Any]:
    """Cruza o perfil verificado da empresa com os trechos da base NVIDIA."""
    perfis = []

    for perfil in estado["perfis"]:
        dados_rag = estado.get("trechos_nvidia", {}).get(perfil["startup_id"], {})
        trechos = dados_rag.get("trechos", [])

        if not trechos:
            perfil["recomendacoes"] = {
                "recomendacoes": [],
                "sem_recomendacao": "o RAG nao retornou trechos para esta empresa",
            }
            perfis.append(perfil)
            print(f"[recommendation] {perfil['nome']}: sem trechos do RAG")
            continue

        contexto_rag = "\n\n".join(
            f"[{t['tecnologia']} | categoria: {t['categoria']} | fonte: {t['url_fonte']}]\n{t['texto']}"
            for t in trechos
        )
        classificacao = perfil.get("classificacao", {})
        perfil_verificado = {
            k: v for k, v in perfil.items()
            if k not in ("evidencias_rejeitadas", "classificacao", "startup_id", "recomendacoes")
        }

        prompt = f"""### BLOCO 1 - PAPEL E TAREFA
Voce e um assessor de negocios do gerente de Startups & VC da NVIDIA Brasil. Sua tarefa e recomentdar tecnologias NVIDIA que podem ajudar a empresa a superar gargalos tecnicos, com base no perfil tecnico verificado e nos trechos recuperados da base de conhecimento da NVIDIA.

### BLOCO 2 - CONTEXTO
Empresa: {perfil['nome']}
Classificacao: {classificacao.get('classificacao')} (confianca {classificacao.get('confianca')})
Justificativa da classificacao: {classificacao.get('justificativa')}

Perfil tecnico verificado:
{json.dumps(perfil_verificado, ensure_ascii=False, indent=2)}

Trechos recuperados da base de conhecimento NVIDIA:
{contexto_rag}

### BLOCO 3 - SCHEMA
Responda EXATAMENTE neste formato JSON:
{{"recomendacoes": [
  {{"tecnologia": "nome exato da tecnologia NVIDIA",
    "justificativa_tecnica": "que gargalo concreto do perfil ela resolve",
    "justificativa_negocio": "por que importa para a empresa e para a NVIDIA",
    "prioridade": "alta | media | baixa",
    "complexidade": "baixa | media | alta",
    "proxima_acao": "o proximo passo concreto do gerente",
    "evidencias": [{{"origem": "perfil | base_nvidia", "trecho": "...", "url_fonte": "..."}}]
  }}
 ],
 "sem_recomendacao": null}}

### BLOCO 4 - REGRAS
- so recomende tecnologia que aparece nos trechos acima. Nao cite produto NVIDIA
  de conhecimento proprio que nao esteja na base recuperada
- toda justificativa_tecnica precisa apontar um item concreto de
  possiveis_gargalos_tecnicos, tecnologias_citadas ou dados_proprietarios do perfil
- no maximo 3 recomendacoes, ordenadas da mais prioritaria para a menos
- se nao houver base suficiente, devolva "recomendacoes": [] e preencha
  "sem_recomendacao" explicando o que faltou
- a classificacao define profundidade e prioridade, nao a escolha da tecnologia:
  AI-native recebe recomendacao tecnica especifica com prioridade alta; AI-enabled
  recebe recomendacao antecipatoria, ligada ao momento em que o gargalo vai aparecer,
  com prioridade media; non-AI nao recebe recomendacao de stack tecnico
  - para empresa classificada como non-AI, recomende o programa NVIDIA Inception
  quando houver trecho da base que o sustente, e explique o encaixe em vez de
  recomendar tecnologia de stack
- quando o perfil nao revelar gargalo por falta de informacao, e nao por ausencia
  de problema, nao recomende: preencha "sem_recomendacao" dizendo o que precisaria
  ser descoberto sobre a empresa
  - recuse quando nenhum trecho recuperado se conectar a um gargalo concreto do perfil
- recuse quando a unica base para recomendar for afirmacao de marketing da empresa
- recuse quando taxa_validacao for menor que 0.5, porque recomendar sobre evidencia
  nao confirmada propagaria alucinacao para um documento em que um humano vai agir
  - complexidade "baixa": a adocao nao exige reescrever codigo (biblioteca drop-in,
  endpoint compativel com o que a empresa ja usa, container pronto)
- complexidade "media": exige reescrever parte do pipeline ou empacotar o modelo
- complexidade "alta": exige mudar infraestrutura, provisionar GPU ou treinar modelo
- o nivel escolhido precisa ser sustentado por algo dito no trecho recuperado. Se o
  trecho nao falar de esforco de adocao, use "media" e diga na justificativa que o
  nivel foi estimado por falta de informacao na fonte

### BLOCO 5 - FORMATO
Responda apenas com o JSON, sem texto antes ou depois, sem cerca de markdown."""

        try:
            resultado = pedir_json(prompt)
        except Exception as erro:
            print(f"[recommendation] FALHOU em {perfil['nome']}: {causa_real(erro)}")
            resultado = {"recomendacoes": [], "sem_recomendacao": f"falha: {type(erro).__name__}"}

        perfil["recomendacoes"] = resultado
        perfis.append(perfil)
        nomes = [r.get("tecnologia") for r in resultado.get("recomendacoes", [])]
        print(f"[recommendation] {perfil['nome']}: {nomes or 'sem recomendacao'}")
        time.sleep(PAUSA_ENTRE_CHAMADAS)

    return {"perfis": perfis}



# ------------------------------------------------------------------ NO 8
def briefing_agent(estado: Estado) -> Dict[str, Any]:
    """Gera o briefing executivo consolidado para o gerente de Startups & VCs.

    Diferente dos outros nos, faz UMA unica chamada para o lote inteiro em vez de
    uma por empresa. Duas razoes: briefing executivo precisa comparar empresas
    entre si, o que exige ver todas juntas; e uma chamada consome uma fracao dos
    tokens que 31 chamadas consumiriam, o que importa no tier gratuito.

    Para caber no orcamento, monta um resumo compacto de cada empresa em vez de
    mandar os perfis completos.
    """
    perfis = estado["perfis"]
    if not perfis:
        return {"briefing": "nenhuma empresa processada"}

    resumo = []
    for p in perfis:
        cls = p.get("classificacao", {})
        recs = (p.get("recomendacoes") or {}).get("recomendacoes", [])
        resumo.append({
            "empresa": p.get("nome"),
            "classificacao": cls.get("classificacao"),
            "confianca": cls.get("confianca"),
            "taxa_validacao": p.get("taxa_validacao"),
            "gargalos": p.get("possiveis_gargalos_tecnicos", [])[:2],
            "recomendacoes": [
                {"tecnologia": r.get("tecnologia"), "prioridade": r.get("prioridade"),
                 "complexidade": r.get("complexidade"), "porque": r.get("justificativa_negocio", "")[:180]}
                for r in recs
            ],
        })

    contagem = {}
    for p in perfis:
        c = (p.get("classificacao") or {}).get("classificacao", "indeterminado")
        contagem[c] = contagem.get(c, 0) + 1

    prompt = f"""### BLOCO 1 - PAPEL E TAREFA
Voce escreve o briefing executivo do NVIDIA Startup AI Radar.

Quem le e o gerente de Startups & VCs da NVIDIA no Brasil. Ele tem pouco tempo, ja
conhece o mercado, e usa este texto para decidir quais startups procurar primeiro e
com que argumento. Ele nao precisa de explicacao sobre o que e IA, nem de introducao
sobre a importancia do tema.

Sua tarefa e consolidar o que o sistema analisou em um texto de decisao: o que o
conjunto mostra, quem priorizar, com qual tecnologia, e sobre quem ainda ha duvida.

Toda afirmacao deste briefing vem de evidencia que passou pelo validador do sistema.
Onde a evidencia foi fraca, isso e dito explicitamente em vez de ser omitido: um
briefing que esconde incerteza faz o gerente perder tempo em conversas mal fundamentadas.

### BLOCO 2 - CONTEXTO
Empresas analisadas: {len(perfis)}
Distribuicao por classificacao: {json.dumps(contagem, ensure_ascii=False)}

Dados consolidados:
{json.dumps(resumo, ensure_ascii=False, indent=2)}

### BLOCO 3 - FORMATO DE SAIDA
Escreva em markdown, em portugues, com esta estrutura:

## Panorama
Dois ou tres paragrafos sobre o que a analise mostrou no conjunto.

## Prioridades de abordagem
Tabela com as empresas mais promissoras: empresa, classificacao, tecnologia
recomendada, prioridade e o motivo em uma linha.

## Oportunidades por tecnologia
Quais tecnologias NVIDIA aparecem com mais frequencia e em que tipo de empresa.

## Ressalvas
Empresas com taxa de validacao baixa ou confianca baixa, deixando claro que sobre
elas o sistema tem menos certeza e por que.

## Proximos passos
Tres a cinco acoes concretas para o gerente, em ordem de prioridade.

### BLOCO 4 - REGRAS
- nao invente numero, nome de empresa ou tecnologia que nao esteja nos dados acima
- empresa com taxa_validacao abaixo de 0.5 vai para "Ressalvas", nunca para
  "Prioridades de abordagem"
- seja direto: quem le tem pouco tempo e decide com base neste texto
- nao escreva introducao nem conclusao generica, comece pelo Panorama

### BLOCO 5 - FORMATO
Responda apenas com o markdown do briefing, sem cerca de codigo em volta."""

    try:
        texto = chamar_llm(prompt)
    except Exception as erro:
        print(f"[briefing] FALHOU: {causa_real(erro)}")
        texto = f"# Briefing nao gerado\n\nFalha na chamada ao modelo: {causa_real(erro)}"

    caminho = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "briefing.md"
    )
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)

    print(f"[briefing] gerado com {len(texto)} caracteres, salvo em data/briefing.md")
    return {"briefing": texto}


# ------------------------------------------------------------------ GRAFO
grafo = StateGraph(Estado)
grafo.add_node("query_planner", query_planner)
grafo.add_node("retriever", retriever)
grafo.add_node("extractor", extractor)
grafo.add_node("evidence_validator", evidence_validator)
grafo.add_node("startup_classifier", startup_classifier)
grafo.add_node("nvidia_rag", nvidia_rag)
grafo.add_node("recommendation_agent", recommendation_agent)
grafo.add_node("briefing_agent", briefing_agent)

grafo.add_edge(START, "query_planner")
grafo.add_edge("query_planner", "retriever")
grafo.add_edge("retriever", "extractor")
# O validador roda ANTES do classificador de proposito: o classificador so deve
# raciocinar sobre evidencia verificada, nunca sobre afirmacao rejeitada.
grafo.add_edge("extractor", "evidence_validator")
grafo.add_edge("evidence_validator", "startup_classifier")
grafo.add_edge("startup_classifier", "nvidia_rag")
grafo.add_edge("nvidia_rag", "recommendation_agent")
grafo.add_edge("recommendation_agent", "briefing_agent")
grafo.add_edge("briefing_agent", END)

pipeline = grafo.compile()


if __name__ == "__main__":
    resultado = pipeline.invoke({
        "consulta": "startups de saude que usam IA no diagnostico",
        "filtros": {},
        "startups": [],
        "documentos": [],
        "perfis": [],
        "trechos_nvidia": {},
        "briefing": "",
    })
    print("\n===== BRIEFING =====")
    print(resultado.get("briefing", "")[:1500])
    print("\n===== PERFIS =====")
    print(json.dumps(resultado["perfis"], indent=2, ensure_ascii=False))
