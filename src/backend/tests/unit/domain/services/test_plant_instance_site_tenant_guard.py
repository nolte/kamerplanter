"""Service tests for PlantInstance site_key tenant-ownership guard (Issue #719).

The create/update paths re-verify a client-supplied ``site_key`` against the
plant's tenant before persisting: a foreign or unknown site is rejected with
:class:`NotFoundError` and the write path (``repo.create`` / ``repo.update``) is
never reached — closing the same IDOR that #717 closed for locations. Moving a
plant between the caller's *own* sites still works. Sites carry a real
``tenant_key`` (unlike Location docs, #706), so the guard is anchored directly on
the resolved site and is not inert.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.common.enums import SiteType
from app.common.exceptions import NotFoundError
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Site
from app.domain.services.plant_instance_service import PlantInstanceService

TENANT = "tenant-anna"
FOREIGN = "tenant-bob"


class FakeSiteRepo:
    """Minimal site repository fake keyed on site_key → Site."""

    def __init__(self, sites: dict[str, Site]) -> None:
        self.sites = sites

    def get_site_by_key(self, key: str) -> Site | None:
        return self.sites.get(key)

    def get_slot_by_key(self, key):  # pragma: no cover - unused in these tests
        return None

    def update_slot(self, key, slot):  # pragma: no cover - unused in these tests
        return slot


def _site(key: str, tenant: str = TENANT, site_type: SiteType = SiteType.INDOOR) -> Site:
    return Site(key=key, tenant_key=tenant, name=key, type=site_type, climate_zone="")


def _plant(site_key: str | None, *, key: str | None = None, tenant: str = TENANT) -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key=tenant,
        instance_id="i1",
        species_key="species-1",
        planted_on=date(2024, 1, 1),
        site_key=site_key,
    )


def _service(sites: dict[str, Site]) -> tuple[PlantInstanceService, MagicMock]:
    """Build a service with a MagicMock plant_repo so writes are observable.

    No phase / overwintering collaborators are wired: the guard runs before any of
    them, and the create/update happy paths degrade to a plain ``repo.create`` /
    ``repo.update`` when the optional collaborators are absent.
    """
    plant_repo = MagicMock()
    plant_repo.create.side_effect = lambda p: p
    plant_repo.update.side_effect = lambda key, p: p
    site_repo = FakeSiteRepo(sites)
    service = PlantInstanceService(plant_repo, site_repo, MagicMock(), MagicMock())
    return service, plant_repo


# ── create_plant ────────────────────────────────────────────────────────


def test_create_with_own_site_succeeds_and_persists() -> None:
    service, plant_repo = _service({"site-own": _site("site-own")})

    created = service.create_plant(_plant("site-own"), tenant_key=TENANT)

    assert created.site_key == "site-own"
    plant_repo.create.assert_called_once()


def test_create_with_foreign_site_raises_and_does_not_persist() -> None:
    service, plant_repo = _service({"site-foreign": _site("site-foreign", tenant=FOREIGN)})

    with pytest.raises(NotFoundError):
        service.create_plant(_plant("site-foreign"), tenant_key=TENANT)

    plant_repo.create.assert_not_called()


def test_create_with_unknown_site_raises_and_does_not_persist() -> None:
    service, plant_repo = _service({})

    with pytest.raises(NotFoundError):
        service.create_plant(_plant("site-ghost"), tenant_key=TENANT)

    plant_repo.create.assert_not_called()


def test_create_without_site_key_skips_guard() -> None:
    service, plant_repo = _service({})

    created = service.create_plant(_plant(None), tenant_key=TENANT)

    assert created.site_key is None
    plant_repo.create.assert_called_once()


def test_create_without_a_tenant_is_refused_instead_of_skipping_the_guard() -> None:
    """#2107: an empty tenant used to skip the site check; it now fails closed.

    The skip existed for "internal callers / tests without a tenant context". The
    measured callers of ``create_plant`` are the tenant route and the onboarding
    wizard, both with a tenant, so the escape protected nothing and left a write
    that checked no site.
    """
    service, plant_repo = _service({})

    with pytest.raises(ValueError, match="tenant_key"):
        service.create_plant(_plant("site-anything", tenant=""), tenant_key="")

    plant_repo.create.assert_not_called()


def test_create_stamps_the_callers_tenant_over_the_models() -> None:
    """#2107: the argument, not a field of the model, is the tenant the plant is created in."""
    service, plant_repo = _service({"site-own": _site("site-own")})

    created = service.create_plant(_plant("site-own", tenant=FOREIGN), tenant_key=TENANT)

    assert created.tenant_key == TENANT
    plant_repo.create.assert_called_once()


