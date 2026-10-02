"""#1881 class guard — no service constructor or factory accepts a parameter it never reads.

``AuthService``, ``StepUpVerifier`` and ``UserService`` kept taking a
``tombstone_salt`` that nothing used after #1812 moved the log pseudonyms to
``LOG_PSEUDONYM_SALT``. A parameter named after the non-rotatable erasure salt
that keys nothing invites the next change to key something with it again.

**The rule.** In ``app/domain/services/``, every parameter of an ``__init__`` or
of a module-level function is loaded (read, forwarded, stored) somewhere in that
function's own body, and a *salt* parameter stored as ``self._x = salt`` is read
back as ``self._x`` somewhere in its class (the stored-and-never-read spelling is
the one #1881 was: the services stored the erasure salt and nothing read it).
The stored-and-never-read check is limited to salt-named parameters: a salt that
keys nothing invites the next change to key something with it. A name starting
with ``_`` is exempt (the explicit "unused").

Spellings this does NOT see
---------------------------

* a parameter stored on ``self`` under a *different expression* (``self._x = x or y``,
  a conversion) — only the plain ``self._x = x`` is traced to a read of ``self._x``;
* an attribute read through ``getattr(self, "_x")`` or from another object;
* a parameter used only inside a nested function or lambda that is itself dead;
* ``__init__`` parameters of classes outside ``app/domain/services/``
  (``UnsupportedMediaTypeError.content_type`` in ``app/common/exceptions.py`` is
  one such, tracked separately).
"""

from __future__ import annotations

import ast
from pathlib import Path

SERVICES = Path(__file__).resolve().parents[3] / "app" / "domain" / "services"


def unread_parameters(source: str) -> list[tuple[str, str]]:
    """``(function qualname, parameter)`` for every parameter its function never loads."""
    tree = ast.parse(source)
    functions: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            functions.append((node.name, node))
        elif isinstance(node, ast.ClassDef):
            functions.extend(
                (f"{node.name}.__init__", member)
                for member in node.body
                if isinstance(member, ast.FunctionDef) and member.name == "__init__"
            )
    found: list[tuple[str, str]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        read_back = {
            n.attr
            for n in ast.walk(node)
            if isinstance(n, ast.Attribute)
            and isinstance(n.ctx, ast.Load)
            and isinstance(n.value, ast.Name)
            and n.value.id == "self"
        }
        for member in node.body:
            if not (isinstance(member, ast.FunctionDef) and member.name == "__init__"):
                continue
            for stmt in ast.walk(member):
                if (
                    isinstance(stmt, ast.Assign)
                    and isinstance(stmt.value, ast.Name)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Attribute)
                    and isinstance(stmt.targets[0].value, ast.Name)
                    and stmt.targets[0].value.id == "self"
                    and stmt.targets[0].attr not in read_back
                    and "salt" in stmt.value.id
                ):
                    found.append((f"{node.name}.__init__", f"{stmt.value.id} (stored, never read back)"))
    for qualname, function in functions:
        loaded = {n.id for n in ast.walk(function) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        args = function.args
        params = [a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]]
        if args.vararg:
            params.append(args.vararg.arg)
        if args.kwarg:
            params.append(args.kwarg.arg)
        for name in params:
            if name in {"self", "cls"} or name.startswith("_"):
                continue
            if name not in loaded:
                found.append((qualname, name))
    return found


def test_the_detector_sees_the_defect_it_exists_for() -> None:
    source = (
        "class S:\n"
        "    def __init__(self, repo, tombstone_salt: str = ''):\n"
        "        self._repo = repo\n"
        "        self._tombstone_salt = tombstone_salt\n"
        "    def go(self):\n"
        "        return self._repo\n"
        "class T:\n"
        "    def __init__(self, repo, tombstone_salt: str = ''):\n"
        "        self._repo = repo\n"
        "def factory(engine, *, tombstone_salt: str = ''):\n"
        "    return engine\n"
    )
    # ``S`` stores the salt and never reads it back; ``T`` and ``factory`` drop it.
    assert unread_parameters(source) == [
        ("S.__init__", "tombstone_salt (stored, never read back)"),
        ("T.__init__", "tombstone_salt"),
        ("factory", "tombstone_salt"),
    ]


def test_no_service_constructor_or_factory_accepts_a_parameter_it_never_reads() -> None:
    offenders = {
        f"{path.name}:{qualname}({name})"
        for path in sorted(SERVICES.rglob("*.py"))
        for qualname, name in unread_parameters(path.read_text())
    }
    assert not offenders, sorted(offenders)
