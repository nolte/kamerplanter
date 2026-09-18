"""``details[0].entity`` is a closed vocabulary at every raiser site (#1465, NFR-006 §2.2a).

Why an AST guard rather than a convention. The field became machine-readable in
#1437 and was measured, over the tree, one issue later: 146 literal
``NotFoundError`` sites spelling **59** distinct names — prose
(``"LifecycleConfig for species"``), plurals (``"tenants"``, ``"memberships"``)
and case variants — plus 17 sites handing in a run-time *collection* name. A
client branching on ``entity === "tenant"`` missed six raisers, and nothing in
the tree would have told anybody.

What is checked, and why each spelling is here rather than "the obvious one":

* ``NotFoundError("X", key)`` — the plain site.
* ``NotFoundError(entity="X", key=…)`` — three notification routes spell it as a
  keyword. A positional-only sweep reports them as *dynamic* and moves on, which
  is how the first count of this issue came out at 9 rather than 17.
* ``raise NFE(...)`` after ``import … as NFE`` — an alias defeats a name match,
  so the aliases are read out of each module's imports.
* ``class FooNotFoundError(NotFoundError)`` — a subclass hard-codes the name in
  its own ``super().__init__``; the raiser then names no entity at all.
* ``_entity_name = "Actuator"`` — repositories declare the name as a class
  attribute that ``BaseArangoRepository._require_entity_name`` feeds to the
  raiser, so the literal is a file away from any ``NotFoundError(``.
* ``NotFoundError(_ENTITY, key)`` — a module-level constant; resolved rather
  than waved through, since it is a literal with one extra hop.
* The entity-name **parameters** of the shared guards
  (``verify_tenant_ownership``, ``verify_entity_ownership(entity_name=)``,
  ``require_owned_site``, …). Their value reaches ``details[0].entity``
  unchanged, so a bad literal there is as published as a bad literal at the
  raiser.

Anything else non-literal must be listed in :data:`DERIVED_ENTITY_SITES` with
the reason its value is constrained — an f-string, a bare request field or a new
run-time expression fails until somebody says why it is safe.

Known limit, stated rather than hidden: the guard is syntactic. A literal
assigned to a local variable, passed through a helper this module does not know
about, or read out of a dict fails as "underived" — it cannot be laundered into
silence, but it also cannot be *checked*, so it needs an entry here.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from app.common.exceptions import normalise_entity_name
from app.domain.entity_names import NON_MODEL_ENTITY_NAMES, entity_names

APP_ROOT = Path(__file__).resolve().parents[3] / "app"

#: Functions whose argument lands in ``details[0].entity`` verbatim, as
#: ``{function name: (positional index or None, keyword or None)}``.
ENTITY_NAME_ARGUMENTS: dict[str, tuple[int | None, str | None]] = {
    "NotFoundError": (0, "entity"),
    "verify_tenant_ownership": (2, "resource_name"),
    "verify_tenant_read_access": (2, "resource_name"),
    "require_owned_site": (3, "entity_name"),
    "verify_entity_ownership": (None, "entity_name"),
    "verify_entities_ownership": (None, "entity_name"),
    "get_or_raise_named": (None, "entity_name"),
    "_authorize_tenant_owned_write": (None, "entity"),
    "_require_owned_site": (2, "entity_name"),
}

#: Non-literal entity-name arguments, keyed by ``<module>::<unparsed expression>``,
#: with the reason the value cannot leave the vocabulary. Every entry states what
#: constrains it — "it looked fine" is not one of the reasons.
DERIVED_ENTITY_SITES: dict[str, str] = {
    "app/data_access/arango/base_repository.py::self._require_entity_name()": (
        "Derived from the bound model class, or from the collection table for a "
        "model-less repository — both vocabulary by construction."
    ),
    "app/data_access/arango/base_repository.py::entity_name": (
        "``get_or_raise_named``'s own parameter; its call sites are checked through ENTITY_NAME_ARGUMENTS."
    ),
    "app/data_access/arango/tenant_ownership.py::name": (
        "``entity_name or entity_name_for_collection(collection)`` — the "
        "parameter is checked at its call sites, the fallback is table-derived."
    ),
    "app/data_access/arango/inventree_repository.py::entity_name_for_collection(entity_collection)": (
        "Table lookup; a caller-supplied collection that is not in the table folds to the fail-closed ``resource``."
    ),
    "app/domain/services/favorites_service.py::entity_name_for_collection(target_collection)": (
        "Table lookup over the resolver's own fixed collection list."
    ),
    "app/domain/services/task_entity_guard.py::entity_name_for_collection(ENTITY_TYPE_TO_COLLECTION[entity_type])": (
        "Table lookup keyed by ENTITY_TYPE_TO_COLLECTION, which the guard has already membership-tested."
    ),
    "app/common/tenant_guard.py::resource_name": (
        "The guards' own parameter; call sites are checked through ENTITY_NAME_ARGUMENTS."
    ),
    "app/domain/services/location_ownership.py::entity_name": (
        "``require_owned_site``'s own parameter; call sites are checked through ENTITY_NAME_ARGUMENTS."
    ),
    "app/data_access/arango/tenant_ownership.py::entity_name": (
        "``verify_entities_ownership`` forwarding its own parameter to the "
        "single-key variant; call sites are checked through "
        "ENTITY_NAME_ARGUMENTS."
    ),
    "app/domain/services/plant_instance_service.py::entity_name": (
        "``_require_owned_site``'s own parameter, forwarded to the shared "
        "anchor; its two call sites are checked through ENTITY_NAME_ARGUMENTS."
    ),
    "app/domain/services/species_service.py::entity": (
        "``_authorize_tenant_owned_write``'s own parameter; call sites are checked through ENTITY_NAME_ARGUMENTS."
    ),
}


def _module_aliases(tree: ast.Module) -> dict[str, str]:
    """Map every local name bound to a checked callable back to its real name."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in ENTITY_NAME_ARGUMENTS:
                    aliases[alias.asname or alias.name] = alias.name
    return aliases


