"""ChromaDB vector store for the RAG knowledge base.

Uses HuggingFaceEmbeddings with the 'all-MiniLM-L6-v2' model — small,
fast, runs locally with no API key required, and is the standard
default for this kind of retrieval workload.
"""
from typing import List

from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

COLLECTION_NAME = "pokego_meta"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Chroma defaults to Euclidean (L2) distance, whose relevance-score
# conversion isn't bounded to [0, 1] for these embeddings in practice
# (verified: it produces negative "relevance" scores). Explicitly
# requesting cosine distance makes similarity_search_with_relevance_scores
# return properly normalized [0, 1] scores, which retriever.py's
# has_relevant_context depends on.
_COLLECTION_CONFIGURATION = {"hnsw": {"space": "cosine"}}


def get_embeddings() -> Embeddings:
    """Builds the embeddings model used across the knowledge base."""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


def build_store(documents: List[Document], embeddings: Embeddings, persist_path: str) -> Chroma:
    """Rebuilds the pokego_meta collection from scratch.

    Clears any existing collection first so stale documents (e.g. an
    old PvPoke meta snapshot from a previous ingestion run) never
    linger alongside freshly ingested ones.
    """
    store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=persist_path,
        collection_configuration=_COLLECTION_CONFIGURATION,
    )
    store.delete_collection()

    return Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=persist_path,
        collection_configuration=_COLLECTION_CONFIGURATION,
    )


def get_store(embeddings: Embeddings, persist_path: str) -> Chroma:
    """Connects to the existing persisted pokego_meta collection."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=persist_path,
        collection_configuration=_COLLECTION_CONFIGURATION,
    )
