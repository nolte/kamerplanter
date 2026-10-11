"""#2254 — request-body ceiling and upload spool budget at the ASGI boundary.

Measured through raw ASGI calls, not ``TestClient``: the question is how many
body bytes the application pulls from ``receive`` before it answers, and
``TestClient`` hides that. The attachment router runs exactly as mounted in
production (FastAPI parses the multipart body before the route or any
dependency), behind :class:`RequestBodyLimitMiddleware`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

import pytest
from fastapi import FastAPI

from app.common.body_limit import (
    BODY_HEADROOM_BYTES,
    RequestBodyLimitMiddleware,
    SpoolBudget,
    request_body_limit_bytes,
)
from app.common.enums import TenantRole
from app.config.settings import Settings
from tests.api.test_attachments_router import _build, _make_jpeg

MIB = 1024 * 1024
BOUNDARY = b"kp2254boundary"


def _multipart_parts(filler_bytes: int, chunk: int = 64 * 1024) -> list[bytes]:
    """A multipart upload (category + a JPEG padded by ``filler_bytes``) as wire chunks."""
    head = (
        b"--" + BOUNDARY + b'\r\nContent-Disposition: form-data; name="category"\r\n\r\ndiary\r\n'
        b"--" + BOUNDARY + b'\r\nContent-Disposition: form-data; name="file"; filename="a.jpg"\r\n'
        b"Content-Type: image/jpeg\r\n\r\n"
    )
    tail = b"\r\n--" + BOUNDARY + b"--\r\n"
    parts = [head + _make_jpeg()]
    remaining = filler_bytes
    while remaining > 0:
        size = min(chunk, remaining)
        parts.append(b"\x00" * size)
        remaining -= size
    parts.append(tail)
    return parts


class _Probe:
    """Drives one ASGI request and records what the application consumed."""

    def __init__(self, parts: list[bytes], *, declare_length: bool, gate: asyncio.Event | None = None) -> None:
        self.parts = parts
        self.total = sum(len(p) for p in parts)
        self.declare_length = declare_length
        self.consumed = 0
        self.status: int | None = None
        self.headers: dict[str, str] = {}
        self.body = b""
        self._index = 0
        self._gate = gate

    async def receive(self) -> dict[str, Any]:
        if self._gate is not None and self._index == 1:
            await self._gate.wait()
        if self._index >= len(self.parts):
            return {"type": "http.disconnect"}
        body = self.parts[self._index]
        self._index += 1
        self.consumed += len(body)
        return {"type": "http.request", "body": body, "more_body": self._index < len(self.parts)}

    async def send(self, message: dict[str, Any]) -> None:
        if message["type"] == "http.response.start":
            self.status = message["status"]
            self.headers = {k.decode().lower(): v.decode() for k, v in message.get("headers", [])}
        elif message["type"] == "http.response.body":
            self.body += message.get("body", b"")

    def scope(self) -> dict[str, Any]:
        headers = [
            (b"host", b"testserver"),
            (b"content-type", b"multipart/form-data; boundary=" + BOUNDARY),
        ]
        if self.declare_length:
            headers.append((b"content-length", str(self.total).encode()))
        return {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/v1/t/anna/attachments",
            "raw_path": b"/api/v1/t/anna/attachments",
            "query_string": b"",
            "headers": headers,
            "client": ("127.0.0.1", 1),
            "server": ("testserver", 80),
            "root_path": "",
        }

    async def run(self, app: Callable[..., Any]) -> _Probe:
        await app(self.scope(), self.receive, self.send)
        return self


def _limited_app(tmp_path, *, file_limit_mb: int = 1, budget_bytes: int = 64 * MIB, wait: float = 0.0):
    inner, _service, _adapter = _build(
        tmp_path, TenantRole.LEAD, settings=Settings(storage_max_file_size_mb=file_limit_mb)
    )
    wrapped = RequestBodyLimitMiddleware(
        inner,
        max_body_bytes=request_body_limit_bytes(file_limit_mb),
        spool_budget_bytes=budget_bytes,
        spool_wait_seconds=wait,
    )
    return inner, wrapped


class TestBodyCeilingBeforeTheParse:
    def test_without_the_ceiling_the_whole_body_is_parsed_before_the_413(self, tmp_path):
        # The measured defect: the route's Content-Length pre-check runs after
        # FastAPI parsed the multipart body, so 50 MiB are consumed for a 1 MiB limit.
        inner, _wrapped = _limited_app(tmp_path)
        probe = asyncio.run(_Probe(_multipart_parts(50 * MIB), declare_length=True).run(inner))
        assert probe.status == 413
        assert probe.consumed == probe.total

    def test_a_declared_oversized_body_is_refused_before_a_byte_is_read(self, tmp_path):
        _inner, wrapped = _limited_app(tmp_path)
        probe = asyncio.run(_Probe(_multipart_parts(50 * MIB), declare_length=True).run(wrapped))
        assert probe.status == 413
        assert probe.consumed == 0
        assert b"REQUEST_BODY_TOO_LARGE" in probe.body
        assert probe.headers["connection"] == "close"

    def test_a_chunked_oversized_body_stops_at_the_ceiling(self, tmp_path):
        # No Content-Length: the counted receive aborts the parse once the body
        # passes the ceiling (plus at most the one chunk that crossed it).
        _inner, wrapped = _limited_app(tmp_path)
        chunk = 64 * 1024
        probe = asyncio.run(_Probe(_multipart_parts(50 * MIB, chunk), declare_length=False).run(wrapped))
        assert probe.status == 413
        assert b"REQUEST_BODY_TOO_LARGE" in probe.body
        assert probe.consumed <= request_body_limit_bytes(1) + chunk
        assert probe.consumed < probe.total

    def test_a_body_that_lies_about_its_length_is_still_cut(self, tmp_path):
        # A Content-Length below the ceiling does not buy more bytes than the ceiling.
        _inner, wrapped = _limited_app(tmp_path)
        probe = _Probe(_multipart_parts(50 * MIB), declare_length=False)
        scope = probe.scope()
        scope["headers"].append((b"content-length", b"1024"))
        asyncio.run(wrapped(scope, probe.receive, probe.send))
        assert probe.status == 413
        assert probe.consumed <= request_body_limit_bytes(1) + 64 * 1024

    def test_a_file_of_exactly_the_file_limit_still_uploads(self, tmp_path):
        # Compatibility: the ceiling carries the per-file limit plus its framing.
        _inner, wrapped = _limited_app(tmp_path)
        filler = MIB - len(_make_jpeg())
        for declare in (True, False):
            probe = asyncio.run(_Probe(_multipart_parts(filler), declare_length=declare).run(wrapped))
            assert probe.status == 201, probe.body

    def test_between_file_limit_and_ceiling_the_route_answers_its_typed_413(self, tmp_path):
        # The bounded read in the route still holds the exact file limit.
        _inner, wrapped = _limited_app(tmp_path)
        probe = asyncio.run(_Probe(_multipart_parts(MIB + 1024), declare_length=False).run(wrapped))
        assert probe.status == 413
        assert b"FILE_TOO_LARGE" in probe.body

    def test_the_ceiling_is_the_edge_proxy_ceiling(self):
        assert BODY_HEADROOM_BYTES == MIB
        assert request_body_limit_bytes(25) == 26 * MIB


class TestSpoolBudget:
    def test_a_second_upload_waits_for_the_first_and_gets_503_when_the_wait_runs_out(self, tmp_path):
        # Budget for one body at the ceiling: the second concurrent chunked upload
        # (which reserves the whole ceiling) cannot start while the first spools.
        _inner, wrapped = _limited_app(tmp_path, budget_bytes=request_body_limit_bytes(1), wait=0.2)

        async def scenario() -> tuple[_Probe, _Probe]:
            gate = asyncio.Event()
            first = _Probe(_multipart_parts(MIB // 2), declare_length=False, gate=gate)
            second = _Probe(_multipart_parts(MIB // 2), declare_length=False)
            task = asyncio.create_task(first.run(wrapped))
            await asyncio.sleep(0.01)
            await second.run(wrapped)
            gate.set()
            await task
            return first, second

        first, second = asyncio.run(scenario())
        assert first.status == 201, first.body
        assert second.status == 503
        assert second.consumed == 0
        assert b"UPLOAD_CAPACITY_EXHAUSTED" in second.body
        assert second.headers["retry-after"] == "1"

    def test_a_waiting_upload_runs_once_the_budget_frees(self, tmp_path):
        _inner, wrapped = _limited_app(tmp_path, budget_bytes=request_body_limit_bytes(1), wait=5.0)

        async def scenario() -> tuple[_Probe, _Probe]:
            gate = asyncio.Event()
            first = _Probe(_multipart_parts(MIB // 2), declare_length=False, gate=gate)
            second = _Probe(_multipart_parts(MIB // 4), declare_length=False)
            task = asyncio.create_task(first.run(wrapped))
            await asyncio.sleep(0.01)
            waiting = asyncio.create_task(second.run(wrapped))
            await asyncio.sleep(0.1)
            assert second.status is None
            gate.set()
            await asyncio.gather(task, waiting)
            return first, second

        first, second = asyncio.run(scenario())
        assert (first.status, second.status) == (201, 201)
        assert wrapped.budget.in_use_bytes == 0

    def test_the_budget_is_released_when_the_body_is_refused(self, tmp_path):
        _inner, wrapped = _limited_app(tmp_path)
        asyncio.run(_Probe(_multipart_parts(5 * MIB), declare_length=False).run(wrapped))
        assert wrapped.budget.in_use_bytes == 0

    def test_a_single_body_larger_than_the_budget_still_runs_alone(self):
        budget = SpoolBudget(10)
        share = budget.share_for(100)
        assert share == 10
        assert budget.try_reserve(share)
        assert not budget.try_reserve(1)
        budget.release(share)
        assert budget.in_use_bytes == 0


class TestNonMultipartRequests:
    def test_json_bodies_are_bounded_but_take_no_spool_budget(self):
        seen: list[int] = []

        async def echo(scope, receive, send):
            body = b""
            while True:
                message = await receive()
                body += message.get("body", b"")
                if not message.get("more_body"):
                    break
            seen.append(len(body))
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        wrapped = RequestBodyLimitMiddleware(echo, max_body_bytes=100, spool_budget_bytes=1, spool_wait_seconds=0)

        async def call(payload: bytes) -> int | None:
            status: dict[str, int] = {}
            sent = False

            async def receive():
                nonlocal sent
                if sent:
                    return {"type": "http.disconnect"}
                sent = True
                return {"type": "http.request", "body": payload, "more_body": False}

            async def send(message):
                if message["type"] == "http.response.start":
                    status["code"] = message["status"]

            scope = {
                "type": "http",
                "method": "POST",
                "path": "/api/v1/x",
                "raw_path": b"/api/v1/x",
                "query_string": b"",
                "headers": [(b"content-type", b"application/json")],
                "client": ("127.0.0.1", 1),
                "server": ("testserver", 80),
                "scheme": "http",
                "root_path": "",
            }
            await wrapped(scope, receive, send)
            return status.get("code")

        assert asyncio.run(call(b"x" * 100)) == 200
        assert asyncio.run(call(b"x" * 101)) == 413
        assert seen == [100]
        assert wrapped.budget.in_use_bytes == 0


class TestProductionWiring:
    @pytest.fixture
    def production_app(self) -> FastAPI:
        from app.main import app

        return app

    def test_the_production_app_carries_the_middleware_with_the_configured_ceiling(self, production_app):
        from app.config.settings import settings

        layers = [m for m in production_app.user_middleware if m.cls is RequestBodyLimitMiddleware]
        assert len(layers) == 1
        assert layers[0].kwargs["max_body_bytes"] == request_body_limit_bytes(settings.storage_max_file_size_mb)
        assert layers[0].kwargs["spool_budget_bytes"] == settings.upload_spool_budget_mb * MIB
        # Innermost user middleware: its answers pass security headers, request ID, CORS, metrics.
        assert production_app.user_middleware[-1].cls is RequestBodyLimitMiddleware
