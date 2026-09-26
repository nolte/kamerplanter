"""The log-sink redaction of #1795/#1796 has no residual gap (#1828, #1831, #1832).

Three gaps the #1796 handler filter left, each driven here through the real path:

* **Late handlers and ``extra=`` data (#1828).** The filter sat on the handlers
  that existed when ``setup_logging`` ran; a handler added afterwards wrote the
  raw record. And Celery attaches the raw task context to its trace records as
  ``extra={'data': context}`` — the unredacted traceback string and the task's
  ``args``/``kwargs`` — which the filter never touched. Redaction now happens where
  the record is created (the record factory) and, for the ``extra`` data, on the
  logger that attaches it, so no handler order matters.
* **Celery's retry line (#1831).** ``raise self.retry(exc=exc)`` logs
  ``Task … retry: Retry in Ns: <repr of exc>`` with no ``exc_info``; the filter
  redacted exception texts only for records carrying one. Measured before the
  fix: the account key of a ``NotFoundError`` reached the worker log.
* **Before the lifespan (#1832).** A settings ``ValidationError`` raised while
  ``app.main`` is imported printed ``input_value=<the raw value>`` to stderr —
  measured with a password-shaped ``ARANGODB_PORT``. And logging was configured
  only in the lifespan.
"""

from __future__ import annotations

import io
import logging
import os
import subprocess
import sys

import pytest
from celery import Celery
from celery.app.trace import build_tracer

from app.common.exceptions import NotFoundError
from app.config import logging as logging_config
from tests.unit.guards.test_logs_carry_no_secrets_runtime import (  # noqa: F401  (fixture, used via usefixtures)
    _configure,
    isolated_logging,
)
from tests.unit.guards.test_privacy_logs_carry_no_plaintext_subject import BACKEND_ROOT

pytestmark = pytest.mark.usefixtures("isolated_logging")

# Assembled at run time: a literal shaped like a credential is reported by the
# repository's secret scanner (BACKEND.md §16.3).
SUBJECT_KEY = "-".join(("acct", "1828", "subject"))
ADDRESS = "@".join(("mira-1828", "example.org"))
SECRET_VALUE = "-".join(("hunter", "1832", "value"))


class _LateHandler(logging.Handler):
    """A handler added AFTER the process configured logging, with a formatter that prints ``extra`` data."""

    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.setFormatter(logging.Formatter("%(name)s %(message)s | data=%(data)s", defaults={"data": "-"}))
        self.stream = io.StringIO()

    def emit(self, record: logging.LogRecord) -> None:
        self.stream.write(self.format(record) + "\n")


def _late_handler(*loggers: str) -> _LateHandler:
    handler = _LateHandler()
    for name in loggers:
        logging.getLogger(name).addHandler(handler)
    return handler


def _assert_clean(text: str) -> None:
    for secret in (SUBJECT_KEY, ADDRESS):
        assert secret not in text, f"{secret!r} reached the log:\n{text}"


def _probe_app() -> Celery:
    return Celery("probe-1828", broker="memory://", backend="cache+memory://", set_as_current=False)


# ── #1828: late handlers and Celery's extra data ──────────────────────────────


@pytest.mark.parametrize("process", ["api", "worker"])
def test_a_handler_added_after_setup_writes_a_redacted_line_and_traceback(process: str) -> None:
    _configure(process)
    # A library's own handler: it runs before root's, so no filter on a root
    # handler (which mutates the shared record) can have redacted it first.
    late = _late_handler("somelib")

    try:
        raise NotFoundError("User", SUBJECT_KEY)
    except NotFoundError as exc:
        logging.getLogger("somelib").error("failed for %s: %s", ADDRESS, exc, exc_info=True)

    text = late.stream.getvalue()
    assert "failed for" in text, text
    assert "ENTITY_NOT_FOUND" in text, text
    _assert_clean(text)


def test_a_failed_task_attaches_no_raw_data_for_any_handler() -> None:
    """Celery's ``_log_error`` passes ``extra={'data': context}``: traceback text, args and kwargs."""
    _configure("worker")
    late = _late_handler("celery.app.trace")
    probe = _probe_app()

    @probe.task(name="probe.fail_1828")
    def fail(address: str, who: str) -> None:
        raise NotFoundError("User", SUBJECT_KEY)

    tracer = build_tracer(fail.name, fail, app=probe, eager=False, propagate=False, store_errors=False)
    tracer("task-id-1828", (ADDRESS,), {"who": SUBJECT_KEY}, {"hostname": "probe@host", "id": "task-id-1828"})

    text = late.stream.getvalue()
    assert "raised unexpected" in text and "data={" in text, text
    assert "'args': '<withheld>'" in text and "'kwargs': '<withheld>'" in text, text
    _assert_clean(text)


# ── #1831: the retry line ─────────────────────────────────────────────────────


def test_a_retry_line_carries_no_exception_text_that_names_the_subject() -> None:
    """``except Exception as exc: raise self.retry(exc=exc)`` — the spelling of every task in ``app/tasks``."""
    _configure("worker")
    late = _late_handler("celery.app.trace")
    probe = _probe_app()

    @probe.task(name="probe.retry_1831", bind=True, max_retries=3)
    def retrying(self) -> None:
        try:
            raise NotFoundError("User", SUBJECT_KEY)
        except NotFoundError as exc:
            raise self.retry(exc=exc, countdown=60) from exc

    tracer = build_tracer(retrying.name, retrying, app=probe, eager=False, propagate=False, store_errors=False)
    tracer("task-id-1831", (), {}, {"hostname": "probe@host", "id": "task-id-1831", "retries": 0})

    text = late.stream.getvalue()
    assert " retry: " in text, text
    _assert_clean(text)


