import logging
import sys
from collections.abc import Callable
from typing import Any

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


#: Every attribute a plain ``LogRecord`` carries; anything else on a record came in
#: through ``extra=`` (or a formatter's cache) and is read by a formatter that names it.
_STANDARD_RECORD_ATTRIBUTES = frozenset(vars(logging.LogRecord("", logging.INFO, "", 0, "", None, None))) | {
    "message",
    "asctime",
}
#: Marks a record the record factory already redacted (msg, args, traceback).
_REDACTED_MARK = "_kp_redacted"
#: Keys of Celery's ``extra={'data': context}`` (``celery.app.trace``,
#: ``celery.worker.strategy``) that carry the task's raw arguments.
_TASK_ARGUMENT_KEYS = frozenset({"args", "kwargs"})
_WITHHELD = "<withheld>"


def _exceptions_in_flight(record: logging.LogRecord) -> list[BaseException]:
    """The exceptions whose text a record may embed (#1831).

    The record's own ``exc_info``, or — for a line logged *while* an exception is
    handled without ``exc_info`` — the one in flight. That second case is
    Celery's retry line (``Task … retry: Retry in 60s: NotFoundError(…)``), which
    embeds ``safe_repr`` of the original exception with no ``exc_info``: a
    ``celery.exceptions.Retry`` carries that original as ``.exc``.
    """
    exc = record.exc_info[1] if record.exc_info else None
    if exc is None:
        exc = sys.exc_info()[1]
    if exc is None:
        return []
    found = [exc]
    inner = getattr(exc, "exc", None)
    if isinstance(inner, BaseException):
        found.append(inner)
    return found


def _redact_text(text: str, exceptions: list[BaseException]) -> str:
    for exc in exceptions:
        text = redact_exception_texts(text, exc)
    return loggable_text(text)


def _redact_extra(name: str, value: object, exceptions: list[BaseException]) -> object:
    """An ``extra=`` value as a formatter that names it may print it (#1828).

    Celery's ``data`` context holds the raw traceback string and the task's
    ``args``/``kwargs`` (account keys, addresses): the traceback is re-rendered by
    ``redacted_traceback`` (or withheld when no exception is at hand), the
    arguments are withheld, every other text is redacted like a message.
    """
    if isinstance(value, str):
        return _redact_text(value, exceptions)
    if isinstance(value, dict):
        redacted: dict[object, object] = {}
        for key, item in value.items():
            if key in _TASK_ARGUMENT_KEYS:
                redacted[key] = _WITHHELD
            elif key == "traceback" and isinstance(item, str):
                redacted[key] = redacted_traceback(exceptions[0]) if exceptions else _WITHHELD
            else:
                redacted[key] = _redact_extra(f"{name}.{key}", item, exceptions)
        return redacted
    if isinstance(value, list | tuple):
        return type(value)(_redact_extra(name, item, exceptions) for item in value)
    return value


def _redact_extras(record: logging.LogRecord, exceptions: list[BaseException]) -> None:
    for name in [n for n in vars(record) if n not in _STANDARD_RECORD_ATTRIBUTES and n != _REDACTED_MARK]:
        if name == "color_message":
            # uvicorn's colour variant of the format string: it is formatted with
            # the record's ORIGINAL args, which a redaction may have dropped.
            delattr(record, name)
            continue
        setattr(record, name, _redact_extra(name, getattr(record, name), exceptions))


