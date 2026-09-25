"""#1664 — the platform-admin account delete reaches every step of the declared plan.

Before #1664 the admin route ran the object-storage cleanup and a narrow account
cascade; no path applied ``ANONYMIZE_COLLECTIONS`` or the audit pseudonymisation,
and the ``retention_worker`` entries (consents, export requests, favourites, pest
detections, …) survived the account. Every rule was declared and guarded — and
inert. A unit test can pin that the executor *asks* for each step; only a real
server can say whether each AQL write actually reaches the rows, so this reads
the rows back.

**The seeded collections are derived from the plan**, never listed here: every
``edge`` / ``document`` / ``user`` step and every anonymisation and
pseudonymisation rule gets one row of the subject (A) and one of a second user
(B). A declared shape this module cannot seed raises during seeding — the test
fails, it does not skip. What is asserted:

* every A row of a delete step is gone;
* every A row of a retained collection still exists and no field of it holds A's
  key or A's display text;
* the erasure audit rows carry the ``anon_…`` tombstone hash;
* every B row is byte-for-byte unchanged (``_rev`` included);
* every declared ArangoDB step and every rule reached at least one row.

No status field is read as evidence. The object-storage and reference-index
phases are not ArangoDB collections; they are delegated and covered by the unit
tier.

Runs in CI against a service container; locally it needs a database::

    docker run -d -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_account_erasure_reach.py -v
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient

from app.api.v1.admin.platform import router as admin_router
from app.data_access.arango import collections as col
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.engines.erasure_engine import ANONYMIZED_MARKER, ErasureEngine
from app.domain.models.privacy import ErasurePlan
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.user_service import UserService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("privacy_erasure_reach")

SUBJECT = "user-a"
OTHER = "user-b"
ADMIN = "platform-admin"
#: NFR-011 §4 wants >= 32 characters. Synthetic, test-only.
SALT = "reach-test-salt-not-a-secret-0123456789"
TENANT = "t-reach"

pytestmark = pytest.mark.usefixtures("arango_db")

_GRAPH = {definition["edge_collection"]: definition for definition in col.GRAPH_EDGE_DEFINITIONS}


def _plan() -> ErasurePlan:
    return ErasureEngine().build_erasure_plan(SUBJECT)


def _display_text(owner: str) -> str:
    """A name typed into a free-text field beside the key (``harvester`` …)."""
    return f"Display name of {owner}"


def _row_key(collection: str, owner: str, suffix: str = "") -> str:
    return f"{owner}-{collection}{suffix}".replace("_", "-")


#: Fields a repository on the executing path validates when it reads the row
#: back. Only the shape, never the list of collections: the collections come off
#: the plan. ``pest_image_contributions`` is read through its model by the
#: REQ-010 pest cleanup before the executor runs.
_REQUIRED_SHAPE: dict[str, dict[str, Any]] = {
    "pest_image_contributions": {"tenant_key": TENANT, "pest_key": "pest-1", "attachment_id": "att-1"},
}


def _user_document(owner: str) -> dict[str, Any]:
    return {
        "_key": owner,
        "email": f"{owner}@example.com",
        "display_name": _display_text(owner),
        "password_hash": "not-a-hash",
        "email_verified": True,
        "is_active": True,
        "account_type": "human",
        "created_at": "2026-09-01T00:00:00+00:00",
    }


def _ensure(database, name: str, *, edge: bool = False) -> None:
    if not database.has_collection(name):
        database.create_collection(name, edge=edge)


def _seed(database, plan: ErasurePlan) -> dict[str, dict[str, list[str]]]:
    """One row per owner in every collection the plan declares; returns their ids.

    ``seeded[owner][collection]`` lists the ``_id`` of each row. Raises when a
    declared step has a shape this function does not know, so a new kind of
    step fails the test instead of silently going unseeded.
    """
    seeded: dict[str, dict[str, list[str]]] = {SUBJECT: {}, OTHER: {}}

    def record(owner: str, collection: str, doc_id: str) -> None:
        seeded[owner].setdefault(collection, []).append(doc_id)

    user_steps = [step for step in plan.steps if step.kind == "user"]
    assert len(user_steps) == 1, "the plan must declare exactly one user step"
    users = user_steps[0].collection
    _ensure(database, users)
    for owner in (SUBJECT, OTHER, ADMIN):
        inserted = database.collection(users).insert(_user_document(owner))
        if owner != ADMIN:
            record(owner, users, inserted["_id"])

    # Documents first: a ``via`` edge needs its parent row to exist. A document
    # reached ``via`` a parent (#1700: ``location_assignments`` through
    # ``memberships``) carries the parent row's ``_key`` in its user field, so
    # its parent is seeded before it, whatever the declared order.
    documents = [step for step in plan.steps if step.kind == "document"]
    pending = list(documents)
    while pending:
        ready = [step for step in pending if step.via is None or step.via in seeded[SUBJECT]]
        if not ready:
            raise AssertionError(f"document steps {[s.collection for s in pending]} have an unseedable via chain")
        for step in ready:
            pending.remove(step)
            _ensure(database, step.collection)
            for owner in (SUBJECT, OTHER):
                reference = owner if step.via is None else seeded[owner][step.via][0].split("/", 1)[1]
                doc = {
                    "_key": _row_key(step.collection, owner),
                    step.user_field: reference,
                    "tenant_key": TENANT,
                    "marker": f"marker-{step.collection}-{owner}",
                    **_REQUIRED_SHAPE.get(step.collection, {}),
                    **step.where,
                }
                record(owner, step.collection, database.collection(step.collection).insert(doc)["_id"])

    for step in plan.steps:
        if step.kind != "edge":
            continue
        definition = _GRAPH.get(step.collection)
        if definition is None:
            raise AssertionError(f"edge step '{step.collection}' is not in the named graph; cannot seed it")
        _ensure(database, step.collection, edge=True)
        other_side = "to_vertex_collections" if step.user_field == "_from" else "from_vertex_collections"
        endpoint_side = "from_vertex_collections" if step.user_field == "_from" else "to_vertex_collections"
        opposite = "_to" if step.user_field == "_from" else "_from"
        expected_endpoint = step.via or users
        if expected_endpoint not in definition[endpoint_side]:
            raise AssertionError(f"edge step '{step.collection}' cannot hold {expected_endpoint} on {step.user_field}")
        for owner in (SUBJECT, OTHER):
            if step.via is None:
                endpoint = f"{users}/{owner}"
            else:
                parents = seeded[owner].get(step.via)
                if not parents:
                    raise AssertionError(f"via edge '{step.collection}' has no seeded parent in '{step.via}'")
                endpoint = parents[0]
            edge = {
                "_key": _row_key(step.collection, owner),
                step.user_field: endpoint,
                opposite: f"{definition[other_side][0]}/target-{owner}",
            }
            record(owner, step.collection, database.collection(step.collection).insert(edge)["_id"])

    for rule in plan.anonymize:
        _ensure(database, rule.collection)
        for owner in (SUBJECT, OTHER):
            doc = {
                "_key": _row_key(rule.collection, owner, f"-{rule.user_field}"),
                rule.user_field: owner,
                "tenant_key": TENANT,
                "marker": f"marker-{rule.collection}-{owner}",
            }
            doc.update(dict.fromkeys(rule.clear_fields, _display_text(owner)))
            record(owner, rule.collection, database.collection(rule.collection).insert(doc)["_id"])

    for audit_rule in plan.pseudonymize_audit:
        _ensure(database, audit_rule.collection)
        for owner in (SUBJECT, OTHER):
            doc = {
                "_key": _row_key(audit_rule.collection, owner),
                audit_rule.user_field: owner,
                "marker": f"marker-{audit_rule.collection}-{owner}",
            }
            record(owner, audit_rule.collection, database.collection(audit_rule.collection).insert(doc)["_id"])

    return seeded


def _read(database, doc_id: str) -> dict[str, Any] | None:
    collection, key = doc_id.split("/", 1)
    return database.collection(collection).get(key)


def _snapshot(database, ids: dict[str, list[str]]) -> dict[str, dict[str, Any] | None]:
    return {doc_id: _read(database, doc_id) for doc_ids in ids.values() for doc_id in doc_ids}


def _services(database) -> tuple[PrivacyService, UserService]:
    """The two services the admin route is handed, over the test database."""
    from app.data_access.arango.erasure_executor import ArangoErasureExecutor

    user_repo = ArangoUserRepository(database)
    privacy_service = PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=MagicMock(),
        user_repo=user_repo,
        refresh_token_repo=MagicMock(),
        data_export_engine=MagicMock(),
        erasure_engine=ErasureEngine(),
        consent_engine=MagicMock(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="http://localhost",
        membership_repo=ArangoMembershipRepository(database),
        pest_image_repo=ArangoPestImageRepository(database),
        # #1753 — Phase 0.5 needs a wired store; no contribution is on record here.
        reference_index_store=NoopReferenceIndexStore(),
        erasure_executor=ArangoErasureExecutor(database),
        tombstone_salt=SALT,
    )
    return privacy_service, UserService(user_repo, MagicMock())


def _admin_delete(database, captured: dict[str, Any]) -> None:
    """Drive ``DELETE /admin/platform/users/{key}`` exactly as the router does."""
    privacy_service, user_service = _services(database)
    erase = getattr(privacy_service, "erase_account", None)
    if erase is not None:

        async def spy(user_key: str):
            report = await erase(user_key)
            captured["report"] = report
            return report

        privacy_service.erase_account = spy  # type: ignore[method-assign]
    admin_router.delete_user(
        SUBJECT,
        current_user=SimpleNamespace(key=ADMIN),
        privacy_service=privacy_service,
        user_service=user_service,
    )


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    yield client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    system.delete_database(TEST_DATABASE)


@pytest.fixture(scope="module")
def erased(database):
    """Seed, snapshot B, run the admin delete once; hand back what the tests read."""
    plan = _plan()
    seeded = _seed(database, plan)
    before_other = _snapshot(database, seeded[OTHER])
    captured: dict[str, Any] = {}
    _admin_delete(database, captured)
    return SimpleNamespace(plan=plan, seeded=seeded, before_other=before_other, captured=captured)


def _deleted_collections(plan: ErasurePlan) -> list[str]:
    return [step.collection for step in plan.steps if step.kind in ("edge", "document", "user")]


def _retained_collections(plan: ErasurePlan) -> list[str]:
    names = [rule.collection for rule in plan.anonymize] + [rule.collection for rule in plan.pseudonymize_audit]
    return list(dict.fromkeys(names))


def _retained_rows(plan: ErasurePlan, owner: str) -> list[str]:
    """The ``_id`` of each row seeded for a rule — by key, not by collection.

    Since #1700 a collection can carry a delete step *and* a rule
    (``invitations``: accepted ones go, the inviter reference of the rest is
    replaced; ``attachments``, ``pest_image_contributions``), so "every row of
    the collection" is no longer one category.
    """
    ids = [f"{rule.collection}/{_row_key(rule.collection, owner, f'-{rule.user_field}')}" for rule in plan.anonymize]
    ids += [f"{rule.collection}/{_row_key(rule.collection, owner)}" for rule in plan.pseudonymize_audit]
    return list(dict.fromkeys(ids))


def _deleted_rows(plan: ErasurePlan, seeded_owner: dict[str, list[str]], owner: str) -> list[str]:
    retained = set(_retained_rows(plan, owner))
    return [
        doc_id
        for collection in dict.fromkeys(_deleted_collections(plan))
        for doc_id in seeded_owner[collection]
        if doc_id not in retained
    ]


def test_every_subject_row_of_a_delete_step_is_gone(database, erased):
    survivors = [
        doc_id
        for doc_id in _deleted_rows(erased.plan, erased.seeded[SUBJECT], SUBJECT)
        if _read(database, doc_id) is not None
    ]
    assert survivors == []


def test_every_retained_subject_row_survives_without_a_trace_of_the_subject(database, erased):
    lost: list[str] = []
    traces: list[str] = []
    for doc_id in _retained_rows(erased.plan, SUBJECT):
        doc = _read(database, doc_id)
        if doc is None:
            lost.append(doc_id)
            continue
        for field, value in doc.items():
            if field.startswith("_"):
                continue
            if value == SUBJECT or value == _display_text(SUBJECT):
                traces.append(f"{doc_id}.{field}={value!r}")
    assert lost == []
    assert traces == []


def test_each_rule_writes_its_declared_replacement(database, erased):
    tombstone = ErasureEngine.compute_tombstone_hash(SUBJECT, SALT)
    assert tombstone.startswith("anon_")
    wrong: list[str] = []
    for rule in erased.plan.anonymize:
        expected = tombstone if rule.replacement_strategy == "tombstone_hash" else rule.anonymized_value
        doc = _read(database, f"{rule.collection}/{_row_key(rule.collection, SUBJECT, f'-{rule.user_field}')}")
        if doc is None or doc.get(rule.user_field) != expected:
            wrong.append(f"{rule.collection}.{rule.user_field}={None if doc is None else doc.get(rule.user_field)!r}")
            continue
        wrong.extend(f"{rule.collection}.{field} not emptied" for field in rule.clear_fields if doc.get(field) != "")
    assert wrong == []
    assert ANONYMIZED_MARKER in {rule.anonymized_value for rule in erased.plan.anonymize}


def test_the_erasure_audit_rows_carry_the_tombstone_hash(database, erased):
    tombstone = ErasureEngine.compute_tombstone_hash(SUBJECT, SALT)
    for rule in erased.plan.pseudonymize_audit:
        rows = erased.seeded[SUBJECT][rule.collection]
        assert rows, f"no audit row seeded for {rule.collection}"
        for doc_id in rows:
            doc = _read(database, doc_id)
            assert doc is not None, f"{doc_id} is an audit record and must be retained"
            assert doc[rule.user_field] == tombstone


def test_every_row_of_the_other_user_is_unchanged(database, erased):
    after = _snapshot(database, erased.seeded[OTHER])
    changed = [doc_id for doc_id, doc in erased.before_other.items() if after[doc_id] != doc]
    assert changed == []
    assert all(doc is not None for doc in erased.before_other.values())


def test_every_declared_step_and_rule_reached_a_row(erased):
    """A step that reaches 0 of a row that exists is inert — the #1664 defect."""
    report = erased.captured.get("report")
    assert report is not None, "the admin path did not run the shared erasure entry"
    zero = [
        step.collection
        for step in erased.plan.steps
        if step.kind in ("edge", "document", "user") and report.affected(step.collection) < 1
    ]
    zero += [f"{rule.collection}.{rule.user_field}" for rule in report.arango.rules if rule.affected < 1]
    assert zero == []
    declared_rules = {(r.collection, r.user_field) for r in (*erased.plan.anonymize, *erased.plan.pseudonymize_audit)}
    assert {(r.collection, r.user_field) for r in report.arango.rules} == declared_rules
    # The only phases this executor hands off are the non-ArangoDB ones.
    delegated = {
        s.collection for s in erased.plan.steps if s.executor in ("storage_cleanup", "reference_index_cleanup")
    }
    assert set(report.arango.delegated) == delegated
    assert report.arango.absent_collections == []


