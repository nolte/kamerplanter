"""No log line anywhere under ``app/`` names a data subject (#1773, #1781).

The erasure pipeline's rule since #1700 is that its log lines carry ``subject=`` —
the salted subject reference (``ErasureEngine.log_subject``) — and never the
account key: a log stream has no retention rule of its own (NFR-011), so whatever
it receives outlives the account it names, the erasure that removed the account,
and the erasure record that proves it (R-06). #1700 applied that rule to the
erasure lines and stopped; the sibling lines in the same service kept
``user_key=``, ``old_email=`` and ``new_email=``, and the storage adapters kept
logging object keys that embed the account key (``privacy/exports/<user_key>/…``).
**This guard is for the class**, not for the lines #1773 listed: it enumerates
every log call in every module the selector below derives, and refuses one that
hands a subject's identifier to the logger. #1781 widened the selector from the
privacy surface to every module: the same lines lived in ``notification_service``,
``tenant_service``, the migration seeds and ~50 other modules.

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
  account key;
* **exception texts** (#1773 review GDPR-001/-002/-004): ``str(<name>)`` or
  ``repr(<name>)`` handed to the logger, under any keyword or positionally. An
  exception message can name the subject (``NotFoundError("User", <key>)``), an
  export bundle (``privacy/exports/<key>/…``) or a third party's address
  (``SMTPRecipientsRefused``). Log ``error_type=type(exc).__name__``, or the text
  through a redaction call (``app.common.log_privacy.loggable_error``,
  ``PrivacyService._loggable_error``). The AST cannot tell an exception from any
  other name, so every ``str(<name>)`` is refused; a non-exception value is logged
  in a spelling that states its type (``address.compressed``, ``path.as_posix()``,
  ``origin.value``). Measured when this half was added: 18 log-call sites on the
  surface; 6 were fixed, the 12 whose text was read and found subject-free are
  allow-listed with the reason (10 entries — an entry covers every line of its
  function and keyword). #1781 routed the 101 further sites the widened selector
  found through ``loggable_error``;
* **IP addresses** (#1781): an ``ip``/``ip_address``/``remote_addr``/``*_ip``
  keyword must be a call (``ip_prefix=loggable_ip(ip)``, the NFR-011 R-03
  truncation) or a literal, never the raw address.
* **error messages** (#1796): ``<name>.message`` as a value, under any keyword or
  positionally (also in ``a or b``, conditionals, f-strings) — a
  ``KamerplanterError``'s message names what it is about (``NotFoundError("User",
  <key>)``). Log ``error_code=`` or ``loggable_error(exc)``. Measured when added:
  3 sites (``app_error_handler``, ``OnboardingService._create_plants``,
  ``cleanup_unverified_accounts``), all fixed.

* **a local built from one** (#1830): within one function (or the module body),
  ``name = <expr>`` whose right-hand side references a subject identifier — also
  as a call argument or receiver (``self._build_dedup_key(user_key, …)``), in an
  f-string, a ``+`` or a subscript — taints ``name``, to a fixpoint, unless the
  call is a redaction (``log_subject``, ``email_digest``, ``loggable_error``, …).
  A tainted local handed to the logger bare, in ``a or b``, a conditional or an
  f-string is a finding. Measured when added: 3 sites (the dedup key, fixed; two
  subject-free results, allow-listed);
* **composite keys** (#1830): a ``dedup_key``/``group_key`` keyword must be a call
  or a literal — the notification dedup and group keys embed the account key by
  construction, whichever parameter carries them. Measured when added: 5 sites
  (4 fixed, the site-built frost-forecast key allow-listed).

**What the selector derives**: every tracked ``*.py`` under ``app/`` and ``scripts/``
(the operator scripts log too — ``scripts/storage/migrate.py`` walks every object key,
export bundles included) (#1781). Until
then it was a path regex naming the privacy surface, so a module named otherwise —
``notification_service``, ``tenant_service``, the migration seeds — was not
guarded, and 45 identifier findings lived there. ``app/migrations/versions/`` is
scanned too: its class bodies are frozen (``test_applied_migration_sources_are_frozen``
pins exactly that directory — not the seeds, not ``framework/``, which the earlier
docstring wrongly claimed), so a finding in an applied version is allow-listed with
the frozen reason, and a NEW version module is guarded like any other.

**Allow-list**: keyed ``path::enclosing_function::keyword`` rather than by line, so
an unrelated edit above an entry neither orphans it nor moves the excuse onto a
different line. Every entry must name a live site (``test_allowlist_entries_still_exist``).

**Spellings this guard cannot see** (named so nobody reads green as more than it is):

* a value laundered across a function boundary — a parameter the caller filled
  with a key-bearing value, logged under a neutral keyword (only the composite-key
  keywords above are caught whatever carries them) — and through a tuple
  unpacking, a ``for`` target, a ``with … as``, an augmented assignment or a
  container;
* ``**fields`` splats and ``extra={...}`` dicts built elsewhere;
* an exception text reaching the logger in any other spelling than ``str(<name>)`` /
  ``repr(<name>)`` / ``<name>.message`` — ``str(exc.args[0])``, ``f"{exc}"``,
  ``exc`` itself, or a text forwarded into a helper's ``**log_fields`` rather than
  written at the log call (``PrivacyService._record_failed_attempt(..., error=...)``:
  the call site passes ``_loggable_error(...)``, but nothing here sees that
  argument). Tracebacks (``exc_info=True``, ``logger.exception(...)``, uvicorn's
  and Celery's own) are no longer a blind spot of the *sink*: since #1796 every
  one is rendered by ``log_privacy.redacted_traceback`` (structlog's
  ``ExceptionRenderer``, the handler filter in ``app.config.logging``), and the
  handler filter also redacts an embedded ``str(exc)``/``repr(exc)`` and masks
  addresses and URL queries in every stdlib line
  (``test_tracebacks_carry_no_personal_data.py``). What that sink rule cannot
  see: a subject key inside a non-domain exception text (``loggable_error``
  without ``user_key=`` does not know the key), and a handler added after
  ``setup_logging`` ran;
* a raw storage key under a keyword not listed above (``path=``, ``file_path=``);
* a logger reached under another name (``self._audit.info(...)``, an inline
  ``structlog.get_logger().info(...)``) or a level method outside ``_LOG_METHODS``;
* ``structlog.contextvars.bind_contextvars(...)``, and a ``bind`` in another
  module whose bound context later lines inherit;
* the side services ``src/inference-service`` and ``src/knowledge-service`` (measured
  on #1781: their findings are model-file paths and ingestion errors, no account
  identity; the knowledge service's ``query=`` free text is out of this guard's reach);
* access-log lines written by uvicorn and nginx themselves (client address, path,
  query string) — not log calls in this tree; redacted at runtime since #1795
  (``uvicorn.access`` filter, nginx ``kp_redacted`` format) and held by
  ``test_logs_carry_no_secrets_runtime.py``, not by this guard;
* an IP under a keyword not matching ``_IP_KEYWORD`` (``host=``, ``client=``), or
  inside an ``address`` that is a *server's* resolved address (``url_safety``:
  the SSRF target a URL resolves to, not a data subject);
* other personal data than account key, address and IP (names, free text).
"""

