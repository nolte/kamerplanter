"""Plant states of a bed for the plan's markers and info bubbles (REQ-053 GP-FR-190…192, GP-API-054, WP 3.7).

``GET /locations/{key}/plant-states`` answers one window of a bed's standing plants with the state the marker
draws (:mod:`app.domain.calculators.plant_state_calculator`) and the facts of the info bubble. The client
renders hover, focus and tap from this one answer — no request per plant (GP-FR-191).

**Ownership is resolved here, never in the router** (T-01…T-04, #2107): :meth:`list_plant_states` takes
``*, tenant_key: str`` without a default and resolves the bed through
:func:`app.domain.services.location_ownership.resolve_owned_location` before anything is read. A foreign and
an absent bed answer identically (404).

**Frost** (:meth:`_frost_risk`) has no source yet: the bed's ``microclimate.frost_risk`` arrives with WP 3.9
(GP-FR-162). Until then the reason is absent (operator question 2 of #2455), which §11.4 allows (a missing source
drops its reason without an error); the calculator and its vectors already cover it.

**Logs carry no user text** (GP-NFR-060): keys and counts only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from app.domain.calculators.plant_state_calculator import (
    PhaseFacts,
    PlantFacts,
    PlantVisualState,
    compute,
)
from app.domain.interfaces.plant_state_repository import IPlantStateRepository, PlantStateSource
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.site import Location
from app.domain.services.location_ownership import resolve_owned_location

logger = structlog.get_logger()


@dataclass(frozen=True)
class PlantStateEntry:
    """A plant's raw facts with the visual state computed from them."""

    source: PlantStateSource
    state: PlantVisualState
    #: The frost input the state was computed with; the client recomputes with the same input.
    frost_risk: bool = False


def phase_facts(row: PlantStateSource) -> PhaseFacts | None:
    """The phase the calculator reads; a phase without a recorded start counts from the planting day."""
    if not row.phase_key:
        return None
    return PhaseFacts(
        key=row.phase_key,
        started_on=row.phase_started_on or row.planted_on,
        typical_days=row.phase_typical_days,
        allows_harvest=row.phase_allows_harvest,
        is_terminal=row.phase_is_terminal,
    )


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
        frost_risk = self._frost_risk(location)
        entries = [
            PlantStateEntry(row, self._state_of(row, frost_risk=frost_risk, now=moment), frost_risk) for row in rows
        ]
        logger.info("plant_states.listed", location_key=location_key, plants=len(entries))
        return entries

    @staticmethod
    def _frost_risk(location: Location) -> bool:
        """Whether the bed is at frost risk now; ``False`` until WP 3.9 adds ``microclimate.frost_risk``."""
        del location
        return False

    @staticmethod
    def _state_of(row: PlantStateSource, *, frost_risk: bool, now: datetime) -> PlantVisualState:
        return compute(
            PlantFacts(),
            phase_facts(row),
            row.open_tasks,
            open_findings=row.open_finding_count,
            frost_risk=frost_risk,
            harvest_batches=row.harvest_batch_count,
            now=now,
        )
