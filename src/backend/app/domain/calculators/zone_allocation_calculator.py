"""Dividing one total over the beds of a zone (REQ-053 GP-FR-117, WP 7.3). Pure.

The shares are rounded to millilitres and the **last** share takes the rounding remainder, so the shares add up to
the total exactly (the acceptance allows ± 0.01 L; this gives 0). A weight of zero or less gets no share: the
caller decides what that means (``by_area`` leaves a bed without an area out and names it).
"""

from __future__ import annotations

from collections.abc import Sequence

_DECIMALS = 3


def divide_volume(total_liters: float, weights: Sequence[float]) -> list[float]:
    """``total_liters`` split in proportion to ``weights`` (all positive); the shares add up to the total."""
    if total_liters <= 0:
        raise ValueError("The total to divide must be positive.")
    if not weights or any(weight <= 0 for weight in weights):
        raise ValueError("Every weight must be positive and there must be at least one.")
    weight_sum = sum(weights)
    shares = [round(total_liters * weight / weight_sum, _DECIMALS) for weight in weights[:-1]]
    shares.append(round(total_liters - sum(shares), _DECIMALS))
    if shares[-1] < 0:
        # A tiny total over many beds: the shares round up and overshoot, so the remainder goes negative.
        return _largest_remainder(total_liters, weights, weight_sum)
    return shares


def _largest_remainder(total_liters: float, weights: Sequence[float], weight_sum: float) -> list[float]:
    """Whole millilitres by floor, the leftover ones to the largest fractions: every share >= 0, the sum exact."""
    scale = 10**_DECIMALS
    total_units = round(total_liters * scale)
    exact = [total_units * weight / weight_sum for weight in weights]
    units = [int(value) for value in exact]
    leftover = total_units - sum(units)
    for index in sorted(range(len(weights)), key=lambda i: (exact[i] - units[i], -i), reverse=True)[:leftover]:
        units[index] += 1
    return [unit / scale for unit in units]
