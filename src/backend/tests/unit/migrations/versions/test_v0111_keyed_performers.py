"""spec/privacy/09 §5, §9, §11, §12 — v0111 lays down the keyed performer fields (TA-700, TA-702, TA-716).

The phases are decided here against an in-memory store with the shape of :class:`KeyedPerformerStore`;
the AQL itself (the tenant predicate on the row or on its tank, the ``active`` gate, the service-account
check, ``down``) is measured against a real ArangoDB in
``tests/integration/test_v0111_keyed_performers.py``. What this module pins and the integration test
cannot cheaply: a tenant whose transaction fails while the others finish, a residual the after-check
finds, the runner's handling of both, and the build-side precheck (models, inventory, request schemas).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_export_engine import TenantExportEngine
from app.domain.models.nutrient_plan import NutrientPlan
from app.domain.models.privacy import PERSON_LABEL_MAX_LENGTH
from app.domain.models.tank import MaintenanceLog, TankFillEvent
from app.domain.models.task import WorkflowTemplate
from app.domain.models.watering_event import WateringEvent
from app.domain.models.watering_log import WateringLog
from app.migrations.framework import tracking
from app.migrations.framework.report_store import DETAILS_SHAPE, redact_details
from app.migrations.framework.runner import MigrationRunner
from app.migrations.versions import v0111_keyed_performers as v0111
from app.migrations.versions.v0111_keyed_performers import (
    BUCKET_INSPECTOR_CLEARED,
    BUCKET_MAINTENANCE_LOGS,
    BUCKET_NUTRIENT_PLANS,
    BUCKET_SERVICE_ACCOUNT_KEYED,
    BUCKET_WATERING_EVENTS,
    BUCKET_WORKFLOW_TEMPLATES,
    COPY_STEPS,
    STEP_BUCKETS,
    CopyStep,
    Hits,
    KeyedPerformersMigration,
)
from tests.unit.migrations.framework.conftest import FakeDatabase

_STEP_BY_BUCKET: dict[str, CopyStep] = {step.bucket: step for step in COPY_STEPS}


@dataclass
class _Row:
    collection: str
    tenant_key: str
    doc: dict[str, Any]
    key: str


def _copy_needs(step: CopyStep, doc: dict[str, Any]) -> tuple[bool, bool]:
    """The copy rule of the AQL, restated: ``(needs_key, needs_label)``."""
    needs_key = step.key_field not in doc
    if step.label_field is None:
        return needs_key, False
    source = doc.get(step.source_field)
    needs_label = doc.get(step.label_field) is None and isinstance(source, str) and source != ""
    return needs_key, needs_label


@dataclass
class FakeStore:
    """Holds rows per collection and applies the steps the way the AQL does (one tenant at a time)."""

    tenants: dict[str, str]
    rows: list[_Row] = field(default_factory=list)
    #: ``user key -> account_type``; memberships as ``(user key, tenant key)``.
    users: dict[str, str] = field(default_factory=dict)
    memberships: set[tuple[str, str]] = field(default_factory=set)
    missing: list[str] = field(default_factory=list)
    failing_tenants: set[str] = field(default_factory=set)
    #: Rows that reappear after apply (a writer racing the migration) — drives ``verify_failed``.
    resurrect: list[_Row] = field(default_factory=list)
    applied_tenants: list[str] = field(default_factory=list)
    asked_active_only: list[bool] = field(default_factory=list)

    def missing_collections(self) -> list[str]:
        return list(self.missing)

    def tenant_keys(self, *, active_only: bool) -> list[str]:
        self.asked_active_only.append(active_only)
        if active_only:
            return sorted(k for k, status in self.tenants.items() if status == "active")
        return sorted(k for k, status in self.tenants.items() if status != "deleted")

    def _service_key(self, row: _Row) -> str | None:
        if row.doc.get("inspected_by_key") is not None:
            return None
        account = row.doc["inspector"][len("mcp:") :]
        if self.users.get(account) == "service" and (account, row.tenant_key) in self.memberships:
            return account
        return None

    def _matches(self, bucket: str, row: _Row) -> bool:
        if bucket == BUCKET_INSPECTOR_CLEARED:
            inspector = row.doc.get("inspector")
            return row.collection == "inspections" and isinstance(inspector, str) and inspector.startswith("mcp:")
        step = _STEP_BY_BUCKET[bucket]
        return row.collection == step.collection and any(_copy_needs(step, row.doc))

    def hits(self, bucket: str, tenant_key: str) -> Hits:
        rows = [r for r in self.rows if r.tenant_key == tenant_key and self._matches(bucket, r)]
        keyed = sum(1 for r in rows if bucket == BUCKET_INSPECTOR_CLEARED and self._service_key(r) is not None)
        return Hits(len(rows), [r.key for r in rows][:25], keyed)

    def apply(self, tenant_key: str) -> dict[str, int]:
        if tenant_key in self.failing_tenants:
            raise RuntimeError("transaction aborted")
        self.applied_tenants.append(tenant_key)
        changed = dict.fromkeys((*STEP_BUCKETS, BUCKET_SERVICE_ACCOUNT_KEYED), 0)
        for row in self.rows:
            if row.tenant_key != tenant_key:
                continue
            for bucket in STEP_BUCKETS:
                if not self._matches(bucket, row):
                    continue
                changed[bucket] += 1
                if bucket == BUCKET_INSPECTOR_CLEARED:
                    service_key = self._service_key(row)
                    if service_key is not None:
                        row.doc["inspected_by_key"] = service_key
                        changed[BUCKET_SERVICE_ACCOUNT_KEYED] += 1
                    row.doc["inspector"] = ""
                    continue
                step = _STEP_BY_BUCKET[bucket]
                needs_key, needs_label = _copy_needs(step, row.doc)
                if needs_key:
                    row.doc[step.key_field] = None
                if needs_label and step.label_field is not None:
                    row.doc[step.label_field] = row.doc[step.source_field][:80]
        self.rows.extend(self.resurrect)
        self.resurrect = []
        return changed

    def _drops(self, step: CopyStep, doc: dict[str, Any]) -> list[str]:
        drop = []
        if step.key_field in doc and doc[step.key_field] is None:
            drop.append(step.key_field)
        if step.label_field is not None:
            label, source = doc.get(step.label_field), doc.get(step.source_field)
            if isinstance(label, str) and isinstance(source, str) and label == source[:80]:
                drop.append(step.label_field)
        return drop

    def removable(self, tenant_key: str) -> dict[str, Hits]:
        out: dict[str, Hits] = {}
        for step in COPY_STEPS:
            keys = [
                r.key
                for r in self.rows
                if r.tenant_key == tenant_key and r.collection == step.collection and self._drops(step, r.doc)
            ]
            out[step.bucket] = Hits(len(keys), keys[:25])
        return out

    def remove(self, tenant_key: str) -> dict[str, int]:
        removed: dict[str, int] = {}
        for step in COPY_STEPS:
            removed[step.bucket] = 0
            for row in self.rows:
                if row.tenant_key != tenant_key or row.collection != step.collection:
                    continue
                drop = self._drops(step, row.doc)
                if drop:
                    removed[step.bucket] += 1
                    for name in drop:
                        row.doc.pop(name)
        return removed


#: Seeded per tenant. ``svc`` is a service account and member of ``t_active``; ``human`` is a person;
#: ``svc_other`` a service account of another tenant only.
def _seeded() -> FakeStore:
    store = FakeStore(
        tenants={"t_active": "active", "t_suspended": "suspended", "t_deleted": "deleted"},
        users={"svc": "service", "human": "human", "svc_other": "service"},
        memberships={("svc", "t_active"), ("human", "t_active"), ("svc_other", "t_other")},
    )
    for tenant in ("t_active", "t_suspended"):
        store.rows += [
            _Row("watering_events", tenant, {"performed_by": "Lisa"}, f"{tenant}-we1"),
            _Row("watering_events", tenant, {"performed_by": None}, f"{tenant}-we2"),
            _Row("watering_logs", tenant, {"performed_by": "x" * 120}, f"{tenant}-wl1"),
            _Row("maintenance_logs", tenant, {"performed_by": ""}, f"{tenant}-ml1"),
            _Row("tank_fill_events", tenant, {"performed_by": "Maren"}, f"{tenant}-tf1"),
            _Row("nutrient_plans", tenant, {"author": "Lisa Beispiel"}, f"{tenant}-np1"),
            _Row("workflow_templates", tenant, {"created_by": "Lisa"}, f"{tenant}-wt1"),
            # A name that is literally an existing account key never becomes a key (TA-702).
            _Row("watering_events", tenant, {"performed_by": "human"}, f"{tenant}-we3"),
            _Row("inspections", tenant, {"inspector": "mcp:svc", "inspected_by_key": None}, f"{tenant}-in1"),
            _Row("inspections", tenant, {"inspector": "mcp:human", "inspected_by_key": None}, f"{tenant}-in2"),
            _Row("inspections", tenant, {"inspector": "mcp:svc_other", "inspected_by_key": None}, f"{tenant}-in3"),
            _Row("inspections", tenant, {"inspector": "mcp:gone", "inspected_by_key": None}, f"{tenant}-in4"),
            _Row("inspections", tenant, {"inspector": "mcp:svc", "inspected_by_key": "svc"}, f"{tenant}-in5"),
            _Row("inspections", tenant, {"inspector": "Maren", "inspected_by_key": None}, f"{tenant}-in6"),
        ]
    return store


def _doc(store: FakeStore, key: str) -> dict[str, Any]:
    return next(r for r in store.rows if r.key == key).doc


@pytest.fixture
def use_store(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    def _install(store: FakeStore) -> KeyedPerformersMigration:
        monkeypatch.setattr(KeyedPerformersMigration, "store_factory", lambda db: store)
        return KeyedPerformersMigration()

    return _install


class TestTheFrozenValues:
    def test_the_frozen_literals_are_the_definitions_at_the_time_of_writing(self) -> None:
        assert v0111._LABEL_MAX == PERSON_LABEL_MAX_LENGTH == 80
        assert v0111._MCP_PREFIX == "mcp:"
        assert v0111._SERVICE == "service"

    def test_it_is_a_reversible_data_backfill(self) -> None:
        """PRIV-716: a backfill walks the active tenants only — and asks for exactly those."""
        assert v0111.migration.kind == "data_backfill"
        assert v0111.migration.reversible is True
        assert v0111.migration.version == "0111"

    def test_rooting_protocols_are_not_a_step(self) -> None:
        """``rooting_protocols.author`` holds the creator's account key, not a typed name (09 §5, Stand)."""
        assert "rooting_protocols" not in {step.collection for step in COPY_STEPS}