def test_a_second_run_finds_nothing_left_and_touches_nobody_else(database, erased):
    """Re-running after a completed erasure is a no-op — the property a crash retry relies on."""
    before = _snapshot(database, erased.seeded[SUBJECT]) | _snapshot(database, erased.seeded[OTHER])
    privacy_service, _ = _services(database)
    import asyncio

    report = asyncio.run(privacy_service.erase_account(SUBJECT))
    assert [s.affected for s in report.arango.steps if s.affected] == []
    assert [r.affected for r in report.arango.rules if r.affected] == []
    after = _snapshot(database, erased.seeded[SUBJECT]) | _snapshot(database, erased.seeded[OTHER])
    assert after == before


def test_a_failure_mid_plan_rolls_the_whole_arango_run_back(database, erased, monkeypatch):
    """One stream transaction: a crash at the anonymisation phase leaves A intact.

    Runs last in this module and reseeds a third user so the earlier tests'
    shared state is not disturbed.
    """
    from app.data_access.arango.erasure_executor import ArangoErasureExecutor

    subject = "user-c"
    plan = ErasureEngine().build_erasure_plan(subject)
    users = next(step.collection for step in plan.steps if step.kind == "user")
    database.collection(users).insert(_user_document(subject))
    first_document = next(step for step in plan.steps if step.kind == "document" and step.via is None)
    database.collection(first_document.collection).insert({first_document.user_field: subject, "_key": "c-row"})

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated crash inside the anonymisation phase")

    monkeypatch.setattr(ArangoErasureExecutor, "_anonymize", boom)
    with pytest.raises(RuntimeError, match="simulated crash"):
        ArangoErasureExecutor(database).run_erasure_plan(
            plan, tombstone=ErasureEngine.compute_tombstone_hash(subject, SALT)
        )

    # The steps before the crash removed these rows inside the transaction; the
    # abort must have put them back.
    assert database.collection(first_document.collection).get("c-row") is not None
    assert database.collection(users).get(subject) is not None
    monkeypatch.undo()

    report = ArangoErasureExecutor(database).run_erasure_plan(
        plan, tombstone=ErasureEngine.compute_tombstone_hash(subject, SALT)
    )
    assert report.affected(first_document.collection) == 1
    assert report.affected(users) == 1
    assert database.collection(first_document.collection).get("c-row") is None
