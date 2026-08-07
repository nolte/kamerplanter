"""REQ-004 — API tests for the tenant-scoped watering-log write endpoints (#970).

``POST /t/{slug}/watering-logs`` answered **500** for a request that carried
neither ``slot_keys`` nor ``plant_keys``. The input genuinely *is* invalid — the
domain model's cross-field validator says so — but the router built that domain
model itself:

    log = WateringLog(**body.model_dump(), tenant_key=ctx.tenant_key)

and the ``pydantic.ValidationError`` it raises is **not** FastAPI's
``RequestValidationError``. It therefore matches neither registered validation
handler and falls through to the 500 handler, telling the caller "we broke" for
a request we ourselves consider invalid.

These tests pin the boundary contract of the write endpoints: every input the
domain model would reject is rejected by the API layer first, with a 422 that
names the offending fields — and no write path may answer 500 for caller input.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.watering_logs.tenant_router import router as watering_logs_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_watering_log_service
from app.common.enums import ApplicationMethod, TenantRole, WaterSource
from app.common.error_handlers import (
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.common.exceptions import KamerplanterError
from app.domain.models.tenant_context import TenantContext
from app.domain.models.watering_log import WateringLog

TENANT_SLUG = "lisa"
TENANT_KEY = "tenant_lisa"

_URL = f"/api/v1/t/{TENANT_SLUG}/watering-logs"

# The payload the create dialog sends once a plant is picked (WateringLogCreateDialog
# .onSubmit): it omits ``plant_keys``/``slot_keys`` entirely when both are empty.
_VALID_PAYLOAD = {
    "application_method": "drench",
    "is_supplemental": False,
    "volume_liters": 1.5,
    "plant_keys": ["plant_tomate_1"],
    "water_source": "tap",
}


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key="user_lisa",
        role=TenantRole.LEAD,
    )


def _build() -> tuple[TestClient, MagicMock]:
    stored = WateringLog(
        _key="log_1",
        tenant_key=TENANT_KEY,
        volume_liters=1.5,
        plant_keys=["plant_tomate_1"],
    )
    service = MagicMock()
    service.create_log.side_effect = lambda log: {
        "log": log.model_copy(update={"key": "log_1"}),
        "warnings": [],
    }
    service.get_log.return_value = stored
    service.update_log.side_effect = lambda key, data: stored.model_copy(update=data)
    service.resolve_plant_names.return_value = {}
    service.resolve_fertilizer_names.return_value = {}

    app = FastAPI()
    app.include_router(watering_logs_router, prefix="/api/v1/t/{tenant_slug}")
    # Mirror the production handler wiring (main.py) so an unhandled error shows up
    # as the 500 the client sees, instead of surfacing as a test-time exception.
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_watering_log_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False), service


def _created_log(service: MagicMock) -> WateringLog:
    return service.create_log.call_args.args[0]


def _fields(payload: dict) -> set[str]:
    return {detail["field"] for detail in payload["details"]}


class TestCreateLogRequiresATarget:
    """The cross-field rule "at least one of slot_keys or plant_keys"."""

    def test_neither_target_is_rejected_with_422(self):
        """Observed as 500 before the fix — the defect reported in #970."""
        client, service = _build()

        resp = client.post(_URL, json={"volume_liters": 1.5})

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        service.create_log.assert_not_called()

    def test_empty_target_lists_are_rejected_with_422(self):
        """Explicitly empty lists are the same fact as omitting them."""
        client, service = _build()

        resp = client.post(_URL, json={"volume_liters": 1.5, "plant_keys": [], "slot_keys": []})

        assert resp.status_code == 422, resp.text
        service.create_log.assert_not_called()

    def test_error_body_names_both_target_fields(self):
        """A generic "input is invalid" would not tell the caller what to change."""
        client, _service = _build()

        body = client.post(_URL, json={"volume_liters": 1.5}).json()

        assert _fields(body) == {"body.plant_keys", "body.slot_keys"}
        for detail in body["details"]:
            assert detail["reason"] == "At least one of slot_keys or plant_keys must be provided"
            assert detail["code"] == "watering_target_required"

    def test_plant_keys_only_is_accepted(self):
        client, service = _build()

        resp = client.post(_URL, json={"volume_liters": 1.5, "plant_keys": ["plant_tomate_1"]})

        assert resp.status_code == 201, resp.text
        created = _created_log(service)
        assert created.plant_keys == ["plant_tomate_1"]
        assert created.slot_keys == []
        assert created.tenant_key == TENANT_KEY

    def test_slot_keys_only_is_accepted(self):
        client, service = _build()

        resp = client.post(_URL, json={"volume_liters": 1.5, "slot_keys": ["slot_a1"]})

        assert resp.status_code == 201, resp.text
        created = _created_log(service)
        assert created.slot_keys == ["slot_a1"]
        assert created.plant_keys == []

    def test_full_payload_is_accepted(self):
        client, service = _build()

        resp = client.post(_URL, json=_VALID_PAYLOAD)

        assert resp.status_code == 201, resp.text
        created = _created_log(service)
        assert created.application_method is ApplicationMethod.DRENCH
        assert created.water_source is WaterSource.TAP
        assert created.volume_liters == 1.5


