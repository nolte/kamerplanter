"""#2107 (MT-010) — the site service resolves the tenant on every keyed write itself.

The routers used to call ``get_site(key, tenant_key=…)`` / ``_verify_slot_tenant``
and then an unscoped ``update_site(key, …)`` / ``delete_slot(key)``. The check now
lives in the service, so a handler or MCP tool that forgets a pre-check cannot
write into another tenant's site tree. Each write is pinned in both directions:
a foreign key is ``NotFoundError`` and the repository write is never called; the
own key writes.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.site import Location, Site, Slot
from app.domain.services.site_service import SiteService

OWN, FOREIGN = "t-own", "t-foreign"

SITES = {
    "site-own": Site(_key="site-own", tenant_key=OWN, name="Own", type="indoor"),
    "site-foreign": Site(_key="site-foreign", tenant_key=FOREIGN, name="Foreign", type="indoor"),
}
LOCATIONS = {
    "loc-own": Location(_key="loc-own", name="Own", site_key="site-own", area_m2=1),
    "loc-foreign": Location(_key="loc-foreign", name="Foreign", site_key="site-foreign", area_m2=1),
}
SLOTS = {
    "slot-own": Slot(_key="slot-own", slot_id="OWN_A1", location_key="loc-own"),
    "slot-foreign": Slot(_key="slot-foreign", slot_id="FOREIGN_A1", location_key="loc-foreign"),
}


def _or_raise(table: dict, entity: str):
    def lookup(key: str):
        if key not in table:
            raise NotFoundError(entity, key)
        return table[key]

    return lookup


@pytest.fixture
def repo() -> MagicMock:
    repo = MagicMock()
    repo.get_site_or_raise.side_effect = _or_raise(SITES, "Site")
    repo.get_site_by_key.side_effect = SITES.get
    repo.get_location_or_raise.side_effect = _or_raise(LOCATIONS, "Location")
    repo.get_location_by_key.side_effect = LOCATIONS.get
    repo.get_slot_or_raise.side_effect = _or_raise(SLOTS, "Slot")
    repo.get_slot_by_key.side_effect = SLOTS.get
    return repo


def _site(tenant: str = OWN) -> Site:
    return Site(name="Renamed", type="indoor", tenant_key=tenant)


def _slot(location: str = "loc-own") -> Slot:
    return Slot(slot_id="NEW_A1", location_key=location)


#: (service call, repository write it must not reach for a foreign key)
WRITES = [
    (lambda s, k: s.update_site(k, _site(), tenant_key=OWN), "update_site", "site"),
    (lambda s, k: s.delete_site(k, tenant_key=OWN), "delete_site", "site"),
    (lambda s, k: s.delete_location(k, tenant_key=OWN), "delete_location", "loc"),
    (lambda s, k: s.create_slot(_slot(k), tenant_key=OWN), "create_slot", "loc"),
    (lambda s, k: s.update_slot(k, _slot(), tenant_key=OWN), "update_slot", "slot"),
    (lambda s, k: s.delete_slot(k, tenant_key=OWN), "delete_slot", "slot"),
]


@pytest.mark.parametrize(("call", "write", "kind"), WRITES, ids=[w[1] for w in WRITES])
def test_a_foreign_key_is_not_found_and_nothing_is_written(repo, call, write, kind) -> None:
    with pytest.raises(NotFoundError):
        call(SiteService(repo), f"{kind}-foreign")
    getattr(repo, write).assert_not_called()


@pytest.mark.parametrize(("call", "write", "kind"), WRITES, ids=[w[1] for w in WRITES])
def test_the_own_key_writes(repo, call, write, kind) -> None:
    call(SiteService(repo), f"{kind}-own")
    getattr(repo, write).assert_called_once()


@pytest.mark.parametrize(("call", "write", "kind"), WRITES, ids=[w[1] for w in WRITES])
def test_an_empty_tenant_writes_nothing(repo, call, write, kind) -> None:
    """``""`` used to switch the check off (``if tenant_key:``); it is no tenant now."""
    service = SiteService(repo)
    with pytest.raises(NotFoundError):
        call(_EmptyTenant(service), f"{kind}-own")
    getattr(repo, write).assert_not_called()


def test_a_slot_cannot_be_moved_into_a_foreign_location(repo) -> None:
    with pytest.raises(NotFoundError):
        SiteService(repo).update_slot("slot-own", _slot("loc-foreign"), tenant_key=OWN)
    repo.update_slot.assert_not_called()


def test_an_update_cannot_hand_the_site_to_another_tenant(repo) -> None:
    SiteService(repo).update_site("site-own", _site(tenant=FOREIGN), tenant_key=OWN)
    (_, stored), _ = repo.update_site.call_args
    assert stored.tenant_key == OWN


class _EmptyTenant:
    """Re-routes every ``tenant_key=OWN`` call of :data:`WRITES` to ``tenant_key=""``."""

    def __init__(self, service: SiteService) -> None:
        self._service = service

    def __getattr__(self, name: str):
        method = getattr(self._service, name)

        def call(*args, **kwargs):
            kwargs["tenant_key"] = ""
            return method(*args, **kwargs)

        return call
