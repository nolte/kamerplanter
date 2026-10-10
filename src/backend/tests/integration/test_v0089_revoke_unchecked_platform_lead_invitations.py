"""#2180 - v0089 revokes the pending ``lead`` invitations into the platform tenant and nothing else (real ArangoDB).

The rows are written through the real ``ArangoInvitationRepository`` - the stored shape the
issuing code produced, ``expires_at`` spelling included - so the predicate is measured against
what a volume holds. Around the four hits sit the rows a wrong predicate would take along: a
platform invitation below ``lead``, a ``lead`` invitation into an ordinary tenant, and platform
``lead`` invitations that are no longer pending.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import InvitationStatus, InvitationType, TenantRole
from app.data_access.arango import collections as col
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.models.invitation import Invitation
from app.migrations.versions.v0089_revoke_unchecked_platform_lead_invitations import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration rewrites rows on a real server"),
]

_DB_NAME = run_database_name("v0089_platform_lead_invitations")
PLATFORM = "platform"
GARDEN = "t-garden"


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    for key, is_platform in ((PLATFORM, True), (GARDEN, False)):
        database.collection(col.TENANTS).insert(
            {"_key": key, "name": key, "slug": key, "tenant_type": "organization", "is_platform": is_platform}
        )
    yield database
    system.delete_database(_DB_NAME)


#: token digest -> the name a test gave the invitation
_NAMES: dict[str, str] = {}


def _invite(
    db,
    key: str,
    *,
    tenant: str = PLATFORM,
    role: TenantRole = TenantRole.LEAD,
    kind: InvitationType = InvitationType.LINK,
    status: InvitationStatus = InvitationStatus.PENDING,
    expires_in: timedelta = timedelta(days=5),
) -> None:
    _NAMES[InvitationEngine.hash_token(key)] = key
    ArangoInvitationRepository(db).create(
        Invitation(
            tenant_key=tenant,
            invited_by_user_key="u-secretary",
            invitation_type=kind,
            email="someone@example.org" if kind == InvitationType.EMAIL else None,
            role=role,
            token_hash=InvitationEngine.hash_token(key),
            status=status,
            expires_at=datetime.now(UTC) + expires_in,
        )
    )


def _statuses(db) -> dict[str, str]:
    """Status per invitation, named by the token it was created with (the repository assigns the keys)."""
    return {_NAMES[doc["token_hash"]]: doc["status"] for doc in db.collection(col.INVITATIONS).all()}


def _doc(db, name: str) -> dict:
    (doc,) = [d for d in db.collection(col.INVITATIONS).all() if _NAMES[d["token_hash"]] == name]
    return doc


def test_only_pending_platform_lead_invitations_are_revoked_and_a_rerun_is_a_noop(db):
    # The hits: link and e-mail, unexpired and expired-but-still-pending.
    _invite(db, "plat-lead-link")
    _invite(db, "plat-lead-email", kind=InvitationType.EMAIL)
    _invite(db, "plat-lead-link-expired", expires_in=timedelta(days=-2))
    _invite(db, "plat-lead-email-expired", kind=InvitationType.EMAIL, expires_in=timedelta(days=-1))
    # What stays: below lead, another tenant, no longer pending.
    _invite(db, "plat-grower", role=TenantRole.GROWER)
    _invite(db, "garden-lead", tenant=GARDEN)
    _invite(db, "plat-lead-accepted", status=InvitationStatus.ACCEPTED)
    _invite(db, "plat-lead-revoked", status=InvitationStatus.REVOKED)
    before = _statuses(db)

    dry = migration.up(db, dry_run=True)

    assert (dry.scanned, dry.changed, dry.dry_run) == (4, 0, True)
    assert dry.details == {"pending_platform_lead_invitations": 4, "unexpired": 2}
    assert _statuses(db) == before

    report = migration.up(db)

    assert (report.scanned, report.changed) == (4, 4)
    assert report.details == {"pending_platform_lead_invitations": 4, "unexpired": 2}
    after = _statuses(db)
    revoked = {"plat-lead-link", "plat-lead-email", "plat-lead-link-expired", "plat-lead-email-expired"}
    assert {key for key, status in after.items() if status == "revoked" and before[key] == "pending"} == revoked
    assert {key: after[key] for key in after if key not in revoked} == {
        key: before[key] for key in before if key not in revoked
    }
    assert _doc(db, "plat-lead-link")["updated_at"]

    rerun = migration.up(db)

    assert (rerun.scanned, rerun.changed) == (0, 0)
    assert _statuses(db) == after


def test_a_revoked_platform_lead_invitation_can_no_longer_be_found_as_pending(db):
    """The revocation is the state every reader of a pending invitation already honours."""
    _invite(db, "plat-lead-email", kind=InvitationType.EMAIL)
    migration.up(db)

    pending = ArangoInvitationRepository(db).list_pending_email_invitations("someone@example.org")

    assert pending == []


def test_a_lead_invitation_into_an_ordinary_tenant_is_never_swept(db):
    _invite(db, "garden-lead", tenant=GARDEN)

    report = migration.up(db)

    assert (report.scanned, report.changed) == (0, 0)
    assert _statuses(db) == {"garden-lead": "pending"}


# ── review W-2: the layouts a volume really holds ────────────────────────────


def test_on_the_seeded_layout_the_flagged_row_and_the_literal_key_are_both_swept(db):
    """The seed gives the platform row a generated key and the flag; the admin membership names ``platform``."""
    from app.data_access.arango.membership_repository import ArangoMembershipRepository
    from app.data_access.arango.tenant_repository import ArangoTenantRepository
    from app.migrations.seed_auth import _ensure_platform_admin

    db.collection(col.TENANTS).delete(PLATFORM)
    _ensure_platform_admin("u-admin", ArangoTenantRepository(db), ArangoMembershipRepository(db))
    (row,) = [t for t in db.collection(col.TENANTS).all() if t["slug"] == "platform"]
    assert row["_key"] != PLATFORM and row["is_platform"] is True  # the measured layout
    _invite(db, "row-lead", tenant=row["_key"])
    _invite(db, "literal-lead", tenant=PLATFORM)  # no tenant row carries this key any more
    _invite(db, "garden-lead", tenant=GARDEN)

    report = migration.up(db)

    assert report.changed == 2
    assert _statuses(db) == {"row-lead": "revoked", "literal-lead": "revoked", "garden-lead": "pending"}


def test_a_row_keyed_platform_without_the_flag_is_swept(db):
    db.collection(col.TENANTS).update({"_key": PLATFORM, "is_platform": False})
    _invite(db, "plat-lead-link")

    assert migration.up(db).changed == 1
    assert _statuses(db) == {"plat-lead-link": "revoked"}
