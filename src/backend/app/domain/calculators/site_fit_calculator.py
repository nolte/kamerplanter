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

**Site axes (GP-FR-161, WP 8.21).** Besides the sun verdict, :func:`assess_axes` names up to three *hints*
beyond the light ladder, each a pure ordinal comparison of one bed feature with one species value, shown
next to the verdict and never blocking:

* ``frost_mismatch``: the bed's ``microclimate.frost_risk`` is ``high`` **and** ``Species.frost_sensitivity``
  is ``sensitive``;
* ``wind_support_needed``: the bed's ``wind_exposure`` is ``exposed`` **and** ``Species.support_required``;
* ``waterlogging_risk``: the bed's ``soil_profile.drainage`` is ``poor`` **and**
  ``Species.waterlogging_tolerance`` is ``sensitive``.

These three cells are the ones the agrobiology review confirmed; every other cell (``high`` x ``moderate``,
``normal`` x ``sensitive``, ``poor`` x ``moderate`` ...) has no source and stays **off** (E-10), and so does
an unknown or missing value on either side: an unknown is no hint, and a missing species value is never read
as "tolerant". ``support_required`` is a flag that defaults to ``false`` (not recorded), so only ``true`` speaks.
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


# Axis hint codes (GP-FR-161); the UI maps each to a sentence (``siteFit.axis.*``).
HINT_FROST_MISMATCH: Final = "frost_mismatch"
HINT_WIND_SUPPORT_NEEDED: Final = "wind_support_needed"
HINT_WATERLOGGING_RISK: Final = "waterlogging_risk"


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


def assess_axes(
    frost_risk: str | None,
    frost_sensitivity: str | None,
    wind_exposure: str | None,
    support_required: bool | None,
    drainage: str | None,
    waterlogging_tolerance: str | None,
) -> list[str]:
    """The axis hints of GP-FR-161 for one bed and one species, in the fixed order frost, wind, waterlogging.

    An empty list is "nothing to say". ``None`` and ``unknown`` on the bed side, ``None`` on the species side
    and every cell without a source give no hint; see the module docstring for the three cells that do.
    """
    hints: list[str] = []
    if str(frost_risk) == "high" and str(frost_sensitivity) == "sensitive":
        hints.append(HINT_FROST_MISMATCH)
    if str(wind_exposure) == "exposed" and support_required is True:
        hints.append(HINT_WIND_SUPPORT_NEEDED)
    if str(drainage) == "poor" and str(waterlogging_tolerance) == "sensitive":
        hints.append(HINT_WATERLOGGING_RISK)
    return hints
