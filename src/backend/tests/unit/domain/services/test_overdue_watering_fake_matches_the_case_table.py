"""#3135 — the unit fake's overdue selection answers the case table the AQL answers.

The integration twin (``tests/integration/test_overdue_watering_candidates.py``)
asks ArangoDB the same table; see ``tests/support/overdue_watering_cases.py`` for
why the predicate is measured on both sides instead of being described twice.
"""

from __future__ import annotations

import pytest

from app.domain.models.notification import Notification
from tests.support.overdue_watering_cases import CASES, CUTOFF, LEVEL, TENANT, Case, document
from tests.unit.domain.services.notification_fakes import EscalationNotificationRepo


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_overdue_watering_fake_matches_the_case_table(case: Case) -> None:
    repo = EscalationNotificationRepo()
    row = Notification(**document(case))
    repo._store[row.key or ""] = row

    selected = {n.key for n in repo.find_overdue_watering(CUTOFF, LEVEL, tenant_key=TENANT)}

    assert (case.name in selected) is case.selected, case.why


def test_an_empty_tenant_selects_nothing() -> None:
    repo = EscalationNotificationRepo()
    row = Notification(**document(CASES[0]))
    repo._store[row.key or ""] = row

    assert repo.find_overdue_watering(CUTOFF, LEVEL, tenant_key="") == []
