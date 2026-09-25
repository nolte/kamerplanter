"""No log call anywhere under ``app/`` or ``scripts/`` hands a secret to the logger (#1795).

A token, API key, password or cookie that reaches a log line is a credential
copied into a stream that has no retention rule (NFR-011), no access control
beyond "can read the cluster's logs" and no rotation. #1795 found the class on
four surfaces — the console e-mail adapter logged the password-reset URL, whose
token takes over the account; httpx logged the OpenWeatherMap/Perenual request
URL with the API key in its query; uvicorn and nginx logged the attachment
token path — and this guard covers the one of them that is a log call in this
tree, **for the class**: every log call in every module the selector derives.
The other three are library/proxy access logs and are held by
``test_logs_carry_no_secrets_runtime.py`` and the nginx ``log_format``.

One detector, :func:`_findings_in_source`, decides for the tree scan **and** for
the parametrised self-test, so the self-test exercises the rule through the same
path the scan does. What counts as a log call is decided by the privacy guard's
:func:`_is_log_call` (imported, not mirrored, so both guards agree on the
receiver rule), and the selector is its :func:`_guarded_modules`: every tracked
``*.py`` under ``app/`` and ``scripts/``.

What counts as "hands a secret over" — a log-call argument, keyword or
positional, that *references*:

* **a secret-named name or attribute** (:data:`_SECRET_NAME`): ``token`` and any
  ``*_token``, ``api_key``/``*_api_key``/``apikey``, ``secret``/``*_secret``/
  ``secret_key``/``private_key``, ``password``/``*_password``/``passwd``,
  ``authorization``, ``cookie`` — also inside an f-string, ``a or b``,
  ``a if c else b``, a ``+`` concatenation, a subscript (``token[:8]`` is still
  part of the secret) and the arguments or receiver of any call that is not a
  redaction (``str(token)``, ``token.strip()``);
* **a local tainted by one**: within one function (or the module body), a simple
  ``name = <expr>`` / ``name: T = <expr>`` whose right-hand side references a
  secret or an already tainted local taints ``name``, to a fixpoint. This is the
  #1795 console-adapter spelling — ``url = f"{frontend}/password-reset/{token}"``
  then ``reset_url=url``;
* **a secret-named keyword** whose value is not a literal or a redaction call
  (a ``password`` keyword bound to a local) — the renamed-value spelling the
  value half cannot see.

What passes: a value wrapped in a redaction call (:data:`_REDACTIONS`:
``loggable_error``, ``log_subject``, ``email_digest``, ``loggable_path``,
``loggable_url_text``, ``loggable_ip``, ``len``, ``bool``), ``type(x).__name__``, a comparison
(``token is not None`` is a bool), and a keyword whose NAME states a non-secret
(:data:`_NON_SECRET_KEYWORD`: ``token_type``, ``has_*``/``is_*``, ``*_count``,
``*_len``, ``*_configured``, ``*_sha256``/``*_digest``/``*_hash``, ``*_type``) —
but only when its value is a call, a comparison or a literal: a raw secret
under a harmless name (``token_hash=token``) is still reported.

**Allow-list**: keyed ``path::enclosing_function::keyword`` (``<positional>`` for
a positional argument), every entry with a reason read from the code, and every
entry must name a live site (``test_allowlist_entries_still_exist``). An entry
excused as debug-only is re-checked against the code
(``test_debug_only_entries_are_debug_gated``): the key alone would keep matching
if the ``settings.debug`` gate were removed.

**Spellings this guard cannot see** (named so nobody reads green as more than it is):

* a secret under a name outside :data:`_SECRET_NAME` — ``raw_key`` (the freshly
  minted API key in ``AuthService.create_api_key``; ``*_key`` is too broad to
  add: ``user_key``, ``tenant_key``), ``dsn``, ``url`` of a DSN — and a neutral
  name that never touched a secret-named one in the same function — a parameter
  ``value`` the caller filled with a token, a dict value (``creds["x"]``), an
  attribute of a neutral object (``cfg.value``);
* taint across functions, through a tuple unpacking, a ``for`` target, a
  ``with … as``, an augmented assignment or a container (``parts.append(token)``);
* ``**fields`` splats and ``extra={...}`` dicts built elsewhere, and
  ``structlog.contextvars.bind_contextvars(...)``;
* a logger reached under another name or a level method outside the privacy
  guard's receiver rule (see its docstring);
* exception texts and tracebacks that embed a secret (an httpx error names the
  request URL) — ``loggable_error`` masks URL query strings and userinfo, the
  traceback half is #1796;
* library and proxy access logs (httpx/httpcore/urllib3, ``uvicorn.access``,
  nginx) — not log calls in this tree; held at runtime by
  ``test_logs_carry_no_secrets_runtime.py`` and by the redacted nginx
  ``log_format`` in ``src/frontend/nginx.conf`` and the Helm ConfigMaps;
* the side services ``src/inference-service`` and ``src/knowledge-service``.
"""

