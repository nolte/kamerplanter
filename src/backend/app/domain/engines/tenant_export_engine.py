"""The declared tenant export (REQ-056 §8.3, #2138, audit MT-042).

Pure logic, no database or network I/O. Three things live here, each in one place:

**What an archive holds.** The source is the tenant-erasure inventory
(:attr:`TenantErasureEngine.INVENTORY`): what the deletion of a tenant reaches is
what belongs to it. The export takes every inventory collection except those
:attr:`TenantExportEngine.EXCLUDED` names with a reason (secrets, audit logs,
access grants bound to accounts, caches). ``tests/unit/guards/
test_tenant_export_covers_the_inventory.py`` holds both lists against each other
in both directions (REQ-056 AK-29): a new inventory collection fails until it is
exported or excluded.

**Which fields are references.** ``_key`` is generated per collection and global
across tenants, so an import gives every document a new key and rewrites every
reference through a mapping table (§8.4). Which fields *are* references is
declared — :attr:`FIELD_REFERENCES` by field name, :attr:`COLLECTION_REFERENCES`
per collection (a ``batch_key`` names a harvest batch in one collection and a
post-harvest batch in another), and the account fields read off the account
erasure (:class:`ErasureEngine`), never restated. The guard
``test_tenant_export_references_are_declared.py`` derives every ``*_key`` /
``*_keys`` field (nested ones included) of every exported model and fails on one
that is not declared (AK-31); at import time a document carrying an undeclared
``*_key`` path is refused rather than written with a stale key that could name a
row of another tenant in the target database.

**The archive format** (``kamerplanter-tenant-export/1``): one ZIP with
``manifest.json`` (format, source migration level, creation time, a random source
instance id, per part the row count and the SHA-256), ``tenant.json``,
``collections/<name>.jsonl``, ``edges/<name>.jsonl``, ``members.jsonl`` and
``objects/<path>`` (the originals of the tenant's attachments, path relative to
``t/<tenant_key>/``). :class:`TenantArchiveWriter` writes it into a caller-supplied
binary file, :func:`read_tenant_archive` verifies and parses one.

**Optional parts** (``timeseries/``, #2138): format 1 carries the tenant's TimescaleDB readings as
``timeseries/readings.csv`` when the source has any (:data:`READINGS_COLUMNS`; the manifest lists its
hash like every part and describes it under ``timeseries``). A format-1 reader checks that every
``timeseries/`` part is listed in the manifest, never decompresses it and imports nothing from it —
the import of readings is not part of format 1's reader. An archive without the part is complete.
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import hmac
import io
import json
import re
import zipfile
import zlib
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import IO, Any, Literal

from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.observation import ArchivedReading
from app.domain.models.tenant_erasure import TenantErasureEntry
from app.domain.models.tenant_export import TenantArchive, TenantArchiveMember

#: The archive format this code writes and reads. A new incompatible format gets a new number.
ARCHIVE_FORMAT = "kamerplanter-tenant-export/1"

MANIFEST_NAME = "manifest.json"
TENANT_NAME = "tenant.json"
MEMBERS_NAME = "members.jsonl"
COLLECTIONS_DIR = "collections/"
EDGES_DIR = "edges/"
OBJECTS_DIR = "objects/"
#: Optional parts a format-1 reader lists but never reads (module docstring, "Optional parts").
TIMESERIES_DIR = "timeseries/"
READINGS_NAME = f"{TIMESERIES_DIR}readings.csv"

#: The columns of ``timeseries/readings.csv``, in order (:class:`ArchivedReading`). ``series`` is
#: ``raw`` / ``hourly`` / ``daily``; ``time`` is ISO 8601 with offset; ``metadata`` is JSON; an empty
#: cell is ``None``. A text cell that starts with ``=``, ``+``, ``-``, ``@``, a tab or a carriage
#: return is prefixed with ``'`` so a spreadsheet opening the file does not run it as a formula; a
#: reader strips one leading ``'`` before such a character.
READINGS_COLUMNS: tuple[str, ...] = (
    "series",
    "time",
    "sensor_key",
    "sensor_type",
    "value",
    "unit",
    "source",
    "quality_score",
    "raw_value",
    "metadata",
    "avg_value",
    "min_value",
    "max_value",
    "sample_count",
)

#: The first characters a spreadsheet reads as the start of a formula (CSV injection).
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

#: The storage category the archives are kept under (``t/<tenant>/tenant_export/<export_key>.zip``).
ARCHIVE_STORAGE_CATEGORY = "tenant_export"

#: What a document of the archive may never carry into an import: the database's own bookkeeping.
_SYSTEM_ATTRIBUTES = ("_id", "_rev")

#: A collection or edge-collection name as ``collections.py`` spells them.
_COLLECTION_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

#: An object path inside ``objects/`` — the tail of a ``t/<tenant>/…`` key, never climbing out.
_OBJECT_PATH = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]{0,511}$")

#: An account value that is no account: the pseudonym, the account-erasure tombstone, or nothing.
_TOMBSTONE = re.compile(r"^anon_[0-9a-f]{16}$")

#: The pseudonym an unmapped member's account references become (REQ-056 §8.4 step 4).
ANONYMIZED_ACCOUNT = "_anonymized"

type ReferenceKind = Literal[
    "internal",  # a row of the archive (mapped), else a global catalogue row when a target is a catalogue
    "global",  # a row of a global catalogue; must exist in the target database
    "account",  # an account key: mapped by the admin, else the pseudonym
    "tenant",  # the tenant itself
    "storage",  # an object key under t/<tenant>/
    "attachment",  # an attachment id (photo_refs); a legacy storage key is rewritten like one
    "polymorphic",  # the collection is named by a sibling field (entity_type, entity_collection)
    "opaque",  # looks like a key, is none (an adapter id, an i18n key, a value of the row itself)
]


class TenantReference(BaseModel):
    """How the import rewrites one reference field (REQ-056 §8.4 step 3)."""

    model_config = {"frozen": True}

    kind: ReferenceKind
    targets: tuple[str, ...] = ()
    #: ``polymorphic`` only: the sibling field and its value → collection mapping.
    discriminator: str | None = None
    by_value: dict[str, str] = Field(default_factory=dict)
    reason: str | None = None


def _internal(*targets: str) -> TenantReference:
    return TenantReference(kind="internal", targets=targets)


def _global(*targets: str) -> TenantReference:
    return TenantReference(kind="global", targets=targets)


def _opaque(reason: str) -> TenantReference:
    return TenantReference(kind="opaque", reason=reason)


def _polymorphic(discriminator: str, **by_value: str) -> TenantReference:
    return TenantReference(kind="polymorphic", discriminator=discriminator, by_value=by_value)


_ACCOUNT_REF = TenantReference(kind="account")
_TENANT_REF = TenantReference(kind="tenant")
_STORAGE_REF = TenantReference(kind="storage")
_ATTACHMENT_REF = TenantReference(kind="attachment", targets=("attachments",))

_SECRET = "carries an encrypted secret of an integration; a new installation is configured anew (REQ-056 §8.3)"
_AUDIT = "an audit log with its own retention; it proves what happened in this installation (REQ-056 §8.3)"


class TenantArchiveError(ValueError):
    """The archive is not one this installation can import (format, checksum, content). Nothing was written."""

    def __init__(self, code: str, message: str, *, entries: list[str] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.entries = entries or []


class TenantExportEngine:
    """Declares what a tenant archive holds and how its references are rewritten."""

    FORMAT = ARCHIVE_FORMAT

    #: Inventory collections the archive leaves out, each with the reason (written to ``excluded[]``).
    EXCLUDED: dict[str, str] = {
        "memberships": (
            "accounts are not the tenant's: memberships travel as members.jsonl (user key, display name, role, "
            "scopes, joined_at — no e-mail address, REQ-056 E-09) and are re-created by the admin's member mapping"
        ),
        "invitations": "invitation tokens and invitee e-mail addresses are credentials, not tenant data (§8.3)",
        "location_assignments": (
            "write grants bound to memberships of this installation; the new tenant's management assigns anew"
        ),
        "ai_provider_configs": _SECRET,
        "inventree_connections": _SECRET,
        "inventree_references": "links to parts of the InvenTree instance the (not exported) connection points at",
        "stock_transactions": "the push queue of the (not exported) InvenTree connection",
        "api_keys": "API keys and their hashes are credentials (§8.3)",
        "tenant_ha_entity_grants": (
            "a platform admin's grant of the operator's own Home Assistant entities; meaningless elsewhere"
        ),
        "notifications": "notification delivery state of this installation's accounts (§8.3)",
        "calendar_feeds": "iCal subscription tokens of this installation's accounts are credentials",
        "ai_conversations": "an account's chat transcripts with a provider configuration that is not exported",
        "ai_tip_cache": "a cache, regenerated on demand",
        "import_jobs": "short-lived CSV upload jobs of this installation",
        "mcp_idempotency_record": "short-lived MCP replay protection of this installation",
        "ai_audit_log": _AUDIT,
        "mcp_audit_log": _AUDIT,
        "security_audit_log": _AUDIT,
        "garden_plan_audit": _AUDIT,  # REQ-053 SR-011: the plan change log names this installation's accounts
        "tenant_erasure_records": "the proof of a tenant deletion in this installation",
        "tenant_export_requests": "export requests are not exported (§8.3)",
    }

    _ACCOUNT_EDGE = (
        "connects an account to its own data (sessions, keys, consents, requests); accounts are not exported"
    )
    _CATALOGUE_EDGE = (
        "relates two global catalogue rows only; an archive may never write catalogue relations every tenant reads"
    )

    #: Edge collections an import never writes, each with the reason (SEC-002 of the PR #2267 review).
    #: ``test_tenant_export_covers_the_inventory.py`` holds this and :attr:`IMPORTABLE_EDGES` against
    #: ``collections.EDGE_COLLECTIONS`` in both directions: a new edge collection needs a decision.
    EXCLUDED_EDGES: dict[str, str] = {
        "tenant_has_access": (
            "an access grant onto another tenant's catalogue rows; an archive must not grant itself access"
        ),
        "has_membership": "memberships are re-created from the admin's member mapping, never from an archive",
        "membership_in": "memberships are re-created from the admin's member mapping, never from an archive",
        "assignment_for": "location assignments are not exported (write grants bound to memberships)",
        "assignment_in_tenant": "location assignments are not exported (write grants bound to memberships)",
        "assigned_to_location": "location assignments are not exported (write grants bound to memberships)",
        "task_assigned_to": "points at an account; accounts are not exported",
        "has_api_key": _ACCOUNT_EDGE,
        "has_auth_provider": _ACCOUNT_EDGE,
        "has_consent": _ACCOUNT_EDGE,
        "has_restriction": _ACCOUNT_EDGE,
        "has_session": _ACCOUNT_EDGE,
        "requested_email_change": _ACCOUNT_EDGE,
        "requested_erasure": _ACCOUNT_EDGE,
        "requested_export": _ACCOUNT_EDGE,
        "user_favorites": _ACCOUNT_EDGE,
        "has_invitation": "invitations are credentials and not exported",
        "has_inventree_ref": "the InvenTree references are not exported",
        "has_stock_transaction": "the InvenTree push queue is not exported",
        "notified_about_plant": "notifications are not exported",
        "notified_about_task": "notifications are not exported",
        "notification_for_run": "notifications are not exported",
        "ai_audit_about": "the AI audit log is not exported",
        "ai_conversation_about": "AI conversations are not exported",
        "ai_tip_references_plant": "the AI tip cache is not exported",
        "ai_tip_references_run": "the AI tip cache is not exported",
        "consists_of": _CATALOGUE_EDGE,
        "contraindicated_with": _CATALOGUE_EDGE,
        "entry_uses_definition": _CATALOGUE_EDGE,
        "family_compatible_with": _CATALOGUE_EDGE,
        "family_incompatible_with": _CATALOGUE_EDGE,
        "governed_by": _CATALOGUE_EDGE,
        "next_phase": _CATALOGUE_EDGE,
        "requires_profile": _CATALOGUE_EDGE,
        "rotation_after": _CATALOGUE_EDGE,
        "seq_has_entry": _CATALOGUE_EDGE,
        "shares_pest_risk": _CATALOGUE_EDGE,
        "targets_disease": _CATALOGUE_EDGE,
        "targets_pest": _CATALOGUE_EDGE,
        "uses_nutrients": _CATALOGUE_EDGE,
        "vulnerable_in_phase": _CATALOGUE_EDGE,
    }

    #: The edge collections an archive may carry and an import writes — an allowlist, not "whatever the
    #: database has" (SEC-002). An edge is still written only when at least one end is a row of the
    #: archive or the tenant itself (:meth:`TenantImportEngine.remap_edge`).
    IMPORTABLE_EDGES: frozenset[str] = frozenset(
        {
            "actuator_controls_location",
            "actuator_event",
            "actuator_has_override",
            "actuator_has_rule",
            "actuator_has_schedule",
            "adjacent_to",
            "applied_to_plant",
            "assessed_by_quality",
            "belongs_to_family",
            "belongs_to_tenant",
            "care_event_at",  # REQ-053 M1 (#2323): care_events → locations
            "care_event_for",
            "cloned_from",
            "compatible_fish_plant",
            "compatible_with",
            "confirms_care",
            "contains",
            "created_by_wizard",
            "current_phase",
            "cv_attached_to_inspection",
            "cv_diagnosed_for",
            "cv_diagnosis_found",
            "cv_phenotype_of",
            "demand_for_run",
            "descended_from",
            "detected_disease",
            "detected_pest",
            "enriched_by",
            "entry_for_species",
            "equipment_at",
            "fed_by",
            "feeding_for_stock",
            "feeding_used",
            "feeds_from",
            "fert_incompatible",
            "filled_with",
            "follows_plan",
            "follows_workflow",
            "generated_task",
            "grown_in",
            "harvested_as",
            "has_actuator",
            "has_burping_event",
            "has_care_profile",
            "has_climate_normal",
            "has_component",
            "has_cultivar",
            "has_diary_entry",
            "has_drying_progress",
            "has_entry",
            "has_fill_event",
            "has_fish_stock",
            "has_forecast",
            "has_garden_object",  # REQ-053 M1 (#2323): sites → garden_objects
            "has_harvest_indicator",
            "has_irrigation_demand",
            "has_irrigation_zone",  # REQ-053 M1 (#2323): sites → irrigation_zones
            "has_lifecycle",
            "has_maintenance",
            "has_overwintering_profile",
            "has_phase_entry",
            "has_phase_sequence",
            "has_schedule",
            "has_season_state",
            "has_slot",
            "has_state",
            "has_stock",
            "has_storage_observation",
            "has_succession_plan",
            "has_tank",
            "has_task",
            "has_weather_source_config",
            "has_yield_metric",
            "includes_cultivar",
            "includes_nutrient_plan",
            "includes_species",
            "includes_template",
            "incompatible_fish_plant",
            "incompatible_with",
            "inspected_by",
            "instance_of",
            "located_at",
            "located_in_zone",
            "location_profile",
            "log_fertilizer",
            "log_plant",
            "log_slot",
            "mixed_into",
            "monitors_tank",
            "observed_for_harvest",
            "overwinters_at",
            "pest_detection_flagged",
            "pest_detection_of",
            "pest_detection_suggested_inspection",
            "phase_history_edge",
            "phase_profile",
            "placed_in",
            "plan_uses_fertilizer",
            "post_harvest_of",
            "requires_phase",
            "rule_monitors",
            "run_at_location",
            "run_contains",
            "run_follows_plan",
            "run_planned_at",  # REQ-053 M1 (#2323): planting_runs → slots
            "run_uses_substrate",
            "stock_of_species",
            "succession_at",
            "supplementation_for",
            "supplies",
            "system_has_growbed",
            "system_has_tank",
            "task_blocks",
            "task_cloned_from",
            "task_has_audit",
            "task_has_comment",
            "task_logged_as",  # REQ-053 M1 (#2323): tasks → care_events
            "task_recurs_from",
            "task_uses_activity",
            "to_run",
            "treatment_uses",
            "triggered_mold_alert",
            "uses_indicator",
            "uses_overwintering_template",
            "uses_type",
            "water_test_for",
            "watered_plant",
            "watering_from",
            "wf_contains",
            "wf_executing",
            "wf_generated",
            "wf_has_phase",
            "zone_actuated_by",  # REQ-053 M1 (#2323): irrigation_zones → actuators
            "zone_covers",  # REQ-053 M1 (#2323): irrigation_zones → locations
            "zone_supplied_by",  # REQ-053 M1 (#2323): irrigation_zones → garden_objects
        }
    )

    #: Fields an export removes before a row leaves the installation (SEC-005): an encrypted secret
    #: or a reference to one is configured anew in the target. Dot paths; lists are walked.
    REDACTED_FIELDS: dict[str, tuple[str, ...]] = {
        "weather_source_configs": ("sources.config.api_key_ref",),
    }

    #: Field names that look like a secret (``*_ref``, ``*token*``, ``*secret*``, ``*encrypted*``,
    #: ``*password*``, ``*api_key*``) and are none, with the reason. The guard in
    #: ``test_tenant_export_covers_the_inventory.py`` fails on a match that is neither here nor redacted.
    NOT_SECRET_FIELDS: dict[str, str] = {
        "photo_refs": "attachment ids of the tenant's own photos (rewritten on import)",
        "cover_photo_ref": "the attachment id of the cover photo (rewritten on import)",
        "external_ref": "a machine producer's idempotency key of a task (#1082), not a credential",
        "source_run_ref": "the id of the producer run (pipeline) that emitted a task, shown for traceability",
        "ppfd_ref": "a reference PPFD value of a lamp in µmol/m²/s (REQ-053 §9.8), a number, not an id",
        "product_ref": "{kind, key} of a product document of a care event (REQ-053 §20.10), not a credential",
        "source_ref": "{collection, key} of the event a care event mirrors (REQ-053 §20.10), not a credential",
    }

    #: Inventory collections whose global rows carry an empty ``tenant_key`` beside tenant-owned rows:
    #: a reference into one is either a row of the archive or a global catalogue row of the target.
    HYBRID_CATALOGUES: frozenset[str] = frozenset(
        {
            "species",
            "cultivars",
            "fertilizers",
            "nutrient_plans",
            "nutrient_plan_phase_entries",
            "substrates",
            "activities",
            "workflow_templates",
            "workflow_phases",
            "task_templates",
        }
    )

    #: Reference fields by name, valid in every exported collection unless overridden below.
    FIELD_REFERENCES: dict[str, TenantReference] = {
        "tenant_key": _TENANT_REF,
        "storage_key": _STORAGE_REF,
        "photo_refs": _ATTACHMENT_REF,
        "cover_photo_ref": _ATTACHMENT_REF,
        # Places
        "site_key": _internal("sites"),
        "location_key": _internal("locations"),
        "parent_location_key": _internal("locations"),
        "sensor_location_key": _internal("locations"),
        "winter_quarter_key": _internal("locations"),
        "irrigation_zone_key": _internal("irrigation_zones"),  # REQ-053 §20.3 (WP 1.7, #2326)
        "slot_key": _internal("slots"),
        "slot_keys": _internal("slots"),
        "tank_key": _internal("tanks"),
        "source_tank_key": _internal("tanks"),
        "sensor_key": _internal("sensors"),
        # Plants and runs
        "plant_key": _internal("plant_instances"),
        "plant_keys": _internal("plant_instances"),
        "plant_instance_key": _internal("plant_instances"),
        "mother_key": _internal("plant_instances"),
        "source_plant_key": _internal("plant_instances"),
        "child_plant_keys": _internal("plant_instances"),
        "parent_plant_keys": _internal("plant_instances"),
        "planting_run_key": _internal("planting_runs"),
        "target_planting_run_key": _internal("planting_runs"),
        "clone_from_run_key": _internal("planting_runs"),
        "run_key": _internal("planting_runs"),
        "succession_plan_key": _internal("succession_plans"),
        "substrate_batch_key": _internal("substrate_batches"),
        "harvest_batch_key": _internal("harvest_batches"),
        "harvest_observation_key": _internal("harvest_observations"),
        "inspection_key": _internal("inspections"),
        "protocol_key": _internal("rooting_protocols"),
        "care_profile_key": _internal("care_profiles"),
        # Hybrid catalogues: a row of the archive, or a global row of the target
        "species_key": _internal("species"),
        "species_keys": _internal("species"),
        "recommended_species_keys": _internal("species"),
        "matched_species_key": _internal("species"),
        "cultivar_key": _internal("cultivars"),
        "fertilizer_key": _internal("fertilizers"),
        "product_key": _internal("fertilizers"),
        "substrate_key": _internal("substrates"),
        "nutrient_plan_key": _internal("nutrient_plans"),
        "default_nutrient_plan_key": _internal("nutrient_plans"),
        "activity_key": _internal("activities"),
        "workflow_template_key": _internal("workflow_templates"),
        "source_workflow_key": _internal("workflow_templates"),
        "workflow_phase_key": _internal("workflow_phases"),
        # Work
        "task_key": _internal("tasks"),
        "parent_recurring_task_key": _internal("tasks"),
        "template_key": _internal("task_templates"),
        "workflow_execution_key": _internal("workflow_executions"),
        "watering_event_key": _internal("watering_events"),
        "watering_log_key": _internal("watering_logs"),
        "tank_fill_event_key": _internal("tank_fill_events"),
        # Control
        "actuator_key": _internal("actuators"),
        "triggered_by_rule_key": _internal("control_rules"),
        "triggered_by_schedule_key": _internal("control_schedules"),
        # Aquaponics
        "system_key": _internal("aquaponic_systems"),
        "stock_key": _internal("fish_stocks"),
        # Global catalogues
        "family_key": _global("botanical_families"),
        "location_type_key": _global("location_types"),
        "lifecycle_config_key": _global("lifecycle_configs"),
        "lifecycle_key": _global("lifecycle_configs"),
        "phase_sequence_key": _global("phase_sequences"),
        "phase_definition_key": _global("phase_definitions"),
        "current_phase_key": _global("growth_phases", "phase_definitions"),
        "indicator_key": _global("harvest_indicators"),
        "treatment_key": _global("treatments"),
        "pest_key": _global("pests"),
        "matched_pest_key": _global("pests"),
        "detected_pest_keys": _global("pests"),
        "disease_key": _global("diseases"),
        "matched_disease_key": _global("diseases"),
        "detected_disease_keys": _global("diseases"),
        "matched_beneficial_key": _global("beneficials"),
        # Not references
        "adapter_key": _opaque("the id of a recognition adapter, not a document"),
        "trigger_reason_i18n_key": _opaque("an i18n message key"),
        "mixing_result_key": _opaque("an id of a transient mixing calculation; no collection holds it"),
    }

    #: Per-collection overrides and additions (paths are dot-separated; lists are walked transparently).
    COLLECTION_REFERENCES: dict[str, dict[str, TenantReference]] = {
        "nutrient_plans": {"cloned_from_key": _internal("nutrient_plans")},
        "nutrient_plan_phase_entries": {
            "plan_key": _internal("nutrient_plans"),
            "delivery_channels.fertilizer_dosages.fertilizer_key": _internal("fertilizers"),
        },
        "substrates": {"mix_components.substrate_key": _internal("substrates")},
        # REQ-053 §15.1 (WP 1.7, #2326): the bed's substrate (GP-FR-121) — a tenant row or a global one.
        "locations": {"soil_profile.substrate_key": _internal("substrates")},
        "task_templates": {"source_template_key": _internal("task_templates")},
        # REQ-053 §20.10 (WP 1.9): the supersede chain of the care log points within the collection.
        "care_events": {
            "supersedes_key": _internal("care_events"),
            "superseded_by_key": _internal("care_events"),
            # WP 3.4 (#2394): a backfilled year names the family (global catalogue) and, optionally, the species.
            "rotation_entry.family_key": _global("botanical_families"),
            "rotation_entry.species_key": _internal("species"),
        },
        "overwintering_profiles": {"source_template_key": _global("overwintering_profile_templates")},
        "fish_stocks": {"species_key": _global("fish_species")},
        "phase_histories": {"phase_key": _global("growth_phases", "phase_definitions")},
        "quality_assessments": {"batch_key": _internal("harvest_batches")},
        "yield_metrics": {"batch_key": _internal("harvest_batches")},
        "drying_progress": {"batch_key": _internal("post_harvest_batches")},
        "storage_observations": {"batch_key": _internal("post_harvest_batches")},
        "mold_alerts": {"batch_key": _internal("post_harvest_batches")},
        "burping_events": {"batch_key": _internal("post_harvest_batches")},
        "propagation_events": {"batch_key": _internal("propagation_batches")},
        "tank_fill_events": {"fertilizers_used.product_key": _internal("fertilizers")},
        "watering_events": {"fertilizers_used.product_key": _internal("fertilizers")},
        "feeding_events": {"fertilizers_used.fertilizer_key": _internal("fertilizers")},
        "watering_logs": {"fertilizers_used.fertilizer_key": _internal("fertilizers")},
        "plant_diary_entries": {"environment.sensor_key": _internal("sensors")},
        "inspections": {"findings.disease_key": _global("diseases"), "findings.pest_key": _global("pests")},
        "pest_detections": {
            "findings.matched_beneficial_key": _global("beneficials"),
            "findings.matched_pest_key": _global("pests"),
        },
        "plant_diagnosis_requests": {
            "classifications.matched_disease_key": _global("diseases"),
            "classifications.matched_pest_key": _global("pests"),
        },
        "identification_requests": {"results.matched_species_key": _internal("species")},
        "tasks": {
            "entity_key": _polymorphic(
                "entity_type",
                plant_instance="plant_instances",
                planting_run="planting_runs",
                location="locations",
                tank="tanks",
                site="sites",
                actuator="actuators",
            )
        },
        "workflow_executions": {
            "entity_key": _polymorphic(
                "entity_type",
                plant_instance="plant_instances",
                planting_run="planting_runs",
                location="locations",
                tank="tanks",
            )
        },
        "ha_publish_settings": {
            "entity_key": _polymorphic("entity_type", plant="plant_instances", tank="tanks", location="locations")
        },
    }

    # ── what the archive holds ────────────────────────────────────────

    @classmethod
    def exported_entries(cls) -> list[TenantErasureEntry]:
        """The inventory entries the archive carries, in inventory order (parents before children)."""
        return [entry for entry in TenantErasureEngine.INVENTORY if entry.collection not in cls.EXCLUDED]

    @classmethod
    def exported_collections(cls) -> list[str]:
        return [entry.collection for entry in cls.exported_entries()]

    @classmethod
    def global_catalogues(cls) -> frozenset[str]:
        """Collections whose every row is global (declared so by the tenant-erasure inventory)."""
        return frozenset(
            name
            for name, reason in TenantErasureEngine.NOT_TENANT_SCOPED.items()
            if reason.startswith("global catalogue")
        )

    @classmethod
    def validate(cls) -> None:
        """Refuse declarations the import would have to guess at (called by the guards and before a run)."""
        inventory = {entry.collection for entry in TenantErasureEngine.INVENTORY}
        stale = sorted(set(cls.EXCLUDED) - inventory)
        if stale:
            raise ValueError(f"excluded collections that are not in the tenant-erasure inventory: {stale}")
        exported = set(cls.exported_collections())
        catalogues = cls.global_catalogues()
        pairs: list[tuple[str, dict[str, TenantReference]]] = [
            ("*", cls.FIELD_REFERENCES),
            *cls.COLLECTION_REFERENCES.items(),
        ]
        for collection, refs in pairs:
            if collection != "*" and collection not in exported:
                raise ValueError(f"references declared for '{collection}', which the archive does not carry")
            declared: dict[str, TenantReference] = refs
            for path, ref in declared.items():
                reference: TenantReference = ref
                by_value: dict[str, str] = reference.by_value
                for target in reference.targets:
                    if reference.kind == "global" and target not in catalogues:
                        raise ValueError(f"{collection}.{path}: '{target}' is not a global catalogue")
                    if reference.kind == "internal" and target not in exported:
                        raise ValueError(f"{collection}.{path}: '{target}' is not carried by the archive")
                for target in by_value.values():
                    if target not in exported:
                        raise ValueError(f"{collection}.{path}: '{target}' is not carried by the archive")

    # ── which fields are references ───────────────────────────────────

    @classmethod
    def account_fields(cls, collection: str) -> frozenset[str]:
        """The account fields of *collection*, read off the account erasure (one declaration, #1700)."""
        fields = {rule.user_field for rule in ErasureEngine.ANONYMIZE_COLLECTIONS if rule.collection == collection}
        fields |= {
            step.user_field
            for step in ErasureEngine.DELETE_STEPS
            if step.collection == collection and step.kind == "document" and step.user_field
        }
        return frozenset(fields)

    @classmethod
    def references_of(cls, collection: str) -> dict[str, TenantReference]:
        """Every declared reference path of *collection* (field defaults, overrides, account fields)."""
        refs: dict[str, TenantReference] = dict(cls.FIELD_REFERENCES)
        for field in cls.account_fields(collection):
            refs[field] = _ACCOUNT_REF
        refs.update(cls.COLLECTION_REFERENCES.get(collection, {}))
        return refs

    @staticmethod
    def looks_like_reference(name: str) -> bool:
        """The shape of a field the import must know: ``*_key`` / ``*_keys``."""
        return name.endswith(("_key", "_keys"))

    @classmethod
    def undeclared_reference_paths(cls, collection: str, document: dict[str, Any]) -> list[str]:
        """Every ``*_key``/``*_keys`` path in *document* the declarations do not cover (sorted)."""
        declared = set(cls.references_of(collection))
        found: set[str] = set()
        _collect_key_paths(document, "", declared, found)
        return sorted(found)

    # ── manifest ──────────────────────────────────────────────────────

    @classmethod
    def excluded_manifest(cls) -> list[dict[str, str]]:
        """The ``excluded[]`` block: every inventory collection left out, plus the stores outside ArangoDB.

        TimescaleDB readings are not excluded: they travel as the optional ``timeseries/readings.csv``.
        """
        rows = [{"collection": name, "reason": reason} for name, reason in sorted(cls.EXCLUDED.items())]
        rows.append(
            {
                "collection": "pgvector:recognition_embeddings",
                "reason": "recognition vectors are recomputed from the photos or missing (REQ-056 §8.3)",
            }
        )
        return rows


def _collect_key_paths(value: Any, prefix: str, declared: set[str], found: set[str]) -> None:
    """Add to *found* every ``*_key``/``*_keys`` path under *value* that *declared* does not hold."""
    if isinstance(value, list):
        for inner in value:
            _collect_key_paths(inner, prefix, declared, found)
        return
    if not isinstance(value, dict):
        return
    mapping: dict[str, Any] = value
    for name, inner in mapping.items():
        label: str = str(name)
        if label[:1] == "_":
            continue
        path = f"{prefix}{label}"
        if TenantExportEngine.looks_like_reference(label) and path not in declared:
            found.add(path)
        _collect_key_paths(inner, f"{path}.", declared, found)


# ── serialisation ─────────────────────────────────────────────────────


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime | date):
        instant: datetime | date = value
        return instant.isoformat()
    if isinstance(value, set | frozenset | tuple):
        return list(value)
    raise TypeError(f"not serialisable: {type(value).__name__}")


