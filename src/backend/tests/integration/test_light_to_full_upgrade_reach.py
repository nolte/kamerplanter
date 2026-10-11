"""#1855 / REQ-027 §7a — the switch from light to full mode, end to end against a **real** ArangoDB.

The light-mode installation is written by the real light-mode seed (``run_seed_light_mode``), its
API key minted by the real ``AuthService.create_api_key`` in light mode; the start is the real
``ModeSwitchService.reconcile`` over the real repositories, the take-over the real ``/system`` router.
What it leaves is read straight off the collections.

The measured gap (before the fix, ``develop`` ``9c8965982``): after a switch to ``full`` the system
account stayed active with its ``lead`` membership, a ``kp_`` key minted unauthenticated in light mode
kept authenticating as it, and a newly registered account got an empty garden with no way to reach
the light-mode data.

Runs in CI against the service container; locally it needs a database of its own
(``docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12``).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from arango import ArangoClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth.router import limiter
from app.api.v1.system.router import router as system_router
from app.common.auth import get_authenticated_with_api_key, require_account_principal
from app.common.dependencies import get_mode_switch_service
from app.common.enums import AdminScope, SecurityAuditAction, SecurityAuditVia, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.common.rate_limit import rate_limit_exceeded_with_retry_after
from app.data_access.arango import collections as col
from app.data_access.arango.api_key_repository import ArangoApiKeyRepository
from app.data_access.arango.calendar_feed_repository import ArangoCalendarFeedRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.mode_switch_repository import ArangoModeSwitchRepository
from app.data_access.arango.refresh_token_repository import ArangoRefreshTokenRepository
from app.data_access.arango.security_audit_repository import ArangoSecurityAuditRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.mode_switch import SYSTEM_TENANT_KEY, SYSTEM_USER_KEY, TakeoverReceipt
from app.domain.models.user import User
from app.domain.services.auth_service import AuthService
from app.domain.services.mode_switch_service import ModeSwitchService
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.step_up_service import default_step_up_verifier
from app.domain.services.tenant_service import TenantService
from app.migrations import seed_light_mode
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("light_to_full_upgrade")
# Credential-shaped values are assembled at runtime (GitGuardian, #1838).
PASSWORD = "-".join(["takeover", "Owner", "pw", "1855"])
_PASSWORDS = PasswordEngine()

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)


class _Installation:
    """A light-mode installation with data, then the same database started in full mode."""

    def __init__(self, db, monkeypatch: pytest.MonkeyPatch) -> None:
        self.db = db
        for name in (
            col.USERS,
            col.TENANTS,
            col.MEMBERSHIPS,
            col.API_KEYS,
            col.REFRESH_TOKENS,
            col.CALENDAR_FEEDS,
            col.SECURITY_AUDIT_LOG,
            col.SYSTEM_META,
            col.PLANT_INSTANCES,
            col.SITES,
            col.HAS_MEMBERSHIP,
            col.MEMBERSHIP_IN,
        ):
            db.collection(name).truncate()
        # The real light-mode seed writes the system account, its tenant and its membership.
        monkeypatch.setattr(seed_light_mode, "get_connection", lambda: SimpleNamespace(db=db))
        seed_light_mode.run_seed_light_mode()

        self.users = ArangoUserRepository(db)
        self.memberships = ArangoMembershipRepository(db)
        self.api_keys = ArangoApiKeyRepository(db)
        self.audit = SecurityAuditService(ArangoSecurityAuditRepository(db))
        self.tenants = TenantService(
            tenant_repo=ArangoTenantRepository(db),
            membership_repo=self.memberships,
            invitation_repo=None,  # type: ignore[arg-type]
            assignment_repo=None,  # type: ignore[arg-type]
            tenant_engine=TenantEngine(),
            membership_engine=MembershipEngine(),
            invitation_engine=InvitationEngine(),
            security_audit=self.audit,
            user_repo=self.users,
            takeover_repo=ArangoModeSwitchRepository(db),
        )
        self.service = ModeSwitchService(
            repo=self.repo_for(db),
            user_repo=self.users,
            tenant_service=self.tenants,
            api_key_repo=self.api_keys,
            refresh_token_repo=ArangoRefreshTokenRepository(db),
            calendar_feed_repo=ArangoCalendarFeedRepository(db),
            security_audit=self.audit,
            # The real verifier over the in-memory tiers: the deciding account's password is checked.
            step_up_verifier=default_step_up_verifier(PasswordEngine()),
        )
        self.repo = ArangoModeSwitchRepository(db)
        # Light-mode data: two plants (one removed) and a site, all in the system tenant.
        db.collection(col.SITES).insert({"_key": "site-1", "tenant_key": SYSTEM_TENANT_KEY, "name": "Balkon"})
        db.collection(col.PLANT_INSTANCES).insert(
            {"_key": "plant-1", "tenant_key": SYSTEM_TENANT_KEY, "instance_id": "P-1"}
        )
        db.collection(col.PLANT_INSTANCES).insert(
            {"_key": "plant-2", "tenant_key": SYSTEM_TENANT_KEY, "instance_id": "P-2", "removed_on": "2026-05-01"}
        )

    @staticmethod
    def repo_for(db) -> ArangoModeSwitchRepository:
        return ArangoModeSwitchRepository(db)

    def auth_service(self, *, light_mode: bool) -> AuthService:
        return AuthService(
            user_repo=self.users,
            auth_provider_repo=MagicMock(),
            refresh_token_repo=ArangoRefreshTokenRepository(self.db),
            password_engine=PasswordEngine(),
            token_engine=MagicMock(),
            throttle_engine=LoginThrottleEngine(),
            email_service=MagicMock(),
            frontend_url="",
            api_key_repo=self.api_keys,
            light_mode=light_mode,
        )

    def register(
        self,
        name: str,
        *,
        verified: bool = True,
        active: bool = True,
        account_type: str = "human",
        created_at: datetime | None = None,
        personal_garden: bool = True,
    ) -> User:
        """A full-mode account with its personal garden, as registration leaves it (each one a minute later)."""
        when = created_at or datetime.now(UTC) + timedelta(minutes=len(self.registered) + 1)
        self.db.collection(col.USERS).insert(
            {
                "_key": name,
                "email": f"{name}@example.com",
                "display_name": name.title(),
                "password_hash": _PASSWORDS.hash_password(PASSWORD),
                "is_active": active,
                "account_type": account_type,
                "email_verified": verified,
                "created_at": when.isoformat(),
            }
        )
        self.registered.append(name)
        user = self.users.get_by_key(name)
        assert user is not None
        if personal_garden:
            self.tenants.create_personal_tenant(name, user.display_name)
        return user

    def decide(self, user: User, *, accept: bool, password: str = PASSWORD, api_key: bool = False):
        return self.client(user, api_key=api_key).post(
            "/api/v1/system/takeover", json={"accept": accept, "current_password": password}
        )

    registered: list[str]

    def client(self, user: User, *, api_key: bool = False) -> TestClient:
        app = FastAPI()
        app.include_router(system_router, prefix="/api/v1")
        app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_with_retry_after)  # type: ignore[arg-type]
        app.state.limiter = limiter
        app.dependency_overrides[require_account_principal] = lambda: user
        app.dependency_overrides[get_authenticated_with_api_key] = lambda: api_key
        app.dependency_overrides[get_mode_switch_service] = lambda: self.service
        return TestClient(app, raise_server_exceptions=False)

    def membership(self, user_key: str, tenant_key: str):
        return self.memberships.get_by_user_and_tenant(user_key, tenant_key)

    def audit_rows(self) -> list[dict]:
        return list(self.db.collection(col.SECURITY_AUDIT_LOG).all())


@pytest.fixture
def installation(database, monkeypatch) -> _Installation:
    limiter.reset()  # the take-over routes are rate-limited per account (R3 W-5); every test starts afresh
    stage = _Installation(database, monkeypatch)
    stage.registered = []
    return stage


def test_a_key_minted_in_light_mode_does_not_survive_the_switch(installation: _Installation) -> None:
    """REQ-027 AK-35: mint a key in light mode, switch to full, the key no longer authenticates (401)."""
    minted = installation.auth_service(light_mode=True).create_api_key(
        SYSTEM_USER_KEY,
        "mcp",
        current_password=None,
        step_up_code=None,
        step_up_token=None,
        authenticated_with_api_key=False,
        client_ip=None,
    )
    light_auth = installation.auth_service(light_mode=True)
    full_auth = installation.auth_service(light_mode=False)
    # Non-vacuity: before the switch the key is a working credential of the system account.
    before = light_auth.authenticate_api_key(minted.raw_key, client_ip=None)
    assert before is not None and before.key == SYSTEM_USER_KEY
    # SEC-006: full mode refuses the system account even before any start sealed it (the stored state
    # still says active, the key unrevoked) - a replica serving before the seal, a restored backup.
    assert full_auth.authenticate_api_key(minted.raw_key, client_ip=None) is None

    outcome = installation.service.reconcile("full")

    assert full_auth.authenticate_api_key(minted.raw_key, client_ip=None) is None
    assert light_auth.authenticate_api_key(minted.raw_key, client_ip=None) is None  # revoked, not only refused
    assert outcome.sealing.deactivated is True
    assert outcome.sealing.api_keys_revoked == 1
    system_user = installation.users.get_by_key(SYSTEM_USER_KEY)
    assert system_user is not None and system_user.is_active is False
    stored_keys = installation.api_keys.list_by_user(SYSTEM_USER_KEY)
    assert [k.revoked for k in stored_keys] == [True]
    deactivations = [r for r in installation.audit_rows() if r["action"] == SecurityAuditAction.ACCOUNT_DEACTIVATED]
    assert [(r["via"], r["target_user_key"]) for r in deactivations] == [
        (SecurityAuditVia.MODE_SWITCH, SYSTEM_USER_KEY)
    ]


def test_the_first_account_takes_the_light_mode_data_over(installation: _Installation) -> None:
    """REQ-027 Szenario 5 / AK-15..AK-21, AK-28 — the data stay where they are, the membership moves."""
    plant_rev = installation.db.collection(col.PLANT_INSTANCES).get("plant-1")["_rev"]

    outcome = installation.service.reconcile("full")
    assert (outcome.previous_mode, outcome.previous_mode_inferred) == ("light", True)
    assert outcome.pending_takeover_recorded is True
    assert installation.db.collection(col.SYSTEM_META).get("deployment_mode")["mode"] == "full"

    anna = installation.register("anna")
    max_ = installation.register("max")

    hidden = installation.client(max_).get("/api/v1/system/takeover-status").json()
    assert hidden == {
        "pending": True,
        "eligible": False,
        "tenant_key": None,
        "tenant_name": None,
        "tenant_slug": None,
        "resource_counts": None,
    }
    status = installation.client(anna).get("/api/v1/system/takeover-status").json()
    assert status["eligible"] is True
    assert status["tenant_slug"] == "mein-garten"
    assert status["resource_counts"] == {"plants": 1, "sites": 1, "planting_runs": 0, "nutrient_plans": 0, "tasks": 0}

    assert installation.decide(max_, accept=True).status_code == 403
    assert installation.decide(anna, accept=True, api_key=True).status_code == 403
    # SEC-003: the wrong password is the step-up's 401, and nothing is written or claimed.
    assert installation.decide(anna, accept=True, password="wrong").status_code == 401
    assert installation.db.collection(col.SYSTEM_META).get("pending_takeover").get("claim_id") is None
    assert installation.membership("anna", SYSTEM_TENANT_KEY) is None

    response = installation.decide(anna, accept=True)

    assert response.status_code == 200, response.text
    assert response.json() == {"accepted": True, "tenant_slug": "mein-garten", "platform_admin_granted": True}
    owner = installation.membership("anna", SYSTEM_TENANT_KEY)
    assert owner is not None and owner.is_active and owner.role == TenantRole.LEAD
    assert owner.admin_scopes == [AdminScope.MANAGEMENT, AdminScope.TECHNICAL]
    ended = installation.membership(SYSTEM_USER_KEY, SYSTEM_TENANT_KEY)
    assert ended is not None and ended.is_active is False
    tenant = installation.db.collection(col.TENANTS).get(SYSTEM_TENANT_KEY)
    assert (tenant["owner_user_key"], tenant["name"], tenant["slug"]) == ("anna", "Anna", "mein-garten")
    platform = installation.membership("anna", "platform")
    assert platform is not None and platform.is_active and platform.role == TenantRole.LEAD
    assert installation.db.collection(col.TENANTS).find({"slug": "platform"}).count() == 1
    # No resource document was rewritten: same tenant, same revision.
    plant = installation.db.collection(col.PLANT_INSTANCES).get("plant-1")
    assert (plant["tenant_key"], plant["_rev"]) == (SYSTEM_TENANT_KEY, plant_rev)
    assert installation.db.collection(col.SYSTEM_META).get("pending_takeover") is None
    takeover_rows = {
        (r["action"], r.get("target_user_key"), r.get("tenant_key"))
        for r in installation.audit_rows()
        if r["via"] == SecurityAuditVia.LIGHT_MODE_TAKEOVER
    }
    assert takeover_rows == {
        (SecurityAuditAction.MEMBERSHIP_REMOVED, SYSTEM_USER_KEY, SYSTEM_TENANT_KEY),
        (SecurityAuditAction.MEMBERSHIP_ADDED, "anna", SYSTEM_TENANT_KEY),
        (SecurityAuditAction.TENANT_TAKEN_OVER, None, SYSTEM_TENANT_KEY),
        (SecurityAuditAction.MEMBERSHIP_ADDED, "anna", "platform"),
        (SecurityAuditAction.TAKEOVER_ACCEPTED, "anna", SYSTEM_TENANT_KEY),
        # The refused attempts before it (R2 review): a later account, and the API key.
        (SecurityAuditAction.TAKEOVER_REFUSED, "max", SYSTEM_TENANT_KEY),
        (SecurityAuditAction.TAKEOVER_REFUSED, "anna", None),
    }
    decision = next(r for r in installation.audit_rows() if r["action"] == SecurityAuditAction.TAKEOVER_ACCEPTED)
    assert (decision["platform_admin_granted"], decision["step_up_method"]) == (True, "password")
    refusals = {r["reason"] for r in installation.audit_rows() if r["action"] == SecurityAuditAction.TAKEOVER_REFUSED}
    assert refusals == {"not_eligible", "api_key"}
    # Decided once: a second decision finds nothing open, and a restart does not reopen it.
    assert installation.decide(anna, accept=True).status_code == 404
    again = installation.service.reconcile("full")
    assert (again.pending_takeover_recorded, again.sealing.deactivated) == (False, False)


def test_declining_keeps_the_light_mode_tenant_and_hands_over_the_platform_role(installation: _Installation) -> None:
    """REQ-027 Szenario 6 / AK-20."""
    installation.service.reconcile("full")
    anna = installation.register("anna")

    response = installation.decide(anna, accept=False)

    assert response.json() == {"accepted": False, "tenant_slug": None, "platform_admin_granted": True}
    assert installation.membership("anna", SYSTEM_TENANT_KEY) is None
    tenant = installation.db.collection(col.TENANTS).get(SYSTEM_TENANT_KEY)
    assert (tenant["status"], tenant["owner_user_key"]) == ("active", SYSTEM_USER_KEY)
    assert installation.membership("anna", "platform").role == TenantRole.LEAD


def test_roundtrip_light_full_light_full(installation: _Installation) -> None:
    """REQ-027 Szenario 7/8: back in light mode the system account works again; the next upgrade reopens."""
    installation.service.reconcile("full")
    anna = installation.register("anna")
    assert installation.decide(anna, accept=True).status_code == 200

    back = installation.service.reconcile("light")

    assert back.system_account_restored is True
    system_user = installation.users.get_by_key(SYSTEM_USER_KEY)
    assert system_user is not None and system_user.is_active is True
    restored = installation.membership(SYSTEM_USER_KEY, SYSTEM_TENANT_KEY)
    assert restored is not None and restored.is_active and restored.role == TenantRole.LEAD
    assert installation.db.collection(col.SYSTEM_META).get("deployment_mode")["mode"] == "light"
    # Anna's data and memberships are untouched by the downgrade.
    assert installation.membership("anna", SYSTEM_TENANT_KEY).is_active

    up_again = installation.service.reconcile("full")

    assert up_again.previous_mode == "light" and up_again.previous_mode_inferred is False
    assert up_again.pending_takeover_recorded is True
    response = installation.decide(anna, accept=True)
    assert response.status_code == 200, response.text
    # Anna was a member already: raised in place, not a second membership; the system account is out again.
    rows = list(installation.db.collection(col.MEMBERSHIPS).find({"user_key": "anna", "tenant_key": SYSTEM_TENANT_KEY}))
    assert len(rows) == 1
    assert installation.membership(SYSTEM_USER_KEY, SYSTEM_TENANT_KEY).is_active is False
    # She is the platform admin already: the role is not handed out a second time.
    assert response.json()["platform_admin_granted"] is False


def test_the_seal_writes_one_aggregate_audit_row(installation: _Installation) -> None:
    """#1855 SEC-005 — counts of what the start revoked; a repeated start writes no second row."""
    installation.service.reconcile("full")
    installation.service.reconcile("full")

    rows = [r for r in installation.audit_rows() if r["action"] == SecurityAuditAction.SYSTEM_ACCOUNT_SEALED]
    assert len(rows) == 1
    assert rows[0]["via"] == SecurityAuditVia.MODE_SWITCH
    assert rows[0]["revoked_counts"] == {"api_keys": 0, "sessions": 0, "calendar_feeds": 0}


