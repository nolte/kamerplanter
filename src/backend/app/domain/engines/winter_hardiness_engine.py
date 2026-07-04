"""REQ-039 / REQ-022 winter hardiness engine — pure domain logic, no I/O.

Unifies the winter hardiness traffic light (REQ-022 §"Winterhärte-Ampel") on a
numeric USDA-zone comparison (REQ-039 ``evaluate_winter_hardiness``) and enforces
the D5 consistency invariant that binds ``OverwinteringProfile.winter_action`` to
the derived winter path.
"""

import re
from typing import Literal

from app.common.enums import FrostTolerance, WinterAction, WinterHardinessLight
from app.common.exceptions import WinterPathViolationError
from app.domain.models.overwintering_profile import OverwinteringProfile

#: Code-enum :class:`FrostTolerance` → spec ampel vocabulary (hardy/half_hardy/
#: tender). REQ-022 note: VERY_HARDY+HARDY → "hardy", MODERATE → "half_hardy",
#: SENSITIVE → "tender".
_FROST_SENSITIVITY_MAP: dict[FrostTolerance, Literal["hardy", "half_hardy", "tender"]] = {
    FrostTolerance.VERY_HARDY: "hardy",
    FrostTolerance.HARDY: "hardy",
    FrostTolerance.MODERATE: "half_hardy",
    FrostTolerance.SENSITIVE: "tender",
}

#: Winter paths (D5). Path A = in-situ (green/yellow), Path B = relocated (red).
WinterPath = Literal["A", "B"]

_PATH_A_ACTIONS: frozenset[WinterAction] = frozenset(
    {WinterAction.NONE, WinterAction.MULCH, WinterAction.FLEECE, WinterAction.EARTH_UP, WinterAction.WRAP}
)
_PATH_B_ACTIONS: frozenset[WinterAction] = frozenset({WinterAction.MOVE_INDOORS, WinterAction.DIG_STORE})

_ZONE_PATTERN = re.compile(r"(\d+)\s*([ab])?", re.IGNORECASE)


def map_frost_sensitivity(
    frost_sensitivity: FrostTolerance | None,
) -> Literal["hardy", "half_hardy", "tender"] | None:
    """Map the code-level :class:`FrostTolerance` onto the spec ampel vocabulary."""
    if frost_sensitivity is None:
        return None
    return _FROST_SENSITIVITY_MAP.get(frost_sensitivity)


def parse_zone(zone: str | None) -> float | None:
    """Parse a USDA hardiness zone to a comparable number.

    ``"7b" -> 7.5``, ``"8a" -> 8.0``, ``"7" -> 7.0``. Tolerates prefixes such as
    ``"USDA 7b"`` / ``"z7"``. Returns ``None`` when no zone number is present.
    """
    if not zone:
        return None
    match = _ZONE_PATTERN.search(zone)
    if match is None:
        return None
    number = float(match.group(1))
    if match.group(2) and match.group(2).lower() == "b":
        number += 0.5
    return number


def _zone_delta(species_zone: str | None, site_zone: str | None) -> float | None:
    """Return ``site_zone - species_zone`` (positive = site warmer than required)."""
    species_num = parse_zone(species_zone)
    site_num = parse_zone(site_zone)
    if species_num is None or site_num is None:
        return None
    return site_num - species_num


def evaluate_winter_hardiness(
    frost_sensitivity: FrostTolerance | None,
    species_zone: str | None,
    site_zone: str | None,
) -> WinterHardinessLight:
    """Compute the winter hardiness traffic light (REQ-022 / REQ-039).

    - **green**: hardy AND the site zone covers the species requirement
      (``species_zone <= site_zone``);
    - **yellow**: half_hardy OR the zone gap is marginal (site at/just below need);
    - **red**: tender OR the site is more than one zone too cold.

    Robust for missing zones: with no zone data the result is driven by
    ``frost_sensitivity`` alone (hardy→green, half_hardy→yellow, tender→red);
    with neither zone nor sensitivity known it defaults to **yellow** (the safe
    "check it" state) rather than a false all-clear.
    """
    mapped = map_frost_sensitivity(frost_sensitivity)
    delta = _zone_delta(species_zone, site_zone)

    if mapped == "tender" or (delta is not None and delta < -1):
        return WinterHardinessLight.RED
    if mapped == "half_hardy" or (delta is not None and delta <= 0):
        return WinterHardinessLight.YELLOW
    if mapped is None and delta is None:
        return WinterHardinessLight.YELLOW
    return WinterHardinessLight.GREEN


def derive_winter_path(light: WinterHardinessLight) -> WinterPath:
    """green/yellow → path A (in-situ); red → path B (relocated)."""
    return "B" if light == WinterHardinessLight.RED else "A"


def validate_d5_invariant(profile: OverwinteringProfile, light: WinterHardinessLight) -> None:
    """Enforce the D5 winter-path invariant (REQ-022 §"Konsistenz-Invariante D5").

    Path A (green/yellow) ⇒ ``winter_action`` ∈ {none, mulch, fleece, earth_up,
    wrap}; Path B (red) ⇒ ``winter_action`` ∈ {move_indoors, dig_store}.
    Raises :class:`WinterPathViolationError` (HTTP 422) on contradiction.
    """
    path = derive_winter_path(light)
    if path == "A" and profile.winter_action not in _PATH_A_ACTIONS:
        raise WinterPathViolationError(
            profile.winter_action.value,
            path,
            sorted(a.value for a in _PATH_A_ACTIONS),
        )
    if path == "B" and profile.winter_action not in _PATH_B_ACTIONS:
        raise WinterPathViolationError(
            profile.winter_action.value,
            path,
            sorted(a.value for a in _PATH_B_ACTIONS),
        )
