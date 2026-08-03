import math

import pytest

from backend.data import cp_calculator, loader, type_chart


@pytest.fixture(scope="session")
def shared_cache_path(tmp_path_factory):
    """One cache dir for the whole test session so the ~19MB game master
    is only downloaded once, not once per test."""
    return str(tmp_path_factory.mktemp("game_master_cache"))


@pytest.fixture(autouse=True)
def isolated_cache(shared_cache_path, monkeypatch):
    """Never touch the developer's real ./cache directory from tests."""
    monkeypatch.setattr(loader.settings, "cache_path", shared_cache_path)


# --- type_chart.py ---------------------------------------------------------

def test_water_vs_fire_is_super_effective():
    assert type_chart.get_effectiveness("WATER", ["FIRE"]) == pytest.approx(1.6)


def test_fire_vs_water_is_not_very_effective():
    assert type_chart.get_effectiveness("FIRE", ["WATER"]) == pytest.approx(0.625)


def test_double_super_effective_stacks_multiplicatively():
    # Electric vs Water/Flying (e.g. Gyarados): both types are weak to Electric.
    assert type_chart.get_effectiveness("ELECTRIC", ["WATER", "FLYING"]) == pytest.approx(1.6 * 1.6)


def test_double_resist_for_mainline_immunity_matchup():
    # Ghost vs Normal is a hard immunity in mainline games; GO has no true
    # immunities, so this becomes a double resist instead.
    assert type_chart.get_effectiveness("GHOST", ["NORMAL"]) == pytest.approx(0.390625)


def test_get_weaknesses_and_resistances_for_fire():
    weaknesses = type_chart.get_weaknesses(["FIRE"])
    resistances = type_chart.get_resistances(["FIRE"])

    assert weaknesses["WATER"] == pytest.approx(1.6)
    assert weaknesses["ROCK"] == pytest.approx(1.6)
    assert weaknesses["GROUND"] == pytest.approx(1.6)

    assert resistances["GRASS"] == pytest.approx(0.625)
    assert resistances["ICE"] == pytest.approx(0.625)
    assert resistances["STEEL"] == pytest.approx(0.625)


# --- data/loader.py ----------------------------------------------------------

def test_fetch_game_master_loads_and_parses():
    game_master = loader.fetch_game_master()

    assert isinstance(game_master, list)
    assert len(game_master) > 1000
    assert any(t.get("templateId") == "PLAYER_LEVEL_SETTINGS" for t in game_master)


def test_get_pokemon_go_stats_medicham():
    # Verified against the live PokeMiners game master: attack and defense
    # match commonly-cited values, but stamina is 155 (not 130).
    stats = loader.get_pokemon_go_stats("medicham")

    assert stats is not None
    assert stats["dex_number"] == 308
    assert stats["base_attack"] == 121
    assert stats["base_defense"] == 152
    assert stats["base_stamina"] == 155
    assert "FIGHTING" in stats["types"]
    assert "PSYCHIC" in stats["types"]


def test_get_pokemon_go_stats_unknown_pokemon_returns_none():
    assert loader.get_pokemon_go_stats("not_a_real_pokemon_xyz") is None


def test_get_all_pokemon_names_includes_known_pokemon():
    names = loader.get_all_pokemon_names()

    assert isinstance(names, list)
    assert len(names) > 500
    assert "MEDICHAM" in names


def test_get_cp_multipliers_matches_real_game_master_values():
    cpms = loader.get_cp_multipliers()

    assert cpms[1.0] == pytest.approx(0.094, abs=1e-4)
    assert cpms[20.0] == pytest.approx(0.5974, abs=1e-4)
    assert 40.0 in cpms
    assert 51.0 in cpms


def test_get_cp_multipliers_sourced_from_game_master_not_hardcoded(monkeypatch):
    """Feeds a synthetic game master with values nothing like the real
    curve, and confirms get_cp_multipliers() reflects exactly that data
    (proving there's no separate hardcoded lookup table backing it up)."""
    fake_game_master = [
        {
            "templateId": "PLAYER_LEVEL_SETTINGS",
            "data": {
                "playerLevel": {
                    "cpMultiplier": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2],
                }
            },
        }
    ]
    monkeypatch.setattr(loader, "fetch_game_master", lambda force_refresh=False: fake_game_master)

    cpms = loader.get_cp_multipliers()

    assert cpms[1.0] == pytest.approx(0.1)
    assert cpms[12.0] == pytest.approx(1.2)
    assert cpms[1.5] == pytest.approx(math.sqrt((0.1**2 + 0.2**2) / 2))
    # Range reflects the fake array's length (12), not a hardcoded 51.
    assert max(cpms) == 12.0


# --- data/cp_calculator.py -----------------------------------------------

MEDICHAM_BASE_ATTACK = 121
MEDICHAM_BASE_DEFENSE = 152
MEDICHAM_BASE_STAMINA = 155


def test_calculate_cp_matches_known_medicham_value():
    # Cross-referenced against both the live game master's CPM data and
    # PvPoke's own published cp1500 IV spread for Medicham.
    cp = cp_calculator.calculate_cp(
        base_attack=MEDICHAM_BASE_ATTACK,
        base_defense=MEDICHAM_BASE_DEFENSE,
        base_stamina=MEDICHAM_BASE_STAMINA,
        iv_attack=7,
        iv_defense=15,
        iv_stamina=14,
        level=49,
    )
    assert cp == 1500


def test_find_level_for_cp_cap_great_league():
    level = cp_calculator.find_level_for_cp_cap(
        base_attack=MEDICHAM_BASE_ATTACK,
        base_defense=MEDICHAM_BASE_DEFENSE,
        base_stamina=MEDICHAM_BASE_STAMINA,
        iv_attack=7,
        iv_defense=15,
        iv_stamina=14,
        cp_cap=1500,
    )
    assert level == 49.0

    cp_at_level = cp_calculator.calculate_cp(
        MEDICHAM_BASE_ATTACK, MEDICHAM_BASE_DEFENSE, MEDICHAM_BASE_STAMINA,
        7, 15, 14, level,
    )
    cp_at_next_half_level = cp_calculator.calculate_cp(
        MEDICHAM_BASE_ATTACK, MEDICHAM_BASE_DEFENSE, MEDICHAM_BASE_STAMINA,
        7, 15, 14, level + 0.5,
    )

    assert cp_at_level <= 1500
    assert cp_at_next_half_level > 1500


def test_calculate_stat_product_is_positive_and_scales_with_level():
    low_level_product = cp_calculator.calculate_stat_product(
        MEDICHAM_BASE_ATTACK, MEDICHAM_BASE_DEFENSE, MEDICHAM_BASE_STAMINA,
        15, 15, 15, level=20,
    )
    high_level_product = cp_calculator.calculate_stat_product(
        MEDICHAM_BASE_ATTACK, MEDICHAM_BASE_DEFENSE, MEDICHAM_BASE_STAMINA,
        15, 15, 15, level=40,
    )

    assert low_level_product > 0
    assert high_level_product > low_level_product
