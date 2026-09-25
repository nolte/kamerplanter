"""What a log line may carry about a person (#1781).

A log stream has no retention rule of its own (NFR-011): whatever it receives
outlives the account it names, the erasure that removed the account and the
erasure record proving it (R-06). A log call therefore never hands the logger a
data subject's account key, e-mail address, full IP address or an unredacted
exception text — it hands it the value of one of these helpers:

* :func:`log_subject` — the salted subject reference instead of an account key;
* :func:`loggable_error` — an exception text with the subject's key, export
  bundle keys, e-mail addresses and URL query strings masked;
* :func:`loggable_ip` — an IP truncated the NFR-011 R-03 way, i.e. no more than
  the database keeps long-term;
* :func:`loggable_path` — a request path reduced to the app's literal route
  segments (#1795): no token, tenant slug, key or query string;
* :func:`redacted_traceback` — a traceback whose every exception line (cause
  and context too) went through :func:`loggable_exception_text` (#1796): the
  structlog chain and every stdlib log handler render tracebacks with it;
* :func:`loggable_text` — the sink backstop over a whole rendered line
  (addresses, URL userinfo, query strings, fragments, export-bundle keys);
* :func:`loggable_url_text` — a library's request line with every URL's userinfo
  and query string masked (#1795: the API keys OpenWeatherMap and Perenual carry
  in the query);
* ``app.common.decoys.email_digest`` — the keyed pseudonym of an address.

``tests/unit/guards/test_privacy_logs_carry_no_plaintext_subject.py`` enforces
the rule over every module under ``app/``. The salt is read from ``settings`` at
call time, so tests can monkeypatch it.
"""

from __future__ import annotations

import ipaddress
import re
import traceback
from collections.abc import Callable, Iterable
from types import TracebackType

from app.common.decoys import email_digest
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.storage.export_bundle_key import mask_export_bundle_keys

#: The domain half of an e-mail address inside free text (an
#: ``SMTPRecipientsRefused`` names the refused address, a ``NotFoundError`` may
#: name the looked-up one): ``@`` plus at least two labels. ``\w`` is Unicode, so
#: ``bücher.de`` is a domain; labels are bounded to their DNS length (63).
_EMAIL_DOMAIN = re.compile(r"@[\w-]{1,63}(?:\.[\w-]{1,63})+")
#: One character of an address's local part (``\w`` Unicode: ``müller``). An RFC
#: local part is at most 64 characters, so the scan left of ``@`` stops there.
#: ``/ ? & = #`` are legal in a local part but never seen in a real one, and they
#: are what separates URL parts: allowing them let the scan swallow
#: ``//api.x.com/v1/u/alice`` and hide the URL's query from the masking (review
#: SEC-001), so the scan stops at them.
_EMAIL_LOCAL_CHAR = re.compile(r"[\w.!$%*+^`{|}~-]")
_HEX4 = re.compile(r"[0-9A-Fa-f]{4}")
_EMAIL_LOCAL_MAX = 64
#: Where a URL starts inside free text; its end is the next whitespace or quote.
_URL_START = re.compile(r"https?://", re.IGNORECASE)
_URL_END = re.compile(r"[\s'\"\\]")
_URL_TAIL = re.compile(r"[?#]")
#: A URL's userinfo (``user:password@`` or ``user@``) inside free text: a Redis
#: or SMTP DSN in a connection error carries the password there (#1795). The
#: lookbehind makes only the start of a scheme-character run a candidate, and
#: the scheme is bounded, so a long run is tried once, not once per character.
#: The userinfo runs to the LAST ``@`` before ``/ ? #`` — a password may contain
#: ``@`` (``redis://:p@ss@valkey``, review SEC-004); the greedy run is bounded by
#: the authority, so each scheme is scanned once.
_URL_USERINFO = re.compile(r"(?<![A-Za-z0-9+.-])([A-Za-z][A-Za-z0-9+.-]{0,31}://)[^\s/?#'\"\\]*@")
#: Any query string inside a library's request line — a full URL's (httpx) or a
#: bare request target's (urllib3: ``"GET /path?query HTTP/1.1"``). A ``?``
#: ends it, so ``?a?a?a…`` is linear.
_ANY_QUERY = re.compile(r"\?[^\s'\"?\\]+")
#: The two spellings in which libraries put a *bare* request target (no scheme,
#: no host) into an exception text or a request line (review SEC-006): urllib3's
#: ``Max retries exceeded with url: /path?query`` and a ``"GET /path?query
#: HTTP/1.1"`` request line. Deliberately not a general ``?`` rule — that would
#: mangle traceback source lines (``x if y else None  # why?``).
_BARE_TARGET_QUERIES = (
    re.compile(r"(with url: /[^\s?'\"\\]*)\?[^\s'\"\\)]+"),
    re.compile(r"(\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) /[^\s?'\"\\]*)\?[^\s'\"\\]+(?= HTTP/)"),
)
#: The longest text :func:`loggable_error` returns; the rest is replaced by a
#: marker naming how much was cut. Applied after masking, so a cut can never
#: leave half an address readable.
MAX_LOGGABLE_TEXT = 4000
#: What stands in for a path segment that is not a literal segment of a route.
PATH_PLACEHOLDER = "{}"
#: The segments :func:`loggable_path` keeps when the app's routes are unknown.
_FALLBACK_SEGMENT = re.compile(r"api|v\d+")

