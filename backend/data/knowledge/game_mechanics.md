# Pokemon GO Mechanics Reference

Evergreen game mechanics that don't shift with the meta — unlike move
rebalances or the current best Pokemon per league, these rules haven't
changed in years and don't need to be re-fetched from anywhere.

## Individual Values (IVs)

Every Pokemon has three hidden Individual Values: Attack, Defense, and
Stamina, each ranging from 0 to 15. IVs are fixed per catch/hatch/trade
and add directly onto a Pokemon's base stats before the CP multiplier
(CPM) for its level is applied. A "perfect" Pokemon has 15/15/15 IVs; a
"hundo" is community slang for exactly that.

## Why PvP Wants Different IVs Than PvE

For PvE (raids, gyms, general damage output), higher IVs are always
better — especially Attack, since it scales linearly in the CP formula
and directly increases damage per hit. Maximize all three IVs if you
can.

For PvP, the picture flips because leagues are capped by CP (see
below), not by level. A Pokemon can only be powered up until its CP
hits the cap. Since Attack contributes linearly to CP while Defense
and Stamina contribute via square root, a *lower* Attack IV lets you
power up to a *higher level* before hitting the CP cap — and that
extra level adds more Defense and Stamina (bulk) than the Attack IV
points you gave up. This is why the best Great League IV spreads for
many Pokemon look unintuitive, like a 0 Attack IV paired with 14-15
Defense/Stamina IVs, rather than a "perfect" 15/15/15 spread.

## Stat Product: The PvP Evaluation Metric

```
stat_product = effective_attack * effective_defense * effective_hp
```

where each effective stat is `(base_stat + iv) * cpm` for the
Pokemon's level (HP is additionally floored, since displayed HP is
always a whole number). This is the metric PvP players actually rank
IV spreads by, rather than raw CP — because CP formula overweights
Attack (linear) relative to Defense/Stamina (square root), ranking by
CP alone would bias toward high-attack, low-bulk spreads even when a
bulkier spread survives more hits and performs better overall. Stat
product treats all three stats symmetrically, which is a much better
proxy for "how good is this Pokemon in a real battle."

(See `backend/data/cp_calculator.py`'s `calculate_stat_product` for
the implementation this project uses.)

## CP Caps by League

- **Great League**: 1500 CP cap
- **Ultra League**: 2500 CP cap
- **Master League**: no cap — Pokemon battle at their maximum level
  (typically level 50-51), so raw stats and movesets matter more than
  IV optimization

## Shadow and Purified Pokemon

Shadow Pokemon (caught from Team GO Rocket) get an Attack multiplier
of **1.2x** (+20%) and a Defense multiplier of **~0.8333x**. That
defense number is worth calling out explicitly because it's commonly
misstated as a flat "-20%" (0.8x) — it's actually the mathematical
reciprocal of the attack buff (1 / 1.2 ≈ 0.8333), which works out to
roughly **-16.67%** defense, not -20%. Shadow Pokemon also always know
Frustration (a weak Normal-type charged move) until purified.

Purifying a Shadow Pokemon removes both the attack buff and the
defense penalty, restoring its normal base stats, replaces Frustration
with Return, and resets its IVs to a guaranteed-high floor.

## XL Candy and Level 40+

Pokemon can be powered up to level 40 using normal Candy and Stardust.
Going beyond level 40 (up to a level 50 cap) requires **XL Candy**
instead of regular Candy, starting at 40 required. XL Candy is
significantly harder to obtain than regular Candy (primarily from
catching, hatching, and weekly raid/research rewards rather than
walking with a buddy), which is why pushing a Pokemon to its max
Ultra/Master League level is a much bigger investment than reaching
level 40.

## Weather Boost

When the in-game weather matches a Pokemon's type (e.g. Sunny/Clear
boosts Fire, Grass, and Ground types), that Pokemon gets:

- **1.2x** move power on all its moves (both fast and charged)
- +5 to the maximum level of wild-encountered Pokemon during that
  weather (raising the ceiling on CP/IVs you might find)
- A guaranteed IV floor of 4 (out of 15) on each stat for
  weather-boosted wild encounters

Weather-boosted Pokemon are also visually marked with a sparkle
animation in the overworld.

## Stardust Costs

Stardust and Candy costs for powering up scale with level: they're
cheap at low levels (a few hundred Stardust and 1 Candy per power-up)
and climb into the thousands of Stardust plus multiple Candy per
power-up near the CP-cap-relevant levels for competitive PvP builds.
XL Candy costs for levels 41-50 climb further still, from around 10
XL Candy per power-up near level 40 up to roughly 20 XL Candy per
power-up near level 50.

Unlocking a Pokemon's second charged move (or rerolling it) also costs
Stardust plus Candy, with the cost scaling by the Pokemon's rarity
tier — a common Pokemon might cost 10,000-50,000 Stardust, while
rarer/evolved Pokemon can cost significantly more (Medicham, for
example, costs 50,000 Stardust and 50 Candy to unlock a second move).
