"""``PATCH /care-reminders/plants/{key}/profile`` — a sent ``null`` is a clear (#1506).

Every field of :class:`CareProfileUpdate` is declared ``T | None`` with a ``None``
default, because that is how a partial update says "not supplied". The handler then
dumped the body with ``exclude_none=True``, which collapses the two cases a PATCH
has to keep apart:

* the field is **absent** from the JSON body — leave the stored value alone;
* the field is present and **``null``** — write ``null``, i.e. clear it.

Only ``model_fields_set`` (what ``exclude_unset`` reads) distinguishes them, so
``notes: null`` never left the router. The frontend's care form sends exactly that
the moment the user empties the notes box (``notes: notes || null`` in
``CareProfileForm.tsx``), so the note could not be removed through the UI at all.

The storage half — that a ``None`` on the model then reaches ArangoDB as a removal
rather than being dropped by the merge-mode repository — is measured against a real
server in ``tests/integration/test_care_profile_null_clearing.py``. This file
measures the boundary: what the router hands the service.

Doubled vs real: the care service is doubled (it is the observation point), as are
the authenticated user, the plant-ownership gate and the tenant rank — this file
makes no claim about either gate, and ``test_plant_scoped_global_routers_api.py``
owns those. Real: the router, the schema and the serialisation decision under test.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.care_reminders.router import router as care_router
from app.api.v1.care_reminders.schemas import CLEARABLE_PROFILE_FIELDS, CareProfileUpdate
from app.common.auth import get_active_tenant_context, get_current_user
from app.common.dependencies import get_care_reminder_service
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.common.plant_ownership import require_owned_plant
from app.domain.models.care_reminder import CareProfile

_PLANT = "plant-1"
_PATH = f"/api/v1/care-reminders/plants/{_PLANT}/profile"


@pytest.fixture
def care_service() -> MagicMock:
    service = MagicMock()
    service.update_profile.return_value = CareProfile(_key="cp1", plant_key=_PLANT)
    return service


@pytest.fixture
def client(care_service: MagicMock) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(care_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(key="u1", account_type="user")
    app.dependency_overrides[require_owned_plant] = lambda: None
    app.dependency_overrides[get_active_tenant_context] = lambda: SimpleNamespace(tenant_key="t1", role=TenantRole.LEAD)
    app.dependency_overrides[get_care_reminder_service] = lambda: care_service
    return TestClient(app, raise_server_exceptions=False)


def _updates(care_service: MagicMock) -> dict[str, Any]:
    """The ``updates`` dict the handler actually handed the service."""
    assert care_service.update_profile.call_count == 1, "the handler did not reach the service"
    return care_service.update_profile.call_args[0][1]


# ── a sent null clears ───────────────────────────────────────────────────────


@pytest.mark.parametrize("field", ["notes", "water_quality_hint"])
def test_an_explicit_null_reaches_the_service_as_none(client: TestClient, care_service: MagicMock, field: str):
    """``{"<field>": null}`` arrives as ``{"<field>": None}``, not as ``{}``.

    Against ``exclude_none=True`` the service was called with an empty dict, so the
    edit was a no-op that answered 200 — the user pressed save, the note came back.
    """
    response = client.patch(_PATH, json={field: None})

    assert response.status_code == 200
    assert _updates(care_service) == {field: None}


def test_the_form_payload_clears_the_note_and_keeps_the_rest(client: TestClient, care_service: MagicMock):
    """The real shape ``CareProfileForm`` sends when the user empties the notes box.

    It posts every edited field, with ``notes``/``water_quality_hint`` as ``null``
    when empty. All of it must arrive; nothing may be dropped for being ``null``.
    """
    response = client.patch(
        _PATH,
        json={
            "watering_interval_days": 9,
            "notes": None,
            "water_quality_hint": None,
            "adaptive_learning_enabled": False,
        },
    )

    assert response.status_code == 200
    assert _updates(care_service) == {
        "watering_interval_days": 9,
        "notes": None,
        "water_quality_hint": None,
        "adaptive_learning_enabled": False,
    }


# ── an absent field is still absent ──────────────────────────────────────────


def test_an_omitted_field_is_not_forwarded_as_none(client: TestClient, care_service: MagicMock):
    """The falsification companion: ``exclude_unset`` must not turn a PATCH into a PUT.

    A change that merely dropped ``exclude_none`` (``model_dump()`` plain) would pass
    every test above and send all 19 declared fields as ``None`` — clearing the whole
    profile on any edit. Only the field the body named may appear.
    """
    response = client.patch(_PATH, json={"watering_interval_days": 9})

    assert response.status_code == 200
    assert _updates(care_service) == {"watering_interval_days": 9}


# ── a null for a field the profile cannot hold as one ────────────────────────


@pytest.mark.parametrize("field", ["care_style", "watering_interval_days", "fertilizing_active_months"])
def test_a_null_for_a_non_nullable_field_is_refused_at_the_boundary(
    client: TestClient, care_service: MagicMock, field: str
):
    """422, not a 500 from ``CareProfile(**data)`` and not a silent drop.

    ``CareProfile.care_style`` is a plain ``CareStyleType``; there is no ``None`` to
    write. Now that a sent ``null`` is forwarded, such a body has to be refused where
    request shapes are refused — at the schema.
    """
    response = client.patch(_PATH, json={field: None})

    assert response.status_code == 422
    assert care_service.update_profile.call_count == 0
    assert field in response.text


# ── the clearable set is derived, not listed ─────────────────────────────────


def test_the_clearable_fields_are_the_exposed_nullable_ones_and_nothing_else():
    """Every clearable field is nullable on the model **and** sendable by a client.

    Deliberately *not* the production expression re-derived and compared against
    itself: that assertion holds however wrong the expression is. The first draft of
    this file did exactly that and stayed green while the constant claimed eight
    fields — ``key``, ``created_at``, ``dormancy_watering``, the learned intervals —
    that no request can name (#1506 review, SCR-006/SCR-007).

    What is asserted here is the consequence: the two names a client may null, and
    representatives of the two reasons a name is excluded.
    """
    assert {"notes", "water_quality_hint"} == CLEARABLE_PROFILE_FIELDS

    # Reason one — exposed by the update schema, but not nullable on the domain
    # model: there is no `None` for the profile to hold.
    assert "care_style" in CareProfileUpdate.model_fields
    assert "care_style" not in CLEARABLE_PROFILE_FIELDS
    assert "watering_interval_days" not in CLEARABLE_PROFILE_FIELDS

    # Reason two — nullable on the domain model, but not exposed: no request can
    # name it, so calling it clearable would overstate the contract.
    nullable_on_the_model = {
        name
        for name, field in CareProfile.model_fields.items()
        if type(None) in getattr(field.annotation, "__args__", ())
    }
    assert "watering_interval_learned" in nullable_on_the_model
    assert "watering_interval_learned" not in CareProfileUpdate.model_fields
    assert "watering_interval_learned" not in CLEARABLE_PROFILE_FIELDS
