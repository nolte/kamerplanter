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

import logging
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from os import environ
from typing import Any

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
        if _is_sensitive_name(str(key)) or depth >= _MAX_DEPTH:
            mapping[key] = _REDACTED
        else:
            _redact_nested(mapping[key], depth + 1)


def _redact_nested(value: Any, depth: int) -> None:
    if isinstance(value, dict):
        _redact_mapping(value, depth)
    elif isinstance(value, list) and depth < _MAX_DEPTH:
        for item in value:
            _redact_nested(item, depth + 1)


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
        return {key: _redact_strings(item, exceptions, depth + 1) for key, item in value.items()}
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
    log record's format string, its arguments and the formatted line. Without a
    redactor these are left as the SDK built them.
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
    extra = event.get("extra")
    if isinstance(extra, dict):
        event["extra"] = _redact_strings(extra, exceptions)


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
    parts = []
    for pair in query.split("&"):
        name, sep, _value = pair.partition("=")
        if sep and _is_sensitive_name(name):
            parts.append(f"{name}={_REDACTED}")
        else:
            parts.append(pair)
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

    user = event.get("user")
    if isinstance(user, dict):
        # A tenant/user id is the join key that makes an issue actionable; the
        # attributes that identify the human are not.
        event["user"] = {k: v for k, v in user.items() if k in ("id", "tenant")}

    for section in ("extra", "tags", "contexts"):
        value = event.get(section)
        if isinstance(value, dict):
            _redact_mapping(value)

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


def init_error_tracking(*, component: str, release: str, redact_text: TextRedactor | None) -> bool:
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

    Returns:
        ``True`` when the SDK was initialised, ``False`` when it stayed a no-op.
        Callers ignore this; it exists so the behaviour is directly testable.
    """
    global _text_redactor
    _text_redactor = redact_text

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
