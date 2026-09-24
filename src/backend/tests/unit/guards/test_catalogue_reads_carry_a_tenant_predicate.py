"""#1561 class guard — hand-written AQL over a hybrid catalogue must name a tenant.

The defect this file exists for: ``FavoritesService.get_matching_nutrient_plans``
took a ``tenant_key`` and ran its query **without** ``bind_vars``. Its only filter
was ``is_template == true OR origin == "system"``, so every row any tenant flagged
as a template was served to any authenticated caller of any tenant, with the
product name and brand of every fertilizer it used. Nothing raised, nothing logged,
and the parameter in the signature made the call site read as if it were scoped.

**The class, stated as a rule and not as today's literal value** (the failure PR
#1608 had to repair): *a hand-written AQL read that loops over a collection whose
model declares ownership must mention that ownership somewhere in the query.* The
guard does not care which predicate, which helper, or which bind-variable name —
only that the query text names ``tenant_key`` at all. A wrong predicate is a code
review's job; a **missing** one is mechanical, and it is the one that shipped.

The catalogue set is
:data:`~app.domain.services.favorites_service._TENANT_OWNED_CATALOG_COLLECTIONS`,
which ``test_favoritable_collections_declare_ownership.py`` holds equal to the set
of models that actually declare ``tenant_key`` — so this guard inherits a set
derived from the models rather than carrying a fourth hand-list that can drift.

**Query-text resolution.** A query reaches ``aql.execute`` in more spellings than
one, and a sweep that knows only one of them looks complete while missing sites —
this repository has paid for that twice (a regex that demanded a string literal,
a glob that assumed a name prefix). Resolved here: an inline literal, an f-string
(its placeholders become ``<<EXPR>>``), implicit and ``+`` concatenation, a name
assigned anywhere in the same function or at module level, and the receiver of a trailing
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
  ``FOR x IN <collection>``;
* a query whose ``tenant_key`` mention sits in a projection or a comment rather
  than in a ``FILTER`` — textual presence is the predicate here, deliberately: the
  cheap rule that fires on the real defect beats the expensive one nobody trusts.

``app/migrations/`` is out of scope on purpose: a migration runs in the system
context and is *required* to see every tenant's rows.
"""

from __future__ import annotations

import ast
import re
from functools import cache
from pathlib import Path

import pytest

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
#: the module rather than typed out: a fourth builder added there is recognised
#: here without editing this file, and a renamed one breaks loudly instead of
#: silently widening the guard.
_PREDICATE_BUILDERS = frozenset(
    name for name in dir(tenant_scope) if not name.startswith("_") and callable(getattr(tenant_scope, name))
)

#: Call sites that loop a catalogue collection without naming a tenant, keyed by
#: ``(file, function)``, each with the reason it is legitimate. An entry here is a
#: decision someone wrote down; an unlisted site fails.
#:
#: ``find_unmapped_species`` (REQ-011 external enrichment) is an installation-wide
#: catalogue sweep, reachable only behind ``require_platform_admin`` or the Celery
#: schedule. Its result is written back as mappings and is never served to a tenant
#: caller — seeing every row is the point of the job.
_ALLOWLIST: frozenset[tuple[str, str]] = frozenset(
    {("data_access/arango/enrichment_repository.py", "find_unmapped_species")}
)


def _resolve(node: ast.AST, assigns: dict[str, ast.AST]) -> str | None:
    """The query text behind an expression, in every spelling listed above."""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            parts.append(str(value.value) if isinstance(value, ast.Constant) else "<<EXPR>>")
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


