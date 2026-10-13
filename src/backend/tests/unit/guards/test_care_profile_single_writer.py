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
from drifting back, and it takes **three** measurements to do so, because no one
of them is enough:

* :class:`TestOnlyOneFunctionInsertsTheProfilePair` is the obvious arm — nothing
  under ``app/`` may *insert* into ``care_profiles`` or ``has_care_profile``
  outside that one method. Three spellings reach the collections and it took the
  review to name them all; each was measured against the real tree rather than
  imagined:

  1. a driver primitive whose receiver names the collection —
     ``transaction.collection(col.CARE_PROFILES).insert(...)``;
  2. a primitive on a **local handle** bound earlier —
     ``handle = db.collection(col.CARE_PROFILES)`` … ``handle.insert(...)``. Not
     hypothetical: ``collections.py`` already binds both collections that way
     (``has_care_profile_col = db.collection(HAS_CARE_PROFILE)``), so the first
     version of this guard would have watched a variable it could not follow. The
     local assignment is now resolved back to its ``db.collection(...)``
     initialiser;
  3. an **AQL** ``INSERT … IN <collection>`` in a query string, the shape
     ``_write_call_graph._QUERY_WRITE`` already knows about.

  Restricted to ``INSERT`` on purpose, and the restriction is measured, not
  convenient: ``app/migrations/backfill_tenant_key.py`` runs
  ``UPDATE doc WITH {tenant_key: …} IN care_profiles`` over every top-level
  collection. That is a legitimate stamping pass over *existing* rows and it can
  never create an unlinked profile. The invariant this file defends is "a care
  profile comes into existence only together with its edge", so the predicate is
  about creation.

* :class:`TestTheRepositoryCannotStoreABareProfile` is the arm that catches what
  the first one structurally cannot: ``def create_profile(self, profile): return
  super().create(profile)`` — the exact spelling the repository used to carry —
  names neither collection and calls no driver primitive, because
  ``BaseArangoRepository`` already knows which collection it is bound to. Since
  that class is bound to ``care_profiles``, any method reaching the inherited
  document-insert primitives stores a profile, and the honest expectation is that
  **no** method does.

* :class:`TestTheEdgeCollectionHasADeclaredAudience` is the ratchet under both.
  A static scan cannot follow an AQL statement whose collection name is
  interpolated (``f"… IN {coll_name}"``, again a real shape in
  ``backfill_tenant_key.py``), so a new module could in principle insert the edge
  invisibly. It could not do so without *naming* ``HAS_CARE_PROFILE`` somewhere,
  and the set of modules that do is small and listed. This says nothing about what
  a module does with it — only that a new one has to be argued for here.