_route_source: Callable[[], Iterable[str]] | None = None
_literal_segments: frozenset[str] | None = None


def log_subject(user_key: str | None) -> str | None:
    """The reference a log line carries instead of *user_key*; ``None`` for no key.

    ``ErasureEngine.log_subject`` keyed with the configured tombstone salt; a
    missing or short salt yields ``anon_unavailable``, never the plaintext key.
    """
    if not user_key:
        return None
    return ErasureEngine.log_subject(user_key, settings.erasure_tombstone_salt)


def loggable_error(error: BaseException | str, *, user_key: str | None = None) -> str:
    """*error*'s text as it may reach a log line.

    The text stays — an operator needs it — with, in this order: *user_key*
    replaced by :func:`log_subject`, the account segment of every embedded
    export-bundle key masked, every URL's userinfo replaced by ``<redacted>``
    (before the address rule, so ``mailto://alice:pw@host`` loses both), every
    e-mail address (Unicode included) replaced by
    ``<email:{email_digest(address)}>``, and every URL query string and fragment
    replaced by ``<redacted>``. The result is capped at
    :data:`MAX_LOGGABLE_TEXT` characters with a ``…<truncated N chars>`` marker.
    """
    text = error if isinstance(error, str) else str(error)
    if user_key:
        text = ErasureEngine.redact_subject(text, user_key, settings.erasure_tombstone_salt)
    text = _mask_text(mask_export_bundle_keys(text))
    if len(text) <= MAX_LOGGABLE_TEXT:
        return text
    return f"{text[:MAX_LOGGABLE_TEXT]}…<truncated {len(text) - MAX_LOGGABLE_TEXT} chars>"


def _mask_text(text: str) -> str:
    """URL userinfo, URL query strings and fragments, bare request-target queries, then addresses — linear (#1796).

    Every pattern either starts only at a run boundary with bounded quantifiers or
    is driven by a cursor that never revisits text, so a 200 000-character
    exception text of any shape masks in milliseconds (the unbounded predecessors
    were quadratic: 8 000 characters of ``a.`` took 0.85 s).
    """
    text = _URL_USERINFO.sub(r"\1<redacted>@", text)
    # URL tails before addresses: an address-shaped path segment
    # (``/u/alice@example.org/``, ``tile@2x.png``) must not be turned into an
    # ``<email:…>`` token that hides the URL — and its query — from this step.
    text = _mask_url_tails(text)
    for pattern in _BARE_TARGET_QUERIES:
        text = pattern.sub(r"\1?<redacted>", text)
    return _mask_emails(text)


def _skip_escape(text: str, start: int) -> int:
    """*start* moved past a backslash escape the leftward scan ran into.

    The sink backstop runs over rendered structlog JSON, where a newline before
    an address is the two characters ``\\n``: the ``n`` is a local-part
    character, so the scan would swallow it and leave a lone backslash in
    front of ``<email:…>`` — an invalid JSON escape (``Invalid \\escape``). The
    escape letter (and a ``\\uXXXX`` escape's four hex digits) stays outside
    the address.
    """
    if start == 0 or text[start - 1] != "\\":
        return start
    if text[start : start + 1] == "u" and _HEX4.fullmatch(text[start + 1 : start + 5]):
        return start + 5
    return start + 1


