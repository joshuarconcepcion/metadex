"""Similarity search over the ingested knowledge base."""
from typing import List, Optional, Tuple

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever


def get_retriever(store: Chroma, k: int = 4, league_filter: Optional[str] = None) -> VectorStoreRetriever:
    """Returns an MMR retriever, optionally restricted to one league's documents.

    MMR (Maximum Marginal Relevance) balances relevance against
    diversity among the returned documents, so a query doesn't come
    back as several near-duplicate restatements of the same top-ranked
    Pokemon.
    """
    search_kwargs = {"k": k}
    if league_filter is not None:
        search_kwargs["filter"] = {"league": league_filter}

    return store.as_retriever(search_type="mmr", search_kwargs=search_kwargs)


def search(store: Chroma, query: str, k: int = 4) -> List[Tuple[Document, float]]:
    """Direct similarity search, returning (document, score) pairs."""
    return store.similarity_search_with_score(query, k=k)


def has_relevant_context(store: Chroma, query: str, threshold: float = 0.7) -> bool:
    """True if any result's normalized relevance score meets the threshold.

    Uses similarity_search_with_relevance_scores rather than the raw
    similarity_search_with_score, since the latter returns Chroma's
    unnormalized distance metric (where *lower* is more similar) —
    the relevance-scores variant normalizes to a 0-1 scale where
    higher means more similar, which is what "exceeds threshold" means
    here.
    """
    results = store.similarity_search_with_relevance_scores(query, k=4)
    return any(score >= threshold for _, score in results)
