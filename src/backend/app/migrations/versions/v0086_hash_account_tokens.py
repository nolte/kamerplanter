"""v0086 - #2158: hash the password-reset and e-mail-verification tokens stored in clear.

Until #2158 ``users.password_reset_token`` and ``users.email_verification_token``
held the raw token the mail carried, and the lookups matched it by value: a read of
the database or of a backup was a working reset link (1 h) or verification link
(24 h) for every account with one pending. The model now keeps only the SHA-256
digest under ``password_reset_token_hash`` / ``email_verification_token_hash`` and
the services hash what a link presents before looking it up.

**Why hash rather than clear.** Both tokens are short-lived, so clearing them would
also be safe; it would however break every link mailed in the hour (reset) or day
(verification) before the upgrade, and an account whose verification link dies has
to ask for a new one before it can sign in at all (REQ-023 §3.2b). Hashing keeps
those links working exactly once and leaves no clear value behind, so it costs the
user nothing. The digest is computed by AQL ``SHA256()``, which is the lowercase
hex SHA-256 of the UTF-8 string - the same value ``TokenEngine.hash_token``
produces in Python (``hashlib.sha256(token.encode()).hexdigest()``), measured in
``tests/integration/test_credential_tokens_at_rest.py``.

The old attributes are removed (``UNSET``): the user repository's full-replace
keeps an attribute the model does not declare, so leaving them would leave the
clear value in place forever. Expiry fields are untouched - expiry and single use
work exactly as before.

Idempotent (M-3): a re-run finds no clear attribute and changes nothing.
Irreversible (M-6): a digest cannot be turned back into the token.
"""

from __future__ import annotations

from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: The attributes the model lost, and the digest each one becomes.
_RESET_TOKEN = "password_reset_token"
_VERIFICATION_TOKEN = "email_verification_token"
_RESET_TOKEN_HASH = "password_reset_token_hash"
_VERIFICATION_TOKEN_HASH = "email_verification_token_hash"

#: Accounts that still carry a token attribute in clear (a ``null`` counts: it is
#: an attribute the model no longer declares and is removed as well).
_COUNT_AQL = """
FOR u IN @@users
  FILTER HAS(u, @reset) OR HAS(u, @verify)
  COLLECT WITH COUNT INTO n
  RETURN n
"""

_HASH_AQL = """
FOR u IN @@users
  FILTER HAS(u, @reset) OR HAS(u, @verify)
  LET reset = IS_STRING(u[@reset]) AND u[@reset] != "" ? { [@reset_hash]: SHA256(u[@reset]) } : {}
  LET verify = IS_STRING(u[@verify]) AND u[@verify] != "" ? { [@verify_hash]: SHA256(u[@verify]) } : {}
  REPLACE u WITH MERGE(UNSET(u, @reset, @verify), reset, verify) IN @@users
  RETURN 1
"""


class HashAccountTokensMigration(Migration):
    version = "0086"
    name = "hash_account_tokens"
    description = (
        "Replace the clear password-reset and e-mail-verification tokens on users with their SHA-256 "
        "digests (#2158); links mailed before the upgrade keep working once."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.USERS):
            return MigrationReport(version=self.version, name=self.name, scanned=0, changed=0, dry_run=dry_run)
        names = {"reset": _RESET_TOKEN, "verify": _VERIFICATION_TOKEN}
        pending = next(iter(cast(Cursor, db.aql.execute(_COUNT_AQL, bind_vars={"@users": col.USERS, **names}))), 0)
        details = {"accounts_with_clear_tokens": pending}
        if dry_run:
            logger.info("hash_account_tokens_migration_dry_run", **details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=pending, changed=0, dry_run=True, details=details
            )
        bind_vars: dict[str, Any] = {
            "@users": col.USERS,
            **names,
            "reset_hash": _RESET_TOKEN_HASH,
            "verify_hash": _VERIFICATION_TOKEN_HASH,
        }
        changed = sum(cast(Cursor, db.aql.execute(_HASH_AQL, bind_vars=bind_vars)))
        logger.info("hash_account_tokens_migration_applied", changed=changed)
        return MigrationReport(
            version=self.version, name=self.name, scanned=pending, changed=changed, dry_run=False, details=details
        )


migration = HashAccountTokensMigration()
