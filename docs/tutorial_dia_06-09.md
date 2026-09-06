# Tutorial do dia 06/09: dados no banco e primeira pipeline rodando

## Antes de começar: onde você está de verdade

O repositório tem só o commit inicial. As pastas `agents/`, `rag/` e `app/` estão vazias. Os dias 04/09 e 05/09 não produziram código.

Sobrou hoje (06/09), domingo 07, segunda 08 e terça 09 até 23:59. São **3 dias e meio para 5 entregáveis, um vídeo e a documentação**.

Isso ainda é viável, mas só com um cronograma novo e uma regra: **nada de perfeccionismo antes de existir uma versão que roda**. Um pipeline simples que funciona ponta a ponta vale muito mais na nota do que três agentes sofisticados que nunca rodaram juntos. Lembre que "projeto que não executa" é critério eliminatório.

### Cronograma revisado

| Dia | Entrega mínima |
|---|---|
| **06/09 (hoje)** | Postgres carregado + pipeline LangGraph rodando com 3 agentes |
| 07/09 | Classifier + Evidence Validator + RAG NVIDIA com reranking |
| 08/09 | Motor de recomendação + Briefing + interface Streamlit + README |
| 09/09 | Gravar e revisar o vídeo, commit final, entregar antes das 23:59 |

Se algum dia atrasar, o que se corta é a interface (vale só 5 pontos) e o refinamento dos prompts. O que **não** se corta: pipeline que executa, RAG com reranking, e o vídeo.

### Dois diferenciais quase de graça (valem 5 pontos)

Você já tem dois candidatos a "diferencial do projeto" sem trabalho extra grande:

1. **Critério de fonte acessível para IA.** Toda a base foi montada testando se cada URL podia ser lida por uma IA; 50 fontes foram reprovadas e a Neurotech foi descartada inteira por bloquear com 403. Isso é uma decisão de arquitetura de dados defensável e pouca gente vai ter.
2. **Medição de acurácia do classificador.** O arquivo `docs/perfil_hipotese.md` tem a hipótese de perfil das 31 empresas. Quando o Classifier Agent estiver rodando, compare a saída dele com essa tabela e calcule o acerto. Mostrar métrica no vídeo, em vez de só afirmar que funciona, pesa.

---

## Etapa 0: salvar o que está pendente (5 min)

Você editou `.env.example`, `.gitignore`, `README.md`, `docker-compose.yml` e `requirements.txt` mas nunca commitou. Os CSVs também estão fora do Git.

```bash
cd ~/Documents/Inteli/Clubes/inteli-academy/case-nvidia
git add .
git commit -m "adiciona base de startups curada (31 empresas, 93 documentos)"
git push
```

Confira depois que `.env` **não** apareceu na lista do commit:

```bash
git ls-files | grep -c "^\.env$"
```

Tem que responder `0`.

---

## Etapa 1: subir o Postgres e carregar os dados (45 min)

### 1.1 Suba o banco

Abra o Docker Desktop, espere a baleia estabilizar, e no Git Bash:

```bash
docker compose up -d
docker ps
```

Você deve ver o container `startups_db` rodando.

### 1.2 Crie o arquivo de schema

Crie `data/schema.sql`:

```sql
DROP TABLE IF EXISTS documentos;
DROP TABLE IF EXISTS startups;

CREATE TABLE startups (
    id              TEXT PRIMARY KEY,
    nome            TEXT NOT NULL,
    site            TEXT,
    setor           TEXT,
    estagio         TEXT,
    localizacao     TEXT,
    descricao_curta TEXT,
    ano_fundacao    TEXT,
    tamanho_time    TEXT
);

CREATE TABLE documentos (
    id              TEXT PRIMARY KEY,
    startup_id      TEXT REFERENCES startups(id),
    tipo            TEXT,
    titulo          TEXT,
    conteudo_texto  TEXT,
    url_fonte       TEXT,
    data_publicacao TEXT
);

CREATE INDEX idx_documentos_startup ON documentos(startup_id);
CREATE INDEX idx_startups_setor ON startups(setor);
```

**Por que `ano_fundacao` é TEXT e não INTEGER?** Porque a Cuponeria tem o valor `2011 (fontes divergem: Empreendedor indica outubro de 2011 e Projeto Draft indica 2012)`. Se você declarar como número, a carga quebra. Manter a incerteza registrada é mais honesto do que forçar um número, e isso é assunto bom para o vídeo: você tratou conflito de fonte em vez de esconder.

### 1.3 Crie o script de carga

Crie `data/load_csv.py`:

