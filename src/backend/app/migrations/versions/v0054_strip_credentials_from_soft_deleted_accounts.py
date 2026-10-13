"""v0054 — remove the credential left on accounts soft-deleted before #1525.

``ArangoUserRepository`` ran in merge mode until #1525, so ``password_hash = None``
never reached the store. ``PrivacyService.request_erasure`` wrote ``is_active = False``
and kept the bcrypt hash of an account whose erasure the user had requested, for the
90 days until the hard delete (NFR-011 R-01) — and at the time this migration was
written ``login_local`` did **not** gate on ``is_active`` (#1528), so the hash was
usable, not merely present. It gates since #1551, which is why this paragraph is in
the past tense: the rows this migration cleans up are no longer reachable through
the local login even before it runs.

#1525 fixes the write. This migration deals with the rows written before it.

**Only one of the two soft-delete paths can have left rows.** ``UserService
.delete_account`` wrote the tombstone address ``deleted_<key>@deleted.local``, which
``EmailStr`` refuses as a special-use name, so the repository's model re-validation
(#968) raised and **nothing** was persisted — not even ``is_active = False``. That
path therefore left no soft-deleted rows anywhere, by construction rather than by
measurement. ``request_erasure`` does not touch the address and did write.

**Scoped by the erasure request, never by ``is_active`` alone.** A deactivated account
is not necessarily a deleted one: a platform admin can set ``is_active = False``
through ``PATCH /admin/platform/users/{key}`` (``AdminUserUpdate``), and that is
**reversible** — stripping the password of a temporarily suspended account would lock
its owner out permanently and silently. The population is therefore the intersection:
inactive **and** named by an ``ErasureRequest``, or inactive **and** already carrying a
tombstone address. Both spellings are matched, because the tombstone domain changed in
#1525 and a row could exist under either.

**Measured before writing.** Against the kind installation on 2026-09-18:

    inactive users: 0 · with surviving hash: 0 · erasure_requests: 0 · users: 1

so this migration is a no-op *there*. It exists for installations where somebody
exercised Art. 17: the count is a property of the deployment, not of the schema, and a
migration that only runs where the developer happened to have data is the "inert
guard" shape. The falsification in the unit test seeds the population explicitly.

**Not reversible (M-6).** A bcrypt hash that has been removed cannot be reconstructed,
and reconstructing it is the opposite of the point. ``reversible = False`` rather than
a faked inverse. The affected accounts are unaffected in practice: they are awaiting
hard deletion, and a user who wants back in uses the password-reset flow.

**Idempotent (M-3).** The scan only matches documents that still *have* the attribute,
so a second run reports ``changed == 0``. The write removes the attributes rather than
setting them to ``null`` (``keep_none=False``), matching what #1525's repository now
does, so a re-run cannot find its own output.

**On the version number.** This module was written as ``0053`` and renumbered to
``0054`` when #1505 (``v0053_recompute_care_profiles_newly_mapped_families``) landed on
``develop`` first — the collision ``app/migrations/README.md`` describes, resolved the
way it prescribes: whoever lands second rebases and renames *before* the merge, all of
it at once (module file, ``version`` string, integration-test module and its imports).
Safe because it has been applied nowhere: M-7 pins an *applied* migration to its number
and its checksum, and renumbering after that is the thing M-7 forbids.

``discovery.validate_sequence`` enforces gapless numbering from ``0001`` (M-1) and that
check sits on the application's startup path, so a number cannot be reserved ahead of a
branch that has not landed — which is why the collision is resolved after the fact
rather than avoided in advance. v0047, v0049 and v0052 record the same collision and
the same resolution. **#1524 therefore takes ``0055``**, not ``0054``.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

#: The attributes a soft-delete is supposed to remove (REQ-025 Szenario 3).
_CREDENTIAL_FIELDS = ("password_hash", "avatar_url")


class StripCredentialsFromSoftDeletedAccountsMigration(Migration):
    version = "0054"
    name = "strip_credentials_from_soft_deleted_accounts"
    description = "Remove password_hash/avatar_url left on accounts soft-deleted before #1525."
    reversible = False

    #: Inactive **and** provably deleted — never inactive alone (see the module
    #: docstring: admin deactivation is reversible and must keep its credential).
    #:
    #: ``LIKE(..., true)`` is case-insensitive; the ``\\_`` escapes AQL's single-character
    #: wildcard so ``deleted_`` matches the literal underscore and not any character.
    #: Both tombstone domains are accepted: ``deleted.local`` could only ever have been
    #: written by a path that raised, but matching it costs nothing and a row that
    #: somehow carries it is unambiguously deleted.
    _SCAN_QUERY = f"""
    FOR u IN {col.USERS}
      FILTER u.is_active == false
      FILTER u.password_hash != null OR u.avatar_url != null
      LET erasure_requested = LENGTH(
        FOR e IN {col.ERASURE_REQUESTS}
          FILTER e.user_key == u._key
          LIMIT 1
          RETURN 1
      ) > 0
      LET tombstoned = LIKE(u.email, "deleted\\\\_%@deleted.example.com", true)
        OR LIKE(u.email, "deleted\\\\_%@deleted.local", true)
      FILTER erasure_requested OR tombstoned
      RETURN u._key
    """

    _TOTAL_QUERY = f"RETURN LENGTH({col.USERS})"

    def _plan(self, db: StandardDatabase) -> tuple[int, list[str]]:
        """Return ``(scanned, keys to strip)`` without writing.

        Pure, so ``dry_run`` reports the numbers the real run would produce (M-5).
        """
        if not db.has_collection(col.USERS) or not db.has_collection(col.ERASURE_REQUESTS):
            return (0, [])
        scanned = int(next(iter(db.aql.execute(self._TOTAL_QUERY)), 0))
        keys = [str(k) for k in db.aql.execute(self._SCAN_QUERY)]
        return (scanned, keys)

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        scanned, keys = self._plan(db)

        if not dry_run and keys:
            users = db.collection(col.USERS)
            for key in keys:
                # ``keep_none=False`` **removes** the attributes rather than storing an
                # explicit ``null`` — the same end state #1525's full-replace repository
                # produces, so a document repaired here is indistinguishable from one
                # written by the fixed code, and the scan above cannot rediscover it.
                users.update(
                    {"_key": key, **dict.fromkeys(_CREDENTIAL_FIELDS)},
                    keep_none=False,
                    silent=True,
                )

        logger.info(
            "strip_credentials_from_soft_deleted_accounts",
            scanned=scanned,
            stripped=len(keys),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=0 if dry_run else len(keys),
            dry_run=dry_run,
            # Keys only — never the values. This migration's whole subject is a
            # credential, and a migration report is logged and stored.
            details={"stripped": len(keys), "keys": keys},
        )


migration = StripCredentialsFromSoftDeletedAccountsMigration()
