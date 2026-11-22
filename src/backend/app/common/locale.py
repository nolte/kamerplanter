"""The one server-side locale resolution (NFR-017 R-112, R-114).

:func:`get_request_locale` is the FastAPI dependency a router injects when the
answer contains text the server words in a language (today: the species display
names of REQ-001 / #2902). The effective locale is, by priority:

1. an explicit ``locale`` / ``language`` query parameter, where the endpoint offers one;
2. *(not applied yet)* ``user.locale`` - the UI language switch does not write it and
   every account carries the default ``de``, so applying it would override the
   language the client actually displays with a value nobody chose (R-113 stays open);
3. the ``Accept-Language`` header, negotiated by q-value - the frontend sends its UI
   language (``i18n.language``) on every request;
4. :data:`DEFAULT_LOCALE`.

Only :data:`SUPPORTED_LOCALES` are ever returned; anything else falls through to
the next source. A background caller (Celery task, persisted text) has no request
and passes nothing: the services default to the canonical language.
"""

from __future__ import annotations

import re

from fastapi import Request

#: The canonical language (UI-NFR-007 R-009a): the fallback of every chain.
DEFAULT_LOCALE = "de"
#: The locales the server words content in. Order is the tie-break of equal q-values only.
SUPPORTED_LOCALES: tuple[str, ...] = ("de", "en")

#: One language range of ``Accept-Language`` (RFC 9110 §12.5.4): a tag or ``*``, an optional weight.
_RANGE = re.compile(
    r"^\s*(?P<tag>\*|[A-Za-z]{1,8}(?:[-_][A-Za-z0-9]{1,8})*)\s*(?:;\s*q\s*=\s*(?P<q>[0-9](?:\.[0-9]{0,3})?))?\s*$",
    re.IGNORECASE,
)
#: An ``Accept-Language`` value longer than this is not negotiated (a header is not a payload).
MAX_ACCEPT_LANGUAGE_LENGTH = 1024


def normalize_locale(value: str | None) -> str | None:
    """``value`` as a supported locale (``en-GB`` / ``EN_us`` -> ``en``), or ``None`` when it names none."""
    primary: str = re.split(r"[-_]", value or "", maxsplit=1)[0]
    stripped: str = primary.strip()
    code: str = stripped.lower()
    return code if code in SUPPORTED_LOCALES else None


def negotiate_accept_language(header: str | None) -> str | None:
    """The supported locale an ``Accept-Language`` value prefers most, or ``None`` when it accepts none.

    Ranges are ordered by their ``q`` weight (default 1, highest first, stable for equal
    weights); ``q=0`` means "not acceptable". A range with a malformed weight or tag is
    ignored, not the whole header. ``*`` accepts any language: the default one.
    """
    if not header or len(header) > MAX_ACCEPT_LANGUAGE_LENGTH:
        return None
    ranges: list[tuple[float, int, str]] = []
    for position, part in enumerate(header.split(",")):
        match = _RANGE.match(part)
        if match is None:
            continue
        weight = float(match.group("q")) if match.group("q") is not None else 1.0
        if weight <= 0.0 or weight > 1.0:
            continue
        ranges.append((-weight, position, match.group("tag")))
    for _weight, _position, tag in sorted(ranges):
        if tag == "*":
            return DEFAULT_LOCALE
        locale = normalize_locale(tag)
        if locale is not None:
            return locale
    return None


def resolve_locale(*, explicit: str | None, accept_language: str | None) -> str:
    """The effective locale from its sources, by the priority of the module docstring."""
    return normalize_locale(explicit) or negotiate_accept_language(accept_language) or DEFAULT_LOCALE


def get_request_locale(request: Request) -> str:
    """FastAPI dependency: the request's effective locale (NFR-017 R-112/R-114), always a supported one."""
    explicit = request.query_params.get("locale") or request.query_params.get("language")
    return resolve_locale(explicit=explicit, accept_language=request.headers.get("accept-language"))
