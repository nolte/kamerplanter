"""REQ-013 §2 — SuccessionPlanService CRUD + run generation (Szenario 4)."""

from datetime import date

import pytest

from app.common.enums import SuccessionPlanStatus
from app.common.exceptions import NotFoundError
from app.domain.models.planting_run import PlantingRun
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.services.succession_plan_service import SuccessionPlanService

TENANT = "tenant_lisa"


class _FakeSuccessionRepo:
    def __init__(self) -> None:
        self._store: dict[str, SuccessionPlan] = {}
        self._seq = 0
        self.run_edges: list[tuple[str, str]] = []
        self.location_edges: list[tuple[str, str]] = []

    def get_all(self, offset=0, limit=50, tenant_key=None, *, all_tenants=False):
        items = [p for p in self._store.values() if p.tenant_key == tenant_key]
        return items[offset : offset + limit], len(items)

    def get_by_key(self, key):
        return self._store.get(key)

    def get_or_raise(self, key):
        plan = self._store.get(key)
        if plan is None:
            raise NotFoundError("SuccessionPlan", key)
        return plan

    def create(self, plan: SuccessionPlan) -> SuccessionPlan:
        self._seq += 1
        key = f"sp{self._seq}"
        stored = plan.model_copy(update={"key": key})
        self._store[key] = stored
        return stored

    def update(self, key, plan: SuccessionPlan) -> SuccessionPlan:
        stored = plan.model_copy(update={"key": key})
        self._store[key] = stored
        return stored

    def delete(self, key) -> bool:
        return self._store.pop(key, None) is not None

    def link_plan_to_run(self, plan_key, run_key) -> None:
        self.run_edges.append((plan_key, run_key))

    def link_plan_to_location(self, plan_key, location_key) -> None:
        self.location_edges.append((plan_key, location_key))

    def get_run_keys_for_plan(self, plan_key) -> list[str]:
        return [rk for pk, rk in self.run_edges if pk == plan_key]


class _FakeRunService:
    """Echoes back created runs with a fresh key; records the entries per run."""

    def __init__(self) -> None:
        self._seq = 0
        self.created_runs: list[PlantingRun] = []
        self.created_entries: list[list] = []

    def create_run(self, run: PlantingRun, entries=None) -> PlantingRun:
        self._seq += 1
        created = run.model_copy(update={"key": f"run{self._seq}"})
        self.created_runs.append(created)
        self.created_entries.append(entries or [])
        return created


def _plan(**overrides) -> SuccessionPlan:
    data = {
        "tenant_key": TENANT,
        "name": "Salat-Staffel Beet C 2026",
        "species_key": "species_lactuca_sativa",
        "cultivar_key": "cultivar_lollo_rosso",
        "interval_days": 21,
        "start_date": date(2026, 4, 1),
        "end_date": date(2026, 8, 31),
        "plants_per_batch": 12,
        "location_key": "loc_beet_c",
    }
    data.update(overrides)
    return SuccessionPlan(**data)


def _service():
    repo = _FakeSuccessionRepo()
    run_service = _FakeRunService()
    return SuccessionPlanService(repo, run_service), repo, run_service


class TestCrud:
    def test_create_sets_defaults_and_total_batches(self):
        service, _repo, _rs = _service()
        created = service.create_plan(_plan())
        assert created.status == SuccessionPlanStatus.PLANNED
        assert created.total_batches == 8
        assert created.completed_batches == 0

    def test_get_plan_enforces_tenant(self):
        service, _repo, _rs = _service()
        created = service.create_plan(_plan())
        with pytest.raises(NotFoundError):
            service.get_plan(created.key, tenant_key="other")

    def test_update_recomputes_total_batches(self):
        service, _repo, _rs = _service()
        created = service.create_plan(_plan())
        updated = service.update_plan(created.key, {"interval_days": 42}, tenant_key=TENANT)
        # 152-day window / 42 → 3 + 1 = 4 batches.
        assert updated.total_batches == 4

    def test_update_ignores_unknown_fields(self):
        service, _repo, _rs = _service()
        created = service.create_plan(_plan())
        updated = service.update_plan(created.key, {"tenant_key": "hijack", "notes": "spring"}, tenant_key=TENANT)
        assert updated.tenant_key == TENANT
        assert updated.notes == "spring"

    def test_delete_plan(self):
        service, _repo, _rs = _service()
        created = service.create_plan(_plan())
        assert service.delete_plan(created.key, tenant_key=TENANT) is True


class TestGenerateRuns:
    def test_generate_creates_eight_runs_and_edges(self):
        service, repo, run_service = _service()
        created = service.create_plan(_plan())

        plan, runs = service.generate_runs(created.key, tenant_key=TENANT)

        assert len(runs) == 8
        assert len(run_service.created_runs) == 8
        # one has_succession_plan edge per run + one succession_at edge.
        assert len(repo.run_edges) == 8
        assert repo.location_edges == [(created.key, "loc_beet_c")]
        # plan bookkeeping updated.
        assert plan.total_batches == 8
        assert plan.completed_batches == 8
        assert plan.status == SuccessionPlanStatus.ACTIVE

    def test_generated_runs_carry_sequence_and_entry(self):
        service, _repo, run_service = _service()
        created = service.create_plan(_plan())

        _plan_out, runs = service.generate_runs(created.key, tenant_key=TENANT)

        assert [r.succession_sequence for r in runs] == list(range(1, 9))
        assert all(r.succession_total == 8 for r in runs)
        assert runs[0].planned_start_date == date(2026, 4, 1)
        assert runs[1].planned_start_date == date(2026, 4, 22)
        # each run received exactly one entry with the plan's species.
        for entries in run_service.created_entries:
            assert len(entries) == 1
            assert entries[0].species_key == "species_lactuca_sativa"
            assert entries[0].quantity == 12


class TestGenerateNextRun:
    def test_generate_next_advances_one_batch(self):
        service, repo, run_service = _service()
        created = service.create_plan(_plan())

        plan1, run1 = service.generate_next_run(created.key, tenant_key=TENANT)
        assert run1 is not None
        assert run1.succession_sequence == 1
        assert plan1.completed_batches == 1
        assert plan1.status == SuccessionPlanStatus.ACTIVE

        plan2, run2 = service.generate_next_run(created.key, tenant_key=TENANT)
        assert run2 is not None
        assert run2.succession_sequence == 2
        assert plan2.completed_batches == 2
        assert len(repo.run_edges) == 2

    def test_generate_next_returns_none_when_complete(self):
        service, _repo, _rs = _service()
        created = service.create_plan(_plan(end_date=date(2026, 4, 1)))  # single batch

        _p1, run1 = service.generate_next_run(created.key, tenant_key=TENANT)
        assert run1 is not None

        plan2, run2 = service.generate_next_run(created.key, tenant_key=TENANT)
        assert run2 is None
        assert plan2.completed_batches == 1
