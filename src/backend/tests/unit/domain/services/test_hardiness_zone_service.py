"""REQ-039 — unit tests for :class:`HardinessZoneService` (auto-fill + guards)."""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.engines.hardiness_zone_resolver import zone_bounds_c, zone_bounds_f
from app.domain.models.hardiness_zone import HardinessZone
from app.domain.models.site import Site
from app.domain.models.weather import ClimateNormal
from app.domain.services.hardiness_zone_service import HardinessZoneService


def _zone(label: str, **overrides) -> HardinessZone:
    index_min_c, index_max_c = zone_bounds_c(12)
    min_f, max_f = zone_bounds_f(12)
    data = {
        "zone": label,
        "zone_number": int(label[:-1]),
        "subzone": label[-1],
        "temp_min_c": index_min_c,
        "temp_max_c": index_max_c,
        "temp_min_f": min_f,
        "temp_max_f": max_f,
        "description_de": "Testzone",
        "typical_last_frost_md": "05-15",
        "typical_first_frost_md": "10-10",
    }
    data.update(overrides)
    return HardinessZone(**data)


def _site(**overrides) -> Site:
    data = {
        "_key": "site1",
        "tenant_key": "t1",
        "name": "Beet",
        "type": "outdoor",
        "gps_coordinates": (52.5, 13.4),
    }
    data.update(overrides)
    return Site(**data)


def _normal(**overrides) -> ClimateNormal:
    data = {
        "site_key": "site1",
        "tenant_key": "t1",
        "source": "nasa-power",
        "fetched_at": datetime.now(tz=UTC),
        "coldest_month_min_c": -17.0,  # 1.4 °F → 7a
        "monthly_temp_min_c": [-17.0] * 12,
    }
    data.update(overrides)
    return ClimateNormal(**data)


def _service(site, normals, zone_doc=_zone("7a")):
    site_repo = MagicMock()
    site_repo.get_site_by_key.return_value = site
    site_repo.update_site.side_effect = lambda key, updated: updated
    climate_repo = MagicMock()
    climate_repo.get_by_site.return_value = normals
    zone_repo = MagicMock()
    zone_repo.get_by_zone.return_value = zone_doc
    service = HardinessZoneService(zone_repo=zone_repo, site_repo=site_repo, climate_normal_repo=climate_repo)
    return service, site_repo, climate_repo, zone_repo


class TestResolveForSite:
    def test_derives_zone_and_persists(self) -> None:
        service, site_repo, _climate, zone_repo = _service(_site(), [_normal()])

        result = service.resolve_for_site("site1", "t1")

        assert result.hardiness_zone == "7a"
        assert result.hardiness_zone_source == "derived_gps"
        assert result.mean_annual_minimum_c == -17.0
        # Legacy free-text field kept in sync for the ampel fallback.
        assert result.climate_zone == "7a"
        assert result.hardiness_zone_resolved_at is not None
        site_repo.update_site.assert_called_once()
        zone_repo.assign_site_to_zone.assert_called_once()
        _, kwargs = zone_repo.assign_site_to_zone.call_args
        assert kwargs["source"] == "derived_gps"

    def test_fills_frost_defaults_when_unset(self) -> None:
        service, _repo, _climate, _zone = _service(_site(), [_normal()])

        result = service.resolve_for_site("site1", "t1")

        assert result.last_frost_date_avg == date(datetime.now(tz=UTC).year, 5, 15)
        assert result.first_frost_date_avg == date(datetime.now(tz=UTC).year, 10, 10)

    def test_does_not_overwrite_existing_frost_dates(self) -> None:
        existing = date(2020, 4, 1)
        site = _site(last_frost_date_avg=existing, first_frost_date_avg=existing)
        service, _repo, _climate, _zone = _service(site, [_normal()])

        result = service.resolve_for_site("site1", "t1")

        assert result.last_frost_date_avg == existing
        assert result.first_frost_date_avg == existing

    def test_manual_zone_is_protected(self) -> None:
        site = _site(hardiness_zone="6b", hardiness_zone_source="manual")
        service, site_repo, climate_repo, zone_repo = _service(site, [_normal()])

        result = service.resolve_for_site("site1", "t1")

        assert result.hardiness_zone == "6b"
        assert result.hardiness_zone_source == "manual"
        site_repo.update_site.assert_not_called()
        climate_repo.get_by_site.assert_not_called()
        zone_repo.assign_site_to_zone.assert_not_called()

    def test_force_overrides_manual_zone(self) -> None:
        site = _site(hardiness_zone="6b", hardiness_zone_source="manual")
        service, site_repo, _climate, _zone = _service(site, [_normal()])

        result = service.resolve_for_site("site1", "t1", force=True)

        assert result.hardiness_zone == "7a"
        assert result.hardiness_zone_source == "derived_gps"
        site_repo.update_site.assert_called_once()

    def test_missing_normals_raise_422(self) -> None:
        service, site_repo, _climate, zone_repo = _service(_site(), [])

        with pytest.raises(ValidationError):
            service.resolve_for_site("site1", "t1")
        site_repo.update_site.assert_not_called()
        zone_repo.assign_site_to_zone.assert_not_called()

    def test_normals_without_minimum_raise_422(self) -> None:
        # A coarse foundation record carrying neither a coldest-month nor monthly min.
        blank = ClimateNormal(site_key="site1", tenant_key="t1", source="nasa-power", fetched_at=datetime.now(tz=UTC))
        service, _repo, _climate, _zone = _service(_site(), [blank])

        with pytest.raises(ValidationError):
            service.resolve_for_site("site1", "t1")

    def test_foreign_tenant_is_not_found(self) -> None:
        service, _repo, _climate, _zone = _service(_site(tenant_key="other"), [_normal()])

        with pytest.raises(NotFoundError):
            service.resolve_for_site("site1", "t1")

    def test_unknown_site_is_not_found(self) -> None:
        service, site_repo, _climate, _zone = _service(_site(), [_normal()])
        site_repo.get_site_by_key.return_value = None

        with pytest.raises(NotFoundError):
            service.resolve_for_site("site1", "t1")


class TestGetSiteHardiness:
    def test_returns_site_and_zone_doc(self) -> None:
        site = _site(hardiness_zone="7a", hardiness_zone_source="derived_gps")
        service, _repo, _climate, _zone = _service(site, [])

        got_site, zone_doc = service.get_site_hardiness("site1", "t1")

        assert got_site is site
        assert zone_doc is not None
        assert zone_doc.zone == "7a"

    def test_no_zone_yields_none_doc(self) -> None:
        service, _repo, _climate, zone_repo = _service(_site(hardiness_zone=None), [])

        _got, zone_doc = service.get_site_hardiness("site1", "t1")

        assert zone_doc is None
        zone_repo.get_by_zone.assert_not_called()


class TestCatalog:
    def test_get_zone_raises_when_absent(self) -> None:
        service, _repo, _climate, zone_repo = _service(_site(), [])
        zone_repo.get_by_zone.return_value = None

        with pytest.raises(NotFoundError):
            service.get_zone("99a")
