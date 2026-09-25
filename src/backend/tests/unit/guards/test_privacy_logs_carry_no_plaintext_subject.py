"""No log line on the privacy, auth, retention or storage path names a data subject (#1773).

The erasure pipeline's rule since #1700 is that its log lines carry ``subject=`` —
the salted tombstone reference (``ErasureEngine.log_subject``) — and never the
account key: a log stream has no retention rule of its own (NFR-011), so whatever
it receives outlives the account it names, the erasure that removed the account,
and the erasure record that proves it (R-06). #1700 applied that rule to the
erasure lines and stopped; the sibling lines in the same service kept
``user_key=``, ``old_email=`` and ``new_email=``, and the storage adapters kept
logging object keys that embed the account key (``privacy/exports/<user_key>/…``).
**This guard is for the class**, not for the lines #1773 listed: it enumerates
every log call in every module the selector below derives, and refuses one that
hands a subject's identifier to the logger.

One detector, :func:`_findings_in_source`, decides for the tree scan **and** for
the parametrised self-test, so the self-test exercises the rule through the same
path the scan does — not a re-implementation of it.

What counts as a log call: ``<receiver>.<level>(…)`` where the receiver is named
``logger``/``log`` or ends in ``_logger``/``_log``, and a bare ``log(…)`` /
``logger(…)`` call — the spelling of a level chosen at run time
(``log = logger.error if … else logger.info``).

What counts as "names a subject" — both halves, because either alone misses a
spelling the other catches:

* **by keyword**: ``user_key=``, ``email=`` or any ``*_email=`` keyword (``old_email``,
  ``new_email``, ``provider_email``, ``to_email``), unless the name says the value is
  a digest (``*_sha256``, ``*_digest``, ``*_hash``);
* **by value**, under ANY keyword or as a positional argument: a bare name or
  attribute that *is* the identifier — ``user_key``, ``x.user_key``, anything ending
  in ``email``, ``user.key`` / ``account.key`` / ``current_user.key`` — including
  inside ``a or b``, ``a if c else b`` and f-strings. ``subject=user_key`` is the
  renamed-keyword spelling this half exists for. A value wrapped in a call
  (``log_subject(user_key)``, ``email_digest(address)``) passes: the call is where
  the pseudonymisation happens;
* **storage object keys**: in ``data_access/storage/`` a ``key``/``prefix``/``src``/
  ``dst`` keyword, and anywhere on the surface an ``*object_key``/``*storage_key``
  keyword, must be a call (``loggable_storage_key``) or a literal, never the raw
  key — the key shape is decided by the caller, and the export bundle's embeds the
  account key.

**What the selector derives**: every tracked module under ``app/`` whose path names
the privacy, auth, retention, erasure, data-subject or export surface, plus the
device-pairing store (it is authentication, but its file name does not say so), the
storage adapters and ``user_service`` (account deletion). A new module on that
surface is guarded by being named like it; one named otherwise is not — see below.
``app/migrations/`` is excluded: an applied migration's source is frozen
(``test_applied_migration_sources_are_frozen``), so a finding there could not be
fixed without breaking that guard; its log lines are part of the residue below.

**Allow-list**: keyed ``path::enclosing_function::keyword`` rather than by line, so
an unrelated edit above an entry neither orphans it nor moves the excuse onto a
different line. Every entry must name a live site (``test_allowlist_entries_still_exist``).

**Spellings this guard cannot see** (named so nobody reads green as more than it is):

* a value laundered through a neutral local first (``who = user.key`` then
  ``who=who``) — the AST has no data flow here;
* ``**fields`` splats and ``extra={...}`` dicts built elsewhere;
* identifiers inside an exception message (``error=str(exc)`` where the exception
  text embeds a key or address) — the export failure path redacts its exception
  text (``PrivacyService._redact_subject``), but nothing here enforces that;
* a raw storage key under a keyword not listed above (``path=``, ``file_path=``);
* a logger reached under another name (``self._audit.info(...)``, an inline
  ``structlog.get_logger().info(...)``) or a level method outside ``_LOG_METHODS``;
* ``structlog.contextvars.bind_contextvars(...)``, and a ``bind`` in another
  module whose bound context later lines inherit;
* modules outside the selector — ``migrations/``, ``notification_service``, the
  e-mail adapters, ``tenant_service`` and others still log keys/addresses; they are
  the recorded residue of #1773 (follow-up issue), not covered here;
* other personal data such as ``ip_address=`` — the guard asserts identifiers of
  the account (key, address) only.
"""

