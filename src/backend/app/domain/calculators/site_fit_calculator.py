"""Site fit: does a bed's sun class meet a species' light requirement? (REQ-053 GP-FR-160, E-05).

A pure function, no I/O. Python is the reference; ``features/gardenPlanner/model/siteFit.ts`` is the
port, and both run against the ``site_fit`` cases of
``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (§19.6). The block is generic —
``site_suitability``: a bed feature against a species demand — and REQ-054 reuses it as a criterion.

Rules, over the ladder ``full_sun > partial_shade > shade > deep_shade``:

* the bed's ``sun_exposure`` equals the species' ``light_requirement`` → ``ok``;
* the bed is **shadier** than required: one step → ``marginal`` when ``shade_tolerance`` reaches down to
  the bed's step, ``marginal`` with the reason ``tolerance_unknown`` when the tolerance is not recorded
  (no silent ``poor``), otherwise ``poor``; two steps or more → ``poor``;
* the bed is **sunnier** than required (woodruff on a full-sun bed: scorch, drought stress): one step →
  ``marginal``, two or more → ``poor``;
* either side unknown (``unknown`` bed class, no ``light_requirement``) → ``unknown``.

``shade_tolerance`` is the tolerance ("grows down to this step") and never derives the requirement
(E-05): ``light_requirement`` is a separate, sourced Steckbrief value (E-10).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.common.enums import SiteFit, SunExposure

#: Position on the ladder; the higher, the sunnier. ``unknown`` is not on it.
_LADDER: Final[dict[str, int]] = {"deep_shade": 0, "shade": 1, "partial_shade": 2, "full_sun": 3}

#: A species' ``light_requirement`` is one of these (``deep_shade`` is a bed class, not a demand).
REQUIREMENT_VALUES: Final[frozenset[str]] = frozenset({"full_sun", "partial_shade", "shade"})

# Reasons, in the order the matrix reads. The UI maps each to a sentence (``siteFit.reason.*``).
REASON_MATCH: Final = "match"
REASON_TOO_SHADY: Final = "too_shady"
REASON_TOLERATED: Final = "tolerated"
REASON_TOLERANCE_UNKNOWN: Final = "tolerance_unknown"
REASON_TOO_SUNNY: Final = "too_sunny"
REASON_BED_UNKNOWN: Final = "bed_unknown"
REASON_REQUIREMENT_UNKNOWN: Final = "requirement_unknown"


@dataclass(frozen=True)
class SiteFitResult:
    """The verdict and the reason code the UI turns into plain text."""

    fit: SiteFit
    reason: str
    #: Steps between the bed and the requirement; negative = shadier than required.
    steps: int = 0


def _rank(value: str | SunExposure | None) -> int | None:
    return _LADDER.get(str(value)) if value is not None else None


def assess(
    sun_exposure: str | SunExposure | None,
    light_requirement: str | None,
    shade_tolerance: str | None,
) -> SiteFitResult:
    """Compare the bed with the species; see the module docstring for the matrix."""
    bed = _rank(sun_exposure)
    if bed is None:
        return SiteFitResult(SiteFit.UNKNOWN, REASON_BED_UNKNOWN)
    required = _rank(light_requirement) if light_requirement in REQUIREMENT_VALUES else None
    if required is None:
        return SiteFitResult(SiteFit.UNKNOWN, REASON_REQUIREMENT_UNKNOWN)

    steps = bed - required
    if steps == 0:
        return SiteFitResult(SiteFit.OK, REASON_MATCH, 0)
    if steps > 0:
        fit = SiteFit.MARGINAL if steps == 1 else SiteFit.POOR
        return SiteFitResult(fit, REASON_TOO_SUNNY, steps)
    if steps <= -2:
        return SiteFitResult(SiteFit.POOR, REASON_TOO_SHADY, steps)
    # Exactly one step shadier: the tolerance decides.
    tolerance = _rank(shade_tolerance)
    if tolerance is None:
        return SiteFitResult(SiteFit.MARGINAL, REASON_TOLERANCE_UNKNOWN, steps)
    if tolerance <= bed:
        return SiteFitResult(SiteFit.MARGINAL, REASON_TOLERATED, steps)
    return SiteFitResult(SiteFit.POOR, REASON_TOO_SHADY, steps)


def compute(
    sun_exposure: str | SunExposure | None,
    light_requirement: str | None,
    shade_tolerance: str | None,
) -> SiteFit:
    """``site_fit_calculator.compute(sun_exposure, light_requirement, shade_tolerance)`` of GP-FR-160."""
    return assess(sun_exposure, light_requirement, shade_tolerance).fit
