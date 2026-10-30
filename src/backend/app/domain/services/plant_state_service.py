"""Plant states of a bed for the plan's markers and info bubbles (REQ-053 GP-FR-190…192, GP-API-054, WP 3.7).

``GET /locations/{key}/plant-states`` answers one window of a bed's standing plants with the state the marker
draws (:mod:`app.domain.calculators.plant_state_calculator`) and the facts of the info bubble. The client
renders hover, focus and tap from this one answer — no request per plant (GP-FR-191).

**Ownership is resolved here, never in the router** (T-01…T-04, #2107): :meth:`list_plant_states` takes
``*, tenant_key: str`` without a default and resolves the bed through
:func:`app.domain.services.location_ownership.resolve_owned_location` before anything is read. A foreign and
an absent bed answer identically (404).

**The state is assembled in** :mod:`app.domain.calculators.plant_state_inputs` — the same function the plan's SVG/PDF
export uses, so a plant has the same ring and badge on the screen and on paper (#2489). Frost has no source yet
(:func:`~app.domain.services.plant_state_inputs.frost_risk_of`, WP 3.9).

**Logs carry no user text** (GP-NFR-060): keys and counts only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from app.domain.calculators.plant_state_calculator import PlantVisualState
from app.domain.calculators.plant_state_inputs import visual_state_of
from app.domain.interfaces.plant_state_repository import IPlantStateRepository, PlantStateSource
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.services.location_ownership import resolve_owned_location
from app.domain.services.plant_state_inputs import frost_risk_of

logger = structlog.get_logger()


@dataclass(frozen=True)
class PlantStateEntry:
    """A plant's raw facts with the visual state computed from them."""

    source: PlantStateSource
    state: PlantVisualState
    #: The frost input the state was computed with; the client recomputes with the same input.
    frost_risk: bool = False


class PlantStateService:
    def __init__(self, sites: ISiteRepository, repo: IPlantStateRepository) -> None:
        self._sites = sites
        self._repo = repo

    def list_plant_states(
        self,
        location_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
        now: datetime | None = None,
    ) -> list[PlantStateEntry]:
        """A window of the standing plants of the bed with their visual state, ordered by plant key."""
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        moment = now if now is not None else datetime.now(UTC)
        rows = self._repo.list_bed_plants(location_key, tenant_key=tenant_key, now=moment, offset=offset, limit=limit)
        frost_risk = frost_risk_of(location)
        entries = [
            PlantStateEntry(row, visual_state_of(row, frost_risk=frost_risk, now=moment), frost_risk) for row in rows
        ]
        logger.info("plant_states.listed", location_key=location_key, plants=len(entries))
        return entries
