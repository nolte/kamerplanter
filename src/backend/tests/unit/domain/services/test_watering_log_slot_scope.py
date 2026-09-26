"""A watering log references only slots of its own tenant — #1871 B4.

``POST /t/{slug}/watering-logs`` took ``slot_keys`` from the body. The service
read the first slot and its location *unscoped* (another tenant's irrigation
system then shaped the returned warnings — an oracle) and the repository wrote
``LOG_SLOT`` edges to every named slot, any tenant's. Each slot is now resolved
through its location's site under the log's tenant before anything is read
through it or written.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import ApplicationMethod
from app.common.exceptions import NotFoundError
from app.domain.engines.watering_engine import WateringEngine
from app.domain.models.watering_log import WateringLog
from app.domain.services.watering_log_service import WateringLogService
from tests.unit.domain.services.test_site_service_location_tenant import OWN, FakeSiteRepo


def _service() -> tuple[WateringLogService, MagicMock]:
    repo = MagicMock()
    repo.create.side_effect = lambda log: log
    return WateringLogService(repo, WateringEngine(), site_repo=FakeSiteRepo()), repo  # type: ignore[arg-type]


def _log(*slots: str) -> WateringLog:
    return WateringLog(
        tenant_key=OWN,
        logged_at=datetime(2026, 9, 26, tzinfo=UTC),
        application_method=ApplicationMethod.DRENCH,
        volume_liters=1.0,
        slot_keys=list(slots),
    )


@pytest.mark.parametrize("slots", [("slot_foreign",), ("slot_own", "slot_foreign"), ("no-such-slot",)])
def test_a_log_naming_a_slot_that_is_not_the_tenants_is_refused(slots: tuple[str, ...]) -> None:
    service, repo = _service()

    with pytest.raises(NotFoundError):
        service.create_log(_log(*slots))

    repo.create.assert_not_called()


def test_a_log_of_own_slots_is_stored() -> None:
    service, repo = _service()

    service.create_log(_log("slot_own"))

    repo.create.assert_called_once()
