"""A care profile and its ``has_care_profile`` edge have exactly ONE writer (#1292).

The defect this guard closes was not a missing check, it was a *shape*: two
writes, one after the other, for a pair the database treats as one fact. Between
them the profile document was committed and readable through ``plant_key`` — a
field with no unique index — while nothing linked it yet. Measured twice: as a
500 in the 2026-09-14 nightly, and on 2026-09-16 in PR #1498's required
``Integration tests (ArangoDB)`` lane as ``racers answered with different
profiles: ['11770', '11772', '11772', '11772']`` while storage held one profile
and one edge.

``ArangoCareReminderRepository.create_linked_profile`` writes both inside one
stream transaction. That fixes the tree as it stands; this file is what stops it
from drifting back, and it takes **two** measurements to do so, because one is not
enough:

* :class:`TestOnlyOneFunctionWritesTheProfilePair` is the obvious arm — nothing
  under ``app/`` may write ``care_profiles`` or ``has_care_profile`` outside that
  one method. It is defeated by the exact spelling the repository used to carry:
  ``def create_profile(self, profile): return super().create(profile)`` names
  neither collection and calls no driver primitive, because ``BaseArangoRepository``
  already knows which collection it is bound to.
* :class:`TestTheRepositoryCannotStoreABareProfile` is therefore the arm that
  matters. ``ArangoCareReminderRepository`` is *bound* to ``care_profiles``, so any
  method reaching the inherited document-insert primitives stores a profile — and
  since the transactional writer uses its own handle, the honest expectation is
  that **no** method reaches them at all.

Both are AST measurements over the source, not imports: the question is what the
code is allowed to spell, and a reflective check would miss a method that is never
called from a test.
"""

from __future__ import annotations

import ast
import pathlib

import app as _app_package
from app.domain.interfaces.care_reminder_repository import ICareReminderRepository

APP_ROOT = pathlib.Path(_app_package.__file__).resolve().parent
REPOSITORY = APP_ROOT / "data_access" / "arango" / "care_reminder_repository.py"

#: The method allowed to write the pair — module-qualified so a same-named method
#: on another class cannot inherit the permission.
THE_WRITER = "ArangoCareReminderRepository.create_linked_profile"

#: Calls that put a *document* into a collection. Index and collection creation
#: (``add_persistent_index``, ``create_collection``) are deliberately absent:
#: ``collections.py`` bootstraps both collections and must keep naming them.
#: ``create_edge`` is present because the pre-#1292 ``create_profile_edge`` wrote
#: the edge through it and through no driver primitive of its own.
_DOCUMENT_WRITES = frozenset(
    {
        "insert",
        "insert_many",
        "update",
        "update_many",
        "replace",
        "replace_many",
        "delete",
        "delete_many",
        "truncate",
        "create_edge",
    }
)

#: Names of the two collections, as a constant reference and as the stored string.
_PAIR = frozenset({"CARE_PROFILES", "HAS_CARE_PROFILE", "care_profiles", "has_care_profile"})

#: ``BaseArangoRepository`` primitives that insert into the repository's **bound**
#: collection. For this class that collection is ``care_profiles``, so any of these
#: reached through ``self``/``super()`` stores a care profile on its own.
_INHERITED_PROFILE_INSERTS = frozenset({"create", "_insert_doc"})


def _functions(path: pathlib.Path) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Every function in *path*, labelled ``Class.method`` or ``function``."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, ast.FunctionDef | ast.AsyncFunctionDef):
                    found.append((f"{node.name}.{member.name}", member))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found.append((node.name, node))
    return found


def _names_the_pair(expression: ast.expr | None) -> bool:
    """Does this expression name ``care_profiles`` or ``has_care_profile``?

    Asked of the *target* of a write — the receiver of ``.insert()``, the first
    argument of ``create_edge()`` — and never of the whole function body. The
    looser "does the function mention it anywhere" reading was measured first and
    it reports ``create_confirmation_edges``, which builds a ``_to`` id out of
    ``col.CARE_PROFILES`` while writing two entirely different edge collections.
    A guard that has to be argued with on every run is a guard that gets lifted.
    """
    if expression is None:
        return False
    rendered = ast.unparse(expression)
    return any(name in rendered for name in _PAIR)


def _writes_the_pair(node: ast.AST) -> bool:
    """Is this call a document write **into** one of the two collections?

    Two shapes, because the pre-#1292 code used both: a driver primitive whose
    *receiver* names the collection (``transaction.collection(col.CARE_PROFILES)
    .insert(...)``, ``self._db.collection(...).insert(...)``), and
    ``BaseArangoRepository.create_edge(col.HAS_CARE_PROFILE, ...)``, which names it
    as the first argument and calls no primitive of its own.
    """
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    name = node.func.attr
    if name == "create_edge":
        return _names_the_pair(node.args[0] if node.args else None)
    return name in _DOCUMENT_WRITES and _names_the_pair(node.func.value)


class TestOnlyOneFunctionWritesTheProfilePair:
    def test_no_other_function_under_app_writes_either_collection(self):
        writers: dict[str, list[str]] = {}
        for path in sorted(APP_ROOT.rglob("*.py")):
            for label, node in _functions(path):
                calls = sorted({ast.unparse(call.func) for call in ast.walk(node) if _writes_the_pair(call)})
                if calls:
                    writers[f"{path.relative_to(APP_ROOT)}::{label}"] = calls

        assert sorted(writers) == [f"data_access/arango/care_reminder_repository.py::{THE_WRITER}"], (
            "a care profile or its has_care_profile edge is written outside the one transactional "
            f"writer; every write to the pair has to happen inside it:\n  {writers}"
        )


class TestTheRepositoryCannotStoreABareProfile:
    def test_no_method_reaches_the_inherited_document_insert(self):
        """The arm that survives the spelling the other one misses.

        ``return super().create(profile)`` — the pre-#1292 ``create_profile`` — names
        no collection and calls no driver primitive, and is exactly the call that
        stores a profile with nothing linking it.
        """
        offenders: dict[str, list[str]] = {}
        for label, node in _functions(REPOSITORY):
            reached = sorted(
                {
                    f"{ast.unparse(inner.func.value)}.{inner.func.attr}"
                    for inner in ast.walk(node)
                    if isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Attribute)
                    and inner.func.attr in _INHERITED_PROFILE_INSERTS
                    and (
                        ast.unparse(inner.func.value) == "self"
                        or isinstance(inner.func.value, ast.Call)
                        and isinstance(inner.func.value.func, ast.Name)
                        and inner.func.value.func.id == "super"
                    )
                }
            )
            if reached:
                offenders[label] = reached

        assert offenders == {}, (
            "ArangoCareReminderRepository is bound to care_profiles, so these calls store a profile "
            "document on their own — with no has_care_profile edge, which is the #1292 window:\n  "
            f"{offenders}"
        )

    def test_the_interface_offers_no_second_way_to_store_one(self):
        """The narrow methods are gone from the contract, not merely unused.

        A repository can only be *asked* for what the interface declares, so their
        absence is what makes the two-step write unspellable for every caller
        (service, migration, MCP dispatcher) rather than only for today's ones.
        """
        for retired in ("create_profile", "create_profile_edge"):
            assert not hasattr(ICareReminderRepository, retired), (
                f"ICareReminderRepository.{retired} is back; a caller can store a care profile "
                "without its edge again, which reopens #1292"
            )
        assert hasattr(ICareReminderRepository, "create_linked_profile")
