"""#2029 — a unique index on a tenant-bearing collection is scoped to the tenant, or declared.

``tanks`` carried a unique index on ``name`` alone. On a tenant-owned collection that
is a cross-tenant constraint: tenant B was refused a tank name tenant A used, and the
``409`` told B that another tenant holds such a tank. #2000 (fertilizers) and #1162
(species) were the same shape. This guard asks the **class**, not the sites:

* the population is every unique index ``ensure_collections`` creates, recorded by
  running it against :class:`_RecordingDb` — the helpers
  (``ensure_species_normalized_index``, ``ensure_seed_identity_indexes`` …) are
  reached the same way the boot reaches them. On 2026-10-03 the recording matched a
  real ArangoDB 3.12.8 exactly: 57 unique indexes on both sides, no difference;
* "tenant-bearing" is not remembered here: it is :func:`build_inventory`'s derivation
  (``test_tenant_scoped_reads_are_derived.py`` — a model declaring ``tenant_key``, a
  hybrid catalogue, or a declared parent chain);
* an index is **scoped** when its fields include ``tenant_key`` or, for a
  parent-scoped collection, the declared parent key (``slots → location_key``).

Every other unique index on a tenant-bearing collection must be in :data:`DECLARED`
with a reason why uniqueness across tenants is correct, or in :data:`OPEN` — known
defects of this class, which may only shrink. An entry that no longer matches an
index fails, so neither list can outlive what it excused.

**Spellings this does not see:** an index created outside ``ensure_collections`` (a
migration that never re-creates it in the bootstrap — the bootstrap is the target
state, so such an index would be drift of its own); edge collections, which the
derivation does not classify; a collection whose tenant comes from a parent the
derivation does not declare; and uniqueness enforced in application code instead of
an index.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.data_access.arango import collections as col
from tests.support.execution_guards import find_project_root
from tests.unit.guards.test_tenant_scoped_reads_are_derived import PARENT_CHAINS, build_inventory

_APP = find_project_root(Path(__file__)) / "app"

TENANT_SCOPE_FIELD = "tenant_key"

#: Unique across tenants **on purpose**, with the reason. ``(collection, fields)``.
DECLARED: dict[tuple[str, tuple[str, ...]], str] = {
    (col.CALENDAR_FEEDS, ("token",)): (
        "secret feed token; the subscription URL carries only the token and is resolved "
        "without a tenant (CalendarFeedRepository.get_by_token), so it must be unique globally"
    ),
    (col.INVITATIONS, ("token_hash",)): (
        "hash of a secret invitation token; the accept link carries only the token and is "
        "resolved before any tenant is known"
    ),
    (col.LOCATION_ASSIGNMENTS, ("membership_key", "location_key")): (
        "membership_key names one membership of one tenant, so the pair is tenant-scoped by its first field"
    ),
    (col.TASKS, tuple(col.CARE_TASK_DEDUP_INDEX_FIELDS)): (
        "computed value CARE_TASK_DEDUP_EXPRESSION concatenates @doc.tenant_key first — the tenant "
        "is inside the key (asserted by test_the_care_dedup_key_carries_the_tenant)"
    ),
}

#: Known defects of this class: a tenant is refused a value another tenant holds.
#: May only shrink — fix the index (with a migration) and delete the line.
OPEN: dict[tuple[str, tuple[str, ...]], str] = {
    (col.SPECIES, ("scientific_name",)): (
        "hybrid catalogue; #1162 scoped scientific_name_normalized to the tenant but left the raw "
        "scientific_name index collection-wide (#2063)"
    ),
    (col.PLANT_INSTANCES, ("instance_id",)): (
        "caller-supplied id; onboarding derives it as onb-<species_key>-<n> from a global species, "
        "so two tenants onboarding the same species collide (#2065)"
    ),
    (col.HARVEST_BATCHES, ("batch_id",)): "caller-supplied lot label (#2065)",
    (col.SLOTS, ("slot_id",)): "caller-supplied slot label such as TENT01_A1 (#2065)",
}


class _RecordingCollection:
    """Records index creations and answers ``indexes()`` from them; nothing else."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.rows: list[dict[str, Any]] = []

    def _add(self, fields: list[str], unique: bool, sparse: bool) -> dict[str, Any]:
        row = {
            "id": f"{self.name}/{len(self.rows)}",
            "type": "persistent",
            "fields": list(fields),
            "unique": bool(unique),
            "sparse": bool(sparse),
        }
        self.rows.append(row)
        return row

    def add_persistent_index(
        self, fields: list[str], unique: bool = False, sparse: bool = False, **_: Any
    ) -> dict[str, Any]:
        return self._add(fields, unique, sparse)

    def add_index(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._add(data["fields"], data.get("unique", False), data.get("sparse", False))

    def indexes(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows]

    def properties(self) -> dict[str, Any]:
        return {"computedValues": []}

    def configure(self, **_: Any) -> dict[str, Any]:
        return {}


class _RecordingDb:
    """A fresh volume: no collection, no graph."""

    def __init__(self) -> None:
        self.collections: dict[str, _RecordingCollection] = {}

    def has_collection(self, name: str) -> bool:
        return name in self.collections

    def create_collection(self, name: str, **_: Any) -> None:
        self.collections.setdefault(name, _RecordingCollection(name))

    def collection(self, name: str) -> _RecordingCollection:
        return self.collections.setdefault(name, _RecordingCollection(name))

    def has_graph(self, name: str) -> bool:  # noqa: ARG002
        return False

    def create_graph(self, *_: Any, **__: Any) -> None:
        return None


def bootstrap_unique_indexes() -> set[tuple[str, tuple[str, ...]]]:
    """Every unique index ``ensure_collections`` creates on a fresh volume."""
    db = _RecordingDb()
    col.ensure_collections(db)  # type: ignore[arg-type]
    return {(name, tuple(row["fields"])) for name, c in db.collections.items() for row in c.rows if row["unique"]}


def unscoped_findings(
    unique_indexes: set[tuple[str, tuple[str, ...]]],
    tenant_collections: dict[str, str],
    parent_keys: dict[str, set[str]],
) -> set[tuple[str, tuple[str, ...]]]:
    """The one detector: unique indexes on tenant-bearing collections without a tenant scope."""
    findings = set()
    for name, fields in unique_indexes:
        if name not in tenant_collections:
            continue
        scopes = {TENANT_SCOPE_FIELD} | parent_keys.get(name, set())
        if not scopes & set(fields):
            findings.add((name, fields))
    return findings


@pytest.fixture(scope="module")
def findings() -> set[tuple[str, tuple[str, ...]]]:
    inventory = build_inventory(_APP)
    parent_keys = {name: {field for field, _parent in pairs} for name, pairs in PARENT_CHAINS.items()}
    return unscoped_findings(bootstrap_unique_indexes(), dict(inventory.tenant_collections), parent_keys)


def test_every_unscoped_unique_index_is_declared_or_known_open(findings) -> None:
    undeclared = sorted(findings - set(DECLARED) - set(OPEN))
    assert not undeclared, (
        "unique index on a tenant-bearing collection without tenant_key (or the declared parent key): "
        f"{undeclared}. Scope it to the tenant, or declare in DECLARED why it must be unique across tenants."
    )


def test_no_entry_outlives_its_index(findings) -> None:
    stale = sorted((set(DECLARED) | set(OPEN)) - findings)
    assert not stale, f"entries that match no unscoped unique index any more — delete them: {stale}"


def test_the_lists_are_disjoint_and_reasoned() -> None:
    assert not set(DECLARED) & set(OPEN)
    assert all(reason.strip() for reason in (*DECLARED.values(), *OPEN.values()))


def test_tanks_are_scoped_to_the_tenant() -> None:
    """#2029 itself: the tank name is unique per tenant."""
    unique = bootstrap_unique_indexes()
    assert (col.TANKS, tuple(col.TANK_NAME_INDEX_FIELDS)) in unique
    assert (col.TANKS, ("name",)) not in unique


@pytest.mark.parametrize(
    ("collection", "fields"),
    [
        (col.ACTIVITIES, col.ACTIVITY_NAME_INDEX_FIELDS),
        (col.WORKFLOW_TEMPLATES, col.WORKFLOW_TEMPLATE_NAME_INDEX_FIELDS),
    ],
)
def test_hybrid_catalogue_names_are_scoped_to_the_tenant(collection: str, fields: list[str]) -> None:
    """#2027: a global seed row and a tenant's row of one name coexist (v0076, v0077)."""
    unique = bootstrap_unique_indexes()
    assert (collection, tuple(fields)) in unique
    assert (collection, ("name",)) not in unique


def test_the_care_dedup_key_carries_the_tenant() -> None:
    """The evidence behind the ``tasks`` entry of :data:`DECLARED`."""
    assert "CONCAT_SEPARATOR('/', @doc.tenant_key," in col.CARE_TASK_DEDUP_EXPRESSION


class TestTheDetector:
    """The detector against constructed inputs, so a green tree check means something."""

    def test_a_name_only_index_on_an_owned_collection_is_found(self) -> None:
        found = unscoped_findings({("tanks", ("name",))}, {"tanks": "own"}, {})
        assert found == {("tanks", ("name",))}

    def test_a_tenant_scoped_index_is_not_found(self) -> None:
        assert not unscoped_findings({("tanks", ("tenant_key", "name"))}, {"tanks": "own"}, {})

    def test_a_parent_key_scopes_a_parent_chained_collection(self) -> None:
        indexes = {("slots", ("location_key", "slot_id"))}
        assert not unscoped_findings(indexes, {"slots": "parent"}, {"slots": {"location_key"}})

    def test_a_global_collection_is_not_in_scope(self) -> None:
        assert not unscoped_findings({("pests", ("scientific_name",))}, {}, {})

    def test_the_recording_reaches_helper_created_indexes(self) -> None:
        unique = bootstrap_unique_indexes()
        assert (col.SPECIES, tuple(col.SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS)) in unique
        assert (col.HARVEST_INDICATORS, tuple(col.HARVEST_INDICATOR_IDENTITY_FIELDS)) in unique
