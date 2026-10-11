"""MT-035 (#2131) — each count-free window reads the same page as its counted sibling, in one query.

The list routes answer a bare JSON array. Thirteen of them called a repository
method that returns ``(rows, total)`` and dropped ``total`` — a second scan of
every row the filter matches, paid on every page. Each now calls a ``*_window``
sibling. Two properties make that a safe swap, and both are asserted here
against a recording database double:

* the window issues **exactly** the page query of the counted method — same
  text, same bind variables (tenant predicate and ``LIMIT`` included) — so the
  route answers the same rows it did;
* it issues **no** ``COLLECT WITH COUNT`` query, which is the whole saving.

The real-server half (the window reads an index, the cursor walks a tenant
once) lives in ``tests/integration/test_list_windows.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.harvest_repository import ArangoHarvestRepository
from app.data_access.arango.import_job_repository import ArangoImportJobRepository
from app.data_access.arango.ipm_repository import ArangoIpmRepository
from app.data_access.arango.plant_diary_repository import ArangoPlantDiaryRepository
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from app.data_access.arango.post_harvest_repository import ArangoPostHarvestRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.data_access.repositories.propagation_repository import PropagationRepository

T = "tenant-a"
_COUNT = "COLLECT WITH COUNT"


class _RecordingDb:
    """Records every AQL query; a count query answers ``[7]``, a page query ``[]``."""

    def __init__(self) -> None:
        self.executed: list[tuple[str, dict[str, Any]]] = []
        self.aql = MagicMock()
        self.aql.execute.side_effect = self._execute

    def _execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        self.executed.append((query, dict(bind_vars or {})))
        return iter([7] if _COUNT in query else [])

    def collection(self, name: str) -> MagicMock:
        return MagicMock(name=name)


@dataclass(frozen=True)
class _Pair:
    id: str
    repo: Callable[[Any], Any]
    window: Callable[[Any], Any]
    counted: Callable[[Any], tuple[list[Any], int]]


_PAIRS = [
    _Pair(
        "ipm-inspections",
        ArangoIpmRepository,
        lambda r: r.get_inspections_for_plant_window("p1", 4, 3),
        lambda r: r.get_inspections_for_plant("p1", 4, 3),
    ),
    _Pair(
        "ipm-applications",
        ArangoIpmRepository,
        lambda r: r.get_applications_for_plant_window("p1", 4, 3),
        lambda r: r.get_applications_for_plant("p1", 4, 3),
    ),
    _Pair(
        "harvest-observations",
        ArangoHarvestRepository,
        lambda r: r.get_observations_for_plant_window("p1", 4, 3, tenant_key=T),
        lambda r: r.get_observations_for_plant("p1", 4, 3, tenant_key=T),
    ),
    _Pair(
        "harvest-batches",
        ArangoHarvestRepository,
        lambda r: r.list_batches_window(4, 3, tenant_key=T),
        lambda r: r.get_all_batches(4, 3, tenant_key=T),
    ),
    _Pair(
        "diary-plant",
        ArangoPlantDiaryRepository,
        lambda r: r.get_by_plant_window("p1", tenant_key=T, offset=4, limit=3),
        lambda r: r.get_by_plant("p1", tenant_key=T, offset=4, limit=3),
    ),
    _Pair(
        "diary-run",
        ArangoPlantDiaryRepository,
        lambda r: r.get_by_run_window("r1", tenant_key=T, offset=4, limit=3),
        lambda r: r.get_by_run("r1", tenant_key=T, offset=4, limit=3),
    ),
    _Pair(
        "post-harvest-batches",
        ArangoPostHarvestRepository,
        lambda r: r.list_batches_window(tenant_key=T, offset=4, limit=3),
        lambda r: r.list_batches(T, 4, 3),
    ),
    _Pair(
        "propagation-events",
        PropagationRepository,
        lambda r: r.list_events_window(tenant_key=T, method="cutting", status="rooting", offset=4, limit=3),
        lambda r: r.list_events(T, method="cutting", status="rooting", offset=4, limit=3),
    ),
    _Pair(
        "propagation-batches",
        PropagationRepository,
        lambda r: r.list_batches_window(tenant_key=T, status="open", method="cutting", offset=4, limit=3),
        lambda r: r.list_batches(T, status="open", method="cutting", offset=4, limit=3),
    ),
    _Pair(
        "tasks",
        ArangoTaskRepository,
        lambda r: r.get_tasks_window(4, 3, {"status": "pending"}, tenant_key=T, origins=["manual"]),
        lambda r: r.get_all_tasks(4, 3, {"status": "pending"}, tenant_key=T, origins=["manual"]),
    ),
    _Pair(
        "planting-runs-filtered",
        ArangoPlantingRunRepository,
        lambda r: r.get_runs_window(4, 3, {"status": "active"}, tenant_key=T),
        lambda r: r.get_all(4, 3, {"status": "active"}, tenant_key=T),
    ),
    _Pair(
        "planting-runs",
        ArangoPlantingRunRepository,
        lambda r: r.get_runs_window(4, 3, None, tenant_key=T),
        lambda r: r.get_all(4, 3, None, tenant_key=T),
    ),
    _Pair(
        "import-jobs",
        ArangoImportJobRepository,
        lambda r: r.list_all_window(4, 3, tenant_key=T),
        lambda r: r.list_all(4, 3, tenant_key=T),
    ),
]


def _queries(pair: _Pair, read: Callable[[Any], Any]) -> list[tuple[str, dict[str, Any]]]:
    db = _RecordingDb()
    read(pair.repo(db))
    return db.executed


@pytest.mark.parametrize("pair", _PAIRS, ids=[p.id for p in _PAIRS])
def test_the_counted_method_pays_a_second_scan(pair: _Pair) -> None:
    # Non-vacuity: the double does see the count the window is meant to drop,
    # and the counted method still answers it to its remaining callers.
    db = _RecordingDb()
    _, total = pair.counted(pair.repo(db))
    assert total == 7
    assert [_COUNT in q for q, _ in db.executed].count(True) == 1
    assert len(db.executed) == 2


@pytest.mark.parametrize("pair", _PAIRS, ids=[p.id for p in _PAIRS])
def test_the_window_is_the_counted_page_without_the_count(pair: _Pair) -> None:
    window = _queries(pair, pair.window)
    counted_page = [(q, v) for q, v in _queries(pair, pair.counted) if _COUNT not in q]

    assert window == counted_page
    assert len(window) == 1


@pytest.mark.parametrize("pair", _PAIRS, ids=[p.id for p in _PAIRS])
def test_the_window_binds_the_requested_page(pair: _Pair) -> None:
    ((query, bind_vars),) = _queries(pair, pair.window)

    assert "LIMIT @" in query
    assert sorted(v for k, v in bind_vars.items() if k in {"offset", "limit", "__offset", "__limit"}) == [3, 4]


@pytest.mark.parametrize(
    "read",
    [
        lambda r: r.list_batches_window(0, 3, tenant_key=""),
        lambda r: r.get_observations_for_plant_window("p1", 0, 3, tenant_key=""),
    ],
    ids=["harvest-batches", "harvest-observations"],
)
def test_a_harvest_window_refuses_an_unscoped_read(read: Callable[[Any], Any]) -> None:
    db = _RecordingDb()
    with pytest.raises(ValueError, match="tenant"):
        read(ArangoHarvestRepository(db))
    assert db.executed == []


@pytest.mark.parametrize(
    ("repo", "read"),
    [
        (ArangoPlantDiaryRepository, lambda r: r.get_by_plant_window("p1", tenant_key="")),
        (ArangoPlantDiaryRepository, lambda r: r.get_by_run_window("r1", tenant_key="")),
        (ArangoPostHarvestRepository, lambda r: r.list_batches_window(tenant_key="")),
        (ArangoTaskRepository, lambda r: r.get_tasks_window(tenant_key="")),
        (ArangoPlantingRunRepository, lambda r: r.get_runs_window(tenant_key="")),
        (ArangoImportJobRepository, lambda r: r.list_all_window(tenant_key="")),
    ],
    ids=["diary-plant", "diary-run", "post-harvest", "tasks", "planting-runs", "import-jobs"],
)
def test_every_tenant_scoped_window_refuses_the_empty_tenant(repo: Any, read: Callable[[Any], Any]) -> None:
    # The window is a new read path: it must refuse the empty-tenant sentinel
    # exactly like its counted sibling, not read across every tenant.
    db = _RecordingDb()
    with pytest.raises(ValueError, match="tenant"):
        read(repo(db))
    assert db.executed == []
