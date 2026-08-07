"""REQ-013 §2.3a — capturing the environment on the diary create path.

These tests are about the *contract of the create path*, not about the chain
itself (that is ``test_environment_snapshot_service.py``). Four properties carry
it, and each has a test that fails loudly if it is ever relaxed:

* the snapshot is **never** taken from the request body;
* the capture **never** stops the entry from being written;
* an edit **never** re-captures or mutates it;
* nothing automatic **ever** lands in ``measurements``.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.common.enums import (
    DiaryEntryType,
    DiaryEnvironmentOrigin,
    DiaryEnvironmentStatus,
    TenantRole,
)
from app.domain.models.plant_diary_entry import DiaryEnvironmentReading, PlantDiaryEntry
from app.domain.services.environment_snapshot_service import EnvironmentSnapshot
from app.domain.services.plant_diary_service import PlantDiaryService
from tests.support.diary_fakes import FakeDiaryRepository

TENANT = "tenant-a"
PLANT = "plant-1"
AUTHOR = "user-author"
MEASURED_AT = datetime(2026, 8, 3, 18, 21, 44, tzinfo=UTC)
CAPTURED_AT = datetime(2026, 8, 3, 18, 22, 11, tzinfo=UTC)


def _reading(metric_type: str = "temperature_celsius", value: float = 31.2) -> DiaryEnvironmentReading:
    return DiaryEnvironmentReading(
        metric_type=metric_type,
        value=value,
        unit="°C",
        source="ha_auto",
        measured_at=MEASURED_AT,
        sensor_key="s-temp",
        origin=DiaryEnvironmentOrigin.LOCATION,
    )


class StubEnvironmentService:
    """Answers with a canned snapshot and records what it was asked."""

    def __init__(self, snapshot: EnvironmentSnapshot | None = None, *, raises: bool = False) -> None:
        self.snapshot = snapshot or EnvironmentSnapshot(
            readings=[_reading()],
            status=DiaryEnvironmentStatus.CAPTURED,
            captured_at=CAPTURED_AT,
        )
        self.raises = raises
        self.calls: list[tuple[str, str]] = []

    def capture_for_plant(self, plant_key: str, *, tenant_key: str) -> EnvironmentSnapshot:
        self.calls.append((plant_key, tenant_key))
        if self.raises:
            raise RuntimeError("everything is on fire")
        return self.snapshot


def _entry(**kwargs) -> PlantDiaryEntry:
    fields = {
        "tenant_key": TENANT,
        "created_by": AUTHOR,
        "entry_type": DiaryEntryType.PROBLEM,
        "text": "Untere Blätter hängen seit gestern.",
    }
    fields.update(kwargs)
    return PlantDiaryEntry(**fields)


def _service(environment_service=None) -> tuple[PlantDiaryService, FakeDiaryRepository]:
    repo = FakeDiaryRepository()
    return (
        PlantDiaryService(diary_repo=repo, environment_service=environment_service),
        repo,
    )


class TestCaptureOnCreate:
    def test_the_snapshot_is_stored_on_the_entry(self):
        environment = StubEnvironmentService()
        service, _repo = _service(environment)

        created = service.create_entry(PLANT, _entry(), actor_role=TenantRole.GROWER)

        assert environment.calls == [(PLANT, TENANT)]
        assert created.environment_status is DiaryEnvironmentStatus.CAPTURED
        assert created.environment_captured_at == CAPTURED_AT
        assert [r.metric_type for r in created.environment] == ["temperature_celsius"]

    def test_it_round_trips_through_the_repository(self):
        service, repo = _service(StubEnvironmentService())

        created = service.create_entry(PLANT, _entry(), actor_role=TenantRole.GROWER)
        stored = repo.get_or_raise(created.key)

        assert stored.environment_status is DiaryEnvironmentStatus.CAPTURED
        assert stored.environment[0].source == "ha_auto"
        assert stored.environment[0].origin is DiaryEnvironmentOrigin.LOCATION
        assert stored.environment[0].measured_at == MEASURED_AT

    def test_an_empty_capture_is_stored_with_its_reason(self):
        environment = StubEnvironmentService(
            EnvironmentSnapshot(readings=[], status=DiaryEnvironmentStatus.NO_SOURCE, captured_at=CAPTURED_AT)
        )
        service, _repo = _service(environment)

        created = service.create_entry(PLANT, _entry(), actor_role=TenantRole.GROWER)

        assert created.environment == []
        # ``[]`` alone would be unreadable: this is what tells "nothing measures
        # this plant" apart from "we could not reach the sensors".
        assert created.environment_status is DiaryEnvironmentStatus.NO_SOURCE

    def test_without_a_wired_service_nothing_is_attempted(self):
        service, _repo = _service(None)

        created = service.create_entry(PLANT, _entry(), actor_role=TenantRole.GROWER)

        assert created.environment == []
        assert created.environment_status is DiaryEnvironmentStatus.NOT_ATTEMPTED
        assert created.environment_captured_at is None


class TestNeverFromTheClient:
    def test_a_client_supplied_snapshot_is_overwritten(self):
        # The forged snapshot is plausible and well-formed — which is the point:
        # the guard cannot be a validation rule, it has to be that the server
        # writes the field unconditionally.
        forged = _reading(value=18.0)
        environment = StubEnvironmentService()
        service, _repo = _service(environment)

        created = service.create_entry(
            PLANT,
            _entry(
                environment=[forged],
                environment_status=DiaryEnvironmentStatus.CAPTURED,
                environment_captured_at=datetime(2020, 1, 1, tzinfo=UTC),
            ),
            actor_role=TenantRole.GROWER,
        )

        assert [r.value for r in created.environment] == [31.2]
        assert created.environment_captured_at == CAPTURED_AT

    def test_a_client_supplied_snapshot_is_dropped_when_nothing_is_wired(self):
        # The dangerous variant: no capture service at all. A "keep what came in"
        # implementation would persist the client's invention verbatim.
        service, _repo = _service(None)

        created = service.create_entry(
            PLANT,
            _entry(environment=[_reading(value=18.0)], environment_status=DiaryEnvironmentStatus.CAPTURED),
            actor_role=TenantRole.GROWER,
        )

        assert created.environment == []
        assert created.environment_status is DiaryEnvironmentStatus.NOT_ATTEMPTED


class TestOptOut:
    def test_opting_out_stores_an_empty_snapshot_flagged_as_such(self):
        environment = StubEnvironmentService()
        service, _repo = _service(environment)

        created = service.create_entry(
            PLANT,
            _entry(),
            actor_role=TenantRole.GROWER,
            capture_environment=False,
        )

        assert created.environment == []
        assert created.environment_status is DiaryEnvironmentStatus.OPTED_OUT
        assert created.environment_captured_at is None
        # Nothing was even read: opting out is not "capture and discard".
        assert environment.calls == []


class TestCaptureNeverFailsTheWrite:
    def test_an_exploding_capture_still_writes_the_entry(self):
        # The moment a grower documents a problem is the worst possible moment to
        # refuse the entry over a sensor.
        service, repo = _service(StubEnvironmentService(raises=True))

        created = service.create_entry(PLANT, _entry(text="Blätter braun"), actor_role=TenantRole.GROWER)

        assert created.key is not None
        assert repo.get_or_raise(created.key).text == "Blätter braun"
        assert created.environment_status is DiaryEnvironmentStatus.UNAVAILABLE
        assert created.environment == []


class TestSeparationFromMeasurements:
    """The load-bearing invariant: nothing automatic ever lands in ``measurements``."""

    def test_an_automatic_reading_never_appears_in_measurements(self):
        service, repo = _service(StubEnvironmentService())

        created = service.create_entry(
            PLANT,
            _entry(measurements={"height_cm": 84}),
            actor_role=TenantRole.GROWER,
        )
        stored = repo.get_or_raise(created.key)

        # The grower's dict is exactly what the grower typed — no key was added,
        # renamed or merged in. A merged value would be indistinguishable from a
        # human reading a year later, which is the whole reason for two fields.
        assert stored.measurements == {"height_cm": 84}
        assert "temperature_celsius" not in stored.measurements
        assert [r.metric_type for r in stored.environment] == ["temperature_celsius"]

    def test_an_entry_without_measurements_keeps_none(self):
        service, repo = _service(StubEnvironmentService())

        created = service.create_entry(PLANT, _entry(), actor_role=TenantRole.GROWER)

        assert repo.get_or_raise(created.key).measurements is None
        assert repo.get_or_raise(created.key).environment != []

    def test_provenance_survives_on_every_captured_reading(self):
        # REQ-005 §1: the data source is tracked. ``measurements`` has nowhere to
        # put this, which is why the snapshot is not merged into it.
        service, _repo = _service(StubEnvironmentService())

        created = service.create_entry(PLANT, _entry(), actor_role=TenantRole.GROWER)

        for reading in created.environment:
            assert reading.source
            assert reading.origin
            assert reading.measured_at is not None


class TestEditDoesNotRecapture:
    @pytest.fixture
    def created(self):
        environment = StubEnvironmentService()
        service, repo = _service(environment)
        entry = service.create_entry(PLANT, _entry(), actor_role=TenantRole.GROWER)
        return service, repo, environment, entry

    def test_updating_the_text_leaves_the_snapshot_untouched(self, created):
        service, _repo, environment, entry = created

        updated = service.update_entry(
            entry.key,
            {"text": "Korrektur: es sind die mittleren Blätter."},
            tenant_key=TENANT,
            user_key=AUTHOR,
            actor_role=TenantRole.GROWER,
        )

        assert updated.text.startswith("Korrektur")
        # No second capture: a later edit must not restamp the entry with a
        # climate it was never written under.
        assert environment.calls == [(PLANT, TENANT)]
        assert updated.environment_captured_at == CAPTURED_AT
        assert [r.value for r in updated.environment] == [31.2]

    def test_the_snapshot_fields_are_protected_from_a_direct_write(self, created):
        service, _repo, _environment, entry = created

        updated = service.update_entry(
            entry.key,
            {
                "environment": [],
                "environment_status": DiaryEnvironmentStatus.NO_SOURCE,
                "environment_captured_at": None,
            },
            tenant_key=TENANT,
            user_key=AUTHOR,
            actor_role=TenantRole.GROWER,
        )

        assert updated.environment_status is DiaryEnvironmentStatus.CAPTURED
        assert [r.value for r in updated.environment] == [31.2]


class TestBackwardCompatibility:
    def test_a_document_written_before_the_feature_still_validates(self):
        # AK: additive fields only. A pre-existing document carries none of the
        # three attributes and must round-trip unchanged.
        repo = FakeDiaryRepository()
        repo.seed("legacy-1", tenant_key=TENANT, plant_key=PLANT, text="Alte Notiz")
        assert "environment" not in repo.docs["legacy-1"]

        entry = repo.get_or_raise("legacy-1")

        assert entry.environment == []
        assert entry.environment_captured_at is None
        assert entry.environment_status is DiaryEnvironmentStatus.NOT_ATTEMPTED

    def test_explicit_nulls_in_a_stored_document_are_tolerated(self):
        # The partial-update path persists explicit ``null``s; a document that
        # acquired them must not stop validating and become unreadable.
        repo = FakeDiaryRepository()
        repo.seed(
            "nulled-1",
            tenant_key=TENANT,
            plant_key=PLANT,
            environment=None,
            environment_status=None,
            environment_captured_at=None,
        )

        entry = repo.get_or_raise("nulled-1")

        assert entry.environment == []
        assert entry.environment_status is DiaryEnvironmentStatus.NOT_ATTEMPTED