@pytest.mark.parametrize(
    "earlier",
    [
        pytest.param({"account_type": "service"}, id="service-account"),
        pytest.param({"active": False}, id="inactive"),
        pytest.param({"verified": False}, id="unverified"),
        pytest.param({"personal_garden": False}, id="no-personal-garden"),
        pytest.param({"created_at": datetime(2026, 1, 1, tzinfo=UTC)}, id="registered-before-the-switch"),
    ],
)
def test_only_an_eligible_account_registered_after_the_switch_is_the_first(
    installation: _Installation, earlier: dict
) -> None:
    """#1855 SEC-002 / SEC-008 — the earliest-account query, measured on the real collections.

    An earlier account that is a service account, inactive, unverified, without its own garden or
    registered before the take-over opened is never "the first account"; the next eligible one is.
    """
    installation.service.reconcile("full")
    early = installation.register("early", **earlier)
    anna = installation.register("anna")

    assert installation.client(early).get("/api/v1/system/takeover-status").json()["eligible"] is False
    assert installation.client(anna).get("/api/v1/system/takeover-status").json()["eligible"] is True
    assert installation.decide(early, accept=True).status_code == 403
    assert installation.decide(anna, accept=False).status_code == 200


def test_the_claim_is_held_by_one_decision_and_lapses(installation: _Installation) -> None:
    """#1855 SEC-004 — the claim queries on the real collection: one holder, its own release, the TTL."""
    installation.service.reconcile("full")
    repo = installation.repo
    now = datetime.now(UTC)

    first = repo.claim_pending_takeover(claimant="a:1", now=now, stale_before=now - timedelta(minutes=10))
    second = repo.claim_pending_takeover(claimant="b:2", now=now, stale_before=now - timedelta(minutes=10))

    assert first is not None and first.claim_id == "a:1"
    assert second is None
    assert repo.complete_pending_takeover(claimant="b:2") is False  # not the holder: nothing removed
    assert repo.release_pending_takeover(claimant="a:1") is True
    pending = repo.get_pending_takeover()
    assert pending is not None and pending.claim_id is None
    # A claim older than the TTL belongs to a decision that died: another may take it over.
    stale = now - timedelta(hours=1)
    assert repo.claim_pending_takeover(claimant="a:1", now=stale, stale_before=stale - timedelta(minutes=10))
    taken = repo.claim_pending_takeover(claimant="b:2", now=now, stale_before=now - timedelta(minutes=10))
    assert taken is not None and taken.claim_id == "b:2"
    assert repo.complete_pending_takeover(claimant="b:2") is True
    assert repo.get_pending_takeover() is None


