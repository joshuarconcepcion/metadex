"""Pokemon GO type effectiveness chart and lookups.

Pokemon GO uses its own multiplier scale, different from the mainline
games, and it has no true immunities: mainline 0x matchups (e.g. Ghost
vs. Normal) become a "double resist" of 0.390625 instead.

The values below were extracted directly from the live PokeMiners game
master's POKEMON_TYPE_* templates (typeEffective.attackScalar), so this
is the actual data Niantic ships, not a transcription from a wiki.
"""
from typing import Dict, List

SUPER_EFFECTIVE = 1.6
NOT_VERY_EFFECTIVE = 0.625
DOUBLE_RESIST = 0.390625
NEUTRAL = 1.0

TYPES = [
    "NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG", "GHOST",
    "STEEL", "FIRE", "WATER", "GRASS", "ELECTRIC", "PSYCHIC", "ICE", "DRAGON",
    "DARK", "FAIRY",
]

# TYPE_CHART[attacking_type][defending_type] = multiplier
TYPE_CHART: Dict[str, Dict[str, float]] = {
    "NORMAL": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 1.0, "POISON": 1.0, "GROUND": 1.0, "ROCK": 0.625, "BUG": 1.0, "GHOST": 0.390625, "STEEL": 0.625, "FIRE": 1.0, "WATER": 1.0, "GRASS": 1.0, "ELECTRIC": 1.0, "PSYCHIC": 1.0, "ICE": 1.0, "DRAGON": 1.0, "DARK": 1.0, "FAIRY": 1.0},
    "FIGHTING": {"NORMAL": 1.6, "FIGHTING": 1.0, "FLYING": 0.625, "POISON": 0.625, "GROUND": 1.0, "ROCK": 1.6, "BUG": 0.625, "GHOST": 0.390625, "STEEL": 1.6, "FIRE": 1.0, "WATER": 1.0, "GRASS": 1.0, "ELECTRIC": 1.0, "PSYCHIC": 0.625, "ICE": 1.6, "DRAGON": 1.0, "DARK": 1.6, "FAIRY": 0.625},
    "FLYING": {"NORMAL": 1.0, "FIGHTING": 1.6, "FLYING": 1.0, "POISON": 1.0, "GROUND": 1.0, "ROCK": 0.625, "BUG": 1.6, "GHOST": 1.0, "STEEL": 0.625, "FIRE": 1.0, "WATER": 1.0, "GRASS": 1.6, "ELECTRIC": 0.625, "PSYCHIC": 1.0, "ICE": 1.0, "DRAGON": 1.0, "DARK": 1.0, "FAIRY": 1.0},
    "POISON": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 1.0, "POISON": 0.625, "GROUND": 0.625, "ROCK": 0.625, "BUG": 1.0, "GHOST": 0.625, "STEEL": 0.390625, "FIRE": 1.0, "WATER": 1.0, "GRASS": 1.6, "ELECTRIC": 1.0, "PSYCHIC": 1.0, "ICE": 1.0, "DRAGON": 1.0, "DARK": 1.0, "FAIRY": 1.6},
    "GROUND": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 0.390625, "POISON": 1.6, "GROUND": 1.0, "ROCK": 1.6, "BUG": 0.625, "GHOST": 1.0, "STEEL": 1.6, "FIRE": 1.6, "WATER": 1.0, "GRASS": 0.625, "ELECTRIC": 1.6, "PSYCHIC": 1.0, "ICE": 1.0, "DRAGON": 1.0, "DARK": 1.0, "FAIRY": 1.0},
    "ROCK": {"NORMAL": 1.0, "FIGHTING": 0.625, "FLYING": 1.6, "POISON": 1.0, "GROUND": 0.625, "ROCK": 1.0, "BUG": 1.6, "GHOST": 1.0, "STEEL": 0.625, "FIRE": 1.6, "WATER": 1.0, "GRASS": 1.0, "ELECTRIC": 1.0, "PSYCHIC": 1.0, "ICE": 1.6, "DRAGON": 1.0, "DARK": 1.0, "FAIRY": 1.0},
    "BUG": {"NORMAL": 1.0, "FIGHTING": 0.625, "FLYING": 0.625, "POISON": 0.625, "GROUND": 1.0, "ROCK": 1.0, "BUG": 1.0, "GHOST": 0.625, "STEEL": 0.625, "FIRE": 0.625, "WATER": 1.0, "GRASS": 1.6, "ELECTRIC": 1.0, "PSYCHIC": 1.6, "ICE": 1.0, "DRAGON": 1.0, "DARK": 1.6, "FAIRY": 0.625},
    "GHOST": {"NORMAL": 0.390625, "FIGHTING": 1.0, "FLYING": 1.0, "POISON": 1.0, "GROUND": 1.0, "ROCK": 1.0, "BUG": 1.0, "GHOST": 1.6, "STEEL": 1.0, "FIRE": 1.0, "WATER": 1.0, "GRASS": 1.0, "ELECTRIC": 1.0, "PSYCHIC": 1.6, "ICE": 1.0, "DRAGON": 1.0, "DARK": 0.625, "FAIRY": 1.0},
    "STEEL": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 1.0, "POISON": 1.0, "GROUND": 1.0, "ROCK": 1.6, "BUG": 1.0, "GHOST": 1.0, "STEEL": 0.625, "FIRE": 0.625, "WATER": 0.625, "GRASS": 1.0, "ELECTRIC": 0.625, "PSYCHIC": 1.0, "ICE": 1.6, "DRAGON": 1.0, "DARK": 1.0, "FAIRY": 1.6},
    "FIRE": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 1.0, "POISON": 1.0, "GROUND": 1.0, "ROCK": 0.625, "BUG": 1.6, "GHOST": 1.0, "STEEL": 1.6, "FIRE": 0.625, "WATER": 0.625, "GRASS": 1.6, "ELECTRIC": 1.0, "PSYCHIC": 1.0, "ICE": 1.6, "DRAGON": 0.625, "DARK": 1.0, "FAIRY": 1.0},
    "WATER": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 1.0, "POISON": 1.0, "GROUND": 1.6, "ROCK": 1.6, "BUG": 1.0, "GHOST": 1.0, "STEEL": 1.0, "FIRE": 1.6, "WATER": 0.625, "GRASS": 0.625, "ELECTRIC": 1.0, "PSYCHIC": 1.0, "ICE": 1.0, "DRAGON": 0.625, "DARK": 1.0, "FAIRY": 1.0},
    "GRASS": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 0.625, "POISON": 0.625, "GROUND": 1.6, "ROCK": 1.6, "BUG": 0.625, "GHOST": 1.0, "STEEL": 0.625, "FIRE": 0.625, "WATER": 1.6, "GRASS": 0.625, "ELECTRIC": 1.0, "PSYCHIC": 1.0, "ICE": 1.0, "DRAGON": 0.625, "DARK": 1.0, "FAIRY": 1.0},
    "ELECTRIC": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 1.6, "POISON": 1.0, "GROUND": 0.390625, "ROCK": 1.0, "BUG": 1.0, "GHOST": 1.0, "STEEL": 1.0, "FIRE": 1.0, "WATER": 1.6, "GRASS": 0.625, "ELECTRIC": 0.625, "PSYCHIC": 1.0, "ICE": 1.0, "DRAGON": 0.625, "DARK": 1.0, "FAIRY": 1.0},
    "PSYCHIC": {"NORMAL": 1.0, "FIGHTING": 1.6, "FLYING": 1.0, "POISON": 1.6, "GROUND": 1.0, "ROCK": 1.0, "BUG": 1.0, "GHOST": 1.0, "STEEL": 0.625, "FIRE": 1.0, "WATER": 1.0, "GRASS": 1.0, "ELECTRIC": 1.0, "PSYCHIC": 0.625, "ICE": 1.0, "DRAGON": 1.0, "DARK": 0.390625, "FAIRY": 1.0},
    "ICE": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 1.6, "POISON": 1.0, "GROUND": 1.6, "ROCK": 1.0, "BUG": 1.0, "GHOST": 1.0, "STEEL": 0.625, "FIRE": 0.625, "WATER": 0.625, "GRASS": 1.6, "ELECTRIC": 1.0, "PSYCHIC": 1.0, "ICE": 0.625, "DRAGON": 1.6, "DARK": 1.0, "FAIRY": 1.0},
    "DRAGON": {"NORMAL": 1.0, "FIGHTING": 1.0, "FLYING": 1.0, "POISON": 1.0, "GROUND": 1.0, "ROCK": 1.0, "BUG": 1.0, "GHOST": 1.0, "STEEL": 0.625, "FIRE": 1.0, "WATER": 1.0, "GRASS": 1.0, "ELECTRIC": 1.0, "PSYCHIC": 1.0, "ICE": 1.0, "DRAGON": 1.6, "DARK": 1.0, "FAIRY": 0.390625},
    "DARK": {"NORMAL": 1.0, "FIGHTING": 0.625, "FLYING": 1.0, "POISON": 1.0, "GROUND": 1.0, "ROCK": 1.0, "BUG": 1.0, "GHOST": 1.6, "STEEL": 1.0, "FIRE": 1.0, "WATER": 1.0, "GRASS": 1.0, "ELECTRIC": 1.0, "PSYCHIC": 1.6, "ICE": 1.0, "DRAGON": 1.0, "DARK": 0.625, "FAIRY": 0.625},
    "FAIRY": {"NORMAL": 1.0, "FIGHTING": 1.6, "FLYING": 1.0, "POISON": 0.625, "GROUND": 1.0, "ROCK": 1.0, "BUG": 1.0, "GHOST": 1.0, "STEEL": 0.625, "FIRE": 0.625, "WATER": 1.0, "GRASS": 1.0, "ELECTRIC": 1.0, "PSYCHIC": 1.0, "ICE": 1.0, "DRAGON": 1.6, "DARK": 1.6, "FAIRY": 1.0},
}


def get_effectiveness(attacking_type: str, defending_types: List[str]) -> float:
    """Returns the combined effectiveness multiplier of an attacking type
    against one or two defending types (multipliers stack multiplicatively)."""
    row = TYPE_CHART[attacking_type.upper()]
    multiplier = 1.0
    for defending_type in defending_types:
        multiplier *= row[defending_type.upper()]
    return multiplier


def get_weaknesses(defending_types: List[str]) -> Dict[str, float]:
    """Returns all attacking types that are super effective (>1.0x) against
    the given defending type(s), mapped to their combined multiplier."""
    return {
        attacking_type: multiplier
        for attacking_type in TYPES
        if (multiplier := get_effectiveness(attacking_type, defending_types)) > NEUTRAL
    }


def get_resistances(defending_types: List[str]) -> Dict[str, float]:
    """Returns all attacking types that deal reduced damage (<1.0x) against
    the given defending type(s), mapped to their combined multiplier."""
    return {
        attacking_type: multiplier
        for attacking_type in TYPES
        if (multiplier := get_effectiveness(attacking_type, defending_types)) < NEUTRAL
    }
