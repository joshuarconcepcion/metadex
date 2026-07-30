"""FastAPI app entrypoint.

Phase 0: exposes a health check and a thin read-only endpoint over the
data foundation (data/loader.py) so the layer can be sanity-checked
end-to-end. The conversational agent endpoint lands in a later phase.
"""
from fastapi import FastAPI, HTTPException

from backend.data.loader import get_pokemon_go_stats

app = FastAPI(title="PokeGO Advisor", version="0.1.0")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/pokemon/{pokemon_name}")
def read_pokemon(pokemon_name: str) -> dict:
    stats = get_pokemon_go_stats(pokemon_name)
    if stats is None:
        raise HTTPException(status_code=404, detail=f"Pokemon '{pokemon_name}' not found")
    return stats
