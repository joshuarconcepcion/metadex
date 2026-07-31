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

## PvP rankings: PvPoke, not a hand-written tier list

The RAG knowledge base (`backend/rag/`) pulls PvP meta rankings from
[PvPoke's own GitHub repo](https://github.com/pvpoke/pvpoke) (MIT
licensed) rather than a hand-written tier list file, since the meta
shifts too fast for a static file to stay accurate — this is the raw
JSON PvPoke's own site is generated from, not the pvpoke.com website.

Two schema quirks worth knowing if you touch `backend/data/pvpoke.py`,
both verified directly against the live endpoints:

- `moveset` is a flat `[fastMove, chargedMove1, chargedMove2]` array,
  not a `{"fastMove": ..., "chargedMoves": [...]}` object.
- `scores` is an unlabeled 6-element array, not a dict. The order —
  verified against PvPoke's own `RankerOverall.js` — is
  `[lead, closer, switch, charger, attacker, consistency]`. There are
  also two candidate "rating" fields; the one we use (`score`, 0-100)
  is the one that's actually monotonic with rank position, unlike the
  top-level `rating` field.

The only hand-written content is `backend/data/knowledge/game_mechanics.md`
— evergreen mechanics (IVs, CP caps, shadow/purified multipliers,
weather boost, stardust costs) that don't shift with the meta. The
shadow Pokemon defense multiplier there (~0.8333x, not a flat -20%)
and the weather boost figures were verified against the live game
master's `COMBAT_SETTINGS`/`WEATHER_BONUS_SETTINGS`, not assumed.

## Project status: Phase 1

Phase 0 built the static data foundation (Pokemon GO stats/moves
loading, type effectiveness, CP/PvP stat-product calculations). Phase 1
adds the RAG knowledge base: live PvPoke rankings plus the mechanics
reference, chunked and embedded into a ChromaDB collection queryable
via MMR or direct similarity search. Agent tools (`backend/agents/`)
and the conversational agent/API endpoints beyond a health check land
in Phase 2+.

## Project structure

```
metadex/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # environment variables and settings
│   ├── data/
│   │   ├── loader.py        # loads and caches PokeMiners game master data
│   │   ├── type_chart.py    # type effectiveness calculations
│   │   ├── cp_calculator.py # CP and PvP stat-product calculations
│   │   ├── pvpoke.py        # fetches and caches live PvPoke rankings
│   │   └── knowledge/
│   │       └── game_mechanics.md  # evergreen mechanics reference
│   ├── rag/
│   │   ├── ingestion.py     # combines PvPoke + mechanics into Documents
│   │   ├── store.py         # ChromaDB vector store (all-MiniLM-L6-v2)
│   │   └── retriever.py     # MMR + similarity search over the store
│   ├── scripts/
│   │   ├── build_knowledge_base.py   # initial build / cache-respecting rebuild
│   │   └── update_knowledge_base.py  # forces a fresh PvPoke fetch
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

The first run downloads and caches the game master (~19MB) and the
`all-MiniLM-L6-v2` embedding model; subsequent runs reuse both.

## Building the knowledge base

```bash
python -m backend.scripts.build_knowledge_base
```

Fetches PvPoke rankings (respecting the 24h cache) and the mechanics
doc, embeds them, and writes the `pokego_meta` collection to
`CHROMA_DB_PATH`. After a Niantic balance update or new competitive
season, force a live re-fetch instead:

```bash
python -m backend.scripts.update_knowledge_base
```

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
- `CHROMA_DB_PATH` — where the `pokego_meta` ChromaDB collection persists
- `CACHE_PATH` — where the cached game master JSON and PvPoke rankings
  (`pvpoke_great.json`, `pvpoke_ultra.json`, `pvpoke_master.json`) are stored
