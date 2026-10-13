"""A tenant key inside free log text, and in a Celery task's return value, is masked (#2020).

#1928/#1966 replace the tenant key at log *calls*. Two spellings reach the sink as
text instead, past every call-site rule:

* the tenant-erasure Celery task returns ``{"record_key": "ter_<tenant_key>", …}``;
  Celery logs the return value on its ``Task … succeeded in …`` line (INFO) and as
  ``extra['data']['return_value']`` — the sink withheld only the task's args/kwargs
  (measured before the fix: the key was on the line verbatim);
* an exception text that names a storage object (``t/<tenant_key>/<category>/…``) or
  a prefix (``t/<tenant_key>/``) — a storage adapter's ``OSError`` or ``ClientError``.

Both are driven through the real path: Celery's real tracer under the worker's
logging setup, and the text redaction every sink shares.
"""

from __future__ import annotations

import pytest
from celery import Celery
from celery.app.trace import build_tracer

from app.common import log_privacy
from app.common.log_privacy import log_tenant, loggable_error, loggable_text, redact_text_in_flight
from app.config.settings import settings
from tests.unit.guards.test_log_redaction_has_no_residual_gaps import _late_handler
from tests.unit.guards.test_logs_carry_no_secrets_runtime import (  # noqa: F401  (fixture, used via usefixtures)
    _configure,
    isolated_logging,
)

# Assembled at run time: a literal shaped like a key is reported by the secret scanner.
TENANT_KEY = "-".join(("tenant", "2020", "owner"))
SALT = "-".join(("salt", "for", "the", "log", "pseudonym", "2020", "probe"))


@pytest.fixture(autouse=True)
def _log_salt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "log_pseudonym_salt", SALT)


@pytest.mark.usefixtures("isolated_logging")
def test_the_success_line_of_the_tenant_erasure_task_carries_no_tenant_key() -> None:
    """Celery's real tracer, the task body of ``run_tenant_erasure`` through the real service."""
    from unittest.mock import MagicMock

    from app.domain.services.tenant_service import TenantService

    _configure("worker")
    late = _late_handler("celery.app.trace")
    probe = Celery("probe-2020", broker="memory://", backend="cache+memory://", set_as_current=False)

    service = TenantService.__new__(TenantService)
    repo = MagicMock()
    repo.get.return_value = None
    service._tenant_erasure_repo = repo  # type: ignore[attr-defined]
    service._require_tenant_erasure_repo = lambda: repo  # type: ignore[method-assign]

    @probe.task(name="probe.run_tenant_erasure_2020")
    def run(record_key: str) -> dict[str, object]:
        return service.run_tenant_erasure_task(record_key)

    tracer = build_tracer(run.name, run, app=probe, eager=False, propagate=False, store_errors=False)
    tracer("task-id-2020", (f"ter_{TENANT_KEY}",), {}, {"hostname": "probe@host", "id": "task-id-2020"})

    text = late.stream.getvalue()
    assert "succeeded in" in text, text
    assert TENANT_KEY not in text, text
    assert f"ter_{log_tenant(TENANT_KEY)}" in text, text


@pytest.mark.usefixtures("isolated_logging")
def test_any_task_that_returns_a_record_key_is_masked_at_the_sink() -> None:
    """The sink, not the one task: a return value in the same spelling from another task is masked too."""
    _configure("worker")
    late = _late_handler("celery.app.trace")
    probe = Celery("probe-2020b", broker="memory://", backend="cache+memory://", set_as_current=False)

    @probe.task(name="probe.other_task_2020")
    def other(record_key: str) -> dict[str, object]:
        return {"record_key": record_key, "outcome": "completed"}

    tracer = build_tracer(other.name, other, app=probe, eager=False, propagate=False, store_errors=False)
    tracer("task-id-2020b", (f"ter_{TENANT_KEY}",), {}, {"hostname": "probe@host", "id": "task-id-2020b"})

    text = late.stream.getvalue()
    assert "succeeded in" in text and "completed" in text, text
    assert TENANT_KEY not in text, text


@pytest.mark.parametrize(
    "text",
    [
        f"[Errno 2] No such file or directory: '/data/t/{TENANT_KEY}/photo/2026/10/01ABCDEFGHJKMNPQRSTVWXYZ00.jpg'",
        f"An error occurred (NoSuchKey): key t/{TENANT_KEY}/photo/2026/10/01ABCDEFGHJKMNPQRSTVWXYZ00.jpg",
        f"delete_prefix failed for 't/{TENANT_KEY}/'",
        f"delete_prefix failed for t/{TENANT_KEY}/",
        f"record ter_{TENANT_KEY} failed",
        f"{{'record_key': 'ter_{TENANT_KEY}', 'outcome': 'held'}}",
    ],
)
@pytest.mark.parametrize("sink", [loggable_error, loggable_text, redact_text_in_flight])
def test_free_text_tenant_keys_are_masked(text: str, sink) -> None:  # type: ignore[no-untyped-def]
    masked = sink(text)
    assert TENANT_KEY not in masked, masked
    assert log_tenant(TENANT_KEY) in masked, masked


@pytest.mark.parametrize(
    "text",
    [
        "see /api/v1/t/{tenant_slug}/plants for details",
        "report/t/ is not a key",
        "filter_ter_count=3",
        "a/b/t/c",
    ],
)
def test_text_that_is_no_tenant_key_is_left_alone(text: str) -> None:
    assert loggable_text(text) == text


def test_the_masking_is_idempotent() -> None:
    once = loggable_text(f"ter_{TENANT_KEY} and t/{TENANT_KEY}/photo/2026/10/x.jpg")
    assert loggable_text(once) == once
    assert log_privacy.log_tenant(TENANT_KEY) in once


def test_a_quiet_salt_still_never_names_the_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "log_pseudonym_salt", "")
    masked = loggable_text(f"ter_{TENANT_KEY} t/{TENANT_KEY}/photo/2026/10/x.jpg")
    assert TENANT_KEY not in masked, masked
