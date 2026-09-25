import logging

import structlog

from app.common.log_privacy import (
    loggable_ip,
    loggable_path,
    loggable_text,
    loggable_url_text,
    redact_exception_texts,
    redacted_traceback,
)

#: Libraries that log every outbound request with its full URL at INFO/DEBUG —
#: query string included, which is where OpenWeatherMap (``appid``) and Perenual
#: (``key``) carry their API key (#1795). httpcore and urllib3 (python-arango
#: talks to ArangoDB through ``requests``) log request targets at DEBUG.
_QUIET_LIBRARY_LOGGERS = ("httpx", "httpcore", "urllib3")
#: The loggers that write those request lines themselves. A logger-level filter
#: only sees records logged *on* that logger, not on its children, hence the
#: concrete ``urllib3.connectionpool``.
_URL_LOGGING_LOGGERS = ("httpx", "urllib3.connectionpool")
_UVICORN_ACCESS_LOGGER = "uvicorn.access"
#: ``client_addr, method, path_with_query, http_version, status_code`` — the
#: argument tuple uvicorn's HTTP protocols hand to ``uvicorn.access``.
_ACCESS_ARGS_LEN = 5


class _UrlRedactionFilter(logging.Filter):
    """Masks every URL userinfo and query string in a library's request line (#1795).

    Defence in depth behind the WARNING level: whoever lowers ``httpx`` to INFO
    or DEBUG to debug a weather fetch gets the host and path, never the API key.
    The record is rendered once and its arguments dropped, so the filter holds
    whatever type httpx hands over (an ``httpx.URL``, a ``str``).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except TypeError, ValueError:
            return False
        record.msg = loggable_url_text(message)
        record.args = None
        return True


def _loggable_client_addr(client_addr: object) -> str:
    """uvicorn's ``host:port`` reduced to the truncated host; the port is dropped."""
    text = str(client_addr or "")
    if not text:
        return text
    host, _sep, port = text.rpartition(":")
    if not host or not port.isdigit():
        host = text
    return loggable_ip(host) or ""


class _AccessLogRedactionFilter(logging.Filter):
    """Rewrites the arguments of a ``uvicorn.access`` record before any formatter sees them (#1795).

    The client address becomes its NFR-011 R-03 truncation without the port; the
    path keeps only the app's literal route segments and loses its query string
    (``loggable_path``). A record of another shape is dropped rather than passed
    on unredacted — uvicorn's own ``AccessFormatter`` could not render it anyway.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if not isinstance(args, tuple) or len(args) != _ACCESS_ARGS_LEN:
            return False
        client_addr, method, path, http_version, status_code = args
        record.args = (_loggable_client_addr(client_addr), method, loggable_path(str(path)), http_version, status_code)
        return True


class _SinkRedactionFilter(logging.Filter):
    """The handler-level backstop: what a stdlib handler writes is redacted, whoever logged it (#1796).

    Installed on the handlers, not the loggers, because a logger filter never
    sees a record propagated from a child logger. For every record:

    * a record with ``exc_info`` gets ``exc_text`` from ``redacted_traceback`` —
      ``logging.Formatter`` uses a set ``exc_text`` instead of rendering the
      traceback itself, so uvicorn's ``Exception in ASGI application`` and
      Celery's task-failure traceback come out redacted;
    * every ``repr``/``str`` of that exception inside the rendered message
      (Celery's ``%(exc)s``) is replaced by its loggable text;
    * the whole rendered message goes through ``loggable_text`` (addresses, URL
      userinfo/queries/fragments, export-bundle keys).

    ``uvicorn.access`` records are left alone: their argument tuple is what
    uvicorn's ``AccessFormatter`` unpacks, and ``_AccessLogRedactionFilter``
    already reduced it.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == _UVICORN_ACCESS_LOGGER:
            return True
        try:
            self._redact(record)
        # Fail closed (review SEC-003): a record that cannot be rendered — bad
        # format arguments, an argument whose ``__str__`` raises, a pathological
        # exception chain — must neither reach stdlib ``handleError`` (which prints
        # the raw message and arguments to stderr) nor raise inside the caller's
        # log statement. It is replaced by a placeholder naming only what failed.
        except Exception as failure:
            record.msg = f"<log message withheld: {type(failure).__name__} while redacting a {record.name} record>"
            record.args = None
            if record.exc_info or record.exc_text:
                record.exc_text = "<traceback withheld>"
            record.exc_info = None
            record.stack_info = None
        return True

    @staticmethod
    def _redact(record: logging.LogRecord) -> None:
        exc = record.exc_info[1] if record.exc_info else None
        if exc is not None:
            record.exc_text = redacted_traceback(exc)
        rendered = record.getMessage()
        message = redact_exception_texts(rendered, exc) if exc is not None else rendered
        message = loggable_text(message)
        if message != rendered:
            record.msg = message
            record.args = None


_URL_FILTER = _UrlRedactionFilter()
_ACCESS_FILTER = _AccessLogRedactionFilter()
_SINK_FILTER = _SinkRedactionFilter()
#: The loggers whose handlers write lines in the API (root from ``basicConfig``,
#: uvicorn's own) and in the worker (root and ``celery.task`` from Celery).
_SINK_LOGGERS = ("", "uvicorn", "uvicorn.error", "celery", "celery.task", "celery.redirected")


def install_sink_redaction() -> None:
    """Put the redacting filter on every handler of the loggers that write lines (#1796). Idempotent."""
    for name in _SINK_LOGGERS:
        for handler in logging.getLogger(name).handlers:
            handler.addFilter(_SINK_FILTER)


def harden_library_loggers() -> None:
    """Keep secrets out of the request lines libraries log themselves (#1795).

    Runs in the API (``setup_logging`` from the lifespan, after uvicorn has
    configured its loggers) and in the Celery worker and beat (``after_setup_logger``
    in :mod:`app.tasks`). Idempotent: a filter instance is added at most once.

    * httpx, httpcore and urllib3 at WARNING — their INFO/DEBUG request lines
      carry the full URL, query string included;
    * a URL-redacting filter on the loggers that write those lines, so a later
      lowering of the level still leaks nothing;
    * a redacting filter on ``uvicorn.access``, whose lines carry the attachment
      download token, the tenant slug and the full client address.
    """
    for name in _QUIET_LIBRARY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    for name in _URL_LOGGING_LOGGERS:
        logging.getLogger(name).addFilter(_URL_FILTER)
    logging.getLogger(_UVICORN_ACCESS_LOGGER).addFilter(_ACCESS_FILTER)
    install_sink_redaction()


def setup_logging(debug: bool = False) -> None:
    log_level = logging.DEBUG if debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            # Not ``format_exc_info``: its traceback ends in the raw exception
            # text — the subject key a NotFoundError names, the URL an httpx
            # error carries (#1796).
            structlog.processors.ExceptionRenderer(redacted_traceback),
            structlog.processors.UnicodeDecoder(),
            # ``ensure_ascii=False``: an escaped ``b\u00fccher.de`` is invisible to
            # the sink's address masking (review SEC-007). stdout/stderr are UTF-8.
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # A no-op when the root logger already has handlers — which is what the
    # Celery worker relies on: Celery configured root first, structlog lines
    # reach its handler through the stdlib LoggerFactory.
    logging.basicConfig(format="%(message)s", level=log_level)
    harden_library_loggers()
