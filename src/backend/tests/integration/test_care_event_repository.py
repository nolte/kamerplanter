"""REQ-053 WP 4.1 (#2400) — the care log against a real ArangoDB.

What no double can decide, measured here: that the document and its edges are written in **one** transaction,
that a supersede sets ``superseded_by_key`` and inserts the successor atomically (and refuses a branch), that
the tenant predicate of every read really hides a foreign tenant's events, that the redaction touches the whole
chain and writes its audit row in the same transaction, and that the retention sweep anonymises exactly the
expired rows and never selects them again.

Every "nothing is there" assertion is paired with the positive control in the same test — the tenant's own row
read through the same path — so an empty answer cannot be a reader that sees nothing at all.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.common.exceptions import DuplicateError, NotFoundError, PlanError
from app.data_access.arango import collections as col
from app.data_access.arango.care_event_repository import ArangoCareEventRepository
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.domain.interfaces.care_event_repository import CareEventFilter
from app.domain.models.care_event import ANONYMIZED_MARKER, REDACTED, CareEvent
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("care_event_repository")
A, B = "ten_a", "ten_b"
USER = "u_sabine"
NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)

_DOCUMENTS = (
    col.CARE_EVENTS,
    col.SITES,
    col.LOCATIONS,
    col.PLANT_INSTANCES,
    col.TASKS,
    col.USERS,
    col.GARDEN_PLAN_AUDIT,
)
_EDGES = (col.CARE_EVENT_AT, col.CARE_EVENT_FOR, col.TASK_LOGGED_AS)


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _DOCUMENTS:
        db.create_collection(name)
    for name in _EDGES:
        db.create_collection(name, edge=True)
    yield db
    system.delete_database(TEST_DATABASE)


@pytest.fixture
def db(database):
    for entry in database.collections():
        if not entry["system"]:
            database.collection(entry["name"]).truncate()
    database.collection(col.USERS).insert({"_key": USER, "display_name": "Sabine"})
    database.collection(col.SITES).insert(
        {"_key": "site_a", "tenant_key": A, "name": "A", "type": "outdoor", "plan": {"plan_revision": 7}}
    )
    database.collection(col.SITES).insert({"_key": "site_b", "tenant_key": B, "name": "B", "type": "outdoor"})
    for key, tenant in (("pi_1", A), ("pi_2", A), ("pi_b", B)):
        database.collection(col.PLANT_INSTANCES).insert(
            {"_key": key, "tenant_key": tenant, "location_key": "bed" if tenant == A else "bed_b"}
        )
    return database


@pytest.fixture
def repo(db) -> ArangoCareEventRepository:
    return ArangoCareEventRepository(db)


def event(tenant: str = A, **overrides) -> CareEvent:
    data = {
        "tenant_key": tenant,
        "site_key": "site_a" if tenant == A else "site_b",
        "location_key": "bed" if tenant == A else "bed_b",
        "category": "watering",
        "summary": "Watered",
        "performed_at": NOW - timedelta(days=1),
        "performed_by_user_key": USER,
        "created_by": USER,
        **overrides,
    }
    return CareEvent(**data)


def edges(db, collection: str) -> list[dict]:
    return list(db.collection(collection).all())


class TestInsert:
    def test_the_document_and_all_its_edges_are_written_together(self, db, repo) -> None:
        stored = repo.insert(event(plant_keys=["pi_1", "pi_2"], task_key="task_9", reason="dry"), tenant_key=A)

        assert stored.key and stored.created_at is not None
        assert db.collection(col.CARE_EVENTS).get(stored.key)["reason"] == "dry"
        (at,) = edges(db, col.CARE_EVENT_AT)
        assert (at["_from"], at["_to"]) == (f"care_events/{stored.key}", "locations/bed")
        assert sorted(e["_to"] for e in edges(db, col.CARE_EVENT_FOR)) == [
            "plant_instances/pi_1",
            "plant_instances/pi_2",
        ]
        (logged,) = edges(db, col.TASK_LOGGED_AS)
        assert (logged["_from"], logged["_to"]) == ("tasks/task_9", f"care_events/{stored.key}")

    def test_a_source_ref_is_unique_per_tenant_when_the_index_exists(self, db, repo) -> None:
        db.collection(col.CARE_EVENTS).add_persistent_index(
            fields=col.CARE_EVENT_SOURCE_REF_INDEX_FIELDS, unique=True, sparse=True
        )
        ref = {"collection": "watering_events", "key": "we_1"}
        repo.insert(event(source_ref=ref), tenant_key=A)

        with pytest.raises(DuplicateError):
            repo.insert(event(source_ref=ref), tenant_key=A)
        repo.insert(event(source_ref=None), tenant_key=A)
        repo.insert(event(source_ref=None), tenant_key=A)
        assert len(list(db.collection(col.CARE_EVENTS).all())) == 3
        assert len(edges(db, col.CARE_EVENT_AT)) == 3  # the refused insert left no edge behind


class TestTheTenantPredicate:
    def test_a_foreign_event_is_invisible_to_every_read(self, db, repo) -> None:
        mine = repo.insert(event(), tenant_key=A)
        theirs = repo.insert(event(B), tenant_key=B)

        assert repo.get(mine.key, tenant_key=A) is not None  # the positive control
        assert repo.get(theirs.key, tenant_key=A) is None
        assert repo.get_row(theirs.key, tenant_key=A) is None
        assert repo.chain(theirs.key, tenant_key=A) == []
        keys = [row.event.key for row in repo.list_events(CareEventFilter(), tenant_key=A, offset=0, limit=50)]
        assert keys == [mine.key]
        assert repo.plants_in_locations(["pi_1", "pi_b"], ["bed", "bed_b"], tenant_key=A) == {"pi_1"}

    def test_an_empty_tenant_is_refused(self, repo) -> None:
        with pytest.raises(ValueError, match="tenant_key"):
            repo.get("x", tenant_key="")


class TestList:
    def test_newest_first_with_names_filters_and_paging(self, repo) -> None:
        old = repo.insert(
            event(performed_at=NOW - timedelta(days=5), category="feeding", plant_keys=["pi_1"]), tenant_key=A
        )
        new = repo.insert(event(performed_at=NOW - timedelta(days=1)), tenant_key=A)
        labelled = repo.insert(
            event(performed_at=NOW - timedelta(days=3), performed_by_user_key=None, performed_by_label="neighbour"),
            tenant_key=A,
        )

        rows = repo.list_events(CareEventFilter(), tenant_key=A, offset=0, limit=50)
        assert [r.event.key for r in rows] == [new.key, labelled.key, old.key]
        assert rows[0].performed_by_name == "Sabine" and rows[1].performed_by_name is None

        assert [
            r.event.key for r in repo.list_events(CareEventFilter(category="feeding"), tenant_key=A, offset=0, limit=9)
        ] == [old.key]
        assert [
            r.event.key for r in repo.list_events(CareEventFilter(plant_key="pi_1"), tenant_key=A, offset=0, limit=9)
        ] == [old.key]
        assert [
            r.event.key for r in repo.list_events(CareEventFilter(performed_by=USER), tenant_key=A, offset=0, limit=9)
        ] == [new.key, old.key]
        window = CareEventFilter(performed_from=NOW - timedelta(days=4), performed_to=NOW - timedelta(days=2))
        assert [r.event.key for r in repo.list_events(window, tenant_key=A, offset=0, limit=9)] == [labelled.key]
        assert [r.event.key for r in repo.list_events(CareEventFilter(), tenant_key=A, offset=1, limit=1)] == [
            labelled.key
        ]


class TestPlantNames:
    def test_list_and_single_reads_name_the_plants_and_skip_foreign_ones(self, db, repo) -> None:
        """#2514: ``plant_name``, else ``instance_id``, in ``plant_keys`` order; a foreign or gone plant is left out."""
        plants = db.collection(col.PLANT_INSTANCES)
        plants.update({"_key": "pi_1", "instance_id": "TOM-1"})
        plants.update({"_key": "pi_2", "instance_id": "TOM-2", "plant_name": "Black Krim"})
        plants.update({"_key": "pi_b", "instance_id": "THEIRS"})
        moved = repo.insert(
            event(category="position_corrected", plant_keys=["pi_2", "pi_b", "pi_gone", "pi_1"]), tenant_key=A
        )
        bare = repo.insert(event(performed_at=NOW - timedelta(days=2)), tenant_key=A)

        rows = {r.event.key: r for r in repo.list_events(CareEventFilter(), tenant_key=A, offset=0, limit=50)}
        assert rows[moved.key].plant_names == ("Black Krim", "TOM-1")
        assert rows[bare.key].plant_names == ()
        row = repo.get_row(moved.key, tenant_key=A)
        assert row is not None and row.plant_names == ("Black Krim", "TOM-1")


