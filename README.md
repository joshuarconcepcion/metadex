# PokeGO Advisor

A conversational AI agent for Pokemon GO players — team optimization, raid
counter recommendations, and power-up/investment decisions. Built with
LangChain, LangGraph, and FastAPI on the backend, with a React (Next.js)
frontend arriving in Phase 3.

## Why not PokeAPI

PokeAPI serves mainline-game data: different base stats, different move
values, no CP system. Pokemon GO uses its own stat system (base
attack/defense/stamina, CP multipliers, GO-specific move power/energy)
derived by Niantic from the mainline games but not equivalent to them.

This project instead uses the **PokeMiners game master**
(`https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json`),
a JSON file the community extracts from the GO client APK after every
game update. It's the single source of truth for all GO-specific data
here: base stats, moves, CP multipliers, and type effectiveness.

One nuance worth knowing if you touch `backend/data/loader.py`: the game
master's CP multiplier table only stores one value per *integer* level.
The half-level (x.5) values Pokemon leveling actually uses aren't stored
independently — they're derived from the two neighboring integer CPMs via
`cpm(L + 0.5) = sqrt((cpm(L)^2 + cpm(L + 1)^2) / 2)`, which is what
`get_cp_multipliers()` does. This was verified against PvPoke's
independently published half-level table (exact match).

## Project status: Phase 0

Phase 0 sets up project structure, dependencies, and the static data
foundation the agent will build on: Pokemon GO stats/moves loading, type
effectiveness, and CP/PvP stat-product calculations. The RAG pipeline
(`backend/rag/`) and agent tools (`backend/agents/`) are stubbed out with
docstrings describing what lands in Phases 1-2; the conversational
agent and API endpoints beyond a health check come later too.

## Project structure

```
metadex/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # environment variables and settings
│   ├── data/
│   │   ├── loader.py        # loads and caches PokeMiners game master data
│   │   ├── type_chart.py    # type effectiveness calculations
│   │   └── cp_calculator.py # CP and PvP stat-product calculations
│   ├── rag/                 # community content ingestion + retrieval (Phase 1)
│   ├── agents/tools/        # LangChain tools for the agent (Phase 2)
│   └── tests/
├── frontend/                 # Next.js app (Phase 3)
├── requirements.txt
├── .env.example
└── docker-compose.yml
```

## Setup

```bash
cd metadex
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# then fill in ANTHROPIC_API_KEY in .env
```

## Running the tests

```bash
pytest
```

The first run downloads and caches the game master (~19MB); subsequent
runs within 24 hours reuse the cache.

## Running the backend

```bash
uvicorn backend.main:app --reload
```

Then check `http://localhost:8000/health` and
`http://localhost:8000/pokemon/medicham`.

### With Docker

```bash
docker compose up --build
```

## Environment variables

See `.env.example`:

- `ANTHROPIC_API_KEY` — Claude API key, used by the LangGraph agent (Phase 2+)
- `CHROMA_DB_PATH` — where the ChromaDB vector store persists (Phase 1+)
- `CACHE_PATH` — where the cached game master JSON is stored
