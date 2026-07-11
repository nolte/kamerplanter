"""Tests for the REQ-017 PropagationService.

Covers the D10 clone path (``record``), event outcome/progress transitions,
batch finalize, protocol deletion guards and phenotype ownership. Persistence
is mocked (``PropagationRepository``); the lineage engine is exercised in
``test_lineage_engine``.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import PropagationBatchStatus, PropagationEventStatus
from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.data_access.repositories.propagation_repository import PropagationRepository
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.propagation import (
    PhenotypeNote,
    PropagationBatch,
    PropagationEvent,
    RootingProtocol,
)
from app.domain.services.propagation_service import PropagationService


def _clone_event() -> PropagationEvent:
    return PropagationEvent(
        tenant_key="tenant-a",
        method="clone",
        parent_plant_keys=["mother-1"],
        child_plant_keys=["pup-1"],
    )


def _event(**overrides) -> PropagationEvent:
    base = {
        "key": "evt-1",
        "tenant_key": "tenant-a",
        "method": "cutting",
        "quantity": 10,
        "status": PropagationEventStatus.IN_PROGRESS,
    }
    base.update(overrides)
    return PropagationEvent(**base)


def _prop_repo() -> MagicMock:
    repo = MagicMock(spec=PropagationRepository)
    repo.update_event.side_effect = lambda key, event: event
    repo.update_batch.side_effect = lambda key, batch: batch
    return repo


# ── D10 clone path (unchanged behaviour) ──────────────────────────────────────


def test_record_persists_via_legacy_repo_and_stamps_happened_at() -> None:
    repo = MagicMock()
    repo.create.side_effect = lambda event: event
    service = PropagationService(repo)

    result = service.record(_clone_event())

    repo.create.assert_called_once()
    assert result.happened_at is not None
    assert result.method == "clone"


def test_record_via_propagation_repo() -> None:
    repo = _prop_repo()
    repo.create_event.side_effect = lambda event: event
    service = PropagationService(propagation_repo=repo)

    result = service.record(_clone_event())

    repo.create_event.assert_called_once()
    assert result.happened_at is not None


def test_record_without_repo_returns_event_unpersisted() -> None:
    result = PropagationService().record(_clone_event())
    assert result.happened_at is not None
    assert result.child_plant_keys == ["pup-1"]


# ── Events ────────────────────────────────────────────────────────────────────


def test_list_for_plant_requires_tenant_key() -> None:
    service = PropagationService(propagation_repo=_prop_repo())
    with pytest.raises(ValidationError):
        service.list_for_plant("pup-1", tenant_key="")


def test_list_for_plant_delegates_to_repo() -> None:
    repo = _prop_repo()
    repo.list_events_for_plant.return_value = [_event()]
    service = PropagationService(propagation_repo=repo)

    result = service.list_for_plant("pup-1", tenant_key="tenant-a")

    repo.list_events_for_plant.assert_called_once_with("pup-1", "tenant-a")
    assert len(result) == 1


def test_update_outcome_success_derives_rate_and_status() -> None:
    repo = _prop_repo()
    repo.get_event.return_value = _event(quantity=10)
    service = PropagationService(propagation_repo=repo)

    result = service.update_outcome("evt-1", "tenant-a", survived_count=8)

    assert result.survived_count == 8
    assert result.success_rate == 0.8
    assert result.status == PropagationEventStatus.COMPLETED


def test_update_outcome_zero_survivors_marks_failed() -> None:
    repo = _prop_repo()
    repo.get_event.return_value = _event(quantity=5)
    service = PropagationService(propagation_repo=repo)

    result = service.update_outcome("evt-1", "tenant-a", survived_count=0, failure_reasons=["rot"])

    assert result.status == PropagationEventStatus.FAILED
    assert result.failure_reasons == ["rot"]


def test_update_outcome_over_quantity_is_422() -> None:
    repo = _prop_repo()
    repo.get_event.return_value = _event(quantity=5)
    service = PropagationService(propagation_repo=repo)

    with pytest.raises(ValidationError):
        service.update_outcome("evt-1", "tenant-a", survived_count=6)


def test_update_outcome_unknown_event_is_404() -> None:
    repo = _prop_repo()
    repo.get_event.return_value = None
    service = PropagationService(propagation_repo=repo)

    with pytest.raises(NotFoundError):
        service.update_outcome("missing", "tenant-a", survived_count=1)


def test_update_progress_advances_status() -> None:
    repo = _prop_repo()
    repo.get_event.return_value = _event()
    service = PropagationService(propagation_repo=repo)

    rooted = service.update_progress("evt-1", "tenant-a", roots_observed_at=datetime.now(UTC))
    assert rooted.status == PropagationEventStatus.ROOTED

    repo.get_event.return_value = _event(status=PropagationEventStatus.ROOTED)
    transplanted = service.update_progress("evt-1", "tenant-a", transplant_ready_at=datetime.now(UTC))
    assert transplanted.status == PropagationEventStatus.TRANSPLANTED


# ── Batches ────────────────────────────────────────────────────────────────────


def test_finalize_batch_rolls_up_survivors_and_links_run() -> None:
    repo = _prop_repo()
    repo.get_batch.return_value = PropagationBatch(key="batch-1", tenant_key="tenant-a", name="B", method="cutting")
    repo.list_events_for_batch.return_value = [
        _event(quantity=10, survived_count=8),
        _event(quantity=5, survived_count=5),
    ]
    run = MagicMock()
    run.tenant_key = "tenant-a"
    planting_run_repo = MagicMock()
    planting_run_repo.get_by_key.return_value = run
    service = PropagationService(propagation_repo=repo, planting_run_repo=planting_run_repo)

    result = service.finalize_batch("batch-1", "tenant-a", "run-1")

    assert result.status == PropagationBatchStatus.COMPLETED
    assert result.total_survived == 13
    assert result.target_planting_run_key == "run-1"


def test_finalize_batch_foreign_run_is_404() -> None:
    repo = _prop_repo()
    repo.get_batch.return_value = PropagationBatch(key="batch-1", tenant_key="tenant-a", name="B", method="cutting")
    planting_run_repo = MagicMock()
    planting_run_repo.get_by_key.return_value = None
    service = PropagationService(propagation_repo=repo, planting_run_repo=planting_run_repo)

    with pytest.raises(NotFoundError):
        service.finalize_batch("batch-1", "tenant-a", "foreign-run")


def test_finalize_already_completed_is_422() -> None:
    repo = _prop_repo()
    repo.get_batch.return_value = PropagationBatch(
        key="batch-1",
        tenant_key="tenant-a",
        name="B",
        method="cutting",
        status=PropagationBatchStatus.COMPLETED,
    )
    service = PropagationService(propagation_repo=repo)

    with pytest.raises(ValidationError):
        service.finalize_batch("batch-1", "tenant-a", "run-1")


# ── Protocols ──────────────────────────────────────────────────────────────────


def test_delete_global_protocol_is_forbidden() -> None:
    repo = _prop_repo()
    repo.get_protocol.return_value = RootingProtocol(key="p1", tenant_key="", name="G", method="cutting")
    service = PropagationService(propagation_repo=repo)

    with pytest.raises(ForbiddenError):
        service.delete_protocol("p1", "tenant-a")


def test_delete_protocol_in_use_is_422() -> None:
    repo = _prop_repo()
    repo.get_protocol.return_value = RootingProtocol(key="p1", tenant_key="tenant-a", name="Own", method="cutting")
    repo.protocol_in_use.return_value = True
    service = PropagationService(propagation_repo=repo)

    with pytest.raises(ValidationError):
        service.delete_protocol("p1", "tenant-a")


def test_delete_protocol_ok() -> None:
    repo = _prop_repo()
    repo.get_protocol.return_value = RootingProtocol(key="p1", tenant_key="tenant-a", name="Own", method="cutting")
    repo.protocol_in_use.return_value = False
    service = PropagationService(propagation_repo=repo)

    service.delete_protocol("p1", "tenant-a")

    repo.delete_protocol.assert_called_once_with("p1")


# ── Phenotypes ─────────────────────────────────────────────────────────────────


def test_add_phenotype_requires_owned_plant() -> None:
    repo = _prop_repo()
    repo.get_plant.return_value = None
    service = PropagationService(propagation_repo=repo)
    note = PhenotypeNote(plant_key="foreign", note="Nice aroma")

    with pytest.raises(NotFoundError):
        service.add_phenotype(note, "tenant-a")


def test_delete_phenotype_wrong_plant_is_404() -> None:
    repo = _prop_repo()
    repo.get_phenotype.return_value = PhenotypeNote(key="n1", tenant_key="tenant-a", plant_key="other-plant", note="x")
    service = PropagationService(propagation_repo=repo)

    with pytest.raises(NotFoundError):
        service.delete_phenotype("plant-1", "n1", "tenant-a")


# ── Stats ──────────────────────────────────────────────────────────────────────


def test_stats_rejects_unknown_grouping() -> None:
    service = PropagationService(propagation_repo=_prop_repo())
    with pytest.raises(ValidationError):
        service.stats("tenant-a", "banana")


def test_stats_valid_grouping_delegates() -> None:
    repo = _prop_repo()
    repo.stats.return_value = [{"key": "cutting", "event_count": 3}]
    service = PropagationService(propagation_repo=repo)
    result = service.stats("tenant-a", "method")
    repo.stats.assert_called_once_with("tenant-a", "method")
    assert result[0]["event_count"] == 3


# ── create / list delegation ───────────────────────────────────────────────────


def test_create_event_stamps_happened_at() -> None:
    repo = _prop_repo()
    repo.create_event.side_effect = lambda e: e
    service = PropagationService(propagation_repo=repo)
    created = service.create_event(_event(happened_at=None))
    assert created.happened_at is not None


def test_create_batch_stamps_started_at() -> None:
    repo = _prop_repo()
    repo.create_batch.side_effect = lambda b: b
    service = PropagationService(propagation_repo=repo)
    batch = service.create_batch(PropagationBatch(tenant_key="tenant-a", name="B", method="cutting"))
    assert batch.started_at is not None


def test_list_events_and_batches_delegate() -> None:
    repo = _prop_repo()
    repo.list_events.return_value = ([_event()], 1)
    repo.list_batches.return_value = ([], 0)
    service = PropagationService(propagation_repo=repo)
    assert service.list_events("tenant-a", method="cutting")[1] == 1
    assert service.list_batches("tenant-a", status="in_progress")[1] == 0


def test_get_event_and_batch_404() -> None:
    repo = _prop_repo()
    repo.get_event.return_value = None
    repo.get_batch.return_value = None
    service = PropagationService(propagation_repo=repo)
    with pytest.raises(NotFoundError):
        service.get_event("x", "tenant-a")
    with pytest.raises(NotFoundError):
        service.get_batch("x", "tenant-a")


def test_get_batch_events_checks_ownership_first() -> None:
    repo = _prop_repo()
    repo.get_batch.return_value = PropagationBatch(key="b1", tenant_key="tenant-a", name="B", method="cutting")
    repo.list_events_for_batch.return_value = [_event()]
    service = PropagationService(propagation_repo=repo)
    assert len(service.get_batch_events("b1", "tenant-a")) == 1


def test_update_progress_callus_keeps_in_progress() -> None:
    repo = _prop_repo()
    repo.get_event.return_value = _event()
    service = PropagationService(propagation_repo=repo)
    result = service.update_progress("evt-1", "tenant-a", callus_observed_at=datetime.now(UTC))
    assert result.status == PropagationEventStatus.IN_PROGRESS
    assert result.callus_observed_at is not None


def test_update_batch_applies_fields() -> None:
    repo = _prop_repo()
    repo.get_batch.return_value = PropagationBatch(key="b1", tenant_key="tenant-a", name="B", method="cutting")
    service = PropagationService(propagation_repo=repo)
    updated = service.update_batch("b1", "tenant-a", status=PropagationBatchStatus.FAILED, notes="lost")
    assert updated.status == PropagationBatchStatus.FAILED
    assert updated.notes == "lost"


# ── protocols ──────────────────────────────────────────────────────────────────


def test_update_global_protocol_forbidden() -> None:
    repo = _prop_repo()
    repo.get_protocol.return_value = RootingProtocol(key="p1", tenant_key="", name="G", method="cutting")
    service = PropagationService(propagation_repo=repo)
    with pytest.raises(ForbiddenError):
        service.update_protocol("p1", "tenant-a", RootingProtocol(name="G2", method="cutting"))


def test_update_own_protocol_ok() -> None:
    repo = _prop_repo()
    repo.get_protocol.return_value = RootingProtocol(key="p1", tenant_key="tenant-a", name="Own", method="cutting")
    repo.update_protocol.side_effect = lambda key, p: p
    service = PropagationService(propagation_repo=repo)
    updated = service.update_protocol("p1", "tenant-a", RootingProtocol(name="Own2", method="cutting"))
    assert updated.tenant_key == "tenant-a"


def test_list_protocols_delegates() -> None:
    repo = _prop_repo()
    repo.list_protocols.return_value = ([RootingProtocol(name="G", method="cutting")], 1)
    service = PropagationService(propagation_repo=repo)
    assert service.list_protocols("tenant-a")[1] == 1


def test_protocol_stats_matches_row() -> None:
    repo = _prop_repo()
    repo.get_protocol.return_value = RootingProtocol(key="p1", tenant_key="tenant-a", name="Own", method="cutting")
    repo.stats.return_value = [{"key": "p1", "event_count": 2, "success_rate": 0.5}]
    service = PropagationService(propagation_repo=repo)
    assert service.protocol_stats("p1", "tenant-a")["event_count"] == 2


def test_protocol_stats_zero_when_absent() -> None:
    repo = _prop_repo()
    repo.get_protocol.return_value = RootingProtocol(key="p1", tenant_key="tenant-a", name="Own", method="cutting")
    repo.stats.return_value = []
    service = PropagationService(propagation_repo=repo)
    assert service.protocol_stats("p1", "tenant-a")["event_count"] == 0


# ── mothers ─────────────────────────────────────────────────────────────────────


def _owned_plant() -> PlantInstance:
    return PlantInstance(
        _key="plant-1", tenant_key="tenant-a", instance_id="P-1", species_key="tomato", planted_on="2026-01-01"
    )


def test_designate_and_retire_and_health_mother() -> None:
    repo = _prop_repo()
    repo.get_plant.return_value = _owned_plant()
    repo.update_plant_fields.side_effect = lambda key, fields: {"_key": key, **fields}
    service = PropagationService(propagation_repo=repo)

    designated = service.designate_mother("plant-1", "tenant-a", priority="critical")
    assert designated["is_mother"] is True
    assert designated["mother_priority"] == "critical"

    retired = service.retire_mother("plant-1", "tenant-a", reason="old")
    assert retired["is_mother"] is False

    healthy = service.update_mother_health("plant-1", "tenant-a", health_score=90)
    assert healthy["mother_health_score"] == 90


def test_update_mother_health_out_of_range_is_422() -> None:
    service = PropagationService(propagation_repo=_prop_repo())
    with pytest.raises(ValidationError):
        service.update_mother_health("plant-1", "tenant-a", health_score=150)


def test_list_and_get_mother() -> None:
    repo = _prop_repo()
    repo.list_mothers.return_value = [{"_key": "plant-1", "is_mother": True}]
    repo.get_plant_raw.return_value = {"_key": "plant-1", "is_mother": True}
    service = PropagationService(propagation_repo=repo)
    assert service.list_mothers("tenant-a")[0]["_key"] == "plant-1"
    assert service.get_mother("plant-1", "tenant-a")["is_mother"] is True


def test_get_mother_unknown_is_404() -> None:
    repo = _prop_repo()
    repo.get_plant_raw.return_value = None
    service = PropagationService(propagation_repo=repo)
    with pytest.raises(NotFoundError):
        service.get_mother("ghost", "tenant-a")


# ── phenotypes + lineage ─────────────────────────────────────────────────────────


def test_add_and_list_phenotype() -> None:
    repo = _prop_repo()
    repo.get_plant.return_value = _owned_plant()
    repo.create_phenotype.side_effect = lambda n: n
    repo.list_phenotypes_for_plant.return_value = [
        PhenotypeNote(key="n1", tenant_key="tenant-a", plant_key="plant-1", note="Nice")
    ]
    service = PropagationService(propagation_repo=repo)
    added = service.add_phenotype(PhenotypeNote(plant_key="plant-1", note="Nice"), "tenant-a")
    assert added.tenant_key == "tenant-a"
    assert added.observed_at is not None
    assert len(service.list_phenotypes("plant-1", "tenant-a")) == 1


def test_lineage_and_descendants_and_graft() -> None:
    from app.common.enums import GraftCompatibilityLevel
    from app.domain.engines.lineage_engine import (
        GraftCompatibilityResult,
        LineageEngine,
        LineagePath,
    )

    repo = _prop_repo()
    repo.get_plant.return_value = _owned_plant()
    engine = MagicMock(spec=LineageEngine)
    engine.trace_ancestors.return_value = [LineagePath(plant_keys=("mother-1",))]
    engine.list_ancestors.return_value = [_owned_plant()]
    engine.trace_descendants.return_value = [_owned_plant()]
    engine.check_graft_compatibility.return_value = GraftCompatibilityResult(
        scion_species_key="tomato",
        rootstock_species_key="tomato",
        compatible=True,
        level=GraftCompatibilityLevel.COMPATIBLE,
        same_genus=True,
        same_family=True,
        message="ok",
    )
    service = PropagationService(propagation_repo=repo, lineage_engine=engine)

    lineage = service.get_lineage("plant-1", "tenant-a")
    assert lineage["paths"] == [["mother-1"]]
    assert len(service.get_descendants("plant-1", "tenant-a")) == 1

    # graft check needs two distinct owned plants
    repo.get_plant.side_effect = [
        _owned_plant(),
        PlantInstance(
            _key="plant-2",
            tenant_key="tenant-a",
            instance_id="P-2",
            species_key="tomato2",
            planted_on="2026-01-01",
        ),
    ]
    result = service.check_graft_compatibility("plant-1", "plant-2", "tenant-a")
    assert result.compatible is True


def test_graft_same_plant_is_422() -> None:
    repo = _prop_repo()
    repo.get_plant.return_value = _owned_plant()
    from app.domain.engines.lineage_engine import LineageEngine

    service = PropagationService(propagation_repo=repo, lineage_engine=MagicMock(spec=LineageEngine))
    with pytest.raises(ValidationError):
        service.check_graft_compatibility("plant-1", "plant-1", "tenant-a")