class TestSupersede:
    def test_the_successor_and_the_pointer_are_written_atomically(self, db, repo) -> None:
        first = repo.insert(event(plant_keys=["pi_1"]), tenant_key=A)

        second = repo.supersede(first.key, event(supersedes_key=first.key, summary="Corrected"), tenant_key=A)

        assert repo.get(first.key, tenant_key=A).superseded_by_key == second.key
        assert repo.get(first.key, tenant_key=A).summary == "Watered"  # the old entry stays as it was
        assert [e.key for e in repo.chain(second.key, tenant_key=A)] == [first.key, second.key]
        assert [e.key for e in repo.chain(first.key, tenant_key=A)] == [first.key, second.key]
        listed = repo.list_events(CareEventFilter(), tenant_key=A, offset=0, limit=50)
        assert [r.event.key for r in listed] == [second.key]

    def test_a_correction_of_a_task_entry_does_not_link_the_task_twice(self, db, repo) -> None:
        first = repo.insert(event(task_key="task_9", trigger="task"), tenant_key=A)

        second = repo.supersede(
            first.key, event(supersedes_key=first.key, task_key="task_9", trigger="task"), tenant_key=A
        )

        assert second.task_key == "task_9"  # shown on the correction ...
        (logged,) = edges(db, col.TASK_LOGGED_AS)  # ... but the task is logged as the first entry only
        assert logged["_to"] == f"care_events/{first.key}"

    def test_a_correction_that_names_another_bed_or_tenant_is_refused(self, db, repo) -> None:
        first = repo.insert(event(), tenant_key=A)
        documents = len(list(db.collection(col.CARE_EVENTS).all()))

        with pytest.raises(PlanError):
            repo.supersede(first.key, event(supersedes_key=first.key, location_key="other_bed"), tenant_key=A)
        with pytest.raises(ValueError, match="another tenant"):
            repo.supersede(first.key, event(B, supersedes_key=first.key), tenant_key=A)

        assert len(list(db.collection(col.CARE_EVENTS).all())) == documents

    def test_a_branch_is_refused_and_writes_nothing(self, db, repo) -> None:
        first = repo.insert(event(), tenant_key=A)
        repo.supersede(first.key, event(supersedes_key=first.key), tenant_key=A)
        documents, at_edges = len(list(db.collection(col.CARE_EVENTS).all())), len(edges(db, col.CARE_EVENT_AT))

        with pytest.raises(PlanError) as exc:
            repo.supersede(first.key, event(supersedes_key=first.key), tenant_key=A)

        assert exc.value.error_code == "care_event.sequence"
        assert len(list(db.collection(col.CARE_EVENTS).all())) == documents
        assert len(edges(db, col.CARE_EVENT_AT)) == at_edges

    def test_a_foreign_predecessor_is_not_found_and_writes_nothing(self, db, repo) -> None:
        theirs = repo.insert(event(B), tenant_key=B)
        documents = len(list(db.collection(col.CARE_EVENTS).all()))

        with pytest.raises(NotFoundError):
            repo.supersede(theirs.key, event(supersedes_key=theirs.key), tenant_key=A)

        assert len(list(db.collection(col.CARE_EVENTS).all())) == documents
        assert repo.get(theirs.key, tenant_key=B).superseded_by_key is None


