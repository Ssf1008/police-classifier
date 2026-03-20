from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


def build_embeddings(model_name: str) -> HuggingFaceEmbeddings:
    # SentenceTransformers-backed embeddings (local, no API key needed).
    return HuggingFaceEmbeddings(model_name=model_name)


def get_vectorstore(
    *,
    persist_dir: str,
    collection: str,
    embedding_model_name: str,
) -> Chroma:
    embeddings = build_embeddings(embedding_model_name)
    return Chroma(
        collection_name=collection,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )


def chroma_add_texts(
    vs: Chroma,
    *,
    ids: Sequence[str],
    texts: Sequence[str],
    metadatas: Sequence[Dict[str, Any]],
) -> None:
    if not (len(ids) == len(texts) == len(metadatas)):
        raise ValueError("ids/texts/metadatas length mismatch")
    vs.add_texts(texts=list(texts), metadatas=list(metadatas), ids=list(ids))
    # Persist for local disk-based usage.
    vs.persist()


def chroma_similarity_search(
    vs: Chroma, *, query: str, top_k: int
) -> List[Tuple[str, float, Dict[str, Any]]]:
    """
    Returns list of (page_content, score, metadata).
    Note: score meaning depends on Chroma distance metric; we return raw score.
    """
    docs_and_scores = vs.similarity_search_with_score(query, k=top_k)
    results: List[Tuple[str, float, Dict[str, Any]]] = []
    for doc, score in docs_and_scores:
        results.append((doc.page_content, float(score), dict(doc.metadata or {})))
    return results

