"""v0064 — bind every unambiguous provider link to the configuration it was made through (#1869).

A provider link (``auth_providers``) records ``oidc_config_slug`` and ``issuer``
since #1815 (review SEC-001); links made before carry neither. The login and the
step-up re-authentication now match a link by (configuration, ``sub``) only —
``sub`` is unique per issuer, and every generic OIDC configuration stores its links
under the one type ``oidc`` — and an unbound link matches nothing
(``AuthService._login_link``, ``FederatedReauthPolicy``). This migration binds the
links for which that is decidable, once, at deploy: an unbound link decided later
could look unambiguous only because a configuration was deleted in between.

**Per link without ``oidc_config_slug``:**

1. Exactly one configuration — **enabled or not**; a disabled one made links too —
   stores its links under the link's type → ``oidc_config_slug`` is set to it.
2. None or several → left alone. The login does not guess either: such a link
   signs nobody in; its owner is linked afresh through the e-mail auto-link path
   (verified addresses) or signs in with a password.

``issuer`` is not backfilled: the configuration's current issuer need not be the
one the link was made with. The first sign-in of the link records it.

**What this cannot decide.** A link made through a configuration that has since
been *deleted* is indistinguishable from one of the remaining configuration of the
same type; rule 1 binds it there — exactly the link the login accepted before this
migration. It widens nothing; and because an unbound link is never decided after
this run, no later deletion widens anything either.

**The unique index.** ``auth_providers`` carried a unique index over
(``provider``, ``provider_user_id``) — the same "one subject per type" assumption in
the database: the second of two identities with the same ``sub`` at two OIDC
configurations could never be linked. ``ensure_collections`` now creates the unique
index over (``provider``, ``oidc_config_slug``, ``provider_user_id``); this
migration drops the old one (after the backfill, which cannot collide under
either).

**Idempotent (M-3).** Bound links are not scanned; a second run changes nothing.

**Dry run (M-5).** Computes the plan and writes nothing.

**Not reversible (M-6).** After the run a backfilled binding is indistinguishable
from one the login wrote.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.engines.oauth_engine import OAuthEngine
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)


#: The unique index an existing volume carries from before #1869.
LEGACY_UNIQUE_FIELDS = ["provider", "provider_user_id"]


def plan_bindings(links: list[dict[str, Any]], configs: list[dict[str, Any]]) -> dict[str, str]:
    """Decide per unbound link (pure, so the rule is testable without a database).

    Args:
        links: ``{_key, provider}`` of every link without ``oidc_config_slug``.
        configs: ``{slug, provider_type}`` of every configuration, enabled or not.

    Returns:
        ``{link _key: configuration slug}`` for the links with exactly one
        configuration of their type.
    """
    slugs_by_type: dict[str, list[str]] = {}
    for config in configs:
        link_type = OAuthEngine.link_type_for(str(config.get("provider_type") or "")).value
        slugs_by_type.setdefault(link_type, []).append(str(config["slug"]))
    plan: dict[str, str] = {}
    for link in links:
        slugs = slugs_by_type.get(str(link.get("provider") or ""), [])
        if len(slugs) == 1:
            plan[str(link["_key"])] = slugs[0]
    return plan


class BindProviderLinksToConfigurationMigration(Migration):
    version = "0064"
    name = "bind_provider_links_to_configuration"
    description = (
        "Record the configuration of every provider link made before #1815 where exactly one "
        "configuration of its type exists; make the link key unique per configuration (#1869)."
    )
    reversible = False

    _LINKS_QUERY = f"""
    FOR p IN {col.AUTH_PROVIDERS}
      FILTER p.oidc_config_slug == null
      RETURN {{_key: p._key, provider: p.provider}}
    """
    _CONFIGS_QUERY = f"FOR c IN {col.OIDC_PROVIDER_CONFIGS} RETURN {{slug: c.slug, provider_type: c.provider_type}}"

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        links = list(db.aql.execute(self._LINKS_QUERY)) if db.has_collection(col.AUTH_PROVIDERS) else []
        configs = (
            list(db.aql.execute(self._CONFIGS_QUERY)) if links and db.has_collection(col.OIDC_PROVIDER_CONFIGS) else []
        )
        plan = plan_bindings(links, configs)
        legacy_indexes = self._legacy_indexes(db)
        if not dry_run:
            providers = db.collection(col.AUTH_PROVIDERS)
            for key, slug in plan.items():
                providers.update({"_key": key, "oidc_config_slug": slug}, silent=True)
            if legacy_indexes:
                # ``ensure_collections`` runs before the migrations, so the new
                # index exists; added here too so the drop never leaves none.
                providers.add_persistent_index(fields=col.AUTH_PROVIDER_UNIQUE_FIELDS, unique=True)
                for idx in legacy_indexes:
                    providers.delete_index(idx["id"], ignore_missing=True)
        logger.info(
            "bind_provider_links_to_configuration",
            scanned=len(links),
            bound=len(plan),
            left_ambiguous=len(links) - len(plan),
            legacy_unique_indexes=len(legacy_indexes),
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=len(links),
            changed=0 if dry_run else len(plan) + len(legacy_indexes),
            dry_run=dry_run,
            details={
                "bound": len(plan),
                "left_unbound": len(links) - len(plan),
                "legacy_unique_indexes_dropped": 0 if dry_run else len(legacy_indexes),
            },
        )

    @staticmethod
    def _legacy_indexes(db: StandardDatabase) -> list[dict[str, Any]]:
        if not db.has_collection(col.AUTH_PROVIDERS):
            return []
        return [
            idx
            for idx in db.collection(col.AUTH_PROVIDERS).indexes()
            if isinstance(idx, dict)
            and idx.get("type") == "persistent"
            and idx.get("unique")
            and list(idx.get("fields") or []) == LEGACY_UNIQUE_FIELDS
        ]


migration = BindProviderLinksToConfigurationMigration()
