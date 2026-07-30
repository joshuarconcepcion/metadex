"""CP and PvP stat-product calculations for Pokemon GO.

Base stats passed into these functions must be GO-specific values from
data/loader.py's get_pokemon_go_stats() — not mainline stats from
PokeAPI. CP multipliers must come from data/loader.py's
get_cp_multipliers(), which sources them from the game master rather
than a hardcoded table.
"""
import math
from typing import Dict

from backend.data.loader import get_cp_multipliers

MIN_CP = 10


def calculate_cp(
    base_attack: int,
    base_defense: int,
    base_stamina: int,
    iv_attack: int,
    iv_defense: int,
    iv_stamina: int,
    level: float,
) -> int:
    """CP = (atk+ivAtk) * sqrt(def+ivDef) * sqrt(sta+ivSta) * cpm^2 / 10."""
    cpm = get_cp_multipliers()[level]

    attack = base_attack + iv_attack
    defense = base_defense + iv_defense
    stamina = base_stamina + iv_stamina

    cp = (attack * math.sqrt(defense) * math.sqrt(stamina) * cpm**2) / 10
    return max(math.floor(cp), MIN_CP)


def find_level_for_cp_cap(
    base_attack: int,
    base_defense: int,
    base_stamina: int,
    iv_attack: int,
    iv_defense: int,
    iv_stamina: int,
    cp_cap: int,
) -> float:
    """Finds the highest level this Pokemon can be powered up to without
    its CP exceeding cp_cap (e.g. 1500 for Great League, 2500 for Ultra)."""
    cpms: Dict[float, float] = get_cp_multipliers()

    best_level = min(cpms)
    for level in sorted(cpms):
        cp = calculate_cp(
            base_attack, base_defense, base_stamina,
            iv_attack, iv_defense, iv_stamina,
            level,
        )
        if cp <= cp_cap:
            best_level = level
        else:
            break

    return best_level


def calculate_stat_product(
    base_attack: int,
    base_defense: int,
    base_stamina: int,
    iv_attack: int,
    iv_defense: int,
    iv_stamina: int,
    level: float,
) -> float:
    """Stat product = effective_attack * effective_defense * effective_hp.

    The primary metric for evaluating PvP IV spreads, since it captures
    overall bulk+power independent of raw CP.
    """
    cpm = get_cp_multipliers()[level]

    effective_attack = (base_attack + iv_attack) * cpm
    effective_defense = (base_defense + iv_defense) * cpm
    effective_hp = math.floor((base_stamina + iv_stamina) * cpm)

    return effective_attack * effective_defense * effective_hp
