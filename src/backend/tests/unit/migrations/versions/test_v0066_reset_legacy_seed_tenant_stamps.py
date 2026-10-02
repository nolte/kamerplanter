"""v0066 (#1805): which stamp counts as proven — pure decision, no database.

The collection queries and the erasure that follows are measured against a real
server in ``tests/integration/test_v0066_reset_legacy_seed_tenant_stamps.py``.
"""

from __future__ import annotations

from app.migrations.versions.v0066_reset_legacy_seed_tenant_stamps import (
    ResetLegacySeedTenantStampsMigration,
    seed_identities,
)

_proven = ResetLegacySeedTenantStampsMigration._proven_stamps
EXPECTED = 10


def proven(rows):
    return _proven(rows, EXPECTED)


def _row(tenant_key: str, parent: str | None = None, collection: str = "fertilizers") -> dict[str, str]:
    row = {"collection": collection, "key": "k", "tenant_key": tenant_key}
    if parent is not None:
        row["parent_tenant_key"] = parent
    return row


def test_a_key_on_most_seed_named_rows_is_the_stamp() -> None:
    assert proven([_row("d")] * 6 + [_row("other"), _row("")]) == {"d"}


def test_a_lone_foreign_row_on_a_clean_volume_is_not_a_stamp() -> None:
    assert proven([_row("other"), _row(""), _row("")]) == set()


def test_plans_never_count_toward_the_majority_because_a_tenant_can_repeat_a_name() -> None:
    assert proven([_row("other", collection="nutrient_plans")] * 50) == set()


def test_a_child_stamped_under_a_global_parent_proves_its_key() -> None:
    assert proven([_row("d", parent="", collection="nutrient_plan_phase_entries"), _row("other")]) == {"d"}


def test_a_child_under_its_tenants_own_parent_proves_nothing() -> None:
    assert proven([_row("other", parent="other", collection="task_templates"), _row(""), _row("")]) == set()


def test_no_seed_named_rows_proves_nothing() -> None:
    assert proven([]) == set()


def test_the_identities_are_read_off_the_shipped_seed_files() -> None:
    ids = seed_identities()

    assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in ids.fertilizers | ids.task_templates)
    assert {wf for wf, _ in ids.task_templates} <= ids.workflow_templates
