"""LangChain tools exposing PvP/raid meta and community-content retrieval to the agent.

Wraps backend/rag/retriever.py so the agent can pull PvPoke meta context
and type-based raid counter analysis into its responses.

Note on get_raid_counters: Phase 1's knowledge base only contains PvP
league rankings and evergreen mechanics — no raid-specific rankings
source. Its RAG lookup here will typically return weak or irrelevant
context (verified during Phase 1: a "raid counters" query scored close
to nonsense-query levels against that corpus). The type-effectiveness
analysis below is the reliable part of this tool; the RAG context is a
best-effort supplement, not the primary source, until a raid-specific
knowledge source is added.
"""
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.tools import tool

from backend.data.loader import get_pokemon_go_stats
from backend.data.type_chart import get_weaknesses
from backend.rag import retriever

# Tools must be plain, directly-importable callables whose signature (via
# type hints) becomes the schema the LLM sees — so the RAG store, a
# runtime dependency rather than something the LLM should choose, is
# injected via module state instead of being a tool argument.
# build_advisor() calls set_rag_store() once before constructing the agent.
_rag_store: Optional[Chroma] = None


def set_rag_store(store: Chroma) -> None:
    """Injects the shared RAG store so search_meta/get_raid_counters can use it."""
    global _rag_store
    _rag_store = store


@tool
def search_meta(query: str, league: str = "great") -> str:
    """Search the Pokemon GO meta knowledge base for information
    about team compositions, tier lists, movesets, and strategy.
    Use this for any question about what's currently strong,
    recommended movesets, or team building advice.
    League options: 'great', 'ultra', 'master', 'raid'"""
    if _rag_store is None:
        return "The meta knowledge base hasn't been initialized yet."

    results = retriever.search(_rag_store, query, k=4)

    league_key = league.strip().lower()
    if league_key in {"great", "ultra", "master"}:
        filtered = [(doc, score) for doc, score in results if doc.metadata.get("league") == league_key]
        # Fall back to the unfiltered results rather than returning nothing
        # if the league filter happens to exclude everything retrieved.
        results = filtered or results

    if not results:
        return f"No meta information found for '{query}'."

    context = "\n\n".join(doc.page_content for doc, _ in results)
    return f"Meta knowledge base results for '{query}':\n\n{context}"


@tool
def get_raid_counters(raid_boss: str) -> str:
    """Get the best counters for a specific raid boss.
    Use this when a user asks about how to beat a raid."""
    stats = get_pokemon_go_stats(raid_boss)
    if stats is None:
        return f"Could not find raid boss '{raid_boss}' in the game master."

    weaknesses = get_weaknesses(stats["types"])
    sorted_weaknesses = sorted(weaknesses.items(), key=lambda kv: -kv[1])
    type_summary = ", ".join(f"{t} ({m}x)" for t, m in sorted_weaknesses) or "no significant weaknesses"

    result = (
        f"{stats['pokemon_id']} ({'/'.join(stats['types'])}) is weak to: {type_summary}. "
        f"Prioritize attackers of these types with strong same-type fast and charged moves."
    )

    if _rag_store is not None:
        rag_results = retriever.search(_rag_store, f"{raid_boss} raid counters", k=3)
        if rag_results:
            context = "\n".join(doc.page_content for doc, _ in rag_results)
            result += f"\n\nRelated context from the knowledge base:\n{context}"

    return result
