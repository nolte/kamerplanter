"""The two global routers that address a plant by key resolve a tenant (#1402 group C).

`/plant-instances/{plant_key}/phases/*` and `/care-reminders/plants/{plant_key}/*`
carry no `/t/{slug}` segment, so `get_current_tenant` structurally cannot bind
there, and until #1402 neither resolved a tenant at all. Every operation on both
took a plant key from the path and handed it to a by-key lookup.

**Eleven operations, not the two #1402 names.** The issue lists
`POST /phases/transition` and `DELETE /phases/history/{key}`; measured, all five
phase operations and all six care-reminder operations were unscoped. The reads
leak another tenant's phase history and care log exactly as the writes change
them.

`CareReminderService.confirm_reminder` is the sharper half: it *has* an ownership
check, written `if tenant_key and self._plant_repo is not None:`, and the REST
router called it without a `tenant_key`. Its own comment says "when a caller
passes its `tenant_key` (the MCP path always does)" — the REST path did not, so
the check never ran and a confirmation wrote a `WateringLog` stamped into the
victim's tenant. The #1042 shape: documented as enforced, wired nowhere.

Doubled vs real
---------------
Real: `get_active_tenant_key` and its whole resolution path, `require_owned_plant`,
`PlantInstanceService.get_plant` with `verify_tenant_ownership`, and both routers.
Doubled: the authenticated user, `TenantService`, the plant repository, and the
two domain services behind the handlers — everything that would otherwise be
ArangoDB.

The resolver is deliberately **not** overridden. Overriding it would move the rule
under test into the double, which is how the original defect survived: the check
existed and nothing drove it.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.care_reminders.router import router as care_router
from app.api.v1.phases.router import router as phases_router
from app.common.auth import ACTIVE_TENANT_HEADER, get_current_user
from app.common.dependencies import (
    get_care_reminder_service,
    get_phase_service,
    get_plant_instance_service,
    get_tenant_service,
)
from app.common.enums import AdminScope, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_instance_service import PlantInstanceService

_USER = "user_1"
_OWN = SimpleNamespace(key="tenant_own", slug="my-garden")
_FOREIGN = SimpleNamespace(key="tenant_foreign", slug="other-garden")

_OWN_HEADER = {ACTIVE_TENANT_HEADER: _OWN.slug}

OWN_PLANT = "plant_own"
FOREIGN_PLANT = "plant_foreign"

#: Every write route, with a body the schema accepts. The point of the table is
#: that it is a TABLE: a hand-picked pair would prove the two routes #1402 names
#: and say nothing about the other nine.
ROUTES: list[tuple[str, str, dict[str, Any] | None]] = [
    ("GET", "/api/v1/plant-instances/{k}/phases/current", None),
    ("POST", "/api/v1/plant-instances/{k}/phases/transition", {"target_phase_key": "gp_veg", "force": True}),
    ("GET", "/api/v1/plant-instances/{k}/phases/history", None),
    ("PATCH", "/api/v1/plant-instances/{k}/phases/history/h1", {"entered_at": "2026-01-01T00:00:00Z"}),
    ("DELETE", "/api/v1/plant-instances/{k}/phases/history/h1", None),
    ("GET", "/api/v1/care-reminders/plants/{k}/profile", None),
    ("PATCH", "/api/v1/care-reminders/plants/{k}/profile", {}),
    ("POST", "/api/v1/care-reminders/plants/{k}/confirm", {"reminder_type": "watering"}),
    ("POST", "/api/v1/care-reminders/plants/{k}/snooze", {"reminder_type": "watering", "snooze_days": 1}),
    ("GET", "/api/v1/care-reminders/plants/{k}/history", None),
    ("POST", "/api/v1/care-reminders/plants/{k}/reset-profile", None),
]


class _FakeTenantService:
    """Slug→tenant and membership, without ArangoDB. Same contract as the header suite."""

    def __init__(self) -> None:
        self._by_slug = {t.slug: t for t in (_OWN, _FOREIGN)}
        self._memberships = {
            (_USER, _OWN.key): SimpleNamespace(
                role=TenantRole.LEAD, admin_scopes=[AdminScope.MANAGEMENT], is_active=True
            ),
        }

    def get_personal_tenant(self, user_key: str) -> SimpleNamespace | None:
        return _OWN if user_key == _USER else None

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        tenant = self._by_slug.get(slug)
        if tenant is None:
            raise NotFoundError("tenants", slug)
        return tenant

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        return self._memberships.get((user_key, tenant_key))


class _FakePlantRepo:
    """Two plants in two tenants. `get_or_raise` is by key and unscoped — as production's is."""

    def __init__(self) -> None:
        self._plants = {
            OWN_PLANT: PlantInstance(
                _key=OWN_PLANT,
                instance_id="own-1",
                species_key="sp",
                planted_on=date(2026, 1, 1),
                tenant_key=_OWN.key,
            ),
            FOREIGN_PLANT: PlantInstance(
                _key=FOREIGN_PLANT,
                instance_id="foreign-1",
                species_key="sp",
                planted_on=date(2026, 1, 1),
                tenant_key=_FOREIGN.key,
            ),
        }

    def get_or_raise(self, key: str) -> PlantInstance:
        plant = self._plants.get(key)
        if plant is None:
            raise NotFoundError("PlantInstance", key)
        return plant