from __future__ import annotations

import ast
import pathlib
import re
import subprocess

import pytest

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[3]

#: Path fragments that put a module on the guarded surface.
_SURFACE = re.compile(
    r"(privacy|auth|retention|erasure|data_subject|data_export|device_pairing|/storage/|user_service)"
)
#: Excluded with the reason in the module docstring.
_EXCLUDED_DIRS = ("app/migrations/",)

_LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "fatal", "msg", "bind"}
_LOGGER_RECEIVER = re.compile(r"(^|_)(logger|log)$")
#: A bare call on one of these names is a logger method chosen at run time.
_LOGGER_CALLABLES = {"log", "logger"}
_DIGEST_SUFFIX = re.compile(r"_(sha256|digest|hash)$")
_SUBJECT_KEYWORD = re.compile(r"^(user_key|email|\w+_email)$")
_IDENTIFIER_NAME = re.compile(r"(^|_)(user_key|email)$")
_SUBJECT_OWNERS = {"user", "account", "current_user", "subject_user", "created_user"}
_STORAGE_MODULE_KEYWORDS = {"key", "prefix", "src", "dst"}
_STORAGE_KEY_KEYWORD = re.compile(r"(^|_)(object_key|storage_key)$")

#: ``path::enclosing_function::keyword`` -> reason a subject identifier may be
#: logged there. Empty on purpose: every site #1773 found could log the salted
#: reference instead, so none needed an excuse.
_ALLOWED: dict[str, str] = {}


def _is_log_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in _LOGGER_CALLABLES
    if not isinstance(func, ast.Attribute) or func.attr not in _LOG_METHODS:
        return False
    receiver = func.value
    name = receiver.attr if isinstance(receiver, ast.Attribute) else getattr(receiver, "id", "")
    return bool(_LOGGER_RECEIVER.search(name))


def _raw_identifier(value: ast.expr) -> str | None:
    """The subject identifier *value* hands over unwrapped, if any."""
    if isinstance(value, ast.Name) and _IDENTIFIER_NAME.search(value.id):
        return value.id
    if isinstance(value, ast.Attribute):
        if _IDENTIFIER_NAME.search(value.attr):
            return ast.unparse(value)
        owner = value.value
        if value.attr == "key" and isinstance(owner, ast.Name) and owner.id in _SUBJECT_OWNERS:
            return ast.unparse(value)
    if isinstance(value, ast.BoolOp):
        return next((hit for part in value.values if (hit := _raw_identifier(part))), None)
    if isinstance(value, ast.IfExp):
        return _raw_identifier(value.body) or _raw_identifier(value.orelse)
    if isinstance(value, ast.JoinedStr):
        parts = [p.value for p in value.values if isinstance(p, ast.FormattedValue)]
        return next((hit for part in parts if (hit := _raw_identifier(part))), None)
    return None


def _is_raw_storage_key(keyword: str, value: ast.expr, *, storage_module: bool) -> bool:
    names_a_key = (storage_module and keyword in _STORAGE_MODULE_KEYWORDS) or bool(_STORAGE_KEY_KEYWORD.search(keyword))
    return names_a_key and not isinstance(value, ast.Call | ast.Constant)


