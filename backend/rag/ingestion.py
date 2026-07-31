"""Ingestion pipeline combining PvPoke rankings and hand-written mechanics content.

Deliberately only two sources feed the knowledge base:

1. PvPoke rankings (backend/data/pvpoke.py) — always current meta,
   fetched live from PvPoke's own repo.
2. backend/data/knowledge/game_mechanics.md — evergreen mechanics that
   don't shift with the meta, so a single hand-written file suffices.

No hand-written meta tier lists: the PvP meta shifts too fast for a
static file to stay accurate, and PvPoke's community-maintained
rankings are the trusted source of truth for "what's good right now."
"""
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownTextSplitter

from backend.data.pvpoke import fetch_all_rankings, fetch_rankings, rankings_to_documents

MECHANICS_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge" / "game_mechanics.md"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def ingest_pvpoke(league: str = "all", force_refresh: bool = False) -> List[Document]:
    """Fetches PvPoke rankings and converts them into Documents.

    league="all" (default) pulls Great, Ultra, and Master League;
    pass a specific league ("great"/"ultra"/"master") to ingest just one.
    """
    if league == "all":
        rankings = fetch_all_rankings(force_refresh=force_refresh)
    else:
        rankings = {league: fetch_rankings(league, force_refresh=force_refresh)}

    return rankings_to_documents(rankings)


def ingest_mechanics() -> List[Document]:
    """Loads and chunks the hand-written game mechanics reference."""
    text = MECHANICS_PATH.read_text()

    splitter = MarkdownTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_text(text)

    return [
        Document(page_content=chunk, metadata={"source": "mechanics", "league": "all"})
        for chunk in chunks
    ]


def ingest_all(force_refresh: bool = False) -> List[Document]:
    """Combines PvPoke rankings and mechanics documents into one corpus."""
    pvpoke_docs = ingest_pvpoke(force_refresh=force_refresh)
    mechanics_docs = ingest_mechanics()

    print(f"Ingested {len(pvpoke_docs)} PvPoke ranking documents")
    print(f"Ingested {len(mechanics_docs)} game mechanics documents")

    return pvpoke_docs + mechanics_docs