def _mask_emails(text: str) -> str:
    """Every address replaced by ``<email:{email_digest(address)}>``.

    Found from its ``@`` + domain, then extended left over at most 64 local-part
    characters — an over-long run of address characters therefore still loses
    the address at its end, and no start position is tried twice.
    """
    parts: list[str] = []
    cursor = 0
    for match in _EMAIL_DOMAIN.finditer(text):
        at = match.start()
        start = at
        floor = max(cursor, at - _EMAIL_LOCAL_MAX)
        while start > floor and _EMAIL_LOCAL_CHAR.fullmatch(text[start - 1]):
            start -= 1
        start = _skip_escape(text, start)
        if start >= at:
            continue
        parts.append(text[cursor:start])
        parts.append(f"<email:{email_digest(text[start : match.end()])}>")
        cursor = match.end()
    parts.append(text[cursor:])
    return "".join(parts)


def _mask_url_tails(text: str) -> str:
    """Every ``http(s)://`` URL's query string and fragment replaced by ``<redacted>``.

    httpx errors embed the full request URL: the weather adapters' carries the
    site coordinates, OpenWeatherMap's and Perenual's an API key; an OAuth
    redirect carries ``#access_token=``. Everything from the first ``?`` or ``#``
    to the URL's end (whitespace or a quote) goes, whichever comes first.
    """
    parts: list[str] = []
    cursor = 0
    for match in _URL_START.finditer(text):
        if match.start() < cursor:
            continue
        stop = _URL_END.search(text, match.end())
        end = stop.start() if stop else len(text)
        tail = _URL_TAIL.search(text, match.end(), end)
        if tail is None:
            parts.append(text[cursor:end])
        else:
            parts.append(text[cursor : tail.start() + 1])
            parts.append("<redacted>")
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


def loggable_ip(ip: str | None) -> str | None:
    """*ip* truncated the NFR-011 R-03 way: IPv4 last octet 0, IPv6 its /48 network.

    The same truncation ``anonymize_old_ips`` applies to the stored refresh-token
    IP after 7 days, so a log line never holds more than the database keeps
    long-term. An unparsable value yields ``0.0.0.0``; ``None`` stays ``None``.
    """
    if ip is None:
        return None
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "0.0.0.0"
    if isinstance(addr, ipaddress.IPv4Address):
        return str(ipaddress.IPv4Network(f"{addr}/24", strict=False).network_address)
    return str(ipaddress.IPv6Network(f"{addr}/48", strict=False).network_address)


def loggable_url_text(text: str) -> str:
    """*text* (a library's rendered request line) with every URL userinfo and query string masked.

    For the lines httpx and urllib3 write themselves (#1795): the userinfo becomes
    ``<redacted>@`` and every ``?query`` — of a full URL or of a bare request
    target — becomes ``?<redacted>``. Nothing else is touched: host and path stay,
    an operator needs them.
    """
    text = _URL_USERINFO.sub(r"\1<redacted>@", text)
    return _ANY_QUERY.sub("?<redacted>", text)


_URL_PATH_START = re.compile(r"[/?#]")


def mask_url_paths(text: str) -> str:
    """*text* with every ``http(s)://`` URL cut back to scheme and host: ``https://host/<redacted>`` (#1796).

    For texts whose URLs carry a credential in the *path*, where
    :func:`loggable_error` (query and fragment only) is not enough: a Web Push
    endpoint's path is the device's push token. Linear, like :func:`_mask_url_tails`.
    """
    parts: list[str] = []
    cursor = 0
    for match in _URL_START.finditer(text):
        if match.start() < cursor:
            continue
        stop = _URL_END.search(text, match.end())
        end = stop.start() if stop else len(text)
        path = _URL_PATH_START.search(text, match.end(), end)
        if path is None:
            parts.append(text[cursor:end])
        else:
            parts.append(text[cursor : path.start()])
            parts.append("/<redacted>")
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts)