def _app() -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(phases_router, prefix="/api/v1")
    app.include_router(care_router, prefix="/api/v1")

    # The REAL service, so `get_plant` -> `verify_tenant_ownership` runs the
    # production predicate. Only its repository is doubled; the three collaborators
    # below are constructor requirements this path never reaches.
    plant_service = PlantInstanceService(
        _FakePlantRepo(),  # type: ignore[arg-type]
        site_repo=MagicMock(),
        rotation_validator=MagicMock(),
        companion_engine=MagicMock(),
    )

    # The handlers themselves are doubled: this file is about the GATE, and a real
    # PhaseService would need a phase repository, a sequence repository and a
    # transition engine to answer at all — none of which decides who may call.
    phase_service = MagicMock()
    phase_service.get_current_phase.return_value = {"phase_key": "gp_veg", "phase_name": "Vegetative"}
    phase_service.get_phase_history.return_value = []

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key=_USER, account_type="user")
    app.dependency_overrides[get_tenant_service] = _FakeTenantService
    app.dependency_overrides[get_plant_instance_service] = lambda: plant_service
    app.dependency_overrides[get_phase_service] = lambda: phase_service
    app.dependency_overrides[get_care_reminder_service] = MagicMock
    return TestClient(app, raise_server_exceptions=False)


def _call(client: TestClient, method: str, path: str, body: dict[str, Any] | None):
    return client.request(method, path, json=body, headers=_OWN_HEADER)


@pytest.fixture(autouse=True)
def _full_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """`light` mode resolves every caller to the system user, which would bypass the gate."""
    from app.config.settings import settings

    monkeypatch.setattr(settings, "kamerplanter_mode", "full")


@pytest.mark.parametrize(("method", "template", "body"), ROUTES, ids=lambda v: v if isinstance(v, str) else "")
class TestAForeignPlantIsRefusedOnEveryRoute:
    def test_a_foreign_plant_is_refused(self, method: str, template: str, body: dict[str, Any] | None):
        response = _call(_app(), method, template.format(k=FOREIGN_PLANT), body)

        assert response.status_code == 404, (
            f"{method} {template} answered {response.status_code} for a plant owned by another tenant"
        )

    def test_the_refusal_does_not_disclose_that_the_plant_exists(
        self, method: str, template: str, body: dict[str, Any] | None
    ):
        """404 and not 403, and the same 404 an unknown key gets.

        A 403 would confirm the key names a real plant somewhere — the ownership
        oracle REQ-049 §2.4 closes. The two answers must be indistinguishable.
        """
        foreign = _call(_app(), method, template.format(k=FOREIGN_PLANT), body)
        unknown = _call(_app(), method, template.format(k="plant_does_not_exist"), body)

        assert foreign.status_code == unknown.status_code == 404

    def test_the_caller_own_plant_is_admitted(self, method: str, template: str, body: dict[str, Any] | None):
        """The control, and it carries the weight.

        A gate that refuses everything satisfies both assertions above. This is
        what separates "scoped" from "broken".
        """
        response = _call(_app(), method, template.format(k=OWN_PLANT), body)

        assert response.status_code not in (401, 403, 404), (
            f"{method} {template} refused the caller's OWN plant with {response.status_code}: {response.text}"
        )


class TestTheTableCoversTheWholeSurface:
    """A hand-written table is the next thing to drift (#948), so it is checked against the routers."""

    def test_every_mounted_operation_is_in_the_table(self):
        mounted = set()
        for router, prefix in ((phases_router, "/api/v1"), (care_router, "/api/v1")):
            for route in router.routes:
                for method in route.methods:
                    mounted.add((method, prefix + route.path))

        tabled = {(m, t.replace("{k}", "{plant_key}").replace("/h1", "/{history_key}")) for m, t, _ in ROUTES}

        missing = sorted(mounted - tabled)
        assert not missing, "These operations are mounted and untested:\n  " + "\n  ".join(map(str, missing))
