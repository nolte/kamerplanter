"""The declared tenant-erasure inventory (REQ-024 / REQ-025 / NFR-011, #1769).

Pure logic, no I/O. :class:`TenantErasureEngine` owns the one list of what
tenant deletion does with every collection that can hold a tenant's rows;
``ArangoTenantErasureExecutor`` runs it and ``TenantService.delete_tenant`` is
its only caller. Before #1769 the deletion hand-wrote four collections
(assignments, invitations, memberships, the tenant) and left every other
tenant-scoped collection — sites, plants, diary entries, tasks, tanks, … —
behind under a ``tenant_key`` that pointed at nothing.

**Complete by construction, not by memory.** Every document collection
``collections.py`` declares is classified exactly once: an entry of
:attr:`TenantErasureEngine.INVENTORY` (delete / pseudonymize / retain), or a
reason in :attr:`TenantErasureEngine.NOT_TENANT_SCOPED`.
``tests/unit/guards/test_tenant_erasure_inventory_is_complete.py`` holds both
against ``collections.py`` and against the tenant-bearing collections derived
from the models (the #1708 derivation), so a new collection cannot be added
without being classified. The executor adds a runtime backstop: after the commit
it counts, in every collection outside the inventory, rows still stamped with the
tenant's key, and reports any as ``undeclared:<collection>`` — the deletion stays
open instead of claiming success.

**Edges are not listed.** Every edge collection is swept: an edge whose ``_from``
or ``_to`` is a deleted row (or the tenant document) goes with it. Edges between
two retained rows stay.

Collection names are spelled as literals: the domain layer does not import the
data-access constants (NFR-001), and the guard pins each literal to a
``collections.py`` value.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.legal_retention import LegalRetentionChild, LegalRetentionRule
from app.domain.models.tenant_erasure import (
    TenantErasureEntry,
    TenantErasureParent,
    TenantErasurePlan,
    TenantErasurePseudonymization,
)

_R16 = (
    "NFR-011 R-16 / CanG: harvest documentation is kept for 5 years. Every account key on the row "
    "becomes that account's tombstone hash and the free-text name is emptied; the row itself stays."
)
_R17 = (
    "NFR-011 R-17 / PflSchG section 11: treatment records are kept for 3 years. Account key "
    "pseudonymised, free-text applicator name emptied; the row stays."
)
_R18 = (
    "NFR-011 R-18 / PflSchG section 11: inspection records are kept for 3 years. Account key "
    "pseudonymised, free-text inspector name emptied; the row stays."
)
#: An inventory reason that keeps a row for one of the three legal retention rules.
_LEGAL_RETENTION_REASON = re.compile(r"\bR-1[678]\b")
_CATALOGUE = "global catalogue: every tenant reads it; the model carries no tenant_key, so no row is a tenant's"
_LEGACY_STAMP = (
    " A tenant_key stored on a row is the v0004 default-tenant backfill stamp on a seed "
    "(migrations/backfill_tenant_key.py), not ownership — deleting it would remove the seed for every tenant."
)
_ACCOUNT = "account-scoped: belongs to a user, not a tenant, and is removed by the account erasure (ErasureEngine)"
_PLATFORM = "platform configuration or bookkeeping, not tenant data"


def _parent(field: str, collection: str, **where: str) -> TenantErasureParent:
    return TenantErasureParent(field=field, collection=collection, where=where)


def _delete(collection: str, *parents: TenantErasureParent) -> TenantErasureEntry:
    return TenantErasureEntry(collection=collection, action="delete", parents=parents)


#: A tenant's erasure record is keyed ``ter_<tenant_key>``: the record key *is* the tenant key.
RECORD_KEY_PREFIX = "ter_"


class TenantErasureEngine:
    """Declares and validates what tenant deletion does with every collection."""

    #: The collection holding the tenant document itself. Removed last, by key.
    TENANT_COLLECTION = "tenants"

    #: Where the persisted proof lives (:class:`TenantErasureRecord`).
    RECORD_COLLECTION = "tenant_erasure_records"

    # ── The inventory ─────────────────────────────────────────────────
    #
    # Order is load-bearing only in one way: a collection reached through a
    # parent is declared after that parent, because the executor resolves the
    # parent's rows first (validated by :meth:`validate`).
    INVENTORY: list[TenantErasureEntry] = [
        # ── Membership, access and the tenant's own configuration ──
        _delete("memberships"),
        _delete("invitations"),
        _delete("location_assignments"),
        _delete("ai_provider_configs"),
        _delete("inventree_connections"),
        _delete("inventree_references"),
        _delete("ha_publish_settings"),  # raw repository, no model (ha_publish_repository.py)
        # ── Places ──
        _delete("sites"),
        _delete("locations", _parent("site_key", "sites")),
        _delete("slots", _parent("location_key", "locations")),
        _delete("weather_source_configs"),
        _delete("weather_forecasts"),
        _delete("climate_normals"),
        _delete("season_states"),
        # ── Tanks, equipment, control ──
        _delete("tanks"),
        _delete("tank_states", _parent("tank_key", "tanks")),
        _delete("tank_fill_events", _parent("tank_key", "tanks")),
        _delete("maintenance_logs", _parent("tank_key", "tanks")),
        _delete("maintenance_schedules", _parent("tank_key", "tanks")),
        _delete(
            "sensors",
            _parent("tank_key", "tanks"),
            _parent("site_key", "sites"),
            _parent("location_key", "locations"),
        ),
        _delete("equipment"),
        _delete("actuators"),
        _delete("control_rules"),
        _delete("control_schedules"),
        _delete("control_events"),
        _delete("manual_overrides"),
        _delete("phase_control_profiles"),
        _delete("aquaponic_systems"),
        _delete("fish_stocks"),
        _delete("fish_feeding_events"),
        _delete("water_tests"),
        # ── Tenant-owned rows of the hybrid catalogues (``tenant_key == ""`` is global and never matches) ──
        # A tenant-owned species/cultivar another tenant was granted
        # (``tenant_has_access``, #1638) stays: that tenant's plants point at it.
        TenantErasureEntry(collection="species", action="delete", keep_if_granted_via="tenant_has_access"),
        TenantErasureEntry(collection="cultivars", action="delete", keep_if_granted_via="tenant_has_access"),
        _delete("fertilizers"),
        _delete("fertilizer_stocks"),
        _delete("stock_transactions"),
        _delete("nutrient_plans"),
        _delete("nutrient_plan_phase_entries", _parent("plan_key", "nutrient_plans")),
        _delete("substrates"),
        _delete("substrate_batches"),
        # A system seed the v0004 backfill stamped with this tenant is not its row.
        TenantErasureEntry(collection="activities", action="delete", keep_when=({"is_system": True},)),
        # A system seed the v0004 backfill stamped with this tenant is not its row.
        TenantErasureEntry(collection="workflow_templates", action="delete", keep_when=({"is_system": True},)),
        _delete("workflow_phases", _parent("workflow_template_key", "workflow_templates")),
        _delete("task_templates"),
        # ── Plants and runs ──
        _delete("plant_instances"),
        _delete("planting_runs"),
        _delete("planting_run_entries"),
        _delete("succession_plans"),
        _delete("propagation_batches"),
        _delete("propagation_events"),
        _delete("rooting_protocols"),
        _delete("overwintering_profiles"),
        _delete("phenotype_notes"),
        _delete("care_profiles", _parent("plant_key", "plant_instances")),
        _delete("care_confirmations", _parent("plant_key", "plant_instances")),
        _delete("phase_histories", _parent("plant_instance_key", "plant_instances")),
        _delete("harvest_observations", _parent("plant_key", "plant_instances")),
        _delete("plant_diary_entries"),
        _delete("feeding_events"),
        _delete("watering_events"),
        _delete("watering_logs"),
        _delete("irrigation_demands"),
        _delete("supplementation_events"),
        # ── Harvest and post-harvest ──
        TenantErasureEntry(collection="harvest_batches", action="pseudonymize", reason=_R16),
        TenantErasureEntry(
            collection="quality_assessments",
            action="pseudonymize",
            parents=(_parent("batch_key", "harvest_batches"),),
            reason=_R16,
        ),
        TenantErasureEntry(
            collection="yield_metrics",
            action="retain",
            parents=(_parent("batch_key", "harvest_batches"),),
            reason="NFR-011 R-16 / CanG: part of the harvest documentation; the row carries no account reference.",
        ),
        _delete("post_harvest_batches"),
        _delete("drying_progress", _parent("batch_key", "post_harvest_batches")),
        _delete("storage_observations", _parent("batch_key", "post_harvest_batches")),
        _delete("mold_alerts", _parent("batch_key", "post_harvest_batches")),
        _delete("burping_events", _parent("batch_key", "post_harvest_batches")),
        # ── Plant protection ──
        TenantErasureEntry(collection="treatment_applications", action="pseudonymize", reason=_R17),
        TenantErasureEntry(collection="inspections", action="pseudonymize", reason=_R18),
        _delete("pest_detections"),
        _delete("plant_diagnosis_requests"),
        _delete("identification_requests"),
        # Declared and indexed on ``tenant_key`` in collections.py; no code path writes it today.
        _delete("diagnosis_requests"),
        _delete("pest_image_contributions"),
        # ── Work ──
        _delete("tasks"),
        _delete("task_comments", _parent("task_key", "tasks")),
        _delete("task_audit_entries", _parent("task_key", "tasks")),
        _delete(
            "workflow_executions",
            _parent("entity_key", "plant_instances", entity_type="plant_instance"),
            _parent("entity_key", "locations", entity_type="location"),
            _parent("entity_key", "tanks", entity_type="tank"),
            _parent("entity_key", "planting_runs", entity_type="planting_run"),
        ),
        # ── Members' own rows inside the tenant ──
        _delete("notifications"),
        _delete("calendar_feeds"),
        _delete("ai_conversations"),
        _delete("ai_tip_cache"),
        _delete("import_jobs"),
        _delete("attachments"),
        _delete("mcp_idempotency_record"),
        # #1769 review GDPR-007 — an API key restricted to this tenant
        # (``tenant_scope``) authorises nothing once the tenant is gone; its
        # label and IP allowlist are the member's. Account-scoped keys stay.
        TenantErasureEntry(collection="api_keys", action="delete", tenant_field="tenant_scope"),
        # ── Audit logs with their own retention purge ──
        TenantErasureEntry(
            collection="ai_audit_log",
            action="retain",
            reason=(
                "REQ-031 section 7.4: the AI audit log is kept for its 30-day window and purged by "
                "ai_tasks (purge of ai_audit_log past the retention window); it outlives the tenant by design."
            ),
        ),
        TenantErasureEntry(
            collection="mcp_audit_log",
            action="retain",
            reason=(
                "REQ-033 / NFR-011: the MCP tool-call audit log is kept for MCP_AUDIT_RETENTION_DAYS and "
                "purged by mcp_tasks; it outlives the tenant by design."
            ),
        ),
        # ── The proof of this very deletion ──
        TenantErasureEntry(
            collection="tenant_erasure_records",
            action="retain",
            reason=(
                "REQ-025 / Art. 5(2) accountability: the record proves the tenant deletion and drives its retry, "
                "so it must outlive the tenant. It names no tenant name, slug or owner."
            ),
        ),
    ]

    #: Every other document collection, with the reason it holds no tenant's rows.
    NOT_TENANT_SCOPED: dict[str, str] = {
        # Accounts.
        "users": _ACCOUNT,
        "auth_providers": _ACCOUNT,
        "refresh_tokens": _ACCOUNT,
        "consent_records": _ACCOUNT,
        "processing_restrictions": _ACCOUNT,
        "data_export_requests": _ACCOUNT,
        "email_change_requests": _ACCOUNT,
        "erasure_requests": _ACCOUNT + " (the Art. 17 proof, NFR-011 R-06)",
        "notification_preferences": _ACCOUNT,
        "onboarding_states": _ACCOUNT + "." + _LEGACY_STAMP.replace("on a seed", "on the account's wizard state"),
        "user_preferences": _ACCOUNT + "." + _LEGACY_STAMP.replace("on a seed", "on the account's preferences"),
        # Global catalogues.
        "pests": _CATALOGUE + "." + _LEGACY_STAMP,
        "diseases": _CATALOGUE + "." + _LEGACY_STAMP,
        "treatments": _CATALOGUE + "." + _LEGACY_STAMP,
        "harvest_indicators": _CATALOGUE + "." + _LEGACY_STAMP,
        "beneficials": _CATALOGUE,
        "botanical_families": _CATALOGUE,
        "fish_species": _CATALOGUE,
        "growth_phases": _CATALOGUE + " (children of a species lifecycle)",
        "lifecycle_configs": _CATALOGUE + " (children of a species)",
        "nutrient_profiles": _CATALOGUE + " (children of a growth phase)",
        "requirement_profiles": _CATALOGUE + " (children of a growth phase)",
        "phase_transition_rules": _CATALOGUE,
        "phase_definitions": _CATALOGUE,
        "phase_sequences": _CATALOGUE,
        "phase_sequence_entries": _CATALOGUE,
        "hardiness_zones": _CATALOGUE,
        "location_types": _CATALOGUE,
        "overwintering_profile_templates": _CATALOGUE,
        "starter_kits": _CATALOGUE,
        "glossary_terms": _CATALOGUE,
        "glossary_term_cache": _CATALOGUE + " (REQ-029 glossary cache, not tenant-scoped, section 6)",
        "external_sources": _CATALOGUE + " (enrichment source registry)",
        "external_mappings": _CATALOGUE + " (species/cultivar to external ids)",
        "sync_runs": _CATALOGUE + " (enrichment runs)",
        "reference_image_jobs": _CATALOGUE + " (species reference-image fetch jobs)",
        # Platform.
        "oidc_provider_configs": _PLATFORM,
        "system_settings": _PLATFORM,
        "schema_migrations": _PLATFORM,
    }

    # ── What happens to the rows that stay (NFR-011 §2.3, #1789) ────────
    #
    # The ``pseudonymize``/``retain`` entries above keep R-16..R-18 rows past the
    # tenant. These rules say when they go: ``retention.purge_expired_legal_retention_rows``
    # removes a row whose tenant no longer exists once its period, counted from
    # ``date_field``, has run out — with its children and every edge touching
    # either. :meth:`validate` holds the rules to the inventory, so a row kept
    # for a retention law cannot lack a purge, and a purge cannot reach a
    # collection this inventory deletes outright.
    LEGAL_RETENTION_RULES: tuple[LegalRetentionRule, ...] = (
        LegalRetentionRule(
            rule="R-16",
            collection="harvest_batches",
            date_field="harvest_date",
            fallback_date_field="created_at",
            children=(
                LegalRetentionChild(collection="quality_assessments", parent_field="batch_key"),
                LegalRetentionChild(collection="yield_metrics", parent_field="batch_key"),
            ),
        ),
        LegalRetentionRule(rule="R-17", collection="treatment_applications", date_field="applied_at"),
        LegalRetentionRule(rule="R-18", collection="inspections", date_field="inspected_at"),
    )

    # ── Retry lifecycle (the #1666 shape of the account erasure) ────────
    #: The n-th failed attempt defers the next by ``2 ** (n - 1)`` days, capped.
    RETRY_MAX_DELAY_DAYS = 7
    #: A claim older than this is taken to belong to a crashed run.
    STALE_AFTER_HOURS = 6
    #: The n-th consecutive failed attempt escalates the deletion to the operator
    #: (an error-level ``tenant_erasure.escalated`` event and ``escalated_at`` on the
    #: record, #1792): a failure that deterministic needs a person, not the next retry.
    ESCALATE_AFTER_ATTEMPTS = 3

    @classmethod
    def validate(cls) -> None:
        """Refuse an inventory the executor would have to guess at.

        Each collection once; each parent declared before its child and not
        itself reached only through ``retain``; every ``pseudonymize`` entry backed
        by at least one account-erasure ``tombstone_hash`` rule.
        """
        seen: dict[str, TenantErasureEntry] = {}
        for entry in cls.INVENTORY:
            if entry.collection in seen:
                msg = f"tenant-erasure inventory names '{entry.collection}' twice"
                raise ValueError(msg)
            if entry.collection in cls.NOT_TENANT_SCOPED or entry.collection == cls.TENANT_COLLECTION:
                msg = f"'{entry.collection}' is both inventoried and declared not tenant-scoped"
                raise ValueError(msg)
            for parent in entry.parents:
                if parent.collection not in seen:
                    msg = (
                        f"tenant-erasure entry '{entry.collection}' is reached via '{parent.collection}', "
                        "which is not declared before it"
                    )
                    raise ValueError(msg)
            if entry.action == "pseudonymize" and not cls._pseudonymizations_for(entry.collection):
                msg = f"'{entry.collection}' is pseudonymised but the account erasure declares no tombstone rule for it"
                raise ValueError(msg)
            seen[entry.collection] = entry
        cls._validate_legal_retention_rules(seen)

    @classmethod
    def _validate_legal_retention_rules(cls, inventory: dict[str, TenantErasureEntry]) -> None:
        """Every row kept for R-16..R-18 has a purge rule, and every rule reaches only kept rows (#1789)."""
        covered: set[str] = set()
        for rule in cls.LEGAL_RETENTION_RULES:
            anchor = inventory.get(rule.collection)
            if anchor is None or anchor.action == "delete" or anchor.parents:
                msg = f"{rule.rule} purges '{rule.collection}', which the inventory does not keep under its tenant key"
                raise ValueError(msg)
            covered.add(rule.collection)
            for child in rule.children:
                entry = inventory.get(child.collection)
                reached = entry is not None and any(
                    parent.collection == rule.collection and parent.field == child.parent_field
                    for parent in entry.parents
                )
                if entry is None or entry.action == "delete" or not reached:
                    msg = f"{rule.rule} purges '{child.collection}' as a child the inventory does not keep through it"
                    raise ValueError(msg)
                covered.add(child.collection)
        kept_for_a_rule = {
            name
            for name, entry in inventory.items()
            if entry.action != "delete" and entry.reason and _LEGAL_RETENTION_REASON.search(entry.reason)
        }
        if kept_for_a_rule != covered:
            msg = f"rows kept for NFR-011 R-16..R-18 without a purge rule: {sorted(kept_for_a_rule - covered)}"
            raise ValueError(msg)

    @classmethod
    def pseudonymized_account_fields(cls) -> frozenset[tuple[str, str]]:
        """``(collection, account field)`` pairs a tenant deletion rewrites to the tombstone hash.

        The Art. 15 walk matches the subject's tombstone on exactly these fields
        (REQ-025 §3.1.2 rule 6, #1793): derived, so a collection added as
        ``pseudonymize`` is disclosed by tombstone without a second list.
        """
        return frozenset(
            (rule.collection, rule.user_field)
            for entry in cls.INVENTORY
            if entry.action == "pseudonymize"
            for rule in cls._pseudonymizations_for(entry.collection)
        )

    @staticmethod
    def _pseudonymizations_for(collection: str) -> list[TenantErasurePseudonymization]:
        """The account-erasure ``tombstone_hash`` rules of *collection*, as tenant-erasure rules.

        Read, never copied: the fields a retained harvest/treatment/inspection row
        names an account in are declared once, on the account erasure (#1669),
        and both erasures act on the same fields.
        """
        return [
            TenantErasurePseudonymization(
                collection=rule.collection,
                user_field=rule.user_field,
                clear_fields=tuple(rule.clear_fields),
            )
            for rule in ErasureEngine.ANONYMIZE_COLLECTIONS
            if rule.collection == collection and rule.replacement_strategy == "tombstone_hash"
        ]

    def build_plan(
        self, tenant_key: str, *, known_parent_keys: dict[str, list[str]] | None = None
    ) -> TenantErasurePlan:
        """The plan for one tenant: the inventory, its pseudonymisations and the residue exemptions."""
        self.validate()
        pseudonymizations = [
            rule
            for entry in self.INVENTORY
            if entry.action == "pseudonymize"
            for rule in self._pseudonymizations_for(entry.collection)
        ]
        exempt = [entry.collection for entry in self.INVENTORY if entry.action == "retain"]
        exempt.extend(self.NOT_TENANT_SCOPED)
        return TenantErasurePlan(
            tenant_key=tenant_key,
            tenant_collection=self.TENANT_COLLECTION,
            entries=list(self.INVENTORY),
            pseudonymizations=pseudonymizations,
            residue_exempt=exempt,
            known_parent_keys=dict(known_parent_keys or {}),
        )

    @classmethod
    def classified_collections(cls) -> set[str]:
        """Every collection name this engine classifies (inventory, exemptions, the tenant)."""
        return {entry.collection for entry in cls.INVENTORY} | set(cls.NOT_TENANT_SCOPED) | {cls.TENANT_COLLECTION}

    @staticmethod
    def record_key(tenant_key: str) -> str:
        """The document key of a tenant's erasure record: one per tenant, so two deletions collide."""
        return f"{RECORD_KEY_PREFIX}{tenant_key}"

    @classmethod
    def next_attempt_at(cls, attempt: int, now: datetime) -> datetime:
        """The backoff horizon after the *attempt*-th failed run (1, 2, 4, 7, 7, … days)."""
        delay_days = min(2 ** max(attempt - 1, 0), cls.RETRY_MAX_DELAY_DAYS)
        # recurrence-owner-ok: a retry backoff after a failed tenant-erasure attempt, not a calendar recurrence
        return now + timedelta(days=delay_days)