class TestCreateLogSupplementalFertigation:
    """The sibling rule in the same domain validator — same 500, same fix."""

    def test_supplemental_fertigation_is_rejected_with_422(self):
        client, service = _build()

        resp = client.post(
            _URL,
            json={**_VALID_PAYLOAD, "application_method": "fertigation", "is_supplemental": True},
        )

        assert resp.status_code == 422, resp.text
        assert _fields(resp.json()) == {"body.is_supplemental", "body.application_method"}
        assert resp.json()["details"][0]["code"] == "supplemental_cannot_fertigate"
        service.create_log.assert_not_called()

    def test_non_supplemental_fertigation_is_accepted(self):
        client, service = _build()

        resp = client.post(
            _URL,
            json={**_VALID_PAYLOAD, "application_method": "fertigation", "is_supplemental": False},
        )

        assert resp.status_code == 201, resp.text
        assert _created_log(service).application_method is ApplicationMethod.FERTIGATION


class TestCreateLogEnumFields:
    """An unknown enum value is a caller error, not an internal one.

    ``application_method`` and ``water_source`` were typed ``str`` at the boundary
    while the domain model types them as enums, so an unknown value passed the API
    layer and blew up inside ``WateringLog`` as an unhandled ``ValidationError``
    (HTTP 500) — the #967 shape, in this router.
    """

    def test_unknown_application_method_is_rejected_with_422(self):
        client, service = _build()

        resp = client.post(_URL, json={**_VALID_PAYLOAD, "application_method": "sprinkle"})

        assert resp.status_code == 422, resp.text
        assert "body.application_method" in _fields(resp.json())
        service.create_log.assert_not_called()

    def test_unknown_water_source_is_rejected_with_422(self):
        client, service = _build()

        resp = client.post(_URL, json={**_VALID_PAYLOAD, "water_source": "pond"})

        assert resp.status_code == 422, resp.text
        assert "body.water_source" in _fields(resp.json())
        service.create_log.assert_not_called()

    def test_omitted_application_method_defaults_to_drench(self):
        client, service = _build()

        resp = client.post(_URL, json={"volume_liters": 1.5, "plant_keys": ["plant_tomate_1"]})

        assert resp.status_code == 201, resp.text
        assert _created_log(service).application_method is ApplicationMethod.DRENCH


class TestUpdateLogEnumFields:
    """The update path never 500'd on the way in — it did something worse.

    ``update_log`` hands the request values to ``update_fields``, which writes the
    document **first** and only then rebuilds the domain model from it. An unknown
    ``application_method`` string was therefore persisted, and the rebuild then
    raised — a 500 *and* a poisoned document that every later read chokes on.
    """

    def test_unknown_application_method_is_rejected_with_422(self):
        client, service = _build()

        resp = client.put(f"{_URL}/log_1", json={"application_method": "sprinkle"})

        assert resp.status_code == 422, resp.text
        assert "body.application_method" in _fields(resp.json())
        service.update_log.assert_not_called()

    def test_known_application_method_is_forwarded(self):
        client, service = _build()

        resp = client.put(f"{_URL}/log_1", json={"application_method": "foliar"})

        assert resp.status_code == 200, resp.text
        assert service.update_log.call_args.args[1] == {"application_method": ApplicationMethod.FOLIAR}

    def test_omitted_fields_stay_out_of_the_update(self):
        client, service = _build()

        resp = client.put(f"{_URL}/log_1", json={"notes": "Nachgegossen"})

        assert resp.status_code == 200, resp.text
        assert service.update_log.call_args.args[1] == {"notes": "Nachgegossen"}


class TestConfirmWateringOverrides:
    """``overrides`` was an untyped ``dict`` feeding a domain model.

    ``confirm_watering`` builds ``WateringLogFertilizer`` from
    ``overrides["fertilizers"]``, whose ``ml_per_liter`` must be > 0. As a free-form
    dict the boundary validated none of it: a missing key raised ``KeyError`` and a
    non-positive dose raised ``ValidationError`` — both 500s for caller input.
    """

    def test_non_positive_dose_is_rejected_with_422(self):
        client, service = _build()

        resp = client.post(
            f"{_URL}/confirm",
            json={
                "run_key": "run_1",
                "task_key": "task_1",
                "overrides": {"fertilizers": [{"fertilizer_key": "fert_1", "ml_per_liter": 0}]},
            },
        )

        assert resp.status_code == 422, resp.text
        service.confirm_watering.assert_not_called()

    def test_fertilizer_line_without_a_key_is_rejected_with_422(self):
        client, service = _build()

        resp = client.post(
            f"{_URL}/confirm",
            json={
                "run_key": "run_1",
                "task_key": "task_1",
                "overrides": {"fertilizers": [{"ml_per_liter": 2.0}]},
            },
        )

        assert resp.status_code == 422, resp.text
        service.confirm_watering.assert_not_called()

    def test_valid_overrides_reach_the_service_as_a_dict(self):
        client, service = _build()
        service.confirm_watering.return_value = {
            "watering_log_key": "log_1",
            "task_completed": True,
            "warnings": [],
        }

        resp = client.post(
            f"{_URL}/confirm",
            json={
                "run_key": "run_1",
                "task_key": "task_1",
                "overrides": {"fertilizers": [{"fertilizer_key": "fert_1", "ml_per_liter": 2.0}]},
            },
        )

        assert resp.status_code == 201, resp.text
        assert service.confirm_watering.call_args.kwargs["overrides"] == {
            "fertilizers": [{"fertilizer_key": "fert_1", "ml_per_liter": 2.0}]
        }

    def test_confirm_without_overrides_still_works(self):
        client, service = _build()
        service.confirm_watering.return_value = {
            "watering_log_key": "log_1",
            "task_completed": True,
            "warnings": [],
        }

        resp = client.post(f"{_URL}/confirm", json={"run_key": "run_1", "task_key": "task_1"})

        assert resp.status_code == 201, resp.text
        assert service.confirm_watering.call_args.kwargs["overrides"] is None