@cache
def _aql_execute_calls() -> tuple[tuple[str, int, str, str | None, bool], ...]:
    """``(path, line, function, query, builds_a_predicate)`` for every AQL call.

    ``builds_a_predicate`` is true when the enclosing function calls one of
    :data:`_PREDICATE_BUILDERS`. That is how a query whose predicate is *spliced*
    rather than written inline still counts as scoped — the #1561 repair itself is
    that spelling. It is a real code fact, not a marker string: a comment claiming
    the predicate cannot satisfy it, which is the vacuum trap PR #1545 fell into.
    """
    found: list[tuple[str, int, str, str | None, bool]] = []
    for path in sorted(_APP.rglob("*.py")):
        if any(part in _EXCLUDED_DIRS for part in path.relative_to(_APP).parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # Module-level constants (#1664): ``ArangoErasureExecutor`` keeps its AQL in
        # ``_REMOVE_DOCUMENTS`` & co. A function-local name shadows a module one.
        module_assigns: dict[str, ast.AST] = {
            target.id: node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        for function in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]:
            assigns: dict[str, ast.AST] = dict(module_assigns)
            for node in ast.walk(function):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            assigns[target.id] = node.value
            builds_a_predicate = any(
                isinstance(node, ast.Call)
                and (
                    (isinstance(node.func, ast.Name) and node.func.id in _PREDICATE_BUILDERS)
                    or (isinstance(node.func, ast.Attribute) and node.func.attr in _PREDICATE_BUILDERS)
                )
                for node in ast.walk(function)
            )
            for node in ast.walk(function):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if not (isinstance(func, ast.Attribute) and func.attr == "execute"):
                    continue
                if not (isinstance(func.value, ast.Attribute) and func.value.attr == "aql"):
                    continue
                query = _resolve(node.args[0], assigns) if node.args else None
                found.append((str(path.relative_to(_APP)), node.lineno, function.name, query, builds_a_predicate))
    return tuple(found)


#: ``FOR <var> IN <collection>`` — the only shape this guard claims to see. A
#: catalogue reached through a graph traversal or through a bind-variable
#: collection name is named in the module docstring as out of reach.
_LOOP = re.compile(r"\bFOR\s+\w+\s+IN\s+([a-z_][a-z_0-9]*)\b")


def _catalogues_read(query: str) -> set[str]:
    """Catalogue collections the query loops over by name."""
    return {name for name in _LOOP.findall(query) if name in _TENANT_OWNED_CATALOG_COLLECTIONS}


def test_every_catalogue_read_names_a_tenant() -> None:
    offenders = []
    for rel_path, lineno, function, query, builds_a_predicate in _aql_execute_calls():
        if query is None:
            continue
        if not _catalogues_read(query):
            continue
        if "tenant_key" in query or builds_a_predicate:
            continue
        if (rel_path, function) in _ALLOWLIST:
            continue
        offenders.append(f"{rel_path}:{lineno} in {function}() reads {sorted(_catalogues_read(query))}")

    assert offenders == [], (
        "A hand-written AQL read loops a tenant-owned catalogue without naming tenant_key. "
        "This is the #1561 class: the filter was is_template only, and one tenant's template "
        "plans were served to every other tenant. Apply tenant_union_predicate (own ∪ global — "
        "a strict owner filter hides the global seeds, which is the #324 regression), or add the "
        "site to _ALLOWLIST with the reason it is legitimate.\n  " + "\n  ".join(offenders)
    )


def test_the_guard_can_see_the_defect_it_was_written_for() -> None:
    """The falsification: the pre-#1561 query text must be rejected by the rule.

    Asserts on the **same expressions** the rule above evaluates — the catalogue
    detector and the tenant mention — not on a neighbouring statement. A guard whose
    counter-example is merely "some string without the word tenant" would stay green
    while the detector stopped recognising the loop.
    """
    before = """
            FOR plan IN nutrient_plans
                FILTER plan.is_template == true OR plan.origin == "system"
                RETURN plan
    """
    assert _catalogues_read(before) == {"nutrient_plans"}
    assert "tenant_key" not in before

    after = """
            FOR plan IN nutrient_plans
                FILTER (plan.is_template == true OR plan.origin == "system")
                    AND (plan.tenant_key == @tenant_key OR plan.tenant_key == "")
                RETURN plan
    """
    assert _catalogues_read(after) == {"nutrient_plans"}
    assert "tenant_key" in after


def test_unresolvable_queries_are_reported_rather_than_assumed_safe() -> None:
    """The blind spot is measured, not hidden.

    A query this guard cannot read is neither a pass nor a failure — it is a
    number that must not grow quietly. The assertion pins the count so that a new
    indirection over a catalogue read shows up as a diff to this file.
    """
    if not _UNRESOLVED_IS_A_FINDING:  # pragma: no cover - the flag exists to be read
        pytest.skip("unresolved queries are treated as passes")
    unresolved = [f"{p}:{line} in {fn}()" for p, line, fn, query, _ in _aql_execute_calls() if query is None]

    assert len(unresolved) == _EXPECTED_UNRESOLVED, (
        "The set of AQL calls whose query text this guard cannot resolve changed. "
        "Raising the number is a decision: it means one more catalogue read is outside "
        "the rule's reach. Extend _resolve() instead where the spelling allows.\n  " + "\n  ".join(unresolved)
    )


#: Measured on the commit that introduced this guard. See the test above.
_EXPECTED_UNRESOLVED = 8
