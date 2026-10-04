"""Who an error event is about, as the backend may name it (#2129, MT-033).

The backend's :data:`~app.observability.error_tracking.UserContext`: called by the
shared ``scrub_event`` hook at capture time, in the context of the request that
failed. It returns the request's pseudonyms — ``id`` is ``log_subject`` of the
principal (``sub_…``), ``tenant`` is ``log_tenant`` of the tenant the request
acts in (``ten_…``) — as recorded on the request's telemetry holder
(:mod:`app.common.request_context`). It never sees, and so can never send, an
account or tenant key.

Backend-only, unlike ``error_tracking.py`` (a shared copy): the request holder
and the pseudonym salt are the backend's. Events outside a request (the worker,
startup) carry no ``user`` block.
"""

from __future__ import annotations

from app.common.request_context import current_request


def error_event_user() -> dict[str, str] | None:
    """The pseudonymous ``user`` block of the current request's error event, or ``None``."""
    telemetry = current_request()
    if telemetry is None or not telemetry.actor:
        return None
    user = {"id": telemetry.actor}
    if telemetry.tenant:
        user["tenant"] = telemetry.tenant
    return user