def test_a_failed_platform_grant_undoes_the_take_over(installation: _Installation, monkeypatch) -> None:
    """#1855 SEC-004 — the take-over stood, the grant failed: every write is taken back, the take-over reopens."""
    installation.service.reconcile("full")
    anna = installation.register("anna")

    def fail(_account, *, receipt):
        raise RuntimeError("platform store down")

    monkeypatch.setattr(installation.tenants, "grant_first_platform_admin", fail)

    assert installation.decide(anna, accept=True).status_code == 500

    assert installation.membership("anna", SYSTEM_TENANT_KEY) is None
    system = installation.membership(SYSTEM_USER_KEY, SYSTEM_TENANT_KEY)
    assert system is not None and system.is_active
    tenant = installation.db.collection(col.TENANTS).get(SYSTEM_TENANT_KEY)
    assert (tenant["owner_user_key"], tenant["name"]) == (SYSTEM_USER_KEY, "Mein Garten")
    pending = installation.repo.get_pending_takeover()
    assert pending is not None and pending.claim_id is None
    assert any(r["action"] == SecurityAuditAction.TAKEOVER_REVERTED for r in installation.audit_rows())


def _assert_restored(installation: _Installation, *, owner: str) -> None:
    """The light-mode tenant as before the decision: no membership of *owner*, the system account's back."""
    assert installation.membership(owner, SYSTEM_TENANT_KEY) is None
    assert installation.membership(owner, "platform") is None
    system = installation.membership(SYSTEM_USER_KEY, SYSTEM_TENANT_KEY)
    assert system is not None and system.is_active
    tenant = installation.db.collection(col.TENANTS).get(SYSTEM_TENANT_KEY)
    assert (tenant["owner_user_key"], tenant["name"]) == (SYSTEM_USER_KEY, "Mein Garten")


