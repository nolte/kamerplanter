"""#2138 — the tenant import has a body ceiling of its own; every other route keeps the global one.

``RequestBodyLimitMiddleware`` runs before FastAPI parses (and spools) a multipart body, so the
import's ceiling has to be decided there, from the request line alone: ``POST`` on exactly the
import path gets ``TENANT_IMPORT_MAX_UPLOAD_MB`` + 1 MiB, any other method, path or path variant the
global ``STORAGE_MAX_FILE_SIZE_MB`` + 1 MiB, a non-multipart body 1 MiB everywhere. A route ceiling
above the spool budget is lowered to the budget at start — a body the budget can never hold gets
``413`` with the limit rather than waiting into ``503``.

Measured through raw ASGI calls against an application that reads the whole body (what FastAPI's
form parser does), so the assertion is on how many bytes reached the application before the answer.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from app.common.body_limit import RequestBodyLimitMiddleware, RouteBodyCeiling, request_body_limit_bytes

MIB = 1024 * 1024
IMPORT_PATH = "/api/v1/admin/platform/tenant-imports"
MULTIPART = b"multipart/form-data; boundary=x"


class _Reader:
    """An application that reads the body to the end, then answers 200 with the bytes it got."""

    def __init__(self) -> None:
        self.read = 0

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break
            self.read += len(message.get("body", b""))
            if not message.get("more_body"):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": str(self.read).encode()})


async def _post(
    app: Any,
    *,
    path: str,
    size: int,
    method: str = "POST",
    content_type: bytes = MULTIPART,
    declare: bool = False,
) -> tuple[int, dict[str, Any]]:
    chunk = 256 * 1024
    parts = [b"\0" * min(chunk, size - offset) for offset in range(0, size, chunk)] or [b""]
    index = 0
    status = 0
    body = b""

    async def receive() -> dict[str, Any]:
        nonlocal index
        if index >= len(parts):
            return {"type": "http.disconnect"}
        part = parts[index]
        index += 1
        return {"type": "http.request", "body": part, "more_body": index < len(parts)}

    async def send(message: dict[str, Any]) -> None:
        nonlocal status, body
        if message["type"] == "http.response.start":
            status = message["status"]
        elif message["type"] == "http.response.body":
            body += message.get("body", b"")

    headers = [(b"host", b"testserver"), (b"content-type", content_type)]
    if declare:
        headers.append((b"content-length", str(size).encode()))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 1),
        "server": ("testserver", 80),
        "root_path": "",
    }
    await app(scope, receive, send)
    try:
        payload: dict[str, Any] = json.loads(body) if status != 200 else {"read": int(body)}
    except ValueError:
        payload = {"raw": body.decode(errors="replace")}
    return status, payload


def _app(*, global_mb: int = 1, import_mb: int = 4, budget_mb: int = 64) -> tuple[_Reader, RequestBodyLimitMiddleware]:
    inner = _Reader()
    wrapped = RequestBodyLimitMiddleware(
        inner,
        max_body_bytes=request_body_limit_bytes(global_mb),
        spool_budget_bytes=budget_mb * MIB,
        spool_wait_seconds=0,
        route_ceilings=[
            RouteBodyCeiling(method="POST", path=IMPORT_PATH, max_body_bytes=request_body_limit_bytes(import_mb))
        ],
    )
    return inner, wrapped


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


class TestOnlyTheImportRouteGetsItsCeiling:
    @pytest.mark.parametrize("declare", [True, False], ids=["declared", "chunked"])
    def test_an_archive_above_the_global_ceiling_reaches_the_import(self, declare: bool) -> None:
        inner, app = _app()
        size = 3 * MIB  # above 1 + 1 MiB, below 4 + 1 MiB

        status, payload = _run(_post(app, path=IMPORT_PATH, size=size, declare=declare))

        assert (status, payload) == (200, {"read": size})
        assert app.budget.in_use_bytes == 0  # what the request took is returned

    @pytest.mark.parametrize(
        ("path", "method"),
        [
            ("/api/v1/t/anna/attachments", "POST"),
            (IMPORT_PATH + "/", "POST"),  # a path variant falls back to the global ceiling
            ("/api/v1/admin/platform/tenant-imports/x", "POST"),
            (IMPORT_PATH, "PUT"),
        ],
    )
    def test_every_other_route_keeps_the_global_ceiling(self, path: str, method: str) -> None:
        inner, app = _app()

        status, payload = _run(_post(app, path=path, method=method, size=3 * MIB))

        assert status == 413 and payload["error_code"] == "REQUEST_BODY_TOO_LARGE"
        assert inner.read <= request_body_limit_bytes(1)

    @pytest.mark.parametrize("declare", [True, False], ids=["declared", "chunked"])
    def test_an_archive_above_the_import_ceiling_is_refused_before_it_is_read(self, declare: bool) -> None:
        inner, app = _app()

        status, payload = _run(_post(app, path=IMPORT_PATH, size=6 * MIB, declare=declare))

        assert status == 413 and payload["error_code"] == "REQUEST_BODY_TOO_LARGE"
        assert inner.read <= request_body_limit_bytes(4)
        if declare:
            assert inner.read == 0

    def test_a_body_that_is_no_multipart_keeps_one_mib_on_the_import_route(self) -> None:
        inner, app = _app()

        status, _payload = _run(_post(app, path=IMPORT_PATH, size=2 * MIB, content_type=b"application/json"))

        assert status == 413
        assert inner.read <= MIB


class TestTheSpoolBudgetBoundsTheRouteCeiling:
    def test_a_ceiling_above_the_budget_is_lowered_to_it(self) -> None:
        _inner, app = _app(global_mb=1, import_mb=512, budget_mb=8)

        assert app.route_ceilings[("POST", IMPORT_PATH)] == 8 * MIB

    def test_a_body_above_the_budget_is_413_not_a_wait_into_503(self) -> None:
        inner, app = _app(global_mb=1, import_mb=512, budget_mb=8)

        status, payload = _run(_post(app, path=IMPORT_PATH, size=9 * MIB, declare=True))

        assert status == 413 and payload["error_code"] == "REQUEST_BODY_TOO_LARGE"
        assert inner.read == 0

    def test_an_import_below_the_budget_still_takes_its_bytes_from_it(self) -> None:
        """The ceiling admits the body; the shared budget still counts it (``/tmp`` is shared)."""
        inner, app = _app(global_mb=1, import_mb=512, budget_mb=8)
        seen: list[int] = []
        original = app.budget.try_reserve

        def spying(size: int) -> bool:
            granted = original(size)
            seen.append(app.budget.in_use_bytes)
            return granted

        app.budget.try_reserve = spying  # type: ignore[method-assign]

        status, _payload = _run(_post(app, path=IMPORT_PATH, size=6 * MIB))

        assert status == 200
        assert max(seen) == 6 * MIB  # every received byte was taken from the budget …
        assert app.budget.in_use_bytes == 0  # … and returned when the request ended
