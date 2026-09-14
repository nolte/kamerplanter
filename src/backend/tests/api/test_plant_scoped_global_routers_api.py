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

from datetime import UTC, date, datetime
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
from app.common.enums import AdminScope, ConfirmAction, ReminderType, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_instance_service import PlantInstanceService

_USER = "user_1"
_SERVICE = "svc_1"
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

    def __init__(self, role: TenantRole = TenantRole.LEAD) -> None:
        # The role is a parameter because #1422 is about rank, and a fake that hard-codes
        # `LEAD` can only ever demonstrate that a lead is admitted. Every pre-existing
        # case keeps the default and is unaffected.
        self._by_slug = {t.slug: t for t in (_OWN, _FOREIGN)}
        member = SimpleNamespace(role=role, admin_scopes=[AdminScope.MANAGEMENT], is_active=True)
        self._memberships = {
            (_USER, _OWN.key): member,
            # A service account bound to a tenant holds a membership there like any
            # other principal: with a header, `_membership_for_slug` runs the same
            # validated route a `/t/{slug}/` segment takes, for every account type.
            # Without one it resolves `""` by design (auth.py:251), which is the case
            # `TestACallerWhoseTenantDoesNotResolveIsRefused` drives.
            (_SERVICE, _OWN.key): member,
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


def _doubled_services() -> tuple[Any, Any]:
    """Phase and care services that answer what the response schemas accept.

    Shallow doubles were not enough once the admission control demanded a 2xx
    rather than merely "not 401/403/404". Two things bit:

    * `app.dependency_overrides[dep] = MagicMock` passes the CLASS, so FastAPI
      introspects `MagicMock.__init__` and demands query parameters named `args`
      and `kw` — every call answered 422 and the loose control read that as
      admitted. It has to be `lambda: MagicMock()`.
    * a `MagicMock` return value does not serialise through a response model, so
      the handlers answered 500 — also invisible to the loose control.

    Both are harness defects, and both were hidden by an assertion that only
    excluded the refusal codes. That is the shape this file exists to catch, one
    level down.
    """
    phase = MagicMock()
    phase.get_current_phase.return_value = {
        "phase": "Vegetative",
        "phase_key": "gp_veg",
        "days_in_phase": 3,
        "next_phase": "Flowering",
    }
    phase.get_phase_history.return_value = []
    plant = PlantInstance(
        _key=OWN_PLANT,
        instance_id="own-1",
        species_key="sp",
        planted_on=date(2026, 1, 1),
        tenant_key=_OWN.key,
    )
    phase.transition_phase.return_value = plant
    phase.update_phase_history_dates.return_value = PhaseHistory(
        _key="h1",
        plant_key=OWN_PLANT,
        phase_key="gp_veg",
        entered_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    phase.delete_phase_history.return_value = None

    care = MagicMock()
    profile = CareProfile(_key="cp1", plant_key=OWN_PLANT)
    care.get_or_create_profile.return_value = profile
    care.update_profile.return_value = profile
    care.reset_profile.return_value = profile
    confirmation = CareConfirmation(
        _key="cc1",
        plant_key=OWN_PLANT,
        care_profile_key="cp1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    care.confirm_reminder.return_value = confirmation
    care.snooze_reminder.return_value = confirmation
    care.get_confirmation_history.return_value = []
    return phase, care


def _app(role: TenantRole = TenantRole.LEAD) -> TestClient:
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

    phase_service, care_service = _doubled_services()

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key=_USER, account_type="user")
    app.dependency_overrides[get_tenant_service] = lambda: _FakeTenantService(role)
    app.dependency_overrides[get_plant_instance_service] = lambda: plant_service
    app.dependency_overrides[get_phase_service] = lambda: phase_service
    app.dependency_overrides[get_care_reminder_service] = lambda: care_service
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

        assert response.status_code < 400, (
            f"{method} {template} did not admit the caller's OWN plant: {response.status_code} {response.text}"
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


class TestACallerWhoseTenantDoesNotResolveIsRefused:
    """The class the first version of this gate admitted, and it is the whole point.

    `_resolve_active_tenant` answers `""` for a **service account** with no
    `X-Active-Tenant` header — pinned deliberately at `auth.py:251` so a header-less
    M2M call cannot silently act inside a tenant — and for any user without a
    personal tenant. `PlantInstanceService.get_plant` reads a falsy `tenant_key` as
    *skip the check*, because its own service makes unscoped system-context reads
    through it.

    So the same value meant "narrow to global-only" at one end and "do not narrow"
    at the other, and delegating the decision made `require_owned_plant` **inert**
    for those callers: measured, a service principal with no header answered 200
    with a foreign tenant's phase data.

    The suite above could not see it — its fake tenant service hands the test user a
    personal tenant, and the user is `account_type="user"`. Both properties are what
    this class varies.
    """

    def _client_for(self, principal: SimpleNamespace, *, header: bool) -> TestClient:
        app = FastAPI()
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.include_router(phases_router, prefix="/api/v1")
        app.include_router(care_router, prefix="/api/v1")

        plant_service = PlantInstanceService(
            _FakePlantRepo(),  # type: ignore[arg-type]
            site_repo=MagicMock(),
            rotation_validator=MagicMock(),
            companion_engine=MagicMock(),
        )
        phase_service, care_service = _doubled_services()

        app.dependency_overrides[get_current_user] = lambda: principal
        app.dependency_overrides[get_tenant_service] = _FakeTenantService
        app.dependency_overrides[get_plant_instance_service] = lambda: plant_service
        app.dependency_overrides[get_phase_service] = lambda: phase_service
        app.dependency_overrides[get_care_reminder_service] = lambda: care_service
        client = TestClient(app, raise_server_exceptions=False)
        if header:
            client.headers[ACTIVE_TENANT_HEADER] = _OWN.slug
        return client

    @pytest.mark.parametrize(
        ("principal", "header", "what"),
        [
            (SimpleNamespace(key=_SERVICE, account_type="service"), False, "a service account with no header"),
            (SimpleNamespace(key="nobody", account_type="user"), False, "a user with no personal tenant"),
        ],
    )
    def test_an_unresolvable_tenant_reaches_no_plant(self, principal: SimpleNamespace, header: bool, what: str):
        client = self._client_for(principal, header=header)

        for target in (OWN_PLANT, FOREIGN_PLANT):
            response = client.get(f"/api/v1/plant-instances/{target}/phases/current")
            assert response.status_code == 404, (
                f"{what} read plant {target} with {response.status_code}; the gate resolved an "
                "empty tenant key and `get_plant` treated that as 'skip the check'"
            )

    def test_a_service_account_that_does_send_a_header_is_still_scoped(self):
        """The control: refusing the empty key must not refuse a resolvable one.

        A service account that names its tenant is a legitimate M2M caller, and a
        gate that refused it would break the MCP surface REQ-033 exists for.
        """
        client = self._client_for(SimpleNamespace(key=_SERVICE, account_type="service"), header=True)

        own = client.get(f"/api/v1/plant-instances/{OWN_PLANT}/phases/current")
        foreign = client.get(f"/api/v1/plant-instances/{FOREIGN_PLANT}/phases/current")

        assert own.status_code == 200, own.text
        assert foreign.status_code == 404


class TestTheServiceOwnCheckIsReachedOnTheRestPath:
    """The half of the #1042 shape this module's docstring names.

    `CareReminderService.confirm_reminder` carries its own SEC-001 ownership
    re-check, written `if tenant_key and self._plant_repo is not None:`. Its only
    REST caller passed no `tenant_key`, so that branch ran for MCP and never here:
    a guard sitting in the service, beside the route it was written for, doing
    nothing on it.

    The router-level `require_owned_plant` already refuses a foreign plant, so this
    is defence in depth rather than the only line — which is exactly why it needs a
    witness. A second layer nobody asserts is a second layer nobody notices losing.

    Asserted on the argument the service receives, not on the status code: a 201
    is returned either way, which is what let this sit unnoticed.
    """

    def test_confirm_passes_the_resolved_tenant_to_the_service(self):
        app = FastAPI()
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.include_router(care_router, prefix="/api/v1")

        plant_service = PlantInstanceService(
            _FakePlantRepo(),  # type: ignore[arg-type]
            site_repo=MagicMock(),
            rotation_validator=MagicMock(),
            companion_engine=MagicMock(),
        )
        _, care_service = _doubled_services()
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key=_USER, account_type="user")
        app.dependency_overrides[get_tenant_service] = _FakeTenantService
        app.dependency_overrides[get_plant_instance_service] = lambda: plant_service
        app.dependency_overrides[get_care_reminder_service] = lambda: care_service
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            f"/api/v1/care-reminders/plants/{OWN_PLANT}/confirm",
            json={"reminder_type": "watering"},
            headers=_OWN_HEADER,
        )

        assert response.status_code == 201, response.text
        care_service.confirm_reminder.assert_called_once()
        passed = care_service.confirm_reminder.call_args.kwargs.get("tenant_key")
        assert passed == _OWN.key, (
            f"the service received tenant_key={passed!r}; its own ownership branch is "
            "guarded by `if tenant_key` and therefore does not run"
        )


#: The seven write routes, with the rank REQ-049 §2.3 puts on each.
#:
#: Spelled out rather than filtered out of ``ROUTES`` by HTTP method: the whole point
#: of #1422 is that ``DELETE`` sits at a different rank from the other six, and a
#: derivation that computed the rank from the method would encode that rule in the
#: test instead of checking it.
WRITE_ROUTES_WITH_RANK: list[tuple[str, str, dict[str, Any] | None, TenantRole]] = [
    (
        "POST",
        "/api/v1/plant-instances/{k}/phases/transition",
        {"target_phase_key": "gp_veg", "force": True},
        TenantRole.GROWER,
    ),
    (
        "PATCH",
        "/api/v1/plant-instances/{k}/phases/history/h1",
        {"entered_at": "2026-01-01T00:00:00Z"},
        TenantRole.GROWER,
    ),
    # The irreversibility boundary REQ-049 §2.3 names explicitly.
    ("DELETE", "/api/v1/plant-instances/{k}/phases/history/h1", None, TenantRole.LEAD),
    ("PATCH", "/api/v1/care-reminders/plants/{k}/profile", {}, TenantRole.GROWER),
    ("POST", "/api/v1/care-reminders/plants/{k}/confirm", {"reminder_type": "watering"}, TenantRole.GROWER),
    (
        "POST",
        "/api/v1/care-reminders/plants/{k}/snooze",
        {"reminder_type": "watering", "snooze_days": 1},
        TenantRole.GROWER,
    ),
    ("POST", "/api/v1/care-reminders/plants/{k}/reset-profile", None, TenantRole.GROWER),
]


def test_the_rank_table_covers_every_write_route_in_the_route_table():
    """The two tables must not drift, or a new write route is checked by nothing.

    ``ROUTES`` is the file's inventory of every route on both routers;
    ``WRITE_ROUTES_WITH_RANK`` is the subset that must carry a rank gate. Derived
    here rather than trusted: a route added to ``ROUTES`` with a write method and
    forgotten below would otherwise be covered by no rank test at all — the opt-in
    drift #948 is about, one level up in the test suite.
    """
    writes_in_inventory = {(method, template) for method, template, _body in ROUTES if method != "GET"}
    ranked = {(method, template) for method, template, _body, _rank in WRITE_ROUTES_WITH_RANK}

    assert writes_in_inventory == ranked, (
        f"write routes with no rank expectation: {sorted(writes_in_inventory - ranked)}; "
        f"ranked routes that are not in ROUTES: {sorted(ranked - writes_in_inventory)}"
    )


@pytest.mark.parametrize(
    ("method", "template", "body", "min_role"),
    WRITE_ROUTES_WITH_RANK,
    ids=[f"{m}:{t.split('/')[-1]}" for m, t, _b, _r in WRITE_ROUTES_WITH_RANK],
)
class TestRankIsCheckedOnEveryWriteRoute:
    """#1422 — ownership was checked, rank was not.

    ``require_owned_plant`` closed the cross-tenant axis and left this one open: any
    member of the owning tenant, **a viewer included**, could drive all seven. Among
    them a phase transition accepting ``force: bool`` — which bypasses the transition
    rules — and an irreversible ``DELETE`` on recorded history.

    Asserted per route rather than per router, deliberately. A router-level assertion
    would pass for a route that inherited the gate from a sibling, which is exactly
    how the gap survived: the routers *do* carry a shared dependency, and it is the
    wrong one for this axis.
    """

    def test_a_viewer_of_the_owning_tenant_is_refused(
        self, method: str, template: str, body: dict[str, Any] | None, min_role: TenantRole
    ):
        client = _app(TenantRole.VIEWER)

        response = _call(client, method, template.format(k=OWN_PLANT), body)

        assert response.status_code == 403, (
            f"a viewer drove {method} {template} — ownership is checked here, rank is not (#1422)"
        )

    def test_a_lead_is_admitted(self, method: str, template: str, body: dict[str, Any] | None, min_role: TenantRole):
        """The control. Without it every refusal above passes for a gate that refuses everyone."""
        client = _app(TenantRole.LEAD)

        response = _call(client, method, template.format(k=OWN_PLANT), body)

        assert response.status_code < 400, response.text

    def test_a_grower_is_admitted_unless_the_route_needs_a_lead(
        self, method: str, template: str, body: dict[str, Any] | None, min_role: TenantRole
    ):
        """The rank actually differs per route, and this is where that is asserted.

        Six routes admit a grower; ``DELETE /phases/history/{key}`` does not. Gating
        all seven at ``lead`` would satisfy the viewer refusals above and quietly take
        six operations away from the role that does the work.
        """
        client = _app(TenantRole.GROWER)

        response = _call(client, method, template.format(k=OWN_PLANT), body)

        if min_role is TenantRole.LEAD:
            assert response.status_code == 403, f"a grower drove {method} {template} (REQ-049 §2.3 delete)"
        else:
            assert response.status_code < 400, response.text
