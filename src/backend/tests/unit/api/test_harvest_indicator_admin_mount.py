"""Harvest indicators are written from the platform-admin mount only (#1249).

`HarvestIndicator` is global master data: no `tenant_key`, keyed on
`species_key`, and read with no tenant predicate. REQ-007 §4's rights table has
always said so — create/update/delete are `Plattform-Admin`. The create endpoint
nevertheless sat on the tenant mount behind
`require_permission(HARVEST, CREATE)`, so a grower in any tenant could write a
record every tenant then reads.

The route's own module is asserted through the OpenAPI document rather than
`app.routes`: `include_router` does not flatten routes onto the application, so
a scan over `app.routes` finds only the docs routes and reads as correct while
proving nothing.
"""

from __future__ import annotations

import inspect

import pytest

TENANT_PATH = "/api/v1/t/{tenant_slug}/harvest/indicators"
ADMIN_PATH = "/api/v1/admin/harvest-indicators"


@pytest.fixture(scope="module")
def paths() -> dict:
    from app.main import app

    return app.openapi()["paths"]


def test_the_write_is_served_from_the_admin_mount(paths) -> None:
    assert "post" in paths[ADMIN_PATH]


def test_the_tenant_mount_serves_reads_only(paths) -> None:
    """The regression: a POST here is the defect, whatever guards it."""
    assert set(paths[TENANT_PATH]) == {"get"}


def test_the_admin_route_is_platform_admin_gated() -> None:
    """Not merely 'off the tenant mount' — the gate itself.

    Moving the route without the gate would satisfy the two assertions above
    and leave it open to any authenticated caller.
    """
    from app.api.v1.admin.harvest_indicators.router import create_indicator
    from app.common.auth import require_platform_admin

    dependency = inspect.signature(create_indicator).parameters["_user"].default.dependency
    assert dependency is require_platform_admin


def test_the_tenant_router_no_longer_imports_the_write_gate_for_indicators() -> None:
    """Guards against the route being re-added beside the reads.

    `require_permission` is still used by this router for genuinely
    tenant-scoped resources, so its presence is not the signal — a POST on the
    indicators path is, and the OpenAPI assertion above carries that. This test
    states the source-level intent that the handler is gone.
    """
    from app.api.v1.harvest import tenant_router

    source = inspect.getsource(tenant_router)
    assert '@router.post("/indicators"' not in source
