"""#1535 / #1533 class sweep — an omitted argument must not silently unscope a call.

Both issues of this group are one class: **a permissive call surface, and a call
site that drifts off it.** ``delete_edges`` accepts an id that matches nothing and
runs happily; ``get_all_tasks`` accepted a missing ``tenant_key`` and answered for
every tenant. Neither failure raises, logs or shows up in a response — the first
returns "0 edges removed", the second returns rows.

The rules below are the mechanical part of closing that class over ``app/``:

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

``R4`` an edge call whose vertex sits on an end the edge is not declared to have.
      This is the failure mode grep cannot find: ``direction`` defaults to
      ``outbound``, so a call on an edge whose vertex is the ``_to`` end deletes
      nothing while looking correct. **It runs over every edge, with no allowlist**
      (#1574). Until the membership declarations were corrected, two edges were
      exempt because R4's own oracle — ``GRAPH_EDGE_DEFINITIONS`` — was wrong for
      them; :class:`TestR4JudgesEveryDeclaredEdge` now pins that no edge can be
      exempted again, by enumerating the whole table rather than those two names.

``R5`` a vertex-wide ``delete_edges`` on a **symmetric** edge collection (one whose
      declared ``from`` and ``to`` sets are the same) that does not use
      ``direction="any"``. Such an edge is written in both directions for one
      logical relation — ``GraphRepository.set_adjacent_slots`` writes ``a → b``
      *and* ``b → a`` — so detaching a vertex outbound-only leaves the other half
      dangling. That was live in ``_delete_slot_internal`` two lines below the
      #1535 repair and is the one thing R4 cannot see: both ends are declared
      ``slots``, so the outbound spelling is *declaration*-legal and still wrong
      (#1573 review SCR-001). Judged per *function*, not per call: covering both
      ends with two calls is legitimate and live (``tank_repository.delete``), and a
      delete that names the **opposite endpoint** is a single ordered pair rather
      than a vertex detach, so it is left alone.

**Function-wide resolution, in statement order.** A name is resolved from the
assignments that *precede* the call in the same function, including inside nested
``if``/``for``/``with``/``try`` bodies (a branch gets a copy of the environment,
and names it binds are dropped again afterwards — a value bound in one branch says
nothing about the code below the branch). Both halves are load-bearing and both
were measured:

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
  arguments, but R4 cannot resolve the collection and stays silent);
* a call through an alias (``fn = repo.delete_edges``) or ``getattr``;
* arguments splatted from a dict (``repo.get_all_tasks(**kwargs)``) without also
  naming ``tenant_key`` — such a call is *reported* as unreadable rather than
  cleared, and the inventory must stay empty;
* an *empty* ``tenant_key`` passed explicitly, which is a value question, not a
  syntax one — ``_require_tenant_key`` in the repository and the service answers
  it, pinned in :class:`TestTheSurfacesStayStrict`;
* a **misleading but correct** spelling: ``substrate_repository.py:159`` passes the
  vertex positionally as ``from_id`` and sets ``direction="inbound"``, so the
  argument name says the opposite of what the call does. R4 reads the anchor, not
  the parameter name, so it passes — correctly. A readability rule against that
  spelling is a separate decision, deliberately not taken here.

**A scan can also fail by pointing at nothing**, which is why
:class:`TestTheScanHasACorpus` asserts that ``app/`` exists, that files were read
and that each rule still has a *live* subject in the tree. ``TestTheRulesFire``
proves the engine fires; only the corpus test proves it is aimed at the
application.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import pytest

from app.data_access.arango import collections as col
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

#: Positional order of ``create_edge(edge_collection, from_id, to_id)``.
_CREATE_EDGE_POSITIONAL = ("edge_collection", "from_id", "to_id")

#: The declared ends of every edge in the named graph, by collection name.
_DECLARED_ENDS = {d["edge_collection"]: d for d in col.GRAPH_EDGE_DEFINITIONS}


@dataclass
class _Violation:
    rule: str
    location: str
    detail: str

    def __str__(self) -> str:
        return f"{self.rule} {self.location}: {self.detail}"


@dataclass
class _Findings:
    """What one scan saw — returned, never accumulated in a module global."""

    violations: list[_Violation] = field(default_factory=list)
    #: ``get_all_tasks(**kwargs)`` calls that do not *also* name ``tenant_key``.
    unreadable_calls: list[str] = field(default_factory=list)
    #: Every ``delete_edges`` call, for the R5 post-pass:
    #: ``(scope, edge, anchor prefix, names opposite end, direction, location)``.
    deletes: list[tuple[str, str | None, str | None, bool, str | None, str]] = field(default_factory=list)
    files_scanned: int = 0
    #: Live subjects per rule, so the corpus test can prove the scan is aimed.
    subjects: dict[str, int] = field(default_factory=dict)

    def note_subject(self, kind: str) -> None:
        self.subjects[kind] = self.subjects.get(kind, 0) + 1


def _string_value(node: ast.AST, env: dict[str, str]) -> str | None:
    """Resolve ``node`` to a string, or ``None`` when it cannot be known statically.

    Handles literals, ``col.CONSTANT`` collection names, f-strings (an unknown
    interpolation becomes ``\\x00``, which is not a pattern character and therefore
    never invents a violation) and names bound earlier in the same scope.
    """
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.Name):
        return env.get(node.id)
    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id == "col":
            value = getattr(col, node.attr, None)
            return value if isinstance(value, str) else None
        return None
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


def _id_prefix(node: ast.AST | None, env: dict[str, str]) -> str | None:
    """The collection an id expression points into, when that is statically knowable."""
    if node is None:
        return None
    value = _string_value(node, env)
    if value is None or "/" not in value:
        return None
    prefix = value.split("/", 1)[0]
    return prefix if prefix and "\x00" not in prefix else None


def _call_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return None


def _bound_arguments(call: ast.Call, positional: tuple[str, ...]) -> dict[str, ast.AST]:
    arguments: dict[str, ast.AST] = {}
    for index, value in enumerate(call.args):
        if index < len(positional):
            arguments[positional[index]] = value
    for keyword in call.keywords:
        if keyword.arg:
            arguments[keyword.arg] = keyword.value
    return arguments


def _direction_of(arguments: dict[str, ast.AST]) -> str | None:
    """The literal ``direction`` of a call, or ``None`` when it is not a literal."""
    node = arguments.get("direction")
    if node is None:
        return "outbound"
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _check_declared_ends(
    *,
    edge: str | None,
    ends: list[tuple[str | None, str]],
    location: str,
    findings: _Findings,
) -> None:
    """R4 — every resolvable vertex must sit on an end the edge is declared to have.

    ``ends`` pairs a resolved collection prefix with the end it is used on
    (``from``/``to``/``any``). Unresolvable prefixes are skipped rather than
    guessed: a rule that reports what it cannot read produces the ten false
    positives the first draft of this sweep produced.
    """
    if edge is None or edge not in _DECLARED_ENDS:
        return
    findings.note_subject("edge_call_with_known_declaration")
    declared = _DECLARED_ENDS[edge]
    for prefix, end in ends:
        if prefix is None:
            continue
        if end == "from":
            allowed = declared["from_vertex_collections"]
        elif end == "to":
            allowed = declared["to_vertex_collections"]
        else:
            allowed = [*declared["from_vertex_collections"], *declared["to_vertex_collections"]]
        if prefix not in allowed:
            findings.violations.append(
                _Violation(
                    "R4",
                    location,
                    f"uses {prefix!r} on the {end!r} end of {edge!r}, which is declared "
                    f"{declared['from_vertex_collections']} → {declared['to_vertex_collections']}",
                )
            )


def _check_call(call: ast.Call, env: dict[str, str], location: str, findings: _Findings) -> None:
    name = _call_name(call)
    if name == "delete_edges":
        arguments = _bound_arguments(call, _DELETE_EDGES_POSITIONAL)
        findings.note_subject("delete_edges")

        for parameter in _ID_PARAMETERS:
            node = arguments.get(parameter)
            if node is not None and _carries_pattern(node, env):
                findings.violations.append(
                    _Violation(
                        "R1",
                        location,
                        f"{parameter}= carries a pattern character; delete_edges compares with "
                        "`==`, so it matches nothing (#1535)",
                    )
                )
        anchor = arguments.get("vertex_id") or arguments.get("from_id")
        opposite = arguments.get("other_id") or arguments.get("to_id")
        if opposite is not None and anchor is None:
            findings.violations.append(
                _Violation(
                    "R2",
                    location,
                    "names the opposite end without an anchor; delete_edges raises ValueError "
                    "before deleting anything (#1525)",
                )
            )

        direction = _direction_of(arguments)
        edge_collection = _string_value(arguments.get("edge_collection", ast.Constant(value=None)), env)
        findings.deletes.append(
            (
                location.rsplit(":", 1)[0],
                edge_collection,
                _id_prefix(anchor, env),
                opposite is not None,
                direction,
                location,
            )
        )
        if direction is not None:
            end = {"outbound": "from", "inbound": "to", "any": "any"}.get(direction)
            if end is not None:
                opposite_end = {"from": "to", "to": "from", "any": "any"}[end]
                _check_declared_ends(
                    edge=_string_value(arguments.get("edge_collection", ast.Constant(value=None)), env),
                    ends=[(_id_prefix(anchor, env), end), (_id_prefix(opposite, env), opposite_end)],
                    location=location,
                    findings=findings,
                )
    elif name == "create_edge":
        arguments = _bound_arguments(call, _CREATE_EDGE_POSITIONAL)
        findings.note_subject("create_edge")
        _check_declared_ends(
            edge=_string_value(arguments.get("edge_collection", ast.Constant(value=None)), env),
            ends=[
                (_id_prefix(arguments.get("from_id"), env), "from"),
                (_id_prefix(arguments.get("to_id"), env), "to"),
            ],
            location=location,
            findings=findings,
        )
    elif name == "get_all_tasks":
        findings.note_subject("get_all_tasks")
        names_tenant = any(keyword.arg == "tenant_key" for keyword in call.keywords)
        if names_tenant:
            return
        if any(keyword.arg is None for keyword in call.keywords):
            # ``**kwargs`` without an explicit tenant_key: unreadable, not cleared.
            findings.unreadable_calls.append(location)
            return
        findings.violations.append(
            _Violation(
                "R3",
                location,
                "does not name tenant_key; the page would be drawn from every tenant (#1533)",
            )
        )


def _nested_bodies(statement: ast.stmt) -> list[list[ast.stmt]]:
    """The statement lists a compound statement owns (branch bodies, loop bodies…)."""
    bodies: list[list[ast.stmt]] = []
    for attribute in ("body", "orelse", "finalbody"):
        value = getattr(statement, attribute, None)
        if isinstance(value, list) and value and isinstance(value[0], ast.stmt):
            bodies.append(value)
    for handler in getattr(statement, "handlers", []) or []:
        bodies.append(handler.body)
    return bodies


def _assigned_names(body: list[ast.stmt]) -> set[str]:
    names: set[str] = set()
    for statement in body:
        for node in ast.walk(statement):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.add(node.id)
    return names


def _walk_in_order(body: list[ast.stmt], env: dict[str, str], location: str, findings: _Findings) -> None:
    """Check ``body`` statement by statement, growing ``env`` as assignments pass.

    Statement order is what keeps a later rebinding of ``to_id`` from being read back
    onto an earlier call (the ``sensor_repository.create`` false positive). Nested
    bodies are walked with a *copy* of the environment and their bindings are
    invalidated afterwards, because a value assigned inside one branch is not a value
    the code after the branch can be assumed to hold.
    """
    for statement in body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue  # its own scope, visited separately
        nested = _nested_bodies(statement)
        nested_nodes = {id(node) for group in nested for stmt in group for node in ast.walk(stmt)}
        for node in ast.walk(statement):
            if isinstance(node, ast.Call) and id(node) not in nested_nodes:
                _check_call(node, env, f"{location}:{node.lineno}", findings)
        for group in nested:
            _walk_in_order(group, dict(env), location, findings)
            for name in _assigned_names(group):
                env.pop(name, None)
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            if isinstance(target, ast.Name):
                value = _string_value(statement.value, env)
                if value is None:
                    env.pop(target.id, None)
                else:
                    env[target.id] = value


#: The end(s) a ``direction`` detaches a vertex from.
_ENDS_OF_DIRECTION = {"outbound": {"from"}, "inbound": {"to"}, "any": {"from", "to"}}


def _apply_r5(findings: _Findings) -> None:
    """R5 — a vertex detach from a symmetric edge must cover both ends.

    Judged **per scope**, not per call, because covering both ends with two calls is
    a legitimate spelling and live: ``tank_repository.delete`` detaches ``feeds_from``
    outbound at one line and inbound five lines later. Judging each call alone
    reported that correct code — found by running this rule, not by reading it.

    A scope containing a ``delete_edges`` whose edge collection does not resolve (the
    ``for edge_col in [...]`` spelling) is **skipped entirely**: the unresolvable call
    may be the other half, and a rule that cannot see it must not claim it is absent.
    """
    opaque_scopes = {scope for scope, edge, *_ in findings.deletes if edge is None}
    coverage: dict[tuple[str, str, str], set[str]] = {}
    candidates: dict[tuple[str, str, str], tuple[str, str | None]] = {}
    for scope, edge, prefix, names_opposite, direction, location in findings.deletes:
        if edge is None or prefix is None or direction is None or names_opposite:
            continue
        declared = _DECLARED_ENDS.get(edge)
        if declared is None or set(declared["from_vertex_collections"]) != set(declared["to_vertex_collections"]):
            continue
        key = (scope, edge, prefix)
        coverage.setdefault(key, set()).update(_ENDS_OF_DIRECTION.get(direction, set()))
        candidates.setdefault(key, (location, direction))
    for key, (location, direction) in candidates.items():
        scope, edge, _prefix = key
        if scope in opaque_scopes or coverage[key] == {"from", "to"}:
            continue
        findings.violations.append(
            _Violation(
                "R5",
                location,
                f"detaches a vertex from the symmetric edge {edge!r} with direction={direction!r} "
                "and nothing in this function covers the other end; such an edge carries the "
                'relation in both directions, so the other half survives — use direction="any" '
                "(#1573 review SCR-001)",
            )
        )


def _dedupe(violations: list[_Violation]) -> list[_Violation]:
    """One report per (rule, call).

    A method is reached twice — once by the module-level pass walking into its class
    body, once by its own scope — and a doubled line reads like two defects. The
    function-scoped report wins because it names the function.
    """
    by_call: dict[tuple[str, str], _Violation] = {}
    for violation in violations:
        key = (violation.rule, violation.location.rsplit(":", 1)[-1] + "@" + violation.location.split("::")[0])
        if key not in by_call or "::" in violation.location:
            by_call[key] = violation
    return list(by_call.values())


def _scan_source(source: str, location: str, findings: _Findings) -> None:
    """Scan one module. R5 is applied by the caller, after every scope is recorded."""
    tree = ast.parse(source)
    _walk_in_order(tree.body, {}, location, findings)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _walk_in_order(node.body, {}, f"{location}::{node.name}", findings)


@cache
def _scan_application() -> _Findings:
    """Scan ``app/`` once.

    Cached: six test cases ask the same question, and re-parsing the whole tree for
    each of them made this guard the slowest module in the tier.
    """
    findings = _Findings()
    for path in sorted(_APP.rglob("*.py")):
        findings.files_scanned += 1
        _scan_source(path.read_text(encoding="utf-8"), str(path.relative_to(_APP.parent)), findings)
    _apply_r5(findings)
    findings.violations = _dedupe(findings.violations)
    return findings


class TestTheScanHasACorpus:
    """A scan over an empty tree is green and measures nothing (#1573 review SCR-002).

    ``rglob`` on a directory that does not exist yields nothing at all, and
    ``find_project_root`` anchors on ``pyproject.toml``, not on ``app/`` — so a moved
    or renamed source root would leave every assertion below trivially satisfied and
    every rule silently retired.
    """

    def test_the_application_tree_is_where_the_scan_looks(self) -> None:
        assert _APP.is_dir(), f"{_APP} is not a directory — the scan would read nothing"

    def test_files_were_actually_read(self) -> None:
        assert _scan_application().files_scanned > 100

    @pytest.mark.parametrize(
        "subject,minimum",
        [("delete_edges", 20), ("create_edge", 20), ("get_all_tasks", 1), ("edge_call_with_known_declaration", 20)],
    )
    def test_each_rule_still_has_a_live_subject(self, subject: str, minimum: int) -> None:
        """Proving the engine fires (``TestTheRulesFire``) is not proving it is aimed."""
        seen = _scan_application().subjects.get(subject, 0)
        assert seen >= minimum, f"only {seen} {subject} call(s) found under {_APP}"


class TestTheApplicationIsClean:
    def test_no_call_is_silently_unscoped_or_inert(self) -> None:
        violations = _scan_application().violations
        assert not violations, "Silently unscoped or inert calls:\n" + "\n".join(str(v) for v in violations)

    def test_no_call_hides_its_arguments_behind_a_splat(self) -> None:
        """A call R3 cannot read is not a call R3 has cleared."""
        unreadable = _scan_application().unreadable_calls
        assert unreadable == [], (
            "get_all_tasks is called with **kwargs and no explicit tenant_key, so this "
            "guard cannot see whether the tenant is among them:\n" + "\n".join(unreadable)
        )


#: A collection name that is in no edge definition, used to synthesise a wrong end.
_NOT_A_VERTEX = "zzz_no_such_vertex"


class TestR4JudgesEveryDeclaredEdge:
    """R4's oracle must cover the **class**, not the two edges #1574 happened to fix.

    Before #1574, ``has_membership`` and ``membership_in`` were exempt from R4 —
    ``GRAPH_EDGE_DEFINITIONS`` declared them against the direction
    ``ArangoMembershipRepository`` writes, so the rule's own oracle was wrong and
    the rule had to be silenced there. Silencing it meant a genuinely inert
    ``delete_edges(col.HAS_MEMBERSHIP, membership_id)`` — the default ``outbound``
    on an edge whose vertex is the ``_to`` end, removing nothing — passed this
    guard without a word. That is the shape this repository keeps paying for: a
    guard that exists and is inert.

    The repair is not "remove those two entries"; it is "make an entry
    impossible". These two cases run over **every** edge in the table, so an edge
    added tomorrow is judged on the day it is declared, and a future attempt to
    re-introduce a per-edge escape hatch fails here rather than going unnoticed:

    * the positive case proves R4 accepts each edge's *declared* direction, so the
      rule is reading the real table and not a constant ``True``;
    * the negative case proves R4 rejects a vertex on an end the edge does not
      have, for that same edge — the falsification of the exact expression the
      positive case asserts.
    """

    @staticmethod
    def _r4_details(source: str) -> list[str]:
        findings = _Findings()
        _scan_source(source, "<inline>", findings)
        _apply_r5(findings)
        return [v.detail for v in _dedupe(findings.violations) if v.rule == "R4"]

    def test_the_synthetic_wrong_end_is_really_absent_from_every_declaration(self) -> None:
        """Without this, the negative case below could be passing for the wrong reason."""
        declared = {
            name
            for definition in col.GRAPH_EDGE_DEFINITIONS
            for name in (*definition["from_vertex_collections"], *definition["to_vertex_collections"])
        }
        assert _NOT_A_VERTEX not in declared

    @pytest.mark.parametrize("edge", sorted(_DECLARED_ENDS))
    def test_the_declared_direction_is_accepted(self, edge: str) -> None:
        declared = _DECLARED_ENDS[edge]
        source = (
            "def f(self):\n"
            f'    self.create_edge("{edge}", '
            f'from_id="{declared["from_vertex_collections"][0]}/a", '
            f'to_id="{declared["to_vertex_collections"][0]}/b")\n'
        )
        assert self._r4_details(source) == [], f"R4 rejects the declared direction of {edge!r}"

    @pytest.mark.parametrize("edge", sorted(_DECLARED_ENDS))
    def test_a_vertex_on_an_end_the_edge_does_not_have_is_rejected(self, edge: str) -> None:
        declared = _DECLARED_ENDS[edge]
        source = (
            "def f(self):\n"
            f'    self.create_edge("{edge}", '
            f'from_id="{_NOT_A_VERTEX}/a", '
            f'to_id="{declared["to_vertex_collections"][0]}/b")\n'
        )
        assert self._r4_details(source), (
            f"R4 is inert for {edge!r} — a vertex from an undeclared collection was accepted "
            "on its 'from' end. No edge may be exempt from R4 (#1574)."
        )


class TestTheRulesFire:
    """The rules against the exact code each issue measured — red-first, mechanically.

    Without these, a refactor that broke the scan (an unhandled node type, a lost
    keyword) would leave every rule silently inert while the suite stayed green.
    """

    @staticmethod
    def _rules(source: str) -> set[str]:
        findings = _Findings()
        _scan_source(source, "<inline>", findings)
        _apply_r5(findings)
        return {v.rule for v in _dedupe(findings.violations)}

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

    def test_r1_reaches_into_a_nested_body(self) -> None:
        """A call inside an ``if``/``for`` is still a call (#1573 review SCR-010)."""
        source = (
            "def f(self, keys):\n"
            "    for key in keys:\n"
            '        anchor = "locations/%"\n'
            "        self.delete_edges(col.HAS_SLOT, from_id=anchor)\n"
        )
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

    def test_r4_catches_the_default_outbound_on_an_inbound_edge(self) -> None:
        """The #1535 line as it would have looked *without* the wildcard.

        ``has_slot`` is ``locations → slots``; anchoring a slot on the default
        ``outbound`` end deletes nothing and reads as correct — the failure mode no
        grep finds.
        """
        source = 'def f(self, key):\n    self.delete_edges(col.HAS_SLOT, from_id=f"{col.SLOTS}/{key}")\n'
        assert "R4" in self._rules(source)

    def test_r4_catches_a_create_edge_written_the_wrong_way_round(self) -> None:
        source = (
            "def f(self, location_key, slot_key):\n"
            '    self.create_edge(col.HAS_SLOT, f"{col.SLOTS}/{slot_key}", f"{col.LOCATIONS}/{location_key}")\n'
        )
        assert "R4" in self._rules(source)

    def test_r5_catches_the_adjacency_half_of_the_slot_delete(self) -> None:
        """``_delete_slot_internal`` as it stood before the #1573 review (SCR-001)."""
        source = (
            "def _delete_slot_internal(self, key):\n"
            '    slot_id = f"{col.SLOTS}/{key}"\n'
            "    self.delete_edges(col.ADJACENT_TO, from_id=slot_id)\n"
        )
        assert "R5" in self._rules(source)

    def test_r5_leaves_a_single_ordered_pair_alone(self) -> None:
        """``set_adjacent_slots`` deletes one direction at a time, on purpose."""
        source = (
            "def set_adjacent_slots(self, a, b):\n"
            '    a_id = f"{col.SLOTS}/{a}"\n'
            '    b_id = f"{col.SLOTS}/{b}"\n'
            "    self.delete_edges(col.ADJACENT_TO, a_id, b_id)\n"
            "    self.delete_edges(col.ADJACENT_TO, b_id, a_id)\n"
        )
        assert self._rules(source) == set()

    def test_r4_clears_the_membership_deletes_against_the_corrected_table(self) -> None:
        """The #1574 subject, judged rather than exempted.

        ``ArangoMembershipRepository.delete`` detaches the membership from both
        edges: inbound on ``has_membership`` (the membership is its ``_to`` end)
        and outbound on ``membership_in`` (its ``_from`` end). Both spellings were
        already correct; what changed is that R4 now reads a table that agrees
        with them, so it clears them on their merits instead of skipping them.
        """
        source = (
            "def delete(self, key):\n"
            '    membership_id = f"{col.MEMBERSHIPS}/{key}"\n'
            '    self.delete_edges(col.HAS_MEMBERSHIP, membership_id, direction="inbound")\n'
            "    self.delete_edges(col.MEMBERSHIP_IN, membership_id)\n"
        )
        assert self._rules(source) == set()

    def test_r4_catches_the_inert_membership_delete_the_allowlist_used_to_hide(self) -> None:
        """The deletion R4 is *supposed* to refuse, and did not while #1574 stood.

        ``memberships`` is the ``_to`` end of ``has_membership``, so an outbound
        (default) detach anchored on it removes nothing and raises nothing. With
        the old allowlist this call passed the guard in silence.
        """
        source = (
            "def delete(self, key):\n"
            '    membership_id = f"{col.MEMBERSHIPS}/{key}"\n'
            "    self.delete_edges(col.HAS_MEMBERSHIP, membership_id)\n"
        )
        assert "R4" in self._rules(source)

    def test_the_repaired_spellings_pass(self) -> None:
        source = (
            "def f(self, task_repo, key, tenant_key):\n"
            '    slot_id = f"{col.SLOTS}/{key}"\n'
            '    self.delete_edges(col.HAS_SLOT, vertex_id=slot_id, direction="inbound")\n'
            '    self.delete_edges(col.ADJACENT_TO, vertex_id=slot_id, direction="any")\n'
            "    task_repo.get_all_tasks(0, 200, None, tenant_key=tenant_key)\n"
        )
        assert self._rules(source) == set()

    def test_a_splat_that_names_the_tenant_is_not_reported(self) -> None:
        findings = _Findings()
        _scan_source(
            "def f(task_repo, kw, tenant_key):\n    task_repo.get_all_tasks(**kw, tenant_key=tenant_key)\n",
            "<inline>",
            findings,
        )
        assert findings.unreadable_calls == []
        assert findings.violations == []

    def test_a_splat_without_the_tenant_is_reported_as_unreadable(self) -> None:
        findings = _Findings()
        _scan_source("def f(task_repo, kw):\n    task_repo.get_all_tasks(**kw)\n", "<inline>", findings)
        assert findings.unreadable_calls
        assert findings.violations == []

    def test_a_later_rebinding_is_not_read_onto_an_earlier_call(self) -> None:
        """The ``sensor_repository.create`` shape: same name, two values, in order."""
        source = (
            "def create(self, sensor):\n"
            '    to_id = f"{col.TANKS}/{sensor.tank_key}"\n'
            "    self.delete_edges(col.MONITORS_TANK, from_id=to_id)\n"
            '    to_id = "locations/%"\n'
        )
        assert "R1" not in self._rules(source)

    def test_a_binding_from_a_branch_does_not_leak_past_it(self) -> None:
        source = (
            "def f(self, flag):\n"
            "    if flag:\n"
            '        anchor = "locations/%"\n'
            "    self.delete_edges(col.HAS_SLOT, from_id=anchor)\n"
        )
        assert "R1" not in self._rules(source)


class TestTheSurfacesStayStrict:
    """The signatures themselves, because a call-site scan cannot see a default.

    ``tenant_key`` back as an optional parameter would make every one of the repaired
    call sites legal again with one argument dropped — which is exactly how #1533
    happened.
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

    def test_the_service_rejects_the_empty_tenant_too(self) -> None:
        """The value half at the layer the routers actually call (#1573 review SCR-007).

        Keyword-only without a default stops the *omission*; only this stops
        ``tenant_key=""``, which the repository used to read as "every tenant".
        """

        class _Repo:
            def get_all_tasks(self, *args, **kwargs):  # pragma: no cover - must not be reached
                raise AssertionError("list_tasks reached the repository with an empty tenant_key")

        service = TaskService.__new__(TaskService)
        service._repo = _Repo()
        with pytest.raises(ValueError, match="tenant"):
            service.list_tasks(0, 50, None, tenant_key="")

    def test_delete_edges_still_compares_with_equality(self) -> None:
        """R1's premise: a pattern really is inert here.

        If ``delete_edges`` ever grew a ``LIKE``, R1 would be forbidding a spelling
        that had become legitimate — a rule whose reason has quietly expired.
        """
        source = inspect.getsource(BaseArangoRepository.delete_edges)
        assert "e._from == @vertex" in source
        assert "e._to == @vertex" in source
        assert "LIKE" not in source.upper().replace("LIKELY", "")
