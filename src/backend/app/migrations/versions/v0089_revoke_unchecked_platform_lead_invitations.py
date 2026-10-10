"""v0089 - #2180: revoke the pending ``lead`` invitations into the platform tenant issued without the rank rule.

``lead`` in the platform tenant is the platform role (REQ-049 §2.5, ``is_platform_admin``
reads it). Until #2084 the invitation routes handed it out without asking who issued it,
so a ``management`` holder of the platform tenant who is not its lead could invite anyone
- themselves under a second address included - as platform admin. #2084 put the rule
(REQ-024 AK-58) on issuance; #2180 puts it on acceptance as well, against the issuer's
role *now*. What neither reaches is an invitation issued before #2084 by someone who
has since become the platform tenant's lead: the acceptance check then passes.

The operator decided (2026-10-09) to take every such invitation back rather than tell a
legitimate one from an illegitimate one after the fact: nothing stored says which rule
an invitation was issued under. This migration revokes **every pending invitation into
the platform tenant with role** ``lead``, of either type, expired or not.

Why no date bound
-----------------
#2084 is not in a release yet, and a release installation upgrades straight from code
without the rule to code with it: every platform-lead invitation that exists when this
migration first runs there was issued without it. An installation tracking ``develop``
may also lose a few issued under the rule since #2084; those people are invited again
(the changelog says so). The runner applies a version once (NFR-016 M-2), so an
invitation issued after the upgrade is never touched by it.

What it changes and reports
---------------------------
``status`` becomes ``revoked`` and ``updated_at`` is stamped - exactly what
``TenantService.revoke_invitation`` writes. Nothing else: the invitee's address stays as
it was until the invitation's normal retention ends. The report counts the revoked rows
and how many of them were still unexpired (the ones that could have been accepted); the
log line carries the counts only, never a key, an address or a token digest.

**Idempotent (M-3).** A revoked invitation is no longer pending; a second run finds none
and changes nothing.

**Dry run (M-5).** Counts what would be revoked; writes nothing.

**Not reversible (M-6).** Re-opening an invitation of unknown provenance is exactly what
this migration exists to prevent.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.common.enums import InvitationStatus, TenantRole
from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: The pending ``lead`` invitations into a platform tenant; each row says whether it is unexpired.
#: ``DATE_TIMESTAMP`` parses whatever ISO-8601 spelling ``expires_at`` was stored in.
_SELECT = """
LET platforms = (FOR t IN @@tenants FILTER t.is_platform == true RETURN t._key)
FOR i IN @@invitations
  FILTER i.tenant_key IN platforms AND i.role == @lead AND i.status == @pending
"""

_COUNT_AQL = (
    _SELECT
    + """
  COLLECT unexpired = (DATE_TIMESTAMP(i.expires_at) > DATE_NOW()) WITH COUNT INTO n
  RETURN {unexpired, n}
"""
)

_REVOKE_AQL = (
    _SELECT
    + """
  UPDATE i WITH {status: @revoked, updated_at: @now} IN @@invitations
  RETURN 1
"""
)


class RevokeUncheckedPlatformLeadInvitationsMigration(Migration):
    version = "0089"
    name = "revoke_unchecked_platform_lead_invitations"
    description = (
        "Revoke every pending lead invitation into the platform tenant (#2180): it may have been "
        "issued before the rank rule (#2084) existed; the invitees are invited again."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not (db.has_collection(col.INVITATIONS) and db.has_collection(col.TENANTS)):
            return MigrationReport(version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run)
        bind_vars: dict[str, str] = {
            "@tenants": col.TENANTS,
            "@invitations": col.INVITATIONS,
            "lead": TenantRole.LEAD.value,
            "pending": InvitationStatus.PENDING.value,
        }
        counts = {
            bool(row["unexpired"]): int(row["n"])
            for row in cast(Cursor, db.aql.execute(_COUNT_AQL, bind_vars=bind_vars))
        }
        pending = sum(counts.values())
        details = {"pending_platform_lead_invitations": pending, "unexpired": counts.get(True, 0)}
        if dry_run:
            logger.info("revoke_platform_lead_invitations_dry_run", **details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=pending, changed=0, dry_run=True, details=details
            )
        changed = sum(
            cast(
                Cursor,
                db.aql.execute(
                    _REVOKE_AQL,
                    bind_vars={
                        **bind_vars,
                        "revoked": InvitationStatus.REVOKED.value,
                        "now": datetime.now(UTC).isoformat(),
                    },
                ),
            )
        )
        logger.info("revoke_platform_lead_invitations_applied", revoked=changed, unexpired=details["unexpired"])
        return MigrationReport(
            version=self.version, name=self.name, scanned=pending, changed=changed, dry_run=False, details=details
        )


migration = RevokeUncheckedPlatformLeadInvitationsMigration()
