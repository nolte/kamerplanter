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
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import zipfile
from collections.abc import Iterable
from datetime import date, datetime
from typing import IO, Any, Literal

from pydantic import BaseModel, Field

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
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
        "tenant_erasure_records": "the proof of a tenant deletion in this installation",
        "tenant_export_requests": "export requests are not exported (§8.3)",
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
        "task_templates": {"source_template_key": _internal("task_templates")},
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
        """The ``excluded[]`` block: every inventory collection left out, plus the stores outside ArangoDB."""
        rows = [{"collection": name, "reason": reason} for name, reason in sorted(cls.EXCLUDED.items())]
        rows.append(
            {
                "collection": "timescale:sensor_readings",
                "reason": "not yet part of format 1 (REQ-056 §8.3 timeseries/readings.csv is open, #2138)",
            }
        )
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


def archive_document(document: dict[str, Any]) -> dict[str, Any]:
    """A stored document as the archive carries it: without ``_id``/``_rev``, ``_key`` kept as source key."""
    return {name: value for name, value in document.items() if name not in _SYSTEM_ATTRIBUTES}


def _line(document: dict[str, Any]) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, default=_json_default).encode("utf-8") + b"\n"


class ArchiveTooLargeError(Exception):
    """The archive grew past its limit while being written (REQ-056 §8.3, ``too_large``)."""


class TenantArchiveWriter:
    """Writes one archive into a seekable binary file; hashes and counts every part.

    Each part is opened once and written line by line (no part is held whole in memory).
    The size limit is checked against the bytes written to the file after every part
    and every object — a run past the limit stops with :class:`ArchiveTooLargeError`
    before more is read.
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

    def finish(self, manifest: dict[str, Any]) -> dict[str, int]:
        """Write ``manifest.json`` (with every part's count and hash) and close; returns rows per part."""
        payload = {**manifest, "files": dict(sorted(self._parts.items()))}
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


def _parse_lines(data: bytes, part: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lines: list[bytes] = data.splitlines()
    for number, raw in enumerate(lines, start=1):
        line: bytes = raw
        if not line.strip():
            continue
        try:
            document = json.loads(raw)
        except ValueError as exc:
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{part}: line {number} is not JSON") from exc
        if not isinstance(document, dict):
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{part}: line {number} is not an object")
        rows.append(document)
    return rows


def read_tenant_archive(source: IO[bytes], *, max_uncompressed_bytes: int) -> TenantArchive:
    """Verify and parse an archive: format, every checksum, every part listed and nothing unlisted.

    The total uncompressed size is bounded before anything is decompressed (a ZIP bomb
    is refused by its directory, not by running out of memory). Raises
    :class:`TenantArchiveError` (``IMPORT_FORMAT_UNSUPPORTED`` / ``IMPORT_CHECKSUM_MISMATCH``).
    """
    try:
        archive = zipfile.ZipFile(source)
    except zipfile.BadZipFile as exc:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the upload is not a ZIP archive") from exc
    with archive:
        infos: dict[str, zipfile.ZipInfo] = {}
        for listed in archive.infolist():
            info: zipfile.ZipInfo = listed
            if not info.is_dir():
                infos[info.filename] = info
        if sum(info.file_size for info in infos.values()) > max_uncompressed_bytes:
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive unpacks beyond the import limit")
        if MANIFEST_NAME not in infos:
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive has no manifest.json")
        try:
            manifest = json.loads(archive.read(MANIFEST_NAME))
        except ValueError as exc:
            raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "manifest.json is not JSON") from exc
        if not isinstance(manifest, dict) or manifest.get("format") != ARCHIVE_FORMAT:
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
        mismatched: list[str] = []
        listed_files: dict[str, Any] = files
        for name, part in listed_files.items():
            data = archive.read(name)
            entry: dict[str, Any] = part if isinstance(part, dict) else {}
            expected: Any = entry.get("sha256")
            if expected is None or hashlib.sha256(data).hexdigest() != expected:
                mismatched.append(name)
            contents[name] = data
        if mismatched:
            raise TenantArchiveError(
                "IMPORT_CHECKSUM_MISMATCH", "a part of the archive does not match its checksum", entries=mismatched
            )
    return _assemble(manifest, contents)


def _assemble(manifest: dict[str, Any], contents: dict[str, bytes]) -> TenantArchive:
    if TENANT_NAME not in contents:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive has no tenant.json")
    try:
        tenant = json.loads(contents[TENANT_NAME])
    except ValueError as exc:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "tenant.json is not JSON") from exc
    source_tenant_key = manifest.get("source_tenant_key")
    if not isinstance(tenant, dict) or not isinstance(source_tenant_key, str) or not source_tenant_key:
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive names no source tenant")
    collections: dict[str, list[dict[str, Any]]] = {}
    edges: dict[str, list[dict[str, Any]]] = {}
    objects: dict[str, bytes] = {}
    members: list[TenantArchiveMember] = []
    for name, data in contents.items():
        if name in (TENANT_NAME,):
            continue
        if name == MEMBERS_NAME:
            members = [TenantArchiveMember(**row) for row in _parse_lines(data, name)]
        elif name.startswith(COLLECTIONS_DIR) and name.endswith(".jsonl"):
            collection = name[len(COLLECTIONS_DIR) : -len(".jsonl")]
            _require_name(collection, name)
            collections[collection] = _parse_lines(data, name)
        elif name.startswith(EDGES_DIR) and name.endswith(".jsonl"):
            collection = name[len(EDGES_DIR) : -len(".jsonl")]
            _require_name(collection, name)
            edges[collection] = _parse_lines(data, name)
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
    )


def _require_name(collection: str, part: str) -> None:
    if not _COLLECTION_NAME.match(collection):
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"collection name not allowed: {part}")


def peek_tenant_slug(source: IO[bytes]) -> str | None:
    """The slug ``tenant.json`` names, read without verifying anything (the step-up target, §12.1)."""
    try:
        with zipfile.ZipFile(source) as archive:
            tenant = json.loads(archive.read(TENANT_NAME))
    except zipfile.BadZipFile, KeyError, ValueError:
        return None
    finally:
        if isinstance(source, io.IOBase) and source.seekable():
            source.seek(0)
    slug = tenant.get("slug") if isinstance(tenant, dict) else None
    return slug if isinstance(slug, str) else None


def is_tombstone_or_pseudonym(value: str) -> bool:
    """Whether an account value is no live account key (the pseudonym or an erasure tombstone)."""
    return value == ANONYMIZED_ACCOUNT or bool(_TOMBSTONE.match(value))
