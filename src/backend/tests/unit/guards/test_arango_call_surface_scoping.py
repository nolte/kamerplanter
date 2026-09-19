"""#1535 / #1533 class sweep — an omitted argument must not silently unscope a call.

Both issues of this group are one class: **a permissive call surface, and a call
site that drifts off it.** ``delete_edges`` accepts an id that matches nothing and
runs happily; ``get_all_tasks`` accepted a missing ``tenant_key`` and answered for
every tenant. Neither failure raises, logs or shows up in a response — the first
returns "0 edges removed", the second returns rows.

The rules below are the mechanical part of closing that class over
``app/data_access/arango/`` and the callers of its surfaces:

``R1`` a ``delete_edges`` id argument carrying a pattern character (``%``/``*``).
      ``delete_edges`` binds the vertex and compares it with ``==``; there is no
      ``LIKE``, so a pattern is a literal that matches nothing. This is #1535.

``R2`` a ``delete_edges`` call naming ``to_id``/``other_id`` without
      ``from_id``/``vertex_id``. That combination raises ``ValueError`` before
      deleting anything — the #1525 defect (``delete_phase_history``), which is
      how #1535 was found.

``R3`` a call to ``get_all_tasks`` that does not name ``tenant_key``. This is
      #1533; the signature now refuses it too, and :class:`TestTheSurfacesStayStrict`
      pins that, because an AST rule over call sites cannot see a default sneaking
      back into the signature — nor can a signature check see a call that passes
      ``tenant_key=""``, which is why both exist.

**Function-wide resolution, in statement order.** A name is resolved from the
assignments that *precede* the call inside the same function. Both halves are
load-bearing and both were measured:

* A *file*-wide variable map produced ten false positives in ``graph_repository.py``
  alone (lines 99–126, 210–211 bind ``from_id`` locally and correctly).
* A function-wide map that lets the *last* assignment win produced two more, in
  ``sensor_repository.create`` and ``tank_repository.create_fill_event``: both
  rebind ``to_id``/``from_id`` further down, so an order-blind reader attributes
  the second value to the first call.

**Spellings this does not match**, named rather than discovered later — the
question "name a spelling of the same thing my pattern misses" has real answers
here:

* an id or edge collection that arrives as a **parameter**, through a helper, or
  out of a container (``for edge_col in [col.A, col.B]: self.delete_edges(edge_col, x)``
  in ``fertilizer_repository.delete`` is live today — R1/R2 still see its id
  arguments, but nothing resolves the collection);
* a call through an alias (``fn = repo.delete_edges``) or ``getattr``;
* arguments splatted from a dict (``repo.get_all_tasks(**kwargs)``) — R3 cannot
  see a ``tenant_key`` in there, so such a call is collected in
  :data:`_UNRESOLVED_SPLATS` and the inventory must stay empty;
* an *empty* ``tenant_key`` passed explicitly, which is a value question, not a
  syntax one — ``_require_tenant_key`` in the repository is what answers it.

**The direction class is deliberately NOT a rule here.** The third sweep item
#1535 proposes — check each call's vertex against the edge's declared
``from_vertex_collections``/``to_vertex_collections`` in ``collections.py`` — needs
that table to be an oracle, and it is not. Measured over ``app/`` on 2026-09-19,
after the two resolver defects above were fixed, the writers and the declarations
disagree in ``membership_repository`` for **two** edges: ``has_membership`` is
declared ``tenants → memberships`` and written ``users → memberships``, and
``membership_in`` is declared ``users → memberships`` and written
``memberships → tenants``. The code is right and consistent with its own deletes;
the declaration is wrong. A direction guard would therefore have failed on correct
code, and correcting the declaration means replacing a live named-graph edge
definition (``collections.py`` calls ``graph.replace_edge_definition`` on every
bootstrap) — a schema change with its own sign-off, outside this group's scope. It
is filed instead; the boundary is named here so the gap is a decision on the
record rather than an oversight.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.interfaces.task_repository import ITaskRepository
from app.domain.services.task_service import TaskService
from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: Characters that are a wildcard in a ``LIKE`` and a literal in an ``==``.
_PATTERN_CHARACTERS = ("%", "*")

#: ``delete_edges`` parameters that carry a document id.
_ID_PARAMETERS = ("from_id", "to_id", "vertex_id", "other_id")

#: Positional order of ``delete_edges(edge_collection, from_id, to_id)``.
_DELETE_EDGES_POSITIONAL = ("edge_collection", "from_id", "to_id")

#: Calls that splat their arguments and are therefore invisible to R3. Empty
#: today (measured 2026-09-19); a new one must be looked at rather than assumed
#: innocent.
_UNRESOLVED_SPLATS: list[str] = []


class _Violation:
    def __init__(self, rule: str, location: str, detail: str) -> None:
        self.rule = rule
        self.location = location
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.rule} {self.location}: {self.detail}"


def _string_value(node: ast.AST, env: dict[str, str]) -> str | None:
    """Resolve ``node`` to a string, or ``None`` when it cannot be known statically.

    Handles literals, f-strings (unknown interpolations become ``\\x00``, which is
    not a pattern character and therefore never invents a violation), names bound
    earlier in the same function, and ``col.CONSTANT``-style attributes (whose
    *value* is irrelevant to every rule here — only the id prefix would be, and no
    rule uses it).
    """
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.Name):
        return env.get(node.id)
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                inner = _string_value(value.value, env)
                parts.append(inner if inner is not None else "\x00")
            else:  # pragma: no cover - defensive
                parts.append("\x00")
        return "".join(parts)
    return None


def _carries_pattern(node: ast.AST, env: dict[str, str]) -> bool:
    """Whether ``node`` can be seen to contain a pattern character.

    Falls back to every string constant in the subtree when the expression does not
    resolve as a whole, so ``"locations/" + "%"`` is caught as well as the f-string
    #1535 actually used.
    """
    resolved = _string_value(node, env)
    if resolved is not None:
        return any(char in resolved for char in _PATTERN_CHARACTERS)
    return any(
        isinstance(sub, ast.Constant)
        and isinstance(sub.value, str)
        and any(char in sub.value for char in _PATTERN_CHARACTERS)
        for sub in ast.walk(node)
    )


def _call_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return None


def _check_call(call: ast.Call, env: dict[str, str], location: str) -> list[_Violation]:
    name = _call_name(call)
    found: list[_Violation] = []
    if name == "delete_edges":
        arguments: dict[str, ast.AST] = {}
        for index, value in enumerate(call.args):
            if index < len(_DELETE_EDGES_POSITIONAL):
                arguments[_DELETE_EDGES_POSITIONAL[index]] = value
        for keyword in call.keywords:
            if keyword.arg:
                arguments[keyword.arg] = keyword.value

        for parameter in _ID_PARAMETERS:
            node = arguments.get(parameter)
            if node is not None and _carries_pattern(node, env):
                found.append(
                    _Violation(
                        "R1",
                        location,
                        f"{parameter}= carries a pattern character; delete_edges compares with "
                        "`==`, so it matches nothing (#1535)",
                    )
                )
        anchored = any(arguments.get(p) is not None for p in ("from_id", "vertex_id"))
        opposite = any(arguments.get(p) is not None for p in ("to_id", "other_id"))
        if opposite and not anchored:
            found.append(
                _Violation(
                    "R2",
                    location,
                    "names the opposite end without an anchor; delete_edges raises ValueError "
                    "before deleting anything (#1525)",
                )
            )
    elif name == "get_all_tasks":
        if any(keyword.arg is None for keyword in call.keywords):
            _UNRESOLVED_SPLATS.append(location)
        elif not any(keyword.arg == "tenant_key" for keyword in call.keywords):
            found.append(
                _Violation(
                    "R3",
                    location,
                    "does not name tenant_key; the page would be drawn from every tenant (#1533)",
                )
            )
    return found


def _walk_in_order(body: list[ast.stmt], env: dict[str, str], location: str) -> list[_Violation]:
    """Check ``body`` statement by statement, growing ``env`` as assignments pass.

    Statement order is what keeps a later rebinding of ``to_id`` from being read
    back onto an earlier call (the ``sensor_repository.create`` false positive).
    """
    found: list[_Violation] = []
    for statement in body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue  # a nested function gets its own scope below
        for node in ast.walk(statement):
            if isinstance(node, ast.Call):
                found.extend(_check_call(node, env, f"{location}:{node.lineno}"))
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name):
                value = _string_value(statement.value, env)
                if value is None:
                    env.pop(target.id, None)
                else:
                    env[target.id] = value
    return found


def _dedupe(violations: list[_Violation]) -> list[_Violation]:
    """One report per (rule, call).

    A method is reached twice — once by the module-level pass walking into its
    class body, once by its own scope — and a doubled line reads like two defects.
    The function-scoped report wins because it names the function.
    """
    by_call: dict[tuple[str, str], _Violation] = {}
    for violation in violations:
        key = (violation.rule, violation.location.rsplit(":", 1)[-1] + "@" + violation.location.split("::")[0])
        if key not in by_call or "::" in violation.location:
            by_call[key] = violation
    return list(by_call.values())


def _scan(path: Path) -> list[_Violation]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    relative = path.relative_to(_APP.parent)
    found = _walk_in_order(tree.body, {}, str(relative))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.extend(_walk_in_order(node.body, {}, f"{relative}::{node.name}"))
    return _dedupe(found)


def _scan_application() -> list[_Violation]:
    found: list[_Violation] = []
    for path in sorted(_APP.rglob("*.py")):
        found.extend(_scan(path))
    return found


class TestTheApplicationIsClean:
    def test_no_call_is_silently_unscoped_or_inert(self) -> None:
        violations = _scan_application()
        assert not violations, "Silently unscoped or inert calls:\n" + "\n".join(str(v) for v in violations)

    def test_no_call_hides_its_arguments_behind_a_splat(self) -> None:
        """A call R3 cannot read is not a call R3 has cleared."""
        _UNRESOLVED_SPLATS.clear()
        _scan_application()
        assert _UNRESOLVED_SPLATS == [], (
            "get_all_tasks is called with **kwargs, so this guard cannot see whether "
            "tenant_key is among them:\n" + "\n".join(_UNRESOLVED_SPLATS)
        )


class TestTheRulesFire:
    """The rules against the exact code each issue measured — red-first, mechanically.

    Without these, a refactor that broke the scan (an unhandled node type, a lost
    keyword) would leave every rule silently inert while the suite stayed green.
    """

    @staticmethod
    def _rules(source: str) -> set[str]:
        tree = ast.parse(source)
        found = _walk_in_order(tree.body, {}, "<inline>")
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found.extend(_walk_in_order(node.body, {}, f"<inline>::{node.name}"))
        return {v.rule for v in _dedupe(found)}

    def test_r1_catches_the_1535_line_as_it_was_written(self) -> None:
        source = (
            "def _delete_slot_internal(self, key):\n"
            '    slot_id = f"{col.SLOTS}/{key}"\n'
            '    self.delete_edges(col.HAS_SLOT, from_id=f"{col.LOCATIONS}/%", to_id=slot_id)\n'
        )
        assert "R1" in self._rules(source)

    def test_r1_catches_a_pattern_that_arrives_through_a_local(self) -> None:
        source = 'def f(self):\n    anchor = "locations/%"\n    self.delete_edges(col.HAS_SLOT, from_id=anchor)\n'
        assert "R1" in self._rules(source)

    def test_r1_catches_a_concatenated_pattern(self) -> None:
        source = 'def f(self):\n    self.delete_edges(col.HAS_SLOT, from_id="locations/" + "%")\n'
        assert "R1" in self._rules(source)

    def test_r2_catches_the_1525_line_as_it_was_written(self) -> None:
        source = (
            'def delete_phase_history(self, key):\n    self.delete_edges(col.PHASE_HISTORY_EDGE, to_id=f"x/{key}")\n'
        )
        assert "R2" in self._rules(source)

    def test_r3_catches_the_1533_call_as_it_was_written(self) -> None:
        source = (
            'def generate(task_repo):\n    existing, _ = task_repo.get_all_tasks(0, 200, {"category": "maintenance"})\n'
        )
        assert "R3" in self._rules(source)

    def test_the_repaired_spellings_pass(self) -> None:
        source = (
            "def f(self, task_repo, tenant_key):\n"
            '    slot_id = f"{col.SLOTS}/{key}"\n'
            '    self.delete_edges(col.HAS_SLOT, vertex_id=slot_id, direction="inbound")\n'
            "    task_repo.get_all_tasks(0, 200, None, tenant_key=tenant_key)\n"
        )
        assert self._rules(source) == set()

    def test_a_later_rebinding_is_not_read_onto_an_earlier_call(self) -> None:
        """The ``sensor_repository.create`` shape: same name, two values, in order."""
        source = (
            "def create(self, sensor):\n"
            '    to_id = f"{col.TANKS}/{sensor.tank_key}"\n'
            "    self.delete_edges(col.MONITORS_TANK, from_id=to_id)\n"
            '    to_id = "locations/%"\n'
        )
        assert self._rules(source) == set()


class TestTheSurfacesStayStrict:
    """The signatures themselves, because a call-site scan cannot see a default.

    ``tenant_key`` back as an optional parameter would make every one of the
    repaired call sites legal again with one argument dropped — which is exactly how
    #1533 happened.
    """

    @pytest.mark.parametrize(
        "owner,method",
        [
            (ITaskRepository, "get_all_tasks"),
            (ArangoTaskRepository, "get_all_tasks"),
            (TaskService, "list_tasks"),
            (ArangoTaskRepository, "find_open_task_by_name"),
        ],
    )
    def test_tenant_key_is_keyword_only_and_has_no_default(self, owner: type, method: str) -> None:
        parameter = inspect.signature(getattr(owner, method)).parameters["tenant_key"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, f"{owner.__name__}.{method}"
        assert parameter.default is inspect.Parameter.empty, f"{owner.__name__}.{method}"

    def test_delete_edges_still_compares_with_equality(self) -> None:
        """R1's premise: a pattern really is inert here.

        If ``delete_edges`` ever grew a ``LIKE``, R1 would be forbidding a spelling
        that had become legitimate — a rule whose reason has quietly expired.
        """
        source = inspect.getsource(BaseArangoRepository.delete_edges)
        assert "e._from == @vertex" in source
        assert "e._to == @vertex" in source
        assert "LIKE" not in source.upper().replace("LIKELY", "")
