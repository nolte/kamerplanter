"""#1850 — an API key's network controls bind on every surface that accepts the key.

The defect: ``ip_allowlist`` and ``rate_limit_per_minute`` were read by the MCP
authenticator only. On REST a ``kp_`` bearer went through
``AuthService.authenticate_api_key``, which checked revoked / expiry / active
account and nothing else — the same one-surface-only shape #1817 fixed for the
tenant scope.

The fix routes both surfaces through ``enforce_api_key_controls``. The route test
(``tests/api/test_api_key_network_controls_api.py``) holds the behaviour; this
guard holds the **funnel**, over the whole ``app/`` tree:

1. **Every place a stored key is looked up by its hash enforces the controls.**
   A function that calls ``<api-key repo>.get_by_hash(...)`` must also call
   ``enforce_api_key_controls`` — a third key-accepting surface fails here.
2. **One implementation.** ``ip_allowlist`` is read (as an attribute) only in
   ``app/domain/models/auth.py`` and ``app/domain/services/api_key_controls.py``;
   the per-key ``check_and_increment(api_key_key=...)`` is called only in the latter
   (the identification limiter has a counter of its own and a different signature); the limiter is built
   only by ``get_api_key_rate_limiter``, which both service factories use.
3. **The client address is always stated.** ``client_ip`` is keyword-only without
   a default on ``enforce_api_key_controls``, ``authenticate_api_key`` and both
   auth providers' ``resolve_user`` / ``resolve_user_optional`` — a caller that
   forgets it fails at the call, instead of reading as "no address known" and
   being refused (or worse, silently exempted by a future default).
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

_APP = Path(__file__).resolve().parents[3] / "app"
_CONTROL_HOMES = {
    _APP / "domain" / "models" / "auth.py",
    _APP / "domain" / "services" / "api_key_controls.py",
}


def _modules() -> list[tuple[Path, ast.Module]]:
    return [(path, ast.parse(path.read_text(encoding="utf-8"))) for path in sorted(_APP.rglob("*.py"))]


def _called(node: ast.AST) -> set[str]:
    names = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            names.add(func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", ""))
    return names


def _key_lookups_without_controls(tree: ast.Module) -> tuple[int, list[str]]:
    """``(lookups, offenders)`` — functions calling an api-key repo's ``get_by_hash``."""
    lookups, offenders = 0, []
    for func in ast.walk(tree):
        if not isinstance(func, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        hits = [
            node
            for node in ast.walk(func)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get_by_hash"
            and "api_key" in ast.unparse(node.func.value)
        ]
        if not hits:
            continue
        lookups += 1
        if "enforce_api_key_controls" not in _called(func):
            offenders.append(f"{func.name}:{hits[0].lineno}")
    return lookups, offenders


def test_every_api_key_lookup_enforces_the_controls() -> None:
    total, offenders = 0, []
    for path, tree in _modules():
        count, bad = _key_lookups_without_controls(tree)
        total += count
        offenders += [f"{path.relative_to(_APP.parent)}:{site}" for site in bad]

    # Non-vacuity: the REST (AuthService) and MCP (McpAuthenticator) surfaces.
    assert total >= 2, total
    assert offenders == [], f"API key accepted without its ip_allowlist / rate limit (#1850): {offenders}"


@pytest.mark.parametrize(
    ("source", "offending"),
    [
        ("def f(self, h):\n    return self._api_key_repo.get_by_hash(h)\n", True),
        ("def f(repo_api_keys, h):\n    return repo_api_keys.get_by_hash(h)\n", True),
        (
            "def f(self, h, ip):\n    k = self._api_key_repo.get_by_hash(h)\n"
            "    enforce_api_key_controls(k, client_ip=ip, rate_limiter=None)\n",
            False,
        ),
        ("def f(self, h):\n    return self._refresh_token_repo.get_by_hash(h)\n", False),
    ],
    ids=["lookup-only", "other-receiver-name", "enforced", "not-an-api-key"],
)
def test_the_lookup_scan_flags_what_it_should(source: str, offending: bool) -> None:
    _, offenders = _key_lookups_without_controls(ast.parse(source))

    assert bool(offenders) is offending


def test_the_allowlist_and_the_counter_have_one_home() -> None:
    reads, increments = [], []
    for path, tree in _modules():
        rel = f"{path.relative_to(_APP.parent)}"
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "ip_allowlist" and path not in _CONTROL_HOMES:
                reads.append(f"{rel}:{node.lineno}")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "check_and_increment"
                and any(kw.arg == "api_key_key" for kw in node.keywords)
                and path.name != "api_key_controls.py"
            ):
                increments.append(f"{rel}:{node.lineno}")

    assert reads == [], f"ip_allowlist read outside the shared control (#1850): {reads}"
    assert increments == [], f"per-key budget counted outside the shared control (#1850): {increments}"


def test_both_surfaces_are_built_with_the_shared_limiter() -> None:
    tree = ast.parse((_APP / "common" / "dependencies.py").read_text(encoding="utf-8"))
    factories = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    built = [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "ApiKeyRateLimiter"
    ]

    for factory, keyword in (("get_auth_service", "api_key_rate_limiter"), ("get_mcp_authenticator", "rate_limiter")):
        calls = [
            kw.value
            for node in ast.walk(factories[factory])
            if isinstance(node, ast.Call)
            for kw in node.keywords
            if kw.arg == keyword
        ]
        assert [ast.unparse(v) for v in calls] == ["get_api_key_rate_limiter()"], factory
    assert len(built) == 1, f"ApiKeyRateLimiter built outside get_api_key_rate_limiter: lines {built}"


def _client_ip_param(func) -> inspect.Parameter | None:  # noqa: ANN001
    return inspect.signature(func).parameters.get("client_ip")


def _client_ip_takers() -> list:
    from app.domain.engines.full_auth_provider import FullAuthProvider
    from app.domain.engines.light_auth_provider import LightAuthProvider
    from app.domain.interfaces.auth_provider import IAuthProvider
    from app.domain.services.api_key_controls import enforce_api_key_controls
    from app.domain.services.auth_service import AuthService

    return [
        enforce_api_key_controls,
        AuthService.authenticate_api_key,
        *(
            getattr(cls, name)
            for cls in (IAuthProvider, FullAuthProvider, LightAuthProvider)
            for name in ("resolve_user", "resolve_user_optional")
        ),
    ]


@pytest.mark.parametrize("func", _client_ip_takers(), ids=lambda f: f.__qualname__)
def test_the_client_address_is_keyword_only_without_a_default(func) -> None:  # noqa: ANN001
    param = _client_ip_param(func)

    assert param is not None
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is inspect.Parameter.empty
