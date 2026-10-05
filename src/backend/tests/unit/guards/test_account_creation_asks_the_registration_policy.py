"""#2132 - every way the application creates an account asks the registration policy, or is classified.

The defect class: an account-creating path that decides "anybody may" by not asking. ``register_local`` and
the first OIDC sign-in (``_register_oauth_user``) both created accounts unconditionally; a gate added at one
of them alone would leave the other as the open door - the drift between siblings the operator asked to
measure. A hand list cannot notice the third sibling it does not name, so this guard enumerates the class
**by what a function does**.

**Predicate** - a function (method or module function) anywhere under ``app/`` outside ``app/migrations/``
is a member when its own body calls ``create`` on a receiver whose last name contains ``user_repo``
(``self._user_repo.create(...)``, ``user_repo.create(...)``). Every member must call
``self._require_registration_admitted(...)`` (the one gate that reads the policy) or be classified in
:data:`_CLASSIFIED` with the reason it needs none. A classification that names no live member fails.

**Spellings this predicate cannot see:** a user document written through a repository held under a name
without ``user_repo`` in it, a raw AQL ``INSERT`` or ``collection(...).insert`` on ``users``, a
``getattr``-built call, and the operator-run seeds under ``app/migrations/`` (``seed_auth``,
``add_platform_admin``, ``seed_e2e_platform_admin``, ``seed_light_mode``): an operator creating the first
accounts of an installation is not a registration.
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"
_EXCLUDED = ("migrations",)
_GATE = "_require_registration_admitted"

_CLASSIFIED: dict[tuple[str, str], str] = {}


def _own_nodes(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    stack: list[ast.AST] = list(function.body)
    while stack:
        node = stack.pop()
        nodes.append(node)
        stack.extend(
            child
            for child in ast.iter_child_nodes(node)
            if not isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda)
        )
    return nodes


def _last_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _creates_an_account(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "create"
        and "user_repo" in _last_name(node.func.value)
        for node in _own_nodes(function)
    )


def _asks_the_gate(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and node.func.attr == _GATE
        for node in _own_nodes(function)
    )


def _functions(tree: ast.Module) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    found: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found.append((node.name, node))
        elif isinstance(node, ast.ClassDef):
            found += [
                (f"{node.name}.{item.name}", item)
                for item in node.body
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
            ]
    return found


def members(root: Path = APP) -> dict[tuple[str, str], bool]:
    """Every account-creating function: (file, qualname) -> asks the gate."""
    found: dict[tuple[str, str], bool] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if rel.parts[0] in _EXCLUDED:
            continue
        for qualname, function in _functions(ast.parse(path.read_text(encoding="utf-8"))):
            if _creates_an_account(function):
                found[(rel.as_posix(), qualname)] = _asks_the_gate(function)
    return found


def test_every_account_creation_asks_the_registration_policy_or_is_classified() -> None:
    ungated = sorted(
        f"{rel}::{name}" for (rel, name), gated in members().items() if not gated and (rel, name) not in _CLASSIFIED
    )

    assert ungated == [], (
        f"A function that creates an account must call self.{_GATE} (#2132) or be classified:\n  "
        + "\n  ".join(ungated)
    )


def test_the_predicate_sees_the_class() -> None:
    found = members()
    print(f"account creations: {sorted(found.items())}")  # noqa: T201 - the measured set, read by the reviewer

    assert found == {
        ("domain/services/auth_service.py", "AuthService.register_local"): True,
        ("domain/services/auth_service.py", "AuthService._register_oauth_user"): True,
    }


def test_no_classification_is_stale() -> None:
    found = members()

    assert sorted(k for k in _CLASSIFIED if k not in found) == []


def test_the_gate_reads_the_policy() -> None:
    """A gate that stopped deciding would leave every creation 'asked' over nothing."""
    tree = ast.parse((APP / "domain" / "services" / "auth_service.py").read_text(encoding="utf-8"))
    (gate,) = [fn for name, fn in _functions(tree) if name == f"AuthService.{_GATE}"]
    calls = {
        node.func.attr
        for node in _own_nodes(gate)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    raises = {
        node.exc.func.id
        for node in _own_nodes(gate)
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name)
    }

    assert "admits" in calls
    assert "RegistrationNotAllowedError" in raises


def test_the_running_application_wires_the_policy_from_the_settings() -> None:
    """The service takes the policy with an ``open`` default; the wiring is where the setting must reach it."""
    tree = ast.parse((APP / "common" / "dependencies.py").read_text(encoding="utf-8"))
    (factory,) = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "get_auth_service"]
    (call,) = [
        n
        for n in ast.walk(factory)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "AuthService"
    ]
    (policy,) = [kw for kw in call.keywords if kw.arg == "registration_policy"]
    reads = {node.attr for node in ast.walk(policy.value) if isinstance(node, ast.Attribute)}

    assert {"registration_mode", "registration_allowed_domains"} <= reads


# ── self-tests: the predicate recognises every spelling it claims ──────────────


def _member(source: str) -> tuple[bool, bool]:
    (function,) = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)]
    return _creates_an_account(function), _asks_the_gate(function)


def test_the_predicate_recognises_each_spelling() -> None:
    assert _member("def f(self):\n    self._user_repo.create(u)") == (True, False)
    assert _member("def f(user_repo):\n    user_repo.create(u)") == (True, False)
    assert _member(f"def f(self):\n    self.{_GATE}(e)\n    self._user_repo.create(u)") == (True, True)


def test_the_predicate_ignores_other_repositories_and_reads() -> None:
    assert _member("def f(self):\n    self._auth_provider_repo.create(p)") == (False, False)
    assert _member("def f(self):\n    self._user_repo.get_by_email(e)") == (False, False)


def test_the_gate_detection_sees_only_a_call_on_self() -> None:
    assert _member(f"def f(self):\n    other.{_GATE}(e)\n    self._user_repo.create(u)") == (True, False)
    assert _member(f"def f(self):\n    g = self.{_GATE}\n    self._user_repo.create(u)") == (True, False)
