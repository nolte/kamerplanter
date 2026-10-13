"""Optional Sentry-protocol error tracking, shared verbatim by every Python service.

Governing contract: ``spec/project/error-tracking/`` in ``nolte/claude-shared``.
GlitchTip is the reference profile; nothing here binds to it. The SDK speaks the
Sentry protocol, so the backend is swappable by changing ``SENTRY_DSN`` alone.

**The optionality contract is the load-bearing property of this module.** With no
DSN configured the SDK is never initialised, no network call happens, and the
process behaves exactly as it did before this module existed. That is what makes
it safe to call unconditionally at process entry in every deployment, including
local checkouts, the test suite, and CI — none of which set a DSN.

Why this lives in ``src/libs`` and is copied rather than imported: the three
Python services are independent build contexts with their own dependency sets
(the same reason ``kp_vectordb`` exists). The PII-scrubbing rules below are
exactly the kind of code that must never diverge between services — a service
that scrubs one header fewer than its siblings leaks through the weakest link —
so the copies are byte-identical and guarded by a per-service drift test. Edit
this file, then run ``python src/libs/kp_errortracking/sync.py``; never edit a
copy.
"""

from __future__ import annotations

import contextlib
import io
import logging
import re
import sys
import threading
import traceback
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from os import environ
from types import TracebackType
from typing import Any
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

#: The closed stage vocabulary every component tags its events with. Alert rules
#: and release gates filter on these exact strings, so they MUST be identical
#: across backend, worker, frontend and the two microservices.
ENVIRONMENTS = ("development", "e2e", "staging", "production")

#: Request headers that may be forwarded with an event. Allow-list rather than
#: deny-list: a header added by a future proxy or middleware is withheld by
#: default instead of leaking until someone remembers to blocklist it.
_ALLOWED_HEADERS = frozenset(
    {
        "accept",
        "accept-encoding",
        "accept-language",
        "content-length",
        "content-type",
        "user-agent",
        "x-request-id",
    }
)

#: Substrings marking a value as a credential or personal datum wherever it
#: appears by name — query parameters, stack-frame locals, ``extra`` context.
#: Matched case-insensitively against the *name*, never the value, so no secret
#: has to be recognised by shape.
_SENSITIVE_NAME_PARTS = (
    "authorization",
    "api_key",
    "apikey",
    "cookie",
    "credential",
    "email",
    "passwd",
    "password",
    "secret",
    "session",
    "token",
)

_REDACTED = "[redacted]"

#: Keys under which the SDK's HTTP integrations (httpx, stdlib) put the raw query
#: string and fragment of every outbound request into a breadcrumb — the
#: OpenWeatherMap ``appid`` and a site's coordinates. A bare query string has no
#: URL shape a text redactor could recognise, so the value goes wholesale.
_RAW_URL_PART_KEYS = frozenset({"http.query", "http.fragment"})

#: What a service hands :func:`init_error_tracking` to redact free text — an
#: exception's message, a log record's message and arguments, a breadcrumb.
#: Called with the text and the exceptions the event was captured for (so the
#: service can replace *their* texts, not only recognise shapes); returns what
#: may leave the process. The rules live in the service because they are the
#: service's log-redaction rules: an event text is the same text as the log line.
TextRedactor = Callable[[str, Sequence[BaseException]], str]

#: Set by :func:`init_error_tracking`. ``None`` means the service declared that
#: it has no text redaction; structure scrubbing (names, headers, bodies) still runs.
_text_redactor: TextRedactor | None = None

#: What a service hands :func:`init_error_tracking` to reduce a raw request path
#: to what may leave the process (the backend passes ``loggable_path``: every
#: segment that is not a literal of one of its routes becomes ``{}``). Used only
#: where the framework gave no route pattern for the request (#1925).
PathRedactor = Callable[[str], str]

#: Set by :func:`init_error_tracking`. ``None``: the service has no route table
#: to consult, and :func:`_redact_path` keeps only ``api`` and ``v<digits>``.
_path_redactor: PathRedactor | None = None