# ── update_plant ────────────────────────────────────────────────────────


def test_update_keeping_own_site_succeeds() -> None:
    service, plant_repo = _service({"site-own": _site("site-own")})
    plant_repo.get_or_raise.return_value = _plant("site-own", key="plant-1")

    updated = service.update_plant("plant-1", _plant("site-own", key="plant-1"), tenant_key=TENANT)

    assert updated.site_key == "site-own"
    plant_repo.update.assert_called_once()


def test_update_moving_between_own_sites_succeeds() -> None:
    service, plant_repo = _service(
        {
            "site-a": _site("site-a"),
            "site-b": _site("site-b"),
        }
    )
    plant_repo.get_or_raise.return_value = _plant("site-a", key="plant-1")

    updated = service.update_plant("plant-1", _plant("site-b", key="plant-1"), tenant_key=TENANT)

    assert updated.site_key == "site-b"
    plant_repo.update.assert_called_once()


def test_update_moving_to_foreign_site_raises_and_does_not_persist() -> None:
    service, plant_repo = _service(
        {
            "site-a": _site("site-a"),
            "site-foreign": _site("site-foreign", tenant=FOREIGN),
        }
    )
    plant_repo.get_or_raise.return_value = _plant("site-a", key="plant-1")

    with pytest.raises(NotFoundError):
        service.update_plant("plant-1", _plant("site-foreign", key="plant-1"), tenant_key=TENANT)

    plant_repo.update.assert_not_called()


def test_update_moving_to_unknown_site_raises_and_does_not_persist() -> None:
    service, plant_repo = _service({"site-a": _site("site-a")})
    plant_repo.get_or_raise.return_value = _plant("site-a", key="plant-1")

    with pytest.raises(NotFoundError):
        service.update_plant("plant-1", _plant("site-ghost", key="plant-1"), tenant_key=TENANT)

    plant_repo.update.assert_not_called()


# ── #2107: the stored plant is verified in the service, not only by the route ──


def test_update_of_a_foreign_tenants_plant_is_refused_and_does_not_persist() -> None:
    """``update_plant`` re-read the stored plant without a tenant; the route's pre-read was the only check."""
    # No site on the plant, so the site check (#719) cannot be what refuses it — only the ownership check can.
    service, plant_repo = _service({})
    plant_repo.get_or_raise.return_value = _plant(None, key="plant-1", tenant=FOREIGN)

    with pytest.raises(NotFoundError):
        service.update_plant("plant-1", _plant(None, key="plant-1", tenant=FOREIGN), tenant_key=TENANT)

    plant_repo.update.assert_not_called()


def test_remove_of_a_foreign_tenants_plant_is_refused_and_does_not_persist() -> None:
    """``remove_plant``'s ``tenant_key=""`` default skipped the ownership check for a caller that left it out."""
    service, plant_repo = _service({})
    plant_repo.get_or_raise.return_value = _plant(None, key="plant-1", tenant=FOREIGN)

    with pytest.raises(NotFoundError):
        service.remove_plant("plant-1", tenant_key=TENANT)

    plant_repo.update.assert_not_called()