def register_route_source(source: Callable[[], Iterable[str]]) -> None:
    """Tell :func:`loggable_path` where the app's route templates come from.

    ``app.main`` registers a callable right after it creates the app, so this
    module never imports ``app.main``. The callable runs lazily, once, at the
    first :func:`loggable_path` call — when every router is mounted.
    """
    global _route_source, _literal_segments
    _route_source = source
    _literal_segments = None


def _known_segments() -> frozenset[str]:
    global _literal_segments
    if _literal_segments is None:
        if _route_source is None:
            return frozenset()
        try:
            templates = list(_route_source())
        # A failing route walk must never break a log line; the fallback below
        # keeps only ``api``/``v<n>``, which is the privacy-safe direction.
        except Exception:
            templates = []
        _literal_segments = frozenset(
            segment for template in templates for segment in template.split("/") if segment and "{" not in segment
        )
    return _literal_segments


def loggable_path(path: str) -> str:
    """*path* (a request target) with every segment that is not a route literal replaced (#1795).

    A request path carries whatever the route's parameters carry: the attachment
    download token (``/api/v1/attachments/token/{token}``, which *is* the
    authorisation), the tenant slug derived from a person's display name
    (``/api/v1/t/{tenant_slug}/…``), account and entity keys. A segment is kept
    only when it is a literal segment of some route of the app (derived once from
    the source :func:`register_route_source` registered); every other segment
    becomes ``{}``, and a query string becomes ``?<redacted>``. Before a source is
    registered, or when it fails, only ``api`` and ``v<digits>`` are kept.

    ``/api/v1/t/max-mustermann/plant-instances/123`` →
    ``/api/v1/t/{}/plant-instances/{}``. A value that happens to equal a literal
    segment (a tenant slug ``plants``) stays — it is then indistinguishable from
    the route word it matches.
    """
    target, has_query, _query = path.partition("?")
    known = _known_segments()
    segments = [
        segment if not segment or segment in known or _FALLBACK_SEGMENT.fullmatch(segment) else PATH_PLACEHOLDER
        for segment in target.split("/")
    ]
    return "/".join(segments) + ("?<redacted>" if has_query else "")


ExcInfo = tuple[type[BaseException], BaseException, TracebackType | None]

#: A ``str(exc)`` shorter than this is not searched for inside a rendered line —
#: it could not carry a key or an address, and replacing ``"0"`` everywhere would
#: mangle the line.
_MIN_REPLACED_TEXT = 3


def loggable_text(text: str) -> str:
    """A whole rendered log line with addresses, URL userinfo/queries/fragments and bundle keys masked.

    The sink backstop (#1796): applied by the handler-level filter to every line a
    stdlib handler writes, whatever produced it. Not capped — a log line is not
    an exception text.
    """
    return _mask_text(mask_export_bundle_keys(text))


def loggable_exception_text(exc: BaseException) -> str:
    """What a log line may say about *exc*'s message (#1796).

    A ``KamerplanterError`` is a domain error whose message names what it is
    about — ``NotFoundError("User", <key>)`` names the account key — so it is
    reduced to its ``error_code`` (the class name stays next to it). Every other
    exception keeps its text through :func:`loggable_error`.
    """
    if isinstance(exc, KamerplanterError):
        return f"[{exc.error_code}]"
    try:
        return loggable_error(exc)
    except Exception:
        return "<unprintable exception text>"


def _exception_chain(exc: BaseException) -> list[BaseException]:
    """*exc*, its causes and contexts and every exception-group member — each once."""
    chain: list[BaseException] = []
    seen: set[int] = set()
    pending = [exc]
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        chain.append(current)
        pending.extend(e for e in (current.__cause__, current.__context__) if e is not None)
        if isinstance(current, BaseExceptionGroup):
            pending.extend(current.exceptions)
    return chain


def _type_name(exc: BaseException) -> str:
    cls = type(exc)
    module = cls.__module__
    return cls.__qualname__ if module in ("builtins", "__main__") else f"{module}.{cls.__qualname__}"


def _exception_line(exc: BaseException) -> str:
    text = loggable_exception_text(exc)
    return f"{_type_name(exc)}: {text}\n" if text else f"{_type_name(exc)}\n"