#: What a service hands :func:`init_error_tracking` to name *who* an event is
#: about: called at capture time, in the context of the code that failed, it
#: returns the event's ``user`` block — ``{"id": …, "tenant": …}``, pseudonyms
#: the service may send — or ``None`` for none. The service decides there
#: whether the person agreed to be named (the backend asks the request's
#: ``error_tracking`` consent, #2136). Only ``id`` and ``tenant`` string values
#: survive; whatever else it returns is dropped.
UserContext = Callable[[], Mapping[str, Any] | None]

#: Set by :func:`init_error_tracking`. ``None``: no event carries a ``user`` block.
_user_context: UserContext | None = None
#: The keys a ``user`` block may carry, and the longest value kept.
_USER_KEYS = ("id", "tenant")
_MAX_USER_VALUE = 64
_PATH_SAFE_SEGMENT = re.compile(r"api|v\d+")
#: ``transaction_info.source`` values for which the SDK's ``transaction`` is a
#: route *template* (``/t/{tenant_slug}/attachments/{key}``), not the raw path.
_PATTERN_SOURCES = frozenset({"route", "component"})
#: Nesting beyond this is replaced wholesale — the scrubber must not recurse
#: without bound over a value an attacker (or a cyclic structure) shaped.
_MAX_DEPTH = 8


def _is_sensitive_name(name: str) -> bool:
    lowered = name.lower()
    return any(part in lowered for part in _SENSITIVE_NAME_PARTS)


def _redact_mapping(mapping: MutableMapping[str, Any], depth: int = 0) -> None:
    """Replace values under sensitive keys in place, keeping the keys visible.

    The key stays so a reader can tell *that* a credential was present at the
    call site — useful when triaging — while the value never leaves the process.
    Nested mappings and lists are walked too: an ``Authorization`` header sits
    inside a ``headers`` dict, not at the top level.
    """
    for key in list(mapping):
        if _is_sensitive_name(str(key)) or str(key) in _RAW_URL_PART_KEYS or depth >= _MAX_DEPTH:
            mapping[key] = _REDACTED
        else:
            _redact_nested(mapping[key], depth + 1)


def _redact_nested(value: Any, depth: int) -> None:
    if isinstance(value, dict):
        _redact_mapping(value, depth)
    elif isinstance(value, list) and depth < _MAX_DEPTH:
        for item in value:
            _redact_nested(item, depth + 1)


#: What :func:`shape_text_redactor` recognises, by shape alone (no key, no salt, no route
#: table — a service that has none of those passes this instead of ``None``, #1926).
#: Every quantifier is bounded and every scan starts at a run boundary, so a hostile text
#: of any shape is masked in linear time.
_URL_USERINFO = re.compile(r"(?<![A-Za-z0-9+.-])([A-Za-z][A-Za-z0-9+.-]{0,31}://)[^\s/?#'\"\\]{0,512}@")
_HTTP_URL_TAIL = re.compile(
    r"(?<![A-Za-z0-9+.:/-])(https?://[^\s'\"\\?#]{0,2048})[?#][^\s'\"\\]{0,2048}", re.IGNORECASE
)
_BARE_QUERY = re.compile(
    r"(with url: /[^\s?'\"\\]{0,2048}|\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) /[^\s?'\"\\]{0,2048})"
    r"\?[^\s'\"\\]{1,2048}"
)
_PATH_CREDENTIAL_SHAPES = (
    re.compile(r"(/bot)\d{1,32}(?::|%3[Aa])[\w-]{1,512}"),
    re.compile(r"(/webhooks/)\d{1,32}/[\w-]{1,512}"),
    re.compile(r"(/services/)T\w{1,64}/B\w{1,64}/\w{1,512}"),
)
_TOKEN_SEGMENT = re.compile(r"(?<=/)([A-Za-z0-9_:\-]{32,})((?:\.[A-Za-z0-9_:\-]{1,512}){0,8})")
_HEX_RUN = re.compile(r"[0-9A-Fa-f]+")
_EMAIL = re.compile(r"[\w.!$%*+^`{|}~-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63})+")


