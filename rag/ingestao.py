"""
Ingestao da base de conhecimento NVIDIA no Chroma.

Le os arquivos .md de base_conhecimento/, quebra em chunks, gera embeddings
locais (modelo ONNX que ja vem com o chromadb, sem custo de API) e grava
tanto no Chroma quanto num JSON usado depois pela busca lexical BM25.

Rodar uma vez:  python rag/ingestao.py
"""

import os
import re
import json
import glob

import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(AQUI, "base_conhecimento")
PERSIST = os.path.join(AQUI, "chroma_db")
CHUNKS_JSON = os.path.join(AQUI, "chunks.json")
COLECAO = "nvidia"

# Chunk de ~900 caracteres com 150 de sobreposicao.
# Os documentos tem entre 1.700 e 4.900 caracteres, entao isso da de 2 a 6 chunks
# por documento: pedaco grande o suficiente para conter um argumento inteiro,
# pequeno o suficiente para o reranking conseguir discriminar relevancia.
TAMANHO_CHUNK = 900
SOBREPOSICAO = 150


def ler_documento(caminho: str):
    """Separa o frontmatter (metadados) do corpo do texto."""
    texto = open(caminho, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
    if not m:
        return None
    meta = {}
    for linha in m.group(1).splitlines():
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            meta[chave.strip()] = valor.strip()
    return meta, m.group(2).strip()


def main():
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=TAMANHO_CHUNK,
        chunk_overlap=SOBREPOSICAO,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    ids, textos, metadados = [], [], []

    for caminho in sorted(glob.glob(os.path.join(BASE, "*.md"))):
        lido = ler_documento(caminho)
        if not lido:
            print(f"  ignorado (sem frontmatter): {os.path.basename(caminho)}")
            continue
        meta, corpo = lido
        nome = os.path.basename(caminho)
        for i, pedaco in enumerate(splitter.split_text(corpo)):
            ids.append(f"{nome}::{i}")
            textos.append(pedaco)
            metadados.append(
                {
                    "tecnologia": meta.get("tecnologia", ""),
                    "categoria": meta.get("categoria", ""),
                    "url_fonte": meta.get("url_fonte", ""),
                    "titulo": meta.get("titulo", ""),
                    "arquivo": nome,
                }
            )

    print(
        f"{len(ids)} chunks gerados a partir de {len(set(m['arquivo'] for m in metadados))} documentos"
    )

    cliente = chromadb.PersistentClient(path=PERSIST)
    try:
        cliente.delete_collection(COLECAO)
        print("colecao anterior apagada")
    except Exception:
        pass

    colecao = cliente.create_collection(
        name=COLECAO,
        embedding_function=embedding_functions.DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )

    for i in range(0, len(ids), 50):
        colecao.add(
            ids=ids[i : i + 50],
            documents=textos[i : i + 50],
            metadatas=metadados[i : i + 50],
        )
        print(f"  indexados {min(i + 50, len(ids))}/{len(ids)}")

    with open(CHUNKS_JSON, "w", encoding="utf-8") as f:
        json.dump(
            [{"id": i, "texto": t, "meta": m} for i, t, m in zip(ids, textos, metadados)],
            f,
            ensure_ascii=False,
        )

    print(f"pronto: {colecao.count()} chunks no Chroma e em {os.path.basename(CHUNKS_JSON)}")


if __name__ == "__main__":
    main()
