"""
Busca hibrida na base de conhecimento NVIDIA, com reranking.

Pipeline de recuperacao, conforme a secao 5.3 do TAPI:
  1. busca vetorial no Chroma (semantica: acha texto parecido em significado)
  2. busca lexical BM25 (acha o termo exato: "TensorRT-LLM", "cuDF")
  3. fusao das duas listas por Reciprocal Rank Fusion
  4. reranking dos finalistas com Cohere Rerank
  5. devolve os trechos com a url_fonte para citacao

As duas buscas se complementam: a vetorial entende "meu modelo esta lento"
sem que a palavra "latencia" apareca; a lexical acerta nomes de produto que
o embedding trata como token raro.
"""

import os
import re
import json

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
import cohere

load_dotenv()

AQUI = os.path.dirname(os.path.abspath(__file__))
PERSIST = os.path.join(AQUI, "chroma_db")
CHUNKS_JSON = os.path.join(AQUI, "chunks.json")
COLECAO = "nvidia"

# Quantos candidatos cada busca traz antes da fusao.
K_VETORIAL = 25
K_LEXICAL = 25
# Quantos finalistas vao para o reranker (quanto maior, mais caro e mais lento).
K_RERANK = 20
# Quantos trechos a funcao devolve no fim.
K_FINAL = 5

MODELO_RERANK = "rerank-v4.0-pro"

# Constante do Reciprocal Rank Fusion. 60 e o valor usado no artigo original;
# ele amortece a diferenca entre as primeiras posicoes das duas listas.
RRF_K = 60


def tokeniza(texto: str):
    return re.findall(r"\w+", texto.lower())


class BuscaHibrida:
    def __init__(self):
        cliente = chromadb.PersistentClient(path=PERSIST)
        self.colecao = cliente.get_collection(
            COLECAO, embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
        with open(CHUNKS_JSON, encoding="utf-8") as f:
            self.chunks = json.load(f)
        self.por_id = {c["id"]: c for c in self.chunks}
        self.bm25 = BM25Okapi([tokeniza(c["texto"]) for c in self.chunks])
        self.co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))

    def _vetorial(self, consulta: str, k: int):
        r = self.colecao.query(query_texts=[consulta], n_results=k)
        return r["ids"][0]

    def _lexical(self, consulta: str, k: int):
        scores = self.bm25.get_scores(tokeniza(consulta))
        ordem = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [self.chunks[i]["id"] for i in ordem]

    def _fundir(self, listas):
        """Reciprocal Rank Fusion: soma 1/(K + posicao) de cada lista.

        Usado em vez de somar os scores brutos porque similaridade de cosseno e
        score BM25 estao em escalas diferentes e nao sao comparaveis diretamente.
        O RRF olha so a POSICAO, nao o valor, entao dispensa normalizacao.
        """
        pontos = {}
        for lista in listas:
            for posicao, ident in enumerate(lista):
                pontos[ident] = pontos.get(ident, 0) + 1 / (RRF_K + posicao + 1)
        return sorted(pontos, key=lambda i: -pontos[i])

    def buscar(self, consulta: str, consulta_en: str = None,
               k_final: int = K_FINAL, usar_rerank: bool = True):
        """Busca hibrida bilingue.

        A base de conhecimento e majoritariamente em ingles (26 de 33 documentos),
        e o modelo de embedding padrao do Chroma (all-MiniLM-L6-v2) e treinado so
        em ingles. Consulta em portugues, portanto, recupera mal: ela fica mais
        proxima dos poucos trechos em portugues do que dos trechos em ingles que
        de fato respondem a pergunta.

        Mitigacao adotada: passar tambem a consulta em ingles (`consulta_en`).
        As duas versoes alimentam busca vetorial e lexical, as quatro listas sao
        fundidas por RRF, e o reranking final usa a consulta original em portugues,
        porque o modelo de rerank da Cohere e multilingue.

        A correcao definitiva seria trocar o embedding por um modelo multilingue
        (ex: paraphrase-multilingual-MiniLM-L12-v2), o que exige instalar
        sentence-transformers e reindexar a base. Ficou documentado como melhoria.
        """
        consultas = [consulta] + ([consulta_en] if consulta_en else [])
        listas = []
        for c in consultas:
            listas.append(self._vetorial(c, K_VETORIAL))
            listas.append(self._lexical(c, K_LEXICAL))
        fundidos = self._fundir(listas)[:K_RERANK]
        candidatos = [self.por_id[i] for i in fundidos]

        if not usar_rerank or not candidatos:
            return [self._formatar(c, None) for c in candidatos[:k_final]]

        resposta = self.co.rerank(
            model=MODELO_RERANK,
            query=consulta,
            documents=[c["texto"] for c in candidatos],
            top_n=min(k_final, len(candidatos)),
        )
        saida = []
        for r in resposta.results:
            indice = r.index if hasattr(r, "index") else r["index"]
            score = r.relevance_score if hasattr(r, "relevance_score") else r["relevance_score"]
            saida.append(self._formatar(candidatos[indice], score))
        return saida

    @staticmethod
    def _formatar(chunk, score):
        return {
            "texto": chunk["texto"],
            "tecnologia": chunk["meta"]["tecnologia"],
            "categoria": chunk["meta"]["categoria"],
            "url_fonte": chunk["meta"]["url_fonte"],
            "score_rerank": score,
        }


if __name__ == "__main__":
    busca = BuscaHibrida()
    casos = [
        ("startup usa API externa de LLM e sofre com custo e latencia de inferencia",
         "LLM inference cost latency optimization serving throughput"),
        ("processamento de grandes volumes de dados tabulares",
         "large scale tabular dataframe data processing acceleration"),
        ("como controlar o comportamento de um agente de IA",
         "control guardrails safety behavior of AI agents and assistants"),
    ]
    for consulta, consulta_en in casos:
        print("\n" + "=" * 80)
        print("CONSULTA:", consulta)
        for r in busca.buscar(consulta, consulta_en=consulta_en, k_final=3):
            score = f"{r['score_rerank']:.3f}" if r["score_rerank"] is not None else "-"
            print(f"\n  [{score}] {r['tecnologia']} ({r['categoria']})")
            print(f"  {r['texto'][:200]}...")
            print(f"  fonte: {r['url_fonte']}")
