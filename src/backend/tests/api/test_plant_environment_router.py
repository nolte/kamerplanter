"""API tests for the diary environment snapshot (REQ-013 §2.3a).

Two surfaces:

* ``GET /plant-instances/{key}/environment`` — the read-only preview the create
  dialog renders, so a grower sees what will be stored *before* saving;
* ``POST /plant-instances/{key}/diary`` — where the snapshot is actually taken,
  including the opt-out and the proof that the payload cannot supply it.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.plant_instances.diary_router import router as plant_diary_router
from app.api.v1.plant_instances.environment_router import router as plant_environment_router
from app.common.auth import get_current_tenant
from app.common.dependencies import (
    get_environment_snapshot_service,
    get_plant_diary_service,
    get_plant_instance_service,
)
from app.common.enums import DiaryEnvironmentOrigin, DiaryEnvironmentStatus, TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.plant_diary_entry import DiaryEnvironmentReading
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.environment_snapshot_service import EnvironmentSnapshot
from app.domain.services.plant_diary_service import PlantDiaryService
from tests.support.diary_fakes import FakeDiaryRepository, FakePlantInstanceService

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"
PLANT_KEY = "plant-1"
FOREIGN_PLANT_KEY = "plant-b-1"
AUTHOR = "user-author"

MEASURED_AT = datetime(2026, 8, 3, 18, 21, 44, tzinfo=UTC)
CAPTURED_AT = datetime(2026, 8, 3, 18, 22, 11, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _full_mode(monkeypatch):
    monkeypatch.setattr("app.domain.services.plant_diary_service.settings.kamerplanter_mode", "full")
    monkeypatch.setattr("app.domain.services.plant_diary_service.settings.jwt_secret_key", "api-test-secret-value")


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _plant(key: str, tenant_key: str = TENANT_KEY) -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key=tenant_key,
        instance_id=f"P-{key}",
        species_key="solanum_lycopersicum",
        plant_name=f"Tomate {key}",
        planted_on=date(2026, 4, 18),
    )


def _reading(
    metric_type: str = "temperature_celsius",
    value: float = 31.2,
    *,
    unit: str = "°C",
    origin: DiaryEnvironmentOrigin = DiaryEnvironmentOrigin.LOCATION,
    sensor_key: str | None = "s-temp",
    source: str = "ha_auto",
) -> DiaryEnvironmentReading:
    return DiaryEnvironmentReading(
        metric_type=metric_type,
        value=value,
        unit=unit,
        source=source,
        measured_at=MEASURED_AT,
        sensor_key=sensor_key,
        origin=origin,
    )


class StubEnvironmentService:
    def __init__(self, snapshot: EnvironmentSnapshot | None = None) -> None:
        self.snapshot = snapshot or EnvironmentSnapshot(
            readings=[
                _reading(),
                _reading("humidity_percent", 28.0, unit="%", sensor_key="s-hum"),
            ],
            status=DiaryEnvironmentStatus.CAPTURED,
            captured_at=CAPTURED_AT,
        )
        self.calls: list[tuple[str, str]] = []

    def capture_for_plant(self, plant_key: str, *, tenant_key: str) -> EnvironmentSnapshot:
        self.calls.append((plant_key, tenant_key))
        return self.snapshot

    def preview_for_plant(self, plant_key: str, *, tenant_key: str) -> EnvironmentSnapshot:
        return self.capture_for_plant(plant_key, tenant_key=tenant_key)


def _build(environment: StubEnvironmentService | None = None):
    environment = environment or StubEnvironmentService()
    repo = FakeDiaryRepository()
    diary_service = PlantDiaryService(diary_repo=repo, environment_service=environment)
    plant_service = FakePlantInstanceService(
        plants={
            PLANT_KEY: _plant(PLANT_KEY),
            FOREIGN_PLANT_KEY: _plant(FOREIGN_PLANT_KEY, tenant_key=FOREIGN_TENANT_KEY),
        }
    )

    app = FastAPI()
    app.include_router(plant_diary_router, prefix="/api/v1/t/{tenant_slug}")
    app.include_router(plant_environment_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key=AUTHOR,
        role=TenantRole.GROWER,
    )
    app.dependency_overrides[get_plant_diary_service] = lambda: diary_service
    app.dependency_overrides[get_plant_instance_service] = lambda: plant_service
    app.dependency_overrides[get_environment_snapshot_service] = lambda: environment
    return TestClient(app), repo, environment


def _environment_url(plant_key: str = PLANT_KEY) -> str:
    return f"/api/v1/t/{TENANT_SLUG}/plant-instances/{plant_key}/environment"


def _diary_url(plant_key: str = PLANT_KEY) -> str:
    return f"/api/v1/t/{TENANT_SLUG}/plant-instances/{plant_key}/diary"


def _payload(**overrides):
    body = {
        "entry_type": "problem",
        "title": "Blätter hängen",
        "text": "Untere Blätter hängen seit gestern, Substrat riecht sauer.",
        "tags": ["blatt"],
        "measurements": {"height_cm": 84},
    }
    body.update(overrides)
    return body


# ── The preview route ────────────────────────────────────────────────────────


class TestEnvironmentPreview:
    def test_it_returns_what_a_capture_would_yield(self):
        client, _repo, _env = _build()

        resp = client.get(_environment_url())

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["plant_key"] == PLANT_KEY
        assert body["environment_status"] == "captured"
        assert [r["metric_type"] for r in body["readings"]] == ["temperature_celsius", "humidity_percent"]
        first = body["readings"][0]
        assert first["value"] == 31.2
        assert first["source"] == "ha_auto"
        assert first["origin"] == "location"
        assert first["sensor_key"] == "s-temp"
        assert first["measured_at"].startswith("2026-08-03T18:21:44")

    def test_an_empty_preview_still_says_why(self):
        client, _repo, _env = _build(
            StubEnvironmentService(
                EnvironmentSnapshot(readings=[], status=DiaryEnvironmentStatus.NO_SOURCE, captured_at=CAPTURED_AT)
            )
        )

        resp = client.get(_environment_url())

        assert resp.status_code == 200
        assert resp.json()["readings"] == []
        # The dialog has to say "no sensor covers this plant", not "loading" and
        # not "sensors unreachable" — it can only do that if the reason travels.
        assert resp.json()["environment_status"] == "no_source"

    def test_a_degraded_preview_is_distinguishable(self):
        client, _repo, _env = _build(
            StubEnvironmentService(
                EnvironmentSnapshot(readings=[], status=DiaryEnvironmentStatus.UNAVAILABLE, captured_at=CAPTURED_AT)
            )
        )

        assert client.get(_environment_url()).json()["environment_status"] == "unavailable"

    def test_a_foreign_plant_is_not_found(self):
        client, _repo, env = _build()

        resp = client.get(_environment_url(FOREIGN_PLANT_KEY))

        # 404 and never an empty 200: an empty snapshot would still confirm that
        # the key exists somewhere in the installation.
        assert resp.status_code == 404, resp.text
        assert env.calls == []

    def test_an_unknown_plant_is_not_found(self):
        client, _repo, _env = _build()

        assert client.get(_environment_url("no-such-plant")).status_code == 404


# ── The create path ──────────────────────────────────────────────────────────


class TestCreateCapturesTheEnvironment:
    def test_the_created_entry_carries_the_snapshot(self):
        client, _repo, env = _build()

        resp = client.post(_diary_url(), json=_payload())

        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert env.calls == [(PLANT_KEY, TENANT_KEY)]
        assert body["environment_status"] == "captured"
        assert body["environment_captured_at"].startswith("2026-08-03T18:22:11")
        assert [r["metric_type"] for r in body["environment"]] == ["temperature_celsius", "humidity_percent"]

    def test_the_grower_measurements_stay_exactly_as_typed(self):
        client, _repo, _env = _build()

        body = client.post(_diary_url(), json=_payload()).json()

        # The separation invariant, checked on the wire: nothing automatic ever
        # appears in ``measurements``, and the two fields never merge.
        assert body["measurements"] == {"height_cm": 84}
        assert "temperature_celsius" not in body["measurements"]

    def test_the_payload_cannot_supply_the_snapshot(self):
        """A well-formed forged snapshot in the body must not survive.

        The values are deliberately plausible: the guard is not "the shape is
        wrong", it is that the server resolves the field itself and overwrites
        whatever arrived. ``DiaryEntryCreateRequest`` does not declare these keys,
        so they are dropped at the schema boundary *and* again in the service —
        this test proves the combination, not either half.
        """
        client, _repo, _env = _build()

        body = client.post(
            _diary_url(),
            json=_payload(
                environment=[
                    {
                        "metric_type": "temperature_celsius",
                        "value": 18.0,
                        "unit": "°C",
                        "source": "ha_auto",
                        "measured_at": "2020-01-01T00:00:00Z",
                        "sensor_key": "forged",
                        "origin": "location",
                    }
                ],
                environment_status="no_source",
                environment_captured_at="2020-01-01T00:00:00Z",
            ),
        ).json()

        assert body["environment_status"] == "captured"
        assert [r["value"] for r in body["environment"]] == [31.2, 28.0]
        assert all(r["sensor_key"] != "forged" for r in body["environment"])
        assert body["environment_captured_at"].startswith("2026-08-03")

    def test_opting_out_stores_an_empty_snapshot(self):
        client, _repo, env = _build()

        body = client.post(_diary_url(), json=_payload(capture_environment=False)).json()

        assert body["environment"] == []
        assert body["environment_status"] == "opted_out"
        assert env.calls == []

    def test_a_read_back_entry_projects_the_snapshot(self):
        client, _repo, _env = _build()
        created = client.post(_diary_url(), json=_payload()).json()

        fetched = client.get(f"{_diary_url()}/{created['key']}").json()

        assert fetched["environment"] == created["environment"]
        assert fetched["environment_status"] == "captured"

    def test_editing_an_entry_does_not_recapture(self):
        client, _repo, env = _build()
        created = client.post(_diary_url(), json=_payload()).json()

        updated = client.put(
            f"{_diary_url()}/{created['key']}",
            json={"text": "Korrektur: die mittleren Blätter."},
        ).json()

        assert env.calls == [(PLANT_KEY, TENANT_KEY)]
        assert updated["environment_captured_at"] == created["environment_captured_at"]
        assert updated["environment"] == created["environment"]
