"""Prometheus metrics of the API process (#2129, MT-033, NFR-007).

Backend-only (unlike ``error_tracking.py`` this is not a shared copy).

**What is measured.** ``http_request_duration_seconds`` — a histogram per
``method``, ``handler`` and ``status`` — and ``http_requests_total`` with the same
labels, from which the NFR-007 latency percentiles, error rate and throughput
follow; ``http_requests_in_progress`` per method;
and the client library's process/platform/GC collectors (memory, CPU, file
descriptors, the Python version).

**What is never a label.** ``handler`` is the route *pattern* the framework
matched (``/api/v1/t/{tenant_slug}/plants``), never the requested path: the
path carries the tenant slug derived from a person's display name, and on the
attachment route the download token. A request no route matched is
``unmatched`` — a scanner probing random paths cannot grow the series set. A
tenant is not a label either: the per-tenant view is the ``tenant=ten_…`` log
field (#2130); as a label it would multiply every series by the tenant count
and publish the tenant set to anyone who can scrape.

**Where it is served.** On its own listener (``METRICS_PORT``, off when ``0``),
never as a route of the API app. The public ingress reaches the API through
the frontend's nginx on port 8000; the metrics port is not behind it, and the
chart admits only the configured Prometheus to it (``monitoring`` in
``helm/kamerplanter/values.yaml``). The listener is the client library's own
threaded WSGI server: one per process, which matches the single uvicorn
process per pod the image runs.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, MutableMapping
from time import perf_counter
from typing import Any
from wsgiref.simple_server import WSGIServer

import structlog
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, start_http_server
from prometheus_client.gc_collector import GCCollector
from prometheus_client.platform_collector import PlatformCollector
from prometheus_client.process_collector import ProcessCollector
from starlette.routing import compile_path

from app.config.settings import settings

logger = structlog.get_logger(__name__)

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

#: The ``handler`` of a request no route matched (404, a probe, a typo).
UNMATCHED_HANDLER = "unmatched"
#: Methods kept as their own label value; anything else is ``OTHER`` (bounded set).
_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"})

#: The registry the listener serves. Its own rather than the library's global
#: default, so nothing a dependency registers there is published by accident.
REGISTRY = CollectorRegistry(auto_describe=True)
ProcessCollector(registry=REGISTRY)
PlatformCollector(registry=REGISTRY)
GCCollector(registry=REGISTRY)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duration of HTTP requests by method, route pattern and status code (NFR-007).",
    ("method", "handler", "status"),
    registry=REGISTRY,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)
#: The counter NFR-007 §2.1/§2.5 name for error rate and throughput. Equal to the
#: histogram's ``_count``; kept under its own name so the spec's recording rules
#: read as written.
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "HTTP requests by method, route pattern and status code (NFR-007).",
    ("method", "handler", "status"),
    registry=REGISTRY,
)
HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being served, by method.",
    ("method",),
    registry=REGISTRY,
)


#: Per application: ``id(route)`` → the full templates that route is served under.
_TEMPLATES: dict[int, dict[int, list[tuple[re.Pattern[str], str]]]] = {}
#: Per application: route ids the walk did not find, so a miss does not re-walk every request.
_UNKNOWN: dict[int, set[int]] = {}
_MAX_DEPTH = 10


def _walk(routes: Any, prefix: str, depth: int, out: dict[int, list[tuple[re.Pattern[str], str]]]) -> None:
    """Collect the full template of every route, following ``include_router`` inclusions.

    ``include_router`` does not flatten in this FastAPI version: ``app.routes``
    holds an ``_IncludedRouter`` whose ``original_router`` keeps the real routes,
    with the inclusion prefix on ``include_context.prefix`` (the walk
    ``app.main._mounted_paths`` relies on too). The route object a request
    matched — ``scope["route"]`` — carries only the path relative to its router,
    e.g. ``/health/live`` for ``/api/v1/health/live``.
    """
    if depth > _MAX_DEPTH:
        return
    for route in routes or []:
        nested = getattr(route, "original_router", None)
        if nested is not None:
            include_prefix = getattr(getattr(route, "include_context", None), "prefix", "") or ""
            _walk(getattr(nested, "routes", None), prefix + include_prefix, depth + 1, out)
            continue
        path = getattr(route, "path", None)
        if isinstance(path, str) and path.startswith("/"):
            template = prefix + path
            out.setdefault(id(route), []).append((compile_path(template)[0], template))


def _templates_of(app: Any, route: Any) -> list[tuple[re.Pattern[str], str]]:
    table = _TEMPLATES.get(id(app))
    unknown = _UNKNOWN.setdefault(id(app), set())
    if (table is None or id(route) not in table) and id(route) not in unknown:
        table = {}
        _walk(getattr(app, "routes", None), "", 0, table)
        _TEMPLATES[id(app)] = table
        if id(route) not in table:
            unknown.add(id(route))
    return (table or {}).get(id(route), [])


def _handler(scope: Scope) -> str:
    """The full route pattern the framework matched, or :data:`UNMATCHED_HANDLER`.

    One route object can be included under several prefixes; the template whose
    pattern matches the requested path is the one served. Never the path itself.
    """
    route = scope.get("route")
    if route is None:
        return UNMATCHED_HANDLER
    path = str(scope.get("path") or "")
    for pattern, template in _templates_of(scope.get("app"), route):
        if pattern.match(path):
            return template
    relative = getattr(route, "path", None)
    if isinstance(relative, str) and relative.startswith("/"):
        return str(scope.get("root_path") or "") + relative
    return UNMATCHED_HANDLER


class MetricsMiddleware:
    """Pure ASGI middleware recording every HTTP request into :data:`HTTP_REQUEST_DURATION`.

    Pure ASGI rather than ``BaseHTTPMiddleware``: it must not wrap the response
    body, and it reads the route the router recorded on the *same* scope dict
    once the inner app has returned. A request that raised before a response
    started counts as ``500``.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        method = scope.get("method", "")
        method = method if method in _METHODS else "OTHER"
        status = {"code": 500}

        async def send_recording_status(message: Message) -> None:
            if message.get("type") == "http.response.start":
                status["code"] = int(message.get("status", 500))
            await send(message)

        in_progress = HTTP_REQUESTS_IN_PROGRESS.labels(method)
        in_progress.inc()
        started = perf_counter()
        try:
            await self.app(scope, receive, send_recording_status)
        finally:
            in_progress.dec()
            labels = (method, _handler(scope), str(status["code"]))
            HTTP_REQUEST_DURATION.labels(*labels).observe(perf_counter() - started)
            HTTP_REQUESTS_TOTAL.labels(*labels).inc()


def start_metrics_server(port: int, address: str) -> WSGIServer | None:
    """Serve :data:`REGISTRY` on *address*:*port*; ``None`` (and a warning) if the port is taken.

    A failure to bind must not stop the API: metrics are an operational aid, not
    a function of the application.
    """
    try:
        server, _thread = start_http_server(port, addr=address, registry=REGISTRY)
    except OSError as exc:
        logger.warning("metrics_server_not_started", port=port, error=type(exc).__name__)
        return None
    logger.info("metrics_server_started", port=server.server_port)
    return server


def start_configured_metrics_server() -> WSGIServer | None:
    """Start the listener ``METRICS_PORT`` asks for; ``None`` when it is ``0`` (the default)."""
    if settings.metrics_port <= 0:
        return None
    return start_metrics_server(settings.metrics_port, settings.metrics_bind_address)


def stop_metrics_server(server: WSGIServer | None) -> None:
    """Stop a listener :func:`start_metrics_server` started; a no-op for ``None``."""
    if server is None:
        return
    server.shutdown()
    server.server_close()