from __future__ import annotations

import ast
import pathlib
import re
import subprocess

import pytest

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[3]

#: Frozen: an applied migration's class body is pinned by
#: ``test_applied_migration_sources_are_frozen``. Still scanned — a NEW version
#: module is guarded — but a finding in a frozen one is allow-listed with
#: :data:`_FROZEN_MIGRATION`.
_FROZEN_DIR = "app/migrations/versions/"

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
#: A bare conversion of a name to its text — the spelling of "log the exception message".
_TEXT_CONVERSIONS = {"str", "repr"}
#: A keyword that names a client/peer IP address (#1781): ``ip``, ``ip_address``,
#: ``client_ip``, ``remote_addr`` and any ``*_ip``.
_IP_KEYWORD = re.compile(r"(^|_)(ip|ip_address|remote_addr)$")
#: Composite keys that embed the account key by construction (#1830): the Redis
#: notification dedup key (``notif:dedup:<user_key>:…``) and the notification
#: group keys (``care:<user_key>:…``, ``daily_summary:<user_key>:…``). Such a
#: keyword must be a call (a redaction) or a literal — whatever local or
#: parameter carries the value.
_COMPOSITE_KEY_KEYWORD = re.compile(r"(^|_)(dedup_key|group_key)$")

_REDIS_OUTAGE = "a Redis client error names host/port or the command, and the key is a digest — no subject"
_PIL_DECODE = "a Pillow decode error describes the bytes (format, truncation), never who uploaded them"
_FROZEN_MIGRATION = (
    "frozen: an applied migration's class body is pinned by test_applied_migration_sources_are_frozen "
    "(editing it breaks the checksum); the text is an ArangoDB error on the collection it rewrites"
)

