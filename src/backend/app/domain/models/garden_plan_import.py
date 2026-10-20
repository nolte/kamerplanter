"""The report of a garden-plan import (REQ-053 GP-API-005, GP-FR-141/170, GP-UX-051).

One report serves both the ``dry_run`` and the applied import, so the assistant's "check" step and the
confirmation after the write read the same fields. Nothing in it echoes a value of the file beyond the file's
own key of the offending entity: the keys of a backup are references inside that file (§23), not identities of
this system, and a name or a note never travels back in an error.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

#: GP-NFR-051: the file, not the request envelope, is bounded by 5 MB.
MAX_IMPORT_BYTES = 5 * 1024 * 1024
#: The envelope (``mode``, ``dry_run`` … around the document) is small; the body ceiling adds this much to the file's.
IMPORT_ENVELOPE_BYTES = 64 * 1024
#: GP-FR-141 / SR-018: at most this many levels of locations below the site (``depth`` 0 … 9).
MAX_IMPORT_NESTING = 10
#: The import is the largest atomic write of the plan: it gets 30 s where a batch gets 10 (GP-NFR-013).
IMPORT_TIME_BUDGET_SECONDS = 30.0
#: How many findings and dropped references one answer lists; the counts stay exact.
MAX_REPORTED = 50

#: ``GardenPlanExport`` fields the import knows. A top-level key outside this set belongs to a *newer* file.
SUPPORTED_SCHEMA_VERSIONS: tuple[str, ...] = ("1",)

#: Keys that name a technical coupling (a Home Assistant entity, an actuator): never imported (GP-FR-141).
ALWAYS_DROPPED_FIELDS: tuple[str, ...] = ("flow_rate_ha_entity_id", "actuator_key")

type ImportMode = Literal["replace", "merge"]
type DropReason = Literal["not_found", "not_in_site", "always_dropped", "outside_file", "invalid_parent"]


class ImportCounts(BaseModel):
    """What an import creates, updates or deletes, per kind. ``plan_settings`` is 0 or 1 (the site's plan)."""

    locations: int = 0
    garden_objects: int = 0
    slots: int = 0
    plan_settings: int = 0
    zones: int = 0


class DroppedReference(BaseModel):
    """A reference of the file that was not carried over (GP-FR-141): rewritten to ``null`` or the entity skipped."""

    entity: Literal["location", "garden_object", "slot", "irrigation_zone"]
    #: The file's own key of the entity (a reference inside the file, never a system key).
    key: str
    field: str
    reason: DropReason


class ImportFinding(BaseModel):
    """One reason the file cannot be imported: a path in the document, a published code, the file's own key."""

    field: str
    code: str
    key: str | None = None


class PlanImportReport(BaseModel):
    mode: str
    dry_run: bool
    would_create: ImportCounts = Field(default_factory=ImportCounts)
    would_update: ImportCounts = Field(default_factory=ImportCounts)
    would_delete: ImportCounts = Field(default_factory=ImportCounts)
    #: Locations that stay because a plant stands in them (V-09) - only with ``force``; the ancestors count too.
    kept_locations: int = 0
    dropped_references: list[DroppedReference] = Field(default_factory=list)
    dropped_references_total: int = 0
    errors: list[ImportFinding] = Field(default_factory=list)
    errors_total: int = 0
    #: ``True`` once the import was written; a dry run and a refused import leave it ``False``.
    applied: bool = False
    #: The plan revision after the write; ``None`` for a dry run.
    plan_revision: int | None = None
    #: ``replace`` writes the state it replaces into the change log first (SR-011).
    snapshot_written: bool = False
