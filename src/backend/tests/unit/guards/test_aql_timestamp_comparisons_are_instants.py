"""#1784 class guard — an AQL ordering comparison on a stored timestamp compares instants.

**The class.** ArangoDB orders strings by ICU collation, and this system stores
one instant in several spellings (``…:00Z``, ``…:00.500000Z``, ``…:00+00:00``,
``…:00.000Z``). ``.`` collates before ``+`` and ``Z``, so ``doc.expires_at <
@now`` read ``'…:00.5Z' < '…:00+00:00'`` as true although the record expires
half a second *later* — retention sweeps deleted records that were not due and
kept ones that were (#1786 was the first measured instance, #1784 the other 30
sites). A sibling of the same class: an AQL date function that returns a
**string** (``DATE_ADD``, ``DATE_ISO8601``, …) compared with ``DATE_NOW()``, a
number — AQL orders every string above every number, so the Karenz list showed
every treatment ever applied as an active waiting period.

**The rule, stated as a rule and not as today's sites.** In a string expression
anywhere in ``app/``, an ordering operator (``<``, ``<=``, ``>``, ``>=``) whose
left or right operand is

* a **bare attribute path** (``doc.expires_at``, ``w.logged_at``) naming a
  timestamp, or
* a call to an AQL date function that returns a string
  (:data:`_STRING_DATE_FUNCTIONS`)

is a finding. The fix is ``DATE_TIMESTAMP(doc.x) <op> DATE_TIMESTAMP(@bind)``
(see the module docstring of :mod:`app.data_access.arango.query_builder` for the
null and millisecond reasoning). A wrapped operand (``DATE_TIMESTAMP(…)``,
``LEFT(doc.due_date, 10)``) is not bare and not a finding.

The **timestamp name set is derived**, not typed out: every field of every
Pydantic model under :mod:`app.domain.models` whose annotation contains
``datetime``, united with every name ending in ``_at``. A field typed only as
``date`` (``planted_on``) is stored as fixed-width ``YYYY-MM-DD`` and compares
correctly as text, so it is not in the set.

**Filter triples.** ``AQLBuilder.filter`` compares instants itself for a
``datetime`` value or a string value on a ``*_at`` field
(``tests/unit/data_access/arango/test_query_builder.py`` pins that). What it
cannot see is a *string* value on a timestamp field whose name does not end in
``_at`` (``due_date``, ``valid_until``) — so a literal triple or
``.filter(...)`` call with an ordering operator on such a name is a finding
(pass a ``datetime``). A ``.filter`` call whose field is not a literal is a
pass-through of triples written elsewhere and must be named in
:data:`_PASS_THROUGH`.

**NFR-018 §2.3.** The detector never matches raw source text: it parses with
:func:`ast.parse`, reads only string expressions (docstrings skipped — a Python
comment is not in the tree at all), and strips AQL ``//`` and ``/* */`` comments
from each string before it looks for an operator. The falsification tests at the
bottom hold it to that from both ends.

Spellings this does NOT match
-----------------------------

Named rather than discovered later:

* a comparison against a **LET variable** derived from a timestamp
  (``LET t = doc.created_at … FILTER t < @x``) — the variable is not an attribute
  path; ``RETURN``-ed lists compared later (``FOR d IN due_dates FILTER d < …``)
  likewise;
* **bracket access** (``doc["expires_at"]``, ``doc[@field]``) and field names
  built in Python (``f"doc.{field} < @x"``) — the latter is *reported* as an
  unresolved comparison (:data:`_EXPECTED_UNRESOLVED`), not skipped;
* a comparison whose operator itself is spliced in (``f"doc.x {op} @y"``) or
  whose operands are split across two string literals joined at run time by
  anything but ``+``;
* ``SORT`` ordering — out of scope: sorting mixed spellings misorders, it does
  not select;
* date-typed fields (``date``, not ``datetime``), and ``LEFT(doc.x, 10)``
  date-prefix comparisons — deliberately not in the class;
* an AQL string literal that contains ``//`` truncates the rest of that line
  for this detector (it is read as a comment start).
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
import re
import types
import typing
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from pathlib import Path

import pytest
from pydantic import BaseModel

import app.domain.models as models_package
from app.data_access.arango.query_builder import AQLBuilder
from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: AQL date functions that return an ISO **string**; ordering one against a
#: number (``DATE_NOW()``) or another spelling is the Karenz defect.
_STRING_DATE_FUNCTIONS = frozenset({"DATE_ADD", "DATE_SUBTRACT", "DATE_ISO8601", "DATE_FORMAT", "DATE_TRUNC"})

_ORDERING_OPS = frozenset({"<", "<=", ">", ">="})

#: What an f-string placeholder becomes. Contains no operator character, so a
#: placeholder cannot fake a comparison.
_PLACEHOLDER = "__EXPR__"

#: Findings that are not repaired here, keyed by ``(file relative to app/,
#: function)``, each with the reason. An entry is a decision someone wrote down,
#: and :func:`test_every_allowlist_entry_still_matches_a_site` keeps an entry
#: from outliving its site — the repair of a listed site must delete its entry.
_ALLOWLIST: dict[tuple[str, str], str] = {
    ("data_access/arango/ipm_repository.py", "get_active_karenz_periods"): (
        "KNOWN DEFECT, tracked separately from #1784 by operator decision: "
        "DATE_ADD(...) > DATE_NOW() orders a string against a number and is true for every "
        "application, so GET .../karenz lists ended waiting periods as active. The harvest gate "
        "(check_harvest_safety) re-checks in Python and is not affected."
    ),
}

#: ``.filter(field, op, value)`` calls with a non-literal field. They forward
#: :data:`FilterTriple` lists; the literal triples are checked where written.
_PASS_THROUGH: dict[tuple[str, str], str] = {
    ("data_access/arango/base_repository.py", "_find_docs"): "forwards the caller's FilterTriple list",
    ("data_access/arango/base_repository.py", "get_page"): "forwards the caller's FilterTriple list",
}

#: Ordering comparisons with an f-string placeholder as an operand: the field
#: name is built in Python and this guard cannot read it. Pinned so that a new
#: one is a diff to this file, not a silent narrowing.
_EXPECTED_UNRESOLVED: dict[tuple[str, str], str] = {}


# ── the derived timestamp name set ────────────────────────────────────────────


def _mentions_datetime(annotation: object) -> bool:
    if annotation is datetime:
        return True
    origin = typing.get_origin(annotation)
    if origin is None and not isinstance(annotation, types.UnionType):
        return False
    return any(_mentions_datetime(arg) for arg in typing.get_args(annotation))


@cache
def timestamp_names() -> frozenset[str]:
    """Every model field typed ``datetime`` (optionally in a union), plus every ``*_at`` name."""
    names: set[str] = set()
    for info in pkgutil.walk_packages(models_package.__path__, prefix=f"{models_package.__name__}."):
        module = importlib.import_module(info.name)
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, BaseModel) and value is not BaseModel:
                for name, field in value.model_fields.items():
                    if _mentions_datetime(field.annotation):
                        names.add(name)
    return frozenset(names)


def _is_timestamp_name(name: str) -> bool:
    return name.endswith("_at") or name in timestamp_names()


# ── reading string expressions out of the parse tree ──────────────────────────


def _render(node: ast.AST) -> str | None:
    """The text of a string expression: a literal, an f-string, or a ``+`` chain of those."""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.JoinedStr):
        return "".join(str(part.value) if isinstance(part, ast.Constant) else _PLACEHOLDER for part in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _render(node.left), _render(node.right)
        return None if left is None or right is None else left + right
    return None


def _docstring_nodes(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = node.body
            first = body[0] if body else None
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                ids.add(id(first.value))
    return ids


def _string_expressions(node: ast.AST, skip: set[int]):
    """Yield ``(node, text)`` for every maximal string expression below ``node``."""
    if id(node) in skip:
        return
    text = _render(node)
    if text is not None and isinstance(node, ast.Constant | ast.JoinedStr | ast.BinOp):
        yield node, text
        if isinstance(node, ast.JoinedStr):
            # Strings inside a placeholder (``f"{helper('doc.x < @y')}"``) are read too.
            for part in node.values:
                if isinstance(part, ast.FormattedValue):
                    yield from _string_expressions(part.value, skip)
        return
    for child in ast.iter_child_nodes(node):
        yield from _string_expressions(child, skip)


_AQL_COMMENTS = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)


def strip_aql_comments(text: str) -> str:
    """Remove AQL ``/* … */`` and ``// …`` comments, keeping line breaks for line numbers."""
    return _AQL_COMMENTS.sub(lambda m: "\n" * m.group(0).count("\n"), text)