class TestVoid:
    def test_sets_the_three_columns_and_nothing_else(self, repo) -> None:
        stored = repo.insert(event(summary="Keep me"), tenant_key=A)

        voided = repo.void(stored.key, tenant_key=A, voided_by="u_lead", reason="duplicate", at=NOW)

        assert (voided.voided_by, voided.void_reason, voided.voided_at) == ("u_lead", "duplicate", NOW)
        assert voided.summary == "Keep me" and voided.performed_by_user_key == USER

    def test_a_voided_or_foreign_event_is_refused(self, repo) -> None:
        stored = repo.insert(event(), tenant_key=A)
        theirs = repo.insert(event(B), tenant_key=B)
        repo.void(stored.key, tenant_key=A, voided_by=USER, reason="undo", at=NOW)

        with pytest.raises(PlanError):
            repo.void(stored.key, tenant_key=A, voided_by=USER, reason="again", at=NOW)
        with pytest.raises(NotFoundError):
            repo.void(theirs.key, tenant_key=A, voided_by=USER, reason="x", at=NOW)
        assert repo.get(theirs.key, tenant_key=B).voided_at is None


class TestRedact:
    def test_the_whole_chain_is_redacted_and_audited_in_one_transaction(self, db, repo) -> None:
        first = repo.insert(
            event(summary="Frau Mueller", reason="Nachbarin", photo_refs=["att_1", "att_2"]), tenant_key=A
        )
        second = repo.supersede(
            first.key, event(supersedes_key=first.key, summary="Frau Mueller 2", photo_refs=["att_1"]), tenant_key=A
        )
        bystander = repo.insert(event(summary="Unrelated"), tenant_key=A)

        repo.void(second.key, tenant_key=A, voided_by="u_lead", reason="Frau Mueller war es", at=NOW)

        events, detached = repo.redact(second.key, tenant_key=A, redacted_by="u_lead", reason="names a person", at=NOW)

        assert sorted(e.key for e in events) == sorted([first.key, second.key])
        assert detached == ["att_1", "att_2"]
        for key in (first.key, second.key):
            stored = repo.get(key, tenant_key=A)
            assert (stored.summary, stored.photo_refs, stored.redacted_by) == (REDACTED, [], "u_lead")
        assert repo.get(first.key, tenant_key=A).reason == REDACTED
        assert repo.get(second.key, tenant_key=A).void_reason == REDACTED
        assert repo.get(bystander.key, tenant_key=A).summary == "Unrelated"
        (audit,) = db.collection(col.GARDEN_PLAN_AUDIT).all()
        assert (audit["op"], audit["entity"], audit["key"], audit["revision"], audit["tenant_key"]) == (
            "redact",
            "care_event",
            second.key,
            7,
            A,
        )
        assert audit["summary"] == "watering"  # the category, never the text

    def test_a_foreign_event_is_not_found_and_nothing_changes(self, db, repo) -> None:
        theirs = repo.insert(event(B, summary="Theirs"), tenant_key=B)

        with pytest.raises(NotFoundError):
            repo.redact(theirs.key, tenant_key=A, redacted_by="u_lead", reason="x", at=NOW)

        assert repo.get(theirs.key, tenant_key=B).summary == "Theirs"
        assert list(db.collection(col.GARDEN_PLAN_AUDIT).all()) == []


