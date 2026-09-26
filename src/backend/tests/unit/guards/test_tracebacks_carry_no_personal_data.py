"""No traceback in any log sink carries a subject key, an address or a secret (#1796).

``loggable_error`` redacts an exception text handed to a log call — but the same
exception also reaches the log as a **traceback**, whose last line is that text
unredacted: structlog's ``format_exc_info`` rendered it for every
``logger.exception(...)`` / ``exc_info=True`` site, and the stdlib formatters of
uvicorn (``Exception in ASGI application``) and Celery (``Task … raised
unexpected: %(exc)s`` plus its traceback) rendered it for errors no log call in
this tree ever sees. A ``NotFoundError("User", <key>)`` names the account key; an
httpx error names the request URL with the API key in its query.

These tests go through the real paths — structlog's processor chain in the API
and the worker configuration, a real uvicorn server whose app raises, and
Celery's real tracer (``celery.app.trace.build_tracer``) failing a task under
the worker's logging setup — and read what the real handlers write.
"""

from __future__ import annotations

import io
import logging
import socket
import threading
from typing import Any

import httpx
import pytest
import structlog
from celery import Celery
from celery.app.trace import build_tracer
from uvicorn.config import LOGGING_CONFIG

from app.common.exceptions import NotFoundError
from app.config.logging import setup_logging
from tests.unit.guards.test_logs_carry_no_secrets_runtime import (  # noqa: F401  (fixture, used via usefixtures)
    _configure,
    isolated_logging,
)

pytestmark = pytest.mark.usefixtures("isolated_logging")

SUBJECT_KEY = "user-key-1796"
API_KEY = "SECRET-APPID-1796"
ADDRESS = "alice-1796@example.org"


def _raise_chain() -> None:
    """A domain error naming the subject, caused by an httpx error naming the key, caused by one naming an address."""
    request = httpx.Request("GET", f"https://api.openweathermap.org/data/2.5/forecast?lat=52.5&appid={API_KEY}")
    try:
        try:
            raise ValueError(f"recipient {ADDRESS} refused")
        except ValueError as exc:
            raise httpx.ConnectError(f"cannot reach {request.url}", request=request) from exc
    except httpx.ConnectError as exc:
        raise NotFoundError("User", SUBJECT_KEY) from exc


def _assert_redacted(text: str, *, whole_chain: bool = True) -> None:
    for secret in (SUBJECT_KEY, API_KEY, ADDRESS, "lat=52.5"):
        assert secret not in text, f"{secret!r} reached the log:\n{text}"
    assert "Traceback (most recent call last)" in text, text
    if not whole_chain:
        return
    assert "NotFoundError" in text and "ENTITY_NOT_FOUND" in text, text
    assert "ConnectError" in text and "api.openweathermap.org/data/2.5/forecast" in text, text


def _root_stream() -> io.StringIO:
    stream = io.StringIO()
    (handler,) = logging.getLogger().handlers[:1]
    assert isinstance(handler, logging.StreamHandler)
    handler.setStream(stream)
    return stream


@pytest.mark.parametrize("process", ["api", "worker"])
def test_a_structlog_exception_renders_a_redacted_traceback(process: str) -> None:
    capture = _configure(process)

    try:
        _raise_chain()
    except NotFoundError:
        structlog.get_logger("app.probe").exception("probe_failed_1796")

    text = "\n".join(capture.lines)
    assert "probe_failed_1796" in text
    _assert_redacted(text.encode().decode("unicode_escape"))


@pytest.mark.parametrize("process", ["api", "worker"])
def test_a_stdlib_exception_through_the_root_handler_is_redacted(process: str) -> None:
    """A library's own ``logger.exception`` (no structlog) is rendered by the process's real root handler."""
    _configure(process)
    stream = _root_stream()

    try:
        _raise_chain()
    except NotFoundError as exc:
        logging.getLogger("somelib").error("failed on %s: %s", ADDRESS, exc, exc_info=True)

    _assert_redacted(stream.getvalue())


def test_a_real_uvicorn_server_logs_a_redacted_asgi_traceback() -> None:
    """``Exception in ASGI application`` — written by uvicorn.error, rendered by uvicorn's own handler."""
    import uvicorn

    async def asgi(scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            _raise_chain()

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
        (handler,) = logging.getLogger("uvicorn").handlers
        assert isinstance(handler, logging.StreamHandler)
        handler.setStream(stream)
        setup_logging(False)  # the lifespan runs after uvicorn configured its loggers
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5.0) as client:
            assert client.get("/probe").status_code == 500
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()

    text = stream.getvalue()
    assert "Exception in ASGI application" in text, text
    _assert_redacted(text)


def test_a_failed_celery_task_logs_a_redacted_traceback() -> None:
    """``Task … raised unexpected: %(exc)s`` + traceback — Celery's real tracer under the worker's logging setup."""
    _configure("worker")
    stream = _root_stream()

    probe = Celery("probe-1796", set_as_current=False)

    @probe.task(name="probe.fail_1796")
    def fail() -> None:
        _raise_chain()

    tracer = build_tracer(fail.name, fail, app=probe, eager=False, propagate=False, store_errors=False)
    tracer("task-id-1796", (), {}, {"hostname": "probe@host", "id": "task-id-1796"})

    text = stream.getvalue()
    assert "raised unexpected" in text, text
    # Celery hands the logger the exception after a pickle round trip
    # (``get_pickled_exception``): NotFoundError comes back as a bare
    # KamerplanterError without its cause chain — the key must be absent all the same.
    assert "KamerplanterError" in text, text
    _assert_redacted(text, whole_chain=False)


