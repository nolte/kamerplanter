"""MT-032 (#2128) — no task under ``app/tasks`` reads every tenant's rows into the worker.

The defect class: a beat called ``get_all_pages(repo, all_tenants=True)`` (or
``repo.get_all(..., all_tenants=True)``), held every tenant's rows in one list and
dropped a closed tenant's rows in Python. The worker's memory grew with the whole
installation, and the rows it threw away were loaded first. Measured on develop
before this change: 8 such reads in 6 modules (actuators 2, tanks 2, plants 4).

They now walk the tenants they may touch: ``ITenantRepository.keys_in_status`` names
the tenants, ``BaseArangoRepository.iter_for_tenants`` reads exactly those tenants'
rows, filtered in AQL, one keyset page at a time.

The predicate: any call in ``app/tasks/*.py`` carrying the keyword ``all_tenants``
with a value other than the literal ``False``. **Spellings it cannot see:** a task
that reaches an all-tenant read through a service or repository method in another
module (``get_all_profiles`` in the care beat, the raw AQL of ``check_runoff_trends``,
``ingest_ha_readings``), and a keyword passed through ``**kwargs``.
"""

from __future__ import annotations

import ast
from pathlib import Path

TASKS = Path(__file__).resolve().parents[3] / "app" / "tasks"


def _all_tenant_reads(source: str) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg != "all_tenants":
                continue
            if isinstance(keyword.value, ast.Constant) and keyword.value.value is False:
                continue
            lines.append(node.lineno)
    return lines


def test_no_task_reads_every_tenants_rows() -> None:
    hits = {
        f"{path.name}:{line}"
        for path in sorted(TASKS.glob("*.py"))
        for line in _all_tenant_reads(path.read_text(encoding="utf-8"))
    }

    assert sorted(hits) == [], "walk the tenants (keys_in_status + iter_for_tenants) instead (MT-032, #2128)"


def test_the_predicate_tells_an_all_tenant_read_from_a_tenant_walk() -> None:
    """Negative control: the predicate sees both spellings of the old read and passes the new one."""
    assert _all_tenant_reads("rows = get_all_pages(repo, all_tenants=True)\n") == [1]
    assert _all_tenant_reads("page, total = repo.get_all(offset=0, limit=1000, all_tenants=flag)\n") == [1]
    assert _all_tenant_reads("rows = repo.get_all(0, 50, tenant_key=t, all_tenants=False)\n") == []
    assert _all_tenant_reads("rows = repo.iter_for_tenants(tenants, filters=[('removed_on', '==', None)])\n") == []
