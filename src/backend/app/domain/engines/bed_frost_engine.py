"""Bed-level frost rules (REQ-053 GP-FR-162, GP-FR-192; REQ-392 early warning, WP 8.20).

Two consumers read the *same* rule and therefore share this module: the site's frost early warning
(``tasks/frost_forecast_tasks``) names the beds at frost risk, and a plant's visual state carries the frost reason
(``services/plant_state_inputs.frost_risk_of``). Both call :func:`bed_frost_flagged` for the bed side and
:func:`~app.domain.services.frost_forecast.site_frost_verdict` for the forecast side, so the two cannot drift apart.

The rule (operator decision, #2643 question 2): a bed with ``microclimate.frost_risk = high`` is named in the warning
whenever the site warns and shows the frost reason while a frost is predicted within the horizon; ``low`` is never
named; ``normal`` and ``unknown`` are not named either (the warning stays per site). There is no temperature offset
per bed (E-10): the threshold is the site's, unchanged.

Pure, no I/O (engine layer).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from app.common.enums import FrostRisk

if TYPE_CHECKING:
    from app.domain.models.site import Location


def bed_frost_flagged(location: Location) -> bool:
    """Whether the bed itself is marked as frost-prone: ``microclimate.frost_risk`` is ``high``.

    ``low``, ``normal``, ``unknown`` and a bed without site conditions are not.
    """
    conditions = location.site_conditions
    return conditions is not None and conditions.microclimate.frost_risk is FrostRisk.HIGH


def named_frost_beds(locations: Iterable[Location]) -> list[Location]:
    """The beds the early warning names: every ``high`` bed, ordered by name then key; never a ``low`` one."""
    flagged = [loc for loc in locations if bed_frost_flagged(loc)]
    return sorted(flagged, key=lambda loc: (loc.name.casefold(), loc.key or ""))


def frost_reason_active(location: Location, prediction: dict[str, Any]) -> bool:
    """The frost reason of a plant's state: the bed is ``high`` **and** the site's verdict predicts a frost."""
    return bed_frost_flagged(location) and prediction.get("predicted") is True
