"""No new migration recognises an index by an inline type comparison (#2034).

Until 2026-06-07 (``516bcd832``) ``ensure_collections`` created every index with
``add_hash_index``, and ArangoDB 3.12 still reports such an index as
``type: "hash"``. v0030, v0064 and v0069 each found the legacy unique index they
retire with ``type == "persistent"``, missed it on every pre-June volume, reported
success and left the retired constraint in force (v0072, v0073, v0074 correct
them). Three migrations, one spelling — so this guard asks the **class**, not the
three sites: every comparison of an index's ``type`` against an index type name in
a version module.

**What counts as a selector.** Any ``ast.Compare`` (``==``, ``!=``, ``in``,
``not in``, either operand order) between

* a read of the ``type`` key — ``x.get("type")``, ``x.get("type", default)`` or
  ``x["type"]`` (quote style is not part of the AST, so ``'type'`` is the same
  node), and
* an index type name, or a tuple/list/set literal containing one;

plus a ``match`` mapping pattern ``{"type": "<name>"}``. A new migration selects
indexes through :mod:`app.migrations.support.legacy_indexes` instead, and then
carries no such comparison at all.

**Spellings this does NOT see** (named so nobody reads more into a green run):
the type compared against a *name* (``x.get("type") in SOME_TYPES``) — a document
``type`` field compared against a constant looks identical and would make the
guard noisy; a computed key (``x.get(key)``); ``operator.eq`` / ``getattr``; an
index filter written in AQL; the type read into a variable first and compared
later (``t = idx["type"]`` … ``if t == "persistent"``) — the comparison then has
no ``type`` read in it; and every file outside ``app/migrations/versions/v[0-9]*.py``
— ``app/migrations/support/`` and the ``app/data_access`` helpers are not scanned
at all. ``"edge"`` is not in the vocabulary: it is also a
*collection* type (``info["type"] == "edge"`` in the erasure code), and an edge
index is never retired.

**Shipped migrations are frozen** (M-7, ``test_applied_migration_sources_are_frozen``)
and cannot be rewritten to use the helper, so each is allow-listed with its
selector count and the reason it is not, or no longer, a defect. The count is
exact, and an allow-listed version must be at or below ``_SHIPPED_THROUGH`` — a
new migration cannot join the list without moving that boundary on purpose.
"""

from __future__ import annotations

import ast
import textwrap
from collections.abc import Mapping
from pathlib import Path

import pytest

from app.migrations import versions as versions_pkg

_VERSIONS_DIR = Path(next(iter(versions_pkg.__path__)))

#: The highest version merged to ``develop`` when this guard landed (v0072,
#: ``origin/develop`` = ``49c96ec6d``). Allow-list entries above it are refused.
_SHIPPED_THROUGH = "0072"

#: Index type names ArangoDB reports. ``"edge"`` is absent on purpose (module docstring).
_INDEX_TYPE_NAMES = frozenset(
    {"persistent", "hash", "skiplist", "fulltext", "geo", "ttl", "inverted", "zkd", "mdi", "mdi-prefixed", "primary"}
)

#: Shipped (frozen) version modules with inline selectors: ``stem -> (count, reason)``.
_FROZEN_ALLOWED: dict[str, tuple[int, str]] = {
    "v0009_notification_group_key_index": (1, "create-if-missing check of its own new index; no retirement"),
    "v0011_climate_normals_collection": (1, "create-if-missing check on a collection born 2026-07-11"),
    "v0012_irrigation_demands_collection": (1, "create-if-missing check on a collection born 2026-07-11"),
    "v0013_hardiness_zones_collection": (1, "create-if-missing check on a collection born 2026-07-11"),
    "v0014_cv_diagnosis_collections": (1, "create-if-missing check on collections born 2026-07-11"),
    "v0015_inventree_collections": (1, "create-if-missing check on collections born 2026-07-11"),
    "v0016_glossary_terms_collection": (1, "create-if-missing check on a collection born 2026-07-12"),
    "v0017_mcp_collections": (1, "create-if-missing check on collections born 2026-07-12"),
    "v0018_propagation_collections": (1, "create-if-missing check on collections born 2026-07-12"),
    "v0019_actuator_collections": (1, "create-if-missing check on collections born 2026-07-12"),
    "v0026_promote_scientific_name_normalized_unique": (1, "retired index born persistent 2026-07-11 (d6d390b67)"),
    "v0030_sparse_unique_harvest_batch_id": (1, "missed the hash-typed batch_id index; corrected by v0073"),
    "v0031_dedup_user_singletons_unique_index": (1, "user_key index born persistent 2026-07-26 (145b6fc86)"),
    "v0032_two_axis_role_model": (1, "create-if-missing check of its own new index; no retirement"),
    "v0033_diary_analysis_state_index": (1, "create-if-missing check of its own new index; no retirement"),
    "v0041_tenant_scoped_species_dedup_index": (2, "retired index born persistent 2026-07-11 (d6d390b67)"),
    "v0045_dedup_open_care_tasks_unique_index": (1, "named index created by v0045 itself; no retirement"),
    "v0062_split_shared_attachment_ownership": (1, "storage_key index born persistent 2026-06-20 (6c6cdfa81)"),
    "v0064_bind_provider_links_to_configuration": (1, "missed the hash-typed provider index; corrected by v0074"),
    "v0069_tenant_scoped_fertilizer_identity_index": (1, "missed the hash-typed fertilizer index; corrected by v0072"),
    "v0072_complete_fertilizer_identity_cutover": (1, "already matches ('persistent', 'hash')"),
}


def _reads_type_key(node: ast.expr) -> bool:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "type"
    ):
        return True
    return isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == "type"


