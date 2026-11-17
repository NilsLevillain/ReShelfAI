# ADR 010: Why a unit is destroyed

Status: accepted (2026-11-17).

## Context
In the 30 SKU demo world the plan places 6 percent of the stock and destroys the rest. A planner could not see why, nor which rule to change. The rule trace explains the lines that are in the plan. It says nothing about the units that are not.

## Decision
`destruction.py` gives every unit that is not placed one cause. The causes are named after what a planner can do, not after solver constraints. The split adds up to the units destroyed, and a test checks that on every run.

Per material, in this order:
1. `blocked`: a lot has no admissible channel at all (shelf life, brand tier or push rule removed all of them).
2. `no_demand`: the lots can go to some channels, but the ceiling `upper` of every channel is 0 for this product.
3. `coverage_ceiling` and `push_ceiling`: units above the sum of `upper` over the channels that carry the product. Split in proportion to the ceiling that comes from coverage (established products) and the ceiling that comes from the push quantity (new products).
4. `sku_limit`, `capacity`, `group_limit`, `not_worth`: the remaining units, where there was room under the ceiling. Each channel pair with room is credited to the tight limit of that channel (read from the same slack the rule trace uses), or to `not_worth` when no limit is tight. The units are shared out in proportion to the room of each pair, largest remainder first, so the parts are whole numbers and the result is deterministic.

Each cause names the scenario parameter that moves it (`coverage_days`, `push_quantity_units`, `channel_sku_limit_scale`), or none when the cause comes from the world (shelf life, capacity, brand rules).

`channel_sku_limit_scale` is an editor only parameter. It is not a ZPARAM row. The API applies it to `max_skus` of every channel type when the world is built.

## Consequences
* Upside: the Plan page answers "why is stock destroyed" in words, with a button to the rule that moves each cause. A planner can test a rule and see the cause shrink.
* Downside: the split is an attribution, not a proof. When several limits bind at once, the units are shared by room, not by what a re solve would show. The counterfactual (ADR 007) stays the exact answer for one rule.
* Downside: the units are split per material, so two lots of one material share one ceiling. This is exact for the ceiling and approximate for the limits.
* The default world is dominated by the coverage ceiling (68 percent) and the push ceiling (29 percent). Capacity never binds there. The scenarios `max_recovery` and `shelf_life_strict` exist to show a planner what moving these levers does.