# ── finding the comparisons ──────────────────────────────────────────────────

_OPERATOR = re.compile(r"<=|>=|<|>")
_TOKEN_CHARS = re.compile(r"[\w.@\[\]]")
_BARE_PATH = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+")


def _left_operand(text: str, end: int) -> str:
    i = end - 1
    while i >= 0 and text[i] in " \t\r\n":
        i -= 1
    if i < 0:
        return ""
    if text[i] == ")":
        depth, j = 0, i
        while j >= 0:
            if text[j] == ")":
                depth += 1
            elif text[j] == "(":
                depth -= 1
                if depth == 0:
                    break
            j -= 1
        k = j - 1
        while k >= 0 and (text[k].isalnum() or text[k] == "_"):
            k -= 1
        return text[k + 1 : i + 1]
    k = i
    while k >= 0 and _TOKEN_CHARS.match(text[k]):
        k -= 1
    return text[k + 1 : i + 1]


def _right_operand(text: str, start: int) -> str:
    i = start
    while i < len(text) and text[i] in " \t\r\n":
        i += 1
    k = i
    while k < len(text) and _TOKEN_CHARS.match(text[k]):
        k += 1
    if k < len(text) and text[k] == "(":
        depth, j = 0, k
        while j < len(text):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        return text[i : j + 1]
    return text[i:k]