#: ``path::enclosing_function::keyword`` -> reason a subject identifier or an
#: exception text may be logged there. Every #1773 identifier site could log the
#: salted reference instead, so none needed an excuse; the entries below are the
#: exception-text sites (#1773 review) whose text was read and found subject-free.
_ALLOWED: dict[str, str] = {
    "app/data_access/arango/erasure_executor.py::ArangoErasureExecutor._abort_quietly::error": (
        "an ArangoDB transaction-abort error names the transaction id, not the plan's subject"
    ),
    "app/data_access/external/device_pairing_throttle.py::RedisDevicePairingThrottleStore.get_failure_state::error": (
        _REDIS_OUTAGE + "; the corrupt-entry branch's decode error names the counter format, not the IP"
    ),
    "app/data_access/external/device_pairing_throttle.py::RedisDevicePairingThrottleStore.record_failure::error": (
        _REDIS_OUTAGE
    ),
    "app/data_access/external/device_pairing_throttle.py::RedisDevicePairingThrottleStore.clear::error": (
        _REDIS_OUTAGE
    ),
    "app/data_access/external/redis_device_pairing.py::RedisDevicePairingCodeStore.consume::error": (
        _REDIS_OUTAGE + "; the corrupt-entry branch's error names a JSON position or a missing field name"
    ),
    "app/data_access/storage/s3_adapter.py::S3StorageAdapter._health_sync::detail": (
        "the health probe touches the bucket, not an object: the text names endpoint/bucket, no account key"
    ),
    "app/domain/engines/oauth_engine.py::OAuthEngine._fetch_github_user_info::error": (
        "an httpx error names the fixed GitHub /user/emails URL and a status; the TypeError is built from a type name"
    ),
    "app/domain/engines/storage/exif_stripper.py::strip_exif::reason": _PIL_DECODE,
    "app/migrations/versions/v0051_rename_cec_key.py::RenameCecKeyMigration._write::error": _FROZEN_MIGRATION,
    "app/domain/engines/storage/thumbnail_generator.py::metadata_keys::reason": _PIL_DECODE,
    "app/domain/services/notification_service.py::NotificationService.send_frost_forecast_notifications::group_key": (
        "the frost-forecast group key is built from the site and the forecast date "
        "(frost-forecast:<site_key>:<date>), never from an account key (#1830 triage)"
    ),
    "app/domain/services/privacy_service.py::PrivacyService.erase_account_by_admin::step_up": (
        "StepUpVerifier.verify returns only how the step-up was confirmed ('password'/'email_code'); the taint "
        "comes from echo_matches(..., target.email) among its arguments, not from the returned label (#1830 triage)"
    ),
    "app/domain/services/privacy_service.py::PrivacyService._run_export_file_cleanup::closed": (
        "fail_open_for_user(user_key, ...) returns the number of exports it closed, an int (#1830 triage)"
    ),
    "app/tasks/auth_tasks.py::dispatch_duplicate_registration_notice::error": (
        "a broker error names the broker connection; the task argument is an opaque key, not in the text"
    ),
}


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


def _raw_exception_text(value: ast.expr) -> str | None:
    """``str(<name>)`` / ``repr(<name>)``: a text the logger receives unredacted, if any."""
    if (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in _TEXT_CONVERSIONS
        and len(value.args) == 1
        and isinstance(value.args[0], ast.Name)
    ):
        return ast.unparse(value)
    return None


def _raw_error_message(value: ast.expr) -> str | None:
    """``<name>.message`` handed over unwrapped (#1796): a ``KamerplanterError``'s message names what it is about.

    ``NotFoundError("User", <key>).message`` is ``"User with key '<key>' not
    found."``. Wrapped in a call (``loggable_error(exc)``, ``loggable_exception_text(exc)``)
    it passes. Also inside ``a or b``, ``a if c else b`` and f-strings.
    """
    if isinstance(value, ast.Attribute) and value.attr == "message":
        return ast.unparse(value)
    if isinstance(value, ast.BoolOp):
        return next((hit for part in value.values if (hit := _raw_error_message(part))), None)
    if isinstance(value, ast.IfExp):
        return _raw_error_message(value.body) or _raw_error_message(value.orelse)
    if isinstance(value, ast.JoinedStr):
        parts = [p.value for p in value.values if isinstance(p, ast.FormattedValue)]
        return next((hit for part in parts if (hit := _raw_error_message(part))), None)
    return None


