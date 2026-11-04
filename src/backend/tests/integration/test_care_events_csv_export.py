"""WP 8.4 (#2647, GP-FR-104) — the CSV download over the production repository on a real ArangoDB.

The service runs on :class:`ArangoCareEventRepository` (the AQL with ``LIMIT @offset, @limit`` and the display-name
join); the sites and memberships are the in-memory doubles of the API tier. 50 001 stored rows decide the limit.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.common.csv_export import encode_csv
from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.collections import ensure_collections
from app.domain.engines.care_event_csv_engine import CARE_EVENT_CSV_COLUMNS, care_event_csv_rows
from app.domain.interfaces.care_event_repository import CareEventFilter
from app.domain.services.care_event_service import MAX_EXPORT_ROWS, CareEventService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.care_event_fakes import FakeAttachmentRepo, FakeAttachmentService, FakeFertilizers, FakeMemberships
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT, FakeSites, make_site

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the export reads the care log with AQL over a real server"),
]

_DB_NAME = run_database_name("care_events_csv_export")
NOW = datetime.now(UTC)


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    database.collection(col.USERS).insert({"_key": "u_sabine", "display_name": "Sabine"})
    yield database
    system.delete_database(_DB_NAME)


def _service(db) -> CareEventService:  # type: ignore[no-untyped-def]
    return CareEventService(
        ArangoCareEventRepository(db),
        FakeSites(make_site()),
        FakeMemberships(),
        FakeFertilizers(),
        FakeAttachmentRepo(),
        FakeAttachmentService(),
    )


def _event(i: int, tenant: str = TENANT, **extra) -> dict:  # type: ignore[no-untyped-def]
    return {
        "_key": f"e{i:06d}",
        "tenant_key": tenant,
        "site_key": "S1",
        "location_key": "bed",
        "category": "watering",
        "summary": f"entry {i}",
        "performed_at": (NOW - timedelta(minutes=i + 1)).isoformat(),
        "performed_by_user_key": "u_sabine",
        "trigger": "manual",
        "outcome_rating": "unknown",
        **extra,
    }


def _insert(db, docs: list[dict]) -> None:  # type: ignore[no-untyped-def]
    for start in range(0, len(docs), 5000):
        result = db.collection(col.CARE_EVENTS).import_bulk(docs[start : start + 5000])
        assert result["errors"] == 0, result


def _export(service: CareEventService, *, role: TenantRole = TenantRole.GROWER, tenant: str = TENANT, **criteria):  # type: ignore[no-untyped-def]
    return service.export_window(CareEventFilter(**criteria), tenant_key=tenant, user_key="u_sabine", role=role)


def test_the_file_holds_the_entries_with_the_display_name_and_hardened_cells(db) -> None:  # type: ignore[no-untyped-def]
    _insert(
        db, [_event(1, summary="=HYPERLINK(1)"), _event(2, quantity=-1.5, unit="l"), _event(3, tenant=OTHER_TENANT)]
    )

    views = _export(_service(db))
    text = encode_csv(CARE_EVENT_CSV_COLUMNS, care_event_csv_rows(views)).decode("utf-8-sig")

    assert len(views) == 2  # the other tenant's entry is not in it
    assert "'=HYPERLINK(1)" in text and "Sabine" in text and "u_sabine" not in text and ",-1.5," in text


def test_exactly_the_limit_is_a_file_and_one_more_is_422(db) -> None:  # type: ignore[no-untyped-def]
    docs = [_event(i) for i in range(MAX_EXPORT_ROWS)]
    _insert(db, docs)
    service = _service(db)

    assert len(_export(service)) == MAX_EXPORT_ROWS

    _insert(db, [_event(MAX_EXPORT_ROWS)])
    with pytest.raises(PlanError) as refused:
        _export(service)

    assert refused.value.status_code == 422 and refused.value.error_code == "export.too_many_rows"
    # counter-case: narrowing the same data brings it back under the limit
    assert len(_export(service, category="watering", performed_from=NOW - timedelta(minutes=100))) <= 100


def test_a_viewer_filtering_by_another_member_is_forbidden_and_a_foreign_bed_is_404(db) -> None:  # type: ignore[no-untyped-def]
    _insert(db, [_event(1)])
    service = _service(db)

    with pytest.raises(ForbiddenError):
        _export(service, role=TenantRole.VIEWER, performed_by="u_tom")
    with pytest.raises(NotFoundError):
        _export(service, tenant=OTHER_TENANT, location_key="bed")
    assert len(_export(service, role=TenantRole.VIEWER, performed_by="u_sabine")) == 1
