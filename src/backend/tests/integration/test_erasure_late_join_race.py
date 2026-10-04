"""#1924 — a join racing the account erasure ends in exactly one outcome, against a real ArangoDB.

REQ-025 AK-IE-07: once the erasure of a personal tenant is frozen (the
tenant-erasure record is inserted), a join is either refused or — when it slipped
in before the freeze — keeps the tenant. Before #1924 the two decisions could both
fire for the **same** joiner:

1. the erasure inserts the record (the freeze);
2. the joiner's membership insert lands (its freeze check ran before step 1);
3. the erasure's second membership read lists the joiner → *retained*;
4. the joiner's re-check finds the record and takes its membership back;
5. the erasure withdraws the record and reports *retained*.

The tenant stayed, anonymised, with **no active member** — not erased (Art. 17
intent lost) and reachable by nobody. The window is the few statements between
steps 1 and 5; only a real database says what each statement sees, so the
interleaving is forced here over the production repositories and the production
:class:`TenantService`, with hooks at exactly the statements the race needs and
threads standing in for the two requests.

The invariant is asserted on the rows, in both orders of steps 4 and 5:

* the erasure reports ``retained_late_joiner`` → the joiner's membership is an
  active one of an existing tenant;
* the erasure reports ``erased`` → the tenant is gone and so is the membership.

Never "retained, nobody active".

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_erasure_late_join_race.py -v
"""

from __future__ import annotations

import contextlib
import threading
from datetime import UTC, datetime
from typing import Any

import pytest
from arango import ArangoClient

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, WriteConflictError
from app.data_access.arango import collections as col
from app.domain.models.membership import Membership
from app.domain.services.tenant_service import TenantService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.tenant_erasure_wiring import tenant_erasure_service

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("erasure_late_join_race")
SALT = "late-join-race-salt-not-a-secret-0123456789"
LOG_SALT = "log-pseudonym-test-salt-not-a-secret-01234"
OWNER = "u-owner"
JOINER = "u-joiner"
WAIT = 10.0


@pytest.fixture(scope="module", autouse=True)
def _log_pseudonym_salt():
    from app.config.settings import settings

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(settings, "log_pseudonym_salt", LOG_SALT)
        yield


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(database)
    yield database
    system.delete_database(TEST_DATABASE)


_counter = iter(range(10_000))


def _account(database, key: str) -> None:
    database.collection(col.USERS).insert(
        {
            "_key": key,
            "email": f"{key}@example.com",
            "display_name": key,
            "password_hash": "not-a-hash",
            "email_verified": True,
            "is_active": True,
            "account_type": "human",
            "created_at": "2026-09-01T00:00:00+00:00",
        }
    )


@pytest.fixture
def personal_tenant(database) -> str:
    """A personal tenant of ``OWNER`` — the owner is its only member."""
    n = next(_counter)
    tenant = f"t-personal-{n}"
    for key in (OWNER, JOINER):
        if not database.collection(col.USERS).has(key):
            _account(database, key)
    database.collection(col.TENANTS).insert(
        {
            "_key": tenant,
            "name": "Garden",
            "slug": tenant,
            "tenant_type": "personal",
            "owner_user_key": OWNER,
            "is_active": True,
            "created_at": "2026-09-01T00:00:00+00:00",
        }
    )
    database.collection(col.MEMBERSHIPS).insert(
        {"user_key": OWNER, "tenant_key": tenant, "role": "lead", "is_active": True}
    )
    return tenant


def _joiner_membership(tenant: str) -> Membership:
    return Membership(
        user_key=JOINER,
        tenant_key=tenant,
        role=TenantRole.GROWER,
        is_active=True,
        joined_at=datetime.now(UTC).isoformat(),
    )


def _joiner_state(database, tenant: str) -> tuple[bool, bool]:
    """``(tenant document exists, an active membership of the joiner exists)``."""
    tenant_exists = database.collection(col.TENANTS).has(tenant)
    cursor = database.aql.execute(
        "FOR m IN @@c FILTER m.tenant_key == @t AND m.user_key == @u AND m.is_active != false RETURN 1",
        bind_vars={"@c": col.MEMBERSHIPS, "t": tenant, "u": JOINER},
    )
    return tenant_exists, bool(list(cursor))


