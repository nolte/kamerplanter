"""Request-body ceilings and upload spool budget at the ASGI boundary (#2254).

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

This middleware sits in front of the router and enforces, before the parse:

* **Two body ceilings.** A body Starlette would parse as multipart — decided
  with Starlette's own parser (:func:`is_multipart`), so a content type the
  framework spools can never slip past as "not multipart" — may carry an upload:
  its ceiling equals the edge proxy's (``storage.maxFileSizeMb`` + 1 MiB,
  #2144). Every other body (JSON, form-urlencoded, unknown or missing type) is
  held to :data:`NON_MULTIPART_MAX_BODY_BYTES` (1 MiB). A declared
  ``Content-Length`` above the ceiling is refused with ``413`` before a byte is
  read; otherwise the body is counted as the application reads it and aborted
  with ``413`` the moment it passes the ceiling.
* **Spool budget, counted in received bytes.** Concurrent multipart bodies
  share a byte budget sized to the temporary storage. Each received chunk takes
  its bytes from the budget before the parser sees it, so only bytes that
  actually arrived are held — a client that announces 25 MiB and sends nothing
  holds nothing. A chunk that cannot get its bytes within
  ``spool_wait_seconds`` ends the request with ``503`` + ``Retry-After``
  instead of filling ``/tmp`` until the parse fails with an unexplained
  ``400``. Everything a request took is returned when it ends — answered,
  refused, disconnected or cancelled.

* **Route ceilings** (#2138). One route may carry its own multipart ceiling
  (:class:`RouteBodyCeiling`, matched on the exact method and path before the
  body is read): the platform admin's tenant import takes an archive up to
  ``TENANT_IMPORT_MAX_UPLOAD_MB`` + 1 MiB. Every other route keeps the global
  ceiling, and a path variant that does not match exactly falls back to it
  (the safe direction). A route ceiling above the spool budget is lowered to
  the budget at start (logged): a body the budget can never hold would only
  wait for ``spool_wait_seconds`` and end in ``503``; ``413`` names the limit
  instead. The route's own gates — platform admin, step-up — run after the
  parse as before; what the ceiling admits is still counted against the
  shared budget, which therefore stays the bound on what ``/tmp`` holds.

Non-multipart bodies take nothing from the budget: their 1 MiB ceiling keeps
them in memory (Starlette spools file parts of multipart bodies only, and only
above 1 MiB), so they cannot reach ``/tmp``.

The route-level ``Content-Length`` check and bounded read stay as defence in
depth: they hold the *per-route* file limit, which may be smaller than the
global ceiling.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterable
from dataclasses import dataclass

import structlog
from python_multipart.multipart import parse_options_header
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.common.error_handlers import app_error_response
from app.common.exceptions import KamerplanterError, RequestBodyTooLargeError, UploadCapacityExhaustedError
from app.common.upload_bounds import parse_content_length

logger = structlog.get_logger()

#: Headroom above the file limit for the multipart framing and form fields —
#: the same 1 MiB the edge proxy adds (``client_max_body_size``, #2144).
BODY_HEADROOM_BYTES = 1024 * 1024

#: Ceiling for every body that is not a multipart upload (JSON, form-urlencoded,
#: unknown). The largest JSON request the API takes is far below it; it also
#: keeps such a body under Starlette's 1 MiB spool threshold.
NON_MULTIPART_MAX_BODY_BYTES = 1024 * 1024

#: How often a request waiting for spool budget looks again.
_BUDGET_POLL_SECONDS = 0.05


def request_body_limit_bytes(max_file_size_mb: int) -> int:
    """The multipart body ceiling for a file limit of ``max_file_size_mb`` MiB (edge parity)."""
    return max_file_size_mb * 1024 * 1024 + BODY_HEADROOM_BYTES


def declared_length(headers: Headers) -> int | None:
    """``Content-Length`` as an int, or ``None`` when absent or not a plain ASCII decimal."""
    return parse_content_length(headers.get("content-length"))


def is_multipart(headers: Headers) -> bool:
    """Whether Starlette would parse this body as ``multipart/form-data``.

    The same parser and the same comparison as ``starlette.requests.Request.form``
    (``parse_options_header(ct)[0] == b"multipart/form-data"``). A home-grown
    prefix check disagreed with it: ``"\\xa0multipart/form-data"`` is multipart to
    Starlette (the parser strips the leading space) but not to ``startswith``.
    """
    raw = headers.get("content-type")
    if not raw:
        return False
    content_type, _options = parse_options_header(raw)
    return bool(content_type == b"multipart/form-data")


@dataclass(frozen=True)
class RouteBodyCeiling:
    """A multipart body ceiling of its own for one route: exact ``method`` and ``path`` (#2138)."""

    method: str
    path: str
    max_body_bytes: int


class _AbortBodyError(Exception):
    """Raised from the counting ``receive`` to stop the application's read."""


class SpoolBudget:
    """A byte budget shared by the multipart bodies of one process.

    Loop-agnostic on purpose (a counter, no asyncio primitive): the check and
    the increment in :meth:`try_reserve` run without an ``await`` between them,
    so two coroutines of one loop cannot both take the last bytes.
    """

    def __init__(self, capacity_bytes: int) -> None:
        self.capacity_bytes = capacity_bytes
        self.in_use_bytes = 0

    def try_reserve(self, size: int) -> bool:
        if self.in_use_bytes + size > self.capacity_bytes:
            return False
        self.in_use_bytes += size
        return True

    async def reserve(self, size: int, wait_seconds: float) -> bool:
        """Reserve ``size`` bytes, waiting up to ``wait_seconds`` for them to free."""
        deadline = time.monotonic() + wait_seconds
        while not self.try_reserve(size):
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(_BUDGET_POLL_SECONDS)
        return True

    def release(self, size: int) -> None:
        self.in_use_bytes = max(0, self.in_use_bytes - size)


class RequestBodyLimitMiddleware:
    """Pure ASGI middleware enforcing the body ceilings and the spool budget (#2254)."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        max_body_bytes: int,
        spool_budget_bytes: int,
        spool_wait_seconds: float,
        non_multipart_max_body_bytes: int = NON_MULTIPART_MAX_BODY_BYTES,
        route_ceilings: Iterable[RouteBodyCeiling] = (),
    ) -> None:
        if max_body_bytes > spool_budget_bytes:
            msg = (
                f"The multipart body ceiling ({max_body_bytes} bytes) exceeds the upload spool budget "
                f"({spool_budget_bytes} bytes): a single full-size upload could never be accepted."
            )
            raise ValueError(msg)
        self.app: ASGIApp = app
        self.max_body_bytes = max_body_bytes
        self.non_multipart_max_body_bytes = non_multipart_max_body_bytes
        self.budget = SpoolBudget(spool_budget_bytes)
        self.spool_wait_seconds = spool_wait_seconds
        self.route_ceilings: dict[tuple[str, str], int] = {}
        for route in route_ceilings:
            ceiling = route.max_body_bytes
            if ceiling > spool_budget_bytes:
                logger.warning(
                    "upload_route_ceiling_lowered_to_spool_budget",
                    method=route.method,
                    path=route.path,
                    requested_bytes=ceiling,
                    spool_budget_bytes=spool_budget_bytes,
                )
                ceiling = spool_budget_bytes
            self.route_ceilings[(route.method.upper(), route.path)] = ceiling

    def ceiling_for(self, scope: Scope, *, multipart: bool) -> int:
        """The body ceiling of this request: the route's own for a multipart body, else the global one."""
        if not multipart:
            return self.non_multipart_max_body_bytes
        method: str = scope.get("method", "")
        path: str = scope.get("path", "")
        own = self.route_ceilings.get((method.upper(), path))
        return own if own is not None else self.max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        inner: ASGIApp = self.app
        if scope["type"] != "http":
            await inner(scope, receive, send)
            return

        headers = Headers(scope=scope)
        multipart = is_multipart(headers)
        ceiling = self.ceiling_for(scope, multipart=multipart)
        declared = declared_length(headers)
        if declared is not None and declared > ceiling:
            await self._refuse_too_large(scope, send, ceiling, declared=declared)
            return
        await self._run_counted(inner, scope, receive, send, ceiling=ceiling, accounted=multipart)

    async def _run_counted(
        self,
        inner: ASGIApp,
        scope: Scope,
        receive: Receive,
        send: Send,
        *,
        ceiling: int,
        accounted: bool,
    ) -> None:
        received = 0
        reserved = 0
        abort: str | None = None
        take_budget = self.budget.reserve
        response_started = False

        async def counting_receive() -> Message:
            nonlocal received, reserved, abort
            if abort is not None:
                raise _AbortBodyError
            message: Message = await receive()
            if message["type"] != "http.request":
                return message
            size = len(message.get("body", b""))
            received += size
            if received > ceiling:
                abort = "too_large"
                raise _AbortBodyError
            if accounted and size:
                if not await take_budget(size, self.spool_wait_seconds):
                    abort = "capacity"
                    raise _AbortBodyError
                reserved += size
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            # Once the body was aborted the application's own answer to the
            # broken read (FastAPI turns it into a 400) is dropped for ours.
            if abort is not None and not response_started:
                return
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            try:
                await inner(scope, counting_receive, guarded_send)
            except Exception:
                if abort is None:
                    raise
            if abort is not None and not response_started:
                if abort == "too_large":
                    await self._refuse_too_large(scope, send, ceiling, received=received)
                else:
                    await self._refuse_capacity(scope, send, received=received)
        finally:
            if reserved:
                self.budget.release(reserved)

    async def _refuse_too_large(
        self, scope: Scope, send: Send, ceiling: int, *, declared: int | None = None, received: int | None = None
    ) -> None:
        logger.info("request_body_too_large", limit_bytes=ceiling, declared_bytes=declared, received_bytes=received)
        await self._reply(scope, send, RequestBodyTooLargeError(ceiling), {})

    async def _refuse_capacity(self, scope: Scope, send: Send, *, received: int) -> None:
        logger.warning(
            "upload_spool_budget_exhausted",
            in_use_bytes=self.budget.in_use_bytes,
            capacity_bytes=self.budget.capacity_bytes,
            received_bytes=received,
        )
        exc = UploadCapacityExhaustedError(retry_after=max(1, int(self.spool_wait_seconds)))
        await self._reply(scope, send, exc, {"Retry-After": str(exc.retry_after)})

    @staticmethod
    async def _reply(scope: Scope, send: Send, exc: KamerplanterError, extra_headers: dict[str, str]) -> None:
        response = app_error_response(Request(scope), exc)
        for name, value in extra_headers.items():
            response.headers[name] = value
        # ``Connection: close``: every answer from here leaves the rest of the
        # body unread, and the server must not try to reuse the connection.
        response.headers["Connection"] = "close"

        async def no_body() -> Message:
            return {"type": "http.disconnect"}

        await response(scope, no_body, send)


__all__ = [
    "BODY_HEADROOM_BYTES",
    "NON_MULTIPART_MAX_BODY_BYTES",
    "RequestBodyLimitMiddleware",
    "RouteBodyCeiling",
    "SpoolBudget",
    "declared_length",
    "is_multipart",
    "request_body_limit_bytes",
]
