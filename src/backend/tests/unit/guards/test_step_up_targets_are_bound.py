"""#1884 — every step-up call names the target its act acts on, and only a targeted act names one.

The defect class: a guard whose decision input is narrower than the act it guards.
The verifier bound a code or re-authentication token to the account and the act,
never to *what* the act acts on, so a factor obtained to verify user A verified
user B, one obtained to unlink provider X unlinked provider Y. The fix makes
``target`` a keyword-only argument without a default on every verifier entry that
binds or checks a factor (``verify``, ``issue_code``, ``admit_reauth``,
``issue_reauth_token``); a missing keyword is a ``TypeError`` at runtime. This guard
is the static half, over every call site in ``app/``:

**Predicate** — a call whose callee attribute is one of those four names on a
receiver whose spelling ends in ``step_up_verifier`` (``self._step_up_verifier``,
``privacy_service._step_up_verifier``). Every such call must

* pass ``target=`` as a keyword;
* where ``action=`` is a string literal: pass a non-``None`` target exactly when
  the act is in :data:`TARGETED_ACTIONS` — a literal ``None`` for a targeted act,
  or a non-``None`` target for an untargeted one, is the drift.

**Spellings this predicate cannot see:** a call through a local alias of the verifier
(``v = self._step_up_verifier; v.verify(...)``), a ``**kwargs`` splat, and an
``action`` held in a variable (the target is then only required to be passed — the
runtime check ``assert_target_bound`` covers the pairing).
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.domain.services.step_up_service import TARGETED_ACTIONS

APP = Path(__file__).resolve().parents[3] / "app"
_ENTRIES = {"verify", "issue_code", "admit_reauth", "issue_reauth_token"}

#: Call sites measured when this guard was written (#1884) — a change is a signal to
#: read: a new site must bind its target, a vanished one may mean the predicate went blind.
EXPECTED_CALL_SITES = 11


def _receiver_spelling(node: ast.expr) -> str:
    if isinstance(node, ast.Attribute):
        return f"{_receiver_spelling(node.value)}.{node.attr}"
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _call_sites() -> list[tuple[str, int, ast.Call]]:
    sites: list[tuple[str, int, ast.Call]] = []
    for path in sorted(APP.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in _ENTRIES
                and _receiver_spelling(node.func.value).endswith("step_up_verifier")
            ):
                sites.append((str(path.relative_to(APP)), node.lineno, node))
    return sites


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    return next((kw.value for kw in call.keywords if kw.arg == name), None)


def _violations(sites: list[tuple[str, int, ast.Call]]) -> list[str]:
    found: list[str] = []
    for rel, line, call in sites:
        where = f"{rel}:{line} {call.func.attr}"  # type: ignore[attr-defined]
        target = _keyword(call, "target")
        if target is None:
            found.append(f"{where}: passes no target=")
            continue
        action = _keyword(call, "action")
        if isinstance(action, ast.Constant) and isinstance(action.value, str):
            literal_none = isinstance(target, ast.Constant) and target.value is None
            if action.value in TARGETED_ACTIONS and literal_none:
                found.append(f"{where}: targeted act {action.value!r} with target=None")
            if action.value not in TARGETED_ACTIONS and not literal_none:
                found.append(f"{where}: untargeted act {action.value!r} names a target")
    return found


def test_the_sweep_finds_the_call_sites() -> None:
    """The control: a sweep over nothing is green over nothing."""
    sites = _call_sites()
    print(f"step-up call sites: {len(sites)}")  # noqa: T201 - the measured count, read by the reviewer
    for rel, line, call in sites:
        print(f"  {rel}:{line} {call.func.attr}")  # type: ignore[attr-defined]  # noqa: T201
    assert len(sites) == EXPECTED_CALL_SITES, [(rel, line) for rel, line, _ in sites]


def test_every_call_site_binds_the_target_its_act_needs() -> None:
    violations = _violations(_call_sites())
    assert not violations, "Step-up calls that do not bind their act's target (#1884):\n  " + "\n  ".join(violations)


def test_the_predicate_catches_each_drift_shape() -> None:
    """Falsification on the same expression: each drift shape is reported."""
    source = (
        "class S:\n"
        "    def a(self):\n"
        "        self._step_up_verifier.verify(u, action='admin_account_update', echo_ok=None)\n"
        "    def b(self):\n"
        "        self._step_up_verifier.verify(u, action='tenant_deletion', target=None)\n"
        "    def c(self):\n"
        "        self._step_up_verifier.issue_code(u, action='password_change', target=key)\n"
        "    def d(self):\n"
        "        self._step_up_verifier.verify(u, action='provider_unlink', target=provider_key)\n"
        "    def e(self):\n"
        "        self._step_up_verifier.issue_reauth_token(u, action=action, target=target)\n"
    )
    sites = [
        ("probe.py", node.lineno, node)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _ENTRIES
        and _receiver_spelling(node.func.value).endswith("step_up_verifier")
    ]
    violations = _violations(sites)

    assert len(sites) == 5
    assert any("probe.py:3" in v and "no target" in v for v in violations)
    assert any("probe.py:5" in v and "with target=None" in v for v in violations)
    assert any("probe.py:7" in v and "names a target" in v for v in violations)
    assert not any("probe.py:9" in v or "probe.py:11" in v for v in violations)