```python
import csv, os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/startups_db")
AQUI = os.path.dirname(os.path.abspath(__file__))

def carregar(cur, arquivo, tabela, colunas):
    caminho = os.path.join(AQUI, arquivo)
    with open(caminho, encoding="utf-8") as f:
        linhas = [tuple(r[c] for c in colunas) for r in csv.DictReader(f)]
    marcadores = ",".join(["%s"] * len(colunas))
    cur.executemany(
        f"INSERT INTO {tabela} ({','.join(colunas)}) VALUES ({marcadores})",
        linhas,
    )
    print(f"{tabela}: {len(linhas)} linhas inseridas")

conn = psycopg2.connect(DB)
cur = conn.cursor()

with open(os.path.join(AQUI, "schema.sql"), encoding="utf-8") as f:
    cur.execute(f.read())
print("schema criado")

carregar(cur, "startups.csv", "startups",
         ["id","nome","site","setor","estagio","localizacao",
          "descricao_curta","ano_fundacao","tamanho_time"])
carregar(cur, "documentos.csv", "documentos",
         ["id","startup_id","tipo","titulo","conteudo_texto",
          "url_fonte","data_publicacao"])

conn.commit()

cur.execute("SELECT COUNT(*) FROM startups")
print("total startups no banco:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM documentos")
print("total documentos no banco:", cur.fetchone()[0])

cur.close()
conn.close()
```

### 1.4 Rode

```bash
source .venv/Scripts/activate
python data/load_csv.py
```

**Checkpoint:** tem que imprimir `total startups no banco: 31` e `total documentos no banco: 93`. Se der erro de conexão, o Postgres não subiu; volte ao `docker ps`.

---

## Etapa 2: primeira chamada ao NVIDIA NIM (20 min)

### 2.1 Instale o pacote

Ele não está no seu `requirements.txt` ainda:

```bash
pip install langchain-nvidia-ai-endpoints
echo "langchain-nvidia-ai-endpoints" >> requirements.txt
```

### 2.2 Coloque a chave no `.env`

Abra o `.env` (o de verdade, não o `.example`) e garanta que tem:

```
NVIDIA_API_KEY=nvapi-sua-chave-aqui
COHERE_API_KEY=sua-chave-cohere
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/startups_db
```

A chave da NVIDIA sai em build.nvidia.com, começa com `nvapi-`. O pacote lê a variável `NVIDIA_API_KEY` sozinho, você não precisa passar no código.

### 2.3 Teste

Crie `agents/teste_nim.py`:

```python
import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

llm = ChatNVIDIA(model="meta/llama-3.3-70b-instruct", temperature=0)
resposta = llm.invoke("Responda apenas: conexao ok")
print(resposta.content)
```

```bash
python agents/teste_nim.py
```

Se o modelo que escolhi não existir mais no catálogo, descubra os disponíveis assim:

```python
from langchain_nvidia_ai_endpoints import ChatNVIDIA
for m in ChatNVIDIA.get_available_models()[:30]:
    print(m.id)
```

**Checkpoint:** precisa imprimir a resposta do modelo sem erro de autenticação.

---

## Etapa 3: entender LangGraph em 10 minutos

Não pule esta parte. Você vai precisar explicar isso no vídeo.

Um grafo do LangGraph tem três peças:

1. **State (estado):** um dicionário tipado que atravessa a pipeline inteira. Cada nó lê o estado, faz seu trabalho, e devolve as chaves que quer atualizar. É a memória compartilhada entre os agentes.
2. **Node (nó):** uma função Python comum que recebe o estado e devolve um pedaço de estado. Cada agente do TAPI vira um nó.
3. **Edge (aresta):** a ligação que diz qual nó roda depois de qual. `START` e `END` são os extremos.

A diferença para uma corrente simples de prompts, e é isso que o TAPI valoriza na seção 5.1: com grafo você consegue condicionar caminhos (se o Evidence Validator reprovar, volta para o Extractor), gravar checkpoints e inspecionar o estado a cada passo. Guarde essa frase, ela cabe bem no vídeo.

---

## Etapa 4: a pipeline mínima com 3 agentes (2 a 3 h)

Aqui está o esqueleto. **A parte mecânica está pronta; o que está marcado com `VOCÊ ESCREVE` é seu trabalho**, e é exatamente o que a banca vai querer que você explique.

Crie `agents/pipeline.py`:

