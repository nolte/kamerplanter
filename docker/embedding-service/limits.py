"""Request bounds, CPU budget and serving limits of the embedding service (#1725).

Kept apart from ``main.py`` and importing only the standard library and
pydantic, so the backend's guard suite
(src/backend/tests/unit/guards/test_ml_sidecar_limits.py) loads THIS file — the
one ``main.py`` imports — by path, without onnxruntime, tokenizers or a model.
docker/reranker-service/limits.py is its sibling and is held to the same
assertions by the same parametrized test; ``cpu_budget`` is a verbatim copy
there, because the two images are separate build contexts.

**Why bounds at all.** Before #1725 no field of ``/embed`` was bounded and all
texts of a request ran through the graph as one padded batch. Measured
2026-09-24 in the e5-large image under the chart's limits (``-m 4g --cpus 2``)
with texts of more than 512 tokens: 16 texts answered in 70 s, 64 texts were
OOMKilled in that one-batch shape. The bounds below turn an oversized request
into a 422 (FastAPI's own answer to a pydantic validation error) before it
reaches the tokenizer; ``main.py`` runs the graph one text at a time under one
lock, which is what keeps the memory of an accepted request flat.

**Why these values.** The only caller is src/knowledge-service/app/embedding.py:
``embed()`` sends one query, ``embed_batch()`` the chunks of one knowledge file
(spec/knowledge/rag: at most 16 chunks per file, at most 3524 characters per
chunk, measured 2026-09-24), in slices of at most ``_MAX_TEXTS_PER_REQUEST``
(32) — half of ``MAX_TEXTS`` — so a larger file is split by the caller instead
of refused here. The guard test re-reads that slice size. No minimum is set: an
empty ``texts`` list is answered with empty embeddings.

**Serving limits (security review of #1725).** The bounds act on a PARSED
request. What happens before parsing and while serving is bounded by the
section at the end of this file: ``BodySizeLimit`` (413 past
``MAX_BODY_BYTES``, derived from the bounds), a 422 that never echoes the
input, a lock wait of at most ``LOCK_WAIT_SECONDS`` (then 503 busy) and a
per-request ``MAX_INFERENCE_SECONDS`` deadline (then 503 timeout).
"""

from __future__ import annotations

import json
import math
import os
import threading
import time
from collections.abc import Awaitable, Callable, Iterator, Mapping, MutableMapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

#: The model this image serves; the final Dockerfile target sets it.
DEFAULT_MODEL = os.environ.get("EMBEDDING_MODEL", "multilingual-e5-base")

#: Items in ``texts``. The caller slices to at most 32 per request.
MAX_TEXTS = 64

#: Characters per text. Tokenization truncates each text to 512 tokens anyway,
#: so text past this bound could never change a vector; it would only cost
#: tokenizer time. The largest corpus chunk is 3524 characters.
MAX_TEXT_CHARS = 16384

#: Characters in ``prefix``. The caller sends ``"query: "`` or ``"passage: "``.
MAX_PREFIX_CHARS = 64

#: Characters in ``model`` (echoed back, never used to select a graph).
MAX_MODEL_CHARS = 128

#: Seconds a request waits for the inference lock before it is answered 503
#: ``{"status": "busy"}`` (``Retry-After`` = this value). LONGER than one
#: ingest slice: a search query (``embed()``, one short text) that arrives
#: while an ingest slice of 16 e5-large texts runs must still be served, and
#: that slice takes ~41 s at 2 CPUs (measured 2026-09-24, ``-m 4g --cpus 2``,
#: texts of more than 512 tokens: 16 texts in 40.3 s, 64 in 162 s, one text
#: per graph call).
LOCK_WAIT_SECONDS = 60