def _is_raw_ip(keyword: str, value: ast.expr) -> bool:
    """An IP keyword whose value is handed over as-is — not a call (``loggable_ip``), not a literal."""
    return bool(_IP_KEYWORD.search(keyword)) and not isinstance(value, ast.Call | ast.Constant)


def _is_raw_storage_key(keyword: str, value: ast.expr, *, storage_module: bool) -> bool:
    names_a_key = (storage_module and keyword in _STORAGE_MODULE_KEYWORDS) or bool(_STORAGE_KEY_KEYWORD.search(keyword))
    return names_a_key and not isinstance(value, ast.Call | ast.Constant)


#: Calls that reduce a subject identifier to something loggable (#1830): a local
#: assigned from one of these is not tainted by the identifier it was given.
_SUBJECT_REDACTIONS = {
    "log_subject",
    "email_digest",
    "loggable_error",
    "loggable_error_text",
    "_loggable_error",
    "loggable_storage_key",
    "loggable_ip",
    "len",
    "bool",
}


def _call_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _subject_reference(value: ast.expr, tainted: set[str]) -> str | None:
    """The subject identifier (or tainted local) *value* is built from, if any (#1830).

    Wider than :func:`_raw_identifier`: it also looks into the arguments and the
    receiver of a call that is not a redaction (``self._build_dedup_key(user_key, …)``),
    a ``+`` concatenation and a subscript — the ways a key is folded into another
    value before it is logged under a neutral name.
    """
    if hit := _raw_identifier(value):
        return hit
    if isinstance(value, ast.Name):
        return value.id if value.id in tainted else None
    if isinstance(value, ast.Call):
        if _call_name(value.func) in _SUBJECT_REDACTIONS:
            return None
        parts: list[ast.expr] = [*value.args, *(kw.value for kw in value.keywords)]
        if isinstance(value.func, ast.Attribute):
            parts.append(value.func.value)
        return next((hit for part in parts if (hit := _subject_reference(part, tainted))), None)
    if isinstance(value, ast.BoolOp):
        return next((hit for part in value.values if (hit := _subject_reference(part, tainted))), None)
    if isinstance(value, ast.IfExp):
        return _subject_reference(value.body, tainted) or _subject_reference(value.orelse, tainted)
    if isinstance(value, ast.BinOp):
        return _subject_reference(value.left, tainted) or _subject_reference(value.right, tainted)
    if isinstance(value, ast.JoinedStr):
        parts = [p.value for p in value.values if isinstance(p, ast.FormattedValue)]
        return next((hit for part in parts if (hit := _subject_reference(part, tainted))), None)
    if isinstance(value, ast.Subscript | ast.Starred):
        return _subject_reference(value.value, tainted)
    return None


def _tainted_reference(value: ast.expr, tainted: set[str]) -> str | None:
    """A tainted local handed to the logger as-is: bare, in ``a or b``, a conditional or an f-string."""
    if isinstance(value, ast.Name):
        return value.id if value.id in tainted else None
    if isinstance(value, ast.BoolOp):
        return next((hit for part in value.values if (hit := _tainted_reference(part, tainted))), None)
    if isinstance(value, ast.IfExp):
        return _tainted_reference(value.body, tainted) or _tainted_reference(value.orelse, tainted)
    if isinstance(value, ast.JoinedStr):
        parts = [p.value for p in value.values if isinstance(p, ast.FormattedValue)]
        return next((hit for part in parts if (hit := _tainted_reference(part, tainted))), None)
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
    """Locals assigned (directly or transitively) from a subject identifier in this scope — a fixpoint (#1830)."""
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
            if name not in tainted and _subject_reference(rhs, tainted):
                tainted.add(name)
                changed = True
    return tainted


