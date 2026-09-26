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
    "get_or_raise_by": (1, "entity_name"),
    "_authorize_tenant_owned_write": (None, "entity"),
    "_require_owned_site": (2, "entity_name"),
}

#: Non-literal entity-name arguments, keyed by ``<module>::<unparsed expression>``,
#: with the reason the value cannot leave the vocabulary. Every entry states what
#: constrains it — "it looked fine" is not one of the reasons.
DERIVED_ENTITY_SITES: dict[str, str] = {
    "app/domain/services/ha_publish_service.py::name": (
        "``_ENTITY_NAMES[entity_type]`` — a closed map of the three publishable types to published "
        "entity names (PlantInstance, Tank, Location); #1872 C8."
    ),
    "app/domain/services/ai_assistant_service.py::name": (
        "Unpacked from ``self._context_owners``, a closed map of the two entity context types to "
        "published entity names (PlantInstance, PlantingRun); #1872 C9."
    ),
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
    """Map every local name bound to a checked callable back to its real name.

    Two bindings, not one: ``from … import NotFoundError as NFE`` **and** a plain
    ``E = NotFoundError`` at module level. Reading only the import form leaves the
    assignment as a silent bypass — the guard would see a call to ``E`` and have
    no opinion about it.
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name in ENTITY_NAME_ARGUMENTS:
                    aliases[alias.asname or alias.name] = alias.name
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Name):
            real = aliases.get(node.value.id, node.value.id)
            if real in ENTITY_NAME_ARGUMENTS:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        aliases[target.id] = real
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


def _base_name(base: ast.expr) -> str:
    """The trailing name of a base expression — ``exc.NotFoundError`` included.

    A module-qualified base is the same class as a bare one, and reading only
    ``ast.Name`` would let ``class FooNotFoundError(exc.NotFoundError)`` hard-code
    an entity name the guard never sees.
    """
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return ""


def _not_found_subclasses(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and any(_base_name(base).endswith("NotFoundError") for base in node.bases)
    }


def _entity_arguments(tree: ast.Module) -> list[tuple[int, ast.expr | None]]:
    """Every expression that reaches ``details[0].entity`` in this module."""
    aliases = _module_aliases(tree)
    subclasses = _not_found_subclasses(tree)
    found: list[tuple[int, ast.expr | None]] = []

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
        if index is not None and len(node.args) > index and not _has_spread(node):
            found.append((node.lineno, node.args[index]))
            continue
        named = [kw.value for kw in node.keywords if keyword is not None and kw.arg == keyword]
        if named:
            found.append((node.lineno, named[0]))
            continue
        if _has_spread(node):
            # ``NotFoundError(**payload)`` / ``NotFoundError(*args)``: the entity
            # name is in there somewhere and nothing here can see it. Reported as
            # ``None`` — a shape the guard cannot check is not a shape it may pass.
            found.append((node.lineno, None))
    return found


def _has_spread(call: ast.Call) -> bool:
    return any(isinstance(arg, ast.Starred) for arg in call.args) or any(kw.arg is None for kw in call.keywords)


def _enclosing_function(tree: ast.Module, target: ast.AST) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    innermost: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and any(
            child is target for child in ast.walk(node)
        ):
            innermost = node if innermost is None or node.lineno > innermost.lineno else innermost
    return innermost


def _parameter_is_registered(function: ast.FunctionDef | ast.AsyncFunctionDef, parameter: str) -> bool:
    """Is forwarding ``parameter`` out of ``function`` covered by a call-site check?

    A bare parameter name at a raiser is only as checked as the *callers* of the
    function holding it. Requiring an explicit reason ("call sites are checked")
    would be a sentence anyone can write; this measures the claim: the function
    must be registered in :data:`ENTITY_NAME_ARGUMENTS`, **and** the registration
    must point at this very parameter. Otherwise a new local wrapper
    (``def _missing(name, key): raise NotFoundError(name, key)``) becomes a
    laundering route that reads as declared.
    """
    spec = ENTITY_NAME_ARGUMENTS.get(function.name)
    if spec is None:
        return False
    index, keyword = spec
    positional = [arg.arg for arg in function.args.args]
    if positional and positional[0] in {"self", "cls"}:
        positional = positional[1:]
    if index is not None and index < len(positional) and positional[index] == parameter:
        return True
    return keyword == parameter and parameter in {arg.arg for arg in function.args.kwonlyargs} | set(positional)


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
            if expr is None:
                violations.append(
                    f"{relative}:{lineno}: the entity name arrives through *args/**kwargs, so nothing can "
                    f"check it — pass it explicitly"
                )
                continue
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

            # A forwarded *parameter* is checked before the declaration is even
            # read: a wrapper that is not registered has unchecked callers, and
            # a DERIVED_ENTITY_SITES entry claiming otherwise is the laundering
            # route this arm exists to close.
            function = _enclosing_function(tree, expr) if isinstance(expr, ast.Name) else None
            if (
                isinstance(expr, ast.Name)
                and function is not None
                and expr.id in _function_parameters(function)
                and not _parameter_is_registered(function, expr.id)
            ):
                violations.append(
                    f"{relative}:{lineno}: {source!r} is a parameter of {function.name}(), which is not "
                    f"registered in ENTITY_NAME_ARGUMENTS — its callers are therefore unchecked, whatever "
                    f"the DERIVED_ENTITY_SITES entry says"
                )
                continue

            if f"{relative}::{source}" not in DERIVED_ENTITY_SITES:
                violations.append(
                    f"{relative}:{lineno}: entity name is the non-literal {source!r} with no entry in "
                    f"DERIVED_ENTITY_SITES — derive it from a model or state what constrains it"
                )
    return violations


def _function_parameters(function: ast.FunctionDef | ast.AsyncFunctionDef | None) -> set[str]:
    if function is None:
        return set()
    args = function.args
    return {arg.arg for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]}


def test_every_entity_name_site_is_vocabulary_or_declared_derivation() -> None:
    assert collect_violations(APP_ROOT) == []


def test_guard_sees_the_spellings_it_claims_to_see(tmp_path: Path) -> None:
    """The predicate is not vacuous: every spelling it claims is actually reached.

    Eleven shapes — the eight the tree held before this change (plural, prose, a
    keyword raiser, an aliased import, a class attribute, a module constant, a
    subclass ``super().__init__``, a bare run-time expression) and the three a
    review named as silent bypasses: a ``**kwargs`` spread, a *locally* bound
    alias (``E = NotFoundError``, which no import statement mentions) and a
    subclass whose base is module-qualified (``exc.NotFoundError``). Every one
    must be reported; if a shape stops being, the guard has narrowed without
    saying so.
    """
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "sample.py").write_text(
        "from app.common import exceptions as exc\n"
        "from app.common.exceptions import NotFoundError as NFE\n"
        "E = NFE\n"
        '_ENTITY = "membership records"\n'
        "def a(key):\n"
        '    raise NFE("tenants", key)\n'
        "def b(key):\n"
        '    raise NFE(entity="LifecycleConfig for species", key=key)\n'
        "def c(key, row):\n"
        "    collection = row.collection\n"
        "    raise NFE(collection, key)\n"
        "def d(key):\n"
        "    raise NFE(_ENTITY, key)\n"
        "def e(resource, tenant_key):\n"
        '    verify_tenant_ownership(resource, tenant_key, "memberships")\n'
        "def f(payload):\n"
        "    raise NFE(**payload)\n"
        "def g(key):\n"
        '    raise E("invitations", key)\n'
        "def h(name, key):\n"
        "    raise NFE(name, key)\n"
        "class Repo:\n"
        '    _entity_name = "tenants"\n'
        "class ThingNotFoundError(NotFoundError):\n"
        "    def __init__(self, key):\n"
        '        super().__init__("thing records", key)\n'
        "class OtherNotFoundError(exc.NotFoundError):\n"
        "    def __init__(self, key):\n"
        '        super().__init__("other records", key)\n',
        encoding="utf-8",
    )

    violations = collect_violations(tmp_path / "app")
    reported = " ".join(violations)

    for expected in (
        "'tenants'",  # a plural of a model, and again as a _entity_name attribute
        "'LifecycleConfig for species'",  # prose, through the keyword form
        "'membership records'",  # a module constant, resolved
        "'memberships'",  # a shared guard's entity-name parameter
        "'thing records'",  # a subclass hard-coding its own name
        "'other records'",  # …with a module-qualified base
        "'invitations'",  # reached only through the locally bound alias
        "non-literal 'collection'",  # a local bound at run time
        "*args/**kwargs",  # a spread the guard cannot see into
        "is a parameter of h()",  # an unregistered local wrapper laundering a name
    ):
        assert expected in reported, (expected, violations)
    assert len(violations) == 11, violations


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
    # prose-permeable: the subject is a Markdown table in NFR-006 — the spec prose is exactly what is being compared
    # with the code
    listed = set(re.findall(r"^\|\s*`([a-z_]+)`\s*\|", rows, flags=re.MULTILINE))

    assert listed == set(NON_MODEL_ENTITY_NAMES)


def _collection_constant_values() -> dict[str, str]:
    """``collections.py``'s module-level ``NAME = "value"`` constants."""
    from app.data_access.arango import collections as col

    return {name: value for name, value in vars(col).items() if not name.startswith("_") and isinstance(value, str)}


def _collections_reaching_the_fallback() -> dict[str, set[str]]:
    """Every collection that can reach ``entity_name_for_collection`` at run time.

    Four routes, swept from the code rather than remembered:

    * a ``raw=True`` repository construction — a model-less repository, whose
      ``_require_entity_name()`` has nothing but its collection to go on;
    * :data:`OWNERSHIP_VERIFIABLE_COLLECTIONS`, the shared write-path guard's
      allowlist, whose callers may omit ``entity_name``;
    * ``_owned_reference_fields`` targets, the declarative variant of the same
      guard, which never passes a name;
    * ``ENTITY_TYPE_TO_COLLECTION``, the task entity binding.
    """
    constants = _collection_constant_values()
    routes: dict[str, set[str]] = {"raw repository": set()}

    def resolve(node: ast.expr | None) -> str | None:
        if isinstance(node, ast.Attribute) and node.attr in constants:
            return constants[node.attr]
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else "")
            qualifier = func.value.id if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) else ""
            constructed = qualifier if called == "__init__" else called
            if "Repository" not in constructed:
                continue
            raw = any(kw.arg == "raw" and isinstance(kw.value, ast.Constant) and kw.value.value for kw in node.keywords)
            if not raw:
                continue
            # ``Repo.__init__(self, db, collection, …)`` carries ``self``; the
            # constructor form does not.
            collection = resolve(node.args[2] if called == "__init__" else node.args[1] if len(node.args) > 1 else None)
            if collection is not None:
                routes["raw repository"].add(collection)

    from app.data_access.arango.task_repository import ENTITY_TYPE_TO_COLLECTION
    from app.data_access.arango.tenant_ownership import OWNERSHIP_VERIFIABLE_COLLECTIONS

    routes["ownership allowlist"] = set(OWNERSHIP_VERIFIABLE_COLLECTIONS)
    routes["task entity binding"] = set(ENTITY_TYPE_TO_COLLECTION.values())

    declared: set[str] = set()
    for path in sorted((APP_ROOT / "data_access").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for node in ast.walk(tree):
            targets = node.targets if isinstance(node, ast.Assign) else []
            if not any(isinstance(t, ast.Name) and t.id == "_owned_reference_fields" for t in targets):
                continue
            if isinstance(node.value, ast.Dict):
                declared.update(filter(None, (resolve(value) for value in node.value.values)))
    routes["declared owned reference"] = declared
    return routes


def test_the_collection_table_covers_every_collection_that_reaches_it() -> None:
    """The fallback must be unreachable in practice, and that is measured.

    ``outside <= {"resource"}`` — the first shape of this test — is true of an
    *empty* table: it asserts the fallback returns the fallback. What matters is
    that nothing real lands on it, so this sweeps the four routes into
    ``entity_name_for_collection`` and requires each collection to be a key. It
    is the test that found ``onboarding_states``, ``user_preferences``,
    ``phase_definitions`` and ``starter_kits`` publishing ``resource`` while
    their models sat one import away.
    """
    from app.data_access.arango.collection_entity_names import COLLECTION_ENTITY_MODELS

    routes = _collections_reaching_the_fallback()
    for route, collections in routes.items():
        assert collections, f"the sweep for {route!r} found nothing — the shape it looks for changed"

    reaching = set().union(*routes.values())
    unmapped = sorted(reaching - set(COLLECTION_ENTITY_MODELS))
    assert unmapped == [], f"these reach entity_name_for_collection and fold to 'resource': {unmapped}"


def test_the_collection_table_only_ever_yields_vocabulary() -> None:
    """Whatever the table answers is a published name, mapped or not.

    The complement of the sweep above: that one says nothing *real* reaches the
    fallback, this one says the fallback — and every mapped answer — is still a
    value a client may receive.
    """
    from app.data_access.arango.collection_entity_names import COLLECTION_ENTITY_MODELS, entity_name_for_collection

    every_collection = set(_collection_constant_values().values())
    assert COLLECTION_ENTITY_MODELS.keys() <= every_collection, "the table names something that is not a collection"
    assert {entity_name_for_collection(name) for name in every_collection} <= entity_names()


#: Entity names a *test* may spell that production may not, with the reason. A
#: test-local model exists to exercise the machinery and has no place in a
#: published vocabulary; anything else here would be a double inventing a shape
#: production cannot emit.
TEST_LOCAL_ENTITY_NAMES: dict[str, str] = {
    "gadget": (
        "``NamedRepo._entity_name`` in tests/unit/data_access/arango/"
        "test_base_repository.py — a synthetic repository over the synthetic "
        "``Widget`` model, proving that an explicit name wins over the bound "
        "class. Both are test-local by design."
    ),
}


def test_test_doubles_spell_entity_names_the_way_production_does() -> None:
    """A double that raises a retired spelling certifies a shape nothing emits.

    Seventeen doubles mimicking a changed raiser were corrected by hand for
    #1465 — by hand, which is exactly the method that produced the 59 spellings.
    Literals only: a double legitimately holds run-time expressions and
    test-local models, and demanding a `DERIVED_ENTITY_SITES` entry for each
    would make this a nuisance instead of a check.
    """

    def is_test_local(line: str) -> bool:
        return any(f"to {name!r}" in line for name in TEST_LOCAL_ENTITY_NAMES)

    violations = [
        line
        for line in collect_violations(APP_ROOT.parent / "tests")
        if "normalises to" in line and not is_test_local(line)
    ]
    assert violations == []


def test_spec_additivity_table_names_values_that_really_changed() -> None:
    """NFR-006 §2.2a tables nine old → new values; both halves are checked.

    A migration note is the one place a wrong value is *invisible*: nothing reads
    it, so nothing contradicts it. An entry whose "old" value is still published
    would be a false alarm for every integrator, and one whose "new" value is not
    in the vocabulary would send them to a value they will never receive.
    """
    root = _repo_root()
    if root is None:  # pragma: no cover — only outside a full checkout
        pytest.skip("checkout root not found; spec/ is unreachable from here")

    spec = (root / "spec" / "nfr" / "NFR-006_API-Fehlerbehandlung.md").read_text(encoding="utf-8")
    section = spec.split("**Additivität.**", 1)[1].split("Dazu die Collection-Namen", 1)[0]
    # prose-permeable: the subject is a Markdown table in NFR-006 — the spec prose is exactly what is being compared
    # with the code
    rows = re.findall(r"^\|\s*`([a-z_]+)`\s*\|\s*`([a-z_]+)`\s*\|", section, flags=re.MULTILINE)

    assert len(rows) >= 9, rows
    assert [old for old, _ in rows if old in entity_names()] == []
    assert [new for _, new in rows if new not in entity_names()] == []


def test_no_repository_restates_its_own_model_name() -> None:
    """``_entity_name`` exists to *differ* from the bound model, never to repeat it.

    Five repositories declared ``_model_cls = Actuator`` and
    ``_entity_name = "Actuator"`` next to each other. Harmless until the model is
    renamed, at which point the derivation follows and the string does not — a
    second spelling of one fact, which is the whole defect class #1465 closes.
    """
    restated: list[str] = []
    for path in sorted((APP_ROOT / "data_access").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            declared: dict[str, ast.expr] = {}
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    declared[stmt.targets[0].id] = stmt.value
            model = declared.get("_model_cls")
            name = declared.get("_entity_name")
            if isinstance(model, ast.Name) and isinstance(name, ast.Constant) and name.value == model.id:
                restated.append(f"{path.name}:{node.name} declares _entity_name = {name.value!r} = _model_cls.__name__")
    assert restated == []