def archive_document(document: dict[str, Any], *, collection: str | None = None) -> dict[str, Any]:
    """A stored document as the archive carries it: without ``_id``/``_rev``, ``_key`` kept as source key.

    With *collection*, every :attr:`TenantExportEngine.REDACTED_FIELDS` path of that collection is
    removed (SEC-005) — on export, and again on import for an archive another installation wrote.
    """
    kept = {name: value for name, value in document.items() if name not in _SYSTEM_ATTRIBUTES}
    for path in TenantExportEngine.REDACTED_FIELDS.get(collection or "", ()):
        dotted: str = path
        kept = _without(kept, dotted.split("."))
    return kept


def _without(node: Any, segments: list[str]) -> Any:
    """A copy of *node* without the field at *segments* (lists are walked transparently)."""
    if isinstance(node, list):
        return [_without(item, segments) for item in node]
    if not isinstance(node, dict):
        return node
    mapping: dict[str, Any] = node
    head, rest = segments[0], segments[1:]
    if head not in mapping:
        return mapping
    copy = dict(mapping)
    if rest:
        copy[head] = _without(mapping[head], rest)
    else:
        del copy[head]
    return copy


def _csv_text(value: str | None) -> str:
    if not value:
        return ""
    return f"'{value}" if value.startswith(_FORMULA_PREFIXES) else value


