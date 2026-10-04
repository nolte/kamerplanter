"""Per-request telemetry context: request id, actor and tenant pseudonyms (#2130, MT-034).

**Why a holder object and not ``structlog.contextvars.bind_contextvars``.** The
principal and the tenant are resolved in *sync* FastAPI dependencies
(``get_current_user``, ``get_current_tenant``). FastAPI runs those in a worker
thread with a **copy** of the request's context; a ContextVar set inside that
copy is discarded when the thread returns. Measured on the pre-#2130 tree: a
``bind_contextvars(tenant=…)`` inside the dependency was invisible to the line
the endpoint logged next. The middleware therefore puts one mutable
:class:`RequestTelemetry` into a ContextVar *before* anything else runs; every
copy of the context refers to that same object, so what a dependency records on
it is visible to the endpoint, to a task it dispatches and to the error tracker.

**Only pseudonyms are kept for the log.** ``actor`` is ``log_subject(user_key)``,
``tenant`` is ``log_tenant(tenant_key)`` — the references NFR-011 L-1 allows on a
log line. The raw account key is held privately for one purpose, the consent
lookup of the error tracker (#2136), and never merged into a line.

The holder is task-scoped by construction: the ASGI server runs every request in
its own task with its own context copy, so a request can never see another
request's holder, and nothing needs resetting.
"""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from app.common.log_privacy import log_subject, log_tenant

#: The structlog keys the holder contributes to a line, in this order.
TELEMETRY_KEYS = ("request_id", "actor", "tenant")


@dataclass
class RequestTelemetry:
    """What one request knows about itself, shared by every copy of its context."""

    request_id: str
    #: ``log_subject`` of the authenticated principal; ``None`` before/without one.
    actor: str | None = None
    #: ``log_tenant`` of the tenant the request acts in; ``None`` when none resolved.
    tenant: str | None = None
    #: The principal's account key, for consent lookups only — never logged.
    _user_key: str | None = field(default=None, repr=False)
    _consents: dict[str, bool] = field(default_factory=dict, repr=False)

    @property
    def user_key(self) -> str | None:
        return self._user_key

    def consent(self, purpose: str, lookup: Callable[[str, str], bool]) -> bool:
        """Whether the principal granted *purpose*, asked at most once per request; fails closed."""
        if not self._user_key:
            return False
        if purpose not in self._consents:
            try:
                self._consents[purpose] = bool(lookup(self._user_key, purpose))
            except Exception:  # noqa: BLE001 — an unanswerable question is a "no"
                return False
        return self._consents[purpose]

    def fields(self) -> dict[str, str]:
        """The pseudonymous fields a log line may carry."""
        values = {"request_id": self.request_id, "actor": self.actor, "tenant": self.tenant}
        return {key: value for key, value in values.items() if value}


_CURRENT: ContextVar[RequestTelemetry | None] = ContextVar("kp_request_telemetry", default=None)


def start_request(request_id: str) -> RequestTelemetry:
    """Create the holder for the request now starting; called by the request-id middleware."""
    telemetry = RequestTelemetry(request_id=request_id)
    _CURRENT.set(telemetry)
    return telemetry


def current_request() -> RequestTelemetry | None:
    """The holder of the request this code runs in, or ``None`` outside a request."""
    return _CURRENT.get()


def bind_actor(user_key: str | None) -> None:
    """Record the authenticated principal on the current request (no-op outside one)."""
    telemetry = _CURRENT.get()
    if telemetry is None or not user_key:
        return
    telemetry._user_key = user_key
    telemetry._consents.clear()
    telemetry.actor = log_subject(user_key)


def bind_tenant(tenant_key: str | None) -> None:
    """Record the tenant the current request acts in (no-op outside a request)."""
    telemetry = _CURRENT.get()
    if telemetry is None or not tenant_key:
        return
    telemetry.tenant = log_tenant(tenant_key)


def merge_request_telemetry(
    _logger: Any, _method: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """structlog processor: add the request's pseudonymous context to the line.

    A key the call site set explicitly wins — a line about *another* tenant (an
    admin acting on a foreign tenant) keeps the tenant it names.
    """
    telemetry = _CURRENT.get()
    if telemetry is not None:
        for key, value in telemetry.fields().items():
            event_dict.setdefault(key, value)
    return event_dict