class _LogCallVisitor(ast.NodeVisitor):
    """Walks one module, tracking the enclosing function of every log call and its tainted locals."""

    def __init__(self, rel: str, allowed: dict[str, str]) -> None:
        self.rel = rel
        self.allowed = allowed
        self.storage_module = "/storage/" in rel
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

    def _check(self, node: ast.Call) -> None:
        enclosing = ".".join(self.scope) or "<module>"
        where = f"{self.rel}:{node.lineno} ({enclosing})"
        tainted = self.taint[-1] if self.taint else set()
        for arg in node.args:
            if hit := _raw_identifier(arg):
                self.findings.append(f"{where}: positional {hit}")
            elif hit := _tainted_reference(arg, tainted):
                self.findings.append(f"{where}: positional {hit} (a local built from a subject identifier)")
            elif hit := _raw_exception_text(arg) or _raw_error_message(arg):
                self.findings.append(f"{where}: positional {hit} (unredacted exception text)")
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
            elif hit := _tainted_reference(kw.value, tainted):
                self.findings.append(f"{where}: {kw.arg}={hit} (a local built from a subject identifier, #1830)")
            elif _COMPOSITE_KEY_KEYWORD.search(kw.arg) and not isinstance(kw.value, ast.Call | ast.Constant):
                self.findings.append(f"{where}: {kw.arg}= (a composite key that embeds the account key, #1830)")
            elif _is_raw_ip(kw.arg, kw.value):
                self.findings.append(f"{where}: {kw.arg}= (raw IP address; log ip_prefix=loggable_ip(...))")
            elif _is_raw_storage_key(kw.arg, kw.value, storage_module=self.storage_module):
                self.findings.append(f"{where}: {kw.arg}= (raw storage key; log it through loggable_storage_key)")
            elif hit := _raw_exception_text(kw.value):
                self.findings.append(
                    f"{where}: {kw.arg}={hit} (unredacted exception text; log error_type= or a redaction call)"
                )
            elif hit := _raw_error_message(kw.value):
                self.findings.append(
                    f"{where}: {kw.arg}={hit} (unredacted error message; log error_code= or loggable_error(exc))"
                )


def _scan_source(source: str, rel: str, allowed: dict[str, str] | None = None) -> _LogCallVisitor:
    visitor = _LogCallVisitor(rel, _ALLOWED if allowed is None else allowed)
    visitor.visit(ast.parse(source))
    return visitor


def _findings_in_source(source: str, rel: str, allowed: dict[str, str] | None = None) -> list[str]:
    """THE detector: every log call in *source* (a module at *rel*) that names a subject."""
    return _scan_source(source, rel, allowed).findings


def _guarded_modules() -> list[pathlib.Path]:
    tracked = subprocess.run(
        ["git", "ls-files", "app", "scripts"], cwd=BACKEND_ROOT, check=True, capture_output=True, text=True
    ).stdout.split()
    return [BACKEND_ROOT / rel for rel in sorted(tracked) if rel.endswith(".py")]


def _rel(path: pathlib.Path) -> str:
    return path.relative_to(BACKEND_ROOT).as_posix()


def _surface_scans() -> list[_LogCallVisitor]:
    return [_scan_source(path.read_text(encoding="utf-8"), _rel(path)) for path in _guarded_modules()]


def test_selector_reaches_the_surface() -> None:
    """The selector must find the modules #1773 and #1781 name — an empty population is green over nothing."""
    rels = {_rel(p) for p in _guarded_modules()}
    names = {p.name for p in _guarded_modules()}
    assert any(rel.startswith(_FROZEN_DIR) for rel in rels), "the frozen migration versions left the scan"
    assert "app/migrations/seed_auth.py" in rels, "the editable migration seeds left the scan"
    for expected in (
        # #1781: modules off the privacy surface that name subjects all the same.
        "notification_service.py",
        "tenant_service.py",
        "notification_engine.py",
        "openweathermap_weather_adapter.py",
        "privacy_service.py",
        "data_subject_service.py",
        "user_service.py",
        "auth_service.py",
        "retention_tasks.py",
        "s3_adapter.py",
        "local_fs_adapter.py",
        "redis_device_pairing.py",
        "smtp_email_adapter.py",
        "console_email_adapter.py",
    ):
        assert expected in names, f"selector lost {expected}"


def test_the_scan_sees_log_calls() -> None:
    """A detector that recognised no log call would be green over nothing."""
    sites = {site for scan in _surface_scans() for site in scan.sites}
    assert len(sites) > 100, f"only {len(sites)} log-call keyword sites seen on the surface"


