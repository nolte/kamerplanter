"""Plant states of a bed for the plan's markers and info bubbles (REQ-053 GP-FR-190…192, GP-API-054, WP 3.7).

``GET /locations/{key}/plant-states`` answers one window of a bed's standing plants with the state the marker
draws (:mod:`app.domain.calculators.plant_state_calculator`) and the facts of the info bubble. The client
renders hover, focus and tap from this one answer — no request per plant (GP-FR-191).

**Ownership is resolved here, never in the router** (T-01…T-04, #2107): :meth:`list_plant_states` takes
``*, tenant_key: str`` without a default and resolves the bed through
:func:`app.domain.services.location_ownership.resolve_owned_location` before anything is read. A foreign and
an absent bed answer identically (404).

**The state is assembled in** :mod:`app.domain.calculators.plant_state_inputs` — the same function the plan's SVG/PDF
export uses, so a plant has the same ring and badge on the screen and on paper (#2489). Frost is a live reason
(:func:`~app.domain.services.plant_state_inputs.frost_risk_of`, WP 8.20): a ``high`` bed and a frost predicted for
its site; without a forecast source there is no frost reason.

**Sown slots come first** (§11.3 "gesät", W-015): a ``row``/``zone`` slot with ``sown_at`` and no plant yet is an
entry of its own (:class:`~app.domain.interfaces.plant_state_repository.SownSlotSource`, lifecycle ``sown``). The
answer is the sown slots (by slot key) followed by the plants (by plant key), and ``offset``/``limit`` window that
one sequence — a client paging until a short page sees every entry exactly once.

**Logs carry no user text** (GP-NFR-060): keys and counts only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import structlog

from app.domain.calculators.plant_state_calculator import PlantVisualState
from app.domain.calculators.plant_state_inputs import sown_visual_state, visual_state_of
from app.domain.interfaces.plant_state_repository import IPlantStateRepository, PlantStateSource, SownSlotSource
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.weather_forecast_repository import IWeatherForecastRepository
from app.domain.models.species_names import CANONICAL_NAME_LANGUAGE
from app.domain.services.frost_forecast import read_site_frost_verdict
from app.domain.services.location_ownership import resolve_owned_location
from app.domain.services.plant_state_inputs import frost_risk_of

logger = structlog.get_logger()


@dataclass(frozen=True)
class PlantStateEntry:
    """A plant's (or a sown slot's) raw facts with the visual state computed from them."""

    source: PlantStateSource | SownSlotSource
    state: PlantVisualState
    #: The frost input the state was computed with; the client recomputes with the same input.
    frost_risk: bool = False


class PlantStateService:
    def __init__(
        self, sites: ISiteRepository, repo: IPlantStateRepository, forecasts: IWeatherForecastRepository | None = None
    ) -> None:
        self._sites = sites
        self._repo = repo
        #: ``None`` = no forecast source: no frost reason.
        self._forecasts = forecasts

    def list_plant_states(
        self,
        location_key: str,
        *,
        tenant_key: str,
        offset: int = 0,
        limit: int = 50,
        now: datetime | None = None,
        language: str = CANONICAL_NAME_LANGUAGE,
    ) -> list[PlantStateEntry]:
        """A window of the bed's sown slots (by slot key) followed by its standing plants (by plant key).

        Species names are worded in ``language`` (#2902)."""
        location = resolve_owned_location(self._sites, location_key, tenant_key)
        moment = now if now is not None else datetime.now(UTC)
        sown = self._repo.list_sown_slots(location_key, tenant_key=tenant_key, language=language)
        sown_window = sown[offset : offset + limit]
        plant_limit = limit - len(sown_window)
        rows = (
            self._repo.list_bed_plants(
                location_key,
                tenant_key=tenant_key,
                now=moment,
                offset=max(offset - len(sown), 0),
                limit=plant_limit,
                language=language,
            )
            if plant_limit > 0
            else []
        )
        # The forecast is read only for a window that holds plants (no extra statement for an empty page).
        verdict = (
            read_site_frost_verdict(self._forecasts, location.site_key, tenant_key=tenant_key, now=moment)
            if rows
            else None
        )
        frost_risk = frost_risk_of(location, verdict)
        entries = [PlantStateEntry(slot, sown_visual_state(moment)) for slot in sown_window]
        entries.extend(
            PlantStateEntry(row, visual_state_of(row, frost_risk=frost_risk, now=moment), frost_risk) for row in rows
        )
        logger.info("plant_states.listed", location_key=location_key, plants=len(rows), sown=len(sown_window))
        return entries


__all__ = ["PlantStateEntry", "PlantStateService", "SownSlotSource"]
