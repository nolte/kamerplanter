"""#1800 class guard: the NFR-011 §3.1 task table names exactly the retention tasks the beat runs.

#1800 measured the table lagging the code in both directions: R-04/R-04a/R-12 were listed
as "not implemented" (or absent) while ``retention.purge_expired_consent_records``,
``retention.anonymize_consent_ips`` and the invitation purge ran. The table is the
operator-facing claim of what is enforced, so it is derived against the beat schedule here:

* every ``retention.*`` beat task appears in a §3.1 row;
* every task name in a §3.1 row is a task registered with Celery and scheduled on the beat.

The table is read as Markdown rows (cells split on ``|``), the task names are the backticked
cells of column 2; the beat is ``celery_app.conf.beat_schedule``. Spellings this does NOT
see: a task that runs from the beat under a non-``retention.`` name and is missing from the
table (R-02/R-03/R-11/R-12 are listed by hand); the *period* column of a row.
"""

from __future__ import annotations

from pathlib import Path

from app.tasks import celery_app

REPO = Path(__file__).resolve().parents[5]
SPEC = next((REPO / "spec" / "nfr").glob("NFR-011_*.md"))


#: ``retention.*`` beat tasks that enforce no period, with the reason they have no §3.1 row.
NOT_A_PERIOD: dict[str, str] = {
    "retention.redispatch_stale_pending_exports": (
        "safety net that re-enqueues an export whose dispatch was lost; it deletes nothing and has no period"
    ),
}


def table_tasks(markdown_lines: list[str]) -> set[str]:
    """Task names from the rows of the §3.1 table, i.e. between its heading and the next one."""
    names: set[str] = set()
    inside = False
    for line in markdown_lines:
        if line.startswith("### "):
            inside = line.startswith("### 3.1 ")
            continue
        if not inside or not line.startswith("| R-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[1].startswith("`") and cells[1].endswith("`"):
            names.add(cells[1].strip("`"))
    return names


def beat_tasks() -> set[str]:
    return {entry["task"] for entry in celery_app.conf.beat_schedule.values()}


def test_every_retention_beat_task_has_a_row():
    listed = table_tasks(SPEC.read_text(encoding="utf-8").splitlines())
    retention = {name for name in beat_tasks() if name.startswith("retention.")} - set(NOT_A_PERIOD)
    assert len(retention) >= 8, "the beat set is derived; a near-empty one would pass vacuously"
    assert not retention - listed, f"retention beat tasks missing from NFR-011 §3.1: {sorted(retention - listed)}"


def test_every_listed_task_is_scheduled():
    listed = table_tasks(SPEC.read_text(encoding="utf-8").splitlines())
    assert len(listed) >= 12, "the table parse found too few rows; the heading or layout changed"
    assert not listed - beat_tasks(), f"§3.1 lists tasks the beat does not run: {sorted(listed - beat_tasks())}"


def test_every_exemption_is_still_a_beat_task():
    assert not set(NOT_A_PERIOD) - beat_tasks(), "an exemption for a task the beat no longer runs is stale"


class TestTheGuardIsNotVacuous:
    def test_a_row_is_read_from_a_table_under_its_heading(self):
        lines = ["### 3.1 Einzel-Tasks", "| R-04 | `retention.x` | täglich |", "### 3.2 Anderes", "| R-05 | `y` | z |"]
        assert table_tasks(lines) == {"retention.x"}

    def test_a_missing_row_is_seen(self):
        assert "retention.purge_expired_consent_records" not in table_tasks(
            ["### 3.1 T", "| R-01 | `retention.a` | x |"]
        )

    def test_the_real_table_carries_the_consent_tasks(self):
        listed = table_tasks(SPEC.read_text(encoding="utf-8").splitlines())
        assert {"retention.purge_expired_consent_records", "retention.anonymize_consent_ips"} <= listed