def _bare_timestamp(operand: str) -> bool:
    return bool(_BARE_PATH.fullmatch(operand)) and _is_timestamp_name(operand.rsplit(".", 1)[-1])


def _string_date_call(operand: str) -> bool:
    match = re.match(r"([A-Z_0-9]+)\s*\(", operand)
    return bool(match) and match.group(1) in _STRING_DATE_FUNCTIONS


#: ``doc.{field}`` — an attribute whose *name* is spliced in.
_BUILT_ATTRIBUTE = re.compile(rf"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\.{_PLACEHOLDER}")


def _built_in_python(operand: str, other: str) -> bool:
    """Whether ``operand`` is a field reference this guard cannot read.

    Either an attribute whose name is spliced in (``doc.{field}``), or a whole
    placeholder compared with something that is unmistakably AQL — a bind
    variable, an attribute path, a date function. A placeholder against another
    placeholder or against prose (``f"{a} > {b}"`` in a log message, HTML
    ``<b>{x}</b>``) is not a query and not reported.
    """
    if _BUILT_ATTRIBUTE.fullmatch(operand):
        return True
    if operand != _PLACEHOLDER:
        return False
    return other.startswith("@") or bool(_BARE_PATH.fullmatch(other)) or other.startswith("DATE_")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    function: str
    what: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line} in {self.function}(): {self.what}"


def _comparisons(text: str) -> list[tuple[int, str, str, str]]:
    """``(line offset, left, op, right)`` for every ordering operator in ``text``."""
    found = []
    for match in _OPERATOR.finditer(text):
        left = _left_operand(text, match.start())
        right = _right_operand(text, match.end())
        found.append((text.count("\n", 0, match.start()), left, match.group(0), right))
    return found


def _enclosing_functions(tree: ast.AST) -> dict[int, str]:
    """Map ``id(node)`` of every node to the name of the innermost function holding it."""
    owner: dict[int, str] = {}

    def visit(node: ast.AST, name: str) -> None:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            name = node.name
        owner[id(node)] = name
        for child in ast.iter_child_nodes(node):
            visit(child, name)

    visit(tree, "<module>")
    return owner


