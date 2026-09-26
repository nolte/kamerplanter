"""A child key is resolved within its verified parent — #1867.

Three tenant-scoped writes verified the **parent** (run, tank, fertilizer)
against the caller's tenant and then loaded the **child** by its key alone:

* ``PUT``/``DELETE /t/{slug}/planting-runs/{key}/entries/{entry_key}``: any
  tenant's entry, and the update re-stamped the caller's tenant onto it;
* ``PUT``/``DELETE /t/{slug}/tanks/{key}/schedules/{skey}``: any tenant's
  maintenance schedule;
* ``DELETE /t/{slug}/fertilizers/{key}/incompatibilities/{other_key}``:
  ``other_key`` was never resolved, and ``key`` may be a *global* product, so
  tenant A deleted the edge tenant B declared between its private product and a
  global one.

The doubles store the child's parent key the way the documents do, and the
services are the real ones.
"""

from __future__ import annotations

import pytest

from app.common.enums import FertilizerType, MaintenanceType, PlantingRunStatus, PlantingRunType, TankType
from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.models.tank import MaintenanceSchedule, Tank
from app.domain.services.fertilizer_service import FertilizerService
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.tank_service import TankService

# ── planting-run entries ──────────────────────────────────────────────────


class _RunRepo:
    def __init__(self) -> None:
        self.runs = {
            "run_a": PlantingRun(_key="run_a", tenant_key="t_a", name="A", run_type=PlantingRunType.MONOCULTURE),
            "run_b": PlantingRun(_key="run_b", tenant_key="t_b", name="B", run_type=PlantingRunType.MONOCULTURE),
        }
        self.entries = {
            "e_a": PlantingRunEntry(
                _key="e_a", run_key="run_a", tenant_key="t_a", species_key="s", quantity=2, id_prefix="AA"
            ),
            "e_b": PlantingRunEntry(
                _key="e_b", run_key="run_b", tenant_key="t_b", species_key="s", quantity=3, id_prefix="BB"
            ),
        }
        self.writes: list[tuple[str, str]] = []

    def get_or_raise(self, key: str) -> PlantingRun:
        if key not in self.runs:
            raise NotFoundError("PlantingRun", key)
        return self.runs[key]

    def get_entry_or_raise(self, key: str) -> PlantingRunEntry:
        if key not in self.entries:
            raise NotFoundError("PlantingRunEntry", key)
        return self.entries[key]

    def update_entry(self, key: str, entry: PlantingRunEntry) -> PlantingRunEntry:
        self.writes.append(("update", key))
        self.entries[key] = entry
        return entry

    def delete_entry(self, key: str) -> bool:
        self.writes.append(("delete", key))
        return self.entries.pop(key, None) is not None

    def get_entries(self, run_key: str) -> list[PlantingRunEntry]:
        return [e for e in self.entries.values() if e.run_key == run_key]

    def update(self, key: str, run: PlantingRun) -> PlantingRun:
        return run


def _run_service() -> tuple[PlantingRunService, _RunRepo]:
    repo = _RunRepo()
    return PlantingRunService(repo, None, None), repo  # type: ignore[arg-type]


@pytest.mark.parametrize("entry", ["e_b", "no-such-entry"], ids=["foreign-entry", "unknown-entry"])
def test_an_entry_of_another_run_cannot_be_updated(entry: str) -> None:
    service, repo = _run_service()

    with pytest.raises(NotFoundError):
        service.update_entry("run_a", entry, {"quantity": 9}, tenant_key="t_a")

    assert repo.writes == []
    assert repo.entries["e_b"].tenant_key == "t_b"


@pytest.mark.parametrize("entry", ["e_b", "no-such-entry"], ids=["foreign-entry", "unknown-entry"])
def test_an_entry_of_another_run_cannot_be_deleted(entry: str) -> None:
    service, repo = _run_service()

    with pytest.raises(NotFoundError):
        service.delete_entry("run_a", entry, tenant_key="t_a")

    assert repo.writes == []


def test_the_run_itself_is_resolved_under_the_tenant() -> None:
    service, repo = _run_service()

    with pytest.raises(NotFoundError):
        service.update_entry("run_b", "e_b", {"quantity": 9}, tenant_key="t_a")

    assert repo.writes == []


def test_the_own_entry_of_the_own_run_is_updated_and_deleted() -> None:
    service, repo = _run_service()
    assert repo.runs["run_a"].status == PlantingRunStatus.PLANNED

    service.update_entry("run_a", "e_a", {"quantity": 5}, tenant_key="t_a")
    service.delete_entry("run_a", "e_a", tenant_key="t_a")

    assert repo.writes == [("update", "e_a"), ("delete", "e_a")]


# ── tank maintenance schedules ────────────────────────────────────────────