def test_no_log_call_names_a_data_subject() -> None:
    problems = [finding for scan in _surface_scans() for finding in scan.findings]
    assert not problems, (
        "log calls hand a data subject's account key, address, IP or an unredacted exception text "
        "to the logger (#1773, #1781). Log subject=log_subject(user_key), email_digest(...), "
        "ip_prefix=loggable_ip(...), error=loggable_error(exc) (app.common.log_privacy), "
        "loggable_storage_key(...) or error_type=type(exc).__name__ "
        "instead:\n  " + "\n  ".join(problems)
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
        (_SERVICE, "logger.error('e', error=str(exc))", True),
        (_SERVICE, "logger.warning('e', reason=str(err), error_type=type(err).__name__)", True),
        (_SERVICE, "logger.error('e', detail=repr(exc))", True),
        (_SERVICE, "logger.error('failed: %s', str(exc))", True),
        (_SERVICE, "log('e', error=str(exc))", True),
        (_SERVICE, "logger.error('e', error=self._loggable_error(exc, user_key))", False),
        (_SERVICE, "logger.error('e', error=loggable_error_text(str(exc), user_key, salt))", False),
        (_SERVICE, "logger.error('e', error_type=type(exc).__name__)", False),
        (_SERVICE, "logger.info('e', count=str(n_items))", True),
        (_SERVICE, "logger.error('e', error=loggable_error(exc))", False),
        (_SERVICE, "logger.error('e', error=loggable_error(exc, user_key=user_key))", False),
        (_SERVICE, "logger.info('e', subject=log_subject(user_key))", False),
        (_SERVICE, "logger.info('e', subject=log_subject(user.key))", False),
        (_SERVICE, "logger.info('pairing', ip_address=ip_address)", True),
        (_SERVICE, "logger.info('pairing', client_ip=request.client.host)", True),
        (_SERVICE, "logger.info('pairing', source_ip=ip)", True),
        (_SERVICE, "logger.info('pairing', remote_addr=addr)", True),
        (_SERVICE, "logger.info('pairing', ip_prefix=loggable_ip(ip_address))", False),
        (_SERVICE, "logger.info('pairing', ip_address=loggable_ip(ip_address))", False),
        (_SERVICE, "logger.info('probe', skip=skip)", False),
        (_SERVICE, "logger.warning('e', message=exc.message)", True),
        (_SERVICE, "logger.warning('e', reason=exc.message)", True),
        (_SERVICE, "logger.warning('e', reason=exc.message or 'unknown')", True),
        (_SERVICE, "logger.warning('e', reason=a if c else err.message)", True),
        (_SERVICE, "logger.warning(f'failed: {exc.message}')", True),
        (_SERVICE, "logger.warning('failed: %s', exc.message)", True),
        (_SERVICE, "logger.warning('e', reason=loggable_error(exc))", False),
        (_SERVICE, "logger.warning('e', reason=loggable_error(exc.message))", False),
        (_SERVICE, "logger.warning('e', error_code=exc.error_code)", False),
        (_SERVICE, "logger.warning('e', message_count=len(messages))", False),
        (_SERVICE, "k = self._build_dedup_key(user_key, t, g)\nlog.info('dedup', dedup_key=k)", True),
        (_SERVICE, "k = self._build_dedup_key(user_key, t, g)\nlog.info('dedup', key=k)", True),
        (_SERVICE, "k = f'care:{user_key}:x'\nkk = k + ':y'\nlogger.info('e', key=f'{kk}')", True),
        (_SERVICE, "k = f'care:{user.key}'\nlogger.info('e %s', k)", True),
        (_SERVICE, "k = log_subject(user_key)\nlogger.info('e', who=k)", False),
        (_SERVICE, "n = repo.count(user_key)\nlogger.info('e', n_count=len(items))", False),
        (_SERVICE, "logger.warning('e', group_key=group_key)", True),
        (_SERVICE, "logger.warning('e', dedup_key=self._key)", True),
        (_SERVICE, "logger.warning('e', group_kind=_group_kind(group_key))", False),
        ("app/data_access/external/smtp_email_adapter.py", "logger.info('email_sent', to=to_email)", True),
        (
            "app/data_access/external/smtp_email_adapter.py",
            "logger.info('email_sent', to_sha256=email_digest(to_email))",
            False,
        ),
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