# ── the rule, independent of handler order ────────────────────────────────────


@pytest.mark.parametrize("process", ["api", "worker"])
def test_every_record_is_created_redacted(process: str) -> None:
    """The record factory is the redacting one after either process configured logging."""
    _configure(process)

    assert getattr(logging.getLogRecordFactory(), "_kp_redacting", False)
    for name in logging_config._EXTRA_DATA_LOGGERS:  # noqa: SLF001
        assert logging_config._EXTRAS_FILTER in logging.getLogger(name).filters  # noqa: SLF001


def test_installing_the_record_redaction_twice_wraps_the_factory_once() -> None:
    logging_config.install_record_redaction()
    first = logging.getLogRecordFactory()
    logging_config.install_record_redaction()

    assert logging.getLogRecordFactory() is first


# ── #1832: before the lifespan ────────────────────────────────────────────────


def _python(code: str, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-W", "ignore", "-c", code],
        cwd=BACKEND_ROOT,
        env={**os.environ, "PYTHONPATH": str(BACKEND_ROOT), **env},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_an_invalid_setting_fails_the_import_without_echoing_its_value() -> None:
    result = _python("import app.main", ARANGODB_PORT=SECRET_VALUE)

    assert result.returncode != 0
    assert "SettingsError" in result.stderr and "ARANGODB_PORT" in result.stderr, result.stderr
    assert SECRET_VALUE not in result.stderr + result.stdout, result.stderr
    assert "input_value" not in result.stderr, result.stderr


def test_importing_the_api_configures_redacting_logging() -> None:
    probe = (
        "import logging, structlog, app.main\n"
        "from app.common.log_privacy import redacted_traceback\n"
        "names = [type(p).__name__ for p in structlog.get_config()['processors']]\n"
        "renderer = [p for p in structlog.get_config()['processors'] if type(p).__name__ == 'ExceptionRenderer']\n"
        "print('JSONRenderer' in names, bool(renderer) and renderer[0].format_exception is redacted_traceback,\n"
        "      getattr(logging.getLogRecordFactory(), '_kp_redacting', False))\n"
    )
    result = _python(probe)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "True True True", result.stdout + result.stderr


def test_a_structlog_line_logged_at_import_time_is_already_json() -> None:
    """What ``app.main`` logs at import renders through the configured chain, not structlog's console default."""
    result = _python("import app.main, structlog\nstructlog.get_logger('probe').warning('import_probe_1832')")

    lines = [line for line in (result.stdout + result.stderr).splitlines() if "import_probe_1832" in line]
    assert lines and lines[-1].startswith("{"), result.stdout + result.stderr


# ── review round (#1877) ──────────────────────────────────────────────────────


@pytest.mark.parametrize("process", ["api", "worker"])
def test_a_record_rebuilt_with_make_log_record_is_redacted_by_the_handler_filter(process: str) -> None:
    """``makeLogRecord(d)`` runs the factory on an EMPTY record, then loads ``d``: the handler filter must act."""
    _configure(process)
    record = logging.makeLogRecord(
        {"name": "remote", "levelno": logging.ERROR, "levelname": "ERROR", "msg": f"mail {ADDRESS} failed"}
    )

    logging_config._SINK_FILTER.filter(record)  # noqa: SLF001

    _assert_clean(record.getMessage())


def test_a_failed_task_keeps_no_raw_context_in_the_record_arguments() -> None:
    """Celery passes ONE context dict as the format argument and as ``extra['data']``; both must be redacted."""
    _configure("worker")
    records: list[logging.LogRecord] = []

    class _Keep(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logging.getLogger("celery.app.trace").addHandler(_Keep())
    probe = _probe_app()

    @probe.task(name="probe.fail_args_1877")
    def fail(address: str, who: str) -> None:
        raise ValueError("plain failure")  # a text the message redaction does not change

    tracer = build_tracer(fail.name, fail, app=probe, eager=False, propagate=False, store_errors=False)
    tracer("task-id-1877", (ADDRESS,), {"who": SUBJECT_KEY}, {"hostname": "probe@host", "id": "task-id-1877"})

    failed = [r for r in records if "raised unexpected" in r.getMessage()]
    assert failed, [r.getMessage() for r in records]
    _assert_clean(repr(failed[0].args) + repr(getattr(failed[0], "data", None)))


def test_a_named_tuple_in_extra_does_not_withhold_the_line() -> None:
    from collections import namedtuple

    logging.getLogger().removeHandler(_configure("api"))
    (root_handler,) = logging.getLogger().handlers[:1]
    stream = io.StringIO()
    root_handler.setStream(stream)  # the process's real root handler, which carries the sink filter
    point = namedtuple("point", "a b")

    logging.getLogger("somelib").warning("hello %s", ADDRESS, extra={"pt": point(1, 2)})

    text = stream.getvalue()
    assert "hello" in text and "withheld" not in text, text
    _assert_clean(text)


def test_the_settings_error_carries_no_validation_error_as_its_context() -> None:
    """``raise … from None`` only suppresses the context; a renderer ignoring the flag would print ``input_value``."""
    probe = (
        "import importlib, os\n"
        "s = importlib.import_module('app.config.settings')\n"
        f"os.environ['ARANGODB_PORT'] = {SECRET_VALUE!r}\n"
        "try:\n"
        "    s.load_settings()\n"
        "except s.SettingsError as e:\n"
        "    print(repr(e.__context__), repr(e.__cause__))\n"
    )
    result = _python(probe)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines()[-1] == "None None", result.stdout