All three are AST measurements over the source, not imports: the question is what
the code is allowed to spell, and a reflective check would miss a method that is
never called from a test.
"""

from __future__ import annotations

import ast
import pathlib
import re

import app as _app_package
from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
from tests.support.repo_scripts import load_repo_script

_source_text = load_repo_script("source_text")

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
#:
#: ``update``/``replace``/``delete`` are absent too, and that is the SCR-003
#: narrowing: ``backfill_tenant_key.py`` legitimately stamps ``tenant_key`` onto
#: existing ``care_profiles`` rows, which can never produce an unlinked profile.
#: The invariant is about a profile coming *into existence*.
_DOCUMENT_INSERTS = frozenset({"insert", "insert_many", "create_edge"})

#: Names of the two collections, as a constant reference and as the stored string.
_PAIR = frozenset({"CARE_PROFILES", "HAS_CARE_PROFILE", "care_profiles", "has_care_profile"})

#: An AQL insert into one of them. ``INSERT <expr> IN <collection>`` is AQL's only
#: insert form, and the collection is the token after ``IN``.
_AQL_INSERT = re.compile(r"\bINSERT\b[^\n]*?\bIN\s+(?P<collection>\w+)", re.IGNORECASE)

#: ``BaseArangoRepository`` primitives that insert into the repository's **bound**
#: collection. For this class that collection is ``care_profiles``, so any of these
#: reached through ``self``/``super()`` stores a care profile on its own.
_INHERITED_PROFILE_INSERTS = frozenset({"create", "_insert_doc"})

#: Modules allowed to name the edge collection at all, with the reason. A static
#: scan cannot follow ``f"… IN {coll_name}"``, so this is the ratchet underneath:
#: a new writer must at least appear here.
_EDGE_COLLECTION_AUDIENCE = {
    "data_access/arango/collections.py": "declares the collection and its unique _from index",
    "data_access/arango/care_reminder_repository.py": "the single writer, plus the edge read",
    "migrations/versions/v0048_backfill_missing_care_profiles.py": "declares it in REQUIRED_COLLECTIONS",
}


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


def _collection_handles(node: ast.AST) -> dict[str, ast.expr]:
    """Local names bound to a ``…collection(<expr>)`` call, mapped to that ``<expr>``.

    SCR-003: ``handle = db.collection(col.CARE_PROFILES)`` followed by
    ``handle.insert(...)`` reaches the collection while the receiver at the write
    site is a bare name. ``collections.py`` binds both of this guard's collections
    exactly that way, so the shape is in the tree already — it simply happens not to
    insert through them today.
    """
    handles: dict[str, ast.expr] = {}
    for inner in ast.walk(node):
        if not isinstance(inner, ast.Assign) or not isinstance(inner.value, ast.Call):
            continue
        callee = inner.value.func
        if not isinstance(callee, ast.Attribute) or callee.attr != "collection" or not inner.value.args:
            continue
        for target in inner.targets:
            if isinstance(target, ast.Name):
                handles[target.id] = inner.value.args[0]
    return handles


def _inserts_the_pair(node: ast.AST, handles: dict[str, ast.expr]) -> bool:
    """Is this call an insert **into** one of the two collections?"""
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    name = node.func.attr
    if name == "create_edge":
        return _names_the_pair(node.args[0] if node.args else None)
    if name not in _DOCUMENT_INSERTS:
        return False
    receiver = node.func.value
    if isinstance(receiver, ast.Name) and receiver.id in handles:
        return _names_the_pair(handles[receiver.id])
    return _names_the_pair(receiver)


def _aql_inserts_the_pair(node: ast.AST) -> str | None:
    """The pair collection an AQL ``INSERT`` in this literal targets, if any.

    ``JoinedStr`` parts are joined with a placeholder rather than dropped, so an
    f-string whose *collection* is interpolated cannot accidentally read as an
    insert into a literal name that appears elsewhere in the query.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        text = node.value
    elif isinstance(node, ast.JoinedStr):
        text = "FMT".join(
            part.value for part in node.values if isinstance(part, ast.Constant) and isinstance(part.value, str)
        )
    else:
        return None
    for match in _AQL_INSERT.finditer(text):
        if match.group("collection") in _PAIR:
            return match.group("collection")
    return None