def _csv_number(value: float | None) -> str:
    return "" if value is None else repr(value)


def readings_csv_rows(readings: Iterable[ArchivedReading]) -> list[list[str]]:
    """The cells of ``timeseries/readings.csv`` for *readings*, in :data:`READINGS_COLUMNS` order."""
    rows: list[list[str]] = []
    for reading in readings:
        metadata = (
            json.dumps(reading.metadata, ensure_ascii=False, sort_keys=True, default=_json_default)
            if reading.metadata is not None
            else ""
        )
        rows.append(
            [
                reading.series,
                reading.time.isoformat(),
                _csv_text(reading.sensor_key),
                _csv_text(reading.sensor_type),
                _csv_number(reading.value),
                _csv_text(reading.unit),
                _csv_text(reading.source),
                _csv_number(reading.quality_score),
                _csv_number(reading.raw_value),
                _csv_text(metadata),
                _csv_number(reading.avg_value),
                _csv_number(reading.min_value),
                _csv_number(reading.max_value),
                "" if reading.sample_count is None else str(reading.sample_count),
            ]
        )
    return rows


def manifest_signature(manifest: dict[str, Any], signing_key: bytes) -> str:
    """HMAC-SHA256 over the canonical manifest without its ``signature`` (SEC-003).

    The manifest lists the SHA-256 of every part, so the signature authenticates the whole
    archive — for the installation that holds *signing_key*. The per-part hashes alone only
    detect corruption: anyone can recompute them after an edit.
    """
    body = {name: value for name, value in manifest.items() if name != "signature"}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, default=_json_default).encode("utf-8")
    return hmac.new(signing_key, canonical, hashlib.sha256).hexdigest()


