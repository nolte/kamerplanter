"""No secret reaches a log line through a library's own logging (#1795).

The static guard (``test_logs_carry_no_secrets.py``) sees log calls in this
tree. The three #1795 leaks it cannot see are written by libraries:

* **httpx** logs ``HTTP Request: GET <full URL> "HTTP/1.1 200 OK"`` at INFO on
  the ``httpx`` logger. OpenWeatherMap (``appid=``) and Perenual (``key=``) put
  their API key in the query string, so every weather fetch wrote the key to the
  log — in the API (``setup_logging``) *and* in the Celery worker, which never
  called ``setup_logging`` and whose root logger Celery configures at INFO.
* **uvicorn** logs every request as ``<client ip:port> - "GET <path?query>
  HTTP/1.1" 200`` on ``uvicorn.access``. ``/api/v1/attachments/token/{token}``
  carries a bearer credential in the path; tenant paths carry the tenant slug,
  derived from a person's display name.

These tests drive the real thing: a real ``httpx.Client``/``AsyncClient`` over
``httpx.MockTransport`` (no network), the real ``setup_logging`` for the API and
Celery's real ``app.log.setup`` for the worker — so the ``after_setup_logger``
receiver fires exactly as it does in ``celery -A app.tasks worker`` — and a real
``uvicorn.access`` record built from uvicorn's own ``get_client_addr`` /
``get_path_with_query_string`` and rendered by uvicorn's own logging config and
``AccessFormatter``. Every test restores the global logging state it changed.
"""

from __future__ import annotations

import asyncio
import io
import logging
import logging.config
import os
import warnings
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
import structlog
from celery.app.log import Logging as CeleryLogging
from uvicorn.config import LOGGING_CONFIG
from uvicorn.protocols.utils import get_client_addr, get_path_with_query_string

from app.config.logging import setup_logging

# Probe values are assembled at import time rather than written as literals: a
# literal shaped like a key, a userinfo password or a signed token is reported as
# a leaked credential by the repository's secret scanner (see #1838), although
# none of these values has ever authenticated anything.
API_KEY = "-".join(("SECRET", "OWM", "KEY", "1795"))
USERINFO_PASSWORD = "-".join(("pw", "userinfo", "1795"))
TOKEN = ".".join(("eyJvcCI6ImRvd25sb2FkIn0", "SIGNATURE1795"))
TENANT_SLUG = "max-mustermann-1795"
CLIENT_IP = "203.0.113.77"


@dataclass
class _LoggerState:
    handlers: list[logging.Handler]
    filters: list[Any]
    level: int
    propagate: bool
    disabled: bool


def _all_loggers() -> dict[str, logging.Logger]:
    loggers = {name: obj for name, obj in logging.root.manager.loggerDict.items() if isinstance(obj, logging.Logger)}
    loggers[""] = logging.getLogger()
    return loggers


@pytest.fixture
def isolated_logging() -> Iterator[None]:
    """Snapshot and restore every piece of global logging state the process configs touch."""
    states = {
        name: _LoggerState(list(lg.handlers), list(lg.filters), lg.level, lg.propagate, lg.disabled)
        for name, lg in _all_loggers().items()
    }
    handler_filters = {handler: list(handler.filters) for lg in _all_loggers().values() for handler in lg.handlers}
    structlog_config = structlog.get_config()
    celery_setup = CeleryLogging._setup
    record_factory = logging.getLogRecordFactory()
    environ = dict(os.environ)
    with warnings.catch_warnings():
        yield
    logging.captureWarnings(False)
    for name, lg in _all_loggers().items():
        state = states.get(name)
        if state is None:
            lg.handlers, lg.filters, lg.level, lg.propagate, lg.disabled = [], [], logging.NOTSET, True, False
            continue
        lg.handlers, lg.filters = state.handlers, state.filters
        lg.level, lg.propagate, lg.disabled = state.level, state.propagate, state.disabled
    for handler, filters in handler_filters.items():
        handler.filters = filters
    logging.root.manager._clear_cache()
    structlog.configure(**structlog_config)
    CeleryLogging._setup = celery_setup
    logging.setLogRecordFactory(record_factory)
    os.environ.clear()
    os.environ.update(environ)


class _Capture(logging.Handler):
    """Collects every record's fully formatted text."""

    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.setFormatter(logging.Formatter("%(name)s %(levelname)s %(message)s"))
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


def _api_process() -> None:
    setup_logging(False)


def _worker_process() -> None:
    from app.tasks import celery_app

    CeleryLogging._setup = False
    celery_app.log.setup(loglevel="INFO")


