"""#2043 — every anonymous auth route that can send mail bounds the recipient, or says why it needs no bound.

The defect class: an anonymous route mails an address the caller chooses, and the
only bound is per source IP. ``/auth/resend-verification`` was born with a
per-address budget (#2037); ``/auth/password-reset/request``, its older sibling,
had none, so one source could mail one inbox twenty reset links a minute
(#2043). A hand list of "the mail routes" cannot notice the sibling it does not
name, so this guard enumerates the class **by what a member does**.

**Predicate** — a ``POST`` route of the auth router is a member when

* it is anonymous: no dependency in its tree is named ``require_*`` or
  ``get_current_*`` (read from FastAPI's own dependant tree, not from source);
* and its handler reaches a mail: it calls an ``AuthService`` method that —
  directly, or through ``self.<method>`` references (a call, a ``partial``, a
  lambda) — touches ``self._email_service``; or it references a module-level
  helper of the router that imports from ``app.tasks`` (the Celery dispatch of
  the duplicate-registration notice).

Every mail-reaching ``AuthService`` method of a member must call
``self.<store>.reserve_attempt(...)`` in its own body — a per-recipient budget
reserved on the request path — or be classified in :data:`_CLASSIFIED` with the
reason it needs none. Every task dispatch must be classified as well. A
classification that no longer names a live member fails, so the list cannot go
stale and excuse the next copy.

**Spellings this predicate cannot see** (so nobody reads green as more than it
is): a mail sent through an attribute other than ``self._email_service`` (a
local alias, a collaborator object that mails on the service's behalf), a
service method reached through ``getattr``, a router helper reached other than
by its bare name, a dispatch that imports from somewhere other than
``app.tasks``, routes outside ``app/api/v1/auth/router.py``, and anonymous
``GET`` routes. And a ``reserve_attempt`` call proves a reservation exists, not
that its result is compared with a limit — the route tests own that
(``tests/api/test_auth_password_reset_budget.py``,
``tests/api/test_auth_resend_verification.py``).
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute

APP = Path(__file__).resolve().parents[3] / "app"
AUTH_SERVICE = APP / "domain" / "services" / "auth_service.py"
AUTH_ROUTER = APP / "api" / "v1" / "auth" / "router.py"

_AUTHENTICATING_PREFIXES = ("require_", "get_current_")

#: Members that need no per-recipient reservation of their own, keyed
#: ``"<route> <AuthService method or task:<helper>>"``, with the reason read from the code.
_CLASSIFIED: dict[str, str] = {
    "/auth/register register_local": (
        "The verification mail goes out only when the address gets an account; a second request for "
        "the same address takes the duplicate branch, which mails nothing itself. So one mail per "
        "address, ever (until the account is deleted)."
    ),
    "/auth/register task:_enqueue_duplicate_registration_notice": (
        "The duplicate-registration notice is bounded per recipient in the Celery task: "
        "``send_duplicate_registration_notice`` claims a suppression window on "
        "``get_registration_notice_store()`` before it sends."
    ),
}

#: Pinned so a predicate that silently loses a member fails instead of shrinking.
_EXPECTED_MEMBERS = {
    "/auth/register register_local",
    "/auth/register task:_enqueue_duplicate_registration_notice",
    "/auth/resend-verification resend_verification_email",
    "/auth/password-reset/request request_password_reset",
}


# ── predicate over source ─────────────────────────────────────────────────


@dataclass(frozen=True)
class _Method:
    self_refs: frozenset[str]
    touches_mail: bool
    reserves: bool


def _self_attr_chain(node: ast.AST) -> tuple[str, ...] | None:
    """``self.a.b`` → ``("a", "b")``; anything not rooted at ``self`` → ``None``."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name) and node.id == "self":
        return tuple(reversed(parts))
    return None


def _methods(class_source: str, class_name: str) -> dict[str, _Method]:
    tree = ast.parse(class_source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name)
    names = {f.name for f in cls.body if isinstance(f, ast.FunctionDef)}
    out: dict[str, _Method] = {}
    for func in cls.body:
        if not isinstance(func, ast.FunctionDef):
            continue
        refs: set[str] = set()
        mail = reserves = False
        for node in ast.walk(func):
            chain = _self_attr_chain(node) if isinstance(node, ast.Attribute) else None
            if chain:
                if chain[0] in names:
                    refs.add(chain[0])
                if chain[0] == "_email_service":
                    mail = True
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "reserve_attempt"
                and _self_attr_chain(node.func.value) is not None
            ):
                reserves = True
        out[func.name] = _Method(frozenset(refs), mail, reserves)
    return out


def _mail_reaching(methods: dict[str, _Method]) -> set[str]:
    reaching = {name for name, m in methods.items() if m.touches_mail}
    changed = True
    while changed:
        changed = False
        for name, m in methods.items():
            if name not in reaching and m.self_refs & reaching:
                reaching.add(name)
                changed = True
    return reaching


def _imports_tasks(func_source: str) -> bool:
    return any(
        isinstance(n, ast.ImportFrom) and (n.module or "").startswith("app.tasks")
        for n in ast.walk(ast.parse(textwrap.dedent(func_source)))
    )


def _handler_refs(handler_source: str) -> tuple[set[str], set[str]]:
    """Attribute names called on any object, and bare names referenced, in a handler."""
    tree = ast.parse(textwrap.dedent(handler_source))
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    return attrs, names


