"""Class (A, B, C, NEW) per material and channel, and the SKU score weight."""

from __future__ import annotations

from reshelf.ids import MatChan
from reshelf.schema import AbcClass, CanonicalDataset, Params


def classify_pairs(dataset: CanonicalDataset) -> dict[MatChan, AbcClass]:
    """Class of every (material, channel) pair of a material that has stock.

    A pair that never sold in the channel is NEW: past sales cannot forecast it. A pair with
    sales keeps the ABC class of the material, or C when the material has no ABC row.
    """
    abc = {a.material: a.abc_class for a in dataset.abc}
    history = {(d.material, d.channel) for d in dataset.demand if d.has_history}
    out: dict[MatChan, AbcClass] = {}
    for material in sorted({lot.material for lot in dataset.lots}):
        for channel in dataset.channels:
            pair = (material, channel.channel)
            out[pair] = abc.get(material, "C") if pair in history else "NEW"
    return out


def rank_table(dataset: CanonicalDataset) -> tuple[dict[str, int], int]:
    """Rank per material and N, the number of ranked materials."""
    return {a.material: a.rank for a in dataset.abc}, len(dataset.abc)


def score_weight(params: Params, abc_class: AbcClass, rank: int | None, n_ranked: int) -> float:
    """w = base[class] + rank_weight x (1 - rank / N). A missing rank counts as the lowest, N."""
    if n_ranked == 0:
        bonus = 0.0
    else:
        bonus = 1.0 - min(rank if rank is not None else n_ranked, n_ranked) / n_ranked
    return params.score_base[abc_class] + params.score_rank_weight * bonus
