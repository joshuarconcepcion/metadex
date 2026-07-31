"""Fetches current PvP rankings from PvPoke's public rankings data.

PvPoke's community-maintained rankings (github.com/pvpoke/pvpoke, MIT
licensed) are used instead of a hand-written meta tier list: the PvP
meta shifts constantly as new Pokemon release and moves get
rebalanced, so any static file would go stale almost immediately.
These URLs point at the raw JSON files in the pvpoke repo (not the
pvpoke.com website, which serves PHP pages) — the same data PvPoke's
own site is generated from.

A schema note, verified directly against the live endpoints (a naive
reading of "rankings JSON" undersells how it's actually shaped):

- "moveset" is a flat 3-element array [fastMove, chargedMove1,
  chargedMove2], not a {"fastMove": ..., "chargedMoves": [...]} object.
- "scores" is an unlabeled 6-element array, not a dict keyed by role
  name. The order — verified against PvPoke's own ranking source,
  src/js/battle/rankers/RankerOverall.js (the `categories` array plus
  the separately-appended consistency score) — is:
  [lead, closer, switch, charger, attacker, consistency].
- There are two candidate "overall rating" fields: a top-level
  "rating" (not monotonic with rank — it's some other per-Pokemon
  aggregate) and a "score" field on a 0-100 scale that IS
  monotonically decreasing with rank position across the whole list.
  "score" is the one that actually represents overall rating.
"""
import json
import time
from pathlib import Path
from typing import List

import httpx
from langchain_core.documents import Document

from backend.config import settings

PVPOKE_URLS = {
    "great": "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-1500.json",
    "ultra": "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-2500.json",
    "master": "https://raw.githubusercontent.com/pvpoke/pvpoke/master/src/data/rankings/all/overall/rankings-10000.json",
}
# Source: pvpoke/pvpoke on GitHub (MIT licensed)
# These are raw JSON files from the pvpoke repo, not the pvpoke.com website.
# The website serves PHP pages — the raw JSON on GitHub is what we want.

CACHE_TTL_SECONDS = 24 * 60 * 60
TOP_N_PER_LEAGUE = 50

# Order of PvPoke's unlabeled "scores" array — see module docstring.
_SCORE_ORDER = ["lead", "closer", "switch", "charger", "attacker", "consistency"]


def _cache_file(league: str) -> Path:
    cache_dir = Path(settings.cache_path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"pvpoke_{league}.json"


def fetch_rankings(league: str, force_refresh: bool = False) -> List[dict]:
    """Downloads (or reads from local cache) PvPoke rankings for one league."""
    if league not in PVPOKE_URLS:
        raise ValueError(f"Unknown league '{league}', expected one of {list(PVPOKE_URLS)}")

    cache_file = _cache_file(league)

    if not force_refresh and cache_file.exists():
        age_seconds = time.time() - cache_file.stat().st_mtime
        if age_seconds < CACHE_TTL_SECONDS:
            with cache_file.open("r") as f:
                return json.load(f)

    response = httpx.get(PVPOKE_URLS[league], timeout=30.0)
    response.raise_for_status()
    data = response.json()

    with cache_file.open("w") as f:
        json.dump(data, f)

    return data


def fetch_all_rankings(force_refresh: bool = False) -> dict:
    """Fetches Great, Ultra, and Master League rankings in one call."""
    return {
        league: fetch_rankings(league, force_refresh=force_refresh)
        for league in PVPOKE_URLS
    }


def _build_document(entry: dict, league: str, rank: int) -> Document:
    """Converts one raw PvPoke ranking entry into a Document.

    Three things here rely on the real (undocumented) PvPoke schema
    rather than the obvious one — see the module docstring for how
    each was verified:
    - "moveset" is unpacked positionally as [fast, charged, charged],
      not read as named fields.
    - "scores" is mapped through _SCORE_ORDER, since the array itself
      has no field names.
    - The rating we report is entry["score"], not entry["rating"] —
      "rating" is a different, non-monotonic per-Pokemon stat.
    """
    fast_move, charged_move_1, charged_move_2 = entry["moveset"]
    charged_moves = [charged_move_1, charged_move_2]
    scores = dict(zip(_SCORE_ORDER, entry.get("scores", [])))
    rating = entry.get("score")

    page_content = (
        f"{entry['speciesName']} is a top {rank} Pokemon in {league.capitalize()} League "
        f"with a rating of {rating}. Best moveset: {fast_move} / {', '.join(charged_moves)}. "
        f"Role scores — Lead: {scores.get('lead')}, Switch: {scores.get('switch')}, "
        f"Closer: {scores.get('closer')}, Attacker: {scores.get('attacker')}, "
        f"Consistency: {scores.get('consistency')}."
    )

    return Document(
        page_content=page_content,
        metadata={
            "source": "pvpoke",
            "league": league,
            "species_id": entry["speciesId"],
            "species_name": entry["speciesName"],
            "rank": rank,
            "rating": rating,
            "fast_move": fast_move,
            "charged_moves": charged_moves,
        },
    )


def rankings_to_documents(rankings: dict) -> List[Document]:
    """Converts PvPoke rankings into LangChain Documents.

    Only the top TOP_N_PER_LEAGUE (50) Pokemon per league are included,
    to keep the knowledge base focused on what's actually viable rather
    than every remotely-usable Pokemon PvPoke tracks.
    """
    documents = []
    for league, entries in rankings.items():
        for rank, entry in enumerate(entries[:TOP_N_PER_LEAGUE], start=1):
            documents.append(_build_document(entry, league, rank))
    return documents