def _members(
    routes: Iterable[tuple[str, str]],
    methods: dict[str, _Method],
    router_helpers: dict[str, str],
) -> dict[str, bool]:
    """``{"<path> <method|task:helper>": reserves}`` for every mail-reaching step of an anonymous route."""
    reaching = _mail_reaching(methods)
    out: dict[str, bool] = {}
    for path, handler_source in routes:
        attrs, names = _handler_refs(handler_source)
        for name in sorted(attrs & reaching):
            out[f"{path} {name}"] = methods[name].reserves
        for name in sorted(names & router_helpers.keys()):
            if _imports_tasks(router_helpers[name]):
                out[f"{path} task:{name}"] = False
    return out


# ── the live application ──────────────────────────────────────────────────


def _dependency_names(dependant: Dependant) -> set[str]:
    names: set[str] = set()
    for dep in dependant.dependencies:
        call: Callable[..., object] | None = dep.call
        if call is not None:
            names.add(getattr(call, "__name__", ""))
        names |= _dependency_names(dep)
    return names


def _anonymous_post_routes() -> list[tuple[str, str]]:
    from app.api.v1.auth.router import router

    out: list[tuple[str, str]] = []
    for route in router.routes:
        if not isinstance(route, APIRoute) or "POST" not in (route.methods or set()):
            continue
        if any(n.startswith(_AUTHENTICATING_PREFIXES) for n in _dependency_names(route.dependant)):
            continue
        out.append((route.path, inspect.getsource(inspect.unwrap(route.endpoint))))
    return out


def _router_helpers() -> dict[str, str]:
    source = AUTH_ROUTER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    return {
        n.name: ast.get_source_segment(source, n) or ""
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name.startswith("_")
    }


def _live_members() -> dict[str, bool]:
    methods = _methods(AUTH_SERVICE.read_text(encoding="utf-8"), "AuthService")
    return _members(_anonymous_post_routes(), methods, _router_helpers())


def test_the_predicate_finds_the_known_members() -> None:
    assert set(_live_members()) == _EXPECTED_MEMBERS


def test_every_member_reserves_a_per_recipient_budget_or_is_classified() -> None:
    unbounded = sorted(key for key, reserves in _live_members().items() if not reserves and key not in _CLASSIFIED)

    assert unbounded == [], (
        "Anonymous auth route(s) reach a mail with no per-recipient reservation on the request path "
        "(#2043). Reserve on a store like the password-reset budget, or classify with the reason: "
        f"{unbounded}"
    )


def test_no_classification_is_stale() -> None:
    live = _live_members()
    stale = sorted(key for key in _CLASSIFIED if key not in live or live[key])

    assert stale == [], f"classified entries that no longer name an unreserved member: {stale}"


def test_the_classified_notice_still_claims_its_suppression_window() -> None:
    """The classification above holds only while the task keeps claiming the window before it sends."""
    tree = ast.parse((APP / "tasks" / "auth_tasks.py").read_text(encoding="utf-8"))
    task = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "send_duplicate_registration_notice"
    )
    claims = [
        n
        for n in ast.walk(task)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "claim"
        and isinstance(n.func.value, ast.Call)
        and isinstance(n.func.value.func, ast.Name)
        and n.func.value.func.id == "get_registration_notice_store"
    ]

    assert claims, "send_duplicate_registration_notice no longer claims get_registration_notice_store()"


# ── self-test: the predicate on synthetic code ────────────────────────────

_SYNTHETIC_SERVICE = """
from functools import partial

class S:
    def unbounded(self, email):
        self._deliver(partial(self._send, email))

    def bounded(self, email):
        if self._store.reserve_attempt("p:" + email) > 3:
            return
        self._deliver(lambda: self._send(email))

    def silent(self, email):
        self._repo.get_by_email(email)

    def _deliver(self, send):
        send()

    def _send(self, email):
        self._email_service.send_password_reset_email(to_email=email, token="t", frontend_url="u")
"""

_SYNTHETIC_HELPERS = {
    "_enqueue": "def _enqueue(key):\n    from app.tasks.auth_tasks import dispatch\n    dispatch(key)\n",
    "_plain": "def _plain(key):\n    return key\n",
}


def _synthetic(routes: list[tuple[str, str]]) -> dict[str, bool]:
    return _members(routes, _methods(_SYNTHETIC_SERVICE, "S"), _SYNTHETIC_HELPERS)


def test_selftest_a_mail_through_partial_and_a_helper_is_reached() -> None:
    members = _synthetic([("/a", "def a(service):\n    service.unbounded(x)\n")])

    assert members == {"/a unbounded": False}


def test_selftest_a_reservation_marks_the_member_bounded() -> None:
    members = _synthetic([("/b", "def b(service):\n    service.bounded(x)\n")])

    assert members == {"/b bounded": True}


def test_selftest_a_route_that_reaches_no_mail_is_no_member() -> None:
    members = _synthetic([("/c", "def c(service):\n    service.silent(x)\n    _plain(x)\n")])

    assert members == {}


def test_selftest_a_task_dispatching_helper_is_a_member() -> None:
    members = _synthetic([("/d", "def d(tasks):\n    tasks.add_task(_enqueue, k)\n")])

    assert members == {"/d task:_enqueue": False}


def test_selftest_the_old_password_reset_shape_is_flagged() -> None:
    """#2043 itself: the reset request before its budget — a lookup, then a deferred mail, no reservation."""
    old = """
class S:
    def request_password_reset(self, email, *, defer_mail=None):
        user = self._user_repo.get_by_email(email)
        if user is None:
            return
        def _issue_and_send():
            self._email_service.send_password_reset_email(to_email=email, token="t", frontend_url="u")
        self._deliver_mail("password_reset", _issue_and_send, defer_mail)

    def _deliver_mail(self, kind, send, defer):
        send()
"""
    members = _members(
        [("/password-reset/request", "def r(service):\n    service.request_password_reset(e)\n")],
        _methods(old, "S"),
        {},
    )

    assert members == {"/password-reset/request request_password_reset": False}
