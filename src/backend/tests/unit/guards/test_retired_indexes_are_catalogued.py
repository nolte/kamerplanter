"""#2064 — every migration that drops an index is in the retired-index catalogue, or says why not.

A migration retires an index once; an older image's ``ensure_collections`` re-creates
it on its next start, and the migration never runs again. Every boot therefore
enforces :data:`~app.migrations.support.retired_indexes.RETIRED_INDEXES` after the
migrations. That only protects what the catalogue lists — so this guard asks the
**class**: every version module that drops an index.

**What counts as dropping an index.** In ``app/migrations/versions/v[0-9]*.py``, a call
of ``retire_legacy_index`` (by name, by attribute, or under an ``import … as`` alias)
or of any ``.delete_index(...)`` method. Each such version must be one of the catalogue
entries' ``retired_by``, or in :data:`NOT_CATALOGUED` with the reason.

**Spellings this does NOT see:** ``getattr(collection, "delete_index")``; a drop through
the HTTP API (``DELETE /_api/index/…``) or ``db._conn``; a version that delegates to a
helper outside ``versions/`` which drops an index (``retire_legacy_index`` is matched by
name, any other support function is not); a dropped *collection* (its indexes go with
it); and an index dropped by hand. The catalogue also cannot see an index an older
image creates that no migration ever retired — that would be drift of its own.
"""

from __future__ import annotations

import ast
import textwrap
from collections.abc import Mapping
from pathlib import Path

import pytest

from app.migrations import versions as versions_pkg
from app.migrations.support.legacy_indexes import IndexShape
from app.migrations.support.retired_indexes import RETIRED_INDEXES
from tests.unit.guards.test_tenant_unique_indexes_are_scoped import _RecordingDb

_VERSIONS_DIR = Path(next(iter(versions_pkg.__path__)))

#: Version modules that drop an index but are not catalogue entries, with the reason.
NOT_CATALOGUED: dict[str, str] = {
    "0026": (
        "drops the non-unique species(scientific_name_normalized) bootstrap index; a re-created "
        "non-unique index imposes no constraint, it only costs storage"
    ),
    "0031": (
        "drops non-unique user_key indexes on user_preferences / onboarding_states; a re-created "
        "non-unique index imposes no constraint (and ensure_user_singleton_index creates one itself "
        "as its fallback)"
    ),
    "0062": (
        "a relaxation: the unique attachments(storage_key) index becomes non-unique. retire_legacy_index "
        "refuses a non-unique replacement by design, so this shape cannot be enforced without weakening "
        "that check; measured re-created by the image before v0062 (#2064 report, open)"
    ),
}

_DROP_METHODS = frozenset({"delete_index"})
_RETIRE_FUNCTION = "retire_legacy_index"


def drops_an_index(source: str) -> bool:
    """Whether ``source`` calls ``retire_legacy_index`` (any spelling above) or ``.delete_index``."""
    tree = ast.parse(source)
    retire_names = {_RETIRE_FUNCTION}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            retire_names |= {alias.asname for alias in node.names if alias.name == _RETIRE_FUNCTION and alias.asname}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in retire_names:
            return True
        if isinstance(func, ast.Attribute) and (func.attr in _DROP_METHODS or func.attr == _RETIRE_FUNCTION):
            return True
    return False


def _version_sources() -> dict[str, str]:
    return {path.stem[1:5]: path.read_text(encoding="utf-8") for path in sorted(_VERSIONS_DIR.glob("v[0-9]*.py"))}


def uncatalogued(sources: Mapping[str, str], catalogued: set[str], excused: Mapping[str, str]) -> list[str]:
    """The one detector: dropping versions neither catalogued nor excused."""
    return sorted(v for v, src in sources.items() if drops_an_index(src) and v not in catalogued and v not in excused)


def _catalogued_versions() -> set[str]:
    return {version for entry in RETIRED_INDEXES for version in entry.retired_by}


def _bootstrap_shapes() -> set[tuple[str, IndexShape]]:
    """Every index ``ensure_collections`` creates on a fresh volume, as ``(collection, shape)``."""
    from app.data_access.arango import collections as col

    db = _RecordingDb()
    col.ensure_collections(db)  # type: ignore[arg-type]
    return {
        (name, IndexShape(fields=tuple(row["fields"]), unique=row["unique"], sparse=row["sparse"]))
        for name, c in db.collections.items()
        for row in c.rows
    }


