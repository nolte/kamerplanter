"""#1844 — no route mounted in light mode sets a sign-in credential, unless decided.

A light-mode installation (REQ-027) resolves every request to the one seeded
system account without authentication. A credential set on that account through
such a request proves nothing about who set it, and it outlives the mode: once
the instance runs in ``full`` it is a working sign-in of the operator account.
#1844 was the password route; the class is every route of that shape.

The guard derives both sides rather than listing them:

* **Credential setters** — every method in ``app/domain/services`` that writes a
  non-``None`` ``password_hash`` (attribute or dict key) or constructs an
  ``ApiKey``. Read from the AST, so a new setter is found without being enrolled.
* **Light-mode surface** — the routes ``app.api.v1.router`` mounts when
  ``settings.kamerplanter_mode == "light"``: the module is re-imported under that
  setting and its assembled ``api_router`` walked (prefixes and include-level
  dependencies recovered through ``_IncludedRouter.include_context``).

A light-mode route whose endpoint calls a setter must depend on
``refuse_in_light_mode``, or be on :data:`DECIDED` with its reason. A ``DECIDED``
entry that no longer matches fails, so the list cannot outlive what it excused.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import textwrap
from pathlib import Path
from typing import Any

import pytest

_SERVICES = Path(__file__).resolve().parents[3] / "app" / "domain" / "services"

#: (method name, HTTP method, full path) → why it may set a credential in light mode.
DECIDED: dict[tuple[str, str, str], str] = {
    ("create_api_key", "POST", "/api/v1/auth/api-keys"): (
        "REQ-033 §4.3: API-key management is mounted in light mode on purpose — MCP accepts "
        "nothing but a kp_ key, so a light instance could not use its MCP interface otherwise. "
        "What happens to such keys on the switch to full mode is #1855."
    ),
    ("<endpoint>", "POST", "/api/v1/t/{tenant_slug}/calendar/feeds"): (
        "A calendar feed is a light-mode feature (subscribing an external calendar). Its token "
        "grants read access to the feed only, and no route redeems it yet (feed.ics is not mounted). "
        "Its survival into full mode belongs to the upgrade path of #1855."
    ),
    ("<endpoint>", "PUT", "/api/v1/t/{tenant_slug}/calendar/feeds/{key}"): (
        "Same feed document as the POST above (a regenerated token); same reasoning."
    ),
}


#: Documents whose existence grants access to whoever holds a secret from them: a
#: key, an invitation token, a linked sign-in, a session, an e-mail-change token, a
#: calendar-feed token. Creating one is setting a credential.
ACCESS_ARTIFACTS = frozenset(
    {"ApiKey", "Invitation", "AuthProvider", "RefreshToken", "EmailChangeRequest", "CalendarFeed"}
)


def _is_none(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _sets_directly(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Whether *func* itself writes a password hash or creates an access artifact.

    Every spelling the review of #1844 listed: attribute assignment (plain and
    annotated), a dict key, a keyword argument, ``setattr(obj, "password_hash", …)``,
    and constructing an artifact by name or attribute (``models.ApiKey(...)``) or
    through ``model_validate``.
    """
    for node in ast.walk(func):
        if isinstance(node, ast.Assign | ast.AnnAssign) and not _is_none(node.value):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Attribute) and t.attr == "password_hash" for t in targets):
                return True
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and key.value == "password_hash" and not _is_none(value):
                    return True
        if isinstance(node, ast.Call):
            if any(kw.arg == "password_hash" and not _is_none(kw.value) for kw in node.keywords):
                return True
            func_node = node.func
            if (
                isinstance(func_node, ast.Name)
                and func_node.id == "setattr"
                and len(node.args) >= 3
                and isinstance(node.args[1], ast.Constant)
                and node.args[1].value == "password_hash"
                and not _is_none(node.args[2])
            ):
                return True
            name = func_node.id if isinstance(func_node, ast.Name) else getattr(func_node, "attr", None)
            if name in ACCESS_ARTIFACTS:
                return True
            if (
                isinstance(func_node, ast.Attribute)
                and func_node.attr in {"model_validate", "model_construct"}
                and isinstance(func_node.value, ast.Name | ast.Attribute)
                and (getattr(func_node.value, "id", None) or getattr(func_node.value, "attr", None)) in ACCESS_ARTIFACTS
            ):
                return True
    return False


def _called_names(func: ast.AST) -> set[str]:
    return {
        node.func.attr for node in ast.walk(func) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }


