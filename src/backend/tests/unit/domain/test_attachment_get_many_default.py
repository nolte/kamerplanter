"""#2715 review G — the interface default of ``get_many`` answers like ``get`` (and like the ArangoDB override).

The override is measured against ArangoDB in ``tests/integration/test_attachment_get_many.py``; this pins the
default every fake inherits: absent and foreign keys are missing from the map, repeats are read once, an empty
tenant reads nothing.
"""

from __future__ import annotations

from app.domain.interfaces.attachment_repository import IAttachmentRepository


class _Rows:
    def __init__(self) -> None:
        self.rows = {"p1": "t-a", "p2": "t-a", "foreign": "t-b"}
        self.reads: list[str] = []

    def get(self, key: str, tenant_key: str) -> str | None:
        self.reads.append(key)
        return key if self.rows.get(key) == tenant_key and tenant_key else None


def test_the_default_answers_the_tenants_records_once_each() -> None:
    rows = _Rows()

    found = IAttachmentRepository.get_many(rows, ["p2", "foreign", "gone", "p1", "p2"], tenant_key="t-a")  # type: ignore[arg-type]

    assert found == {"p2": "p2", "p1": "p1"}
    assert rows.reads == ["p2", "foreign", "gone", "p1"]


def test_an_empty_tenant_reads_nothing() -> None:
    assert IAttachmentRepository.get_many(_Rows(), ["p1"], tenant_key="") == {}  # type: ignore[arg-type]