class _LogCallVisitor(ast.NodeVisitor):
    """Walks one module, tracking the enclosing function of every log call."""

    def __init__(self, rel: str, allowed: dict[str, str]) -> None:
        self.rel = rel
        self.allowed = allowed
        self.storage_module = "/storage/" in rel
        self.scope: list[str] = []
        self.findings: list[str] = []
        self.sites: set[str] = set()

    def _enter(self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._enter(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter(node)

    def visit_Call(self, node: ast.Call) -> None:
        if _is_log_call(node):
            self._check(node)
        self.generic_visit(node)

    def _check(self, node: ast.Call) -> None:
        enclosing = ".".join(self.scope) or "<module>"
        where = f"{self.rel}:{node.lineno} ({enclosing})"
        for arg in node.args:
            if hit := _raw_identifier(arg):
                self.findings.append(f"{where}: positional {hit}")
        for kw in node.keywords:
            if kw.arg is None:
                continue
            site = f"{self.rel}::{enclosing}::{kw.arg}"
            self.sites.add(site)
            if site in self.allowed:
                continue
            if _SUBJECT_KEYWORD.match(kw.arg) and not _DIGEST_SUFFIX.search(kw.arg):
                self.findings.append(f"{where}: {kw.arg}= (keyword names a subject identifier)")
            elif hit := _raw_identifier(kw.value):
                self.findings.append(f"{where}: {kw.arg}={hit} (value is a subject identifier)")
            elif _is_raw_storage_key(kw.arg, kw.value, storage_module=self.storage_module):
                self.findings.append(f"{where}: {kw.arg}= (raw storage key; log it through loggable_storage_key)")


def _scan_source(source: str, rel: str, allowed: dict[str, str] | None = None) -> _LogCallVisitor:
    visitor = _LogCallVisitor(rel, _ALLOWED if allowed is None else allowed)
    visitor.visit(ast.parse(source))
    return visitor


def _findings_in_source(source: str, rel: str, allowed: dict[str, str] | None = None) -> list[str]:
    """THE detector: every log call in *source* (a module at *rel*) that names a subject."""
    return _scan_source(source, rel, allowed).findings


def _guarded_modules() -> list[pathlib.Path]:
    tracked = subprocess.run(
        ["git", "ls-files", "app"], cwd=BACKEND_ROOT, check=True, capture_output=True, text=True
    ).stdout.split()
    return [
        BACKEND_ROOT / rel
        for rel in sorted(tracked)
        if rel.endswith(".py") and _SURFACE.search("/" + rel) and not rel.startswith(_EXCLUDED_DIRS)
    ]


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(BACKEND_ROOT).as_posix()


def _surface_scans() -> list[_LogCallVisitor]:
    return [_scan_source(path.read_text(encoding="utf-8"), _rel(path)) for path in _guarded_modules()]


def test_selector_reaches_the_surface() -> None:
    """The selector must find the modules #1773 names — an empty population is green over nothing."""
    names = {p.name for p in _guarded_modules()}
    for expected in (
        "privacy_service.py",
        "data_subject_service.py",
        "user_service.py",
        "auth_service.py",
        "retention_tasks.py",
        "s3_adapter.py",
        "local_fs_adapter.py",
        "redis_device_pairing.py",
    ):
        assert expected in names, f"selector lost {expected}"


def test_the_scan_sees_log_calls() -> None:
    """A detector that recognised no log call would be green over nothing."""
    sites = {site for scan in _surface_scans() for site in scan.sites}
    assert len(sites) > 100, f"only {len(sites)} log-call keyword sites seen on the surface"


def test_no_log_call_names_a_data_subject() -> None:
    problems = [finding for scan in _surface_scans() for finding in scan.findings]
    assert not problems, (
        "log calls hand a data subject's account key or address to the logger (#1773). "
        "Log the salted subject reference (ErasureEngine.log_subject), email_digest(...) "
        "or loggable_storage_key(...) instead:\n  " + "\n  ".join(problems)
    )


def test_allowlist_entries_still_exist() -> None:
    """An allow-list entry whose site vanished is a stale excuse, not a record."""
    live = {site for scan in _surface_scans() for site in scan.sites}
    assert set(_ALLOWED) <= live, sorted(set(_ALLOWED) - live)


_SERVICE = "app/domain/services/probe_service.py"
_STORAGE = "app/data_access/storage/probe_adapter.py"


@pytest.mark.parametrize(
    ("rel", "source", "caught"),
    [
        (_SERVICE, "logger.info('e', user_key=k)", True),
        (_SERVICE, "logger.info('e', subject=user_key)", True),
        (_SERVICE, "logger.info('e', subject=user.key)", True),
        (_SERVICE, "logger.info('e', new_email=user.email)", True),
        (_SERVICE, "logger.info('e', who=export.user_key or '')", True),
        (_SERVICE, "logger.info('e', who=a if c else record.user_key)", True),
        (_SERVICE, "logger.info(f'erased {user_key}')", True),
        (_SERVICE, "logger.info('erased %s', user_key)", True),
        (_SERVICE, "log = logger.error\nlog('e', user_key=k)", True),
        (_SERVICE, "self._logger.warning('e', email=addr)", True),
        (_SERVICE, "logger.error('e', object_key=object_key)", True),
        (_STORAGE, "logger.info('storage_delete_object', key=key)", True),
        (_STORAGE, "logger.info('storage_copy_object', src=src_key, dst=loggable_storage_key(dst_key))", True),
        (_STORAGE, "logger.info('storage_delete_prefix', prefix=safe_prefix)", True),
        (_STORAGE, "logger.info('storage_delete_object', key=loggable_storage_key(key))", False),
        (_STORAGE, "logger.info('storage_put_object', backend=BACKEND_KEY, size_bytes=1)", False),
        (_SERVICE, "logger.info('e', key=export.key)", False),
        (_SERVICE, "log.warning('e', email_sha256=email_digest(addr))", False),
        (_SERVICE, "logger.info('e', subject=log_subject(user_key, salt))", False),
        (_SERVICE, "logger.info('e', export_key=export.key)", False),
        (_SERVICE, "logger.error('e', object_key=loggable_storage_key(object_key))", False),
        (_SERVICE, "send(user_key=k, email=addr)", False),
    ],
)
def test_detector_sees_each_spelling(rel: str, source: str, caught: bool) -> None:
    """The detector itself — the function the scan runs — on every spelling the docstring claims."""
    findings = _findings_in_source(source, rel, allowed={})
    assert bool(findings) is caught, findings


_ALLOWLIST_PROBE = """
class Service:
    def refuse(self, user):
        logger.warning("refused", user_key=user.key)

    def other(self, user):
        logger.warning("refused", user_key=user.key)
"""


def test_allowlist_is_keyed_by_enclosing_function_and_keyword() -> None:
    """An entry excuses exactly its ``path::function::keyword`` — not the sibling method, not another line."""
    entry = f"{_SERVICE}::Service.refuse::user_key"
    allowed = {entry: "probe"}

    unexcused = _findings_in_source(_ALLOWLIST_PROBE, _SERVICE, allowed={})
    excused = _findings_in_source(_ALLOWLIST_PROBE, _SERVICE, allowed=allowed)

    assert len(unexcused) == 2, unexcused
    assert len(excused) == 1, excused
    assert "(Service.other)" in excused[0], "the entry excused the sibling method instead"
    shifted = _findings_in_source("\n\n\n" + _ALLOWLIST_PROBE, _SERVICE, allowed=allowed)
    assert len(shifted) == 1, "the entry must survive lines shifting above it"
    assert "(Service.other)" in shifted[0]
    assert entry in _scan_source(_ALLOWLIST_PROBE, _SERVICE, allowed).sites
