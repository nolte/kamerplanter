"""The cultivar read surface must not silently grow a second scope — #816 pendant (C-6, #1090).

Solitary structural unit tests. The "unit" here is the *shape of the cultivar
read surface*, so the only collaborator is the source text of the modules that
touch the ``cultivars`` collection — read once, parsed with :mod:`ast`, no
database, no clock, no network.

Why the **absence** form, and not the agreement form
----------------------------------------------------
``TestSpeciesScopeConsistency`` (``test_botanical_family_repository.py``, Issue
#816) guards *agreement*: three species reads — the listing, the per-family count
and the bulk count — narrow the collection, a user follows the number straight
into the list, and scoping one without the others makes the displayed count
contradict the list it links to. Agreement is only checkable because there is
more than one narrowing path to compare.

Cultivars have exactly **one** narrowing read path today:
:meth:`ArangoSpeciesRepository.get_cultivars` in its scoped branch. There is no
cultivar count endpoint, no second listing, no aggregate. With a single path
there is nothing to hold *against* anything, so the agreement form would be
vacuous (T2 of ``spec/project/test-falsifiability/``: an assertion no achievable
input can break). Operator decision **Q6** (2026-08-09, recorded in
``.audits/issue-orchestrate/1090/analysis.md``) therefore approved the *absence*
form instead: pin that the "exactly one" is still true, so the day it stops being
true a human is forced to look.

What must happen when a second narrowing path appears
-----------------------------------------------------
These tests fail loudly and name the new path. The correct response is **not** to
extend the declared inventory below and move on. It is to:

1. add the new path to :data:`_DECLARED_CULTIVAR_SURFACE` / :data:`_MODULES_TOUCHING_CULTIVARS`
   with its rationale, and
2. **replace** :class:`TestCultivarScopeConsistency` with the agreement form —
   capture the AQL of every narrowing path and assert their scope predicates are
   identical, exactly as ``TestSpeciesScopeConsistencyWhenTenantScoped`` does for
   species. Two narrowing reads that disagree is the #816 defect; two that agree
   only by coincidence is the #816 defect waiting for the next edit.

The complementary danger — a second read path that narrows by *nothing* and so
leaks every tenant's cultivars (#324 direction 2, the leak #1090 closes) — is
caught by the same inventory: a new cultivar-touching method or module is a
failure regardless of whether it scopes, because "scoped or deliberately
system-context" is a decision that must be recorded, not inferred.

Delimitation: the *behaviour* of the one narrowing path (both #324 directions,
the anonymous ``""`` caller, the bound-not-interpolated tenant value) is pinned in
``test_species_repository_cultivar_tenant_scope.py`` (AQL text) and
``tests/unit/domain/services/test_cultivar_tenant_scope.py`` (observable
visibility). This module pins only that the path stays *alone*, and never
restates those assertions.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import dataclass
from pathlib import Path

import pytest

import app
from app.data_access.arango import collections as col
from app.data_access.arango import species_repository

#: The repository class whose cultivar surface is pinned.
_REPOSITORY_CLASS = "ArangoSpeciesRepository"

#: The shared single-source-of-truth builder for the hybrid-catalogue union
#: (``app.data_access.arango.tenant_scope``). Calling it — rather than inlining a
#: copy — is what makes a *future* second narrowing path agree with this one by
#: construction, which is the whole point of the #816 guard.
_UNION_HELPER = "tenant_union_predicate"

#: An AQL fragment that narrows on the ownership field, e.g. a hand-inlined copy
#: of the union helper. Matched against a function's string literals with its
#: docstring removed, so prose about ``tenant_key ==`` never counts as code.
_INLINE_TENANT_PREDICATE = re.compile(r"\.tenant_key\s*==")

#: The collection name as written in AQL, taken from the constant so a rename
#: moves the guard with it instead of quietly disarming it.
_COLLECTION_NAME = re.compile(rf"\b{re.escape(col.CULTIVARS)}\b")


@dataclass(frozen=True)
class _Surface:
    """A declared cultivar-touching method of the repository.

    Attributes:
        narrows: Whether the method restricts what it reads/writes to a caller's
            tenant. Exactly one method may be ``True`` while the absence form of
            this guard applies.
        why: Why the method is classified that way — the record a reviewer reads
            instead of re-deriving it.
    """

    narrows: bool
    why: str


#: Every method of :class:`ArangoSpeciesRepository` that touches the ``cultivars``
#: collection, with its scope classification. Detected from the source and
#: compared against this declaration: an unregistered method fails the guard.
_DECLARED_CULTIVAR_SURFACE: dict[str, _Surface] = {
    "__init__": _Surface(
        narrows=False,
        why="Binds the ``cultivars`` sub-repository handle; issues no query.",
    ),
    "get_cultivars": _Surface(
        narrows=True,
        why=(
            "THE narrowing read path (C-3). Its scoped branch applies the shared "
            "three-arm hybrid-catalogue union; ``tenant_key=None`` stays the "
            "unscoped system-context read the seed loaders depend on (P5)."
        ),
    ),
    "create_cultivar": _Surface(
        narrows=False,
        why=(
            "Write. Ownership is stamped on the model by the route (#1000) and the "
            "parent species is co-scoped in the service layer (Q3), not here."
        ),
    ),
    "get_cultivar_by_key": _Surface(
        narrows=False,
        why=(
            "System-context single-row load. The ownership check runs *after* the "
            "load in ``SpeciesService.get_cultivar`` so a foreign row and an absent "
            "key are the same 404 — no existence oracle. Narrowing it here would "
            "make the two indistinguishable outcomes distinguishable again."
        ),
    ),
    "get_cultivar_or_raise": _Surface(
        narrows=False,
        why="Same system-context single-row load as ``get_cultivar_by_key``, raising variant.",
    ),
    "update_cultivar": _Surface(
        narrows=False,
        why=(
            "Write. It reads the stored row only to carry the *stored* owner over "
            "the payload (#1090 C-1); the authorization gate lives in the service."
        ),
    ),
    "delete_cultivar": _Surface(
        narrows=False,
        why="Write. Gated in the service (lead-only, REQ-049 §2.3).",
    ),
}

#: Every module under ``app/`` (migrations excluded, see below) that names the
#: ``cultivars`` collection, with why it is allowed to. A new entry means somebody
#: opened a new route to cultivar documents and must say whether it is scoped.
_MODULES_TOUCHING_CULTIVARS: dict[str, str] = {
    "data_access/arango/collections.py": "Declares the collection and its graph edges — the definition, not a read.",
    "data_access/arango/species_repository.py": "Owns the one narrowing read path plus the cultivar CRUD.",
    "data_access/arango/tenant_ownership.py": (
        "Write-path reference guard: ``cultivars`` is on the ownership-verifiable "
        "allowlist so ``plant_instance.cultivar_key`` cannot point at a foreign row "
        "(C-9). It verifies a single supplied key, it does not list."
    ),
    "data_access/arango/plant_instance_repository.py": (
        "``DOCUMENT()`` dereference of a plant's *already tenant-filtered* "
        "``cultivar_key`` to render its name. System context by analysis decision — "
        "the anchor row carries the tenant, the cultivar is only resolved."
    ),
    "domain/engines/calendar_aggregation_engine.py": (
        "Same ``DOCUMENT()`` dereference of an already-anchored ``cultivar_key``, system context by the same decision."
    ),
}

#: ``app/migrations/`` is excluded from the module scan: migrations are one-off
#: maintenance jobs that run outside any request and deliberately see every row
#: (``v0006`` origin backfill, ``v0010`` normalisation, ``v0038`` the cutover
#: itself). ``v0038``'s own scope rules — absent-attribute-only stamping and the
#: executable pin that ``CULTIVARS`` stays out of ``backfill_tenant_key`` — are
#: guarded by ``tests/unit/migrations/versions/test_v0038_cutover_cultivar_tenant_key.py``.
_EXCLUDED_SUBTREE = "migrations"

_APP_ROOT = Path(app.__file__).resolve().parent


# ── source readers: loud on "could not look", never an empty default (T3) ────


def _module_source(module: object) -> str:
    """Return a module's source text, failing loudly when it cannot be read.

    Returning ``""`` for "I could not look" would make every scan below find
    nothing and every inventory comparison fail for the wrong reason — or, if a
    scan were ever phrased as an absence assertion, pass vacuously (T3).
    """
    path = inspect.getsourcefile(module)  # type: ignore[arg-type]
    if path is None:
        raise AssertionError(f"Cannot locate the source file of {module!r} — the scope guard cannot run.")
    text = Path(path).read_text(encoding="utf-8")
    if not text.strip():
        raise AssertionError(f"{path} is empty — the scope guard cannot run against it.")
    return text


def _app_modules() -> list[Path]:
    """Every scanned ``app/`` module path, failing loudly on an empty tree."""
    paths = [
        p
        for p in sorted(_APP_ROOT.rglob("*.py"))
        if _EXCLUDED_SUBTREE not in p.relative_to(_APP_ROOT).parts and "__pycache__" not in p.parts
    ]
    if not paths:
        raise AssertionError(f"No Python modules found under {_APP_ROOT} — the repo-wide scan cannot run.")
    return paths


# ── the detector, applied to real *and* synthetic source below ───────────────


def _code_string_literals(func: ast.FunctionDef) -> list[str]:
    """String literals in ``func``'s body, with its docstring removed.

    The docstring is stripped so prose *about* the tenant predicate (which
    ``get_cultivars`` is full of) is never mistaken for the predicate itself.
    """
    docstring = ast.get_docstring(func, clean=False)
    literals: list[str] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if docstring is not None and node.value == docstring:
                continue
            literals.append(node.value)
    return literals


def _touches_cultivar_collection(func: ast.FunctionDef) -> bool:
    """Whether ``func`` reaches the ``cultivars`` collection at all.

    Three signals, covering the three ways a method can get at the collection:
    the typed sub-repository handle ``self._cultivars``, the collection constant
    ``col.CULTIVARS`` interpolated into hand-written AQL, and the raw collection
    name spelled out in an AQL string. The third matters because bypassing the
    constant is exactly what a hurried new read path does, and it must not buy
    invisibility from this guard.
    """
    if any(isinstance(node, ast.Attribute) and node.attr in ("_cultivars", "CULTIVARS") for node in ast.walk(func)):
        return True
    return any(_COLLECTION_NAME.search(text) for text in _code_string_literals(func))


def _narrows_by_tenant(func: ast.FunctionDef) -> bool:
    """Whether ``func`` restricts what it touches to a caller's tenant.

    Three signals, covering the three shapes a narrowing could take:

    * a call to the shared union helper (the sanctioned shape),
    * an inlined ``<var>.tenant_key ==`` AQL fragment (a copy of the helper), and
    * a ``tenant_key`` parameter (a Python-side post-filter, or any other shape —
      a method that accepts the caller's tenant is making a scope decision).
    """
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            called = node.func
            name = called.id if isinstance(called, ast.Name) else getattr(called, "attr", None)
            if name == _UNION_HELPER:
                return True
    if any(_INLINE_TENANT_PREDICATE.search(text) for text in _code_string_literals(func)):
        return True
    args = func.args
    return any(arg.arg == "tenant_key" for arg in (*args.args, *args.posonlyargs, *args.kwonlyargs))


def cultivar_surface(source: str, class_name: str = _REPOSITORY_CLASS) -> dict[str, bool]:
    """Map every cultivar-touching method of ``class_name`` to whether it narrows.

    Args:
        source: Python source text to scan.
        class_name: The class whose methods are inspected.

    Returns:
        ``{method name: narrows-by-tenant}`` for methods that touch the cultivar
        collection. An empty mapping means the class genuinely has no cultivar
        surface — never "the class was not found", which raises instead.

    Raises:
        AssertionError: ``class_name`` is absent from ``source``. Silently
            returning ``{}`` would turn every assertion below into a comparison
            against nothing (T3).
    """
    tree = ast.parse(source)
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == class_name]
    if not classes:
        raise AssertionError(f"Class {class_name!r} not found in the scanned source — the scope guard cannot run.")
    return {
        node.name: _narrows_by_tenant(node)
        for node in classes[0].body
        if isinstance(node, ast.FunctionDef) and _touches_cultivar_collection(node)
    }


def _modules_naming_the_cultivar_collection() -> dict[str, str]:
    """``{relative module path: source}`` for modules naming the cultivar collection."""
    return {
        path.relative_to(_APP_ROOT).as_posix(): text
        for path in _app_modules()
        if re.search(r"\bCULTIVARS\b", text := path.read_text(encoding="utf-8"))
    }


# ── the guard ────────────────────────────────────────────────────────────────


@pytest.fixture
def surface() -> dict[str, bool]:
    return cultivar_surface(_module_source(species_repository))


class TestCultivarScopeConsistency:
    """Exactly one cultivar read path narrows by tenant — the #816 absence form (Q6).

    See the module docstring for why the absence form applies and what must
    happen when a second narrowing path appears.
    """

    def test_the_repositorys_cultivar_surface_is_the_declared_one(self, surface):
        assert set(surface) == set(_DECLARED_CULTIVAR_SURFACE), (
            "The set of ArangoSpeciesRepository methods touching the cultivars collection "
            f"changed. Detected {sorted(surface)}, declared {sorted(_DECLARED_CULTIVAR_SURFACE)}. "
            "A new cultivar read that forgets the hybrid-catalogue union leaks every tenant's "
            "cultivars (#324 direction 2, the leak #1090 closes); a new one that applies its own "
            "union re-opens the #816 drift risk. Register it in _DECLARED_CULTIVAR_SURFACE with "
            "a rationale — and if it narrows, replace this class with the agreement form."
        )

    def test_exactly_one_cultivar_read_path_narrows_by_tenant(self, surface):
        narrowing = sorted(name for name, narrows in surface.items() if narrows)

        assert narrowing == ["get_cultivars"], (
            f"Expected exactly one narrowing cultivar path, found {narrowing}. "
            "If a second one legitimately exists, the absence form of this guard (operator "
            "decision Q6, #1090) no longer applies: capture the AQL of every narrowing path and "
            "assert their scope predicates are identical, like TestSpeciesScopeConsistencyWhenTenantScoped "
            "does for species (#816). If instead get_cultivars stopped narrowing, the cultivar list "
            "read is leaking again."
        )

    def test_every_method_narrows_exactly_as_declared(self, surface):
        declared = {name: entry.narrows for name, entry in _DECLARED_CULTIVAR_SURFACE.items()}

        assert surface == declared, (
            f"A cultivar-touching method changed its scope classification: detected {surface}, "
            f"declared {declared}. Rationales: "
            + "; ".join(f"{name}: {entry.why}" for name, entry in _DECLARED_CULTIVAR_SURFACE.items())
        )

    def test_the_single_narrowing_path_calls_the_shared_union_helper(self):
        # Not a copy of the AQL-text pin in test_species_repository_cultivar_tenant_scope.py:
        # that one pins *what* the predicate says, this pins *where it comes from*. Routing the
        # single path through the shared helper is what would make a future second path agree
        # with it by construction rather than by review.
        tree = ast.parse(_module_source(species_repository))
        get_cultivars = next(
            node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "get_cultivars"
        )
        calls = {
            node.func.id
            for node in ast.walk(get_cultivars)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }

        assert _UNION_HELPER in calls, (
            f"get_cultivars no longer calls {_UNION_HELPER}. Inlining the union makes it the "
            "fifth hand-written copy of a predicate whose single source of truth exists precisely "
            "so the next consumer cannot drift from it (#324, #816)."
        )


class TestNoOtherModuleReachesTheCultivarCollection:
    """The reach of the cultivar collection across ``app/`` is a declared inventory.

    A method-level scan of one repository cannot see a *new module* opening its
    own route to cultivar documents. This coarse name-level scan can, and is
    immune to query shape: a bound ``@@collection`` variable evades any AQL-text
    pattern, but naming the collection constant does not.
    """

    @pytest.fixture
    def reaching(self) -> dict[str, str]:
        return _modules_naming_the_cultivar_collection()

    def test_only_the_declared_modules_name_the_cultivar_collection(self, reaching):
        assert set(reaching) == set(_MODULES_TOUCHING_CULTIVARS), (
            f"Modules naming the cultivars collection changed: detected {sorted(reaching)}, "
            f"declared {sorted(_MODULES_TOUCHING_CULTIVARS)}. Every route to a cultivar document "
            "must be recorded as scoped or deliberately system-context — an unrecorded one is the "
            "second read path this guard exists to catch (#816 / Q6). Rationales for the current "
            "entries: " + "; ".join(f"{path}: {why}" for path, why in _MODULES_TOUCHING_CULTIVARS.items())
        )

    def test_only_the_species_repository_narrows_the_cultivar_collection(self, reaching):
        narrowing = sorted(path for path, source in reaching.items() if _UNION_HELPER in source)

        assert narrowing == ["data_access/arango/species_repository.py"], (
            f"Modules applying the tenant union to cultivars: {narrowing}. Only the species "
            "repository may — a second one means the absence form of this guard has expired "
            "and the agreement form is owed (#816, operator decision Q6)."
        )


# ── the guard's own falsifiability: the detector must see drift (T8) ─────────

_SECOND_SCOPED_READ = """
class ArangoSpeciesRepository:
    def get_cultivars(self, species_key, *, tenant_key=None):
        predicate, bind_vars = tenant_union_predicate(tenant_key)
        return self._db.aql.execute(f"FOR doc IN {col.CULTIVARS} FILTER {predicate} RETURN doc")

    def count_cultivars(self, species_key, *, tenant_key=None):
        predicate, bind_vars = tenant_union_predicate(tenant_key)
        return self._db.aql.execute(f"FOR doc IN {col.CULTIVARS} FILTER {predicate} COLLECT WITH COUNT INTO n RETURN n")
"""

_INLINED_UNION_COPY = '''
class ArangoSpeciesRepository:
    def get_cultivars(self, species_key, *, tenant_key=None):
        return self._cultivars.find_by_field("species_key", species_key)

    def search_cultivars(self, name):
        """Docstring prose mentioning doc.tenant_key == @tenant_key must not count."""
        return self._db.aql.execute(
            'FOR doc IN cultivars FILTER doc.tenant_key == @t OR doc.tenant_key == "" RETURN doc'
        )
'''

_UNSCOPED_NEW_READ = """
class ArangoSpeciesRepository:
    def get_cultivars(self, species_key, *, tenant_key=None):
        predicate, bind_vars = tenant_union_predicate(tenant_key)
        return self._db.aql.execute(f"FOR doc IN {col.CULTIVARS} FILTER {predicate} RETURN doc")

    def list_all_cultivars(self):
        return self._cultivars.find_by_field("species_key", None)
"""

_UNION_DROPPED = '''
class ArangoSpeciesRepository:
    def get_cultivars(self, species_key):
        """Once documented as tenant-scoped: doc.tenant_key == @tenant_key."""
        return self._cultivars.find_by_field("species_key", species_key)
'''


class TestTheScopeScannerItselfDetectsDrift:
    """Non-vacuity of the guard above: the detector reports each drift shape.

    Every case below is a source snippet the real repository could become. Without
    these, a detector that quietly stopped recognising cultivar methods would make
    :class:`TestCultivarScopeConsistency` pass forever with an empty surface —
    the exact "the check does less than it claims" failure this package exists to
    rule out.
    """

    def test_a_second_scoped_read_path_is_reported_as_narrowing(self):
        assert cultivar_surface(_SECOND_SCOPED_READ) == {"get_cultivars": True, "count_cultivars": True}

    def test_an_inlined_union_copy_counts_as_narrowing_but_a_docstring_does_not(self):
        surface = cultivar_surface(_INLINED_UNION_COPY)

        assert surface == {"get_cultivars": True, "search_cultivars": True}

    def test_prose_alone_never_makes_a_method_look_scoped(self):
        # The mirror of the case above: the same predicate text, but only in the
        # docstring. A detector fooled by prose would certify an unscoped read.
        assert cultivar_surface(_UNION_DROPPED) == {"get_cultivars": False}

    def test_a_new_unscoped_read_shows_up_as_an_unregistered_surface_method(self):
        surface = cultivar_surface(_UNSCOPED_NEW_READ)

        assert set(surface) - set(_DECLARED_CULTIVAR_SURFACE) == {"list_all_cultivars"}
        assert surface["list_all_cultivars"] is False

    def test_a_dropped_union_makes_the_known_path_stop_narrowing(self):
        assert cultivar_surface(_UNION_DROPPED)["get_cultivars"] is False

    def test_the_scanner_fails_loudly_when_the_class_is_gone(self):
        # T3: a renamed or moved repository must not silently produce an empty
        # surface that every inventory assertion then "agrees" with.
        with pytest.raises(AssertionError, match="not found in the scanned source"):
            cultivar_surface("class SomethingElse:\n    pass\n")

    def test_a_class_without_cultivars_yields_an_empty_surface_not_an_error(self):
        # The honest empty case, kept distinct from "could not look" above.
        assert cultivar_surface("class ArangoSpeciesRepository:\n    def get_all(self):\n        return []\n") == {}
