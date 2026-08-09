"""``find_task_by_external_ref`` — the FreeStyle idempotency lookup (#1082).

Exercised against the replaying database double, which applies whatever predicates
the query text *actually* carries (see ``tests/support/tenant_replay.py``). That
is what makes the tenant- and source-scoping assertions here red on a query that
drops either predicate and green only on the fixed one — an ordinary stub would
agree with the implementation whether or not the filter is present.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.common.enums import TaskOrigin
from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.models.task import Task
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase, apply_predicates

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"
SOURCE = "goose/leaf-analysis"
OTHER_SOURCE = "goose/pest-analysis"
EXTERNAL_REF = "run-2026-08-09/leaf-42"

#: The marker substring the lookup query is routed on.
_LOOKUP_MARKER = "doc.external_ref == @external_ref"


def _task_doc(key: str, *, tenant_key: str, source: str, external_ref: str) -> dict[str, Any]:
    task = Task(
        key=key,
        name="Analyse-Befund pruefen",
        tenant_key=tenant_key,
        origin=TaskOrigin.PIPELINE,
        source=source,
        external_ref=external_ref,
    )
    doc = task.model_dump(by_alias=True, exclude_none=True, mode="json")
    doc["_key"] = key
    doc["_id"] = f"{col.TASKS}/{key}"
    doc["created_at"] = "2026-08-09T00:00:00+00:00"
    return doc


def _repo(rows: list[dict[str, Any]]) -> ArangoTaskRepository:
    def _lookup(query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        return apply_predicates(rows, query, bind_vars)[:1]

    aql = ReplayingAql().route(_LOOKUP_MARKER, _lookup)
    return ArangoTaskRepository(ReplayingDatabase(aql, {}))


class TestFindTaskByExternalRef:
    def test_returns_the_matching_task_in_the_callers_tenant(self) -> None:
        repo = _repo([_task_doc("t-a", tenant_key=TENANT_A, source=SOURCE, external_ref=EXTERNAL_REF)])

        found = repo.find_task_by_external_ref(tenant_key=TENANT_A, source=SOURCE, external_ref=EXTERNAL_REF)

        assert found is not None
        assert found.key == "t-a"

    def test_a_foreign_tenants_task_is_not_found(self) -> None:
        """Tenant isolation (#1082 AC-6): the same external_ref in tenant B is invisible to tenant A.

        Red-first: drop ``FILTER doc.tenant_key == @tenant_key`` from the repository
        query and the replaying double hands tenant B's row straight back, so this
        would return it — turning the lookup into a cross-tenant existence oracle.
        """
        repo = _repo([_task_doc("t-b", tenant_key=TENANT_B, source=SOURCE, external_ref=EXTERNAL_REF)])

        found = repo.find_task_by_external_ref(tenant_key=TENANT_A, source=SOURCE, external_ref=EXTERNAL_REF)

        assert found is None

    def test_a_different_producer_source_is_not_found(self) -> None:
        """Two producers sharing an external_ref string stay in separate namespaces.

        Red-first: drop ``FILTER doc.source == @source`` and the row emitted by
        ``OTHER_SOURCE`` would collide with this producer's lookup.
        """
        repo = _repo([_task_doc("t-o", tenant_key=TENANT_A, source=OTHER_SOURCE, external_ref=EXTERNAL_REF)])

        found = repo.find_task_by_external_ref(tenant_key=TENANT_A, source=SOURCE, external_ref=EXTERNAL_REF)

        assert found is None

    def test_empty_tenant_key_is_rejected(self) -> None:
        repo = _repo([])
        with pytest.raises(ValueError, match="tenant"):
            repo.find_task_by_external_ref(tenant_key="", source=SOURCE, external_ref=EXTERNAL_REF)

    def test_missing_source_or_ref_never_dedups(self) -> None:
        repo = _repo([_task_doc("t-a", tenant_key=TENANT_A, source=SOURCE, external_ref=EXTERNAL_REF)])

        assert repo.find_task_by_external_ref(tenant_key=TENANT_A, source="", external_ref=EXTERNAL_REF) is None
        assert repo.find_task_by_external_ref(tenant_key=TENANT_A, source=SOURCE, external_ref="") is None