PROCESSES: dict[str, Callable[[], None]] = {"api": _api_process, "worker": _worker_process}


def _configure(process: str) -> _Capture:
    # A fresh process: pytest's own root handlers (and the WARNING level it keeps
    # them at) would turn ``setup_logging``'s ``basicConfig`` into a no-op and hide
    # the API's real INFO root level.
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(logging.WARNING)
    PROCESSES[process]()
    capture = _Capture()
    logging.getLogger().addHandler(capture)
    return capture


def _transport() -> httpx.MockTransport:
    return httpx.MockTransport(lambda request: httpx.Response(200, json={}))


_OWM = "https://api.openweathermap.org/data/2.5/forecast"
_PARAMS = {"lat": "52.5", "lon": "13.4", "appid": API_KEY}


def _sync_fetch() -> None:
    with httpx.Client(transport=_transport()) as client:
        client.get(_OWM, params=_PARAMS)
        client.get(f"https://probe:{USERINFO_PASSWORD}@perenual.example/api/species-list?key={API_KEY}")


def _async_fetch() -> None:
    async def run() -> None:
        async with httpx.AsyncClient(transport=_transport()) as client:
            await client.get(_OWM, params=_PARAMS)

    asyncio.run(run())


FETCHES: dict[str, Callable[[], None]] = {"sync": _sync_fetch, "async": _async_fetch}


def _assert_no_secret(lines: list[str]) -> None:
    leaked = [line for line in lines if API_KEY in line or USERINFO_PASSWORD in line or "lat=52.5" in line]
    assert not leaked, "a secret or a query string reached the log:\n  " + "\n  ".join(leaked)


@pytest.mark.parametrize("fetch", sorted(FETCHES))
@pytest.mark.parametrize("process", sorted(PROCESSES))
def test_an_outbound_request_logs_no_api_key(isolated_logging: None, process: str, fetch: str) -> None:
    capture = _configure(process)

    FETCHES[fetch]()

    _assert_no_secret(capture.lines)
    for name in ("httpx", "httpcore", "urllib3"):
        level = logging.getLogger(name).getEffectiveLevel()
        assert level >= logging.WARNING, f"{process}: {name} logs at {logging.getLevelName(level)}"


@pytest.mark.parametrize("fetch", sorted(FETCHES))
@pytest.mark.parametrize("process", sorted(PROCESSES))
def test_a_lowered_httpx_level_still_logs_no_api_key(isolated_logging: None, process: str, fetch: str) -> None:
    """Defence in depth: whoever lowers ``httpx`` to DEBUG gets the request line without the secret."""
    capture = _configure(process)
    logging.getLogger("httpx").setLevel(logging.DEBUG)

    FETCHES[fetch]()

    request_lines = [line for line in capture.lines if "HTTP Request" in line]
    assert request_lines, "the lowered level emitted no request line — the assertion below would be vacuous"
    assert any("api.openweathermap.org/data/2.5/forecast" in line for line in request_lines), request_lines
    _assert_no_secret(capture.lines)


def test_the_worker_routes_structlog_through_celerys_handler(isolated_logging: None) -> None:
    """``setup_logging`` in the worker must not replace Celery's handler — structlog lines reach it."""
    capture = _configure("worker")

    structlog.get_logger("app.probe").info("worker_probe_1795", n=1)

    assert any("worker_probe_1795" in line for line in capture.lines), capture.lines


def test_importing_the_task_package_configures_no_logging(isolated_logging: None) -> None:
    """The API imports ``app.tasks`` to enqueue — that import must not hijack the API's logging."""
    before = list(logging.getLogger().handlers)
    import app.tasks  # noqa: F401

    assert logging.getLogger().handlers == before


# ── uvicorn access log ──────────────────────────────────────────────────


def _uvicorn_access_stream() -> io.StringIO:
    """uvicorn's own logging config (as ``uvicorn.run`` applies it), its access handler redirected to a buffer."""
    logging.config.dictConfig(LOGGING_CONFIG)
    stream = io.StringIO()
    (handler,) = logging.getLogger("uvicorn.access").handlers
    assert isinstance(handler, logging.StreamHandler)
    handler.setStream(stream)
    return stream


def _log_request(path: str, query: bytes, client: tuple[str, int]) -> None:
    scope: dict[str, Any] = {"type": "http", "client": client, "path": path, "query_string": query, "root_path": ""}
    logging.getLogger("uvicorn.access").info(
        '%s - "%s %s HTTP/%s" %d',
        get_client_addr(scope),  # type: ignore[arg-type]
        "GET",
        get_path_with_query_string(scope),  # type: ignore[arg-type]
        "1.1",
        200,
    )