class _Race:
    """Two requests — the erasure (``E``) and a join (``J``) — interleaved at the statements the race needs.

    ``E`` runs ``erase_personal_tenant_of``; ``J`` runs the production
    ``_create_membership_unless_erasing`` (the join every path ends in). The hooks
    wrap the **real** repositories of the service; each one only waits for the
    event the other request sets, then calls through.

    * ``J`` inserts its membership as soon as the freeze record exists (step 2).
    * ``J`` makes its freeze decision — the first call it makes into the freeze
      record or the membership delete after the insert — only after ``E`` has
      read the members a second time (step 3) when ``j_decides_after`` is
      ``"second_read"``, and only after ``E`` withdrew the record when it is
      ``"withdrawal"``.
    * ``E`` withdraws the record (step 5) only once ``J`` finished, in the first
      order; in the second it goes first.
    """

    def __init__(self, service: TenantService, tenant: str, *, j_decides_after: str) -> None:
        self.service = service
        self.tenant = tenant
        self.j_decides_after = j_decides_after
        self.joiner_thread: threading.Thread | None = None
        self.freeze_inserted = threading.Event()
        self.joiner_inserted = threading.Event()
        self.second_read_done = threading.Event()
        self.withdrawn = threading.Event()
        self.joiner_finished = threading.Event()
        self.joiner_result: Any = None
        self.errors: list[BaseException] = []
        self._members_reads = 0
        self._wrap()

    def _in_joiner(self) -> bool:
        return threading.current_thread() is self.joiner_thread

    def _wrap(self) -> None:
        service = self.service
        record_repo = service._tenant_erasure_repo
        member_repo = service._membership_repo

        real_create_record = record_repo.create_with_key
        real_members = member_repo.active_member_user_keys
        real_delete_unclaimed = record_repo.delete_unclaimed
        real_create_member = member_repo.create
        real_get = record_repo.get

        def create_record(record, key):
            created = real_create_record(record, key)
            self.freeze_inserted.set()
            # Step 2 happens now: wait until the joiner's insert landed.
            assert self.joiner_inserted.wait(WAIT), "the joiner never inserted its membership"
            return created

        def members(**kwargs):
            result = real_members(**kwargs)
            if not self._in_joiner():
                self._members_reads += 1
                if self._members_reads == 2:
                    self.second_read_done.set()
            return result

        def delete_unclaimed(key):
            if self.j_decides_after == "second_read":
                # Step 4 first: the joiner decides on the freeze, then E withdraws.
                assert self.joiner_finished.wait(WAIT), "the joiner never finished"
            removed = real_delete_unclaimed(key)
            self.withdrawn.set()
            return removed

        def create_member(membership):
            if self._in_joiner():
                assert self.freeze_inserted.wait(WAIT), "the freeze was never inserted"
            created = real_create_member(membership)
            if self._in_joiner():
                self.joiner_inserted.set()
            return created

        def gate_joiner() -> None:
            if not self._in_joiner():
                return
            event = self.second_read_done if self.j_decides_after == "second_read" else self.withdrawn
            assert event.wait(WAIT), f"the erasure never reached {self.j_decides_after}"

        def get(key):
            gate_joiner()
            return real_get(key)

        record_repo.create_with_key = create_record  # type: ignore[method-assign]
        member_repo.active_member_user_keys = members  # type: ignore[method-assign]
        record_repo.delete_unclaimed = delete_unclaimed  # type: ignore[method-assign]
        member_repo.create = create_member  # type: ignore[method-assign]
        record_repo.get = get  # type: ignore[method-assign]
        # The atomic rollback that replaces the read-then-delete (present once #1924 is fixed).
        if hasattr(member_repo, "delete_while_tenant_frozen"):
            real_rollback = member_repo.delete_while_tenant_frozen

            def rollback(*args, **kwargs):
                gate_joiner()
                return real_rollback(*args, **kwargs)

            member_repo.delete_while_tenant_frozen = rollback  # type: ignore[method-assign]

    def run(self) -> Any:
        def joiner() -> None:
            try:
                self.joiner_result = self.service._create_membership_unless_erasing(_joiner_membership(self.tenant))
            except ForbiddenError as exc:
                self.joiner_result = exc
            except BaseException as exc:  # noqa: BLE001 - surfaced by the test
                self.errors.append(exc)
            finally:
                self.joiner_finished.set()

        self.joiner_thread = threading.Thread(target=joiner, daemon=True)
        self.joiner_thread.start()
        outcome = self.service.erase_personal_tenant_of(OWNER, self.tenant, now=datetime.now(UTC))
        self.joiner_thread.join(WAIT)
        assert not self.errors, self.errors
        return outcome