def _line(document: dict[str, Any]) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, default=_json_default).encode("utf-8") + b"\n"


class ArchiveTooLargeError(Exception):
    """The archive grew past its limit while being written (REQ-056 §8.3, ``too_large``)."""


class TenantArchiveWriter:
    """Writes one archive into a seekable binary file; hashes and counts every part.

    Each part is opened once and written line by line (no part is held whole in memory).
    The size limit is checked against the bytes written to the file after every page of a
    part, every part and every object — a run past the limit stops with
    :class:`ArchiveTooLargeError` before more is read.
    """

    def __init__(self, target: IO[bytes], *, max_bytes: int | None) -> None:
        self._target = target
        self._zip: zipfile.ZipFile = zipfile.ZipFile(
            target, mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=True
        )
        self._max_bytes = max_bytes
        self._parts: dict[str, dict[str, Any]] = {}

    def _check_size(self) -> None:
        if self._max_bytes is not None and self._target.tell() > self._max_bytes:
            raise ArchiveTooLargeError

    def write_json(self, name: str, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=_json_default).encode("utf-8")
        self._zip.writestr(name, data)
        self._parts[name] = {"rows": 1, "sha256": hashlib.sha256(data).hexdigest()}
        self._check_size()

    def write_lines(self, name: str, pages: Iterable[list[dict[str, Any]]]) -> int:
        """Write *pages* of documents as one JSONL part; returns the row count (``0`` writes nothing)."""
        digest = hashlib.sha256()
        rows = 0
        handle = None
        try:
            for page in pages:
                for document in page:
                    if handle is None:
                        handle = self._zip.open(name, mode="w", force_zip64=True)
                    line = _line(document)
                    handle.write(line)
                    digest.update(line)
                    rows += 1
                if handle is not None:
                    self._check_size()
        finally:
            if handle is not None:
                handle.close()
        if rows:
            self._parts[name] = {"rows": rows, "sha256": digest.hexdigest()}
            self._check_size()
        return rows

    def write_csv(self, name: str, header: Iterable[str], pages: Iterable[list[list[str]]]) -> int:
        """Write *pages* of CSV rows under one *header* as one part; returns the data rows (``0`` writes nothing).

        Streams: each page is encoded and written before the next is read, and the size limit is
        checked after every page — a part past the limit stops the source it is read from.
        """
        digest = hashlib.sha256()
        rows = 0
        handle = None
        try:
            for page in pages:
                if not page:
                    continue
                buffer = io.StringIO()
                out = csv.writer(buffer, lineterminator="\r\n")
                if handle is None:
                    handle = self._zip.open(name, mode="w", force_zip64=True)
                    out.writerow(list(header))
                out.writerows(page)
                data = buffer.getvalue().encode("utf-8")
                handle.write(data)
                digest.update(data)
                rows += len(page)
                self._check_size()
        finally:
            if handle is not None:
                handle.close()
        if rows:
            self._parts[name] = {"rows": rows, "sha256": digest.hexdigest()}
            self._check_size()
        return rows

    def write_object(self, path: str, data: bytes) -> None:
        name = f"{OBJECTS_DIR}{path}"
        self._zip.writestr(name, data)
        self._parts[name] = {"rows": 1, "sha256": hashlib.sha256(data).hexdigest()}
        self._check_size()

    def finish(self, manifest: dict[str, Any], *, signing_key: bytes | None = None) -> dict[str, int]:
        """Write ``manifest.json`` (every part's count and hash, signed when a key is given) and close."""
        payload: dict[str, Any] = {**manifest, "files": dict(sorted(self._parts.items()))}
        if signing_key:
            payload["signature"] = {"alg": "HMAC-SHA256", "value": manifest_signature(payload, signing_key)}
        self._zip.writestr(
            MANIFEST_NAME, json.dumps(payload, ensure_ascii=False, sort_keys=True, default=_json_default)
        )
        self._zip.close()
        self._check_size()
        return {name: int(part["rows"]) for name, part in self._parts.items()}

    def abort(self) -> None:
        with contextlib.suppress(Exception):  # the archive is discarded either way
            self._zip.close()