def scan_source(source: str, rel_path: str) -> tuple[list[Finding], list[Finding], list[Finding]]:
    """``(findings, unresolved, pass_throughs)`` for one Python source file.

    ``findings`` are rule violations; ``unresolved`` are ordering comparisons with
    an f-string placeholder as an operand; ``pass_throughs`` are ``.filter`` calls
    whose field is not a literal.
    """
    tree = ast.parse(source)
    owner = _enclosing_functions(tree)
    skip = _docstring_nodes(tree)
    findings: list[Finding] = []
    unresolved: list[Finding] = []
    pass_throughs: list[Finding] = []

    for node, text in _string_expressions(tree, skip):
        code = strip_aql_comments(text)
        for offset, left, op, right in _comparisons(code):
            where = (rel_path, node.lineno + offset, owner.get(id(node), "<module>"))
            shown = f"{left} {op} {right}"
            if _bare_timestamp(left) or _bare_timestamp(right):
                findings.append(Finding(*where, f"bare timestamp compared as a string: {shown}"))
            elif _string_date_call(left) or _string_date_call(right):
                findings.append(Finding(*where, f"string-returning date function in an ordering: {shown}"))
            elif _built_in_python(left, right) or _built_in_python(right, left):
                unresolved.append(Finding(*where, f"operand built in Python: {shown}"))

    for node in ast.walk(tree):
        field_node = op_node = None
        if isinstance(node, ast.Tuple) and len(node.elts) == 3:
            field_node, op_node = node.elts[0], node.elts[1]
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "filter"
            and len(node.args) >= 2
        ):
            field_node, op_node = node.args[0], node.args[1]
            if not isinstance(field_node, ast.Constant):
                pass_throughs.append(Finding(rel_path, node.lineno, owner.get(id(node), "<module>"), "filter()"))
                continue
        if field_node is None or not isinstance(op_node, ast.Constant) or op_node.value not in _ORDERING_OPS:
            continue
        if not (isinstance(field_node, ast.Constant) and isinstance(field_node.value, str)):
            continue
        name = field_node.value.rsplit(".", 1)[-1]
        if _is_timestamp_name(name) and not name.endswith("_at"):
            findings.append(
                Finding(
                    rel_path,
                    node.lineno,
                    owner.get(id(node), "<module>"),
                    f"filter triple ({field_node.value!r}, {op_node.value!r}, …): AQLBuilder compares instants "
                    "only for a datetime value or a *_at field — pass a datetime",
                )
            )
    return findings, unresolved, pass_throughs


@cache
def _scan_app() -> tuple[tuple[Finding, ...], tuple[Finding, ...], tuple[Finding, ...]]:
    findings: list[Finding] = []
    unresolved: list[Finding] = []
    pass_throughs: list[Finding] = []
    for path in sorted(_APP.rglob("*.py")):
        rel = str(path.relative_to(_APP))
        f, u, p = scan_source(path.read_text(encoding="utf-8"), rel)
        findings += f
        unresolved += u
        pass_throughs += p
    return tuple(findings), tuple(unresolved), tuple(pass_throughs)


# ── the rule over app/ ────────────────────────────────────────────────────────


def test_every_timestamp_ordering_in_app_compares_instants() -> None:
    findings, _, _ = _scan_app()
    offenders = [str(f) for f in findings if (f.path, f.function) not in _ALLOWLIST]

    assert offenders == [], (
        "An AQL ordering comparison reads a stored timestamp as a string (#1784). ArangoDB collates "
        "'…:00.5Z' before '…:00+00:00', so the record lands on the wrong side of the cutoff. Compare "
        "instants: DATE_TIMESTAMP(doc.x) <op> DATE_TIMESTAMP(@bind), and decide what a null/unreadable "
        "value means for a < selector (see app/data_access/arango/query_builder.py). Or add the site to "
        "_ALLOWLIST with its reason.\n  " + "\n  ".join(offenders)
    )


def test_every_allowlist_entry_still_matches_a_site() -> None:
    findings, _, _ = _scan_app()
    sites = {(f.path, f.function) for f in findings}

    assert sorted(set(_ALLOWLIST) - sites) == [], "an _ALLOWLIST entry names no finding any more: remove it"


def test_unresolved_comparisons_are_reported_rather_than_assumed_safe() -> None:
    _, unresolved, _ = _scan_app()
    sites = {(u.path, u.function) for u in unresolved}

    assert sites == set(_EXPECTED_UNRESOLVED), (
        "The set of ordering comparisons whose operand is built in Python changed. Each is outside this "
        "guard's reach; name it in _EXPECTED_UNRESOLVED with the reason it is not a timestamp, or write the "
        "field literally.\n  " + "\n  ".join(str(u) for u in unresolved)
    )


def test_every_non_literal_filter_call_is_a_named_pass_through() -> None:
    _, _, pass_throughs = _scan_app()
    sites = {(p.path, p.function) for p in pass_throughs}

    assert sites == set(_PASS_THROUGH), "\n  ".join(str(p) for p in pass_throughs)