#: Seconds from the start of ``/embed`` (lock wait included) after which the
#: request is abandoned between two texts with 503 ``{"status": "timeout"}``
#: and the lock released. BELOW the caller's 120 s client timeout
#: (src/knowledge-service/app/embedding.py) — the whole budget, not just the
#: lock wait: past it nobody reads the answer (code review of the bundle; an
#: earlier value of 300 computed on for a caller that had given up). Two
#: concurrent ingest slices of 16 long texts (~41 s each) fit: 41 + 41 < 110.
#: A direct caller sending the full ``MAX_TEXTS`` of long e5-large texts
#: (162 s) is cut here; the knowledge-service never does (it slices at 16).
MAX_INFERENCE_SECONDS = 110

#: Worst-case bytes of JSON per character the bounds count. pydantic's
#: ``max_length`` counts code points; ``json.dumps`` (``ensure_ascii``, the
#: default of every Python client) writes a character outside the Basic
#: Multilingual Plane as a surrogate pair of two ``\uXXXX`` escapes — 12
#: bytes for ONE counted character (``json.dumps("\U0001F600")`` is 14 bytes
#: with its quotes). A BMP control character escapes to 6, raw UTF-8 is at
#: most 4. Taking 6 would refuse a valid request of emoji with 413.
JSON_BYTES_PER_CHAR = 12

#: Room for everything that is not a counted character: keys, quotes, commas
#: and whitespace — 64 texts cost about 256 bytes of it.
BODY_SLACK_BYTES = 64 * 1024

#: The largest request body read at all (``BodySizeLimit``, 413 above it):
#: every counted character at its worst-case encoding, plus the slack —
#: 12 650 752 bytes (~12.1 MiB). Derived from the bounds, never set by hand,
#: so raising a bound raises the cap with it; the guard test builds the
#: largest request the bounds accept and requires it to fit.
MAX_BODY_BYTES = (
    MAX_TEXTS * MAX_TEXT_CHARS + MAX_PREFIX_CHARS + MAX_MODEL_CHARS
) * JSON_BYTES_PER_CHAR + BODY_SLACK_BYTES

#: Where the container's cgroup filesystem is mounted.
CGROUP_ROOT = Path("/sys/fs/cgroup")


class EmbedRequest(BaseModel):
    texts: list[Annotated[str, Field(max_length=MAX_TEXT_CHARS)]] = Field(max_length=MAX_TEXTS)
    model: str = Field(default=DEFAULT_MODEL, max_length=MAX_MODEL_CHARS)
    prefix: str = Field(default="", max_length=MAX_PREFIX_CHARS)


def _available_cpus() -> int:
    """CPUs this process may be scheduled on (affinity), else the host count."""
    sched_getaffinity = getattr(os, "sched_getaffinity", None)
    if sched_getaffinity is not None:
        try:
            return len(sched_getaffinity(0))
        except OSError:
            pass
    return os.cpu_count() or 1


def _read_fields(path: Path) -> list[str] | None:
    try:
        return path.read_text(encoding="ascii", errors="replace").split()
    except OSError:
        return None


def _cgroup_cpu_limit(cgroup_root: Path) -> int | None:
    """The CPU quota of the cgroup, rounded UP to whole CPUs; None when unlimited or unreadable.

    cgroup v2 publishes ``cpu.max`` as ``<quota> <period>`` (``max`` = no
    quota). cgroup v1 publishes ``cpu.cfs_quota_us`` (``-1`` = no quota) and
    ``cpu.cfs_period_us`` under the ``cpu`` controller directory. Rounded up so
    a fractional limit (``1.5`` CPUs) still gets a thread for its fraction.
    """
    v2 = _read_fields(cgroup_root / "cpu.max")
    if v2 is not None:
        if len(v2) == 2 and v2[0] != "max":
            return _ceil_quota(v2[0], v2[1])
        return None
    for controller in ("cpu", "cpu,cpuacct"):
        quota = _read_fields(cgroup_root / controller / "cpu.cfs_quota_us")
        period = _read_fields(cgroup_root / controller / "cpu.cfs_period_us")
        if quota and period:
            return _ceil_quota(quota[0], period[0])
    return None