from __future__ import annotations

import ast
import re

import pytest

from tests.unit.guards.test_privacy_logs_carry_no_plaintext_subject import (
    BACKEND_ROOT,
    _guarded_modules,
    _is_log_call,
    _rel,
)

#: A name or attribute that holds a secret.
_SECRET_NAME = re.compile(
    r"(^|_)(token|api_key|apikey|secret|secret_key|private_key|password|passwd|authorization|cookie)$",
    re.IGNORECASE,
)
#: A keyword whose name states that its value is not the secret itself.
_NON_SECRET_KEYWORD = re.compile(
    r"^(token_type|has_\w+|is_\w+)$|_(count|len|length|configured|sha256|digest|hash|type)$",
    re.IGNORECASE,
)
#: A call to one of these is where a value is reduced to something loggable.
_REDACTIONS = {
    "loggable_error",
    "log_subject",
    "email_digest",
    "loggable_path",
    "loggable_url_text",
    "loggable_ip",
    "len",
    "bool",
}

_POSITIONAL = "<positional>"

#: ``path::enclosing_function::keyword`` -> reason a secret-referencing value may
#: be logged there, read from the code.
_CONSOLE_DEBUG_LINK = (
    "logged only under settings.debug (the early return above handles every other case): the console "
    "adapter's documented dev path, so a local operator can complete a registration/reset (#1795)"
)
_TOKEN_CLAIMS = (
    "payload is the HMAC-verified claim set verify(token) decoded, not the token: tenant_key and aid are "
    "claims naming the tenant and attachment; neither the token nor its signature is logged"
)
_ALLOWED: dict[str, str] = {
    "app/api/v1/attachments/token_router.py::redeem_token::tenant_key": _TOKEN_CLAIMS,
    "app/api/v1/attachments/token_router.py::redeem_token::attachment_id": _TOKEN_CLAIMS,
    "app/data_access/external/console_email_adapter.py::ConsoleEmailAdapter.send_verification_email"
    "::verification_url": _CONSOLE_DEBUG_LINK,
    "app/data_access/external/console_email_adapter.py::ConsoleEmailAdapter.send_password_reset_email"
    "::reset_url": _CONSOLE_DEBUG_LINK,
}


def _call_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _secret_reference(value: ast.expr, tainted: set[str]) -> str | None:
    """The secret (or tainted local) *value* references unredacted, if any."""
    if isinstance(value, ast.Name):
        if _SECRET_NAME.search(value.id) or value.id in tainted:
            return value.id
        return None
    if isinstance(value, ast.Attribute):
        if value.attr == "__name__":
            return None
        if _SECRET_NAME.search(value.attr):
            return ast.unparse(value)
        return None
    if isinstance(value, ast.Call):
        if _call_name(value.func) in _REDACTIONS:
            return None
        parts: list[ast.expr] = [*value.args, *(kw.value for kw in value.keywords)]
        if isinstance(value.func, ast.Attribute):
            parts.append(value.func.value)
        return next((hit for part in parts if (hit := _secret_reference(part, tainted))), None)
    if isinstance(value, ast.BoolOp):
        return next((hit for part in value.values if (hit := _secret_reference(part, tainted))), None)
    if isinstance(value, ast.IfExp):
        return _secret_reference(value.body, tainted) or _secret_reference(value.orelse, tainted)
    if isinstance(value, ast.BinOp):
        return _secret_reference(value.left, tainted) or _secret_reference(value.right, tainted)
    if isinstance(value, ast.JoinedStr):
        parts = [p.value for p in value.values if isinstance(p, ast.FormattedValue)]
        return next((hit for part in parts if (hit := _secret_reference(part, tainted))), None)
    if isinstance(value, ast.Subscript):
        return _secret_reference(value.value, tainted)
    if isinstance(value, ast.Starred):
        return _secret_reference(value.value, tainted)
    return None


