"""#2254 — request-body ceiling and upload spool budget at the ASGI boundary.

Measured through raw ASGI calls, not ``TestClient``: the question is how many
body bytes the application pulls from ``receive`` before it answers, and
``TestClient`` hides that. The attachment router runs exactly as mounted in
production (FastAPI parses the multipart body before the route or any
dependency), behind :class:`RequestBodyLimitMiddleware`.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from typing import Any

import pytest
from fastapi import FastAPI
from starlette.datastructures import Headers

from app.common.body_limit import (
    BODY_HEADROOM_BYTES,
    NON_MULTIPART_MAX_BODY_BYTES,
    RequestBodyLimitMiddleware,
    SpoolBudget,
    declared_length,
    is_multipart,
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

    def __init__(
        self,
        parts: list[bytes],
        *,
        declare_length: bool,
        gate: asyncio.Event | None = None,
        gate_at: int = 1,
        content_type: bytes = b"multipart/form-data; boundary=" + BOUNDARY,
        disconnect_at: int | None = None,
    ) -> None:
        self.parts = parts
        self.total = sum(len(p) for p in parts)
        self.declare_length = declare_length
        self.consumed = 0
        self.status: int | None = None
        self.headers: dict[str, str] = {}
        self.body = b""
        self._index = 0
        self._gate = gate
        self._gate_at = gate_at
        self._content_type = content_type
        self._disconnect_at = disconnect_at

    async def receive(self) -> dict[str, Any]:
        if self._gate is not None and self._index == self._gate_at:
            await self._gate.wait()
        if self._index >= len(self.parts) or self._index == self._disconnect_at:
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
            (b"content-type", self._content_type),
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
        assert wrapped.budget.in_use_bytes == 0

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


class TestMultipartClassification:
    @pytest.mark.parametrize(
        ("content_type", "multipart"),
        [
            (b"multipart/form-data; boundary=x", True),
            (b"\xa0multipart/form-data; boundary=x", True),
            (b" multipart/form-data; boundary=x", True),
            (b"application/json", False),
            (b"application/x-www-form-urlencoded", False),
            (b"Multipart/Form-Data; boundary=x", False),
            (b"", False),
        ],
    )
    def test_multipart_is_what_starlette_parses_as_multipart(self, content_type, multipart):
        # SEC-001: one parser for both. ``Multipart/Form-Data`` is not multipart
        # to Starlette either (exact comparison), so it is not spooled there.
        from python_multipart.multipart import parse_options_header

        headers = Headers(raw=[(b"content-type", content_type)])
        assert is_multipart(headers) is multipart
        assert (parse_options_header(content_type)[0] == b"multipart/form-data") is multipart

    def test_a_nbsp_prefixed_multipart_upload_is_counted_and_bounded(self, tmp_path):
        # Regression for SEC-001: ``startswith`` saw no multipart here, Starlette
        # parsed one; the upload must take budget and meet the upload ceiling.
        _inner, wrapped = _limited_app(tmp_path, budget_bytes=request_body_limit_bytes(1), wait=0.0)
        content_type = b"\xa0multipart/form-data; boundary=" + BOUNDARY

        async def scenario() -> tuple[_Probe, int]:
            gate = asyncio.Event()
            probe = _Probe(_multipart_parts(MIB // 2), declare_length=False, gate=gate, content_type=content_type)
            task = asyncio.create_task(probe.run(wrapped))
            await asyncio.sleep(0.05)
            held = wrapped.budget.in_use_bytes
            gate.set()
            await task
            return probe, held

        probe, held = asyncio.run(scenario())
        assert held > 0
        assert probe.status == 201, probe.body
        assert wrapped.budget.in_use_bytes == 0

    def test_a_non_multipart_body_meets_the_one_mib_ceiling(self, tmp_path):
        _inner, wrapped = _limited_app(tmp_path, file_limit_mb=25, budget_bytes=request_body_limit_bytes(25))
        parts = [b"{" + b" " * (NON_MULTIPART_MAX_BODY_BYTES) + b"}"]
        # Declared: refused before a byte is read. Undeclared JSON bodies are cut
        # while read (see TestNonMultipartRequests); this upload route never reads one.
        probe = asyncio.run(_Probe(parts, declare_length=True, content_type=b"application/json").run(wrapped))
        assert probe.status == 413
        assert probe.consumed == 0
        assert b"REQUEST_BODY_TOO_LARGE" in probe.body
        assert NON_MULTIPART_MAX_BODY_BYTES == MIB

    def test_a_body_with_a_garbled_type_is_not_treated_as_an_upload(self, tmp_path):
        # Fail closed: anything that is not multipart to Starlette gets the small
        # ceiling — declared, refused unread; undeclared, Starlette does not parse
        # it as a form at all (the route answers 422 for its missing fields) and
        # nothing is spooled or held.
        _inner, wrapped = _limited_app(tmp_path, file_limit_mb=25, budget_bytes=request_body_limit_bytes(25))
        garbled = b"multipart/form-dat; boundary=" + BOUNDARY
        declared = asyncio.run(
            _Probe(_multipart_parts(2 * MIB), declare_length=True, content_type=garbled).run(wrapped)
        )
        assert (declared.status, declared.consumed) == (413, 0)
        undeclared = asyncio.run(
            _Probe(_multipart_parts(2 * MIB), declare_length=False, content_type=garbled).run(wrapped)
        )
        assert undeclared.status == 422
        assert undeclared.consumed <= MIB + 64 * 1024
        assert wrapped.budget.in_use_bytes == 0


class TestContentLengthParsing:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [(b"10", 10), (b" 10 ", 10), (b"\xb2", None), (b"1\xb2", None), (b"1e3", None), (b"-1", None), (b"", None)],
    )
    def test_only_a_plain_ascii_decimal_counts(self, raw, expected):
        # ``"²".isdigit()`` is True and ``int("²")`` raises: the old check let a
        # superscript through to a 500 in every upload route. Header bytes are
        # latin-1 decoded, so b"\xb2" arrives as "²".
        assert declared_length(Headers(raw=[(b"content-length", raw)])) == expected

    def test_the_route_precheck_does_not_crash_on_a_superscript_length(self):
        from starlette.requests import Request

        from app.common.upload_bounds import declared_content_length

        # Header bytes reach Starlette latin-1 decoded: b"\xb2" is "²".
        request = Request({"type": "http", "headers": [(b"content-length", b"\xb2")], "query_string": b""})
        assert declared_content_length(request) is None


class TestSpoolBudget:
    def test_a_body_that_cannot_get_budget_gets_503_with_retry_after_and_close(self, tmp_path):
        # Budget of one ceiling (3 MiB file + 1 MiB): the first upload holds 3 MiB
        # of received bytes; the second needs more than the 1 MiB left.
        _inner, wrapped = _limited_app(tmp_path, file_limit_mb=3, budget_bytes=request_body_limit_bytes(3), wait=0.2)

        async def scenario() -> tuple[_Probe, _Probe]:
            gate = asyncio.Event()
            first_parts = _multipart_parts(3 * MIB - 10 * 1024)
            first = _Probe(first_parts, declare_length=False, gate=gate, gate_at=len(first_parts) - 1)
            second = _Probe(_multipart_parts(2 * MIB), declare_length=False)
            task = asyncio.create_task(first.run(wrapped))
            await asyncio.sleep(0.2)
            await second.run(wrapped)
            gate.set()
            await task
            return first, second

        first, second = asyncio.run(scenario())
        assert first.status == 201, first.body
        assert second.status == 503
        assert b"UPLOAD_CAPACITY_EXHAUSTED" in second.body
        assert second.headers["retry-after"] == "1"
        assert second.headers["connection"] == "close"
        assert second.consumed < second.total
        assert wrapped.budget.in_use_bytes == 0

    def test_an_announced_body_that_never_arrives_holds_no_budget(self, tmp_path):
        # SEC-002: budget follows received bytes, not Content-Length.
        _inner, wrapped = _limited_app(tmp_path, budget_bytes=request_body_limit_bytes(1))

        async def scenario() -> int:
            gate = asyncio.Event()
            stalled = _Probe(_multipart_parts(MIB // 2), declare_length=True, gate=gate, gate_at=0)
            task = asyncio.create_task(stalled.run(wrapped))
            await asyncio.sleep(0.05)
            held = wrapped.budget.in_use_bytes
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            return held

        assert asyncio.run(scenario()) == 0
        assert wrapped.budget.in_use_bytes == 0

    def test_a_waiting_upload_runs_once_the_budget_frees(self, tmp_path):
        _inner, wrapped = _limited_app(tmp_path, file_limit_mb=3, budget_bytes=request_body_limit_bytes(3), wait=5.0)

        async def scenario() -> tuple[_Probe, _Probe]:
            gate = asyncio.Event()
            first_parts = _multipart_parts(3 * MIB - 10 * 1024)
            first = _Probe(first_parts, declare_length=False, gate=gate, gate_at=len(first_parts) - 1)
            second = _Probe(_multipart_parts(2 * MIB), declare_length=False)
            task = asyncio.create_task(first.run(wrapped))
            await asyncio.sleep(0.2)
            waiting = asyncio.create_task(second.run(wrapped))
            await asyncio.sleep(0.2)
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

    def test_the_budget_is_released_when_the_client_disconnects(self, tmp_path):
        _inner, wrapped = _limited_app(tmp_path)
        probe = _Probe(_multipart_parts(MIB // 2), declare_length=False, disconnect_at=3)
        with contextlib.suppress(Exception):
            asyncio.run(probe.run(wrapped))
        assert wrapped.budget.in_use_bytes == 0

    def test_the_budget_is_released_when_the_request_is_cancelled_mid_body(self, tmp_path):
        _inner, wrapped = _limited_app(tmp_path)

        async def scenario() -> int:
            gate = asyncio.Event()
            probe = _Probe(_multipart_parts(MIB // 2), declare_length=False, gate=gate, gate_at=4)
            task = asyncio.create_task(probe.run(wrapped))
            await asyncio.sleep(0.05)
            held = wrapped.budget.in_use_bytes
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            return held

        assert asyncio.run(scenario()) > 0
        assert wrapped.budget.in_use_bytes == 0

    def test_an_under_declared_length_ends_at_the_declared_bytes(self, tmp_path):
        # What a real HTTP/1.1 server does with a Content-Length below the body:
        # it delivers the declared bytes only; the truncated form lacks its file
        # part (422), nothing beyond the declared bytes is read or held.
        _inner, wrapped = _limited_app(tmp_path)
        parts = _multipart_parts(MIB // 2)
        wire = b"".join(parts)[:4096]
        probe = _Probe([wire], declare_length=True)
        asyncio.run(probe.run(wrapped))
        assert probe.status == 422
        assert probe.consumed == 4096
        assert wrapped.budget.in_use_bytes == 0

    def test_a_ceiling_above_the_budget_is_refused_at_construction(self):
        with pytest.raises(ValueError, match="spool budget"):
            RequestBodyLimitMiddleware(
                lambda *a: None, max_body_bytes=2 * MIB, spool_budget_bytes=MIB, spool_wait_seconds=0
            )

    def test_a_settings_budget_below_one_full_upload_is_refused_at_load(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="UPLOAD_SPOOL_BUDGET_MB"):
            Settings(storage_max_file_size_mb=60, upload_spool_budget_mb=52)
        assert Settings(storage_max_file_size_mb=51, upload_spool_budget_mb=52).upload_spool_budget_mb == 52

    def test_the_spool_budget_counter(self):
        budget = SpoolBudget(10)
        assert budget.try_reserve(10)
        assert not budget.try_reserve(1)
        budget.release(10)
        assert budget.in_use_bytes == 0


class TestNonMultipartRequests:
    def test_json_bodies_are_bounded_but_take_no_spool_budget(self):
        seen: list[int] = []
        held: list[int] = []

        async def echo(scope, receive, send):
            body = b""
            while True:
                message = await receive()
                body += message.get("body", b"")
                if not message.get("more_body"):
                    break
            seen.append(len(body))
            held.append(wrapped.budget.in_use_bytes)
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b""})

        wrapped = RequestBodyLimitMiddleware(
            echo, max_body_bytes=100, spool_budget_bytes=100, spool_wait_seconds=0, non_multipart_max_body_bytes=50
        )

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

        assert asyncio.run(call(b"x" * 50)) == 200
        assert asyncio.run(call(b"x" * 51)) == 413
        assert seen == [50]
        assert held == [0]
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


def test_an_oversized_pest_image_is_a_413_not_a_422():
    """SEC-007: the pest-detection size check answers like every other upload limit."""
    from app.common.exceptions import PayloadTooLargeError
    from app.config.settings import settings
    from app.domain.services.pest_detection_service import PestDetectionService

    too_large = b"\xff" * (settings.pest_detection_max_image_size_mb * MIB + 1)
    with pytest.raises(PayloadTooLargeError) as caught:
        PestDetectionService._validate_size(too_large)
    assert caught.value.status_code == 413
    assert caught.value.error_code == "PAYLOAD_TOO_LARGE"