class TestTheBuild:
    """The model and inventory half of the precheck, and PRIV-705 on the request side."""

    @pytest.mark.parametrize(
        ("model", "key_field", "label_field"),
        [
            (WateringEvent, "performed_by_user_key", "performed_by_label"),
            (WateringLog, "performed_by_user_key", "performed_by_label"),
            (MaintenanceLog, "performed_by_user_key", "performed_by_label"),
            (TankFillEvent, "performed_by_user_key", "performed_by_label"),
            (NutrientPlan, "author_user_key", "author_label"),
            (WorkflowTemplate, "created_by_user_key", None),
        ],
    )
    def test_a_stored_row_round_trips_the_new_fields(self, model: Any, key_field: str, label_field: str | None) -> None:
        """What the repository writes back after a read keeps the fields v0111 laid down."""
        base: dict[str, Any] = {
            WateringEvent: {"volume_liters": 1.0},
            WateringLog: {"volume_liters": 1.0, "plant_keys": ["p1"]},
            MaintenanceLog: {"maintenance_type": "cleaning"},
            TankFillEvent: {"fill_type": "full_change", "volume_liters": 10.0},
            NutrientPlan: {"name": "n"},
            WorkflowTemplate: {"name": "n"},
        }[model]
        stored = {**base, key_field: None}
        if label_field is not None:
            stored[label_field] = "Lisa"

        dumped = model.model_validate(stored).model_dump(by_alias=True, mode="json")

        assert key_field in dumped
        assert dumped[key_field] is None
        if label_field is not None:
            assert dumped[label_field] == "Lisa"
            with pytest.raises(ValueError):
                model.model_validate({**base, label_field: "x" * 81})

    def test_the_build_meets_the_precheck(self) -> None:
        assert v0111._unmet_build() == []

    def test_every_new_key_field_is_in_the_inventory(self) -> None:
        excluded = {(e.collection, e.user_field) for e in ErasureEngine.EXCLUDED_USER_REFERENCES}
        for step in COPY_STEPS:
            assert (step.collection, step.key_field) in excluded | ErasureEngine.account_reference_fields()
            assert TenantExportEngine.references_of(step.collection)[step.key_field].kind == "account"

    def test_no_request_schema_accepts_a_key_field(self) -> None:
        """PRIV-705: the key is the server's; a body can neither set nor smuggle it."""
        from app.api.v1.nutrient_plans import schemas as plan_schemas
        from app.api.v1.tanks import schemas as tank_schemas
        from app.api.v1.tasks import schemas as task_schemas
        from app.api.v1.watering_events import schemas as event_schemas
        from app.api.v1.watering_logs import schemas as log_schemas

        key_fields = {step.key_field for step in COPY_STEPS}
        for module in (plan_schemas, tank_schemas, task_schemas, event_schemas, log_schemas):
            for name in dir(module):
                schema = getattr(module, name)
                if not (isinstance(schema, type) and hasattr(schema, "model_fields")):
                    continue
                if not any(part in name for part in ("Create", "Update", "Request", "Input")):
                    continue
                assert not key_fields & set(schema.model_fields), f"{module.__name__}.{name}"

    def test_a_model_without_the_field_is_an_unmet_precondition(
        self,
        use_store,  # type: ignore[no-untyped-def]
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delitem(WorkflowTemplate.model_fields, "created_by_user_key")
        store = _seeded()

        report = use_store(store).up(None)

        assert report.precondition_unmet is True
        assert "model.workflow_templates.created_by_user_key" in report.details["phases"]["precheck"]["unmet"]
        assert store.applied_tenants == []


class TestThePrecheck:
    def test_a_missing_collection_leaves_the_migration_pending_and_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.missing = ["tank_fill_events"]

        report = use_store(store).up(None)

        assert report.precondition_unmet is True
        assert report.details["phases"]["precheck"] == {"ok": False, "unmet": ["tank_fill_events"], "candidates": {}}
        assert store.applied_tenants == []
        assert "performed_by_user_key" not in _doc(store, "t_active-we1")


class TestTheDryRun:
    def test_it_counts_and_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()

        report = use_store(store).up(None, dry_run=True)

        assert store.applied_tenants == []
        assert report.changed == 0
        assert report.details["status"] == "dry_run"
        assert report.details["buckets"][BUCKET_WATERING_EVENTS] == {"t_active": 3}
        assert report.details["buckets"][BUCKET_INSPECTOR_CLEARED] == {"t_active": 5}
        assert report.details["buckets"][BUCKET_SERVICE_ACCOUNT_KEYED] == {"t_active": 1}
        assert set(report.details["phases"]) == {"precheck", "dry_run"}
        assert _doc(store, "t_active-in1")["inspector"] == "mcp:svc"


class TestTheRealRun:
    def test_it_lays_down_the_fields_in_active_tenants_only(self, use_store) -> None:  # type: ignore[no-untyped-def]
        """TA-716: a data backfill skips ``suspended`` (and ``deleted``)."""
        store = _seeded()

        report = use_store(store).up(None)

        assert store.asked_active_only == [True]
        assert store.applied_tenants == ["t_active"]
        assert _doc(store, "t_active-we1") == {
            "performed_by": "Lisa",
            "performed_by_user_key": None,
            "performed_by_label": "Lisa",
        }
        # Nothing to copy from a null or empty source: the key alone.
        assert _doc(store, "t_active-we2") == {"performed_by": None, "performed_by_user_key": None}
        assert _doc(store, "t_active-ml1") == {"performed_by": "", "performed_by_user_key": None}
        assert _doc(store, "t_active-wl1")["performed_by_label"] == "x" * 80
        assert _doc(store, "t_active-wl1")["performed_by"] == "x" * 120  # the old field stays
        assert _doc(store, "t_active-np1")["author_label"] == "Lisa Beispiel"
        assert _doc(store, "t_active-wt1") == {"created_by": "Lisa", "created_by_user_key": None}
        assert _doc(store, "t_suspended-we1") == {"performed_by": "Lisa"}
        assert _doc(store, "t_suspended-in1")["inspector"] == "mcp:svc"
        assert report.details["status"] == "applied"
        assert report.incomplete is False
        assert report.details["phases"]["verify"] == {"residual": dict.fromkeys(STEP_BUCKETS, 0)}
        assert {"precheck", "dry_run", "apply", "verify"} <= set(report.details["phases"])

    def test_no_key_is_ever_taken_from_a_name(self, use_store) -> None:  # type: ignore[no-untyped-def]
        """TA-702: a typed name — even one that is literally an account key — leaves the key null."""
        store = _seeded()

        use_store(store).up(None)

        for row in store.rows:
            for step in COPY_STEPS:
                if row.collection == step.collection and row.tenant_key == "t_active":
                    assert row.doc[step.key_field] is None, row.key
        assert _doc(store, "t_active-we3")["performed_by_label"] == "human"

    def test_an_mcp_inspection_is_keyed_only_to_a_live_service_account_of_the_tenant(self, use_store) -> None:  # type: ignore[no-untyped-def]
        """TA-702: ``mcp:<key>`` becomes the key only for an existing service account (here: and member)."""
        store = _seeded()

        report = use_store(store).up(None)

        assert _doc(store, "t_active-in1") == {"inspector": "", "inspected_by_key": "svc"}
        assert _doc(store, "t_active-in2") == {"inspector": "", "inspected_by_key": None}  # a person
        assert _doc(store, "t_active-in3") == {"inspector": "", "inspected_by_key": None}  # another tenant's
        assert _doc(store, "t_active-in4") == {"inspector": "", "inspected_by_key": None}  # no such account
        assert _doc(store, "t_active-in5") == {"inspector": "", "inspected_by_key": "svc"}  # already keyed
        assert _doc(store, "t_active-in6") == {"inspector": "Maren", "inspected_by_key": None}  # not mcp:
        assert report.details["phases"]["apply"]["changed"][BUCKET_SERVICE_ACCOUNT_KEYED] == 1
        assert report.details["phases"]["apply"]["changed"][BUCKET_INSPECTOR_CLEARED] == 5

    def test_a_second_run_changes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        migration = use_store(store)
        migration.up(None)

        again = migration.up(None)

        assert again.changed == 0
        assert again.scanned == 0
        assert again.details["status"] == "applied"

    def test_a_failing_tenant_is_left_alone_and_the_run_is_partial(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.tenants["t_second"] = "active"
        store.rows.append(_Row("watering_events", "t_second", {"performed_by": "Ida"}, "t_second-we1"))
        store.failing_tenants = {"t_active"}

        report = use_store(store).up(None)

        assert report.details["phases"]["apply"]["tenants_failed"] == ["t_active"]
        assert report.details["phases"]["apply"]["tenants_done"] == ["t_second"]
        assert _doc(store, "t_second-we1")["performed_by_label"] == "Ida"
        assert report.details["status"] == "partial"
        assert report.incomplete is True
        assert report.details["phases"]["verify"]["residual"][BUCKET_WATERING_EVENTS] == 3

    def test_a_residual_after_apply_is_verify_failed(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.resurrect = [_Row("nutrient_plans", "t_active", {"author": "late"}, "t_active-np9")]

        report = use_store(store).up(None)

        assert report.details["status"] == "verify_failed"
        assert report.incomplete is True
        assert report.details["phases"]["verify"]["residual"][BUCKET_NUTRIENT_PLANS] == 1


class TestDown:
    def test_it_removes_null_keys_and_copied_labels_only(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        migration = use_store(store)
        migration.up(None)
        _doc(store, "t_active-np1")["author_label"] = "Edited"  # someone changed the label since
        _doc(store, "t_active-tf1")["performed_by_user_key"] = "u_stamped"  # a later path stamped a key

        report = migration.down(None)

        assert _doc(store, "t_active-we1") == {"performed_by": "Lisa"}
        assert _doc(store, "t_active-wl1") == {"performed_by": "x" * 120}
        assert _doc(store, "t_active-np1") == {"author": "Lisa Beispiel", "author_label": "Edited"}
        assert _doc(store, "t_active-tf1") == {"performed_by": "Maren", "performed_by_user_key": "u_stamped"}
        assert _doc(store, "t_active-wt1") == {"created_by": "Lisa"}
        # Step 4 is not reverted (module docstring).
        assert _doc(store, "t_active-in1") == {"inspector": "", "inspected_by_key": "svc"}
        assert report.details["buckets"][BUCKET_WORKFLOW_TEMPLATES + ".removed"] == {"t_active": 1}
        assert report.details["buckets"][BUCKET_MAINTENANCE_LOGS + ".removed"] == {"t_active": 1}
        assert report.details["status"] == "applied"

    def test_a_dry_run_down_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        migration = use_store(store)
        migration.up(None)

        report = migration.down(None, dry_run=True)

        assert _doc(store, "t_active-we1")["performed_by_label"] == "Lisa"
        assert report.changed == 0
        assert report.scanned == 8
        assert report.details["status"] == "dry_run"


def _alone(migration: KeyedPerformersMigration) -> MigrationRunner:
    """A runner over this migration only; the runner wants a gapless history from 0001 (M-1)."""
    migration.version = "0001"
    return MigrationRunner([migration])


class TestTheRunnerAndTheReport:
    def test_a_partial_run_is_not_recorded_and_its_report_is_persisted(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.failing_tenants = {"t_active"}
        db = FakeDatabase()

        reports = _alone(use_store(store)).upgrade(db)

        assert reports[-1].incomplete is True
        assert tracking.applied_versions(db) == set()
        (stored,) = db.collection("migration_reports").all()
        assert stored["status"] == "partial"
        assert stored["kind"] == "data_backfill"
        assert stored["redacted_entries"] == 0

    def test_a_clean_run_is_recorded(self, use_store) -> None:  # type: ignore[no-untyped-def]
        db = FakeDatabase()

        _alone(use_store(_seeded())).upgrade(db)

        assert tracking.applied_versions(db) == {"0001"}

    def test_the_reports_pass_the_redaction_filter_whole(self, use_store) -> None:  # type: ignore[no-untyped-def]
        """TA-700: everything up and down report fits the allowed shape — nothing is dropped."""
        migration = use_store(_seeded())
        dry = migration.up(None, dry_run=True)
        up = migration.up(None)
        down = migration.down(None)

        for report in (dry, up, down):
            redacted, dropped = redact_details(report.details)
            assert dropped == 0
            assert redacted == report.details
            assert set(report.details) <= set(DETAILS_SHAPE)
