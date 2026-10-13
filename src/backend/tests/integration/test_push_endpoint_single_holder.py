"""#2117 (MT-020): one Web-Push endpoint belongs to one account at a time.

A push endpoint identifies a browser profile on a device, not a person. On a
shared device user A enabled push, logged out, user B logged in and enabled push
again: the browser hands out the **same** endpoint, and ``subscribe_pwa``
deduplicated it only inside B's own preferences. Measured before the change
against a real ArangoDB: A's document still held the endpoint, so the device
received A's notifications **and** B's.

Driven through the real ``NotificationService`` over the real
``ArangoNotificationPreferenceRepository``; only the SSRF resolver is bypassed
(it resolves DNS, and the endpoints here are synthetic).

No personal data: every value is synthetic.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from arango import ArangoClient
from arango.database import StandardDatabase

from app.data_access.arango.notification_preference_repository import (
    NOTIFICATION_PREFERENCES,
    ArangoNotificationPreferenceRepository,
)
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.services import notification_service as notification_module
from app.domain.services.notification_service import NotificationService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("push_single_holder")
SHARED = "https://fcm.googleapis.com/fcm/send/shared-device-2117"
OWN = "https://updates.push.services.mozilla.com/wpush/v2/own-2117"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(NOTIFICATION_PREFERENCES)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def service(database: StandardDatabase, monkeypatch: pytest.MonkeyPatch) -> NotificationService:
    database.collection(NOTIFICATION_PREFERENCES).truncate()
    monkeypatch.setattr(notification_module, "validate_push_endpoint", lambda endpoint: endpoint)
    return NotificationService(
        engine=MagicMock(),
        notification_repo=MagicMock(),
        preference_repo=ArangoNotificationPreferenceRepository(database, EncryptionEngine("")),
    )


def _endpoints(service: NotificationService, user_key: str) -> list[str]:
    pwa = service.get_preferences(user_key).channels.get("pwa")
    return [s["endpoint"] for s in (pwa.config.get("subscriptions", []) if pwa else [])]


def test_subscribing_an_endpoint_another_account_holds_takes_it_from_that_account(
    service: NotificationService,
) -> None:
    service.subscribe_pwa("user-a", SHARED, "pa", "aa")
    service.subscribe_pwa("user-a", OWN, "po", "ao")

    service.subscribe_pwa("user-b", SHARED, "pb", "ab")

    assert _endpoints(service, "user-a") == [OWN]  # A keeps its other device
    assert _endpoints(service, "user-b") == [SHARED]


def test_resubscribing_the_same_account_keeps_one_entry(service: NotificationService) -> None:
    service.subscribe_pwa("user-a", SHARED, "p1", "a1")
    service.subscribe_pwa("user-a", SHARED, "p2", "a2")

    assert _endpoints(service, "user-a") == [SHARED]