def _credential_setters() -> set[str]:
    """Public service methods that set a credential — directly or through another setter.

    Transitive by *name* across every service: a method that calls ``.x(...)`` on
    anything, where ``x`` is a setter, is a setter too. Name-based resolution
    over-approximates (two services sharing a method name), which errs towards
    reporting a route, never towards missing one.
    """
    methods: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for path in sorted(_SERVICES.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            methods.extend(
                (func.name, func) for func in cls.body if isinstance(func, ast.FunctionDef | ast.AsyncFunctionDef)
            )
    setters = {name for name, func in methods if _sets_directly(func)}
    while True:
        grown = setters | {name for name, func in methods if _called_names(func) & setters}
        if grown == setters:
            break
        setters = grown
    return {name for name in setters if not name.startswith("_")}


def _dependency_calls(dependant: Any) -> set[Any]:
    found = set()
    for sub in dependant.dependencies:
        found.add(sub.call)
        found |= _dependency_calls(sub)
    return found


def _routes(routes: Any, prefix: str = "", inherited: tuple = ()) -> list[tuple[str, Any, set[Any]]]:
    from fastapi.routing import APIRoute

    out = []
    for route in routes:
        if isinstance(route, APIRoute):
            out.append((prefix + route.path_format, route, set(inherited)))
        elif hasattr(route, "original_router"):
            ctx = route.include_context
            extra = tuple(d.dependency for d in ctx.dependencies)
            out.extend(_routes(route.original_router.routes, prefix + ctx.prefix, inherited + extra))
    return out


#: Marker for an endpoint that creates an access artifact in its own body rather
#: than through a service method (the calendar-feed routes build ``CalendarFeed``).
_IN_ENDPOINT = "<endpoint>"


def _called_methods(endpoint: Any) -> set[str]:
    tree = ast.parse(textwrap.dedent(inspect.getsource(endpoint)))
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef))
    return _called_names(tree) | ({_IN_ENDPOINT} if _sets_directly(func) else set())


@pytest.fixture(scope="module")
def light_mode_routes() -> list[tuple[str, Any, set[Any]]]:
    import app.api.v1.router as router_module
    from app.config.settings import settings

    original = settings.kamerplanter_mode
    try:
        settings.kamerplanter_mode = "light"
        light = importlib.reload(router_module)
        return _routes(light.api_router.routes)
    finally:
        settings.kamerplanter_mode = original
        importlib.reload(router_module)


def _findings(routes: list[tuple[str, Any, set[Any]]], setters: set[str]) -> dict[tuple[str, str, str], bool]:
    """(setter, method, path) → whether the route refuses in light mode."""
    from app.common.auth import refuse_in_light_mode

    hits = {}
    for path, route, inherited in routes:
        called = _called_methods(route.endpoint) & (setters | {_IN_ENDPOINT})
        refuses = refuse_in_light_mode in (_dependency_calls(route.dependant) | inherited)
        for name in called:
            for method in route.methods:
                hits[(name, method, path)] = refuses
    return hits


def test_the_setter_scan_finds_the_known_setters():
    # Non-vacuity: the password setters and the key minting are all seen.
    assert {"change_password", "reset_password", "create_api_key"} <= _credential_setters()


def test_the_light_mode_walk_is_the_light_mode_surface(light_mode_routes):
    paths = {path for path, _route, _deps in light_mode_routes}
    # Mounted in both modes …
    assert "/api/v1/users/me/password" in paths
    assert "/api/v1/auth/api-keys" in paths
    # … and full mode only (login would be a credential route in light mode otherwise).
    assert "/api/v1/auth/login" not in paths


def test_no_light_mode_route_sets_a_credential_without_refusing(light_mode_routes):
    hits = _findings(light_mode_routes, _credential_setters())
    open_sites = sorted(site for site, refuses in hits.items() if not refuses and site not in DECIDED)

    assert hits, "no light-mode route calls a credential setter — the scan is looking in the wrong place"
    assert open_sites == [], (
        "light-mode routes that set a sign-in credential on the unauthenticated system account "
        f"(add Depends(refuse_in_light_mode) or decide it in DECIDED): {open_sites}"
    )


def test_every_decided_entry_still_matches_an_open_site(light_mode_routes):
    hits = _findings(light_mode_routes, _credential_setters())
    stale = [site for site in DECIDED if hits.get(site) is not False]

    assert stale == [], f"DECIDED entries that no longer describe an unrefused light-mode setter: {stale}"


@pytest.mark.parametrize(
    "source",
    [
        "def f(self, u, h):\n    u.password_hash = h\n",
        "def f(self, u, h):\n    u.password_hash: str = h\n",
        "def f(self, k, h):\n    self._repo.update_fields(k, {'password_hash': h})\n",
        "def f(self, k, h):\n    self._repo.update_fields(k, password_hash=h)\n",
        "def f(self, u, h):\n    setattr(u, 'password_hash', h)\n",
        "def f(self):\n    return ApiKey(user_key='u')\n",
        "def f(self):\n    return models.Invitation(token_hash='x')\n",
        "def f(self, d):\n    return RefreshToken.model_validate(d)\n",
        "async def f(self):\n    return AuthProvider(provider='local')\n",
    ],
    ids=["assign", "annassign", "dict", "keyword", "setattr", "apikey", "attr-ctor", "model-validate", "async"],
)
def test_the_setter_scan_sees_every_spelling(source: str):
    # Self-test: each spelling the #1844 review named must be detected.
    func = ast.parse(source).body[0]
    assert isinstance(func, ast.FunctionDef | ast.AsyncFunctionDef)
    assert _sets_directly(func)


def test_clearing_a_password_is_not_setting_one():
    # Erasure writes ``password_hash: None`` — the scan must not flag the removal of a credential.
    func = ast.parse("def f(self, k):\n    self._repo.update_fields(k, {'password_hash': None})\n").body[0]
    assert isinstance(func, ast.FunctionDef)
    assert not _sets_directly(func)
