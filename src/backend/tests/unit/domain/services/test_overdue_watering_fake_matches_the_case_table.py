"""#3135 — the unit fake's overdue selection answers the case table the AQL answers.

The integration twin (``tests/integration/test_overdue_watering_candidates.py``)
asks ArangoDB the same table; see ``tests/support/overdue_watering_cases.py`` for
why the predicate is measured on both sides instead of being described twice.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.models.notification import Notification
from tests.support.overdue_watering_cases import CASES, CUTOFF, CUTOFF_SPELLINGS, LEVEL, TENANT, Case, document
from tests.unit.domain.services.notification_fakes import EscalationNotificationRepo


def _repo_with(*cases: Case) -> EscalationNotificationRepo:
    repo = EscalationNotificationRepo()
    for case in cases:
        row = Notification(**document(case))  # the stored document, as the repository maps it
        repo._store[row.key or ""] = row
    return repo


@pytest.mark.parametrize("cutoff", CUTOFF_SPELLINGS)
@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_overdue_watering_fake_matches_the_case_table(case: Case, cutoff: str) -> None:
    selected = {
        n.key for n in _repo_with(case).find_overdue_watering(datetime.fromisoformat(cutoff), LEVEL, tenant_key=TENANT)
    }

    assert (case.name in selected) is case.selected, case.why


def test_an_empty_tenant_selects_nothing() -> None:
    assert _repo_with(CASES[0]).find_overdue_watering(CUTOFF, LEVEL, tenant_key="") == []