def _own_statements(body: list[ast.stmt]) -> list[ast.AST]:
    """Every node of *body* that belongs to this scope — nested functions and classes excluded."""
    nodes: list[ast.AST] = []
    stack: list[ast.AST] = list(body)
    while stack:
        node = stack.pop()
        nodes.append(node)
        for child in ast.iter_child_nodes(node):
            if not isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda):
                stack.append(child)
    return nodes


def _tainted_locals(body: list[ast.stmt]) -> set[str]:
    """Locals assigned (directly or transitively) from a secret in this scope — a fixpoint."""
    assignments: list[tuple[str, ast.expr]] = []
    for node in _own_statements(body):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assignments.append((node.targets[0].id, node.value))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            assignments.append((node.target.id, node.value))
    tainted: set[str] = set()
    changed = True
    while changed:
        changed = False
        for name, rhs in assignments:
            if name not in tainted and _secret_reference(rhs, tainted):
                tainted.add(name)
                changed = True
    return tainted


class _SecretLogVisitor(ast.NodeVisitor):
    """Walks one module, tracking the enclosing function and its tainted locals."""

    def __init__(self, rel: str, allowed: dict[str, str]) -> None:
        self.rel = rel
        self.allowed = allowed
        self.scope: list[str] = []
        self.taint: list[set[str]] = []
        self.findings: list[str] = []
        self.sites: set[str] = set()

    def visit_Module(self, node: ast.Module) -> None:
        self.taint.append(_tainted_locals(node.body))
        self.generic_visit(node)
        self.taint.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _enter_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        self.taint.append(_tainted_locals(node.body))
        self.generic_visit(node)
        self.taint.pop()
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        if _is_log_call(node):
            self._check(node)
        self.generic_visit(node)

    def _report(self, site: str, finding: str) -> None:
        self.sites.add(site)
        if site not in self.allowed:
            self.findings.append(finding)

    def _check(self, node: ast.Call) -> None:
        enclosing = ".".join(self.scope) or "<module>"
        where = f"{self.rel}:{node.lineno} ({enclosing})"
        tainted = self.taint[-1] if self.taint else set()
        for arg in node.args:
            if hit := _secret_reference(arg, tainted):
                self._report(f"{self.rel}::{enclosing}::{_POSITIONAL}", f"{where}: positional {hit}")
        for kw in node.keywords:
            if kw.arg is None:
                continue
            site = f"{self.rel}::{enclosing}::{kw.arg}"
            self.sites.add(site)
            # A keyword NAME that states a non-secret (``token_count``, ``has_token``)
            # only excuses a value that is computed from the secret — a call or a
            # comparison. A raw secret under that name is still the secret
            # (``token_hash=token``, review SEC-010).
            if _NON_SECRET_KEYWORD.search(kw.arg) and isinstance(kw.value, ast.Call | ast.Compare | ast.Constant):
                continue
            if hit := _secret_reference(kw.value, tainted):
                self._report(site, f"{where}: {kw.arg}={hit} (value references a secret)")
            elif _SECRET_NAME.search(kw.arg) and not isinstance(kw.value, ast.Constant | ast.Call):
                self._report(site, f"{where}: {kw.arg}= (keyword names a secret)")


def _scan_source(source: str, rel: str, allowed: dict[str, str] | None = None) -> _SecretLogVisitor:
    visitor = _SecretLogVisitor(rel, _ALLOWED if allowed is None else allowed)
    visitor.visit(ast.parse(source))
    return visitor


def _findings_in_source(source: str, rel: str, allowed: dict[str, str] | None = None) -> list[str]:
    """THE detector: every log call in *source* (a module at *rel*) that hands a secret to the logger."""
    return _scan_source(source, rel, allowed).findings


def _surface_scans() -> list[_SecretLogVisitor]:
    return [_scan_source(path.read_text(encoding="utf-8"), _rel(path)) for path in _guarded_modules()]


def test_selector_reaches_the_surface() -> None:
    """The #1795 log-call surface must be in the population — an empty population is green over nothing."""
    names = {p.name for p in _guarded_modules()}
    for expected in (
        "console_email_adapter.py",
        "smtp_email_adapter.py",
        "auth_service.py",
        "openweathermap_weather_adapter.py",
        "perenual_adapter.py",
        "token_router.py",
    ):
        assert expected in names, f"selector lost {expected}"


def test_the_scan_sees_log_calls() -> None:
    """A detector that recognised no log call would be green over nothing."""
    sites = {site for scan in _surface_scans() for site in scan.sites}
    assert len(sites) > 100, f"only {len(sites)} log-call argument sites seen"