def test_a_failure_inside_the_take_over_is_undone_from_the_partial_receipt(
    installation: _Installation, monkeypatch
) -> None:
    """#1855 R2-001 — the take-over's own last audit row fails after three writes stood: all three undone."""
    installation.service.reconcile("full")
    anna = installation.register("anna")
    real = installation.tenants._audit_tenant

    def audit(action, **kwargs):
        if action == SecurityAuditAction.TENANT_TAKEN_OVER:
            raise RuntimeError("audit store down")
        return real(action, **kwargs)

    monkeypatch.setattr(installation.tenants, "_audit_tenant", audit)

    assert installation.decide(anna, accept=True).status_code == 500

    _assert_restored(installation, owner="anna")
    pending = installation.repo.get_pending_takeover()
    assert pending is not None and pending.claim_id is None and pending.needs_attention is False


def test_a_failing_platform_grant_audit_removes_the_platform_membership(
    installation: _Installation, monkeypatch
) -> None:
    """#1855 R2-001 — the grant wrote the platform membership, then its audit row failed: removed again."""
    installation.service.reconcile("full")
    anna = installation.register("anna")
    real = installation.tenants._audit_membership

    def audit(**kwargs):
        if kwargs["tenant_key"] == "platform" and kwargs["action"] == SecurityAuditAction.MEMBERSHIP_ADDED:
            raise RuntimeError("audit store down")
        return real(**kwargs)

    monkeypatch.setattr(installation.tenants, "_audit_membership", audit)

    assert installation.decide(anna, accept=True).status_code == 500

    _assert_restored(installation, owner="anna")
    assert installation.repo.get_pending_takeover().claim_id is None