# ── reading ───────────────────────────────────────────────────────────


#: Entries a tenant archive may hold; checked on the ZIP directory before anything is read (SEC-008).
MAX_ARCHIVE_ENTRIES = 200_000

#: ``tenant.json`` is a handful of fields; more is not a tenant document.
MAX_TENANT_JSON_BYTES = 1024 * 1024

#: The deepest nesting a stored document reaches is single digits; anything deeper is crafted.
MAX_JSON_DEPTH = 32

#: Everything an archive may unpack to, documents and objects together (SEC-R2-01 of the PR #2267
#: review). Fixed, not derived from the upload limit: the archive is held in memory while it is
#: verified, and an upload limit an operator raises must not raise what one request may allocate.
MAX_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024

#: Every part but ``objects/`` — the JSON that is parsed into Python objects, several times its
#: size in memory. A real tenant's documents are a few MiB; 128 MiB is a very large garden.
MAX_DOCUMENT_BYTES = 128 * 1024 * 1024

#: Rows one JSONL part may hold, and all parts together. Counted on the bytes before a line is
#: split or parsed: a part of empty objects (``{}\n``) is three bytes a row and a Python dict each.
MAX_ROWS_PER_PART = 250_000
MAX_ROWS = 1_000_000

#: Unpacked size over packed size above which an entry is a decompression bomb, not a document.
#: Deflated JSONL of real rows stays far below it (repeated keys reach 10-20x); a run of ``{}\n``
#: deflates about 1000x.
MAX_COMPRESSION_RATIO = 100

