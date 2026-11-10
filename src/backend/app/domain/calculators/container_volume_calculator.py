"""The pot-volume check of a planting (REQ-053 §9.2a, W-016.5) - pure, a warning and never a refusal.

In a tent the pot, not the spacing, limits the plant: a pot smaller than the species' recommendation
(``Species.recommended_container_volume_l``, a Steckbrief range string such as ``"5-10"``) is worth a warning.
The rule is **one** rule for both ends: the planting dialog runs ``containerCheck`` in
``features/gardenPlanner/planting/plantingLogic.ts`` before the request, the server runs this one on what arrives,
and both run against the operation ``container_volume`` of ``spec/e2e-testcases/fixtures/garden-plan-vectors.json``.

**Reading the recommendation.** The lower value of the range is the recommendation: the leading number of the
string, a decimal comma allowed (``"1,5-3"`` → 1.5), anything after it ignored (``"10-20 L"`` → 10). A string
that does not start with a number, a non-positive value or no value at all is *no recommendation* (``None``):
nothing is assumed (E-10), and without a recommendation there is no warning.

**The comparison.** Strictly below: a pot of exactly the recommended volume is fine.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

# ``re.ASCII``: ``\d`` is 0-9 as in the ECMAScript twin.
_LEADING_NUMBER: re.Pattern[str] = re.compile(r"^\s*(\d+(?:[.,]\d+)?)", re.ASCII)


def recommended_volume_l(value: str | float | None) -> float | None:
    """The lower value of a recommended container volume, in litres; ``None`` when there is no usable one."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        number = float(value)
        return number if math.isfinite(number) and number > 0 else None
    match: re.Match[str] | None = _LEADING_NUMBER.match(value)
    if match is None:
        return None
    number = float(match.group(1).replace(",", "."))
    return number if math.isfinite(number) and number > 0 else None


@dataclass(frozen=True)
class ContainerVolumeCheck:
    #: The pot is smaller than the species' recommendation.
    volume_below: bool
    #: The recommendation read from the species (litres); ``None`` without one.
    recommended_l: float | None


def check_container_volume(container_volume_l: float | None, recommended: str | float | None) -> ContainerVolumeCheck:
    """W-016.5: whether the pot volume is below the species' recommended volume."""
    recommended_l = recommended_volume_l(recommended)
    below = container_volume_l is not None and recommended_l is not None and container_volume_l < recommended_l
    return ContainerVolumeCheck(volume_below=below, recommended_l=recommended_l)