class TestTheTree:
    def test_every_dropping_migration_is_catalogued_or_excused(self) -> None:
        missing = uncatalogued(_version_sources(), _catalogued_versions(), NOT_CATALOGUED)
        assert missing == [], (
            f"migrations that drop an index but are not in RETIRED_INDEXES: {missing}. An older image "
            "re-creates the index and the migration never runs again (#2064) — add an entry to "
            "app/migrations/support/retired_indexes.py, or a reason to NOT_CATALOGUED."
        )

    def test_the_measured_population(self) -> None:
        """14 dropping versions on 2026-10-04 — a scan that finds none is broken, not clean."""
        dropping = {v for v, src in _version_sources().items() if drops_an_index(src)}
        assert {
            "0026",
            "0030",
            "0041",
            "0064",
            "0069",
            "0072",
            "0073",
            "0074",
            "0075",
            "0076",
            "0077",
            "0079",
        } <= dropping
        assert len(dropping) >= 14

    def test_no_entry_names_a_migration_that_drops_nothing(self) -> None:
        sources = _version_sources()
        stale = sorted(
            v for v in _catalogued_versions() | set(NOT_CATALOGUED) if not drops_an_index(sources.get(v, ""))
        )
        assert stale == [], f"catalogue / NOT_CATALOGUED names versions that drop no index (or do not exist): {stale}"

    def test_catalogued_and_excused_are_disjoint_and_reasoned(self) -> None:
        assert not _catalogued_versions() & set(NOT_CATALOGUED)
        assert all(reason.strip() for reason in NOT_CATALOGUED.values())


class TestTheCatalogue:
    def test_every_replacement_is_what_the_bootstrap_creates(self) -> None:
        """Enforcement refuses without the replacement; the boot creates it just before."""
        shapes = _bootstrap_shapes()
        missing = [entry.label for entry in RETIRED_INDEXES if (entry.collection, entry.replacement) not in shapes]
        assert missing == []

    def test_no_legacy_shape_is_what_the_bootstrap_creates(self) -> None:
        """Otherwise every boot would create the index and retire it again."""
        shapes = _bootstrap_shapes()
        recreated = [entry.label for entry in RETIRED_INDEXES if (entry.collection, entry.legacy) in shapes]
        assert recreated == []

    def test_no_replacement_is_itself_retired(self) -> None:
        """A chain must point at today's shape, or enforcement refuses once the middle link is gone."""
        legacy = {(entry.collection, entry.legacy) for entry in RETIRED_INDEXES}
        chained = [entry.label for entry in RETIRED_INDEXES if (entry.collection, entry.replacement) in legacy]
        assert chained == []

    def test_each_shape_has_one_entry(self) -> None:
        keys = [(entry.collection, entry.legacy) for entry in RETIRED_INDEXES]
        assert len(keys) == len(set(keys))


_DROPPING = {
    "direct_import": """
        from app.migrations.support.legacy_indexes import retire_legacy_index
        retire_legacy_index(c, legacy=a, replacement=b, dry_run=False)
    """,
    "aliased_import": """
        from app.migrations.support.legacy_indexes import retire_legacy_index as retire
        retire(c, legacy=a, replacement=b, dry_run=False)
    """,
    "module_attribute": """
        from app.migrations.support import legacy_indexes
        legacy_indexes.retire_legacy_index(c, legacy=a, replacement=b, dry_run=False)
    """,
    "delete_index_method": 'collection.delete_index(idx["id"], ignore_missing=True)',
    "delete_index_in_loop": """
        for index_id in ids:
            db.collection("x").delete_index(index_id)
    """,
}

_NOT_DROPPING = {
    "index_creation_only": 'collection.add_persistent_index(fields=["x"], unique=True)',
    "selector_only": """
        from app.migrations.support.legacy_indexes import indexes_on
        rows = indexes_on(collection, ["x"])
    """,
    "name_mentioned_in_a_string": 'note = "retire_legacy_index and delete_index are documented elsewhere"',
}


class TestTheDetector:
    @pytest.mark.parametrize("source", list(_DROPPING.values()), ids=list(_DROPPING))
    def test_a_synthetic_dropping_migration_is_found(self, source: str) -> None:
        sources = {"9999": textwrap.dedent(source)}
        assert uncatalogued(sources, set(), {}) == ["9999"]

    @pytest.mark.parametrize("source", list(_NOT_DROPPING.values()), ids=list(_NOT_DROPPING))
    def test_a_migration_that_drops_nothing_is_not_found(self, source: str) -> None:
        assert uncatalogued({"9999": textwrap.dedent(source)}, set(), {}) == []

    def test_a_catalogued_or_excused_version_is_not_reported(self) -> None:
        source = textwrap.dedent(_DROPPING["delete_index_method"])
        assert uncatalogued({"9999": source}, {"9999"}, {}) == []
        assert uncatalogued({"9999": source}, set(), {"9999": "reason"}) == []