#: One JSONL line — one stored document. Checked on the bytes before the line is parsed (R3-02 of the
#: PR #2267 review): the row bound counts lines, and a single 25 MiB line of ``[{},{},…]`` is one row
#: and millions of dicts. A real document is a few KiB.
MAX_LINE_BYTES = 1024 * 1024

#: JSON values (objects, arrays, scalars) all parts of one archive may hold together, counted while the
#: depth is checked. Bounds what many lines just under :data:`MAX_LINE_BYTES` can still allocate.
MAX_JSON_NODES = 5_000_000

#: Below this unpacked size the ratio is not checked: a small, repetitive part may compress well.
_RATIO_FLOOR_BYTES = 1024 * 1024


@dataclass(frozen=True)
class _ReadLimits:
    total: int
    entry: int
    entries: int
    documents: int
    rows_per_part: int
    rows: int
    ratio: int


class _NodeBudget:
    """The JSON values one archive may still hold (:data:`MAX_JSON_NODES`), shared by all its parts."""

    def __init__(self, nodes: int) -> None:
        self.left = nodes

    def take(self, part: str) -> None:
        self.left -= 1
        if self.left < 0:
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{part}: the archive holds too many JSON values")


def _check_depth(value: Any, part: str, budget: _NodeBudget | None = None) -> None:
    """Refuse a parsed value nested deeper than :data:`MAX_JSON_DEPTH` (iterative: no recursion to exhaust).

    With *budget*, every value is counted against the archive's node budget (R3-02).
    """
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        node, depth = stack.pop()
        if budget is not None:
            budget.take(part)
        if depth > MAX_JSON_DEPTH:
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{part}: nested deeper than {MAX_JSON_DEPTH}")
        if isinstance(node, dict):
            mapping: dict[str, Any] = node
            stack.extend((inner, depth + 1) for inner in mapping.values())
        elif isinstance(node, list):
            items: list[Any] = node
            stack.extend((inner, depth + 1) for inner in items)