class TestRetention:
    """NFR-011 R-25 — the sweep anonymises exactly the expired rows, once; the photos go in a second phase."""

    CUTOFF = NOW - timedelta(days=5 * 365)

    def sweep(self, repo, **overrides):
        args = {"cutoff": self.CUTOFF, "pflschg_cutoff": self.CUTOFF, "now": NOW, "batch": 500, **overrides}
        return repo.anonymize_expired(**args)

    def test_expired_rows_lose_persons_and_texts_and_keep_the_cultivation_history(self, db, repo) -> None:
        expired = repo.insert(
            event(
                performed_at=self.CUTOFF - timedelta(days=1),
                summary="Frau Mueller",
                reason="x",
                performed_for_user_key="u_tom",
                plant_keys=["pi_1"],
                quantity=2.0,
                unit="l",
                photo_refs=["att_9"],
            ),
            tenant_key=A,
        )
        fresh = repo.insert(event(performed_at=self.CUTOFF + timedelta(days=1), summary="Recent"), tenant_key=A)

        result = self.sweep(repo)

        assert (result.selected, result.anonymized) == (1, 1)
        assert [(p.event_key, p.tenant_key, p.attachment_ids) for p in result.pending_photos] == [
            (expired.key, A, ("att_9",))
        ]
        gone = repo.get(expired.key, tenant_key=A)
        assert (gone.performed_by_user_key, gone.performed_for_user_key, gone.created_by) == (ANONYMIZED_MARKER,) * 3
        assert (gone.summary, gone.reason) == (REDACTED, REDACTED)
        assert gone.photo_refs == ["att_9"]  # kept until the object is deleted
        assert (gone.category, gone.quantity, gone.location_key, gone.plant_keys) == ("watering", 2.0, "bed", ["pi_1"])
        assert gone.performed_at == expired.performed_at and gone.retention_anonymized_at == NOW
        kept = repo.get(fresh.key, tenant_key=A)
        assert (kept.summary, kept.performed_by_user_key) == ("Recent", USER)

    def test_a_row_whose_photos_are_not_cleared_is_selected_again_and_a_cleared_one_never(self, repo) -> None:
        stored = repo.insert(event(performed_at=self.CUTOFF - timedelta(days=1), photo_refs=["att_9"]), tenant_key=A)

        first = self.sweep(repo)
        again = self.sweep(repo)  # the storage failed: nothing was cleared

        assert (first.anonymized, again.anonymized) == (1, 0)  # anonymised once ...
        assert [p.event_key for p in again.pending_photos] == [stored.key]  # ... and its photos are still pending
        assert repo.clear_photo_refs([stored.key]) == 1
        done = self.sweep(repo)
        assert (done.selected, done.pending_photos) == (0, [])
        assert repo.get(stored.key, tenant_key=A).photo_refs == []

    def test_the_reasons_a_person_typed_are_redacted_but_undo_is_not(self, repo) -> None:
        typed = repo.insert(event(performed_at=self.CUTOFF - timedelta(days=1)), tenant_key=A)
        undone = repo.insert(event(performed_at=self.CUTOFF - timedelta(days=1)), tenant_key=A)
        repo.void(typed.key, tenant_key=A, voided_by="u_lead", reason="Frau Mueller", at=NOW)
        repo.void(undone.key, tenant_key=A, voided_by=USER, reason="undo", at=NOW)

        self.sweep(repo)

        assert repo.get(typed.key, tenant_key=A).void_reason == REDACTED
        assert repo.get(undone.key, tenant_key=A).void_reason == "undo"

    def test_a_pest_control_entry_waits_for_its_later_cutoff(self, repo) -> None:
        general = self.CUTOFF - timedelta(days=1)
        pest = repo.insert(event(performed_at=general, category="pest_control", summary="Sprayed"), tenant_key=A)
        ipm = repo.insert(event(performed_at=general, category="ipm", summary="Released predators"), tenant_key=A)
        plain = repo.insert(event(performed_at=general, summary="Watered"), tenant_key=A)

        result = self.sweep(repo, pflschg_cutoff=self.CUTOFF - timedelta(days=2 * 365))

        assert result.anonymized == 1
        assert repo.get(plain.key, tenant_key=A).summary == REDACTED
        assert repo.get(pest.key, tenant_key=A).summary == "Sprayed"
        assert repo.get(ipm.key, tenant_key=A).summary == "Released predators"

    def test_a_batch_is_bounded(self, repo) -> None:
        for _ in range(3):
            repo.insert(event(performed_at=self.CUTOFF - timedelta(days=1)), tenant_key=A)

        assert self.sweep(repo, batch=2).anonymized == 2
        assert self.sweep(repo, batch=2).anonymized == 1


