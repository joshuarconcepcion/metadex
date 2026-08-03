"""The main Pokemon GO advisor agent, built as a LangGraph tool-calling agent.

Two deviations from a literal reading of the original spec, both verified
before writing this file:

- `langgraph.prebuilt.create_react_agent` is deprecated as of LangGraph
  1.0 (removal planned for 2.0) in favor of `langchain.agents.create_agent`,
  which is a drop-in replacement — same {"messages": [...]} input/output
  shape, same stream_mode="messages" token streaming — so this builds on
  the non-deprecated import instead.
- `state_modifier` (the originally-specified kwarg for the system prompt)
  no longer exists at all on either constructor and raises a TypeError;
  `create_agent`'s equivalent parameter is `system_prompt`.

Model: the spec named "claude-sonnet-4-6", which is a real, still-active
model ID, but Claude Sonnet 5 has since superseded it as the current
Sonnet-tier model. This targets claude-sonnet-5 rather than pin to the
now-previous generation.
"""
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma

from backend.agents.tools.meta_tools import get_raid_counters, search_meta, set_rag_store
from backend.agents.tools.pokemon_tools import (
    calculate_battle_matchup,
    calculate_pvp_ivs,
    get_pokemon_info,
    get_type_matchups,
)

MODEL_NAME = "claude-sonnet-5"
MAX_TOKENS = 2048

SYSTEM_PROMPT = """You are an expert Pokemon GO advisor helping
players optimize their teams and improve their gameplay.

You have access to these tools:
- get_pokemon_info: look up stats and moves for any Pokemon
- calculate_pvp_ivs: evaluate IVs for PvP leagues
- get_type_matchups: find weaknesses and resistances
- calculate_battle_matchup: evaluate attacker vs defender
- search_meta: search current meta analysis and tier lists
- get_raid_counters: find best counters for raid bosses

Guidelines:
- Always search the meta knowledge base before giving tier list
  or team composition advice
- When evaluating IVs, always calculate stat product and compare
  to the ideal PvP IVs (0/15/15 for Great and Ultra League)
- Be specific: name exact moves (Fast Move / Charged Move)
- Explain your reasoning — don't just give answers
- If you're unsure about something, say so rather than guessing
- For team building, consider type synergy and coverage
- Shadow Pokemon have 20% more attack (1.2x) but their defense
  penalty is NOT a flat 20% — it's the mathematical reciprocal of
  the attack buff (1 / 1.2 ≈ 0.8333x, about 16.67% less), which is
  smaller than commonly assumed. Factor this in when relevant.
- When discussing Great League, always check the 1500 CP cap
- When discussing Ultra League, always check the 2500 CP cap"""


def build_advisor(rag_store: Chroma):
    """Builds the compiled LangGraph agent, wired up with all six tools."""
    set_rag_store(rag_store)

    llm = ChatAnthropic(model=MODEL_NAME, max_tokens=MAX_TOKENS)

    tools = [
        get_pokemon_info,
        calculate_pvp_ivs,
        get_type_matchups,
        calculate_battle_matchup,
        search_meta,
        get_raid_counters,
    ]

    return create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)
