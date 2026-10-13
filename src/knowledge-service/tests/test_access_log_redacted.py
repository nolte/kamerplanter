"""The knowledge service's access log carries no question text and no full client IP (#1796 review GDPR-003).

uvicorn's default access log writes ``<ip:port> - "GET /search?q=<question> HTTP/1.1"``
for every search — the question is free text a person typed. The real app
(``app.main:app``, lifespan off so no vector database is needed) is served by a
real uvicorn with uvicorn's own logging config, and the line uvicorn's
``AccessFormatter`` writes is read back.
"""

from __future__ import annotations

import io
import logging
import logging.config
import socket
import threading

import httpx
import pytest
import uvicorn
from uvicorn.config import LOGGING_CONFIG

QUESTION = "Erika Mustermann Musterstrasse 12 welke Tomate"


@pytest.fixture
def access_logger_state():
    access = logging.getLogger("uvicorn.access")
    saved = (list(access.handlers), list(access.filters), access.level, access.propagate)
    yield
    access.handlers, access.filters, access.level, access.propagate = saved[0], saved[1], saved[2], saved[3]


def test_a_search_request_logs_no_question_and_no_full_ip(access_logger_state) -> None:
    from app.main import app

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, lifespan="off", log_config=LOGGING_CONFIG))
    stream = io.StringIO()
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    try:
        thread.start()
        for _ in range(250):
            if server.started:
                break
            threading.Event().wait(0.02)
        assert server.started, "uvicorn did not start"
        (handler,) = logging.getLogger("uvicorn.access").handlers
        assert isinstance(handler, logging.StreamHandler)
        handler.setStream(stream)
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5.0) as client:
            client.get("/search", params={"q": QUESTION})
            client.get("/health")
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()

    text = stream.getvalue()
    assert '"GET /search?<redacted> HTTP/1.1"' in text, text
    assert '"GET /health HTTP/1.1"' in text, text
    for leaked in ("Mustermann", "Tomate", "q=", "127.0.0.1"):
        assert leaked not in text, f"{leaked!r} reached the access log: {text!r}"
    assert "127.0.0.0 - " in text, text


@pytest.mark.parametrize(
    ("client_addr", "expected"),
    [("203.0.113.77:51234", "203.0.113.0"), ("2001:db8:1:2::9:443", "2001:db8:1::"), ("", ""), ("garbage", "0.0.0.0")],
)
def test_the_client_address_is_truncated(client_addr: str, expected: str) -> None:
    from app.access_log import loggable_client_addr

    assert loggable_client_addr(client_addr) == expected


def test_a_record_of_another_shape_is_dropped() -> None:
    from app.access_log import AccessLogRedactionFilter

    record = logging.LogRecord(
        "uvicorn.access", logging.INFO, __file__, 1, "%s %s", ("1.2.3.4", f"/search?q={QUESTION}"), None
    )
    assert AccessLogRedactionFilter().filter(record) is False