def _loads(data: bytes, part: str, budget: _NodeBudget | None = None) -> Any:
    try:
        value = json.loads(data)
    except (ValueError, RecursionError) as exc:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{part} is not JSON") from exc
    _check_depth(value, part, budget)
    return value


def _parse_lines(data: bytes, part: str, max_rows: int, budget: _NodeBudget | None = None) -> list[dict[str, Any]]:
    """The rows of one JSONL part; more than *max_rows* refuses before a line is split or parsed (SEC-R2-01).

    A line longer than :data:`MAX_LINE_BYTES` refuses before it is parsed, and every parsed value is
    counted against the archive's *budget* (R3-02).
    """
    # ``bytes.splitlines`` breaks at ``\n``, ``\r`` and ``\r\n``: their count bounds the line count.
    if data.count(b"\n") + data.count(b"\r") > max_rows:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{part}: more than {max_rows} rows")
    rows: list[dict[str, Any]] = []
    lines: list[bytes] = data.splitlines()
    for number, raw in enumerate(lines, start=1):
        line: bytes = raw
        if not line.strip():
            continue
        if len(line) > MAX_LINE_BYTES:
            raise TenantArchiveError(
                "IMPORT_FORMAT_UNSUPPORTED", f"{part}: line {number} is longer than {MAX_LINE_BYTES} bytes"
            )
        document = _loads(line, f"{part}: line {number}", budget)
        if not isinstance(document, dict):
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{part}: line {number} is not an object")
        rows.append(document)
    if len(rows) > max_rows:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{part}: more than {max_rows} rows")
    return rows


def read_tenant_archive(
    source: IO[bytes],
    *,
    max_uncompressed_bytes: int = MAX_UNCOMPRESSED_BYTES,
    max_entry_bytes: int | None = None,
    max_entries: int = MAX_ARCHIVE_ENTRIES,
    signing_key: bytes | None = None,
    max_document_bytes: int = MAX_DOCUMENT_BYTES,
    max_rows_per_part: int = MAX_ROWS_PER_PART,
    max_rows: int = MAX_ROWS,
    max_compression_ratio: int = MAX_COMPRESSION_RATIO,
) -> TenantArchive:
    """Verify and parse an archive: directory bounds, format, every checksum, every part listed.

    Everything the ZIP directory can tell — entry count, each entry's and the total
    uncompressed size, the size of all document parts together, each entry's compression
    ratio, the size of ``tenant.json`` — is checked **before** any entry is decompressed
    (SEC-008, SEC-R2-01). The total is never more than :data:`MAX_UNCOMPRESSED_BYTES`,
    whatever the caller asks for. The rows of a JSONL part are counted before the part is
    split into lines. Every failure of the ZIP or JSON reader is a refusal
    (:class:`TenantArchiveError`: ``IMPORT_FORMAT_UNSUPPORTED`` / ``IMPORT_CHECKSUM_MISMATCH``),
    never an unhandled exception. With *signing_key* the manifest signature is checked:
    ``TenantArchive.verified`` says whether this installation wrote the archive unchanged
    (SEC-003); an unsigned or foreign archive reads as unverified, it is not refused.
    """
    total = min(max_uncompressed_bytes, MAX_UNCOMPRESSED_BYTES)
    limits = _ReadLimits(
        total=total,
        entry=min(max_entry_bytes or total, total),
        entries=max_entries,
        documents=min(max_document_bytes, total),
        rows_per_part=max_rows_per_part,
        rows=max_rows,
        ratio=max_compression_ratio,
    )
    try:
        return _read(source, limits, signing_key)
    except TenantArchiveError:
        raise
    except (zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError, NotImplementedError, EOFError, OSError) as exc:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive cannot be read") from exc
    except (zlib.error, ValueError, TypeError, KeyError) as exc:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive's content has the wrong shape") from exc


def _check_directory(infos: dict[str, zipfile.ZipInfo], limits: _ReadLimits) -> None:
    """The bounds the ZIP directory alone can prove, before one entry is decompressed (SEC-008, SEC-R2-01)."""
    read = {name: info for name, info in infos.items() if not is_ignored_part(name)}
    if sum(info.file_size for info in read.values()) > limits.total:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive unpacks beyond the import limit")
    documents = sum(info.file_size for name, info in read.items() if name[: len(OBJECTS_DIR)] != OBJECTS_DIR)
    if documents > limits.documents:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive's documents unpack beyond the import limit")
    for name, info in read.items():
        if info.file_size > _RATIO_FLOOR_BYTES and info.file_size > limits.ratio * max(info.compress_size, 1):
            raise TenantArchiveError(
                "IMPORT_FORMAT_UNSUPPORTED", f"an entry exceeds the compression ratio limit of {limits.ratio}: {name}"
            )
    if MANIFEST_NAME not in infos or infos[MANIFEST_NAME].file_size > MAX_TENANT_JSON_BYTES:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive has no readable manifest.json")
    if TENANT_NAME in infos and infos[TENANT_NAME].file_size > MAX_TENANT_JSON_BYTES:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "tenant.json is larger than a tenant document")