def _names_index_type(node: ast.expr) -> bool:
    if isinstance(node, ast.Constant):
        return node.value in _INDEX_TYPE_NAMES
    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        return any(isinstance(elt, ast.Constant) and elt.value in _INDEX_TYPE_NAMES for elt in node.elts)
    return False


def _pattern_names_index_type(pattern: ast.pattern) -> bool:
    if isinstance(pattern, ast.MatchValue):
        return _names_index_type(pattern.value)
    if isinstance(pattern, ast.MatchOr):
        return any(_pattern_names_index_type(alternative) for alternative in pattern.patterns)
    return False


def index_type_selectors(source: str) -> list[int]:
    """Line numbers of every inline index-type selector in ``source``."""
    lines: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Compare):
            operands = [node.left, *node.comparators]
            if any(
                (_reads_type_key(left) and _names_index_type(right))
                or (_reads_type_key(right) and _names_index_type(left))
                for left, right in zip(operands, operands[1:], strict=False)
            ):
                lines.append(node.lineno)
        elif isinstance(node, ast.MatchMapping):
            if any(
                isinstance(key, ast.Constant) and key.value == "type" and _pattern_names_index_type(pattern)
                for key, pattern in zip(node.keys, node.patterns, strict=True)
            ):
                lines.append(node.lineno)
    return sorted(lines)


def violations(sources: Mapping[str, str], allowed: Mapping[str, tuple[int, str]]) -> list[str]:
    """Every module whose selector count differs from its allow-list entry (absent = 0)."""
    found: list[str] = []
    for stem, source in sorted(sources.items()):
        lines = index_type_selectors(source)
        expected = allowed[stem][0] if stem in allowed else 0
        if len(lines) != expected:
            found.append(f"{stem}: {len(lines)} inline index-type selector(s) at lines {lines}, allowed {expected}")
    return found


def _version_sources() -> dict[str, str]:
    return {path.stem: path.read_text(encoding="utf-8") for path in sorted(_VERSIONS_DIR.glob("v[0-9]*.py"))}


class TestTheTree:
    def test_no_version_module_selects_an_index_by_an_inline_type(self) -> None:
        assert violations(_version_sources(), _FROZEN_ALLOWED) == [], (
            "select indexes through app.migrations.support.legacy_indexes (is_index_on / indexes_on / "
            "retire_legacy_index): pre-June volumes report their indexes as type 'hash' (#2034)"
        )

    def test_every_allow_listed_module_exists(self) -> None:
        assert sorted(set(_FROZEN_ALLOWED) - set(_version_sources())) == []

    def test_only_shipped_versions_are_allow_listed(self) -> None:
        assert [stem for stem in _FROZEN_ALLOWED if stem[1:5] > _SHIPPED_THROUGH] == []

    def test_the_measured_population(self) -> None:
        """22 selectors in 21 shipped modules on 2026-10-03 — a scan that finds none is broken, not clean."""
        counts = {stem: len(index_type_selectors(source)) for stem, source in _version_sources().items()}
        assert sum(counts.values()) >= 22
        assert sum(1 for count in counts.values() if count) >= 21


_SPELLINGS = {
    "get_double_quotes": 'ok = idx.get("type") == "persistent"',
    "get_single_quotes": "ok = idx.get('type') == 'persistent'",
    "get_with_default": 'ok = idx.get("type", "") == "persistent"',
    "subscript_double_quotes": 'ok = idx["type"] == "persistent"',
    "subscript_single_quotes": "ok = idx['type'] == 'hash'",
    "reversed_operands": 'ok = "persistent" == idx.get("type")',
    "not_equal": 'ok = idx.get("type") != "persistent"',
    "in_tuple": 'ok = idx["type"] in ("persistent", "hash")',
    "in_list": 'ok = idx.get("type") in ["persistent"]',
    "in_set": "ok = idx.get('type') in {'persistent', 'hash'}",
    "not_in_tuple": 'ok = idx.get("type") not in ("persistent", "hash")',
    "comprehension_filter": 'ids = [i["id"] for i in rows if i.get("type") == "persistent" and i.get("unique")]',
    "match_mapping": """
        match idx:
            case {"type": "persistent" | "hash"}:
                pass
    """,
}


class TestTheSelectorPredicate:
    @pytest.mark.parametrize("source", list(_SPELLINGS.values()), ids=list(_SPELLINGS))
    def test_a_synthetic_new_migration_with_this_spelling_fails(self, source: str) -> None:
        sources = {"v9999_synthetic": textwrap.dedent(source)}

        assert index_type_selectors(sources["v9999_synthetic"]) != []
        assert violations(sources, _FROZEN_ALLOWED) != []

    def test_a_migration_using_the_shared_selector_passes(self) -> None:
        source = textwrap.dedent(
            """
            from app.migrations.support.legacy_indexes import indexes_on, is_index_on
            legacy = [idx for idx in indexes_on(collection, ["batch_id"]) if idx.get("unique")]
            ok = is_index_on(row, ["batch_id"])
            """
        )

        assert violations({"v9999_synthetic": source}, _FROZEN_ALLOWED) == []

    def test_a_document_type_field_is_not_an_index_selector(self) -> None:
        source = 'coco = doc.get("type") == "coco"\nedges = [n for n, info in cols.items() if info["type"] == "edge"]'

        assert index_type_selectors(source) == []

    def test_a_frozen_module_gaining_a_selector_fails(self) -> None:
        source = 'a = idx.get("type") == "persistent"\nb = idx["type"] == "hash"'

        assert violations({"v0030_sparse_unique_harvest_batch_id": source}, _FROZEN_ALLOWED) != []