def test_no_log_call_hands_a_secret_to_the_logger() -> None:
    problems = [finding for scan in _surface_scans() for finding in scan.findings]
    assert not problems, (
        "log calls hand a token, API key, password or a value built from one to the logger (#1795). "
        "Log a digest (*_sha256=), a presence flag (has_*=, bool(...)), a length, "
        "loggable_path(...)/loggable_error(...) (app.common.log_privacy), or nothing:\n  " + "\n  ".join(problems)
    )


def test_allowlist_entries_still_exist() -> None:
    """An allow-list entry whose site vanished is a stale excuse, not a record."""
    live = {site for scan in _surface_scans() for site in scan.sites}
    assert set(_ALLOWED) <= live, sorted(set(_ALLOWED) - live)


def _is_debug_test(test: ast.expr, *, negated: bool) -> bool:
    """``settings.debug`` (or ``not settings.debug`` when *negated*)."""
    if negated:
        if not (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)):
            return False
        test = test.operand
    return (
        isinstance(test, ast.Attribute)
        and test.attr == "debug"
        and isinstance(test.value, ast.Name)
        and test.value.id == "settings"
    )


def _debug_gated_keywords(function: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[set[str], set[str]]:
    """(keywords logged only under ``settings.debug``, keywords logged outside it) in *function*'s own body.

    Gated means: inside ``if settings.debug:``, or after a top-level
    ``if not settings.debug: … return`` guard.
    """
    gated: set[str] = set()
    ungated: set[str] = set()

    def keywords(node: ast.AST) -> set[str]:
        return {
            kw.arg
            for call in ast.walk(node)
            if isinstance(call, ast.Call) and _is_log_call(call)
            for kw in call.keywords
            if kw.arg
        }

    returned_outside_debug = False
    for stmt in function.body:
        if isinstance(stmt, ast.If) and _is_debug_test(stmt.test, negated=True):
            ungated |= keywords(stmt)
            returned_outside_debug = bool(stmt.body) and isinstance(stmt.body[-1], ast.Return)
        elif isinstance(stmt, ast.If) and _is_debug_test(stmt.test, negated=False):
            gated |= set().union(*(keywords(s) for s in stmt.body))
            ungated |= set().union(*(keywords(s) for s in stmt.orelse))
        elif returned_outside_debug:
            gated |= keywords(stmt)
        else:
            ungated |= keywords(stmt)
    return gated, ungated


def test_debug_only_entries_are_debug_gated() -> None:
    """An entry excused as "logged only under settings.debug" must still BE gated — else it excuses a leak.

    The allow-list is keyed by function and keyword, so removing the gate would
    leave the entry matching; this re-derives the gate from the code.
    """
    debug_only = [site for site, reason in _ALLOWED.items() if reason is _CONSOLE_DEBUG_LINK]
    assert debug_only, "no debug-only entry — this check would be vacuous"
    for site in debug_only:
        rel, qualname, keyword = site.split("::")
        tree = ast.parse((BACKEND_ROOT / rel).read_text(encoding="utf-8"))
        class_name, function_name = qualname.split(".")
        (cls,) = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name]
        (function,) = [
            n for n in cls.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef) and n.name == function_name
        ]
        gated, ungated = _debug_gated_keywords(function)
        assert keyword in gated and keyword not in ungated, f"{site}: {keyword}= is logged outside settings.debug"


_MOD = "app/data_access/external/probe_adapter.py"


def _in_function(body: str) -> str:
    return "def probe(token, frontend_url, settings, user, resp, headers):\n" + "".join(
        f"    {line}\n" for line in body.splitlines()
    )