@pytest.mark.parametrize(
    ("path", "query", "client", "expected"),
    [
        (
            f"/api/v1/attachments/token/{TOKEN}",
            b"download=1",
            (CLIENT_IP, 51234),
            "/api/v1/attachments/token/{}?<redacted>",
        ),
        (f"/api/v1/t/{TENANT_SLUG}/plant-instances/123", b"", (CLIENT_IP, 51234), "/api/v1/t/{}/plant-instances/{}"),
        (
            "/api/v1/auth/password-reset/confirm",
            b"token=" + TOKEN.encode(),
            ("2001:db8:1:2::77", 4431),
            "/api/v1/auth/password-reset/confirm?<redacted>",
        ),
    ],
    ids=["attachment-token", "tenant-slug", "query-ipv6"],
)
def test_the_access_log_carries_no_token_slug_query_or_full_ip(
    isolated_logging: None, path: str, query: bytes, client: tuple[str, int], expected: str
) -> None:
    import app.main  # noqa: F401  (registers the route source, as the ASGI app import does in uvicorn)

    stream = _uvicorn_access_stream()
    setup_logging(False)  # the lifespan runs after uvicorn configured its loggers

    _log_request(path, query, client)

    line = stream.getvalue()
    assert '"GET ' in line and " 200" in line, f"no access line rendered: {line!r}"
    for secret in (TOKEN, TENANT_SLUG, "download=1", "token=", client[0], str(client[1])):
        assert secret not in line, f"{secret!r} reached the access log: {line!r}"
    assert f"GET {expected} HTTP/1.1" in line, line
    assert ("2001:db8:1::" if ":" in client[0] else "203.0.113.0 -") in line, line


def test_a_record_of_another_shape_is_dropped_not_passed_on(isolated_logging: None) -> None:
    """A future uvicorn with a different argument tuple must not bypass the redaction."""
    stream = _uvicorn_access_stream()
    setup_logging(False)

    logging.getLogger("uvicorn.access").info("%s %s", CLIENT_IP, f"/api/v1/attachments/token/{TOKEN}")

    assert stream.getvalue() == ""


def test_a_real_uvicorn_server_logs_the_redacted_line(isolated_logging: None) -> None:
    """End to end: uvicorn's own HTTP protocol writes the access line, the lifespan-installed filter redacts it."""
    import socket
    import threading

    import uvicorn

    import app.main  # noqa: F401  (registers the route source)

    async def asgi(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            return
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b""})

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(asgi, lifespan="off", log_config=LOGGING_CONFIG))
    stream = io.StringIO()
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    try:
        thread.start()
        for _ in range(200):
            if server.started:
                break
            threading.Event().wait(0.02)
        assert server.started, "uvicorn did not start"
        # uvicorn configured its loggers in Config(); the lifespan's setup_logging runs after that.
        (handler,) = logging.getLogger("uvicorn.access").handlers
        assert isinstance(handler, logging.StreamHandler)
        handler.setStream(stream)
        setup_logging(False)
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5.0) as client:
            client.get(f"/api/v1/attachments/token/{TOKEN}", params={"download": "1"})
            client.get(f"/api/v1/t/{TENANT_SLUG}/plant-instances/123")
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()

    lines = stream.getvalue()
    assert '"GET /api/v1/attachments/token/{}?<redacted> HTTP/1.1" 204' in lines, lines
    assert '"GET /api/v1/t/{}/plant-instances/{} HTTP/1.1" 204' in lines, lines
    for secret in (TOKEN, TENANT_SLUG, "download=1", "127.0.0.1"):
        assert secret not in lines, f"{secret!r} reached the access log: {lines!r}"


def test_route_path_templates_cover_the_openapi_paths() -> None:
    """``loggable_path``'s source (a router walk) knows every literal segment the OpenAPI document has.

    The walk reads FastAPI internals (``_IncludedRouter.original_router``); if a
    FastAPI upgrade hides routes from it, this fails instead of the access log
    silently turning every route word into ``{}``.
    """
    from app.main import _route_path_templates, app

    def literal(paths: Any) -> set[str]:
        return {seg for path in paths for seg in path.split("/") if seg and "{" not in seg}

    walked = literal(_route_path_templates(app))
    documented = literal(app.openapi()["paths"])
    assert documented <= walked, sorted(documented - walked)
