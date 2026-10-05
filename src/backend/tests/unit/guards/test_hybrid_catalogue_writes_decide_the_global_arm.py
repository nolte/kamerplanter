"""#2120 (MT-024 §1) — a write on a hybrid-catalogue row decides the global arm in the service.

A hybrid catalogue (species, cultivars, fertilizers, nutrient plans, substrates,
activities, workflow/task templates) is read as *own ∪ global*: a tenant sees its
own rows and the seeded global ones (``tenant_key == ""``). The audit's MT-002/003
class was a **write** that reused that read admission — ``get_fertilizer(key,
tenant_key)`` admitted the global seed, and the following ``update_fertilizer``
then let any grower of any tenant rewrite it; a shared workflow plan was editable
the same way. The existing guards only asked *that* a key travels with a tenant,
not *what* the admission means.

**The rule.** Every public service method that writes and touches a hybrid row —
its closure (same-class helpers and same-module functions) calls the hybrid read
admission ``verify_tenant_read_access`` or a gate of
:mod:`app.domain.services.catalogue_authorization`, **or** it calls an
update/delete/grant/revoke writer on a receiver typed as a hybrid-catalogue
repository — must decide the global arm **inside the service**, in one of three
ways the code base uses:

``admin-gate``      a :mod:`~app.domain.services.catalogue_authorization` gate — the
                    global row is a platform admin's (``is_platform_admin`` is a
                    parameter of every one of them), the foreign row is 404;
``owner-only``      ``verify_tenant_ownership`` or ``for_write=True`` — the global row
                    is as unwritable as a foreign one (nutrient plans);
``owner-compared``  an ``if`` on ``<row>.tenant_key`` that raises or forks and does
                    **not** name the empty owner — the shared-workflow refusal /
                    fork-on-write (MT-003), own sub-rows. ``tenant_key not in ("",
                    t)`` is the read admission spelled inline and decides nothing.

A method that reads a hybrid row only to write rows of its own (apply a plan to a
plant, duplicate a template) is listed in :data:`_WRITES_NO_HYBRID_ROW` with the
reason. Anything else is a finding. The issue's literal wording asked for "an
authorisation function with an ``is_platform_admin`` parameter" everywhere;
measured, nutrient plans and workflow templates deliberately refuse the global row
to *everyone* on a tenant route (owner-only / fork), which is stricter — so the
rule accepts the three decisions rather than forcing one policy.

**Red against the code before #2148** (fertilizer service of ``d7365d77f^``):
``update_fertilizer`` / ``delete_fertilizer`` wrote a hybrid row with no decision.
Red against **this** tree when written: ``ActivityService.update_activity`` /
``delete_activity`` — the platform-admin decision lived only in the router.

**Blind spots**, named: a write reached through dynamic dispatch, a hybrid row
written through a repository whose receiver carries no type, and a decision made
in another class (the router) — which is exactly the shape the rule refuses.
"""

from __future__ import annotations

import ast
import inspect
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from app.domain.services import catalogue_authorization
from tests.support.execution_guards import find_project_root
from tests.unit.api._write_call_graph import CallGraph, call_graph
from tests.unit.guards import test_tenant_scoped_reads_are_derived as derived

_APP = find_project_root(Path(__file__)) / "app"

#: The gates, read off the module so a new one is recognised without editing this file.
_GATES = frozenset(
    name
    for name, obj in vars(catalogue_authorization).items()
    if inspect.isfunction(obj) and obj.__module__ == catalogue_authorization.__name__ and not name.startswith("_")
)

#: Writers that change an *existing* row of the receiver's catalogue (a create has
#: no row to admit; ``add_incompatibility`` links two existing products).
_MUTATING = re.compile(r"(?:update|delete|replace|remove|revoke|grant)(?:_\w+)?|add_incompatibility")

_WRITES_NO_HYBRID_ROW: dict[str, str] = {
    "ActivityPlanService.apply_plan_to_plant": (
        "reads a readable plan (own or shared) and creates tasks stamped with the caller's tenant for an own plant"
    ),
    "ActivityPlanService.apply_plan_to_run": "as apply_plan_to_plant, for every plant of an own run",
    "TaskService.duplicate_workflow_template": "reads a readable template and writes a new copy owned by the caller",
    "TaskService.instantiate_workflow": "reads a readable template and writes tasks and an execution of the caller",
    "NutrientPlanService.remove_plant_plan": (
        "deletes the plant's own follows_plan edge, the plan is not written; the plant is verified in the "
        "repository (verify_entity_ownership, #2107)"
    ),
    "UserPreferenceService.update_preferences": (
        "writes the caller's own preference row; the receiver is typed as a union that includes catalogue repositories"
    ),
}


