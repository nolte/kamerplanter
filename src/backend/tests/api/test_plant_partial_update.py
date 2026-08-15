"""`PATCH /plant-instances/{key}` changes a subset without erasing the rest (#1098).

The only way to change one field on a plant was `PUT`, which takes `PlantCreate`
and is a full replacement: it assigns thirteen of the fourteen body fields onto
the stored row, so anything the caller omits is written back as `None` and — the
repository sets `_update_is_full_replace` so a `PUT` can *clear* a nullable field —
removed from the document.

That is correct for the edit form, which always sends the whole record. It is a
trap for anything composing a request from the schema name, which is how #1098 was
filed: an agent asked to set a substrate erases the plant's location and its batch
reference, and the response is a `200` carrying the row it just emptied.

Both halves are pinned here. Testing only the `PATCH` would leave the `PUT`'s
documented behaviour free to drift into something the docstring no longer
describes — and it is the `PUT` that people already call.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.plant_instances.tenant_router import router as plants_router
from app.common import auth as auth_mod
from app.common.dependencies import get_plant_instance_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext

_STORED = PlantInstance(
    key="plant_1",
    instance_id="TOM-001",
    species_key="sp_tomato",
    tenant_key="t1",
    planted_on=date(2026, 4, 1),
    location_key="loc_livingroom",
    slot_key="slot_3",
    cultivar_key="cv_gardeners",
    plant_name="Fensterbank-Tomate",
    container_volume_liters=12.0,
    current_phase_key="phase_vegetative",
    substrate_batch_key="batch_7",
)

#: Everything a caller can lose by omitting it from a `PUT`.
_OPTIONAL_FIELDS = (
    "location_key",
    "slot_key",
    "cultivar_key",
    "plant_name",
    "container_volume_liters",
    "substrate_batch_key",
)


class _Service:
    def __init__(self) -> None:
        self.written: PlantInstance | None = None

    def get_plant(self, key, tenant_key=None):
        return _STORED.model_copy(deep=True)

    def update_plant(self, key, plant):
        self.written = plant
        return plant

    def resolve_phase_name(self, key):
        return "Vegetativ" if key else ""

    def __getattr__(self, name):
        return lambda *a, **k: None


@pytest.fixture
def service() -> _Service:
    return _Service()


@pytest.fixture
def client(service: _Service) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(plants_router, prefix="/api/v1/t/{tenant_slug}")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="u1", account_type="user")
    app.dependency_overrides[get_plant_instance_service] = lambda: service
    app.dependency_overrides[auth_mod.get_current_tenant] = lambda: TenantContext(
        tenant_key="t1", tenant_slug="t1", user_key="u1", role=TenantRole.LEAD, admin_scopes=[]
    )
    return TestClient(app)


_URL = "/api/v1/t/t1/plant-instances/plant_1"


# ── PATCH: the point of the whole change ─────────────────────────────────────


def test_patching_one_field_leaves_every_other_untouched(service: _Service, client: TestClient) -> None:
    """The #1098 scenario, on the new path."""
    response = client.patch(_URL, json={"substrate_key": "sub_new"})

    assert response.status_code == 200, response.text
    written = service.written
    assert written.substrate_key == "sub_new"
    for field in _OPTIONAL_FIELDS:
        assert getattr(written, field) == getattr(_STORED, field), f"{field} was not preserved"


def test_an_explicit_null_clears_the_field(service: _Service, client: TestClient) -> None:
    """Omitted and `null` must mean different things.

    If they did not, "unplace this plant" would be unreachable through `PATCH` —
    and the caller would be pushed back onto the `PUT` this endpoint exists to
    keep them off.
    """
    client.patch(_URL, json={"location_key": None})

    assert service.written.location_key is None
    assert service.written.slot_key == "slot_3"


def test_omitting_a_field_and_sending_it_as_null_are_distinguished(service: _Service, client: TestClient) -> None:
    """The two intents, side by side, on the same field.

    This is the assertion that fails if the handler ever switches to a plain
    `model_dump()`: every unset field would arrive as `None` and a patch of one
    field would erase all the others — the `PUT`'s behaviour, wearing `PATCH`'s
    name, which is worse than not having the endpoint.
    """
    client.patch(_URL, json={"substrate_key": "sub_new"})
    after_omission = service.written.location_key

    client.patch(_URL, json={"location_key": None})
    after_null = service.written.location_key

    assert after_omission == "loc_livingroom"
    assert after_null is None


def test_an_empty_patch_changes_nothing(service: _Service, client: TestClient) -> None:
    client.patch(_URL, json={})

    for field in (*_OPTIONAL_FIELDS, "instance_id", "species_key", "planted_on"):
        assert getattr(service.written, field) == getattr(_STORED, field)


def test_the_phase_cannot_be_set_through_the_patch(client: TestClient) -> None:
    """`current_phase_key` moves only through the transition path, which enforces
    the state machine (REQ-003). Accepting it here would be a second, ungated way
    to set a phase — so the schema forbids the key outright rather than ignoring
    it, because a silently dropped field reads to the caller as a success."""
    response = client.patch(_URL, json={"current_phase_key": "phase_flowering"})

    assert response.status_code == 422, response.text


def test_the_instance_id_cannot_be_changed_through_the_patch(client: TestClient) -> None:
    """It is the plant's human-facing identity. Renaming a plant as a side effect
    of setting its substrate is exactly the class of surprise this endpoint is
    meant to remove."""
    response = client.patch(_URL, json={"instance_id": "TOM-999"})

    assert response.status_code == 422, response.text


# ── PUT: pin what the docstring now claims ───────────────────────────────────


def test_the_put_still_erases_the_fields_it_is_documented_to_erase(service: _Service, client: TestClient) -> None:
    """Not a defect being enshrined — a documented behaviour being held to its
    documentation. The edit form depends on it (a `PUT` must be able to *clear* a
    nullable field), and the endpoint's docstring now names the exact set. If that
    set changes, this test is where it is noticed."""
    response = client.put(
        _URL,
        json={"instance_id": "TOM-001", "species_key": "sp_tomato", "planted_on": "2026-04-01"},
    )

    assert response.status_code == 200, response.text
    for field in _OPTIONAL_FIELDS:
        assert getattr(service.written, field) is None, f"{field} unexpectedly survived a PUT"


def test_the_put_never_loses_the_phase(service: _Service, client: TestClient) -> None:
    """#1098 claimed a `PUT` silently deletes `current_phase_key` on three named
    plants. It does not: the handler assigns thirteen of fourteen fields and
    excludes this one as server-managed.

    Pinned because the correction is easy to lose — the property is expressed by a
    line that *is not there*, and an "improvement" that completed the assignment
    list would reintroduce exactly the loss the issue feared.
    """
    client.put(
        _URL,
        json={"instance_id": "TOM-001", "species_key": "sp_tomato", "planted_on": "2026-04-01"},
    )

    assert service.written.current_phase_key == "phase_vegetative"


def test_the_naive_put_from_the_issue_is_refused_rather_than_destructive(client: TestClient) -> None:
    """The literally naive call writes nothing: three fields are required."""
    response = client.put(_URL, json={"substrate_key": "sub_new"})

    assert response.status_code == 422, response.text
