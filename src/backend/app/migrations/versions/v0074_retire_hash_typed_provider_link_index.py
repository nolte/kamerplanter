"""v0074 — drop the hash-typed ``auth_providers(provider, provider_user_id)`` index v0064 missed (#2034).

``v0064`` (#1869) bound every unambiguous provider link to its configuration and
replaced the unique index over (``provider``, ``provider_user_id``) — "one subject
per link type" — with one over (``provider``, ``oidc_config_slug``,
``provider_user_id``), so the same ``sub`` at two OIDC configurations can be linked
to two identities. It found the old index with ``type == "persistent"``. A volume
first booted before 2026-06-07 created that index with ``add_hash_index``
(``516bcd832^:…/collections.py:1178``), and ArangoDB 3.12 reports it as
``type: "hash"`` — so v0064 left it in place. Measured on 3.12.8: after v0064 a link
for the same ``sub`` through a second configuration is still refused with ``[ERR
1210] unique constraint violated - in index … of type hash over 'provider,
provider_user_id'``; the per-configuration binding was cosmetic on those volumes.

v0064 is shipped, so its class is frozen (M-7); this version is the correction.
It drops every unique index on exactly (``provider``, ``provider_user_id``), ``hash``
or ``persistent``, through the shared selector
(:mod:`app.migrations.support.legacy_indexes`). The non-unique ``user_key`` index and
any non-unique index on the same fields are left alone.

**Never without the replacement.** The drop happens only while the unique index
over ``AUTH_PROVIDER_UNIQUE_FIELDS`` exists — ``ensure_collections`` creates it
before any migration runs. If it is missing, nothing is dropped and the run reports
``precondition_unmet`` with the counts, so the runner leaves this version (and every
later one) pending and a later boot retries it.

Idempotent (M-3): a re-run finds no legacy index → ``changed == 0``. Dry-run (M-5)
counts and drops nothing. Irreversible (M-6): the dropped index is the constraint
#1869 retired.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import IndexShape, retire_legacy_index
from app.migrations.versions.v0064_bind_provider_links_to_configuration import LEGACY_UNIQUE_FIELDS

logger = structlog.get_logger(__name__)

#: The constraint #1869 retired: one subject per link type, across configurations.
LEGACY_PROVIDER_LINK_INDEX = IndexShape(fields=tuple(LEGACY_UNIQUE_FIELDS), unique=True)

#: Its replacement, as ``ensure_collections`` and v0064 create it.
PROVIDER_LINK_INDEX = IndexShape(fields=tuple(col.AUTH_PROVIDER_UNIQUE_FIELDS), unique=True)


class RetireHashTypedProviderLinkIndexMigration(Migration):
    version = "0074"
    name = "retire_hash_typed_provider_link_index"
    description = (
        "Drop the unique auth_providers(provider, provider_user_id) index of type hash that "
        "v0064 missed, once the per-configuration replacement exists (#2034)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.AUTH_PROVIDERS):
            return MigrationReport(version=self.version, name=self.name, dry_run=dry_run)
        outcome = retire_legacy_index(
            db.collection(col.AUTH_PROVIDERS),
            legacy=LEGACY_PROVIDER_LINK_INDEX,
            replacement=PROVIDER_LINK_INDEX,
            dry_run=dry_run,
        )
        if outcome.refused:
            logger.warning("retire_hash_typed_provider_link_index_refused", **outcome.details())
        else:
            logger.info("retire_hash_typed_provider_link_index", dry_run=dry_run, **outcome.details())
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(outcome.legacy_ids),
            changed=outcome.dropped,
            dry_run=dry_run,
            precondition_unmet=outcome.refused,
            details=outcome.details(),
        )


migration = RetireHashTypedProviderLinkIndexMigration()
