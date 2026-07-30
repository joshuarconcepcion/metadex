"""LangChain tools exposing Pokemon lookup, CP, and type-matchup data to the agent.

Phase 2: will wrap backend/data/loader.py, type_chart.py, and
cp_calculator.py as @tool-decorated functions the LangGraph agent can
call (e.g. "get stats for a Pokemon", "compute CP for a level/IV combo",
"find raid counters by type matchup").
"""
