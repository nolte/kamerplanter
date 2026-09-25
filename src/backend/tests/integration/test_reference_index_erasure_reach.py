"""#1753 — the self-service Art. 17 erasure reaches the recognition reference index.

Sibling of ``test_self_service_erasure_reach.py``. That module leaves the
reference-index phase unwired; this one wires it **the way the product does**,
through ``get_reference_index_store()`` with ``inference_service_enabled`` set,
and puts an inference-service double behind the real HTTP client
(``tests/support/fake_inference_service.py``: service-token auth, blank-key
refusal, deletes bound to ``source = 'user_contributed'``). Before #1753 the
provider returned the no-op store whatever the setting, so the subject's
contributed vectors outlived the account while the request ended ``completed``.

Evidence is read off the rows — the double's index and the ArangoDB documents —
never off a status field alone:

* after a finished erasure the subject's contributions are gone, another user's
  contribution and a curated row naming the subject remain, and the retained
  erasure record states the binding and the count that ran;
* when the index refuses, the request stays ``partially_completed`` and **no**
  ArangoDB row of the subject has been touched (AK-OS-05: Phase 0.5 before
  Phase 1, failure ⇒ no ArangoDB delete).

The service's SQL itself is pinned in the inference-service suite. Runs against
a real ArangoDB (see ``tests/integration/conftest.py``)::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_reference_index_erasure_reach.py -v
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

# The module, not its names: importing ``test_*`` functions by name would make
# pytest collect the sibling's tests a second time in this module.
import tests.integration.test_account_erasure_reach as reach
from app.common import dependencies
from app.common.dependencies import get_reference_index_store
from app.config.settings import settings
from app.data_access.arango import collections as col
from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.data_access.arango.erasure_repository import ArangoErasureRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.arango.system_settings_repository import ArangoSystemSettingsRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.data_access.vectordb.pest_prototype_stores import NoopPestPrototypeStore
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.system_settings import HomeAssistantSettings, SystemSettings
from app.domain.services.privacy_service import PrivacyService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.fake_inference_service import FakeInferenceService, route_httpx_post_to
from tests.support.tenant_erasure_wiring import tenant_erasure_service

TEST_DATABASE = run_database_name("reference_index_erasure_reach")

SUBJECT = reach.SUBJECT
OTHER = reach.OTHER
SALT = reach.SALT
TOKEN = "reach-service-token-1753"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture
def database():
    """A fresh database per test: each drives the one subject through one erasure."""
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    yield client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def inference(monkeypatch) -> FakeInferenceService:
    """The deployment has the inference-service enabled, with contributions in its index."""
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    monkeypatch.setattr(settings, "inference_service_url", "http://recognition.reach:8000")
    monkeypatch.setattr(settings, "internal_service_token", TOKEN)
    fake = FakeInferenceService(token=TOKEN)
    fake.add(source="user_contributed", contributed_by=SUBJECT, tenant_key=reach.TENANT, record="subject-1")
    fake.add(source="user_contributed", contributed_by=SUBJECT, tenant_key="t-elsewhere", record="subject-2")
    fake.add(source="user_contributed", contributed_by=OTHER, tenant_key=reach.TENANT, record="other")
    fake.add(source="gbif", contributed_by=SUBJECT, tenant_key=reach.TENANT, record="curated")
    route_httpx_post_to(monkeypatch, fake)
    return fake


def _service(database) -> PrivacyService:
    """``get_privacy_service`` for the beat, with the reference-index store from its provider."""
    password_engine = MagicMock()
    password_engine.verify_password.return_value = True
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=ArangoErasureRepository(database),
        email_change_repo=MagicMock(),
        user_repo=ArangoUserRepository(database),
        refresh_token_repo=MagicMock(),
        data_export_engine=MagicMock(),
        erasure_engine=ErasureEngine(),
        consent_engine=MagicMock(),
        password_engine=password_engine,
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="http://localhost",
        membership_repo=ArangoMembershipRepository(database),
        pest_image_repo=ArangoPestImageRepository(database),
        # #1759 — the pest step needs a wired store; no prototype was ever indexed here.
        pest_prototype_store=NoopPestPrototypeStore(),
        reference_index_store=get_reference_index_store(),
        erasure_executor=ArangoErasureExecutor(database),
        # #1788 — the subject's personal tenant goes through the tenant-erasure inventory.
        tenant_service=tenant_erasure_service(database, SALT, reference_index_store=get_reference_index_store()),
        tombstone_salt=SALT,
    )


def _run_beat(database) -> tuple[dict, int, dict]:
    """Seed, file the subject's request, run the daily beat past the grace period."""
    plan = reach._plan()
    seeded = reach._seed(database, plan)
    request = _service(database).request_erasure(SUBJECT, "confirm")
    assert request.key is not None
    # One day past the date the request itself carries: the R-01 period is a
    # setting read through RetentionService (#1782), not a class constant.
    assert request.hard_delete_scheduled_at is not None
    beat_clock = request.hard_delete_scheduled_at + timedelta(days=1)
    finalised = asyncio.run(_service(database).execute_scheduled_erasures(beat_clock))
    record = database.collection(col.ERASURE_REQUESTS).get(request.key)
    return seeded, finalised, record