#: A chain longer than this is cut, with a line naming how many were left out:
#: the renderer must never raise inside a log call (review SEC-003).
_MAX_CHAIN = 100
#: How deep exception groups nested in exception groups are rendered.
_MAX_GROUP_DEPTH = 8
_CAUSE = "The above exception was the direct cause of the following exception:"
_CONTEXT = "During handling of the above exception, another exception occurred:"


def _format_exception(exc: BaseException, lines: list[str], seen: set[int], indent: str = "", depth: int = 0) -> None:
    """Render *exc*'s chain oldest first — iteratively, so no chain length can raise ``RecursionError``."""
    chain: list[tuple[BaseException, str | None]] = []
    current: BaseException | None = exc
    relation: str | None = None
    while current is not None and id(current) not in seen and len(chain) < _MAX_CHAIN:
        seen.add(id(current))
        chain.append((current, relation))
        if current.__cause__ is not None:
            current, relation = current.__cause__, _CAUSE
        elif current.__context__ is not None and not current.__suppress_context__:
            current, relation = current.__context__, _CONTEXT
        else:
            current = None
    if current is not None and id(current) not in seen:
        lines.append(f"{indent}... older chained exceptions not shown (more than {_MAX_CHAIN})\n\n")
    for position in range(len(chain) - 1, -1, -1):
        member, member_relation = chain[position]
        _format_one(member, lines, seen, indent, depth)
        if position > 0 and member_relation is not None:
            lines.append(f"\n{indent}{member_relation}\n\n")


def _format_one(exc: BaseException, lines: list[str], seen: set[int], indent: str, depth: int) -> None:
    if exc.__traceback__ is not None:
        lines.append(f"{indent}Traceback (most recent call last):\n")
        lines.extend(indent + frame for frame in traceback.format_tb(exc.__traceback__))
    lines.append(indent + _exception_line(exc))
    notes = getattr(exc, "__notes__", None)
    if isinstance(notes, list | tuple):
        lines.extend(f"{indent}{loggable_error(_safe_text(note))}\n" for note in notes)
    if isinstance(exc, BaseExceptionGroup):
        if depth >= _MAX_GROUP_DEPTH:
            lines.append(f"{indent}... nested exception groups not shown\n")
            return
        for number, member in enumerate(exc.exceptions, start=1):
            lines.append(f"{indent}+---------------- {number} ----------------\n")
            _format_exception(member, lines, seen, indent + "    ", depth + 1)


def _safe_text(value: object) -> str:
    try:
        return str(value)
    except Exception:
        return "<unprintable>"


def redacted_traceback(exc_info: ExcInfo | BaseException) -> str:
    """*exc_info* rendered like ``traceback.format_exception`` — frames as usual, messages redacted (#1796).

    Every exception line of the chain (``__cause__``, ``__context__``, group
    members, notes) goes through :func:`loggable_exception_text`: a
    ``KamerplanterError`` shows its class and ``error_code`` only, any other
    exception its :func:`loggable_error` text. Frame lines are the source lines of
    the code, never runtime values. The one renderer both sinks use: structlog's
    ``ExceptionRenderer`` and the stdlib handler filter in ``app.config.logging``.
    """
    exc = exc_info if isinstance(exc_info, BaseException) else exc_info[1]
    if exc is None:
        return ""
    lines: list[str] = []
    _format_exception(exc, lines, set())
    return "".join(lines).rstrip("\n")


def redact_exception_texts(message: str, exc: BaseException) -> str:
    """*message* with every ``repr``/``str`` of an exception in *exc*'s chain replaced by its loggable text.

    For a rendered line that embeds the exception itself — Celery's ``Task …
    raised unexpected: %(exc)s``, a library's ``"failed: %s", exc``.
    """
    for member in _exception_chain(exc):
        replacement = loggable_exception_text(member)
        for rendered, substitute in (
            (_safe_repr(member), f"{type(member).__name__}({replacement!r})"),
            (_safe_str(member), replacement),
        ):
            if len(rendered) >= _MIN_REPLACED_TEXT and rendered in message:
                message = message.replace(rendered, substitute)
    return message


def _safe_str(exc: BaseException) -> str:
    try:
        return str(exc)
    except Exception:
        return ""


def _safe_repr(exc: BaseException) -> str:
    try:
        return repr(exc)
    except Exception:
        return ""
