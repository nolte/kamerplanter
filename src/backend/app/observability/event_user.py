"""Who an error event is about, as the backend may name it (#2129, #2136).

The backend's :data:`~app.observability.error_tracking.UserContext`: called by the
shared ``scrub_event`` hook at capture time, in the context of the request that
failed. It returns the request's pseudonyms — ``id`` is ``log_subject`` of the
principal (``sub_…``), ``tenant`` is ``log_tenant`` of the tenant the request
acts in (``ten_…``) — as recorded on the request's telemetry holder
(:mod:`app.common.request_context`). It never sees, and so can never send, an
account or tenant key.

**Only with the person's ``error_tracking`` consent (#2136, MT-040).** The block
is what makes an event *about someone*; the consent decides whether it is sent.
Without a granted consent, or when the consent cannot be read (a failing store
is a "no"), the event leaves without a ``user`` block. The lookup runs at most
once per request and only when an event is actually captured, so a request
that does not fail costs nothing.

Backend-only, unlike ``error_tracking.py`` (a shared copy): the request holder,
the pseudonym salt and the consent store are the backend's. Events outside a
request (the worker, startup) carry no ``user`` block.
"""

from __future__ import annotations

from app.common.request_context import current_request
from app.domain.engines.consent_engine import ERROR_TRACKING


def has_consent(user_key: str, purpose: str) -> bool:
    """Whether *user_key* currently grants *purpose*, read from the consent store."""
    from app.common.dependencies import get_ai_consent_guard

    return get_ai_consent_guard().has_consent(user_key, purpose)


def error_event_user() -> dict[str, str] | None:
    """The pseudonymous ``user`` block of the current request's error event, or ``None``."""
    telemetry = current_request()
    if telemetry is None or not telemetry.actor:
        return None
    if not telemetry.consent(ERROR_TRACKING, has_consent):
        return None
    user = {"id": telemetry.actor}
    if telemetry.tenant:
        user["tenant"] = telemetry.tenant
    return user
