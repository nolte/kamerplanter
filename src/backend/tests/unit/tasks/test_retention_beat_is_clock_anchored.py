"""#1946 — a retention task runs on the clock, not on "N seconds after the beat started".

``"schedule": 86400`` is an interval relative to the beat process's own start (the
beat keeps no persisted schedule in this deployment). Every beat-pod restart — a
rollout, a node drain — restarts the interval, so the policy's "at the latest N+1
days" would only be true if the pod lived that long. A ``crontab`` entry fires on
the wall clock whichever pod happens to be up, which is what the Art. 13 wording
promises. Read from the real ``celery_app.conf.beat_schedule``.
"""

from __future__ import annotations

import pytest
from celery.schedules import crontab

from app.tasks import celery_app

#: The retention tasks the public policy (``retention_summary``) claims a latest point for.
RETENTION_TASKS = {
    "R-02": "app.tasks.auth_tasks.cleanup_unverified_accounts",
    "R-03": "app.tasks.auth_tasks.anonymize_old_ips",
    "R-11": "app.tasks.auth_tasks.cleanup_expired_tokens",
    "R-12": "app.tasks.tenant_tasks.cleanup_expired_invitations",
}


def _entries(task: str) -> list[dict]:
    return [e for e in celery_app.conf.beat_schedule.values() if e["task"] == task]


@pytest.mark.parametrize(("rule", "task"), RETENTION_TASKS.items())
def test_the_retention_task_is_scheduled_on_the_clock(rule, task):
    entries = _entries(task)
    assert len(entries) == 1, rule
    assert isinstance(entries[0]["schedule"], crontab), f"{rule}: {entries[0]['schedule']!r} is a restartable interval"


def test_every_retention_prefixed_task_is_clock_anchored():
    """The sweep, not the list: any ``retention.*`` task added later must not regress to an interval."""
    offenders = [
        name
        for name, entry in celery_app.conf.beat_schedule.items()
        if entry["task"].startswith("retention.") and not isinstance(entry["schedule"], crontab)
    ]
    assert offenders == []


def test_the_hourly_tasks_still_run_every_hour():
    tokens = _entries(RETENTION_TASKS["R-11"])[0]["schedule"]
    assert tokens.hour == set(range(24))  # one run per hour, at a fixed minute
    assert len(tokens.minute) == 1