def _looks_like_a_token(segment: str) -> bool:
    """A long path segment that is a generated secret rather than a name (letters and digits, or hex)."""
    has_digit = any(char.isdigit() for char in segment)
    if has_digit and any(char.isupper() for char in segment) and any(char.islower() for char in segment):
        return True
    if has_digit and _HEX_RUN.fullmatch(segment) is not None and any(char.isalpha() for char in segment):
        return True
    if not (segment.isascii() and segment.isalnum()):
        return False
    return has_digit or not segment.islower()


def _mask_token_chain(match: re.Match[str]) -> str:
    return _REDACTED if _looks_like_a_token(match.group(1)) else match.group(0)


def shape_text_redactor(text: str, exceptions: Sequence[BaseException] = ()) -> str:
    """*text* with every URL userinfo, URL query and fragment, path credential and e-mail address masked.

    The default :data:`TextRedactor` of a service that has no redaction of its own
    (``knowledge-service``, ``inference-service``, #1926). It recognises *shapes* only:
    ``scheme://user:pw@host`` loses the userinfo, an ``http(s)`` URL its query and
    fragment (where API keys and coordinates live), a bare request target in an HTTP
    library's text its query, the named credential-in-path shapes (Telegram, Discord,
    Slack) and any other long token-shaped path segment (with its dotted tail) become
    ``[redacted]``, and an e-mail address becomes ``<email>``. What it cannot do is hide
    free text — a question a person typed, a name — because that has no shape; the
    *exceptions* argument is accepted for the :data:`TextRedactor` signature and not
    used. The backend registers its own, keyed redaction instead.
    """
    text = _URL_USERINFO.sub(r"\1[redacted]@", text)
    text = _HTTP_URL_TAIL.sub(r"\1?[redacted]", text)
    text = _BARE_QUERY.sub(r"\1?[redacted]", text)
    for pattern in _PATH_CREDENTIAL_SHAPES:
        text = pattern.sub(rf"\1{_REDACTED}", text)
    text = _TOKEN_SEGMENT.sub(_mask_token_chain, text)
    return _EMAIL.sub("<email>", text)


def _redact_text(text: str, exceptions: Sequence[BaseException]) -> str:
    """*text* through the service's redactor; fails closed to the placeholder."""
    if _text_redactor is None:
        return text
    try:
        return _text_redactor(text, exceptions)
    except Exception:
        return _REDACTED