def test_the_erasure_removes_the_subjects_contributions_and_nothing_else(database, inference):
    _, finalised, record = _run_beat(database)

    assert finalised == 1
    assert inference.records() == {"other", "curated"}
    (request,) = inference.requests
    assert request.url.path == "/reference/contributions/erase-by-contributor"
    assert SUBJECT not in str(request.url)
    assert json.loads(request.content)["contributed_by"] == SUBJECT
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert record["status"] == "completed"
    # The retained record says which index was reached and what it removed.
    assert record["reference_index_binding"] == "inference_service"
    assert record["reference_index_removed"] == 2
    assert database.collection("users").get(SUBJECT) is None


def test_a_refusing_index_keeps_the_duty_open_and_arangodb_untouched(database, inference):
    inference.failure_status = 503

    seeded, finalised, record = _run_beat(database)

    assert finalised == 0
    assert record["status"] == "partially_completed"
    assert record["attempt_count"] == 1
    assert record.get("pre_arango_completed_at") is None
    assert SUBJECT not in (record.get("error_message") or "")
    assert inference.records() == {"subject-1", "subject-2", "other", "curated"}
    # Phase 0.5 failed, so the ArangoDB plan never ran: every row of the
    # subject is still there, unchanged in its owner field.
    missing = [doc_id for ids in seeded[SUBJECT].values() for doc_id in ids if reach._read(database, doc_id) is None]
    assert missing == []
    assert database.collection("users").get(SUBJECT) is not None


# -- GDPR-001/002: the process that erases has no inference-service flag ------


@pytest.fixture
def flagless_process(monkeypatch, database) -> ArangoSystemSettingsRepository:
    """The celery-worker case: the flag is unset here, the marker lives in ArangoDB."""
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    if not database.has_collection(col.SYSTEM_SETTINGS):
        database.create_collection(col.SYSTEM_SETTINGS)
    repository = ArangoSystemSettingsRepository(database)
    monkeypatch.setattr(dependencies, "get_system_settings_repo", lambda: repository)
    return repository


def test_the_marker_is_set_once_and_leaves_the_other_settings_alone(database, flagless_process):
    repository = flagless_process
    repository.upsert(SystemSettings(home_assistant=HomeAssistantSettings(ha_url="http://ha.local")))
    first = datetime(2026, 9, 1, tzinfo=UTC)

    repository.record_reference_contributions(first)
    repository.record_reference_contributions(first + timedelta(days=3))

    stored = repository.get()
    assert stored is not None
    assert stored.reference_contributions_since == first
    assert stored.home_assistant.ha_url == "http://ha.local"
    # A later admin save of the other settings keeps the marker.
    stored.home_assistant.ha_url = "http://ha.changed"
    repository.upsert(stored)
    assert repository.reference_contributions_since() == first


def test_the_marker_is_set_on_an_empty_settings_collection(database, flagless_process):
    at = datetime(2026, 9, 2, tzinfo=UTC)

    flagless_process.record_reference_contributions(at)

    assert flagless_process.reference_contributions_since() == at


def test_a_flagless_process_with_contributions_on_record_holds_the_erasure(database, flagless_process):
    flagless_process.record_reference_contributions(datetime(2026, 9, 1, tzinfo=UTC))

    seeded, finalised, record = _run_beat(database)

    assert finalised == 0
    assert record["status"] == "partially_completed"
    assert record.get("attempt_count", 0) == 0
    assert record.get("pre_arango_completed_at") is None
    assert "INFERENCE_SERVICE_ENABLED" in record["error_message"]
    missing = [doc_id for ids in seeded[SUBJECT].values() for doc_id in ids if reach._read(database, doc_id) is None]
    assert missing == []


def test_a_flagless_process_without_contributions_still_completes(database, flagless_process):
    _, finalised, record = _run_beat(database)

    assert finalised == 1
    assert record["status"] == "completed"
    assert record["reference_index_binding"] == "noop"
