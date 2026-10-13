"""A report-only count must never fail the retention task it reports on (#1806 GDPR-003)."""

from __future__ import annotations

from collections.abc import Callable

import structlog

from app.common.log_privacy import loggable_error

logger = structlog.get_logger(__name__)


def held_undated_count(count: Callable[[], int], *, task: str) -> int | None:
    """Return ``count()``, or ``None`` when the count itself failed.

    The held-count only tells the operator how many records an age selector could
    not judge. A transient database error in that query must not abort the
    deletion work around it, nor discard the stats of work already done.
    """
    try:
        return int(count())
    except Exception as exc:  # noqa: BLE001 - a monitoring counter must not fail the task
        logger.warning("held_undated_count_failed", task=task, error=loggable_error(exc))
        return None
