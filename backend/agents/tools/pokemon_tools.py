"""LangChain tools exposing Pokemon lookup, CP, and type-matchup data to the agent.

Thin wrappers around backend/data/loader.py, type_chart.py, and
cp_calculator.py — all the actual game-data logic lives there; these
functions just format that data as natural-language strings for the LLM.
"""
from langchain_core.tools import tool

from backend.data.cp_calculator import calculate_cp, calculate_stat_product, find_level_for_cp_cap
from backend.data.loader import get_cp_multipliers, get_move_data, get_pokemon_go_stats
from backend.data.type_chart import get_effectiveness, get_resistances, get_weaknesses

POKEAPI_SPRITE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{id}.png"

# CP caps by league; Master League has no cap, handled separately below.
_LEAGUE_CP_CAPS = {"great": 1500, "ultra": 2500}


@tool
def get_pokemon_info(pokemon_name: str) -> str:
    """Get stats, types, and movepool for a specific Pokemon.
    Use this when you need to know a Pokemon's base stats,
    typing, or available moves to evaluate its viability."""
    stats = get_pokemon_go_stats(pokemon_name)
    if stats is None:
        return f"Could not find a Pokemon named '{pokemon_name}' in the game master."

    fast_moves = ", ".join(stats["fast_move_ids"]) or "none listed"
    charged_moves = ", ".join(stats["charged_move_ids"]) or "none listed"
    sprite_url = (
        POKEAPI_SPRITE_URL.format(id=stats["dex_number"])
        if stats["dex_number"] is not None
        else "unavailable"
    )

    return (
        f"{stats['pokemon_id']} (#{stats['dex_number']})\n"
        f"Types: {'/'.join(stats['types'])}\n"
        f"Base stats (Pokemon GO values, not mainline) — "
        f"Attack: {stats['base_attack']}, Defense: {stats['base_defense']}, "
        f"Stamina: {stats['base_stamina']}\n"
        f"Fast moves: {fast_moves}\n"
        f"Charged moves: {charged_moves}\n"
        f"Sprite: {sprite_url}"
    )


@tool
def calculate_pvp_ivs(
    pokemon_name: str,
    iv_attack: int,
    iv_defense: int,
    iv_stamina: int,
    league: str = "great",
) -> str:
    """Calculate PvP metrics for a Pokemon with specific IVs.
    Use this when a user asks about whether their IVs are good
    for PvP, or to compare different IV spreads.
    League options: 'great' (1500 CP cap), 'ultra' (2500 CP cap),
    'master' (no cap)"""
    stats = get_pokemon_go_stats(pokemon_name)
    if stats is None:
        return f"Could not find a Pokemon named '{pokemon_name}' in the game master."

    league_key = league.strip().lower()
    base_attack, base_defense, base_stamina = (
        stats["base_attack"],
        stats["base_defense"],
        stats["base_stamina"],
    )

    if league_key == "master":
        # No CP cap, so there's no level/IV tradeoff — Pokemon battle at
        # their maximum achievable level, and higher IVs are always better.
        level = max(get_cp_multipliers())
        ideal_iv_attack, ideal_iv_defense, ideal_iv_stamina = 15, 15, 15
        ideal_level = level
    elif league_key in _LEAGUE_CP_CAPS:
        cp_cap = _LEAGUE_CP_CAPS[league_key]
        level = find_level_for_cp_cap(
            base_attack, base_defense, base_stamina, iv_attack, iv_defense, iv_stamina, cp_cap
        )
        # The commonly-cited "ideal" PvP spread: 0 attack IV (attack scales
        # linearly in the CP formula, so a lower attack IV buys a higher
        # level, which adds more bulk than the attack IV points cost).
        ideal_iv_attack, ideal_iv_defense, ideal_iv_stamina = 0, 15, 15
        ideal_level = find_level_for_cp_cap(
            base_attack, base_defense, base_stamina,
            ideal_iv_attack, ideal_iv_defense, ideal_iv_stamina, cp_cap,
        )
    else:
        return f"Unknown league '{league}'. Use 'great', 'ultra', or 'master'."

    cp = calculate_cp(base_attack, base_defense, base_stamina, iv_attack, iv_defense, iv_stamina, level)
    stat_product = calculate_stat_product(
        base_attack, base_defense, base_stamina, iv_attack, iv_defense, iv_stamina, level
    )
    ideal_stat_product = calculate_stat_product(
        base_attack, base_defense, base_stamina,
        ideal_iv_attack, ideal_iv_defense, ideal_iv_stamina, ideal_level,
    )
    percent_of_ideal = (stat_product / ideal_stat_product) * 100 if ideal_stat_product else 0.0

    return (
        f"{stats['pokemon_id']} with IVs {iv_attack}/{iv_defense}/{iv_stamina} "
        f"in {league.capitalize()} League:\n"
        f"Max level at this cap: {level}\n"
        f"CP: {cp}\n"
        f"Stat product: {stat_product:.0f}\n"
        f"That's {percent_of_ideal:.1f}% of the stat product for the ideal "
        f"{ideal_iv_attack}/{ideal_iv_defense}/{ideal_iv_stamina} spread at the same cap."
    )


@tool
def get_type_matchups(pokemon_name: str) -> str:
    """Get the type weaknesses and resistances for a Pokemon.
    Use this when building teams to understand coverage,
    or when choosing raid counters."""
    stats = get_pokemon_go_stats(pokemon_name)
    if stats is None:
        return f"Could not find a Pokemon named '{pokemon_name}' in the game master."

    weaknesses = get_weaknesses(stats["types"])
    resistances = get_resistances(stats["types"])

    weakness_str = ", ".join(
        f"{t} ({m}x)" for t, m in sorted(weaknesses.items(), key=lambda kv: -kv[1])
    ) or "none"
    resistance_str = ", ".join(
        f"{t} ({m}x)" for t, m in sorted(resistances.items(), key=lambda kv: kv[1])
    ) or "none"

    return (
        f"{stats['pokemon_id']} ({'/'.join(stats['types'])}):\n"
        f"Weak to: {weakness_str}\n"
        f"Resists: {resistance_str}"
    )


@tool
def calculate_battle_matchup(attacker_name: str, defender_name: str) -> str:
    """Calculate the type effectiveness of an attacker's moves
    against a specific defender. Use this when evaluating
    whether a specific Pokemon is a good counter."""
    attacker = get_pokemon_go_stats(attacker_name)
    if attacker is None:
        return f"Could not find a Pokemon named '{attacker_name}' in the game master."

    defender = get_pokemon_go_stats(defender_name)
    if defender is None:
        return f"Could not find a Pokemon named '{defender_name}' in the game master."

    move_ids = attacker["fast_move_ids"] + attacker["charged_move_ids"]
    lines = []
    for move_id in move_ids:
        move = get_move_data(move_id)
        if move is None or not move.get("type"):
            continue
        effectiveness = get_effectiveness(move["type"], defender["types"])
        lines.append(f"{move_id} ({move['type']}): {effectiveness}x vs {defender['pokemon_id']}")

    if not lines:
        return f"No move data found for {attacker['pokemon_id']}'s moves."

    return (
        f"{attacker['pokemon_id']} ({'/'.join(attacker['types'])}) vs "
        f"{defender['pokemon_id']} ({'/'.join(defender['types'])}):\n" + "\n".join(lines)
    )
