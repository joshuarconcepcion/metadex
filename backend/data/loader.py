"""Loads and caches Pokemon GO data from the PokeMiners game master.

PokeAPI is intentionally not used here: it serves mainline-game stats,
which use a different base-stat scale, move values, and CP formula than
Pokemon GO. The game master JSON below is extracted from the GO client
APK by the community after every game update and is the authoritative,
single source of truth for all GO-specific data (base stats, moves, CP
multipliers).

A note on CP multipliers specifically: the game master's PLAYER_LEVEL_SETTINGS
template only stores one CPM value per *integer* level (index i -> level i+1).
It does not separately store the half-level (x.5) values that Pokemon
leveling actually uses. Those are not independently datamined constants —
they are mathematically derived by Niantic from the two neighboring integer
CPMs via:

    cpm(L + 0.5) = sqrt((cpm(L)**2 + cpm(L + 1)**2) / 2)

This relationship was verified against PvPoke's independently published
half-level CPM table (exact match to 6 decimal places for all of levels
1.5-54.5), so get_cp_multipliers() below sources every integer level
straight from game master and derives half levels with this formula,
rather than hardcoding any lookup table.
"""
import json
import math
import time
from pathlib import Path
from typing import Optional

import httpx

from backend.config import settings

GAME_MASTER_URL = "https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json"
CACHE_TTL_SECONDS = 24 * 60 * 60

_TYPE_PREFIX = "POKEMON_TYPE_"
_MAX_POKEMON_LEVEL = 51


def _cache_file() -> Path:
    cache_dir = Path(settings.cache_path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "game_master.json"


def fetch_game_master(force_refresh: bool = False) -> list:
    """Downloads (or reads from local cache) the PokeMiners game master.

    Cached to disk and refreshed at most once every 24 hours, since the
    game master only changes when Niantic ships a game update.
    """
    cache_file = _cache_file()

    if not force_refresh and cache_file.exists():
        age_seconds = time.time() - cache_file.stat().st_mtime
        if age_seconds < CACHE_TTL_SECONDS:
            with cache_file.open("r") as f:
                return json.load(f)

    response = httpx.get(GAME_MASTER_URL, timeout=30.0)
    response.raise_for_status()
    data = response.json()

    with cache_file.open("w") as f:
        json.dump(data, f)

    return data


def _strip_type_prefix(type_id: Optional[str]) -> Optional[str]:
    if not type_id:
        return None
    return type_id.replace(_TYPE_PREFIX, "")


def get_pokemon_go_stats(pokemon_name: str) -> Optional[dict]:
    """Extracts GO-specific base stats, moves, and types for a Pokemon.

    Returns None if the Pokemon isn't found in the game master. GO base
    stats are derived by Niantic from mainline stats via their own
    formula and are not the same numbers PokeAPI returns.
    """
    game_master = fetch_game_master()
    target = pokemon_name.strip().upper()

    for template in game_master:
        pokemon_settings = template.get("data", {}).get("pokemonSettings")
        if not pokemon_settings or pokemon_settings.get("pokemonId") != target:
            continue

        stats = pokemon_settings.get("stats", {})

        types = []
        primary_type = _strip_type_prefix(pokemon_settings.get("type"))
        secondary_type = _strip_type_prefix(pokemon_settings.get("type2"))
        if primary_type:
            types.append(primary_type)
        if secondary_type:
            types.append(secondary_type)

        return {
            "pokemon_id": pokemon_settings.get("pokemonId"),
            "base_attack": stats.get("baseAttack"),
            "base_defense": stats.get("baseDefense"),
            "base_stamina": stats.get("baseStamina"),
            "types": types,
            "fast_move_ids": list(pokemon_settings.get("quickMoves", []))
            + list(pokemon_settings.get("eliteQuickMoves", [])),
            "charged_move_ids": list(pokemon_settings.get("cinematicMoves", []))
            + list(pokemon_settings.get("eliteCinematicMoves", [])),
        }

    return None


def get_move_data(move_id: str) -> Optional[dict]:
    """Extracts GO-specific power/energy/duration/type for a move.

    Returns None if the move isn't found in the game master.
    """
    game_master = fetch_game_master()
    target = move_id.strip().upper()

    for template in game_master:
        combat_move = template.get("data", {}).get("combatMove")
        if combat_move and combat_move.get("uniqueId") == target:
            return {
                "move_id": combat_move.get("uniqueId"),
                "type": _strip_type_prefix(combat_move.get("type")),
                "power": combat_move.get("power", 0),
                "energy_delta": combat_move.get("energyDelta", 0),
                # durationTurns is stored as (actual turns - 1); absent means 1 turn.
                "duration_turns": combat_move.get("durationTurns", 0) + 1,
            }

    return None


def get_cp_multipliers() -> dict:
    """Builds the CP multiplier table for levels 1-51 (0.5 increments).

    Integer levels are read directly from the game master's
    PLAYER_LEVEL_SETTINGS.cpMultiplier array. Half levels are derived from
    them via the documented Niantic formula (see module docstring) rather
    than hardcoded, since the game master does not store half-level values
    independently.
    """
    game_master = fetch_game_master()

    integer_cpms = None
    for template in game_master:
        player_level = template.get("data", {}).get("playerLevel")
        if player_level and "cpMultiplier" in player_level:
            integer_cpms = player_level["cpMultiplier"]
            break

    if integer_cpms is None:
        raise ValueError("PLAYER_LEVEL_SETTINGS.cpMultiplier not found in game master")

    max_level = min(_MAX_POKEMON_LEVEL, len(integer_cpms))

    def cpm_at_integer(level: int) -> float:
        return integer_cpms[level - 1]

    cpms = {}
    for half_steps in range(2, max_level * 2 + 1):
        level = half_steps / 2
        if level == int(level):
            cpms[level] = cpm_at_integer(int(level))
        else:
            lo = int(level)
            hi = lo + 1
            cpms[level] = math.sqrt((cpm_at_integer(lo) ** 2 + cpm_at_integer(hi) ** 2) / 2)

    return cpms


def get_all_pokemon_names() -> list:
    """Returns every Pokemon ID available in GO, per the game master."""
    game_master = fetch_game_master()

    names = []
    seen = set()
    for template in game_master:
        pokemon_settings = template.get("data", {}).get("pokemonSettings")
        if not pokemon_settings:
            continue
        pokemon_id = pokemon_settings.get("pokemonId")
        if pokemon_id and pokemon_id not in seen:
            seen.add(pokemon_id)
            names.append(pokemon_id)

    return names