@pytest.mark.parametrize("j_decides_after", ["second_read", "withdrawal"])
def test_a_join_that_interleaves_with_the_second_read_ends_in_exactly_one_outcome(
    database, personal_tenant, j_decides_after
):
    service = tenant_erasure_service(database, SALT)
    race = _Race(service, personal_tenant, j_decides_after=j_decides_after)

    outcome = race.run()

    tenant_exists, joiner_active = _joiner_state(database, personal_tenant)
    if outcome.outcome == "retained_late_joiner":
        assert tenant_exists, "retained, but the tenant is gone"
        assert joiner_active, "the tenant is retained for a late joiner whose membership was taken back"
    else:
        assert outcome.outcome == "erased", outcome
        assert not tenant_exists
        assert not joiner_active


def test_unhooked_concurrent_joins_never_leave_a_tenant_retained_for_nobody(database):
    """The same invariant without forced interleavings: real threads, jittered starts.

    The forced cases above pin the two orders of the race; this one asks whether
    anything *else* between the statements breaks the invariant. Each round is a
    fresh personal tenant, the erasure and one join started together.
    """
    import random

    rng = random.Random(1924)  # noqa: S311 - jitter, not a secret
    violations: list[str] = []
    for round_number in range(25):
        tenant = f"t-stress-{round_number}"
        database.collection(col.TENANTS).insert(
            {
                "_key": tenant,
                "name": "Garden",
                "slug": tenant,
                "tenant_type": "personal",
                "owner_user_key": OWNER,
                "is_active": True,
                "created_at": "2026-09-01T00:00:00+00:00",
            }
        )
        database.collection(col.MEMBERSHIPS).insert(
            {"user_key": OWNER, "tenant_key": tenant, "role": "lead", "is_active": True}
        )
        service = tenant_erasure_service(database, SALT)
        outcomes: list[Any] = []
        failures: list[BaseException] = []

        def erase(service=service, tenant=tenant, delay=rng.random() * 0.01, outcomes=outcomes, failures=failures):
            threading.Event().wait(delay)
            try:
                outcomes.append(service.erase_personal_tenant_of(OWNER, tenant, now=datetime.now(UTC)))
            except BaseException as exc:  # noqa: BLE001 - recorded, asserted below
                failures.append(exc)

        def join(service=service, tenant=tenant, delay=rng.random() * 0.01):
            threading.Event().wait(delay)
            with contextlib.suppress(ForbiddenError):
                service._create_membership_unless_erasing(_joiner_membership(tenant))

        threads = [threading.Thread(target=erase), threading.Thread(target=join)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(WAIT * 3)
        if failures:
            # A write conflict is the erasure asking to be retried (the daily
            # beat does); the retry is what must reach a consistent end state.
            assert isinstance(failures[0], WriteConflictError), failures
            outcomes.append(service.erase_personal_tenant_of(OWNER, tenant, now=datetime.now(UTC)))
        assert outcomes, f"round {round_number}: the erasure did not finish"
        tenant_exists, joiner_active = _joiner_state(database, tenant)
        if outcomes[0].outcome == "retained_late_joiner" and not joiner_active:
            violations.append(f"round {round_number}: retained, joiner not active")
        if outcomes[0].outcome == "erased" and (tenant_exists or joiner_active):
            violations.append(f"round {round_number}: erased, tenant/joiner still there")
    assert not violations, violations


def _record(database, tenant: str, status: str = "in_progress") -> None:
    from app.domain.engines.tenant_erasure_engine import TenantErasureEngine

    database.collection(col.TENANT_ERASURE_RECORDS).insert(
        {
            "_key": TenantErasureEngine.record_key(tenant),
            "tenant_key": tenant,
            "tenant_type": "personal",
            "origin": "account_erasure",
            "status": status,
            "attempt_count": 0,
        }
    )


class TestRollbackStatement:
    """``ArangoMembershipRepository.delete_while_tenant_frozen`` on its own."""

    def _member(self, database, tenant: str) -> str:
        from app.data_access.arango.membership_repository import ArangoMembershipRepository

        return ArangoMembershipRepository(database).create(_joiner_membership(tenant)).key  # type: ignore[return-value]

    def test_it_removes_the_membership_and_its_edges_while_the_record_is_open(self, database, personal_tenant):
        from app.data_access.arango.membership_repository import ArangoMembershipRepository

        _record(database, personal_tenant)
        key = self._member(database, personal_tenant)

        assert ArangoMembershipRepository(database).delete_while_tenant_frozen(key, personal_tenant) is True

        assert not database.collection(col.MEMBERSHIPS).has(key)
        assert list(database.collection(col.HAS_MEMBERSHIP).find({"_to": f"{col.MEMBERSHIPS}/{key}"})) == []

    def test_it_removes_the_membership_of_a_claimed_run_without_touching_its_record(self, database, personal_tenant):
        """A write on a running erasure's record would conflict with its heartbeat and read as a lost claim."""
        from app.data_access.arango.membership_repository import ArangoMembershipRepository
        from app.domain.engines.tenant_erasure_engine import TenantErasureEngine

        _record(database, personal_tenant)
        record_key = TenantErasureEngine.record_key(personal_tenant)
        database.collection(col.TENANT_ERASURE_RECORDS).update(
            {"_key": record_key, "last_attempt_at": "2026-10-04T05:00:00+00:00", "attempt_count": 1}
        )
        revision = database.collection(col.TENANT_ERASURE_RECORDS).get(record_key)["_rev"]
        key = self._member(database, personal_tenant)

        assert ArangoMembershipRepository(database).delete_while_tenant_frozen(key, personal_tenant) is True

        assert not database.collection(col.MEMBERSHIPS).has(key)
        assert database.collection(col.TENANT_ERASURE_RECORDS).get(record_key)["_rev"] == revision

    def test_it_touches_the_record_of_an_unclaimed_freeze(self, database, personal_tenant):
        """The touch is the arbiter against the erasure's withdrawal; without it the statement is a plain delete."""
        from app.data_access.arango.membership_repository import ArangoMembershipRepository
        from app.domain.engines.tenant_erasure_engine import TenantErasureEngine

        _record(database, personal_tenant)
        record_key = TenantErasureEngine.record_key(personal_tenant)
        revision = database.collection(col.TENANT_ERASURE_RECORDS).get(record_key)["_rev"]
        key = self._member(database, personal_tenant)

        assert ArangoMembershipRepository(database).delete_while_tenant_frozen(key, personal_tenant) is True

        assert database.collection(col.TENANT_ERASURE_RECORDS).get(record_key)["_rev"] != revision

    def test_it_leaves_the_membership_when_there_is_no_record(self, database, personal_tenant):
        from app.data_access.arango.membership_repository import ArangoMembershipRepository

        key = self._member(database, personal_tenant)

        assert ArangoMembershipRepository(database).delete_while_tenant_frozen(key, personal_tenant) is False
        assert database.collection(col.MEMBERSHIPS).has(key)

    def test_it_leaves_the_membership_when_the_deletion_completed(self, database, personal_tenant):
        from app.data_access.arango.membership_repository import ArangoMembershipRepository

        _record(database, personal_tenant, status="completed")
        key = self._member(database, personal_tenant)

        assert ArangoMembershipRepository(database).delete_while_tenant_frozen(key, personal_tenant) is False
        assert database.collection(col.MEMBERSHIPS).has(key)

    def test_it_never_removes_a_membership_of_another_tenant(self, database, personal_tenant):
        from app.data_access.arango.membership_repository import ArangoMembershipRepository

        _record(database, personal_tenant)
        key = self._member(database, personal_tenant)

        assert ArangoMembershipRepository(database).delete_while_tenant_frozen(key, "t-elsewhere") is False
        assert database.collection(col.MEMBERSHIPS).has(key)
