"""Refreshes the knowledge base with the latest PvPoke rankings.

Same as build_knowledge_base.py, but passes force_refresh=True through
ingest_all() to bypass the 24-hour PvPoke cache and pull rankings
live. Use this right after Niantic ships a balance update or a new
competitive season starts, when waiting out the cache would mean
serving stale meta advice.

    python -m backend.scripts.update_knowledge_base
"""
from collections import Counter

from backend.config import settings
from backend.rag.ingestion import ingest_all
from backend.rag.store import build_store, get_embeddings


def main() -> None:
    documents = ingest_all(force_refresh=True)

    embeddings = get_embeddings()
    build_store(documents, embeddings, settings.chroma_db_path)

    by_source = Counter(doc.metadata.get("source") for doc in documents)
    by_league = Counter(doc.metadata.get("league") for doc in documents)

    print(f"\nRefreshed knowledge base with {len(documents)} total documents")
    print("By source:", dict(by_source))
    print("By league:", dict(by_league))


if __name__ == "__main__":
    main()
