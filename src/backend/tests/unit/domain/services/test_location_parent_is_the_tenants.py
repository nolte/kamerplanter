"""A new location may only be nested under a location of the caller's own tenant — #1864 bundle (L1).

``POST /t/{slug}/locations`` verified ``body.site_key`` and then
``SiteService.create_location`` resolved ``parent_location_key`` **without a
tenant**, copied the parent's ``site_key`` over the verified one and wrote a
``CONTAINS`` edge from the parent: a member of tenant A could graft a location
into tenant B's tree (it then shows in B's tree and B's deletes cascade into it),
and the 201 echoed B's site key and the parent's path. The repository double is
the one ``test_site_service_location_tenant`` uses — locations carry no
``tenant_key``, only their site does, as in production.
"""

from __future__ import annotations

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.site import Location
from app.domain.services.site_service import SiteService
from tests.unit.domain.services.test_site_service_location_tenant import OWN, FakeSiteRepo


class _Repo(FakeSiteRepo):
    def __init__(self) -> None:
        super().__init__()
        self.created: list[Location] = []

    def get_site_or_raise(self, key):
        site = self._sites.get(key)
        if site is None:
            raise NotFoundError("Site", key)
        return site

    def create_location(self, location: Location) -> Location:
        self.created.append(location)
        return location


def _new(parent: str | None) -> Location:
    return Location(name="Neu", area_m2=1.0, site_key="site_own", parent_location_key=parent)


@pytest.mark.parametrize("parent", ["loc_foreign", "no-such-location"], ids=["foreign", "unknown"])
def test_a_location_cannot_be_nested_under_another_tenants_location(parent: str) -> None:
    repo = _Repo()

    with pytest.raises(NotFoundError):
        SiteService(repo).create_location(_new(parent), tenant_key=OWN)

    assert repo.created == []


def test_the_site_must_be_the_tenants_too() -> None:
    repo = _Repo()
    location = Location(name="Neu", area_m2=1.0, site_key="site_foreign")

    with pytest.raises(NotFoundError):
        SiteService(repo).create_location(location, tenant_key=OWN)

    assert repo.created == []


def test_nesting_under_the_tenants_own_location_works() -> None:
    repo = _Repo()

    created = SiteService(repo).create_location(_new("loc_own"), tenant_key=OWN)

    assert created.site_key == "site_own"
    assert created.depth == 1


def test_the_tenant_is_keyword_only_without_a_default() -> None:
    import inspect

    param = inspect.signature(SiteService.create_location).parameters["tenant_key"]

    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is inspect.Parameter.empty