def _withhold(record: logging.LogRecord, failure: Exception) -> None:
    """Fail closed (review SEC-003): replace a record that cannot be redacted by a placeholder."""
    record.msg = f"<log message withheld: {type(failure).__name__} while redacting a {record.name} record>"
    record.args = None
    if record.exc_info or record.exc_text:
        record.exc_text = "<traceback withheld>"
    record.exc_info = None
    record.stack_info = None
    for name in [n for n in vars(record) if n not in _STANDARD_RECORD_ATTRIBUTES and n != _REDACTED_MARK]:
        delattr(record, name)


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
            exceptions = _exceptions_in_flight(record)
            if not getattr(record, _REDACTED_MARK, False):
                self._redact(record, exceptions)
            _redact_extras(record, exceptions)
        # Fail closed (review SEC-003): a record that cannot be rendered — bad
        # format arguments, an argument whose ``__str__`` raises, a pathological
        # exception chain — must neither reach stdlib ``handleError`` (which prints
        # the raw message and arguments to stderr) nor raise inside the caller's
        # log statement. It is replaced by a placeholder naming only what failed.
        except Exception as failure:
            _withhold(record, failure)
        return True

    @staticmethod
    def _redact(record: logging.LogRecord, exceptions: list[BaseException]) -> None:
        if record.exc_info and record.exc_info[1] is not None:
            record.exc_text = redacted_traceback(record.exc_info[1])
        rendered = record.getMessage()
        message = _redact_text(rendered, exceptions)
        if message != rendered:
            record.msg = message
            record.args = None


_URL_FILTER = _UrlRedactionFilter()
_ACCESS_FILTER = _AccessLogRedactionFilter()
_SINK_FILTER = _SinkRedactionFilter()
#: The loggers whose handlers write lines in the API (root from ``basicConfig``,
#: uvicorn's own) and in the worker (root and ``celery.task`` from Celery).
_SINK_LOGGERS = ("", "uvicorn", "uvicorn.error", "celery", "celery.task", "celery.redirected")


#: Loggers that attach raw task data as ``extra={'data': context}`` (#1828).
#: A filter on the *logger* sees the record after ``extra`` is applied and before
#: any handler, so the data is redacted whichever handler writes it.
_EXTRA_DATA_LOGGERS = ("celery.app.trace", "celery.worker.strategy")


class _ExtrasRedactionFilter(logging.Filter):
    """Logger-level: redacts ``extra=`` values before any handler — early or late — sees them (#1828)."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            _redact_extras(record, _exceptions_in_flight(record))
        except Exception as failure:
            _withhold(record, failure)
        return True


_EXTRAS_FILTER = _ExtrasRedactionFilter()


def _redacting_factory(previous: Callable[..., logging.LogRecord]) -> Callable[..., logging.LogRecord]:
    def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = previous(*args, **kwargs)
        if record.name != _UVICORN_ACCESS_LOGGER:
            try:
                _SinkRedactionFilter._redact(record, _exceptions_in_flight(record))
            except Exception as failure:
                _withhold(record, failure)
            setattr(record, _REDACTED_MARK, True)
        return record

    factory._kp_redacting = True  # type: ignore[attr-defined]
    return factory


def install_record_redaction() -> None:
    """Redact every stdlib record where it is created, not where it is written (#1828). Idempotent.

    A handler filter only covers the handlers that exist when it is installed; a
    handler added later — by a library, by an operator's logging config, by a
    test — wrote unredacted lines. The record factory runs for every record of
    every logger, before any handler: the message, its arguments and the
    traceback (``exc_text``, which every ``logging.Formatter`` prints instead of
    rendering ``exc_info`` itself) are redacted once, for all handlers.

    What the factory cannot see is ``extra=``: ``Logger.makeRecord`` applies it
    *after* the factory. The two libraries that attach data that way get a
    logger-level filter (:data:`_EXTRA_DATA_LOGGERS`); the handler filter
    (:func:`install_sink_redaction`) stays as the backstop for records made
    elsewhere (``logging.makeLogRecord``) and for other extras.
    """
    current = logging.getLogRecordFactory()
    if not getattr(current, "_kp_redacting", False):
        logging.setLogRecordFactory(_redacting_factory(current))
    for name in _EXTRA_DATA_LOGGERS:
        logging.getLogger(name).addFilter(_EXTRAS_FILTER)


def install_sink_redaction() -> None:
    """Put the redacting filter on every handler of the loggers that write lines (#1796). Idempotent.

    Also installs the record factory and the extras filters
    (:func:`install_record_redaction`), which do not depend on which handlers exist.
    """
    install_record_redaction()
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