```python
import os, json
from typing import TypedDict, List, Dict, Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

llm = ChatNVIDIA(model="meta/llama-3.3-70b-instruct", temperature=0)
DB = os.getenv("DATABASE_URL")


class Estado(TypedDict):
    consulta: str                    # o que o usuario pediu, em linguagem natural
    filtros: Dict[str, Any]          # criterios de busca extraidos da consulta
    startups: List[Dict[str, Any]]   # empresas recuperadas do banco
    documentos: List[Dict[str, Any]] # documentos das empresas recuperadas
    perfis: List[Dict[str, Any]]     # perfil estruturado de cada empresa


def conectar():
    return psycopg2.connect(DB, cursor_factory=psycopg2.extras.RealDictCursor)


def pedir_json(prompt: str) -> Any:
    """Chama o LLM e devolve JSON. Util porque modelos gostam de embrulhar em ```."""
    bruto = llm.invoke(prompt).content.strip()
    if bruto.startswith("```"):
        bruto = bruto.split("```")[1]
        if bruto.startswith("json"):
            bruto = bruto[4:]
    return json.loads(bruto.strip())


# ---------------------------------------------------------------- NO 1
def query_planner(estado: Estado) -> Dict[str, Any]:
    """Transforma a consulta em linguagem natural em criterios de busca."""
    # VOCÊ ESCREVE: o prompt que pede ao modelo para devolver um JSON com
    # as chaves setor, estagio e palavras_chave a partir de estado["consulta"].
    # Dica: mande a lista de setores que existem no seu banco dentro do prompt,
    # senao o modelo inventa setores que nao existem. Rode isto para ver a lista:
    #   SELECT DISTINCT setor FROM startups;
    prompt = f"""..."""
    filtros = pedir_json(prompt)
    return {"filtros": filtros}


# ---------------------------------------------------------------- NO 2
def retriever(estado: Estado) -> Dict[str, Any]:
    """Busca no Postgres as empresas que batem com os filtros."""
    filtros = estado["filtros"]
    conn = conectar()
    cur = conn.cursor()

    # VOCÊ ESCREVE: a query SQL que filtra por setor e/ou palavras-chave.
    # Comece simples (ILIKE em setor e descricao_curta) e melhore depois.
    # Use sempre parametros %s, nunca concatene string na query.
    cur.execute("SELECT * FROM startups LIMIT 5")
    startups = [dict(r) for r in cur.fetchall()]

    ids = [s["id"] for s in startups]
    documentos = []
    if ids:
        cur.execute(
            "SELECT * FROM documentos WHERE startup_id = ANY(%s)", (ids,)
        )
        documentos = [dict(r) for r in cur.fetchall()]

    cur.close(); conn.close()
    print(f"[retriever] {len(startups)} startups, {len(documentos)} documentos")
    return {"startups": startups, "documentos": documentos}


# ---------------------------------------------------------------- NO 3
def extractor(estado: Estado) -> Dict[str, Any]:
    """Le o texto bruto dos documentos e monta um perfil estruturado."""
    perfis = []
    for s in estado["startups"]:
        docs = [d for d in estado["documentos"] if d["startup_id"] == s["id"]]
        textos = "\n\n".join(
            f"[{d['tipo']} | fonte: {d['url_fonte']}]\n{d['conteudo_texto']}"
            for d in docs
        )
        # VOCÊ ESCREVE: o prompt que extrai do texto bruto um JSON com, no minimo:
        #   tecnologias_citadas, sinais_de_uso_de_ia, dados_proprietarios,
        #   possiveis_gargalos_tecnicos, evidencias (com a url que sustenta cada uma)
        # A rastreabilidade e requisito do TAPI: toda afirmacao precisa apontar fonte.
        prompt = f"""..."""
        perfil = pedir_json(prompt)
        perfil["startup_id"] = s["id"]
        perfil["nome"] = s["nome"]
        perfis.append(perfil)
        print(f"[extractor] perfil montado: {s['nome']}")
    return {"perfis": perfis}


# ---------------------------------------------------------------- GRAFO
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
        "filtros": {}, "startups": [], "documentos": [], "perfis": [],
    })
    print(json.dumps(resultado["perfis"], indent=2, ensure_ascii=False))
```

### Ordem de trabalho sugerida dentro desta etapa

1. Rode o arquivo como está, com os prompts vazios, só para ver o grafo executar e quebrar no primeiro `json.loads`. Entender onde quebra é aprendizado, não erro.
2. Escreva o prompt do `query_planner` e rode de novo até ele devolver JSON válido.
3. Escreva a query SQL do `retriever`.
4. Escreva o prompt do `extractor`. **Teste com uma empresa só primeiro** (coloque `LIMIT 1` no SQL), porque cada rodada gasta cota de API.

### Economia de cota

Enquanto estiver depurando, trabalhe com 1 ou 2 empresas. Só rode nas 31 quando a pipeline estiver estável. Sua chave da Cohere tem teto de 1.000 chamadas no mês inteiro, e você ainda vai precisar dela amanhã para embeddings e reranking.

---

## Etapa 5: fechar o dia (10 min)

```bash
git add .
git commit -m "pipeline langgraph inicial com query planner, retriever e extractor"
git push
```

**Você terminou o dia bem se:** o comando `python agents/pipeline.py` roda do início ao fim e imprime pelo menos um perfil estruturado em JSON, com evidências apontando URLs reais da sua base.

Se chegar nisso hoje, o resto da semana é só repetir o padrão: cada agente novo é mais um nó no mesmo grafo.

---

## Uma coisa para anotar enquanto trabalha

Mantenha um arquivo `docs/decisoes.md` e escreva uma linha toda vez que tomar uma decisão técnica: por que Postgres e não SQLite, por que Chroma e não Qdrant, por que NVIDIA NIM como LLM, por que descartou fontes bloqueadas. São 2 minutos por dia e é literalmente o roteiro do seu vídeo depois, além de contar no critério de documentação (10 pontos).
