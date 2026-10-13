"""#1784 — ``anonymize_old_ips`` reaches the database only through the refresh-token repository.

The task used to run its own AQL against ``get_db()`` (a data-access concern in
the task layer, NFR-001) with a string comparison on ``created_at``. The
selection now lives in :meth:`ArangoRefreshTokenRepository.list_unanonymized_ips_before`,
measured against a real ArangoDB in
``tests/integration/test_retention_instant_comparisons.py``; this file pins the
wiring: the cutoff the task hands over, and that every selected session is
written back anonymised with one shared timestamp.

#1782 — the period is NFR-011 R-03 ``RETENTION_IP_ANONYMIZATION_DAYS``, read
through :class:`RetentionService`; the task carried a literal
``timedelta(days=7)`` no setting reached.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common import dependencies
from app.config.settings import settings
from app.domain.services.retention_service import RetentionService
from app.tasks import auth_tasks

#: Slack for the wall clock between the task's ``now`` and the test's.
_CLOCK_SLACK = timedelta(seconds=30)


class _RecordingRepo:
    def __init__(self, rows: list[tuple[str, str]]) -> None:
        self._rows = rows
        self.cutoffs: list[str] = []
        self.written: list[tuple[str, str, str]] = []

    def list_unanonymized_ips_before(self, cutoff_iso: str) -> list[tuple[str, str]]:
        self.cutoffs.append(cutoff_iso)
        return list(self._rows)

    def mark_ip_anonymized(self, key: str, anonymized_ip: str, anonymized_at_iso: str) -> None:
        self.written.append((key, anonymized_ip, anonymized_at_iso))


@pytest.fixture
def repo(monkeypatch) -> _RecordingRepo:
    recording = _RecordingRepo([("s1", "192.0.2.42"), ("s2", "2001:db8:85a3:1::1")])
    monkeypatch.setattr(dependencies, "get_refresh_token_repo", lambda: recording)
    return recording


def test_every_selected_session_is_written_back_anonymised(repo: _RecordingRepo):
    result = auth_tasks.anonymize_old_ips()

    assert result == {"anonymized": 2}
    assert [(key, ip) for key, ip, _ in repo.written] == [("s1", "192.0.2.0"), ("s2", "2001:db8:85a3::")]
    assert len({stamp for _, _, stamp in repo.written}) == 1


def test_the_cutoff_is_seven_days_before_now(repo: _RecordingRepo):
    before = datetime.now(UTC)
    auth_tasks.anonymize_old_ips()
    after = datetime.now(UTC)

    (cutoff,) = repo.cutoffs
    assert before - timedelta(days=7) <= datetime.fromisoformat(cutoff) <= after - timedelta(days=7)


def test_a_configured_period_moves_the_cutoff(monkeypatch, repo: _RecordingRepo):
    """The task reads the R-03 period from the retention service it is wired to."""
    monkeypatch.setattr(dependencies, "get_retention_service", lambda: RetentionService(ip_anonymisation_after_days=3))

    auth_tasks.anonymize_old_ips()

    (cutoff,) = repo.cutoffs
    expected = datetime.now(UTC) - timedelta(days=3)
    assert abs(datetime.fromisoformat(cutoff) - expected) < _CLOCK_SLACK


def test_the_setting_reaches_the_cutoff(monkeypatch, repo: _RecordingRepo):
    """End to end from ``settings.retention_ip_anonymization_days`` to the selection."""
    monkeypatch.setattr(settings, "retention_ip_anonymization_days", 4)

    auth_tasks.anonymize_old_ips()

    (cutoff,) = repo.cutoffs
    expected = datetime.now(UTC) - timedelta(days=4)
    assert abs(datetime.fromisoformat(cutoff) - expected) < _CLOCK_SLACK


def test_the_cutoff_is_written_in_utc(repo: _RecordingRepo):
    auth_tasks.anonymize_old_ips()

    (cutoff,) = repo.cutoffs
    assert datetime.fromisoformat(cutoff).utcoffset() == timedelta(0)


def test_the_task_holds_no_database_handle_of_its_own(monkeypatch, repo: _RecordingRepo):
    def _no_db():
        raise AssertionError("anonymize_old_ips must not open the database itself")

    monkeypatch.setattr(dependencies, "get_db", _no_db)

    assert auth_tasks.anonymize_old_ips() == {"anonymized": 2}