class _TankRepo:
    def __init__(self) -> None:
        self.tanks = {
            "tank_a": Tank(_key="tank_a", tenant_key="t_a", name="A", tank_type=TankType.NUTRIENT, volume_liters=10),
            "tank_b": Tank(_key="tank_b", tenant_key="t_b", name="B", tank_type=TankType.NUTRIENT, volume_liters=10),
        }
        self.schedules = {
            "s_a": MaintenanceSchedule(
                _key="s_a", tank_key="tank_a", maintenance_type=MaintenanceType.CLEANING, interval_days=7
            ),
            "s_b": MaintenanceSchedule(
                _key="s_b", tank_key="tank_b", maintenance_type=MaintenanceType.CLEANING, interval_days=7
            ),
        }
        self.writes: list[tuple[str, str]] = []

    def get_or_raise(self, key: str) -> Tank:
        if key not in self.tanks:
            raise NotFoundError("Tank", key)
        return self.tanks[key]

    def get_schedule_or_raise(self, key: str) -> MaintenanceSchedule:
        if key not in self.schedules:
            raise NotFoundError("MaintenanceSchedule", key)
        return self.schedules[key]

    def update_schedule(self, key: str, schedule: MaintenanceSchedule) -> MaintenanceSchedule:
        self.writes.append(("update", key))
        return schedule

    def delete_schedule(self, key: str) -> bool:
        self.writes.append(("delete", key))
        return True


def _tank_service() -> tuple[TankService, _TankRepo]:
    repo = _TankRepo()
    return TankService(repo, None), repo  # type: ignore[arg-type]


@pytest.mark.parametrize("schedule", ["s_b", "no-such-schedule"], ids=["foreign", "unknown"])
def test_a_schedule_of_another_tank_cannot_be_changed_or_deleted(schedule: str) -> None:
    service, repo = _tank_service()

    with pytest.raises(NotFoundError):
        service.update_schedule("tank_a", schedule, {"interval_days": 1}, tenant_key="t_a")
    with pytest.raises(NotFoundError):
        service.delete_schedule("tank_a", schedule, tenant_key="t_a")

    assert repo.writes == []
    assert repo.schedules["s_b"].interval_days == 7


def test_the_own_schedule_of_the_own_tank_is_changed_and_deleted() -> None:
    service, repo = _tank_service()

    service.update_schedule("tank_a", "s_a", {"interval_days": 14}, tenant_key="t_a")
    service.delete_schedule("tank_a", "s_a", tenant_key="t_a")

    assert repo.writes == [("update", "s_a"), ("delete", "s_a")]


# ── fertilizer incompatibilities ──────────────────────────────────────────


class _FertRepo:
    def __init__(self) -> None:
        def fert(key: str, tenant: str) -> Fertilizer:
            return Fertilizer(_key=key, tenant_key=tenant, product_name=key, fertilizer_type=FertilizerType.BASE)

        self.ferts = {
            "f_a": fert("f_a", "t_a"),
            "f_b": fert("f_b", "t_b"),
            "g1": fert("g1", ""),
            "g2": fert("g2", ""),
        }
        self.removed: list[tuple[str, str]] = []

    def get_or_raise(self, key: str) -> Fertilizer:
        if key not in self.ferts:
            raise NotFoundError("Fertilizer", key)
        return self.ferts[key]

    def remove_incompatibility(self, a: str, b: str) -> bool:
        self.removed.append((a, b))
        return True


def _fert_service() -> tuple[FertilizerService, _FertRepo]:
    repo = _FertRepo()
    return FertilizerService(repo), repo  # type: ignore[arg-type]


@pytest.mark.parametrize("other", ["f_b", "no-such-fertilizer"], ids=["foreign", "unknown"])
def test_removing_against_a_foreign_or_unknown_product_answers_404(other: str) -> None:
    service, repo = _fert_service()

    with pytest.raises(NotFoundError):
        service.remove_incompatibility("g1", other, tenant_key="t_a", is_platform_admin=False)

    assert repo.removed == []


def test_a_member_cannot_remove_a_global_to_global_edge() -> None:
    service, repo = _fert_service()

    with pytest.raises(ForbiddenError):
        service.remove_incompatibility("g1", "g2", tenant_key="t_a", is_platform_admin=False)

    assert repo.removed == []


def test_a_platform_admin_may_remove_a_global_to_global_edge() -> None:
    service, repo = _fert_service()

    service.remove_incompatibility("g1", "g2", tenant_key="t_a", is_platform_admin=True)

    assert repo.removed == [("g1", "g2")]


@pytest.mark.parametrize(("a", "b"), [("f_a", "g1"), ("g1", "f_a")], ids=["own-first", "own-second"])
def test_an_edge_touching_an_own_product_is_removed(a: str, b: str) -> None:
    service, repo = _fert_service()

    service.remove_incompatibility(a, b, tenant_key="t_a", is_platform_admin=False)

    assert repo.removed == [(a, b)]


# ── adding follows the same rule as removing (bundle A review, W2) ─────────


def _add_repo() -> _FertRepo:
    repo = _FertRepo()
    repo.added = []  # type: ignore[attr-defined]
    repo.add_incompatibility = lambda a, b, r, s: repo.added.append((a, b)) or {}  # type: ignore[attr-defined]
    return repo


def test_a_member_cannot_declare_a_global_to_global_edge() -> None:
    repo = _add_repo()

    with pytest.raises(ForbiddenError):
        FertilizerService(repo).add_incompatibility(  # type: ignore[arg-type]
            "g1", "g2", "r", "high", tenant_key="t_a", is_platform_admin=False
        )

    assert repo.added == []  # type: ignore[attr-defined]


def test_a_member_declares_an_edge_touching_an_own_product() -> None:
    repo = _add_repo()

    FertilizerService(repo).add_incompatibility(  # type: ignore[arg-type]
        "f_a", "g1", "r", "high", tenant_key="t_a", is_platform_admin=False
    )

    assert repo.added == [("f_a", "g1")]  # type: ignore[attr-defined]