class TestPlanAuditPurge:
    """NFR-011 R-26."""

    def test_only_rows_older_than_the_cutoff_go_in_bounded_batches(self, db) -> None:
        plan = ArangoGardenPlanRepository(db)
        audit = db.collection(col.GARDEN_PLAN_AUDIT)
        for index, age_days in enumerate((400, 380, 10)):
            audit.insert(
                {
                    "tenant_key": A,
                    "site_key": "site_a",
                    "revision": index,
                    "user_key": USER,
                    "op": "delete",
                    "entity": "location",
                    "key": f"l{index}",
                    "summary": "",
                    "at": (NOW - timedelta(days=age_days)).isoformat(),
                }
            )
        audit.insert(
            {
                "tenant_key": A,
                "site_key": "site_a",
                "revision": 9,
                "user_key": USER,
                "op": "x",
                "entity": "x",
                "key": "k",
                "at": "not a date",
            }
        )
        cutoff = NOW - timedelta(days=365)

        assert plan.purge_audit_before(cutoff, batch=1) == 1
        assert plan.purge_audit_before(cutoff, batch=10) == 1
        assert plan.purge_audit_before(cutoff, batch=10) == 0
        assert sorted(row["key"] for row in audit.all()) == ["k", "l2"]  # the recent row and the unreadable one stay
