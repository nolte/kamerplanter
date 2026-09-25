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
:attr:`TenantErasureEngine.INVENTORY` (delete / anonymise / retain), or a
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

from datetime import datetime, timedelta

from app.domain.engines.erasure_engine import ErasureEngine
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
        _delete("species"),
        _delete("cultivars"),
        _delete("fertilizers"),
        _delete("fertilizer_stocks"),
        _delete("stock_transactions"),
        _delete("nutrient_plans"),
        _delete("nutrient_plan_phase_entries", _parent("plan_key", "nutrient_plans")),
        _delete("substrates"),
        _delete("substrate_batches"),
        _delete("activities"),
        _delete("workflow_templates"),
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
        TenantErasureEntry(collection="harvest_batches", action="anonymize", reason=_R16),
        TenantErasureEntry(
            collection="quality_assessments",
            action="anonymize",
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
        TenantErasureEntry(collection="treatment_applications", action="anonymize", reason=_R17),
        TenantErasureEntry(collection="inspections", action="anonymize", reason=_R18),
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
        "api_keys": _ACCOUNT,
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

    # ── Retry lifecycle (the #1666 shape of the account erasure) ────────
    #: The n-th failed attempt defers the next by ``2 ** (n - 1)`` days, capped.
    RETRY_MAX_DELAY_DAYS = 7
    #: A claim older than this is taken to belong to a crashed run.
    STALE_AFTER_HOURS = 6

    @classmethod
    def validate(cls) -> None:
        """Refuse an inventory the executor would have to guess at.

        Each collection once; each parent declared before its child and not
        itself reached only through ``retain``; every ``anonymize`` entry backed
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
            if entry.action == "anonymize" and not cls._pseudonymizations_for(entry.collection):
                msg = f"'{entry.collection}' is anonymised but the account erasure declares no tombstone rule for it"
                raise ValueError(msg)
            seen[entry.collection] = entry

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

    def build_plan(self, tenant_key: str) -> TenantErasurePlan:
        """The plan for one tenant: the inventory, its pseudonymisations and the residue exemptions."""
        self.validate()
        pseudonymizations = [
            rule
            for entry in self.INVENTORY
            if entry.action == "anonymize"
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
        )

    @classmethod
    def classified_collections(cls) -> set[str]:
        """Every collection name this engine classifies (inventory, exemptions, the tenant)."""
        return {entry.collection for entry in cls.INVENTORY} | set(cls.NOT_TENANT_SCOPED) | {cls.TENANT_COLLECTION}

    @staticmethod
    def record_key(tenant_key: str) -> str:
        """The document key of a tenant's erasure record: one per tenant, so two deletions collide."""
        return f"ter_{tenant_key}"

    @classmethod
    def next_attempt_at(cls, attempt: int, now: datetime) -> datetime:
        """The backoff horizon after the *attempt*-th failed run (1, 2, 4, 7, 7, … days)."""
        delay_days = min(2 ** max(attempt - 1, 0), cls.RETRY_MAX_DELAY_DAYS)
        # recurrence-owner-ok: a retry backoff after a failed tenant-erasure attempt, not a calendar recurrence
        return now + timedelta(days=delay_days)