def _redact_strings(value: Any, exceptions: Sequence[BaseException], depth: int = 0) -> Any:
    """*value* with every string in it — at any depth — run through the text redactor."""
    if isinstance(value, str):
        return _redact_text(value, exceptions)
    if depth >= _MAX_DEPTH:
        return _REDACTED if isinstance(value, (dict, list, tuple)) else value
    if isinstance(value, dict):
        # Keys too (#1926): a dict keyed by a value (``{<address>: …}``) names it as plainly as a value does.
        return {
            (_redact_text(key, exceptions) if isinstance(key, str) else key): _redact_strings(
                item, exceptions, depth + 1
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact_strings(item, exceptions, depth + 1) for item in value]
    return value


def _exceptions_of(hint: Mapping[str, Any] | None) -> list[BaseException]:
    """The exception the SDK captured the event for, from the hint's ``exc_info``."""
    exc_info = (hint or {}).get("exc_info")
    if isinstance(exc_info, BaseException):
        return [exc_info]
    if isinstance(exc_info, tuple) and len(exc_info) > 1 and isinstance(exc_info[1], BaseException):
        return [exc_info[1]]
    return []


def _scrub_texts(event: MutableMapping[str, Any], exceptions: Sequence[BaseException]) -> None:
    """Redact the free text of an event: exception messages, the log entry, the message.

    ``exception.values[].value`` is ``str(exc)`` — a domain error names the
    record it is about, a connection error the URL it dialled. ``logentry`` is a
    log record's format string, its arguments and the formatted line; ``extra``,
    ``tags`` and ``contexts`` are walked with their keys. Without a redactor these
    are left as the SDK built them.
    """
    if _text_redactor is None:
        return
    for exception in (event.get("exception") or {}).get("values") or []:
        if isinstance(exception, dict) and isinstance(exception.get("value"), str):
            exception["value"] = _redact_text(exception["value"], exceptions)
    logentry = event.get("logentry")
    if isinstance(logentry, dict):
        for field in ("message", "formatted", "params"):
            if logentry.get(field) is not None:
                logentry[field] = _redact_strings(logentry[field], exceptions)
    if isinstance(event.get("message"), str):
        event["message"] = _redact_text(event["message"], exceptions)
    for section in ("extra", "tags", "contexts"):
        value = event.get(section)
        if isinstance(value, dict):
            event[section] = _redact_strings(value, exceptions)


def _redact_path(path: str) -> str:
    """*path* with everything that is not a route literal replaced; fails closed."""
    redactor = _path_redactor
    if redactor is not None:
        try:
            return redactor(path).partition("?")[0]
        except Exception:
            pass
    target = path.partition("?")[0]
    return "/".join(
        segment if not segment or _PATH_SAFE_SEGMENT.fullmatch(segment) else "{}" for segment in target.split("/")
    )


def _scrub_route(event: MutableMapping[str, Any]) -> None:
    """Reduce the event's request URL and transaction name to the route pattern (#1925).

    The SDK's ASGI integration fills ``request.url`` from the raw request target
    — the attachment download token (which *is* the authorisation) and a tenant
    slug derived from a person's display name — while the transaction name is
    already the route template when the framework matched one. So: a framework
    pattern is used for both; without one (404, an error before routing) the
    service's path redactor reduces them. Scheme, host and method stay; the
    query string and fragment never do.
    """
    transaction = event.get("transaction")
    source = (event.get("transaction_info") or {}).get("source")
    pattern: str | None = None
    if isinstance(transaction, str) and source in _PATTERN_SOURCES and transaction.startswith("/"):
        pattern = transaction
    elif isinstance(transaction, str) and (source == "url" or transaction.startswith("/") or "://" in transaction):
        # No framework pattern: the SDK named the transaction after the request
        # target — a bare path, or (uvicorn sets ``server``) an absolute URL. A
        # task name (``source=task``, the worker) is not a request target: kept.
        path = _path_of(transaction)
        pattern = event["transaction"] = path if path is not None else _REDACTED
        event["transaction_info"] = {**(event.get("transaction_info") or {}), "source": "route"}
    request = event.get("request")
    if isinstance(request, dict) and isinstance(request.get("url"), str):
        raw = request["url"]
        try:
            parts = urlsplit(raw)
            origin = f"{parts.scheme}://{_host_of(parts)}" if parts.scheme and parts.hostname else ""
        except ValueError:
            request["url"] = _REDACTED
            return
        # Without a scheme the string is only a path (``//slug/x`` is not a host).
        target = parts.path if origin else raw.partition("?")[0].partition("#")[0]
        request["url"] = origin + (pattern if pattern is not None else _redact_path(target))


def _host_of(parts: Any) -> str:
    """``host[:port]`` of a split URL: no userinfo, IPv6 literals re-bracketed."""
    host = parts.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    return f"{host}:{parts.port}" if parts.port else host


def _path_of(target: str) -> str | None:
    """The redacted path of a request target — a bare path or an absolute URL; ``None`` if unparsable."""
    try:
        parts = urlsplit(target)
        raw = parts.path if parts.scheme and parts.hostname else target.partition("?")[0].partition("#")[0]
    except ValueError:
        return None
    return _redact_path(raw)


def _scrub_request(request: MutableMapping[str, Any]) -> None:
    # Bodies and cookies are dropped wholesale: a request body is the single
    # richest source of personal data in this application (plant notes, harvest
    # records, member invitations), and no triage need justifies shipping it.
    request.pop("data", None)
    request.pop("cookies", None)

    headers = request.get("headers")
    if isinstance(headers, dict):
        request["headers"] = {k: v for k, v in headers.items() if str(k).lower() in _ALLOWED_HEADERS}

    # A query string can carry a token even when the header allow-list held; the
    # URL is kept because the route is the most valuable grouping signal there is.
    query = request.get("query_string")
    if isinstance(query, str) and query:
        request["query_string"] = _scrub_query_string(query)


def _scrub_query_string(query: str) -> str:
    """Every value withheld, every name kept: a search term or a coordinate is as personal as a token."""
    parts = []
    for pair in query.split("&"):
        name, sep, _value = pair.partition("=")
        parts.append(f"{name}={_REDACTED}" if sep else pair)
    return "&".join(parts)


def _scrub_frames(event: MutableMapping[str, Any]) -> None:
    """Redact sensitive stack-frame locals.

    :func:`init_error_tracking` switches frame locals off
    (``include_local_variables=False``): a local's *name* does not say what it
    holds — ``url``, ``html``, ``payload``, ``msg`` in a mail adapter hold the
    reset link and the step-up code. This stays as the second line for an event
    that carries locals anyway (another SDK default, a re-enabled option):
    sensitive names are redacted at any depth, every remaining string goes
    through the text redactor.
    """
    for exception in (event.get("exception") or {}).get("values") or []:
        for frame in (exception.get("stacktrace") or {}).get("frames") or []:
            frame_vars = frame.get("vars")
            if isinstance(frame_vars, dict):
                _redact_mapping(frame_vars)
                frame["vars"] = _redact_strings(frame_vars, ())


_TRACEBACK_WITHHELD = "<exception text withheld>"
_HOOK_MARK = "_kp_redacting"
_MUTE_LOCK = threading.RLock()


def _render_uncaught(exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> str:
    """A traceback whose text went through the text redactor; fails closed to the class name."""
    name = getattr(exc_type, "__name__", None) or type(exc).__name__
    if exc is None:
        return name
    try:
        rendered = "".join(traceback.format_exception(exc_type or type(exc), exc, tb))
        return _redact_text(rendered, [exc]).rstrip("\n")
    except Exception:
        return f"{name}: {_TRACEBACK_WITHHELD}"


def _write_stderr(text: str) -> None:
    stream = sys.stderr or sys.__stderr__
    if stream is None:
        return
    # A closed or broken stderr at crash time must not raise out of the hook.
    with contextlib.suppress(Exception):
        stream.write(text)
        stream.flush()


def _call_muted(hook: Callable[..., object], *args: object) -> None:
    """Run a hook somebody else installed without letting it print.

    The error tracker's hook (the Sentry SDK wraps ``sys.excepthook``) captures the
    exception — through its own scrubbing — and then calls the interpreter's default
    hook, which prints the raw traceback. The capture must still happen, the print not.
    """
    with _MUTE_LOCK:
        saved = sys.stderr
        sys.stderr = io.StringIO()
        try:
            hook(*args)
        except BaseException:  # noqa: BLE001, S110 - the redacted print follows; re-raising would print raw text
            pass
        finally:
            sys.stderr = saved


def install_uncaught_exception_redaction() -> None:
    """Print an exception that never becomes a log record through the text redactor (#1926). Idempotent.

    ``sys.excepthook`` (an exception escaping the process entry), ``threading.excepthook``
    (an uncaught exception in a thread) and ``sys.unraisablehook`` (an exception in a
    finaliser) print the raw traceback to stderr, past every logging filter. Each is
    replaced by one that prints the same traceback with the text redactor applied to
    it. A hook installed before this call (the SDK's) still runs — muted, so it captures
    without printing; call this *after* :func:`init_error_tracking`. With no text
    redactor registered the text is printed as it is.
    """
    previous_except = sys.excepthook
    if not getattr(previous_except, _HOOK_MARK, False):

        def excepthook(exc_type: type[BaseException], exc: BaseException, tb: TracebackType | None) -> None:
            if previous_except is not sys.__excepthook__:
                _call_muted(previous_except, exc_type, exc, tb)
            _write_stderr(_render_uncaught(exc_type, exc, tb or exc.__traceback__) + "\n")

        setattr(excepthook, _HOOK_MARK, True)
        sys.excepthook = excepthook

    previous_thread = threading.excepthook
    if not getattr(previous_thread, _HOOK_MARK, False):

        def thread_hook(args: threading.ExceptHookArgs) -> None:
            if previous_thread is not threading.__excepthook__:
                _call_muted(previous_thread, args)
            if args.exc_type is SystemExit:
                return
            name = args.thread.name if args.thread is not None else threading.get_ident()
            body = _render_uncaught(args.exc_type, args.exc_value, args.exc_traceback)
            _write_stderr(f"Exception in thread {name}:\n{body}\n")

        setattr(thread_hook, _HOOK_MARK, True)
        threading.excepthook = thread_hook

    previous_unraisable = sys.unraisablehook
    if not getattr(previous_unraisable, _HOOK_MARK, False):

        def unraisable_hook(unraisable: Any) -> None:
            if previous_unraisable is not sys.__unraisablehook__:
                _call_muted(previous_unraisable, unraisable)
            # The default hook prints ``repr(object)``, a runtime value: only what it is called.
            target = unraisable.object
            try:
                where = getattr(target, "__qualname__", None) or type(target).__name__
            except Exception:
                where = type(target).__name__
            label = unraisable.err_msg or "Exception ignored in"
            body = _render_uncaught(unraisable.exc_type, unraisable.exc_value, unraisable.exc_traceback)
            _write_stderr(f"{label}: {where}\n{body}\n")

        setattr(unraisable_hook, _HOOK_MARK, True)
        sys.unraisablehook = unraisable_hook


def _event_user() -> dict[str, str] | None:
    """The ``user`` block the service's :data:`UserContext` names; fails closed to none."""
    provider = _user_context
    if provider is None:
        return None
    try:
        named = provider()
    except Exception:
        return None
    if not isinstance(named, Mapping):
        return None
    user: dict[str, str] = {}
    for key in _USER_KEYS:
        value = named.get(key)
        if isinstance(value, str) and 0 < len(value) <= _MAX_USER_VALUE:
            user[key] = value
    return user or None


def scrub_event(event: MutableMapping[str, Any], _hint: Mapping[str, Any] | None = None) -> MutableMapping[str, Any]:
    """``before_send`` hook: strip personal data before the event leaves the process.

    This is the error-event instance of the locked emission-boundary redaction
    pillar in ``spec/project/monitoring-observability/``. It runs on every event
    in every environment — including the developer's own dev project — so the
    hook that protects production is the one that has been exercised all along,
    rather than untested PII protection switched on at go-live.

    Structure first (request, user, names), then free text (:func:`_scrub_texts`)
    through the redactor the service registered at init.
    """
    request = event.get("request")
    if isinstance(request, dict):
        _scrub_request(request)

    # The ``user`` block comes from the service's :data:`UserContext` and from
    # nothing else (#2129). Whatever the SDK or an integration put there — an
    # address, a username, a raw account key handed to ``set_user`` — is dropped:
    # the join key that makes an issue actionable is the service's pseudonym, and
    # the service alone knows whether the person agreed to be named (#2136).
    event.pop("user", None)
    user = _event_user()
    if user is not None:
        event["user"] = user

    for section in ("extra", "tags", "contexts"):
        value = event.get(section)
        if isinstance(value, dict):
            _redact_mapping(value)

    _scrub_route(event)
    _scrub_frames(event)
    _scrub_texts(event, _exceptions_of(_hint))
    return event


def scrub_breadcrumb(
    crumb: MutableMapping[str, Any], _hint: Mapping[str, Any] | None = None
) -> MutableMapping[str, Any]:
    """``before_breadcrumb`` hook: the same rules for the trail leading to the event.

    Breadcrumbs are collected before anyone knows an error will happen, so they
    are the easiest place for a credential to arrive unnoticed.
    """
    data = crumb.get("data")
    if isinstance(data, dict):
        _redact_mapping(data)
        crumb["data"] = _redact_strings(data, ())
    if isinstance(crumb.get("message"), str):
        # A log line, or an outbound request's URL: a webhook URL carries its
        # token in the path, which no name-based rule sees.
        crumb["message"] = _redact_text(crumb["message"], ())
    return crumb


def _resolve_sample_rate(raw: str) -> float:
    """Parse ``SENTRY_SAMPLE_RATE``, falling back to full capture on nonsense.

    Sampling is a *decision* per the spec, not an accident; the portfolio default
    for low-traffic services is 1.0. An unparseable value must not silently drop
    events, so it falls back to the documented default and says so.
    """
    try:
        rate = float(raw)
    except ValueError:
        logger.warning("error_tracking: SENTRY_SAMPLE_RATE=%r is not a number, using 1.0", raw)
        return 1.0
    if not 0.0 <= rate <= 1.0:
        logger.warning("error_tracking: SENTRY_SAMPLE_RATE=%r is outside 0..1, using 1.0", raw)
        return 1.0
    return rate


def resolve_release(component: str, version: str) -> str:
    """Return the release identifier for this build.

    ``SENTRY_RELEASE`` is what a deployment sets from the image tag or commit
    SHA and is always preferred. The ``component@version`` fallback keeps events
    attributable in a checkout or compose run where nothing set it — an
    unattributable release is what makes regression detection impossible, so a
    coarse identifier beats none.
    """
    return environ.get("SENTRY_RELEASE", "").strip() or f"{component}@{version}"


def init_error_tracking(
    *,
    component: str,
    release: str,
    redact_text: TextRedactor | None,
    redact_path: PathRedactor | None = None,
    user_context: UserContext | None = None,
) -> bool:
    """Initialise the Sentry-compatible SDK if a DSN is configured.

    Args:
        component: Which in-house component this process is (``backend``,
            ``worker``, ``inference-service``, ``knowledge-service``). Set as a
            tag so one tracker project can still be split by component.
        release: Release identifier for this build — the release tag or commit
            SHA. Without it, regression detection and "which deploy introduced
            this" attribution are impossible.
        redact_text: The service's free-text redaction (see :data:`TextRedactor`),
            applied to exception messages, log entries and breadcrumbs. Required
            and without a default on purpose: every call site states whether it
            has one, so a second process entry cannot silently go without.
            ``None`` declares that the service has no text redaction.
        redact_path: The service's request-path redaction (see
            :data:`PathRedactor`), used for the event's request URL and
            transaction name when the framework provided no route pattern.
            ``None`` keeps only ``api`` and ``v<digits>`` segments.
        user_context: The service's :data:`UserContext` — who an event is about,
            as pseudonyms, decided at capture time. ``None``: events carry no
            ``user`` block at all.

    Returns:
        ``True`` when the SDK was initialised, ``False`` when it stayed a no-op.
        Callers ignore this; it exists so the behaviour is directly testable.
    """
    global _text_redactor, _path_redactor, _user_context
    _text_redactor = redact_text
    _path_redactor = redact_path
    _user_context = user_context

    dsn = environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False

    try:
        import sentry_sdk
    except ImportError:  # pragma: no cover - the dependency is declared, not optional
        logger.warning("error_tracking: SENTRY_DSN is set but sentry-sdk is not installed")
        return False

    env = environ.get("SENTRY_ENVIRONMENT", "development").strip() or "development"
    if env not in ENVIRONMENTS:
        # Deliberately not fatal, and deliberately not silently corrected. A
        # typo'd stage that refused to initialise would look exactly like a
        # healthy quiet service; passing it through puts the wrong value in the
        # tracker's environment list, where an operator sees it.
        logger.warning(
            "error_tracking: SENTRY_ENVIRONMENT=%r is outside the declared vocabulary %s; "
            "alert rules filtering on those values will not match this component",
            env,
            ", ".join(ENVIRONMENTS),
        )

    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        release=release,
        # Never the SDK's own PII defaults: no client IP, no cookies, no bodies.
        send_default_pii=False,
        # A decision, not the SDK default (True): a frame local's name does not
        # say whether it holds a reset link, a mail body or a request payload,
        # so no name-based scrubber can clear locals for leaving the process.
        include_local_variables=False,
        sample_rate=_resolve_sample_rate(environ.get("SENTRY_SAMPLE_RATE", "1.0")),
        # Performance tracing stays advisory per the observability spec and is
        # off until someone decides to adopt it; leaving it at the SDK default
        # would be an accident, not a decision.
        traces_sample_rate=0.0,
        before_send=scrub_event,
        before_breadcrumb=scrub_breadcrumb,
    )
    sentry_sdk.set_tag("component", component)
    logger.info("error_tracking: enabled for %s (environment=%s, release=%s)", component, env, release)
    return True