@dataclass(frozen=True)
class HybridWrite:
    qualname: str
    decision: str | None


def _call_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _closure(fn: ast.AST, klass: ast.ClassDef, functions: dict[str, ast.AST]) -> list[ast.AST]:
    methods = {n.name: n for n in klass.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}
    seen, queue, out = {id(fn)}, [fn], []
    while queue:
        current = queue.pop()
        out.append(current)
        for node in ast.walk(current):
            if not isinstance(node, ast.Call):
                continue
            target = None
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id in ("self", "cls", klass.name):
                    target = methods.get(node.func.attr)
            elif isinstance(node.func, ast.Name):
                target = functions.get(node.func.id)
            if target is not None and id(target) not in seen:
                seen.add(id(target))
                queue.append(target)
    return out


def _admits_the_global_owner(test: ast.expr) -> bool:
    """``x.tenant_key (not) in ("", t)`` — a membership test whose set contains the empty owner."""
    for node in ast.walk(test):
        if not isinstance(node, ast.Compare):
            continue
        for op, comparator in zip(node.ops, node.comparators, strict=True):
            membership = isinstance(op, ast.In | ast.NotIn) and isinstance(comparator, ast.Tuple | ast.List | ast.Set)
            if membership and any(isinstance(e, ast.Constant) and e.value == "" for e in comparator.elts):
                return True
    return False


def decision_of(nodes: list[ast.AST]) -> str | None:
    """Which of the three global-arm decisions *nodes* make, if any."""
    calls = [n for node in nodes for n in ast.walk(node) if isinstance(n, ast.Call)]
    names = {_call_name(c) for c in calls}
    if names & _GATES:
        return "admin-gate"
    if "verify_tenant_ownership" in names or any(
        k.arg == "for_write" and isinstance(k.value, ast.Constant) and k.value.value is True
        for c in calls
        for k in c.keywords
    ):
        return "owner-only"
    for node in nodes:
        for branch in ast.walk(node):
            if not (isinstance(branch, ast.If) and ".tenant_key" in ast.unparse(branch.test)):
                continue
            # ``row.tenant_key not in ("", tenant_key)`` is the hybrid *read* admission
            # spelled inline — the pre-#2100 fertilizer shape. A comparison that names
            # the empty (global) owner admits it, so it decides nothing about writing.
            if _admits_the_global_owner(branch.test):
                continue
            if any(
                isinstance(inner, ast.Raise)
                or (isinstance(inner, ast.Call) and (_call_name(inner) or "").startswith("_copy"))
                for inner in ast.walk(branch)
            ):
                return "owner-compared"
    return None


def _hybrid_repositories() -> frozenset[str]:
    constants = derived.bindings.collection_constants(_APP)
    classes = derived.bindings.repository_classes(_APP, constants, include_plain=True)
    return frozenset(name for name, repo in classes.items() if repo.collection in derived.HYBRID_CATALOGUES)


def _writes_a_hybrid_row(graph: CallGraph, function_id: str, hybrid: frozenset[str]) -> bool:
    fn = graph.by_id.get(function_id)
    if fn is None:
        return False
    writers = graph.writers()
    for call in fn._call_nodes:
        if not (isinstance(call.func, ast.Attribute) and _MUTATING.fullmatch(call.func.attr)):
            continue
        related = {k.name for t in graph._types_of(call.func.value, fn) for k in graph._related_classes(t)}
        if related & hybrid and any(t.id in writers for t in graph._call_targets(call, fn)):
            return True
    return False


def hybrid_writes(root: Path, graph: CallGraph) -> list[HybridWrite]:
    hybrid = _hybrid_repositories()
    writers = graph.writers()
    found: list[HybridWrite] = []
    for path in sorted((root / "domain" / "services").rglob("*.py")):
        module = "app." + ".".join(path.relative_to(root).with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}
        for klass in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            for fn in [n for n in klass.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)]:
                function_id = f"{module}::{klass.name}.{fn.name}"
                if fn.name.startswith("_") or function_id not in writers:
                    continue
                nodes = _closure(fn, klass, functions)
                names = {_call_name(c) for node in nodes for c in ast.walk(node) if isinstance(c, ast.Call)}
                admits = "verify_tenant_read_access" in names or bool(names & _GATES)
                if admits or _writes_a_hybrid_row(graph, function_id, hybrid):
                    found.append(HybridWrite(f"{klass.name}.{fn.name}", decision_of(nodes)))
    return found