_CACHE_PROBE = """
import gc
from celery.signals import celeryd_init
from structlog._config import BoundLoggerLazyProxy
from app.config.settings import settings
settings.erasure_tombstone_salt = "s" * 40
settings.log_pseudonym_salt = "l" * 40  # #1812 worker gate
import base64
settings.fernet_key = base64.urlsafe_b64encode(bytes(range(32))).decode()  # #1859 worker gate
from app.tasks import celery_app
celery_app.loader.import_default_modules()
celeryd_init.send(sender="probe@host", instance=None, conf=celery_app.conf, options={})
cached = [p for p in gc.get_objects() if isinstance(p, BoundLoggerLazyProxy) and "bind" in vars(p)]
print(len(cached))
"""


def test_no_module_logger_is_cached_before_the_worker_configures_logging() -> None:
    """``cache_logger_on_first_use`` would pin a logger used before ``after_setup_logger`` to structlog's defaults.

    Measured: importing ``app.tasks``, every task module and running the
    ``celeryd_init`` receivers (all of which happen before Celery sets up logging)
    uses no module-level logger — so every task logs through the configured
    chain. A fresh interpreter, because this test process has used (and, after a
    ``setup_logging`` test, cached) loggers already.
    """
    import os
    import subprocess
    import sys

    from tests.unit.guards.test_privacy_logs_carry_no_plaintext_subject import BACKEND_ROOT

    env = {**os.environ, "PYTHONPATH": str(BACKEND_ROOT)}
    probe = subprocess.run(
        [sys.executable, "-W", "ignore", "-c", _CACHE_PROBE],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    assert probe.stdout.strip().splitlines()[-1] == "0", probe.stdout + probe.stderr


def test_a_task_logger_line_is_redacted() -> None:
    """``celery.task`` has its own handler (``setup_task_loggers``) and does not propagate to root."""
    from celery.utils.log import get_task_logger

    _configure("worker")
    handlers = [h for h in logging.getLogger("celery.task").handlers if isinstance(h, logging.StreamHandler)]
    assert handlers, "Celery configured no task-logger stream handler"
    stream = io.StringIO()
    for handler in handlers:
        handler.setStream(stream)

    try:
        _raise_chain()
    except NotFoundError:
        get_task_logger("app.tasks.probe").error("probe for %s failed", ADDRESS, exc_info=True)

    _assert_redacted(stream.getvalue())


# ── review round: fail-closed sink, Unicode (#1795/#1796 review SEC-003, SEC-007) ──


def _real_root_only(process: str) -> io.StringIO:
    """The process's real root handler alone — the test capture handler would format the raw record itself."""
    logging.getLogger().removeHandler(_configure(process))
    return _root_stream()


class _Unprintable:
    def __str__(self) -> str:
        raise RuntimeError("SECRET-in-str-1796")

    __repr__ = __str__


@pytest.mark.parametrize("process", ["api", "worker"])
def test_a_badly_formatted_record_leaks_nothing_to_stdout_or_stderr(
    process: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """``"k=%d" % "SECRET"`` fails in ``getMessage``; stdlib ``handleError`` would print msg and args to stderr."""
    stream = _real_root_only(process)

    logging.getLogger("somelib").error("k=%d", "SECRET-ARG-1796")

    captured = capsys.readouterr()
    for sink in (stream.getvalue(), captured.err, captured.out):
        assert "SECRET-ARG-1796" not in sink, sink
    assert "withheld" in stream.getvalue(), stream.getvalue()


@pytest.mark.parametrize("process", ["api", "worker"])
def test_an_argument_whose_str_raises_does_not_raise_at_the_call_site(
    process: str, capsys: pytest.CaptureFixture[str]
) -> None:
    stream = _real_root_only(process)

    logging.getLogger("somelib").error("value=%s", _Unprintable())  # must not raise

    captured = capsys.readouterr()
    for sink in (stream.getvalue(), captured.err):
        assert "SECRET-in-str-1796" not in sink, sink


def test_a_very_long_exception_chain_renders_without_recursion_error() -> None:
    """The chain renderer is iterative: 5 000 chained exceptions neither raise nor leak."""
    stream = _real_root_only("api")
    exc: BaseException = ValueError(f"root {ADDRESS}")
    for depth in range(5_000):
        nxt = ValueError(f"level {depth} {ADDRESS}")
        nxt.__context__ = exc
        exc = nxt

    logging.getLogger("somelib").error("deep chain", exc_info=(type(exc), exc, None))

    text = stream.getvalue()
    assert ADDRESS not in text
    assert "deep chain" in text


@pytest.mark.parametrize("process", ["api", "worker"])
def test_a_non_ascii_address_in_a_structlog_line_is_masked_at_the_sink(process: str) -> None:
    """``JSONRenderer`` escaped ``ü`` to ``\\u00fc``, which no address pattern recognises (SEC-007)."""
    stream = _real_root_only(process)

    structlog.get_logger("app.probe").warning("probe_unicode_1796", detail="refused max@bücher.de")

    text = stream.getvalue()
    assert "probe_unicode_1796" in text, text
    assert "bücher" not in text and "b\\u00fccher" not in text, text
