"""REQ-017 Propagation service.

Business logic for the propagation surface: events (with progress / outcome
transitions), batches (with finalize-to-PlantingRun), rooting-protocol templates,
mother-plant designation, phenotype notes, genetic lineage traversal and success
statistics. Persistence is delegated to :class:`PropagationRepository`; lineage
traversal and graft compatibility to :class:`LineageEngine`.

The D10 clone path (:meth:`record`) is intentionally minimal and no-op-safe so
the service stays usable in propagation-less contexts (e.g. unit tests that only
exercise the plant-instance clone spawn).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

from app.common.enums import (
    PropagationBatchStatus,
    PropagationEventStatus,
)
from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.data_access.repositories.propagation_repository import PropagationRepository
from app.domain.engines.lineage_engine import GraftCompatibilityResult, LineageEngine, LineagePath
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.propagation import (
    PhenotypeNote,
    PropagationBatch,
    PropagationEvent,
    RootingProtocol,
)


class _PropagationEventStore(Protocol):
    """Minimal persistence surface the D10 clone path needs (a bound repository)."""

    def create(self, model: PropagationEvent) -> PropagationEvent: ...


def _now() -> datetime:
    return datetime.now(UTC)


class PropagationService:
    """REQ-017 propagation / lineage business logic."""

    def __init__(
        self,
        repo: _PropagationEventStore | None = None,
        *,
        propagation_repo: PropagationRepository | None = None,
        lineage_engine: LineageEngine | None = None,
        planting_run_repo: Any | None = None,
    ) -> None:
        #: D10-minimal event store (kept for the existing clone-spawn wiring).
        self._repo = repo
        #: Full propagation repository (events / batches / protocols / phenotypes / lineage).
        self._prop = propagation_repo
        self._lineage = lineage_engine
        self._planting_run_repo = planting_run_repo

    # ── D10 minimal clone path (unchanged behaviour) ──────────────────────────

    def record(self, event: PropagationEvent) -> PropagationEvent:
        """Persist one propagation event, stamping ``happened_at`` when unset.

        No-op-safe: when no repository is wired the event is returned unpersisted,
        so the service stays usable in propagation-less contexts (e.g. tests that
        do not exercise persistence)."""
        if event.happened_at is None:
            event.happened_at = _now()
        store = self._repo or self._prop
        if store is None:
            return event
        if isinstance(store, PropagationRepository):
            return store.create_event(event)
        return store.create(event)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _require_prop(self) -> PropagationRepository:
        if self._prop is None:
            raise RuntimeError("PropagationService is not wired with a PropagationRepository.")
        return self._prop

    def _require_lineage(self) -> LineageEngine:
        if self._lineage is None:
            raise RuntimeError("PropagationService is not wired with a LineageEngine.")
        return self._lineage

    def _get_event_or_404(self, key: str, tenant_key: str) -> PropagationEvent:
        event = self._require_prop().get_event(key, tenant_key)
        if event is None:
            raise NotFoundError("PropagationEvent", key)
        return event

    def _get_plant_or_404(self, key: str, tenant_key: str) -> PlantInstance:
        plant = self._require_prop().get_plant(key, tenant_key)
        if plant is None:
            raise NotFoundError("PlantInstance", key)
        return plant

    # ── Events ────────────────────────────────────────────────────────────────

    def list_for_plant(self, plant_key: str, tenant_key: str = "") -> list[PropagationEvent]:
        """All propagation events where the plant is a source or a result."""
        prop = self._require_prop()
        if not tenant_key:
            raise ValidationError("list_for_plant requires a tenant_key (SEC-B4 tenant isolation).")
        return prop.list_events_for_plant(plant_key, tenant_key)

    def list_events(
        self,
        tenant_key: str,
        *,
        method: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PropagationEvent], int]:
        return self._require_prop().list_events(tenant_key, method=method, status=status, offset=offset, limit=limit)

    def get_event(self, key: str, tenant_key: str) -> PropagationEvent:
        return self._get_event_or_404(key, tenant_key)

    def create_event(self, event: PropagationEvent) -> PropagationEvent:
        prop = self._require_prop()
        if event.happened_at is None:
            event.happened_at = _now()
        return prop.create_event(event)

    def update_outcome(
        self,
        key: str,
        tenant_key: str,
        *,
        survived_count: int,
        failure_reasons: list[str] | None = None,
    ) -> PropagationEvent:
        """Record the final outcome (survivors, failures) and derive success rate."""
        event = self._get_event_or_404(key, tenant_key)
        if survived_count > event.quantity:
            raise ValidationError("survived_count cannot exceed the propagated quantity.")
        event.survived_count = survived_count
        event.failure_reasons = failure_reasons or []
        event.success_rate = (survived_count / event.quantity) if event.quantity else None
        event.status = PropagationEventStatus.COMPLETED if survived_count > 0 else PropagationEventStatus.FAILED
        return self._require_prop().update_event(key, event)

    def update_progress(
        self,
        key: str,
        tenant_key: str,
        *,
        callus_observed_at: datetime | None = None,
        roots_observed_at: datetime | None = None,
        transplant_ready_at: datetime | None = None,
    ) -> PropagationEvent:
        """Stamp propagation milestones and advance the derived status."""
        event = self._get_event_or_404(key, tenant_key)
        if callus_observed_at is not None:
            event.callus_observed_at = callus_observed_at
        if roots_observed_at is not None:
            event.roots_observed_at = roots_observed_at
            if event.status == PropagationEventStatus.IN_PROGRESS:
                event.status = PropagationEventStatus.ROOTED
        if transplant_ready_at is not None:
            event.transplant_ready_at = transplant_ready_at
            if event.status in (PropagationEventStatus.IN_PROGRESS, PropagationEventStatus.ROOTED):
                event.status = PropagationEventStatus.TRANSPLANTED
        return self._require_prop().update_event(key, event)

    # ── Batches ────────────────────────────────────────────────────────────────

    def create_batch(self, batch: PropagationBatch) -> PropagationBatch:
        prop = self._require_prop()
        if batch.started_at is None:
            batch.started_at = _now()
        return prop.create_batch(batch)

    def list_batches(
        self,
        tenant_key: str,
        *,
        status: str | None = None,
        method: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PropagationBatch], int]:
        return self._require_prop().list_batches(tenant_key, status=status, method=method, offset=offset, limit=limit)

    def get_batch(self, key: str, tenant_key: str) -> PropagationBatch:
        batch = self._require_prop().get_batch(key, tenant_key)
        if batch is None:
            raise NotFoundError("PropagationBatch", key)
        return batch

    def get_batch_events(self, key: str, tenant_key: str) -> list[PropagationEvent]:
        self.get_batch(key, tenant_key)  # 404 for foreign / unknown batch
        return self._require_prop().list_events_for_batch(key, tenant_key)

    def update_batch(
        self,
        key: str,
        tenant_key: str,
        *,
        status: PropagationBatchStatus | None = None,
        completed_at: datetime | None = None,
        notes: str | None = None,
    ) -> PropagationBatch:
        batch = self.get_batch(key, tenant_key)
        if status is not None:
            batch.status = status
        if completed_at is not None:
            batch.completed_at = completed_at
        if notes is not None:
            batch.notes = notes
        return self._require_prop().update_batch(key, batch)

    def finalize_batch(self, key: str, tenant_key: str, target_planting_run_key: str) -> PropagationBatch:
        """Complete a batch and hand its result plants over to a PlantingRun.

        The batch is marked ``completed`` and linked to the run; the aggregate
        survivor count is rolled up from the batch's events.
        """
        batch = self.get_batch(key, tenant_key)
        if batch.status == PropagationBatchStatus.COMPLETED:
            raise ValidationError("Batch is already finalized.")
        if self._planting_run_repo is not None:
            run = self._planting_run_repo.get_by_key(target_planting_run_key)
            if run is None or getattr(run, "tenant_key", tenant_key) != tenant_key:
                raise NotFoundError("PlantingRun", target_planting_run_key)
        events = self._require_prop().list_events_for_batch(key, tenant_key)
        total_survived = sum(e.survived_count or 0 for e in events)
        total_quantity = sum(e.quantity for e in events)
        batch.status = PropagationBatchStatus.COMPLETED
        batch.completed_at = _now()
        batch.target_planting_run_key = target_planting_run_key
        batch.total_survived = total_survived
        batch.overall_success_rate = (total_survived / total_quantity) if total_quantity else None
        return self._require_prop().update_batch(key, batch)

    # ── Rooting protocols ──────────────────────────────────────────────────────

    def create_protocol(self, protocol: RootingProtocol) -> RootingProtocol:
        return self._require_prop().create_protocol(protocol)

    def list_protocols(
        self,
        tenant_key: str,
        *,
        method: str | None = None,
        is_template: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[RootingProtocol], int]:
        return self._require_prop().list_protocols(
            tenant_key, method=method, is_template=is_template, offset=offset, limit=limit
        )

    def get_protocol(self, key: str, tenant_key: str) -> RootingProtocol:
        protocol = self._require_prop().get_protocol(key, tenant_key)
        if protocol is None:
            raise NotFoundError("RootingProtocol", key)
        return protocol

    def update_protocol(self, key: str, tenant_key: str, protocol: RootingProtocol) -> RootingProtocol:
        existing = self.get_protocol(key, tenant_key)
        if existing.tenant_key == "":
            raise ForbiddenError("Global protocol templates cannot be edited by a tenant.")
        protocol.tenant_key = tenant_key
        return self._require_prop().update_protocol(key, protocol)

    def delete_protocol(self, key: str, tenant_key: str) -> None:
        existing = self.get_protocol(key, tenant_key)
        if existing.tenant_key == "":
            raise ForbiddenError("Global protocol templates cannot be deleted by a tenant.")
        if self._require_prop().protocol_in_use(key, tenant_key):
            raise ValidationError("Protocol is in use by propagation events and cannot be deleted.")
        self._require_prop().delete_protocol(key)

    def protocol_stats(self, key: str, tenant_key: str) -> dict[str, Any]:
        """Per-protocol success statistics across the tenant's events."""
        self.get_protocol(key, tenant_key)  # 404 for foreign / unknown protocol
        rows = self._require_prop().stats(tenant_key, "protocol")
        for row in rows:
            if row.get("key") == key:
                return row
        return {"key": key, "event_count": 0, "total_quantity": 0, "total_survived": 0, "success_rate": None}

    # ── Mother plants ──────────────────────────────────────────────────────────
    #
    # The mother flags (``is_mother`` / ``mother_priority`` / ``mother_health_score``
    # / retirement metadata) are denormalized onto the ``plant_instances`` document
    # per REQ-017 §2. They are not part of the lean :class:`PlantInstance` model, so
    # these operations return the raw document dict (surfaced via ``MotherResponse``).

    def list_mothers(self, tenant_key: str, offset: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        return self._require_prop().list_mothers(tenant_key, offset, limit)

    def get_mother(self, plant_key: str, tenant_key: str) -> dict[str, Any]:
        doc = self._require_prop().get_plant_raw(plant_key, tenant_key)
        if doc is None:
            raise NotFoundError("PlantInstance", plant_key)
        return doc

    def designate_mother(self, plant_key: str, tenant_key: str, *, priority: str | None = None) -> dict[str, Any]:
        self._get_plant_or_404(plant_key, tenant_key)
        fields: dict[str, Any] = {
            "is_mother": True,
            "mother_designated_at": _now().isoformat(),
            "mother_retired_at": None,
        }
        if priority is not None:
            fields["mother_priority"] = priority
        return self._require_prop().update_plant_fields(plant_key, fields)

    def retire_mother(self, plant_key: str, tenant_key: str, *, reason: str | None = None) -> dict[str, Any]:
        self._get_plant_or_404(plant_key, tenant_key)
        fields: dict[str, Any] = {
            "is_mother": False,
            "mother_retired_at": _now().isoformat(),
            "mother_retire_reason": reason,
        }
        return self._require_prop().update_plant_fields(plant_key, fields)

    def update_mother_health(self, plant_key: str, tenant_key: str, *, health_score: int) -> dict[str, Any]:
        if not 0 <= health_score <= 100:
            raise ValidationError("health_score must be between 0 and 100.")
        self._get_plant_or_404(plant_key, tenant_key)
        return self._require_prop().update_plant_fields(plant_key, {"mother_health_score": health_score})

    # ── Phenotype notes ────────────────────────────────────────────────────────

    def add_phenotype(self, note: PhenotypeNote, tenant_key: str) -> PhenotypeNote:
        self._get_plant_or_404(note.plant_key, tenant_key)
        note.tenant_key = tenant_key
        if note.observed_at is None:
            note.observed_at = _now()
        return self._require_prop().create_phenotype(note)

    def list_phenotypes(self, plant_key: str, tenant_key: str) -> list[PhenotypeNote]:
        self._get_plant_or_404(plant_key, tenant_key)
        return self._require_prop().list_phenotypes_for_plant(plant_key, tenant_key)

    def delete_phenotype(self, plant_key: str, note_key: str, tenant_key: str) -> None:
        note = self._require_prop().get_phenotype(note_key, tenant_key)
        if note is None or note.plant_key != plant_key:
            raise NotFoundError("PhenotypeNote", note_key)
        self._require_prop().delete_phenotype(note_key)

    # ── Lineage ────────────────────────────────────────────────────────────────

    def get_lineage(self, plant_key: str, tenant_key: str, max_depth: int = 10) -> dict[str, Any]:
        """Ancestor chains + flat ancestor list for a plant (tenant-scoped)."""
        self._get_plant_or_404(plant_key, tenant_key)
        engine = self._require_lineage()
        paths: list[LineagePath] = engine.trace_ancestors(plant_key, tenant_key, max_depth)
        ancestors = engine.list_ancestors(plant_key, tenant_key, max_depth)
        return {
            "plant_key": plant_key,
            "paths": [list(p.plant_keys) for p in paths],
            "ancestors": ancestors,
        }

    def get_descendants(self, plant_key: str, tenant_key: str, max_depth: int = 10) -> list[PlantInstance]:
        """Descendant (clone-tree) list for a plant (tenant-scoped)."""
        self._get_plant_or_404(plant_key, tenant_key)
        return self._require_lineage().trace_descendants(plant_key, tenant_key, max_depth)

    def check_graft_compatibility(
        self, scion_key: str, rootstock_key: str, tenant_key: str
    ) -> GraftCompatibilityResult:
        """Graft compatibility between two of the tenant's plants (genus/family, §3)."""
        scion = self._get_plant_or_404(scion_key, tenant_key)
        rootstock = self._get_plant_or_404(rootstock_key, tenant_key)
        if scion_key == rootstock_key:
            raise ValidationError("Scion and rootstock must be different plants.")
        return self._require_lineage().check_graft_compatibility(scion.species_key, rootstock.species_key)

    # ── Statistics ──────────────────────────────────────────────────────────────

    def stats(self, tenant_key: str, group_by: str = "method") -> list[dict[str, Any]]:
        if group_by not in ("method", "species", "protocol", "cultivar"):
            raise ValidationError(f"Unsupported stats grouping: {group_by}")
        return self._require_prop().stats(tenant_key, group_by)
