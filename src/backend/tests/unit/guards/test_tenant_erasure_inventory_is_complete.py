"""#1769 — every collection is classified for tenant deletion, derived, not remembered.

Tenant deletion removed four hand-listed collections and left every other
tenant-scoped collection behind. The repair is a declared inventory
(:attr:`TenantErasureEngine.INVENTORY`), and this guard is what keeps it
complete when the next collection arrives. It anchors on three sources nobody
edits to satisfy a privacy list:

* ``collections.py`` — **every** document collection must be classified exactly
  once: an inventory entry (delete / pseudonymize / retain) or a reason in
  :attr:`TenantErasureEngine.NOT_TENANT_SCOPED`. A new collection fails here
  until someone decides. This is what catches a raw-written collection with a
  ``tenant_key`` and no model (``ha_publish_settings``), which a model-anchored
  rule cannot see;
* the models — every collection the #1708 derivation finds tenant-bearing
  (``build_inventory`` in ``test_tenant_scoped_reads_are_derived.py``: a model
  declaring ``tenant_key``, a hybrid catalogue, a declared parent chain) must be
  an *inventory entry*, never "not tenant-scoped", and must be reached through
  every parent chain that derivation declares;
* the legacy backfill (``migrations/backfill_tenant_key.py``) — every collection
  it stamped with a tenant key is either inventoried or declared with the reason
  that its stamp is not ownership.

Edge collections are not classified: the executor sweeps every edge collection
the database has (``_from``/``_to`` of a deleted row), so a new edge collection
is reached without an entry. What the executor reports as
``undeclared:<collection>`` at run time is the backstop for a collection that
exists in a database but not in ``collections.py``.

Spellings this guard does not see: a tenant's rows in a collection outside
ArangoDB (TimescaleDB sensor data, the object store — the latter purged by
prefix), and a document that references a tenant row through a field no parent
chain declares (``workflow_phases`` is declared by hand here, beyond the
derivation). The integration reach test (``test_tenant_erasure_reach.py``)
measures the run itself.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.data_access.arango import collections as col
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.migrations import backfill_tenant_key
from tests.support.execution_guards import find_project_root
from tests.unit.guards.test_tenant_scoped_reads_are_derived import PARENT_CHAINS, build_inventory

_APP = find_project_root(Path(__file__)) / "app"


def classification_findings(
    document_collections: list[str],
    inventory: dict[str, str],
    not_tenant_scoped: dict[str, str],
    tenant_bearing: set[str],
) -> list[str]:
    """The one detector: every way a collection can be mis-classified for tenant deletion.

    ``inventory`` maps collection -> action; ``tenant_bearing`` is the derived set.
    Used by the tree check and the self-test alike.
    """
    findings: list[str] = []
    declared = set(document_collections)
    classified = set(inventory) | set(not_tenant_scoped) | {TenantErasureEngine.TENANT_COLLECTION}
    for name in sorted(declared - classified):
        findings.append(f"{name}: not classified for tenant deletion (inventory entry or NOT_TENANT_SCOPED reason)")
    for name in sorted(classified - declared):
        findings.append(f"{name}: classified but not a document collection in collections.py")
    for name in sorted(set(inventory) & set(not_tenant_scoped)):
        findings.append(f"{name}: both inventoried and declared not tenant-scoped")
    for name in sorted(tenant_bearing - set(inventory)):
        findings.append(f"{name}: tenant-bearing (derived from the models) but not in the tenant-erasure inventory")
    for name, reason in sorted(not_tenant_scoped.items()):
        if not reason.strip():
            findings.append(f"{name}: declared not tenant-scoped without a reason")
    return findings


def _inventory_actions() -> dict[str, str]:
    return {entry.collection: entry.action for entry in TenantErasureEngine.INVENTORY}


@pytest.fixture(scope="module")
def derived():
    return build_inventory(_APP)


class TestEveryCollectionIsClassified:
    def test_the_tree_is_clean(self, derived) -> None:
        findings = classification_findings(
            list(col.DOCUMENT_COLLECTIONS),
            _inventory_actions(),
            TenantErasureEngine.NOT_TENANT_SCOPED,
            set(derived.tenant_collections),
        )
        assert findings == [], "\n".join(findings)

    def test_the_derivation_is_not_vacuous(self, derived) -> None:
        # Measured 2026-09-25: 88 tenant-bearing collections. A reader that
        # collapsed to nothing would make the rule above vacuously green.
        assert len(derived.tenant_collections) >= 80
        assert len(TenantErasureEngine.INVENTORY) >= 80

    def test_the_inventory_validates(self) -> None:
        TenantErasureEngine.validate()


class TestTheDetectorFires:
    """Self-test through :func:`classification_findings`, the detector the tree check uses."""

    def test_a_new_collection_must_be_classified(self) -> None:
        findings = classification_findings(["tenants", "sites", "brand_new"], {"sites": "delete"}, {}, {"sites"})
        assert findings == [
            "brand_new: not classified for tenant deletion (inventory entry or NOT_TENANT_SCOPED reason)"
        ]

    def test_a_tenant_bearing_collection_cannot_be_declared_not_tenant_scoped(self) -> None:
        findings = classification_findings(["tenants", "sites"], {}, {"sites": "looks global"}, {"sites"})
        assert findings == ["sites: tenant-bearing (derived from the models) but not in the tenant-erasure inventory"]

    def test_a_stale_classification_fails(self) -> None:
        findings = classification_findings(["tenants"], {"gone": "delete"}, {}, set())
        assert findings == ["gone: classified but not a document collection in collections.py"]


class TestParentChainsAreReached:
    def test_every_derived_parent_chain_is_an_inventory_parent(self) -> None:
        entries = {entry.collection: entry for entry in TenantErasureEngine.INVENTORY}
        missing = []
        for child, chains in PARENT_CHAINS.items():
            declared = {(p.field, p.collection) for p in entries[child].parents}
            missing += [f"{child}.{field} -> {parent}" for field, parent in chains if (field, parent) not in declared]
        assert missing == []


class TestLegacyStampsAreDecided:
    """Collections ``backfill_tenant_key`` stamped are inventoried or declared with the stamp's reason."""

    def test_every_backfilled_collection_is_decided(self) -> None:
        stamped = set(backfill_tenant_key.TOP_LEVEL_COLLECTIONS)
        stamped |= {child for child, _, _ in backfill_tenant_key.CHILD_PROPAGATION}
        stamped.add(backfill_tenant_key.SLOT_PROPAGATION[0])
        inventory = _inventory_actions()
        undecided = [
            name
            for name in sorted(stamped)
            if name not in inventory and "v0004" not in TenantErasureEngine.NOT_TENANT_SCOPED.get(name, "")
        ]
        assert undecided == []


class TestRetentionRowsAreThoseTheAccountErasureKeeps:
    """What stays after a tenant deletion because a law keeps it is what stays after an account erasure."""

    def test_anonymized_entries_are_exactly_the_tenant_scoped_tombstone_rules(self, derived) -> None:
        tombstoned = {
            rule.collection
            for rule in ErasureEngine.ANONYMIZE_COLLECTIONS
            if rule.replacement_strategy == "tombstone_hash" and rule.collection in derived.tenant_collections
        }
        anonymized = {entry.collection for entry in TenantErasureEngine.INVENTORY if entry.action == "pseudonymize"}
        assert anonymized == tombstoned

    def test_every_kept_entry_says_why(self) -> None:
        silent = [e.collection for e in TenantErasureEngine.INVENTORY if e.action != "delete" and not e.reason]
        assert silent == []
