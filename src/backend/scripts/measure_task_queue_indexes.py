#!/usr/bin/env python
"""Measure candidate ``tenant_key`` indexes for the task queue on a seeded volume (#1534).

**Writes, but only into a database it creates itself.** This is a measurement
harness, not an audit: it creates a throwaway database (the name must start with
``perf_``), bootstraps it with the production ``ensure_collections`` — so the
``tasks`` collection carries exactly the indexes and computed value a fresh
installation has —, seeds a synthetic multi-tenant volume, measures, and drops
the database again unless ``--keep`` is given. It refuses to touch a database
that already exists unless ``--recreate`` is passed. Point it at a disposable
ArangoDB container, never at an installation.

## What it measures

The queries are **not spelled out here**. Each one is produced by calling the
real ``ArangoTaskRepository`` method against the seeded database through a recorder
that captures the AQL and bind variables the builder sent, so a later change to
``_tasks_selection`` or ``get_overdue_tasks`` is measured as it is, rather than as
this script once remembered it.

For every captured query, every index variant and two tenants (the large one and
a median-sized small one) it records:

* the ``explain`` plan — which index the optimizer picked (if any), whether an
  ``EnumerateCollectionNode`` or a ``SortNode`` remains, and the estimated cost;
* the scan statistics of one execution (``scannedIndex``, ``scannedFull``,
  ``filtered``);
* the median server-side execution time and client wall time over ``--runs``
  warm runs (two discarded warm-up runs first).

Index variants: ``baseline`` (bootstrap only), ``+[tenant_key,status]`` and
``+[tenant_key,status,due_date]`` (each compound measured alone). For each
variant it also measures the write cost: one AQL bulk insert of
``--write-batch`` documents and ``--write-singles`` single-document inserts
(the ``create_task`` path), both reverted after every run.

## Usage

    ARANGO_PERF_PASSWORD=... python scripts/measure_task_queue_indexes.py \\
        --url http://127.0.0.1:18634 --json /tmp/out.json

The volume is deterministic for a given ``--seed`` and tenant parameters; the
due dates are relative to the moment of the run, because ``get_overdue_tasks``
compares against ``now``.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from collections.abc import Callable, Iterator, MutableMapping
from datetime import UTC, datetime, timedelta
from typing import Any

from arango.client import ArangoClient
from arango.cursor import Cursor
from arango.database import StandardDatabase

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.common.enums import TaskCategory, TaskOrigin, TaskStatus  # noqa: E402
from app.data_access.arango import collections as col  # noqa: E402
from app.data_access.arango.task_repository import ArangoTaskRepository  # noqa: E402
from app.domain.models.task import Task  # noqa: E402
from app.domain.services.task_service import QUEUE_LIMIT  # noqa: E402

#: Weighted value distributions of the synthetic volume. Pending is the majority
#: on purpose: it is the status the queue filters on, so a pending-heavy volume is
#: the least favourable case for the single-field ``status`` index.
STATUS_WEIGHTS: dict[str, int] = {
    TaskStatus.PENDING.value: 55,
    TaskStatus.COMPLETED.value: 30,
    TaskStatus.SKIPPED.value: 8,
    TaskStatus.IN_PROGRESS.value: 4,
    TaskStatus.DORMANT.value: 2,
    TaskStatus.FAILED.value: 1,
}
CATEGORY_WEIGHTS: dict[str, int] = {
    TaskCategory.CARE_REMINDER.value: 40,
    TaskCategory.FEEDING.value: 15,
    TaskCategory.MAINTENANCE.value: 15,
    TaskCategory.OBSERVATION.value: 10,
    TaskCategory.IPM.value: 5,
    TaskCategory.TRAINING.value: 5,
    TaskCategory.HARVEST.value: 5,
    TaskCategory.PRUNING.value: 5,
}
ORIGIN_WEIGHTS: dict[str, int] = {
    TaskOrigin.USER.value: 65,
    TaskOrigin.SYSTEM.value: 30,
    TaskOrigin.PIPELINE.value: 5,
}
ENTITY_TYPE_WEIGHTS: dict[str | None, int] = {
    "plant_instance": 60,
    "planting_run": 20,
    "location": 10,
    None: 10,
}

#: Share of plant instances seeded as removed, so the queue's orphan guard
#: (``LET _plant = DOCUMENT(...)``) has rows to drop.
REMOVED_PLANT_SHARE = 0.03

LARGE_TENANT = "tenant-large"
WRITE_BENCH_TENANT = "tenant-writebench"

#: The compound candidates under measurement. Never created by this script
#: outside its own throwaway database.
VARIANTS: dict[str, list[str] | None] = {
    "baseline": None,
    "tenant_status": ["tenant_key", "status"],
    "tenant_status_due": ["tenant_key", "status", "due_date"],
}


class _RecordingAQL:
    """Forward ``execute`` to the real AQL API and keep what was sent."""

    def __init__(self, aql: Any) -> None:
        self._aql = aql
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, query: str, bind_vars: MutableMapping[str, Any] | None = None, **kwargs: Any) -> Any:
        self.calls.append((query, dict(bind_vars or {})))
        return self._aql.execute(query, bind_vars=bind_vars, **kwargs)


class _RecordingDB:
    """A ``StandardDatabase`` stand-in whose ``aql`` records; everything else is the real database."""

    def __init__(self, db: StandardDatabase) -> None:
        self._real = db
        self.aql = _RecordingAQL(db.aql)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)


def _run(db: StandardDatabase, query: str, bind_vars: dict[str, Any] | None = None, **kwargs: Any) -> Cursor:
    """``db.aql.execute`` narrowed to the synchronous cursor this script always gets."""
    cursor = db.aql.execute(query, bind_vars=bind_vars, **kwargs)
    if not isinstance(cursor, Cursor):
        raise TypeError(f"expected a Cursor, got {type(cursor).__name__}")
    return cursor


def _indexes(db: StandardDatabase, name: str) -> list[dict[str, Any]]:
    found = db.collection(name).indexes()
    if not isinstance(found, list):
        raise TypeError(f"expected an index list, got {type(found).__name__}")
    return found


def _weighted[T](rng: random.Random, weights: dict[T, int]) -> T:
    return rng.choices(list(weights), weights=list(weights.values()), k=1)[0]


def _tenant_sizes(args: argparse.Namespace, rng: random.Random) -> dict[str, int]:
    sizes = {LARGE_TENANT: args.large_size}
    for i in range(args.medium_tenants):
        sizes[f"tenant-medium-{i:03d}"] = args.medium_size
    for i in range(args.small_tenants):
        sizes[f"tenant-small-{i:05d}"] = rng.randint(args.small_min, args.small_max)
    return sizes


def _task_docs(
    tenant: str,
    count: int,
    plant_keys: list[str],
    rng: random.Random,
    now: datetime,
    serialize: Callable[[Task], dict[str, Any]],
) -> Iterator[dict[str, Any]]:
    for i in range(count):
        status = _weighted(rng, STATUS_WEIGHTS)
        category = _weighted(rng, CATEGORY_WEIGHTS)
        entity_type = _weighted(rng, ENTITY_TYPE_WEIGHTS)
        if status in (TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value, TaskStatus.DORMANT.value):
            due = now + timedelta(days=rng.uniform(-45, 45))
        else:
            due = now - timedelta(days=rng.uniform(0, 365))
        entity_key: str | None = None
        if entity_type == "plant_instance":
            entity_key = rng.choice(plant_keys)
        elif entity_type is not None:
            entity_key = f"{entity_type}-{tenant}-{rng.randint(0, 20)}"
        # Care-task names carry the reminder type after "— "; a per-task suffix keeps
        # the open-care-task dedup index (unique, sparse) satisfiable for the seed.
        name = f"Task {i} — reminder-{i}" if category == TaskCategory.CARE_REMINDER.value else f"Task {i}"
        task = Task(
            tenant_key=tenant,
            name=name,
            category=TaskCategory(category),
            origin=TaskOrigin(_weighted(rng, ORIGIN_WEIGHTS)),
            entity_type=entity_type,
            entity_key=entity_key,
            due_date=due.replace(microsecond=0),
            status=TaskStatus(status),
        )
        doc = serialize(task)
        doc["created_at"] = doc["updated_at"] = now.isoformat()
        yield doc


def _batched(items: Iterator[dict[str, Any]], size: int) -> Iterator[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def seed(db: StandardDatabase, args: argparse.Namespace, now: datetime) -> dict[str, Any]:
    rng = random.Random(args.seed)
    sizes = _tenant_sizes(args, rng)
    repo = ArangoTaskRepository(db)
    tasks_col = db.collection(col.TASKS)
    plants_col = db.collection(col.PLANT_INSTANCES)
    started = time.perf_counter()
    for tenant, count in sizes.items():
        plant_keys = [f"{tenant}-p{j}" for j in range(max(5, count // 20))]
        plants = [
            {
                "_key": key,
                "tenant_key": tenant,
                "instance_id": key,
                "removed_on": now.isoformat() if rng.random() < REMOVED_PLANT_SHARE else None,
            }
            for key in plant_keys
        ]
        plants_col.import_bulk(plants, on_duplicate="error", halt_on_error=True)
        for batch in _batched(_task_docs(tenant, count, plant_keys, rng, now, repo._to_doc), 5000):
            tasks_col.import_bulk(batch, on_duplicate="error", halt_on_error=True)
    small = sorted(v for k, v in sizes.items() if k.startswith("tenant-small-"))
    return {
        "seed": args.seed,
        "tenants": len(sizes),
        "tasks_total": tasks_col.count(),
        "plant_instances_total": plants_col.count(),
        "large_tenant_tasks": sizes[LARGE_TENANT],
        "medium_tenants": args.medium_tenants,
        "medium_size": args.medium_size,
        "small_tenants": args.small_tenants,
        "small_range": [args.small_min, args.small_max],
        "small_median": statistics.median(small) if small else None,
        "seed_seconds": round(time.perf_counter() - started, 1),
        "status_counts": {
            row["s"]: row["n"]
            for row in _run(
                db,
                f"FOR d IN {col.TASKS} COLLECT s = d.status WITH COUNT INTO n RETURN {{s, n}}",
            )
        },
    }


def _median_small_tenant(db: StandardDatabase) -> tuple[str, int]:
    rows = list(
        _run(
            db,
            f"FOR d IN {col.TASKS} FILTER STARTS_WITH(d.tenant_key, 'tenant-small-') "
            "COLLECT t = d.tenant_key WITH COUNT INTO n SORT n, t RETURN [t, n]",
        )
    )
    tenant, count = rows[len(rows) // 2]
    return str(tenant), int(count)


def capture_shapes(db: StandardDatabase, tenant: str) -> dict[str, tuple[str, dict[str, Any]]]:
    """Run the real repository methods once and keep the AQL each one sent."""
    recorder = _RecordingDB(db)
    repo = ArangoTaskRepository(db)
    repo._db = recorder  # type: ignore[assignment]  # recorder proxies the real database
    calls = recorder.aql.calls
    shapes: dict[str, tuple[str, dict[str, Any]]] = {}

    def grab(names: list[str], call: Callable[[], object]) -> None:
        before = len(calls)
        call()
        new = calls[before:]
        if len(new) != len(names):
            raise RuntimeError(f"expected {len(names)} queries for {names}, captured {len(new)}")
        shapes.update(zip(names, new, strict=True))

    care = TaskCategory.CARE_REMINDER.value
    machine = [TaskOrigin.SYSTEM.value, TaskOrigin.PIPELINE.value]
    grab(["queue.window", "queue.count"], lambda: repo.get_pending_tasks(0, QUEUE_LIMIT, tenant_key=tenant))
    grab(
        ["queue_category.window", "queue_category.count"],
        lambda: repo.get_pending_tasks(0, QUEUE_LIMIT, tenant_key=tenant, category=care),
    )
    grab(
        ["queue_category_origin.window", "queue_category_origin.count"],
        lambda: repo.get_pending_tasks(0, QUEUE_LIMIT, tenant_key=tenant, category=care, origins=machine),
    )
    grab(["overdue"], lambda: repo.get_overdue_tasks(tenant_key=tenant))
    # ``get_all_tasks`` sends its window (same AQL as ``get_tasks_window``) and then the count.
    grab(["list_all.window", "list_all.count"], lambda: repo.get_all_tasks(0, 50, None, tenant_key=tenant))
    grab(
        ["list_completed.window"],
        lambda: repo.get_tasks_window(0, 50, {"status": TaskStatus.COMPLETED.value}, tenant_key=tenant),
    )
    # Not queries the code sends: the queue window with the sort on the raw field
    # (with and without the ``_key`` tie-breaker), to show whether a trailing
    # ``due_date`` could serve the sort at all if the query were rewritten.
    window_q, window_vars = shapes["queue.window"]
    raw_sort = window_q.replace("SORT DATE_TIMESTAMP(doc.due_date) ASC", "SORT doc.due_date ASC")
    shapes["HYPOTHETICAL queue.window raw-sort"] = (raw_sort, window_vars)
    shapes["HYPOTHETICAL queue.window raw-sort no-tiebreak"] = (raw_sort.replace(", doc._key ASC", ""), window_vars)
    # ...and without the orphan guard (``LET _plant = DOCUMENT(...) FILTER ...``) that
    # sits between the index scan and the ``SORT``, to separate its cost from the index's.
    no_guard = window_q[: window_q.index(" LET _plant")] + window_q[window_q.index(" SORT ") :]
    shapes["HYPOTHETICAL queue.window no-orphan-guard"] = (no_guard, window_vars)
    shapes["HYPOTHETICAL queue.window no-orphan-guard raw-sort no-tiebreak"] = (
        no_guard.replace("SORT DATE_TIMESTAMP(doc.due_date) ASC, doc._key ASC", "SORT doc.due_date ASC"),
        window_vars,
    )
    return shapes


def _with_tenant(bind_vars: dict[str, Any], tenant: str) -> dict[str, Any]:
    return {**bind_vars, "tenant_key": tenant}


def explain(db: StandardDatabase, query: str, bind_vars: dict[str, Any]) -> dict[str, Any]:
    result = db.aql.explain(query, bind_vars=bind_vars)
    if isinstance(result, list):
        result = result[0]
    if not isinstance(result, dict):
        raise TypeError(f"unexpected explain result {type(result).__name__}")
    plan: dict[str, Any] = result
    nodes = plan.get("nodes", [])
    # One IndexNode can list the same index more than once (one entry per condition
    # branch); the plan uses it once, so it is reported once.
    indexes: list[dict[str, Any]] = []
    for node in nodes:
        if node.get("type") != "IndexNode":
            continue
        for idx in node.get("indexes", []):
            entry = {"fields": idx.get("fields"), "type": idx.get("type"), "name": idx.get("name")}
            if entry not in indexes:
                indexes.append(entry)
    return {
        "nodes": [node.get("type") for node in nodes],
        "indexes": indexes,
        "index_nodes": sum(1 for node in nodes if node.get("type") == "IndexNode"),
        "full_scan": any(node.get("type") == "EnumerateCollectionNode" for node in nodes),
        "sort_node": any(node.get("type") == "SortNode" for node in nodes),
        "estimated_cost": round(float(plan.get("estimatedCost", 0.0)), 1),
        "rules": plan.get("rules", []),
    }


def time_query(db: StandardDatabase, query: str, bind_vars: dict[str, Any], runs: int) -> dict[str, Any]:
    server: list[float] = []
    wall: list[float] = []
    stats: dict[str, Any] = {}
    rows = 0
    for attempt in range(runs + 2):
        started = time.perf_counter()
        cursor = _run(db, query, bind_vars, batch_size=1000)
        rows = len(list(cursor))
        elapsed = time.perf_counter() - started
        stats = cursor.statistics() or {}
        if attempt < 2:
            continue  # warm-up
        wall.append(elapsed * 1000)
        server.append(float(stats.get("execution_time", 0.0)) * 1000)
    return {
        "rows": rows,
        "server_ms": round(statistics.median(server), 2),
        "wall_ms": round(statistics.median(wall), 2),
        "scanned_index": stats.get("scanned_index"),
        "scanned_full": stats.get("scanned_full"),
        "filtered": stats.get("filtered"),
    }


def measure_writes(db: StandardDatabase, args: argparse.Namespace, now: datetime) -> dict[str, Any]:
    rng = random.Random(args.seed + 1)
    repo = ArangoTaskRepository(db)
    tasks_col = db.collection(col.TASKS)
    plant_keys = [f"{WRITE_BENCH_TENANT}-p{j}" for j in range(50)]
    docs = list(_task_docs(WRITE_BENCH_TENANT, args.write_batch, plant_keys, rng, now, repo._to_doc))
    cleanup = f"FOR d IN {col.TASKS} FILTER d.tenant_key == @t REMOVE d IN {col.TASKS}"
    bulk_ms: list[float] = []
    for _ in range(args.write_runs):
        started = time.perf_counter()
        _run(db, f"FOR d IN @docs INSERT d INTO {col.TASKS}", bind_vars={"docs": docs})
        bulk_ms.append((time.perf_counter() - started) * 1000)
        _run(db, cleanup, {"t": WRITE_BENCH_TENANT})
    single_ms: list[float] = []
    for doc in docs[: args.write_singles]:
        started = time.perf_counter()
        tasks_col.insert(doc)
        single_ms.append((time.perf_counter() - started) * 1000)
    _run(db, cleanup, {"t": WRITE_BENCH_TENANT})
    bulk_median = statistics.median(bulk_ms)
    return {
        "bulk_docs": args.write_batch,
        "bulk_median_ms": round(bulk_median, 1),
        "bulk_docs_per_s": round(args.write_batch / (bulk_median / 1000)),
        "single_inserts": len(single_ms),
        "single_median_ms": round(statistics.median(single_ms), 3),
        "single_p95_ms": round(statistics.quantiles(single_ms, n=20)[-1], 3),
    }


def _apply_variant(db: StandardDatabase, fields: list[str] | None) -> float | None:
    tasks_col = db.collection(col.TASKS)
    for idx in _indexes(db, col.TASKS):
        if idx.get("fields") and idx["fields"][0] == "tenant_key":
            tasks_col.delete_index(idx["id"])
    if fields is None:
        return None
    started = time.perf_counter()
    tasks_col.add_index({"type": "persistent", "fields": fields, "unique": False})
    return round(time.perf_counter() - started, 2)


def _render(result: dict[str, Any]) -> str:
    lines = [
        "| shape | tenant | variant | index used | full scan | SortNode | scannedIndex | scannedFull | "
        "filtered | rows | server ms (median) | wall ms (median) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in result["reads"]:
        used = "; ".join(str(i["fields"]) for i in row["plan"]["indexes"]) or "-"
        lines.append(
            f"| {row['shape']} | {row['tenant_label']} | {row['variant']} | {used} | "
            f"{'yes' if row['plan']['full_scan'] else 'no'} | {'yes' if row['plan']['sort_node'] else 'no'} | "
            f"{row['timing']['scanned_index']} | {row['timing']['scanned_full']} | {row['timing']['filtered']} | "
            f"{row['timing']['rows']} | {row['timing']['server_ms']} | {row['timing']['wall_ms']} |"
        )
    lines += [
        "",
        "| variant | index build s | bulk insert docs/s | bulk median ms | single insert median ms | p95 ms |",
        "|---|---|---|---|---|---|",
    ]
    for variant, w in result["writes"].items():
        lines.append(
            f"| {variant} | {result['index_build_s'].get(variant)} | {w['bulk_docs_per_s']} | {w['bulk_median_ms']} | "
            f"{w['single_median_ms']} | {w['single_p95_ms']} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--url", required=True, help="ArangoDB endpoint of a DISPOSABLE server")
    parser.add_argument("--user", default="root")
    parser.add_argument("--password-env", default="ARANGO_PERF_PASSWORD", help="env var holding the password")
    parser.add_argument("--database", default="perf_task_queue")
    parser.add_argument("--recreate", action="store_true", help="drop the database first if it exists")
    parser.add_argument("--keep", action="store_true", help="keep the database after measuring")
    parser.add_argument("--seed", type=int, default=1534)
    parser.add_argument("--large-size", type=int, default=20_000)
    parser.add_argument("--medium-tenants", type=int, default=5)
    parser.add_argument("--medium-size", type=int, default=3_000)
    parser.add_argument("--small-tenants", type=int, default=294)
    parser.add_argument("--small-min", type=int, default=50)
    parser.add_argument("--small-max", type=int, default=500)
    parser.add_argument("--runs", type=int, default=9)
    parser.add_argument("--write-batch", type=int, default=10_000)
    parser.add_argument("--write-runs", type=int, default=5)
    parser.add_argument("--write-singles", type=int, default=1_000)
    parser.add_argument("--json", help="write the full result as JSON to this path")
    args = parser.parse_args()

    if not args.database.startswith("perf_"):
        print("refusing: --database must start with 'perf_' (this script seeds and drops it)", file=sys.stderr)
        return 2
    password = os.environ.get(args.password_env)
    if password is None:
        print(f"refusing: ${args.password_env} is not set", file=sys.stderr)
        return 2

    client = ArangoClient(hosts=args.url, request_timeout=600)
    sys_db = client.db("_system", username=args.user, password=password)
    if sys_db.has_database(args.database):
        if not args.recreate:
            print(f"refusing: database {args.database!r} exists (pass --recreate)", file=sys.stderr)
            return 2
        sys_db.delete_database(args.database)
    sys_db.create_database(args.database)
    db = client.db(args.database, username=args.user, password=password)
    try:
        col.ensure_collections(db)
        now = datetime.now(UTC)
        result: dict[str, Any] = {
            "server_version": sys_db.version(),
            "bootstrap_task_indexes": [
                {k: idx.get(k) for k in ("type", "fields", "unique", "sparse")} for idx in _indexes(db, col.TASKS)
            ],
            "seed": seed(db, args, now),
        }
        small_tenant, small_count = _median_small_tenant(db)
        tenants = {"large": (LARGE_TENANT, args.large_size), "small": (small_tenant, small_count)}
        result["tenants"] = {label: {"key": t, "tasks": n} for label, (t, n) in tenants.items()}
        shapes = capture_shapes(db, LARGE_TENANT)
        result["queries"] = {name: {"aql": q, "bind_vars": bv} for name, (q, bv) in shapes.items()}
        result["reads"] = []
        result["writes"] = {}
        result["index_build_s"] = {}
        for variant, fields in VARIANTS.items():
            result["index_build_s"][variant] = _apply_variant(db, fields)
            for name, (query, bind_vars) in shapes.items():
                for label, (tenant, _) in tenants.items():
                    bv = _with_tenant(bind_vars, tenant)
                    result["reads"].append(
                        {
                            "shape": name,
                            "tenant_label": label,
                            "variant": variant,
                            "plan": explain(db, query, bv),
                            "timing": time_query(db, query, bv, args.runs),
                        }
                    )
            result["writes"][variant] = measure_writes(db, args, now)
        print(json.dumps({k: result[k] for k in ("server_version", "seed", "tenants")}, indent=2, default=str))
        for name, (query, bind_vars) in shapes.items():
            print(f"\n[{name}]\n{query}\nbind_vars={json.dumps(bind_vars, default=str)}")
        print()
        print(_render(result))
        if args.json:
            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump(result, fh, indent=2, default=str)
    finally:
        if not args.keep:
            sys_db.delete_database(args.database)
    return 0


if __name__ == "__main__":
    sys.exit(main())
