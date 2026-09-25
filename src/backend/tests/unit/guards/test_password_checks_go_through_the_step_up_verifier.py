"""#1816 G1/G3 — no password re-check outside the login path and the one step-up verifier.

The defect class: a password step-up written at its call site. Three copies
(account erasure, tenant deletion, password change) re-ran bcrypt without any
throttle, and two erasure routes had no copy at all (#1813, #1814). The class is
enumerated by what every such copy must do — call ``PasswordEngine.verify_password``
— so this guard walks every module under ``app/`` and allows the call in exactly:

* ``AuthService.login_local`` / ``AuthService._reject_unknown_account`` — the login
  path, throttled by its own lockout (``failed_login_attempts`` /
  ``IUnknownAccountStore``);
* ``StepUpVerifier.verify`` — the throttled step-up every other re-check passes.

Selector width (G6): any attribute call named ``verify_password`` — a direct
``bcrypt.checkpw`` would dodge it, so that spelling is refused everywhere except the
engine that wraps it.
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"

_ALLOWED_VERIFY = {
    ("domain/services/auth_service.py", "login_local"),
    ("domain/services/auth_service.py", "_reject_unknown_account"),
    ("domain/services/step_up_service.py", "verify"),
}
_ALLOWED_CHECKPW = {"domain/engines/password_engine.py"}


class _CallSites(ast.NodeVisitor):
    """Every call of one name, with the innermost enclosing function."""

    def __init__(self, rel: str, name: str) -> None:
        self.rel, self.name = rel, name
        self.stack: list[str] = []
        self.found: list[tuple[str, str, int]] = []

    def _enter(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        called = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if called == self.name:
            self.found.append((self.rel, self.stack[-1] if self.stack else "<module>", node.lineno))
        self.generic_visit(node)


def _calls(name: str) -> list[tuple[str, str, int]]:
    found: list[tuple[str, str, int]] = []
    for path in sorted(APP.rglob("*.py")):
        visitor = _CallSites(path.relative_to(APP).as_posix(), name)
        visitor.visit(ast.parse(path.read_text(encoding="utf-8")))
        found.extend(visitor.found)
    return found


def test_verify_password_is_called_only_on_the_login_path_and_in_the_step_up_verifier() -> None:
    offenders = [
        f"{rel}:{line} in {func}()"
        for rel, func, line in _calls("verify_password")
        if (rel, func) not in _ALLOWED_VERIFY
    ]

    assert offenders == [], (
        "A password re-check outside the login path must go through StepUpVerifier.verify "
        "(throttled, API keys refused, #1816): " + ", ".join(offenders)
    )


def test_the_allowed_sites_still_exist() -> None:
    """An allow-list entry nobody uses any more is a hole waiting for the next copy."""
    seen = {(rel, func) for rel, func, _line in _calls("verify_password")}

    assert seen >= _ALLOWED_VERIFY, _ALLOWED_VERIFY - seen


def test_bcrypt_is_called_only_by_the_password_engine() -> None:
    offenders = [f"{rel}:{line}" for rel, _func, line in _calls("checkpw") if rel not in _ALLOWED_CHECKPW]

    assert offenders == []


# ── the erasure entry points cannot be called without a step-up ──────────────

_STEP_UP_ENTRIES = {
    ("domain/services/privacy_service.py", "request_erasure"),
    ("domain/services/privacy_service.py", "erase_account_by_admin"),
    ("domain/services/tenant_service.py", "delete_tenant"),
}
_STEP_UP_ARGS = {"authenticated_with_api_key", "client_ip"}


def _functions(rel: str) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse((APP / rel).read_text(encoding="utf-8"))
    return {node.name: node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_every_irreversible_account_entry_takes_the_step_up_keyword_only_without_a_default() -> None:
    """A new route cannot forget the step-up: the entry refuses to be called without it (G1)."""
    problems = []
    for rel, name in sorted(_STEP_UP_ENTRIES):
        node = _functions(rel)[name]
        kwonly = {arg.arg: default for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)}
        for arg in _STEP_UP_ARGS | {"confirmation"}:
            if arg not in kwonly:
                problems.append(f"{rel}::{name} lacks keyword-only '{arg}'")
            elif kwonly[arg] is not None:
                problems.append(f"{rel}::{name} gives '{arg}' a default")

    assert problems == []


def test_the_immediate_admin_erasure_starts_only_behind_the_step_up() -> None:
    """``erase_account_now(origin="platform_admin")`` is reachable only through ``erase_account_by_admin``."""
    sites = []
    for path in sorted(APP.rglob("*.py")):
        rel = path.relative_to(APP).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for call in ast.walk(node):
                if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)):
                    continue
                if call.func.attr != "erase_account_now":
                    continue
                origin = next((k.value for k in call.keywords if k.arg == "origin"), None)
                if isinstance(origin, ast.Constant) and origin.value == "platform_admin":
                    sites.append((rel, node.name))
                elif not isinstance(origin, ast.Constant):
                    sites.append((rel, f"{node.name} (origin not a literal)"))

    assert sites == [("domain/services/privacy_service.py", "erase_account_by_admin")]