@cache
def _inventory() -> tuple[HybridWrite, ...]:
    return tuple(hybrid_writes(_APP, call_graph()))


def test_every_hybrid_write_decides_the_global_arm_in_the_service() -> None:
    undecided = sorted(
        w.qualname for w in _inventory() if w.decision is None and w.qualname not in _WRITES_NO_HYBRID_ROW
    )
    assert undecided == [], (
        "These service methods write a hybrid-catalogue row but decide nothing about the global arm "
        "inside the service — the router (or nobody) does. Call a catalogue_authorization gate, "
        "verify_tenant_ownership / for_write=True, or compare the row's tenant_key and refuse (#2120, "
        f"MT-002/003): {undecided}"
    )


def test_every_no_hybrid_row_entry_is_still_a_hybrid_write_without_a_decision() -> None:
    """An entry that now decides, or is gone, excuses nothing and must leave the list."""
    undecided = {w.qualname for w in _inventory() if w.decision is None}
    assert sorted(set(_WRITES_NO_HYBRID_ROW) - undecided) == []


def test_the_inventory_reaches_every_hybrid_service() -> None:
    """Anti-vacuity: the selector is as wide as the catalogues, each decision kind occurs."""
    inventory = _inventory()
    owners = {w.qualname.split(".")[0] for w in inventory}
    assert {"FertilizerService", "SpeciesService", "SubstrateService", "NutrientPlanService", "TaskService"} <= owners
    assert {w.decision for w in inventory} >= {"admin-gate", "owner-only", "owner-compared"}
    assert len(inventory) >= 50, len(inventory)


class TestTheRuleSeesTheShapes:
    @staticmethod
    def _nodes(source: str) -> list[ast.AST]:
        tree = ast.parse(source)
        klass = next(n for n in tree.body if isinstance(n, ast.ClassDef))
        functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        method = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == "write")
        return _closure(method, klass, functions)

    def test_the_pre_2100_fertilizer_shape_decides_nothing(self) -> None:
        source = (
            "class S:\n"
            "    def get(self, key, tenant_key=''):\n"
            "        row = self._repo.get_or_raise(key)\n"
            "        verify_tenant_read_access(row, tenant_key, 'Fertilizer')\n        return row\n"
            "    def write(self, key, data):\n        self.get(key)\n        self._repo.update(key, data)\n"
        )
        assert decision_of(self._nodes(source)) is None

    def test_each_decision_is_seen_through_a_helper(self) -> None:
        gate = (
            "def _gate(row, t, admin):\n    authorize_hybrid_catalogue_write(row.tenant_key, is_platform_admin=admin)\n"
        )
        assert (
            decision_of(self._nodes(gate + "class S:\n    def write(self, row):\n        _gate(row, 't', False)\n"))
            == "admin-gate"
        )
        assert (
            decision_of(
                self._nodes("class S:\n    def write(self, k):\n        self.get(k, tenant_key='t', for_write=True)\n")
            )
            == "owner-only"
        )
        refuse = (
            "class S:\n    def _r(self, wt):\n        if not wt.tenant_key:\n            raise ForbiddenError('x')\n"
            "    def write(self, wt):\n        self._r(wt)\n"
        )
        assert decision_of(self._nodes(refuse)) == "owner-compared"

    def test_an_inline_read_admission_is_no_decision(self) -> None:
        """The exact pre-#2100 fertilizer shape: the refusal admits the global row."""
        source = (
            "class S:\n"
            "    def get(self, key, tenant_key=''):\n"
            "        fert = self._repo.get_or_raise(key)\n"
            "        if tenant_key and fert.tenant_key not in ('', tenant_key):\n"
            "            raise NotFoundError('Fertilizer', key)\n        return fert\n"
            "    def write(self, key, data):\n        self.get(key)\n        self._repo.update(key, data)\n"
        )
        assert decision_of(self._nodes(source)) is None

    def test_a_normalised_owner_comparison_is_a_decision(self) -> None:
        """``(row.tenant_key or "") != t`` names ``""`` only to normalise ``None``; it refuses the global row."""
        source = (
            "class S:\n    def write(self, stock, t):\n"
            "        if (stock.tenant_key or '') != t:\n            raise NotFoundError('Stock', 'k')\n"
        )
        assert decision_of(self._nodes(source)) == "owner-compared"

    def test_a_tenant_key_compare_that_does_not_refuse_is_no_decision(self) -> None:
        source = "class S:\n    def write(self, wt):\n        if wt.tenant_key:\n            log(wt)\n"
        assert decision_of(self._nodes(source)) is None
