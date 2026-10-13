"""#1561 class guard — hand-written AQL over a hybrid catalogue must name a tenant.

The defect this file exists for: ``FavoritesService.get_matching_nutrient_plans``
took a ``tenant_key`` and ran its query **without** ``bind_vars``. Its only filter
was ``is_template == true OR origin == "system"``, so every row any tenant flagged
as a template was served to any authenticated caller of any tenant, with the
product name and brand of every fertilizer it used. Nothing raised, nothing logged,
and the parameter in the signature made the call site read as if it were scoped.

**The class, stated as a rule and not as today's literal value** (the failure PR
#1608 had to repair): *every* ``FOR <var> IN <catalogue>`` loop of a hand-written
AQL read must carry a tenant predicate **on that loop variable** — a comparison
``<var>.tenant_key ==`` / ``!=`` / ``IN`` in the query text, or a
:mod:`~app.data_access.arango.tenant_scope` builder called with
``doc_var="<var>"`` (directly, or in a same-class helper the function calls).

**Why per loop variable (#2120, MT-024).** Until 2026-10-05 the rule was "the query
text names ``tenant_key`` somewhere". Two things made that weaker than it read:

* An f-string placeholder became ``<<EXPR>>``, so ``FOR doc IN {col.SPECIES}`` —
  the spelling almost every repository uses — named **no** catalogue. The guard saw
  3 of the 27 catalogue reads it claimed to cover; the other 24 were never asked.
  Placeholders of the shape ``{col.X}`` now resolve to the collection name.
* One predicate satisfied every loop in the query. ``list_template_plan_summaries``
  scoped ``plan`` and then resolved the name and brand of every fertilizer its
  entries named through an unscoped ``FOR f IN fertilizers`` — a legacy entry
  holding another tenant's fertilizer key read that tenant's product (the #952
  shape). A mention in a projection (``RETURN {tenant_key: d.tenant_key}``) counted
  too.

The catalogue set is
:data:`~app.domain.services.favorites_service._TENANT_OWNED_CATALOG_COLLECTIONS`,
which ``test_favoritable_collections_declare_ownership.py`` holds equal to the set
of models that actually declare ``tenant_key`` — so this guard inherits a set
derived from the models rather than carrying a fourth hand-list that can drift.

**Query-text resolution.** A query reaches ``aql.execute`` in more spellings than
one, and a sweep that knows only one of them looks complete while missing sites —
this repository has paid for that twice (a regex that demanded a string literal,
a glob that assumed a name prefix). Resolved here: an inline literal, an f-string
(a ``{col.X}`` placeholder becomes the collection name, any other placeholder
``<<EXPR>>``), implicit and ``+`` concatenation, a name assigned anywhere in the
same function or at module level, and the receiver of a trailing
``.replace``/``.format``/``.join`` — which is the spelling the #1561 repair itself
uses to splice its predicate in.

**Spellings this does NOT match**, named rather than discovered later:

* a query assembled from a *parameter* or a class attribute, or one returned by
  a helper (a module-level constant **is** resolved since #1664) — these resolve to nothing and are **reported**
  (:data:`_UNRESOLVED_IS_A_FINDING`), not silently skipped, because "I could not
  read it" and "it is fine" are different answers;
* a collection named only through a bind variable (``FOR d IN @@collection``) —
  the loop names no catalogue, so no rule fires;
* AQL that reaches the catalogue through a **graph traversal** or an edge whose
  ``_to`` lands in one (``FOR v IN 1..1 OUTBOUND …``) rather than through
  ``FOR x IN <collection>`` — ``test_tenant_scoped_reads_are_derived.py`` counts a
  traversal's vertex collection as touched (#2102);
* a predicate spliced from a builder called in **another** class or module, or with
  a ``doc_var`` that is not a string literal — the loop then counts as unscoped.

``app/migrations/`` is out of scope on purpose: a migration runs in the system
context and is *required* to see every tenant's rows.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango import tenant_scope
from app.domain.services.favorites_service import _TENANT_OWNED_CATALOG_COLLECTIONS
from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: Migrations read across tenants by design.
_EXCLUDED_DIRS = ("migrations",)

#: An unreadable query is a finding, not a pass. Flipping this to ``False`` would
#: make the guard quietly narrower every time a new indirection appears.
_UNRESOLVED_IS_A_FINDING = True

#: The predicate builders in :mod:`app.data_access.arango.tenant_scope`, read off
#: the module rather than typed out: a third builder added there is recognised
#: here without editing this file, and a renamed one breaks loudly instead of
#: silently widening the guard.
_PREDICATE_BUILDERS = frozenset(
    name for name in dir(tenant_scope) if not name.startswith("_") and callable(getattr(tenant_scope, name))
)

#: Each builder's default ``doc_var`` — what a call without the keyword binds to.
#: Read from the signature, so a changed default moves the guard with it.
_DEFAULT_DOC_VAR: dict[str, str] = {
    name: inspect.signature(getattr(tenant_scope, name)).parameters["doc_var"].default for name in _PREDICATE_BUILDERS
}

#: Catalogue loops that carry no tenant predicate, keyed by ``(file, function)``,
#: each with the reason it is legitimate. An entry here is a decision someone
#: wrote down; an unlisted site fails, and an entry that no longer matches a site
#: fails too (:func:`test_every_allowlist_entry_still_matches_a_site`).
_ALLOWLIST: dict[tuple[str, str], str] = {
    # REQ-011 external enrichment: an installation-wide catalogue sweep, reachable
    # only behind ``require_platform_admin`` or the Celery schedule. Its result is
    # written back as mappings and never served to a tenant caller.
    ("data_access/arango/enrichment_repository.py", "find_unmapped_species"): (
        "installation-wide enrichment sweep, platform admin or Celery only"
    ),
    # #2120: seen for the first time once ``{col.X}`` placeholders resolved.
    ("data_access/arango/species_repository.py", "list_all_species"): (
        "backs SpeciesService.list_shadow_pairs, an operator report with no route or MCP caller; "
        "cross-comparing every record is its purpose (the derived-reads guard excludes it alike)"
    ),
}


def _collection_hole(expression: ast.expr) -> str | None:
    """``col.SPECIES`` inside an f-string placeholder -> ``"species"``; anything else -> ``None``."""
    if (
        isinstance(expression, ast.Attribute)
        and isinstance(expression.value, ast.Name)
        and expression.value.id == "col"
    ):
        value = getattr(col, expression.attr, None)
        return value if isinstance(value, str) else None
    return None


def _resolve(node: ast.AST, assigns: dict[str, ast.AST]) -> str | None:
    """The query text behind an expression, in every spelling listed above."""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue) and (name := _collection_hole(value.value)) is not None:
                parts.append(name)
            else:
                parts.append("<<EXPR>>")
        return "".join(parts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _resolve(node.left, assigns), _resolve(node.right, assigns)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.Name):
        target = assigns.get(node.id)
        return _resolve(target, assigns) if target is not None else None
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in {"replace", "format", "join"}:
            return _resolve(func.value, assigns)
    return None


def _builder_doc_vars(function: ast.AST) -> set[str]:
    """The ``doc_var`` of every predicate-builder call *function* makes itself.

    A non-literal ``doc_var`` binds to nothing this guard can name, so it adds no
    variable — the loop it was meant for then counts as unscoped, which is the
    conservative answer.
    """
    found: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if name not in _PREDICATE_BUILDERS:
            continue
        keyword = next((k for k in node.keywords if k.arg == "doc_var"), None)
        if keyword is None:
            found.add(_DEFAULT_DOC_VAR[name])
        elif isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            found.add(keyword.value.value)
    return found


def _same_class_callees(function: ast.AST, class_name: str | None, methods: dict[str, ast.AST]) -> set[str]:
    """Methods of the enclosing class *function* calls (``self.x``, ``cls.x``, ``Class.x``)."""
    receivers = {"self", "cls"} | ({class_name} if class_name else set())
    return {
        node.func.attr
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in receivers
        and node.func.attr in methods
    }


@dataclass(frozen=True)
class AqlCall:
    path: str
    lineno: int
    function: str
    query: str | None
    #: Loop variables a tenant-scope builder was called for — in the function or in
    #: a same-class helper it calls (``_species_scope`` in the botanical families).
    predicate_vars: frozenset[str]


def _calls_in(path: Path, tree: ast.Module) -> list[AqlCall]:
    # Module-level constants (#1664): ``ArangoErasureExecutor`` keeps its AQL in
    # ``_REMOVE_DOCUMENTS`` & co. A function-local name shadows a module one.
    module_assigns: dict[str, ast.AST] = {
        target.id: node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    owner: dict[int, tuple[str | None, dict[str, ast.AST]]] = {}
    for klass in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        methods = {n.name: n for n in klass.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}
        for method in methods.values():
            owner[id(method)] = (klass.name, methods)

    def doc_vars(function: ast.AST, class_name: str | None, methods: dict[str, ast.AST]) -> set[str]:
        found, seen, queue = set(), {id(function)}, [function]
        while queue:
            current = queue.pop()
            found |= _builder_doc_vars(current)
            for callee in _same_class_callees(current, class_name, methods):
                if id(methods[callee]) not in seen:
                    seen.add(id(methods[callee]))
                    queue.append(methods[callee])
        return found

    found: list[AqlCall] = []
    for function in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]:
        class_name, methods = owner.get(id(function), (None, {}))
        assigns: dict[str, ast.AST] = dict(module_assigns)
        for node in ast.walk(function):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigns[target.id] = node.value
        variables = frozenset(doc_vars(function, class_name, methods))
        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == "execute"):
                continue
            if not (isinstance(func.value, ast.Attribute) and func.value.attr == "aql"):
                continue
            query = _resolve(node.args[0], assigns) if node.args else None
            found.append(AqlCall(str(path.relative_to(_APP)), node.lineno, function.name, query, variables))
    return found


@cache
def _aql_execute_calls() -> tuple[AqlCall, ...]:
    """Every ``<x>.aql.execute(...)`` under ``app/`` outside the migrations."""
    found: list[AqlCall] = []
    for path in sorted(_APP.rglob("*.py")):
        if any(part in _EXCLUDED_DIRS for part in path.relative_to(_APP).parts):
            continue
        found.extend(_calls_in(path, ast.parse(path.read_text(encoding="utf-8"))))
    return tuple(found)


#: ``FOR <var> IN <collection>`` — the only shape this guard claims to see. A
#: catalogue reached through a graph traversal or through a bind-variable
#: collection name is named in the module docstring as out of reach.
_LOOP = re.compile(r"\bFOR\s+(\w+)\s+IN\s+([a-z_][a-z_0-9]*)\b")


def _catalogue_loops(query: str) -> list[tuple[str, str]]:
    """``(loop variable, catalogue)`` for every loop over a tenant-owned catalogue."""
    return [(var, name) for var, name in _LOOP.findall(query) if name in _TENANT_OWNED_CATALOG_COLLECTIONS]


def _catalogues_read(query: str) -> set[str]:
    """Catalogue collections the query loops over by name."""
    return {name for _, name in _catalogue_loops(query)}


def _unscoped_loops(call: AqlCall) -> list[tuple[str, str]]:
    """Catalogue loops of *call* whose variable carries no tenant predicate.

    A predicate is a *comparison* of ``<var>.tenant_key`` — a projection that
    merely copies the field out does not scope anything — or a builder called for
    that variable.
    """
    if call.query is None:
        return []
    return [
        (var, name)
        for var, name in _catalogue_loops(call.query)
        if var not in call.predicate_vars
        and not re.search(rf"\b{re.escape(var)}\.tenant_key\s*(?:==|!=|\bIN\b)", call.query)
    ]


def _offenders(calls: tuple[AqlCall, ...] | list[AqlCall]) -> list[str]:
    return [
        f"{c.path}:{c.lineno} in {c.function}() loops {sorted(f'{v} IN {n}' for v, n in _unscoped_loops(c))}"
        for c in calls
        if _unscoped_loops(c) and (c.path, c.function) not in _ALLOWLIST
    ]


def test_every_catalogue_loop_carries_a_tenant_predicate() -> None:
    offenders = _offenders(_aql_execute_calls())

    assert offenders == [], (
        "A hand-written AQL read loops a tenant-owned catalogue without a tenant predicate on that "
        "loop variable. This is the #1561 class: the filter was is_template only, and one tenant's "
        "template plans were served to every other tenant. Apply tenant_union_predicate(doc_var=<var>) "
        "(own ∪ global — a strict owner filter hides the global seeds, which is the #324 regression), "
        "or add the site to _ALLOWLIST with the reason it is legitimate.\n  " + "\n  ".join(offenders)
    )


def test_every_allowlist_entry_still_matches_a_site() -> None:
    """An entry that excuses nothing any more is a silent hole for the next read there."""
    excused = {(c.path, c.function) for c in _aql_execute_calls() if _unscoped_loops(c)}
    assert sorted(set(_ALLOWLIST) - excused) == []


def test_the_guard_sees_the_catalogue_reads_it_claims_to_cover() -> None:
    """Anti-vacuity: 3 of 27 were visible before ``{col.X}`` resolved (2026-10-05)."""
    reads = [c for c in _aql_execute_calls() if c.query is not None and _catalogues_read(c.query)]
    assert len(reads) >= 25, len(reads)
    assert {name for c in reads for name in _catalogues_read(c.query or "")} == set(_TENANT_OWNED_CATALOG_COLLECTIONS)


def test_the_guard_can_see_the_defect_it_was_written_for() -> None:
    """The falsification: the pre-#1561 query text must be rejected by the rule.

    Asserts on the **same expression** the rule above evaluates
    (:func:`_unscoped_loops`), not on a neighbouring statement. A guard whose
    counter-example is merely "some string without the word tenant" would stay green
    while the detector stopped recognising the loop.
    """
    before = """
            FOR plan IN nutrient_plans
                FILTER plan.is_template == true OR plan.origin == "system"
                RETURN plan
    """
    assert _unscoped_loops(AqlCall("x.py", 1, "f", before, frozenset())) == [("plan", "nutrient_plans")]

    after = """
            FOR plan IN nutrient_plans
                FILTER (plan.is_template == true OR plan.origin == "system")
                    AND (plan.tenant_key == @tenant_key OR plan.tenant_key == "")
                RETURN plan
    """
    assert _unscoped_loops(AqlCall("x.py", 1, "f", after, frozenset())) == []


def _calls_of(source: str) -> list[AqlCall]:
    return _calls_in(_APP / "data_access" / "planted.py", ast.parse(source))


class TestTheUpgradedRuleFires:
    """#2120: each shape the old "``tenant_key`` somewhere" rule passed, and its counterpart."""

    def test_a_col_placeholder_names_its_collection(self) -> None:
        """``FOR doc IN {col.SPECIES}`` was ``FOR doc IN <<EXPR>>`` — no catalogue, no rule."""
        calls = _calls_of('def f(db):\n    db.aql.execute(f"FOR doc IN {col.SPECIES} RETURN doc")\n')
        assert [_unscoped_loops(c) for c in calls] == [[("doc", "species")]]

    def test_a_second_loop_is_not_scoped_by_the_first_ones_predicate(self) -> None:
        """The ``list_template_plan_summaries`` shape: ``plan`` scoped, ``f`` not."""
        source = (
            "def f(db, t):\n"
            '    p, v = tenant_union_predicate(t, doc_var="plan")\n'
            '    db.aql.execute("FOR plan IN nutrient_plans FILTER X FOR f IN fertilizers RETURN f".replace("X", p))\n'
        )
        assert [_unscoped_loops(c) for c in _calls_of(source)] == [[("f", "fertilizers")]]
        scoped = source.replace("    db.aql", '    q, w = tenant_union_predicate(t, doc_var="f")\n    db.aql')
        assert scoped != source
        assert [_unscoped_loops(c) for c in _calls_of(scoped)] == [[]]

    def test_a_projection_of_the_field_is_not_a_predicate(self) -> None:
        query = "FOR doc IN species RETURN {name: doc.name, tenant_key: doc.tenant_key}"
        assert _unscoped_loops(AqlCall("x.py", 1, "f", query, frozenset())) == [("doc", "species")]

    def test_a_builder_for_another_variable_does_not_scope_the_loop(self) -> None:
        query = "FOR s IN species FILTER <<EXPR>> RETURN s"
        assert _unscoped_loops(AqlCall("x.py", 1, "f", query, frozenset({"doc"}))) == [("s", "species")]
        assert _unscoped_loops(AqlCall("x.py", 1, "f", query, frozenset({"s"}))) == []

    def test_a_same_class_helper_that_builds_the_predicate_counts(self) -> None:
        """The botanical-family shape: ``self._species_scope(t)`` builds it for ``s``."""
        source = (
            "class R:\n"
            "    @staticmethod\n"
            "    def _scope(t):\n"
            '        return tenant_union_predicate(t, doc_var="s")\n'
            "    def read(self, t):\n"
            "        p, v = self._scope(t)\n"
            '        self._db.aql.execute(f"FOR s IN {col.SPECIES} FILTER {p} RETURN s")\n'
        )
        assert [_unscoped_loops(c) for c in _calls_of(source)] == [[]]
        unhelped = source.replace("p, v = self._scope(t)", "p, v = other(t)")
        assert unhelped != source
        assert [_unscoped_loops(c) for c in _calls_of(unhelped)] == [[("s", "species")]]

    def test_a_non_literal_doc_var_scopes_nothing(self) -> None:
        source = (
            "def f(db, t, var):\n"
            "    p, v = tenant_union_predicate(t, doc_var=var)\n"
            '    db.aql.execute(f"FOR doc IN {col.SPECIES} FILTER {p} RETURN doc")\n'
        )
        assert [_unscoped_loops(c) for c in _calls_of(source)] == [[("doc", "species")]]


def test_unresolvable_queries_are_reported_rather_than_assumed_safe() -> None:
    """The blind spot is measured, not hidden.

    A query this guard cannot read is neither a pass nor a failure — it is a
    number that must not grow quietly. The assertion pins the count so that a new
    indirection over a catalogue read shows up as a diff to this file.
    """
    if not _UNRESOLVED_IS_A_FINDING:  # pragma: no cover - the flag exists to be read
        pytest.skip("unresolved queries are treated as passes")
    unresolved = [f"{c.path}:{c.lineno} in {c.function}()" for c in _aql_execute_calls() if c.query is None]

    assert len(unresolved) == _EXPECTED_UNRESOLVED, (
        "The set of AQL calls whose query text this guard cannot resolve changed. "
        "Raising the number is a decision: it means one more catalogue read is outside "
        "the rule's reach. Extend _resolve() instead where the spelling allows.\n  " + "\n  ".join(unresolved)
    )


#: Measured on the commit that introduced this guard. See the test above.
#: 2026-10-05 (#2107): 8 -> 7 — ``WateringLogRepository.get_recent_runoff_logs`` (dead,
#: its query picked from two class attributes) was removed.
_EXPECTED_UNRESOLVED = 7
