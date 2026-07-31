"""Builds the RAG knowledge base from scratch.

Run once to initialize the vector store after Phase 1 setup, and again
any time you want to pick up newly ingested content (mechanics doc
edits, etc) without necessarily needing a fresh PvPoke fetch — the
24-hour PvPoke cache is respected here. For a forced live re-fetch of
PvPoke rankings (e.g. after a Niantic balance update), use
update_knowledge_base.py instead.

    python -m backend.scripts.build_knowledge_base
"""
from collections import Counter

from backend.config import settings
from backend.rag.ingestion import ingest_all
from backend.rag.store import build_store, get_embeddings


def main() -> None:
    documents = ingest_all()

    embeddings = get_embeddings()
    build_store(documents, embeddings, settings.chroma_db_path)

    by_source = Counter(doc.metadata.get("source") for doc in documents)
    by_league = Counter(doc.metadata.get("league") for doc in documents)

    print(f"\nIndexed {len(documents)} total documents")
    print("By source:", dict(by_source))
    print("By league:", dict(by_league))


if __name__ == "__main__":
    main()
