"""#1881 class guard — no service constructor or factory accepts a parameter it never reads.

``AuthService``, ``StepUpVerifier`` and ``UserService`` kept taking a
``tombstone_salt`` that nothing used after #1812 moved the log pseudonyms to
``LOG_PSEUDONYM_SALT``. A parameter named after the non-rotatable erasure salt
that keys nothing invites the next change to key something with it again. #1972
widened the stored-and-never-read check from salt-named parameters to every
parameter: nine dependencies (``activity_repo``, ``refresh_token_repo``, ...) were
wired through the DI factories into services that never used them.

**The rule.** In ``app/domain/services/``, every parameter of an ``__init__`` or
of a module-level function is loaded (read, forwarded, stored) somewhere in that
function's own body, and a *salt* parameter stored as ``self._x = param`` is read
back as ``self._x`` somewhere in its class (the stored-and-never-read spelling is
the one #1881 was: the services stored the erasure salt and nothing read it).
A name starting with ``_`` is exempt (the explicit "unused"). A dependency that is
kept on purpose is listed in ``DELIBERATELY_UNREAD`` with its reason; a stale entry
fails the guard. ``UnsupportedMediaTypeError`` in ``app/common/exceptions.py`` is
scanned for unread parameters too.

Spellings this does NOT see
---------------------------

* a parameter stored on ``self`` under a *different expression* (``self._x = x or y``,
  a conversion) — only the plain ``self._x = x`` is traced to a read of ``self._x``;
* an attribute read through ``getattr(self, "_x")`` or from another object;
* a parameter used only inside a nested function or lambda that is itself dead;
* ``__init__`` parameters of classes outside ``app/domain/services/`` and
  ``app/common/exceptions.py`` (engines, adapters, repositories);
* a stored parameter whose attribute is read only from another object
  (``service._x``): the scan sees ``self._x`` loads inside the class alone.
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
SERVICES = APP / "domain" / "services"
EXCEPTIONS = APP / "common" / "exceptions.py"

#: ``file:Class.__init__(parameter (stored, never read back))`` -> why it stays.
DELIBERATELY_UNREAD = {
    "ki_assistent_service.py:KiAssistentService.__init__(llm_adapter (stored, never read back))": (
        "REQ-031 scaffold pins the constructor seam of the future assistant; nothing constructs it yet"
    ),
    "ki_assistent_service.py:KiAssistentService.__init__(knowledge_client (stored, never read back))": (
        "REQ-031 scaffold pins the constructor seam of the future assistant; nothing constructs it yet"
    ),
}


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
        "    def go(self):\n"
        "        return self._repo\n"
        "def factory(engine, *, tombstone_salt: str = ''):\n"
        "    return engine\n"
    )
    # ``S`` stores the salt and never reads it back; ``T`` and ``factory`` drop it.
    assert unread_parameters(source) == [
        ("S.__init__", "tombstone_salt (stored, never read back)"),
        ("T.__init__", "tombstone_salt"),
        ("factory", "tombstone_salt"),
    ]


def _offenders() -> set[str]:
    paths = [*sorted(SERVICES.rglob("*.py")), EXCEPTIONS]
    return {
        f"{path.name}:{qualname}({name})"
        for path in paths
        for qualname, name in unread_parameters(path.read_text())
        # Exceptions carry data attributes that the exception handlers read from outside the class.
        if not (path == EXCEPTIONS and name.endswith("(stored, never read back)"))
    }


def test_no_service_constructor_or_factory_accepts_a_parameter_it_never_reads() -> None:
    offenders = _offenders() - DELIBERATELY_UNREAD.keys()
    assert not offenders, sorted(offenders)


def test_every_deliberately_unread_entry_still_exists_and_names_a_reason() -> None:
    stale = DELIBERATELY_UNREAD.keys() - _offenders()
    assert not stale, f"no longer unread, drop from DELIBERATELY_UNREAD: {sorted(stale)}"
    assert all(reason.strip() for reason in DELIBERATELY_UNREAD.values())


def test_the_detector_sees_a_stored_dependency_that_is_not_salt_named() -> None:
    source = (
        "class S:\n"
        "    def __init__(self, repo, activity_repo=None):\n"
        "        self._repo = repo\n"
        "        self._activity_repo = activity_repo\n"
        "    def go(self):\n"
        "        return self._repo\n"
    )
    assert unread_parameters(source) == [("S.__init__", "activity_repo (stored, never read back)")]