def _ceil_quota(quota: str, period: str) -> int | None:
    try:
        quota_us, period_us = int(quota), int(period)
    except ValueError:
        return None
    if quota_us <= 0 or period_us <= 0:
        return None
    return math.ceil(quota_us / period_us)


def cpu_budget(cgroup_root: Path = CGROUP_ROOT, *, available_cpus: int | None = None) -> int:
    """Threads the inference session may use: the container's CPU limit, never the host's.

    ``os.cpu_count()`` reports the HOST. Measured 2026-09-24 with
    ``docker run --cpus 2``: ``os.cpu_count()`` and ``sched_getaffinity`` both
    8, ``cpu.max`` ``200000 100000`` — so the service used to start 8 intra-op
    threads to share 2 CPUs of quota, which the kernel throttles. The budget is
    the smaller of the affinity set and the cgroup quota (rounded up), and at
    least 1.

    Args:
        cgroup_root: The cgroup mount; injectable so the guard test can feed a
            fake v1/v2 tree.
        available_cpus: The affinity count; injectable for the same reason.
            Defaults to ``len(os.sched_getaffinity(0))``.
    """
    budget = available_cpus if available_cpus is not None else _available_cpus()
    limit = _cgroup_cpu_limit(cgroup_root)
    if limit is not None:
        budget = min(budget, limit)
    return max(1, budget)


# --------------------------------------------------------------------------
# Serving under load (security review of #1725)
#
# EVERYTHING BELOW IS A VERBATIM COPY IN BOTH SERVICES' ``limits.py`` — the
# guard test compares the two ASTs. Only the constants it reads
# (``LOCK_WAIT_SECONDS``) differ per service. Standard library only, like the
# rest of this file: ``BodySizeLimit`` must run before FastAPI has parsed
# anything, and the handlers return a plain ASGI callable (Starlette awaits
# whatever an exception handler returns as ``response(scope, receive, send)``,
# starlette/_exception_handler.py), so none of this needs onnxruntime or even
# Starlette to be loaded and tested.
# --------------------------------------------------------------------------

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class JSONAnswer:
    """A complete JSON response as an ASGI callable — without Starlette."""

    def __init__(self, status_code: int, content: Any, headers: Mapping[str, str] | None = None) -> None:
        self.status_code = status_code
        self.body = json.dumps(content, separators=(",", ":")).encode("utf-8")
        self.headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(self.body)).encode("ascii")),
            *((name.lower().encode("latin-1"), value.encode("latin-1")) for name, value in (headers or {}).items()),
        ]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await send({"type": "http.response.start", "status": self.status_code, "headers": self.headers})
        await send({"type": "http.response.body", "body": self.body})


def _declared_length(scope: Scope) -> int | None:
    """The largest ``Content-Length`` the request declares; None when absent or unreadable."""
    lengths = []
    for name, value in scope.get("headers", ()):
        if name.lower() == b"content-length":
            try:
                lengths.append(int(value))
            except ValueError:
                return None
    return max(lengths) if lengths else None