@pytest.mark.parametrize(
    ("source", "caught"),
    [
        # by value, direct
        ("logger.info('e', token=token)", True),
        ("logger.info('e', value=token)", True),
        ("logger.info('e', key=settings.perenual_api_key)", True),
        ("logger.info('e', key=settings.openweathermap_apikey)", True),
        ("logger.info('e', pw=user.password)", True),
        ("logger.info('e', secret=settings.jwt_secret_key)", True),
        ("logger.info('e', header=headers.authorization)", True),
        ("logger.info('e', c=resp.cookie)", True),
        ("logger.info('e', t=refresh_token)", True),
        ("logger.info('sent %s', token)", True),
        ("logger.info(f'reset {token}')", True),
        ("logger.info('e', t=token or '')", True),
        ("logger.info('e', t=x if c else token)", True),
        ("logger.info('e', t='Bearer ' + token)", True),
        ("logger.info('e', t=token[:8])", True),
        ("logger.info('e', t=str(token))", True),
        ("logger.info('e', t=token.strip())", True),
        ("log('e', t=token)", True),
        ("self._logger.warning('e', t=access_token)", True),
        # by taint
        ("url = f'{frontend_url}/password-reset/{token}'\nlogger.info('e', reset_url=url)", True),
        ("a = token\nb = a + 'x'\nlogger.info('e', v=b)", True),
        ("url: str = frontend_url + token\nlogger.info('e', u=url)", True),
        ("url = f'{frontend_url}/x/{token}'\nlogger.info('reset %s', url)", True),
        # by keyword name
        ("logger.info('e', password=pw)", True),
        ("logger.info('e', api_key=k)", True),
        # passes
        ("logger.info('e', token_type='bearer')", False),
        ("logger.info('e', has_token=token is not None)", False),
        ("logger.info('e', token_configured=bool(token))", False),
        ("logger.info('e', token_len=len(token))", False),
        ("logger.info('e', t=bool(token))", False),
        ("logger.info('e', t=len(token))", False),
        ("logger.info('e', error=loggable_error(exc))", False),
        ("logger.info('e', path=loggable_path(path))", False),
        ("logger.info('e', error_type=type(token).__name__)", False),
        ("logger.info('e', token_sha256=digest(token))", False),
        ("logger.info('e', present=token is not None)", False),
        ("logger.info('e', password='<redacted>')", False),
        ("url = f'{frontend_url}/x'\nlogger.info('e', u=url)", False),
        ("send(token=token)", False),
        ("logger.info('e', key=settings.region)", False),
        # a harmless keyword NAME does not excuse a raw secret VALUE (review SEC-010)
        ("logger.info('e', token_hash=token)", True),
        ("logger.info('e', password_type=user.password)", True),
        ("logger.info('e', is_token=token)", True),
        ("logger.info('e', token_count=refresh_token)", True),
        ("url = f'{frontend_url}/x/{token}'\nlogger.info('e', url_len=url)", True),
        ("logger.info('e', token_sha256=digest(token))", False),
        ("logger.info('e', token_count=len(tokens))", False),
        ("logger.info('e', has_token=token is not None)", False),
    ],
)
def test_detector_sees_each_spelling(source: str, caught: bool) -> None:
    """The detector itself — the function the scan runs — on every spelling the docstring claims."""
    findings = _findings_in_source(_in_function(source), _MOD, allowed={})
    assert bool(findings) is caught, findings


def test_taint_does_not_leak_across_functions() -> None:
    source = "def a(token):\n    url = token\n\ndef b(url):\n    logger.info('e', u=url)\n"
    assert _findings_in_source(source, _MOD, allowed={}) == []


_ALLOWLIST_PROBE = """
class Adapter:
    def send(self, token):
        logger.info("sent", reset_url=token)

    def other(self, token):
        logger.info("sent", reset_url=token)
"""


def test_allowlist_is_keyed_by_enclosing_function_and_keyword() -> None:
    """An entry excuses exactly its ``path::function::keyword`` — not the sibling method, not another line."""
    entry = f"{_MOD}::Adapter.send::reset_url"
    allowed = {entry: "probe"}

    unexcused = _findings_in_source(_ALLOWLIST_PROBE, _MOD, allowed={})
    excused = _findings_in_source(_ALLOWLIST_PROBE, _MOD, allowed=allowed)

    assert len(unexcused) == 2, unexcused
    assert len(excused) == 1, excused
    assert "(Adapter.other)" in excused[0], "the entry excused the sibling method instead"
    shifted = _findings_in_source("\n\n\n" + _ALLOWLIST_PROBE, _MOD, allowed=allowed)
    assert len(shifted) == 1, "the entry must survive lines shifting above it"
    assert entry in _scan_source(_ALLOWLIST_PROBE, _MOD, allowed).sites


@pytest.mark.parametrize(
    ("test", "negated", "gated"),
    [
        ("settings.debug", False, True),
        ("not settings.debug", True, True),
        ("request.debug", False, False),
        ("not self.debug", True, False),
        ("debug", False, False),
    ],
)
def test_only_settings_debug_counts_as_the_debug_gate(test: str, negated: bool, gated: bool) -> None:
    """Review SEC-010: any ``.debug`` attribute used to pass as the gate."""
    expr = ast.parse(test, mode="eval").body
    assert _is_debug_test(expr, negated=negated) is gated