def test_the_builder_compares_instants_for_the_triples_it_is_trusted_with() -> None:
    """What makes an ``*_at`` triple with a string value, or any datetime value, safe to skip above."""
    for field in ("created_at", "expires_at"):
        query, bind_vars = AQLBuilder("c").filter(field, "<", "2025-09-25T04:30:00+00:00").build_list()
        assert f"DATE_TIMESTAMP(doc.{field}) < DATE_TIMESTAMP(@v0)" in query
    query, bind_vars = AQLBuilder("c").filter("due_date", ">=", datetime(2025, 9, 25)).build_list()
    assert "DATE_TIMESTAMP(doc.due_date) >= DATE_TIMESTAMP(@v0)" in query
    assert bind_vars["v0"] == "2025-09-25T00:00:00"


# ── the derived name set ──────────────────────────────────────────────────────


def test_the_name_set_is_derived_from_the_models() -> None:
    names = timestamp_names()

    assert {"due_date", "valid_until", "harvest_date", "logged_at"} <= names
    # ``planted_on`` is a ``date`` on PlantInstance and nowhere a ``datetime``.
    assert "planted_on" not in names
    assert not _is_timestamp_name("planted_on")


# ── falsification: the detector reads code, not prose (NFR-018 §2.3) ──────────


def _findings(source: str) -> list[Finding]:
    return scan_source(source, "probe.py")[0]


def test_a_comparison_only_in_a_docstring_or_a_comment_is_no_finding() -> None:
    source = '''
def purge():
    """Deletes where doc.expires_at < @now, compared as text before #1784."""
    # FILTER doc.expires_at < @now
    return "FILTER DATE_TIMESTAMP(doc.expires_at) < DATE_TIMESTAMP(@now)"
'''
    assert _findings(source) == []


def test_a_real_bare_comparison_is_a_finding_no_comment_removes() -> None:
    source = '''
def purge():
    """Compares DATE_TIMESTAMP(doc.expires_at), honestly."""
    # DATE_TIMESTAMP(doc.expires_at) < DATE_TIMESTAMP(@now) -- instants, promise
    return "FILTER doc.expires_at < @now"  # instant comparison
'''
    (finding,) = _findings(source)
    assert finding.function == "purge"
    assert "doc.expires_at < @now" in finding.what


def test_a_wrapped_operand_is_no_finding() -> None:
    source = """
def q():
    return "FILTER DATE_TIMESTAMP(doc.expires_at) < DATE_TIMESTAMP(@now) AND LEFT(doc.due_date, 10) <= @today"
"""
    assert _findings(source) == []


def test_an_aql_comment_is_no_finding() -> None:
    source = '''
def q():
    return """
    FOR doc IN c
      // FILTER doc.expires_at < @now
      /* doc.created_at < @cutoff */
      RETURN doc
    """
'''
    assert _findings(source) == []


def test_a_reversed_operand_order_is_a_finding() -> None:
    assert len(_findings('def q():\n    return "FILTER @now > doc.expires_at"\n')) == 1


def test_an_f_string_fragment_and_a_concatenation_are_read() -> None:
    source = """
def q(filters, name):
    filters.append(f"doc.filled_at >= @start_{name}")
    return "FILTER doc.tenant_key == @t " + "AND doc.created_at < @cutoff"
"""
    assert len(_findings(source)) == 2


def test_a_string_date_function_against_a_number_is_a_finding() -> None:
    source = """
def q():
    return "FILTER DATE_ADD(ta.applied_at, t.days, 'days') > DATE_NOW()"
"""
    (finding,) = _findings(source)
    assert "string-returning date function" in finding.what


def test_a_date_typed_field_is_no_finding() -> None:
    assert _findings('def q():\n    return "FILTER v.planted_on >= @cutoff"\n') == []


def test_a_field_built_in_python_is_reported_as_unresolved() -> None:
    findings, unresolved, _ = scan_source('def q(field):\n    return f"FILTER doc.{field} < @now"\n', "probe.py")
    # ``doc.__EXPR__`` names no timestamp the guard can read: reported, not passed.
    assert findings == []
    (entry,) = unresolved
    assert entry.function == "q"


def test_a_timestamp_triple_the_builder_cannot_recognise_is_a_finding() -> None:
    source = """
def q(now_iso, now):
    a = ("due_date", "<", now_iso)
    b = ("created_at", "<", now_iso)
    c = ("retry_count", "<", 3)
    return a, b, c
"""
    (finding,) = _findings(source)
    assert "'due_date'" in finding.what


@pytest.mark.parametrize("op", sorted(_ORDERING_OPS))
def test_every_ordering_operator_is_seen(op: str) -> None:
    assert len(_findings(f'def q():\n    return "FILTER doc.expires_at {op} @now"\n')) == 1