class BodySizeLimit:
    """Refuse a request body larger than *max_body_bytes* with 413, before anything parses it.

    FastAPI reads the WHOLE body and ``json.loads`` it before pydantic sees a
    single bound, so without this a 1 GiB body is read into memory, decoded and
    turned into Python objects — only to be answered 422 afterwards. Two ways
    past a naive ``Content-Length`` check are closed:

    * a declared ``Content-Length`` above the cap is answered 413 without
      reading a byte (and before uvicorn sends a ``100 Continue``);
    * a body without one (``Transfer-Encoding: chunked``) or one that sends
      more than it declared is COUNTED while it is read, and answered 413 the
      moment the count passes the cap — the rest is never read.

    A body within the cap is buffered (FastAPI would buffer it anyway) and
    replayed to the application as one message; every later ``receive()``
    (a disconnect) goes to the server. The 413 carries ``Connection: close``,
    so the server drops the unread rest instead of parsing it as the next
    request.
    """

    def __init__(self, app: ASGIApp, *, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = _declared_length(scope)
        if declared is not None and declared > self.max_body_bytes:
            await self._too_large(scope, receive, send)
            return

        chunks: list[bytes] = []
        received = 0
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] != "http.request":
                return  # the client went away mid-body: nobody to answer
            body = message.get("body", b"")
            received += len(body)
            if received > self.max_body_bytes:
                await self._too_large(scope, receive, send)
                return
            chunks.append(body)
            more_body = message.get("more_body", False)

        buffered: Message | None = {"type": "http.request", "body": b"".join(chunks), "more_body": False}

        async def replay() -> Message:
            nonlocal buffered
            if buffered is not None:
                message, buffered = buffered, None
                return message
            return await receive()

        await self.app(scope, replay, send)

    async def _too_large(self, scope: Scope, receive: Receive, send: Send) -> None:
        answer = JSONAnswer(
            413,
            {"detail": f"request body larger than {self.max_body_bytes} bytes"},
            headers={"Connection": "close"},
        )
        await answer(scope, receive, send)


class ServiceUnavailableError(Exception):
    """The request cannot be served NOW; answered 503 with ``Retry-After``.

    *status* is ``"busy"`` (the inference lock was not obtained within
    ``LOCK_WAIT_SECONDS``) or ``"timeout"`` (the request passed its deadline
    between two inputs and was abandoned).
    """

    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


@contextmanager
def inference_slot(lock: threading.Lock, *, wait_seconds: float) -> Iterator[None]:
    """Hold *lock* for the body, or raise ``ServiceUnavailableError("busy")`` after *wait_seconds*.

    A bare ``with lock:`` waits forever, and each waiting request holds one of
    the AnyIO threadpool's 40 threads while it does: a queue of requests behind
    one long inference could take every thread. A bounded wait turns the excess
    into a fast 503 the caller can retry. The lock is released however the body
    ends — including the ``Deadline`` abort.
    """
    if not lock.acquire(timeout=wait_seconds):
        raise ServiceUnavailableError("busy")
    try:
        yield
    finally:
        lock.release()


class Deadline:
    """A per-request time budget, checked between two inputs of one request.

    A request whose caller has already given up is not cancelled by anything
    else: a sync route cannot see the disconnect, and ``session.run`` cannot be
    interrupted. ``check()`` before every input bounds how long one request can
    keep the inference lock — and so how long every request queued behind it
    waits — to the budget plus ONE input.
    """

    def __init__(self, seconds: float, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._expires = clock() + seconds

    def check(self) -> None:
        if self._clock() >= self._expires:
            raise ServiceUnavailableError("timeout")


@runtime_checkable
class _HasErrors(Protocol):
    def errors(self) -> Sequence[Mapping[str, Any]]: ...


async def validation_error_handler(request: object, exc: Exception) -> JSONAnswer:
    """422 with ``loc``, ``type`` and ``msg`` per error — never the offending ``input``.

    FastAPI's default handler (0.141.1, the locked version; measured
    2026-09-24) answers every error with its ``input`` and ``ctx``: a
    4097-character query came back as a 4247-byte 422, a 101-document list as
    the whole list. The response to an oversized request was as large as the
    request.
    """
    errors = exc.errors() if isinstance(exc, _HasErrors) else []
    detail = [
        {"loc": list(error.get("loc", ())), "type": error.get("type"), "msg": error.get("msg")} for error in errors
    ]
    return JSONAnswer(422, {"detail": detail})


async def unavailable_handler(request: object, exc: Exception) -> JSONAnswer:
    """503 ``{"status": "busy" | "timeout"}`` with ``Retry-After: LOCK_WAIT_SECONDS``."""
    status = exc.status if isinstance(exc, ServiceUnavailableError) else "busy"
    return JSONAnswer(503, {"status": status}, headers={"Retry-After": str(LOCK_WAIT_SECONDS)})