class TestOnlyOneFunctionInsertsTheProfilePair:
    def test_no_other_function_under_app_inserts_into_either_collection(self):
        """All three insert spellings, over the whole package (SCR-003).

        The first version of this test recognised only spelling (1) — a receiver
        expression that literally names the collection — while promising "nothing
        writes it". A local handle and an AQL ``INSERT`` both pass that promise
        silently, and both shapes exist in this tree already.
        """
        inserters: dict[str, list[str]] = {}
        for path in sorted(APP_ROOT.rglob("*.py")):
            for label, node in _functions(path):
                handles = _collection_handles(node)
                found = {
                    ast.unparse(inner.func)
                    for inner in ast.walk(node)
                    if _inserts_the_pair(inner, handles) and isinstance(inner, ast.Call)
                }
                found |= {
                    f"AQL INSERT INTO {target}"
                    for inner in ast.walk(node)
                    if (target := _aql_inserts_the_pair(inner)) is not None
                }
                if found:
                    inserters[f"{path.relative_to(APP_ROOT)}::{label}"] = sorted(found)

        assert sorted(inserters) == [f"data_access/arango/care_reminder_repository.py::{THE_WRITER}"], (
            "a care profile or its has_care_profile edge is INSERTED outside the one transactional "
            f"writer; a profile may only come into existence together with its edge:\n  {inserters}"
        )

    def test_the_predicate_sees_all_three_spellings(self):
        """The guard's own falsification, so it cannot quietly stop matching.

        Each snippet is a way the pre-#1292 code could be written back in. If the
        predicate stops recognising one, this fails here instead of leaving the arm
        above green against a tree that no longer means what it says.
        """
        snippets = {
            "receiver names it": "def f(txn):\n    txn.collection(col.CARE_PROFILES).insert({})\n",
            "local handle": "def f(db):\n    handle = db.collection(col.HAS_CARE_PROFILE)\n    handle.insert({})\n",
            "create_edge": "def f(self):\n    self.create_edge(col.HAS_CARE_PROFILE, a, b)\n",
            "aql insert": 'def f(db):\n    db.aql.execute("INSERT @doc IN care_profiles RETURN NEW")\n',
        }
        missed = []
        for name, source in snippets.items():
            node = ast.parse(source).body[0]
            handles = _collection_handles(node)
            direct = any(_inserts_the_pair(inner, handles) for inner in ast.walk(node))
            aql = any(_aql_inserts_the_pair(inner) is not None for inner in ast.walk(node))
            if not (direct or aql):
                missed.append(name)
        assert missed == [], f"the predicate no longer recognises: {missed}"

    def test_an_update_of_an_existing_profile_is_not_an_insert(self):
        """The narrowing, pinned — otherwise it is indistinguishable from a hole.

        ``backfill_tenant_key.py`` stamps ``tenant_key`` onto stored profiles. It
        cannot create an unlinked one, so it is out of scope by *predicate* rather
        than by exemption, and this says so in a way that goes red if the predicate
        ever widens back to "any write".
        """
        node = ast.parse(
            'def f(db):\n    db.aql.execute("FOR d IN care_profiles UPDATE d WITH {} IN care_profiles")\n'
        ).body[0]
        handles = _collection_handles(node)
        assert not any(_inserts_the_pair(inner, handles) for inner in ast.walk(node))
        assert all(_aql_inserts_the_pair(inner) is None for inner in ast.walk(node))


class TestTheEdgeCollectionHasADeclaredAudience:
    def test_only_the_listed_modules_name_the_edge_collection(self):
        """The ratchet under a scan that cannot follow an interpolated collection.

        ``f"… IN {coll_name}"`` (a real shape in ``backfill_tenant_key.py``) hides
        its target from every static predicate above. A module cannot insert the
        edge without naming ``HAS_CARE_PROFILE`` somewhere, though — so the set of
        modules that name it is bounded here, with a reason each. This claims
        nothing about what those modules do; it makes a new one a decision.

        Over the **executable** text only (#1456). Both directions of the naive
        form are wrong here: a module that merely explains the edge in a comment
        would have to be excused as if it wrote one, and deleting such a comment
        would make the excuse look stale and turn the test red over prose.
        """
        naming = {}
        for path in sorted(APP_ROOT.rglob("*.py")):
            code = _source_text.executable_source(path.read_text(encoding="utf-8"), language="python")
            if "HAS_CARE_PROFILE" in code:
                naming[str(path.relative_to(APP_ROOT))] = _EDGE_COLLECTION_AUDIENCE.get(str(path.relative_to(APP_ROOT)))

        unexplained = sorted(module for module, reason in naming.items() if reason is None)
        assert unexplained == [], (
            "these modules name the has_care_profile edge collection and this file does not say why. "
            "If one of them inserts the edge, the invariant is broken; if it does not, add it to "
            f"_EDGE_COLLECTION_AUDIENCE with the reason:\n  {unexplained}"
        )
        stale = sorted(set(_EDGE_COLLECTION_AUDIENCE) - set(naming))
        assert stale == [], f"_EDGE_COLLECTION_AUDIENCE excuses modules that no longer name it: {stale}"


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
        for retired, why in {
            "create_profile": "a caller can store a care profile without its edge again",
            "create_profile_edge": "a caller can link a profile as a second, separate write again",
            "delete_profile": (
                "deleting the document while the has_care_profile edge survives locks the plant out "
                "of ever getting a profile: every later create is refused by the unique _from index "
                "and the edge then resolves to nothing, so the race resolution re-raises for good"
            ),
        }.items():
            assert not hasattr(ICareReminderRepository, retired), (
                f"ICareReminderRepository.{retired} is back — {why}, which reopens #1292"
            )
        assert hasattr(ICareReminderRepository, "create_linked_profile")
