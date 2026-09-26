"""The sowing calendar and season overview read only the caller's own site — #1870.

``GET /t/{slug}/calendar/sowing?site_id=`` and ``…/season-overview?site_id=``
passed the key to ``CalendarService`` unchecked: the site (frost dates, name),
every run at its locations and their phase timelines were read for any
tenant's key. Only the MCP tool checked first. The service now resolves the
site under the tenant (one check for every caller), reads runs of that tenant
only, and lists the tenant's visible species rather than every tenant's.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine
from app.domain.models.site import Site
from app.domain.services.calendar_service import CalendarService

OWN = "t_a"


class _Sites:
    _sites = {
        "site_a": Site(_key="site_a", tenant_key=OWN, name="Garten A", eisheilige_date=date(2026, 5, 11)),
        "site_b": Site(_key="site_b", tenant_key="t_b", name="Garten B geheim", eisheilige_date=date(2026, 5, 20)),
    }

    def get_site_by_key(self, key: str):
        return self._sites.get(key)


class _Runs:
    def __init__(self) -> None:
        self.asked: list[tuple[str, str]] = []

    def get_runs_at_site(self, site_key: str, *, tenant_key: str):
        self.asked.append((site_key, tenant_key))
        return []


class _Species:
    def __init__(self) -> None:
        self.tenant_keys: list[str | None] = []

    def get_all(self, offset=0, limit=50, *, tenant_key=None):
        self.tenant_keys.append(tenant_key)
        return [], 0

    def is_granted_to(self, species_key: str, tenant_key: str) -> bool:
        return species_key == "sp_granted" and tenant_key == OWN


def _service() -> tuple[CalendarService, _Runs, _Species]:
    runs, species = _Runs(), _Species()
    run_service = MagicMock()
    run_service._repo = runs
    service = CalendarService(
        MagicMock(),
        CalendarAggregationEngine(),
        MagicMock(),
        species_repo=species,  # type: ignore[arg-type]
        site_repo=_Sites(),  # type: ignore[arg-type]
        planting_run_service=run_service,
    )
    return service, runs, species


@pytest.mark.parametrize("site", ["site_b", "no-such-site"], ids=["foreign", "unknown"])
def test_another_tenants_site_answers_404_and_reads_nothing(site: str) -> None:
    service, runs, species = _service()

    with pytest.raises(NotFoundError):
        service.get_sowing_calendar(site, 2026, tenant_key=OWN)
    with pytest.raises(NotFoundError):
        service.get_season_overview(site, 2026, tenant_key=OWN)

    assert runs.asked == []
    assert species.tenant_keys == []


def test_the_own_site_reads_its_frost_dates_and_the_tenants_runs_and_species() -> None:
    service, runs, species = _service()

    _entries, frost = service.get_sowing_calendar("site_a", 2026, tenant_key=OWN)
    overview = service.get_season_overview("site_a", 2026, tenant_key=OWN)

    assert frost.eisheilige_date == date(2026, 5, 11)
    assert overview.site_name == "Garten A"
    assert runs.asked and set(runs.asked) == {("site_a", OWN)}
    assert set(species.tenant_keys) == {OWN}


def test_without_a_site_the_generic_calendar_still_uses_the_tenants_species() -> None:
    service, runs, species = _service()

    service.get_sowing_calendar(None, 2026, tenant_key=OWN)

    assert runs.asked == []
    assert species.tenant_keys == [OWN]


def test_a_run_entry_naming_another_tenants_species_draws_no_bars_from_it() -> None:
    # Security review S1: _species_harvest_bars read any species by key. With an
    # entry naming a foreign private species (#1871 B11) the calendar returned
    # that species' harvest and bloom months.
    from app.domain.models.species import Species

    service, runs, species = _service()
    foreign = Species(_key="sp_foreign", tenant_key="t_b", scientific_name="Secretus privatus", harvest_months=[7, 8])
    species.get_by_key = lambda key: foreign if key == "sp_foreign" else None  # type: ignore[attr-defined]

    assert service._species_harvest_bars("sp_foreign", 2026, tenant_key=OWN) == []


def test_a_species_granted_to_the_tenant_still_draws_its_bars() -> None:
    # #1874 review: the species list admits granted species (#1092); the bars
    # must apply the same rule or the two reads disagree about "visible".
    from app.domain.models.species import Species

    service, _runs, species = _service()
    granted = Species(_key="sp_granted", tenant_key="t_b", scientific_name="Grantus sharedus", harvest_months=[7, 8])
    species.get_by_key = lambda key: granted if key == "sp_granted" else None  # type: ignore[attr-defined]

    assert service._species_harvest_bars("sp_granted", 2026, tenant_key=OWN) != []
