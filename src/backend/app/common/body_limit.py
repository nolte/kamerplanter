"""Request-body ceiling and upload spool budget at the ASGI boundary (#2254).

FastAPI parses a ``multipart/form-data`` body completely before it calls the
route handler or solves a single dependency: every ``UploadFile`` / ``Form``
parameter is read from ``request.form()`` first. Starlette spools each file
part above 1 MiB into a temporary file under ``tempfile.gettempdir()`` (the
backend's memory-backed ``/tmp`` in the Helm chart). The ``Content-Length``
pre-check and the bounded read in the upload routes therefore ran only after
the whole body had been received and written to ``/tmp`` — measured: a 50 MiB
body against a 1 MiB file limit was consumed to the last byte before the 413,
with and without ``Content-Length``. The authentication dependency ran after
the parse too, so an anonymous caller got the same treatment.

This middleware sits in front of the router and enforces two bounds there:

* **Body ceiling.** A declared ``Content-Length`` above ``max_body_bytes`` is
  refused with ``413`` before a byte is read. A body without one (chunked) is
  counted while the application reads it and aborted with ``413`` the moment it
  passes the ceiling, so nothing beyond the ceiling is ever spooled. The
  ceiling equals the edge proxy's (``storage.maxFileSizeMb`` + 1 MiB, #2144):
  behind the chart's nginx nothing changes, a request that reaches the
  backend directly (port-forward, in-cluster caller, an ingress without a
  body limit) meets the same bound.
* **Spool budget.** Concurrent multipart bodies share a byte budget sized to
  the temporary storage. A request reserves its declared length (the ceiling
  when it declares none) before the parser starts; one that cannot get its
  share within ``spool_wait_seconds`` is answered ``503`` with
  ``Retry-After`` instead of filling ``/tmp`` until the parse fails with an
  unexplained ``400``.

The route-level ``Content-Length`` check and bounded read stay as defence in
depth: they hold the *per-route* file limit, which may be smaller than the
global ceiling.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.common.error_handlers import app_error_response
from app.common.exceptions import RequestBodyTooLargeError, UploadCapacityExhaustedError

logger = structlog.get_logger()

#: Headroom above the file limit for the multipart framing and form fields —
#: the same 1 MiB the edge proxy adds (``client_max_body_size``, #2144).
BODY_HEADROOM_BYTES = 1024 * 1024

#: How often a request waiting for spool budget looks again.
_BUDGET_POLL_SECONDS = 0.05


def request_body_limit_bytes(max_file_size_mb: int) -> int:
    """The body ceiling for a file limit of ``max_file_size_mb`` MiB (edge parity)."""
    return max_file_size_mb * 1024 * 1024 + BODY_HEADROOM_BYTES


class _BodyTooLargeError(Exception):
    """Raised from the counting ``receive`` once the body passes the ceiling."""


class SpoolBudget:
    """A byte budget shared by the multipart bodies of one process.

    Loop-agnostic on purpose (a counter, no asyncio primitive): the check and
    the increment in :meth:`try_reserve` run without an ``await`` between them,
    so two coroutines of one loop cannot both take the last share.
    """

    def __init__(self, capacity_bytes: int) -> None:
        self.capacity_bytes = capacity_bytes
        self.in_use_bytes = 0

    def share_for(self, wanted_bytes: int) -> int:
        """Clamp a reservation to the capacity so a single body always fits alone."""
        return min(wanted_bytes, self.capacity_bytes)

    def try_reserve(self, share: int) -> bool:
        if self.in_use_bytes + share > self.capacity_bytes:
            return False
        self.in_use_bytes += share
        return True

    async def reserve(self, share: int, wait_seconds: float) -> bool:
        """Reserve ``share`` bytes, waiting up to ``wait_seconds`` for them to free."""
        deadline = time.monotonic() + wait_seconds
        while not self.try_reserve(share):
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(_BUDGET_POLL_SECONDS)
        return True

    def release(self, share: int) -> None:
        self.in_use_bytes = max(0, self.in_use_bytes - share)


def _declared_length(headers: Headers) -> int | None:
    raw = headers.get("content-length")
    if raw is None or not raw.strip().isdigit():
        return None
    return int(raw)


class RequestBodyLimitMiddleware:
    """Pure ASGI middleware enforcing the body ceiling and the spool budget (#2254)."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        max_body_bytes: int,
        spool_budget_bytes: int,
        spool_wait_seconds: float,
    ) -> None:
        self.app: ASGIApp = app
        self.max_body_bytes = max_body_bytes
        self.budget = SpoolBudget(spool_budget_bytes)
        self.spool_wait_seconds = spool_wait_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        inner: ASGIApp = self.app
        if scope["type"] != "http":
            await inner(scope, receive, send)
            return

        headers = Headers(scope=scope)
        declared = _declared_length(headers)
        if declared is not None and declared > self.max_body_bytes:
            await self._refuse_too_large(scope, send, declared=declared)
            return

        share = 0
        if headers.get("content-type", "").lower().startswith("multipart/form-data"):
            share = self.budget.share_for(declared if declared is not None else self.max_body_bytes)
            if not await self.budget.reserve(share, self.spool_wait_seconds):
                logger.warning("upload_spool_budget_exhausted", in_use_bytes=self.budget.in_use_bytes, share=share)
                exc = UploadCapacityExhaustedError(retry_after=max(1, int(self.spool_wait_seconds)))
                await self._reply(scope, send, exc, {"Retry-After": str(exc.retry_after)})
                return
        try:
            await self._run_counted(inner, scope, receive, send)
        finally:
            if share:
                self.budget.release(share)

    async def _run_counted(self, inner: ASGIApp, scope: Scope, receive: Receive, send: Send) -> None:
        received = 0
        tripped = False
        response_started = False

        async def counting_receive() -> Message:
            nonlocal received, tripped
            if tripped:
                raise _BodyTooLargeError
            message: Message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_bytes:
                    tripped = True
                    raise _BodyTooLargeError
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            # Once the body was aborted the application's own answer to the
            # broken read (FastAPI turns it into a 400) is dropped for the 413.
            if tripped and not response_started:
                return
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await inner(scope, counting_receive, guarded_send)
        except Exception:
            if not tripped:
                raise
        if tripped and not response_started:
            await self._refuse_too_large(scope, send, declared=None, received=received)

    async def _refuse_too_large(
        self, scope: Scope, send: Send, *, declared: int | None, received: int | None = None
    ) -> None:
        logger.info(
            "request_body_too_large",
            limit_bytes=self.max_body_bytes,
            declared_bytes=declared,
            received_bytes=received,
        )
        # ``Connection: close``: the unread rest of the body is not drained.
        await self._reply(scope, send, RequestBodyTooLargeError(self.max_body_bytes), {"Connection": "close"})

    @staticmethod
    async def _reply(scope: Scope, send: Send, exc: Any, extra_headers: dict[str, str]) -> None:
        response = app_error_response(Request(scope), exc)
        for name, value in extra_headers.items():
            response.headers[name] = value

        async def no_body() -> Message:
            return {"type": "http.disconnect"}

        await response(scope, no_body, send)


__all__ = [
    "BODY_HEADROOM_BYTES",
    "RequestBodyLimitMiddleware",
    "SpoolBudget",
    "request_body_limit_bytes",
]