def _read(source: IO[bytes], limits: _ReadLimits, signing_key: bytes | None) -> TenantArchive:
    archive = zipfile.ZipFile(source)
    with archive:
        listed_infos: list[zipfile.ZipInfo] = archive.infolist()
        if len(listed_infos) > limits.entries:
            raise TenantArchiveError(
                "IMPORT_FORMAT_UNSUPPORTED", f"the archive holds more than {limits.entries} entries"
            )
        infos: dict[str, zipfile.ZipInfo] = {}
        for listed in listed_infos:
            info: zipfile.ZipInfo = listed
            if info.is_dir():
                continue
            if info.file_size > limits.entry and not is_ignored_part(info.filename):
                raise TenantArchiveError(
                    "IMPORT_FORMAT_UNSUPPORTED", f"an entry unpacks beyond the limit: {info.filename}"
                )
            if info.filename in infos:
                raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"a duplicate entry: {info.filename}")
            infos[info.filename] = info
        _check_directory(infos, limits)
        parsed = _loads(archive.read(MANIFEST_NAME), MANIFEST_NAME)
        manifest: dict[str, Any] = parsed if isinstance(parsed, dict) else {}
        if manifest.get("format") != ARCHIVE_FORMAT:
            raise TenantArchiveError(
                "IMPORT_FORMAT_UNSUPPORTED", f"unknown archive format (this installation reads {ARCHIVE_FORMAT})"
            )
        files = manifest.get("files")
        if not isinstance(files, dict):
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "manifest.json lists no files")
        unlisted = sorted(set(infos) - set(files) - {MANIFEST_NAME})
        missing = sorted(set(files) - set(infos))
        if unlisted or missing:
            raise TenantArchiveError(
                "IMPORT_CHECKSUM_MISMATCH",
                "the archive's parts do not match its manifest",
                entries=[*(f"unlisted:{name}" for name in unlisted), *(f"missing:{name}" for name in missing)],
            )
        contents: dict[str, bytes] = {}
        ignored: dict[str, int] = {}
        mismatched: list[str] = []
        listed_files: dict[str, Any] = files
        for name, part in listed_files.items():
            entry: dict[str, Any] = part if isinstance(part, dict) else {}
            if is_ignored_part(name):
                # Listed (above) but never decompressed: a format-1 reader imports nothing from it.
                stated_rows = entry.get("rows")
                ignored[name] = stated_rows if isinstance(stated_rows, int) and stated_rows >= 0 else 0
                continue
            data = archive.read(name)
            expected: Any = entry.get("sha256")
            if expected is None or hashlib.sha256(data).hexdigest() != expected:
                mismatched.append(name)
            contents[name] = data
        if mismatched:
            raise TenantArchiveError(
                "IMPORT_CHECKSUM_MISMATCH", "a part of the archive does not match its checksum", entries=mismatched
            )
    return _assemble(manifest, contents, limits, verified=_signature_valid(manifest, signing_key), ignored=ignored)


def _signature_valid(manifest: dict[str, Any], signing_key: bytes | None) -> bool:
    signature = manifest.get("signature")
    if not signing_key or not isinstance(signature, dict):
        return False
    value = signature.get("value")
    if signature.get("alg") != "HMAC-SHA256" or not isinstance(value, str):
        return False
    return hmac.compare_digest(value, manifest_signature(manifest, signing_key))


def _assemble(
    manifest: dict[str, Any],
    contents: dict[str, bytes],
    limits: _ReadLimits,
    *,
    verified: bool,
    ignored: dict[str, int] | None = None,
) -> TenantArchive:
    if TENANT_NAME not in contents:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive has no tenant.json")
    tenant = _loads(contents[TENANT_NAME], TENANT_NAME)
    source_tenant_key = manifest.get("source_tenant_key")
    if not isinstance(tenant, dict) or not isinstance(source_tenant_key, str) or not source_tenant_key:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive names no source tenant")
    collections: dict[str, list[dict[str, Any]]] = {}
    edges: dict[str, list[dict[str, Any]]] = {}
    objects: dict[str, bytes] = {}
    members: list[TenantArchiveMember] = []
    rows_left = limits.rows
    budget = _NodeBudget(MAX_JSON_NODES)

    def parsed_rows(data: bytes, part: str) -> list[dict[str, Any]]:
        nonlocal rows_left
        rows = _parse_lines(data, part, min(limits.rows_per_part, rows_left), budget)
        rows_left -= len(rows)
        return rows

    for name, data in contents.items():
        if name in (TENANT_NAME,):
            continue
        if name == MEMBERS_NAME:
            try:
                members = [TenantArchiveMember(**row) for row in parsed_rows(data, name)]
            except PydanticValidationError as exc:
                raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "members.jsonl has the wrong shape") from exc
        elif name.startswith(COLLECTIONS_DIR) and name.endswith(".jsonl"):
            collection = name[len(COLLECTIONS_DIR) : -len(".jsonl")]
            _require_name(collection, name)
            collections[collection] = parsed_rows(data, name)
        elif name.startswith(EDGES_DIR) and name.endswith(".jsonl"):
            collection = name[len(EDGES_DIR) : -len(".jsonl")]
            _require_name(collection, name)
            edges[collection] = parsed_rows(data, name)
        elif name.startswith(OBJECTS_DIR):
            path = name[len(OBJECTS_DIR) :]
            if not _OBJECT_PATH.match(path) or ".." in path.split("/"):
                raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"object path not allowed: {name}")
            objects[path] = data
        else:
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"unknown archive part: {name}")
    return TenantArchive(
        format=ARCHIVE_FORMAT,
        source_tenant_key=source_tenant_key,
        source_migration=migration if isinstance(migration := manifest.get("source_migration"), str) else None,
        tenant=tenant,
        collections=collections,
        edges=edges,
        members=members,
        objects=objects,
        verified=verified,
        ignored_parts=ignored or {},
    )


def is_ignored_part(name: str) -> bool:
    """Whether a format-1 reader skips the part (``timeseries/…``, module docstring "Optional parts")."""
    return name[: len(TIMESERIES_DIR)] == TIMESERIES_DIR


def _require_name(collection: str, part: str) -> None:
    if not _COLLECTION_NAME.match(collection):
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"collection name not allowed: {part}")


def is_tombstone_or_pseudonym(value: str) -> bool:
    """Whether an account value is no live account key (the pseudonym or an erasure tombstone)."""
    return value == ANONYMIZED_ACCOUNT or bool(_TOMBSTONE.match(value))
