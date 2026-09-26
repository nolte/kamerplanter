"""#1856 — every placeholder of an HTML mail body is escaped, or built only from escaped and fixed values.

The defect class: ``SmtpEmailAdapter.send_verification_email`` and
``send_password_reset_email`` wrote ``<p>Hello {display_name},</p>`` and
``<a href="{url}">`` into the HTML body. The step-up code mail next to them
escaped the same name; the two older siblings did not. Escaping was opt-in per
f-string, and the siblings drifted.

**Predicate** — an f-string whose literal text contains an HTML tag (``<p>``,
``<a href=...>``, ``</div>``), in a module that builds mail (``app/data_access/external``,
``app/domain/services``, ``app/tasks``). Each of its placeholders must be *safe*:

* ``escape(...)`` / ``html.escape(...)``, also followed by ``.replace(...)``;
* a constant, ``len(...)``, a ``.get(...)`` on a module-level ``UPPER_CASE`` map;
* an f-string, ``+`` or conditional expression of safe parts;
* a local name every assignment of which (``=``, ``+=``) in the same function is safe.

**Spellings this predicate cannot see:** an HTML body built by ``+``
concatenation or ``str.format`` / ``%`` without an f-string, a template file, a
body assembled in a module outside the three directories, and a safe-looking
local that a nested function or ``nonlocal`` rebinds.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
SCOPES = (APP / "data_access" / "external", APP / "domain" / "services", APP / "tasks")
_TAG = re.compile(r"</?[a-zA-Z][a-zA-Z0-9]*(\s[^<>]*)?/?>|<[a-zA-Z][a-zA-Z0-9]*\s")

#: The class size measured when this guard was written (#1856): 8 on develop, +1 the e-mail change mail (#1848).
EXPECTED_HTML_FSTRINGS = 9


def _is_escape_call(node: ast.expr) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == "escape":
        return True
    if isinstance(func, ast.Attribute) and func.attr == "escape":
        return True
    # escape(x).replace("\n", "<br>")
    return isinstance(func, ast.Attribute) and func.attr == "replace" and _is_escape_call(func.value)


class _Scope:
    def __init__(self, function: ast.AST | None) -> None:
        self.assignments: dict[str, list[ast.expr]] = {}
        self.unsafe_names: set[str] = set()
        if function is None:
            return
        for node in ast.walk(function):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.assignments.setdefault(target.id, []).append(node.value)
            elif isinstance(node, ast.AugAssign | ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.value is not None:
                    self.assignments.setdefault(node.target.id, []).append(node.value)
            elif isinstance(node, ast.For | ast.comprehension) and isinstance(node.target, ast.Name):
                self.unsafe_names.add(node.target.id)
        if isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
            self.unsafe_names.update(a.arg for a in function.args.args + function.args.kwonlyargs)


def _safe(node: ast.expr, scope: _Scope, seen: frozenset[str] = frozenset()) -> bool:
    if isinstance(node, ast.Constant) or _is_escape_call(node):
        return True
    if isinstance(node, ast.JoinedStr):
        return all(_safe(v.value, scope, seen) for v in node.values if isinstance(v, ast.FormattedValue))
    if isinstance(node, ast.BinOp):
        return _safe(node.left, scope, seen) and _safe(node.right, scope, seen)
    if isinstance(node, ast.IfExp):
        return _safe(node.body, scope, seen) and _safe(node.orelse, scope, seen)
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id == "len":
            return True
        return (
            isinstance(func, ast.Attribute)
            and func.attr == "get"
            and isinstance(func.value, ast.Name)
            and func.value.id.lstrip("_").isupper()
        )
    if isinstance(node, ast.Name):
        if node.id in scope.unsafe_names or node.id in seen or node.id not in scope.assignments:
            return False
        return all(_safe(value, scope, seen | {node.id}) for value in scope.assignments[node.id])
    return False


def _html_fstrings() -> list[tuple[str, int, list[str]]]:
    """(file:line, placeholders that are not safe) of every HTML f-string in scope."""
    found: list[tuple[str, int, list[str]]] = []
    for root in SCOPES:
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            parents: dict[ast.AST, ast.AST] = {}
            for parent in ast.walk(tree):
                for child in ast.iter_child_nodes(parent):
                    parents[child] = parent
            for node in ast.walk(tree):
                if not isinstance(node, ast.JoinedStr):
                    continue
                # Only the outermost f-string of an implicit concatenation / nesting.
                if isinstance(parents.get(node), ast.FormattedValue):
                    continue
                literal = "".join(v.value for v in node.values if isinstance(v, ast.Constant))
                if not _TAG.search(literal):
                    continue
                function = node
                while function in parents and not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
                    function = parents[function]
                scope = _Scope(function if isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef) else None)
                unsafe = [
                    ast.unparse(v.value)
                    for v in node.values
                    if isinstance(v, ast.FormattedValue) and not _safe(v.value, scope)
                ]
                found.append((path.relative_to(APP).as_posix(), node.lineno, unsafe))
    return found


def test_every_html_mail_placeholder_is_escaped() -> None:
    unescaped = [f"{path}:{line} {unsafe}" for path, line, unsafe in _html_fstrings() if unsafe]

    assert unescaped == [], (
        "An HTML mail body interpolates a value that is neither escaped nor built from escaped/fixed values "
        "(#1856) — wrap it in html.escape():\n  " + "\n  ".join(unescaped)
    )


def test_the_predicate_sees_the_class() -> None:
    found = _html_fstrings()
    print(f"html f-strings in mail code: {len(found)}")  # noqa: T201 - the measured count, read by the reviewer
    for path, line, unsafe in found:
        print(f"  {path}:{line} unsafe={unsafe}")  # noqa: T201

    assert len(found) == EXPECTED_HTML_FSTRINGS, found
    assert any(path.endswith("smtp_email_adapter.py") for path, _, _ in found)
    assert any(path.endswith("email_notification_channel.py") for path, _, _ in found)


def test_the_predicate_refuses_an_unescaped_name() -> None:
    tree = ast.parse('def f(name):\n    return f"<p>Hello {name}</p>"\n')
    function = tree.body[0]
    fstring = function.body[0].value  # type: ignore[attr-defined]

    assert _safe(fstring.values[1].value, _Scope(function)) is False


def test_the_predicate_accepts_an_escaped_local() -> None:
    tree = ast.parse('def f(name):\n    safe = escape(name)\n    return f"<p>Hello {safe}</p>"\n')
    function = tree.body[0]
    fstring = function.body[1].value  # type: ignore[attr-defined]

    assert _safe(fstring.values[1].value, _Scope(function)) is True
