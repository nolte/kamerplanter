"""v0066 (#1805): which stamp counts as proven — pure decision, no database.

The collection queries and the erasure that follows are measured against a real
server in ``tests/integration/test_v0066_reset_legacy_seed_tenant_stamps.py``.
"""

from __future__ import annotations

from app.migrations.versions.v0066_reset_legacy_seed_tenant_stamps import (
    ResetLegacySeedTenantStampsMigration,
    seed_identities,
)

proven = ResetLegacySeedTenantStampsMigration._proven_stamps


def _row(tenant_key: str, parent: str | None = None) -> dict[str, str]:
    row = {"collection": "c", "key": "k", "tenant_key": tenant_key}
    if parent is not None:
        row["parent_tenant_key"] = parent
    return row


def test_a_key_on_most_seed_named_rows_is_the_stamp() -> None:
    assert proven([_row("d"), _row("d"), _row("d"), _row("other"), _row("")]) == {"d"}


def test_a_lone_foreign_row_on_a_clean_volume_is_not_a_stamp() -> None:
    assert proven([_row("other"), _row(""), _row("")]) == set()


def test_a_child_stamped_under_a_global_parent_proves_its_key() -> None:
    assert proven([_row("d", parent=""), _row(""), _row(""), _row("other")]) == {"d"}


def test_a_child_under_its_tenants_own_parent_proves_nothing() -> None:
    assert proven([_row("other", parent="other"), _row(""), _row("")]) == set()


def test_no_seed_named_rows_proves_nothing() -> None:
    assert proven([]) == set()


def test_the_identities_are_read_off_the_shipped_seed_files() -> None:
    ids = seed_identities()

    assert all(isinstance(pair, tuple) and len(pair) == 2 for pair in ids.fertilizers | ids.task_templates)
    assert {wf for wf, _ in ids.task_templates} <= ids.workflow_templates