def test_an_undo_that_failed_is_stored_and_undone_before_the_next_decision(
    installation: _Installation, monkeypatch
) -> None:
    """#1855 R2-002 — the receipt survives on the take-over; the TTL does not hand over a half state."""
    installation.service.reconcile("full")
    anna = installation.register("anna")
    real_undo = installation.tenants.undo_light_mode_takeover
    real_grant = installation.tenants.grant_first_platform_admin

    def fail_grant(_account, *, receipt):
        raise RuntimeError("platform store down")

    def fail_undo(_receipt, **_kwargs):
        raise RuntimeError("store still down")

    monkeypatch.setattr(installation.tenants, "grant_first_platform_admin", fail_grant)
    monkeypatch.setattr(installation.tenants, "undo_light_mode_takeover", fail_undo)
    assert installation.decide(anna, accept=True).status_code == 500

    pending = installation.repo.get_pending_takeover()
    assert pending is not None and pending.needs_attention is True and pending.claim_id is not None
    assert pending.receipt is not None and pending.receipt.created_membership_key
    assert installation.membership("anna", SYSTEM_TENANT_KEY) is not None  # the half state, recorded
    assert any(r["action"] == SecurityAuditAction.TAKEOVER_UNDO_FAILED for r in installation.audit_rows())
    # While the claim is live, nobody decides on top of it.
    assert installation.decide(anna, accept=False).status_code == 404

    # The claim lapses; the next decision undoes the stored receipt first, then decides.
    installation.db.collection(col.SYSTEM_META).update(
        {"_key": "pending_takeover", "claimed_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat()}
    )
    monkeypatch.setattr(installation.tenants, "undo_light_mode_takeover", real_undo)
    monkeypatch.setattr(installation.tenants, "grant_first_platform_admin", real_grant)
    response = installation.decide(anna, accept=False)

    assert response.status_code == 200, response.text
    assert installation.repo.get_pending_takeover() is None
    assert installation.membership("anna", SYSTEM_TENANT_KEY) is None  # the stored take-over was undone
    system = installation.membership(SYSTEM_USER_KEY, SYSTEM_TENANT_KEY)
    assert system is not None and system.is_active
    platform = installation.membership("anna", "platform")
    assert platform is not None and platform.is_active  # the decline made anna the first admin


def test_the_attention_queries_hold_to_the_claimant(installation: _Installation) -> None:
    """#1855 R2-002/003 — store, read back and drop a receipt only as the holder of the claim."""
    installation.service.reconcile("full")
    repo = installation.repo
    now = datetime.now(UTC)
    receipt = TakeoverReceipt(
        tenant_key=SYSTEM_TENANT_KEY,
        new_owner_key="anna",
        system_user_key=SYSTEM_USER_KEY,
        created_membership_key="m-1",
        raised_previous_scopes=["management"],
        tenant_changed=True,
    )
    assert repo.claim_pending_takeover(claimant="a", now=now, stale_before=now - timedelta(minutes=10))

    assert repo.holds_claim(claimant="a") is True and repo.holds_claim(claimant="b") is False
    assert repo.mark_takeover_needs_attention(claimant="b", receipt=receipt) is False
    assert repo.mark_takeover_needs_attention(claimant="a", receipt=receipt) is True
    stored = repo.get_pending_takeover()
    assert stored is not None and stored.needs_attention is True
    # R3 W-3: the deciding account is never stored - the rest of the receipt is, unchanged.
    assert stored.receipt == receipt.model_copy(update={"new_owner_key": None})
    raw = installation.db.collection(col.SYSTEM_META).get("pending_takeover")["receipt"]
    assert "new_owner_key" not in raw and "anna" not in str(raw)
    assert repo.resolve_takeover_attention(claimant="b") is False
    assert repo.resolve_takeover_attention(claimant="a") is True
    resolved = repo.get_pending_takeover()
    assert resolved is not None and resolved.needs_attention is False and resolved.receipt is None
    assert resolved.claim_id == "a"


def _fail_grant(_account, *, receipt):
    raise RuntimeError("platform store down")


def test_a_lead_membership_whose_key_never_came_back_is_undone(installation: _Installation, monkeypatch) -> None:
    """#1855 R3 W-1 — the insert stood, the check after it failed: the intent finds the membership."""
    installation.service.reconcile("full")
    anna = installation.register("anna")

    def count_fails(_created, _limit):
        raise RuntimeError("count unavailable")

    monkeypatch.setattr(installation.tenants, "_settle_join_against_member_limit", count_fails)

    assert installation.decide(anna, accept=True).status_code == 500

    _assert_restored(installation, owner="anna")
    assert installation.repo.get_pending_takeover().claim_id is None


def test_a_platform_membership_whose_key_never_came_back_is_undone(installation: _Installation, monkeypatch) -> None:
    """#1855 R3 W-1 — the same for the first-admin grant's ``platform`` membership."""
    installation.service.reconcile("full")
    anna = installation.register("anna")
    real_create = installation.memberships.create

    def create(membership):
        created = real_create(membership)
        if membership.tenant_key == "platform":
            raise RuntimeError("edge store down")
        return created

    monkeypatch.setattr(installation.memberships, "create", create)

    assert installation.decide(anna, accept=True).status_code == 500

    _assert_restored(installation, owner="anna")


def test_an_undo_stops_when_the_claim_is_lost_midway(installation: _Installation, monkeypatch) -> None:
    """#1855 R3 W-2 — the claim is checked before every undo step, not once; the rest is reported, not written."""
    installation.service.reconcile("full")
    anna = installation.register("anna")
    monkeypatch.setattr(installation.tenants, "grant_first_platform_admin", _fail_grant)
    answers = iter([True])  # the claim holds for the first undo step, then another decision owns it
    monkeypatch.setattr(installation.repo, "holds_claim", lambda **_: next(answers, False))
    installation.service._repo = installation.repo

    assert installation.decide(anna, accept=True).status_code == 500

    # The first step (removing anna's lead membership) ran; the later ones did not write over the new holder.
    assert installation.membership("anna", SYSTEM_TENANT_KEY) is None
    system = installation.membership(SYSTEM_USER_KEY, SYSTEM_TENANT_KEY)
    assert system is not None and system.is_active is False
    reasons = [
        r.get("reason") for r in installation.audit_rows() if r["action"] == SecurityAuditAction.TAKEOVER_UNDO_FAILED
    ]
    assert reasons == ["undo_failed_receipt_not_stored"]


def test_a_tenant_gone_meanwhile_leaves_nothing_to_undo(installation: _Installation, monkeypatch) -> None:
    """#1855 R3 W-4 — the undo does not get stuck on a tenant that no longer exists."""
    installation.service.reconcile("full")
    anna = installation.register("anna")

    def drop_tenant_and_fail(_account, *, receipt):
        installation.db.collection(col.TENANTS).delete(SYSTEM_TENANT_KEY)
        raise RuntimeError("platform store down")

    monkeypatch.setattr(installation.tenants, "grant_first_platform_admin", drop_tenant_and_fail)

    assert installation.decide(anna, accept=True).status_code == 500

    pending = installation.repo.get_pending_takeover()
    assert pending is not None and pending.claim_id is None and pending.needs_attention is False


def test_an_account_erasure_does_not_take_the_light_mode_garden_with_it(
    installation: _Installation, monkeypatch
) -> None:
    """#1855 R3 W-4 — a failed take-over left anna as owner: not her personal garden while the receipt stands."""
    installation.service.reconcile("full")
    anna = installation.register("anna")
    monkeypatch.setattr(installation.tenants, "grant_first_platform_admin", _fail_grant)

    def fail_undo(_receipt, **_kwargs):
        raise RuntimeError("store still down")

    monkeypatch.setattr(installation.tenants, "undo_light_mode_takeover", fail_undo)
    assert installation.decide(anna, accept=True).status_code == 500
    assert installation.db.collection(col.TENANTS).get(SYSTEM_TENANT_KEY)["owner_user_key"] == "anna"

    keys = installation.tenants.personal_tenant_keys_of("anna")

    assert SYSTEM_TENANT_KEY not in keys
    assert len(keys) == 1  # her own garden from registration stays in the erasure


def test_the_take_over_routes_are_rate_limited(installation: _Installation) -> None:
    """#1855 R3 W-5 — refused decisions write audit rows: the route is bounded per caller."""
    installation.service.reconcile("full")
    installation.register("anna")
    max_ = installation.register("max")
    client = installation.client(max_)

    codes = [
        client.post("/api/v1/system/takeover", json={"accept": True, "current_password": PASSWORD}).status_code
        for _ in range(11)
    ]

    assert codes[:10] == [403] * 10
    assert codes[10] == 429