def _module_string_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level ``NAME = "literal"`` assignments, so ``_ENTITY`` resolves."""
    constants: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    constants[target.id] = node.value.value
    return constants


def _not_found_subclasses(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and any(isinstance(base, ast.Name) and base.id.endswith("NotFoundError") for base in node.bases)
    }


def _entity_arguments(tree: ast.Module) -> list[tuple[int, ast.expr]]:
    """Every expression that reaches ``details[0].entity`` in this module."""
    aliases = _module_aliases(tree)
    subclasses = _not_found_subclasses(tree)
    found: list[tuple[int, ast.expr]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # ``_entity_name = "Actuator"`` — the repository's declared name.
            for stmt in node.body:
                targets = (
                    stmt.targets
                    if isinstance(stmt, ast.Assign)
                    else [stmt.target]
                    if isinstance(stmt, ast.AnnAssign) and stmt.value is not None
                    else []
                )
                value = stmt.value if isinstance(stmt, ast.Assign | ast.AnnAssign) else None
                declares_name = any(isinstance(t, ast.Name) and t.id == "_entity_name" for t in targets)
                # ``_entity_name: ClassVar[str | None] = None`` on the base class is
                # the "unset" default, not a published name.
                is_none = isinstance(value, ast.Constant) and value.value is None
                if value is not None and declares_name and not is_none:
                    found.append((stmt.lineno, value))

        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            name = aliases.get(func.id, func.id)
        elif isinstance(func, ast.Attribute):
            name = func.attr
        else:
            continue

        # A subclass hard-codes the name in its own ``super().__init__``.
        if name == "__init__" and isinstance(func.value, ast.Call) and _is_super_call(func.value):
            enclosing = _enclosing_class(tree, node)
            if enclosing is not None and enclosing in subclasses and node.args:
                found.append((node.lineno, node.args[0]))
            continue

        spec = ENTITY_NAME_ARGUMENTS.get(name)
        if spec is None:
            continue
        index, keyword = spec
        if index is not None and len(node.args) > index:
            found.append((node.lineno, node.args[index]))
            continue
        for kw in node.keywords:
            if keyword is not None and kw.arg == keyword:
                found.append((node.lineno, kw.value))
    return found


def _is_super_call(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Name) and call.func.id == "super"


def _enclosing_class(tree: ast.Module, target: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and any(child is target for child in ast.walk(node)):
            return node.name
    return None


def collect_violations(root: Path) -> list[str]:
    """Every entity-name expression under ``root`` that is not vocabulary-bound."""
    violations: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        constants = _module_string_constants(tree)
        relative = path.relative_to(root.parent).as_posix()
        for lineno, expr in _entity_arguments(tree):
            literal: str | None = None
            if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
                literal = expr.value
            elif isinstance(expr, ast.Name) and expr.id in constants:
                literal = constants[expr.id]

            if literal is not None:
                if normalise_entity_name(literal) not in entity_names():
                    violations.append(
                        f"{relative}:{lineno}: entity name {literal!r} normalises to "
                        f"{normalise_entity_name(literal)!r}, which is not in the vocabulary "
                        f"(app/domain/entity_names.py)"
                    )
                continue

            source = ast.unparse(expr)
            if f"{relative}::{source}" not in DERIVED_ENTITY_SITES:
                violations.append(
                    f"{relative}:{lineno}: entity name is the non-literal {source!r} with no entry in "
                    f"DERIVED_ENTITY_SITES — derive it from a model or state what constrains it"
                )
    return violations


def test_every_entity_name_site_is_vocabulary_or_declared_derivation() -> None:
    assert collect_violations(APP_ROOT) == []


def test_guard_sees_the_spellings_it_claims_to_see(tmp_path: Path) -> None:
    """The predicate is not vacuous: each spelling is actually reached.

    Written against the shapes the tree held **before** this change — a plural,
    prose, a keyword raiser, an alias, a subclass, a class attribute, a module
    constant and a bare run-time expression. All eight must be reported; if one
    stops being, the guard has silently narrowed.
    """
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "sample.py").write_text(
        "from app.common.exceptions import NotFoundError as NFE\n"
        '_ENTITY = "membership records"\n'
        "def a(key):\n"
        '    raise NFE("tenants", key)\n'
        "def b(key):\n"
        '    raise NFE(entity="LifecycleConfig for species", key=key)\n'
        "def c(key, collection):\n"
        "    raise NFE(collection, key)\n"
        "def d(key):\n"
        "    raise NFE(_ENTITY, key)\n"
        "def e(resource, tenant_key):\n"
        '    verify_tenant_ownership(resource, tenant_key, "memberships")\n'
        "class Repo:\n"
        '    _entity_name = "tenants"\n'
        "class ThingNotFoundError(NotFoundError):\n"
        "    def __init__(self, key):\n"
        '        super().__init__("thing records", key)\n',
        encoding="utf-8",
    )

    violations = collect_violations(tmp_path / "app")
    reported = " ".join(violations)

    assert len(violations) == 7, violations
    for expected in (
        "'tenants'",
        "'LifecycleConfig for species'",
        "'membership records'",
        "'memberships'",
        "'thing records'",
    ):
        assert expected in reported, (expected, violations)
    assert "non-literal 'collection'" in reported


def test_vocabulary_is_snake_case_and_idempotent() -> None:
    """Every published name is already the normaliser's own output.

    Which is what makes ``entity`` comparable at all: a client that received
    ``plant_instance`` and a raiser that writes ``PlantInstance`` must land on
    the same string, and feeding a published value back through the normaliser
    must not move it.
    """
    unstable = {name for name in entity_names() if normalise_entity_name(name) != name}
    assert unstable == set()


def test_no_published_name_is_the_plural_of_another() -> None:
    """The defect this issue is named after, as a property of the set.

    ``"tenants"`` next to ``"tenant"`` is what made ``entity === "tenant"`` miss
    six raisers. Deriving the vocabulary from model classes already excludes a
    collection name — this states the consequence, so an exception entry cannot
    reintroduce one by hand.
    """
    names = entity_names()
    plurals = {name for name in names if name.endswith("s") and name[:-1] in names}
    assert plurals == set()


def _repo_root() -> Path | None:
    """The checkout root, by marker walk — a ``parents[N]`` index breaks on a move."""
    start = Path(__file__).resolve()
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "spec").is_dir():
            return candidate
    return None


def test_every_repository_bound_model_is_in_the_vocabulary() -> None:
    """``_require_entity_name()`` publishes whatever model a repository binds.

    That derivation is waved through in :data:`DERIVED_ENTITY_SITES` as
    "vocabulary by construction"; this measures the claim instead of trusting it.
    109 models are bound today, and an explicit 60-name list — the first shape of
    this vocabulary — would have been a contract the code already broke.
    """
    bound: set[str] = set()
    for path in sorted((APP_ROOT / "data_access" / "arango").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Name)
                and any(isinstance(t, ast.Name) and t.id == "_model_cls" for t in node.targets)
            ):
                bound.add(node.value.id)
            if isinstance(node, ast.Call) and len(node.args) >= 3 and isinstance(node.args[2], ast.Name):
                func = node.func
                base = func.value if isinstance(func, ast.Subscript) else func
                if isinstance(base, ast.Name) and base.id.endswith("Repository"):
                    bound.add(node.args[2].id)

    assert len(bound) > 50, f"the sweep found only {len(bound)} bound models — the shape it looks for changed"
    missing = sorted(name for name in bound if normalise_entity_name(name) not in entity_names())
    assert missing == []


def test_spec_lists_exactly_the_non_model_exceptions() -> None:
    """NFR-006 §2.2a names the hand-written entries, and only those.

    The spec deliberately does *not* list the model-derived names — that is the
    rule, not a table, and a copy of 260 names in prose is the drift this whole
    issue is about. What it does carry is the nine exceptions, each with its
    reason, so this pins the two against each other.
    """
    root = _repo_root()
    if root is None:  # pragma: no cover — only outside a full checkout
        pytest.skip("checkout root not found; spec/ is unreachable from here")

    spec = (root / "spec" / "nfr" / "NFR-006_API-Fehlerbehandlung.md").read_text(encoding="utf-8")
    section = spec.split("Die Ausnahmen", 1)[1].split("**Additivität.**", 1)[0]
    # After the header separator, so the ``| `entity` |`` column title is not
    # mistaken for a vocabulary entry.
    rows = section.split("|---|---|", 1)[1]
    listed = set(re.findall(r"^\|\s*`([a-z_]+)`\s*\|", rows, flags=re.MULTILINE))

    assert listed == set(NON_MODEL_ENTITY_NAMES)
