"""The exchange file of one bed template (REQ-053 GP-FR-173, GP-API-070/071; WP 9.9, #2749).

A template leaves the system as a small JSON file and comes back - into the same tenant or another one - as a new
template of the importing tenant. The file is a **transport**, not a backup: it carries what makes the template a
template and nothing that names a person, a tenant or another document.

**What the file holds.** ``format`` (so a garden-plan backup is not mistaken for a template), ``schema_version``,
the name, the bed type (``location_type_key`` - a key of the *global* location-type catalogue, the same on every
installation, never a tenant's row), the geometry in the bed frame, the height (the "standard size") and the planting
grid (``default_layout``), plus the soil axes. **What it never holds:** ``_key``, ``tenant_key``, ``created_by``,
timestamps, ``recurring_task_templates`` (keys of a tenant's task templates) and any free text beyond the name -
the domain model carries no note in the first place (``SoilProfileDefaults`` excludes ``notes`` on purpose).

**What the import does with the rest.** Top-level fields the schema does not name - a ``_key``, a ``tenant_key``,
a ``created_by`` someone added by hand, a field of a later version - are **ignored** (GP-API-071: "Keys aus der
Datei werden ignoriert") and counted in the report, never stored. The nested objects (geometry, grid, soil) stay
strict: an unknown field there is a 422, like on ``POST /bed-templates``.

**Versions (GP-NFR-072 as GP-API-071 states it).** The import reads the current ``schema_version`` and exactly one
before it; older ones are a 422. While ``"1"`` is the only version there is nothing to migrate. A breaking change
raises :data:`SCHEMA_VERSION` and registers the step from the previous one in :data:`MIGRATORS`; the chain itself is
the garden-plan one (``app.domain.engines.plan_schema_migration.migrate``), called with these two values.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.models.bed_template import (
    MAX_TEMPLATE_HEIGHT_M,
    MIN_TEMPLATE_HEIGHT_M,
    BedTemplate,
    DefaultLayout,
    SoilProfileDefaults,
    check_default_geometry,
)
from app.domain.models.geometry import BedFrameGeometry

#: The ``format`` marker of a template file; a file with another marker is a 422.
EXCHANGE_FORMAT = "kamerplanter.bed_template"
#: The ``schema_version`` the export writes and the import validates against (after migration).
SCHEMA_VERSION = "1"
#: GP-API-071: how many versions before :data:`SCHEMA_VERSION` the import still reads.
KEPT_PREDECESSORS = 1
#: From-version -> the step to the next version. Empty while ``"1"`` is the only version.
MIGRATORS: Mapping[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

#: GP-API-071: the file (the request body) is at most 256 KB; a larger one is a 413.
MAX_FILE_BYTES = 256 * 1024
#: GP-FR-141 / SR-018: at most this many levels of nested JSON in the file.
MAX_NESTING = 10
#: How many unknown field names the report lists; the count stays exact.
MAX_REPORTED_FIELDS = 20

#: Fields a file may carry that the import knows and drops on purpose: document keys, the owner, the author,
#: timestamps and the task-template keys. The report names them; any other unknown field is only counted, so the
#: answer never echoes an arbitrary string of the file.
KNOWN_DROPPED_FIELDS: frozenset[str] = frozenset(
    {
        "_key",
        "_id",
        "_rev",
        "key",
        "tenant_key",
        "created_by",
        "created_at",
        "updated_at",
        "is_system",
        "recurring_task_templates",
        "notes",
        "note",
    }
)

#: 422 codes of the import (``details[0].code``).
ERROR_FILE_INVALID = "bed_template.import_invalid"
ERROR_SCHEMA_VERSION = "bed_template.schema_version_unsupported"
ERROR_NESTING = "bed_template.import_too_deep"
#: 409 when a visible template already has the name; ``details[0].suggested_name`` proposes a free one.
ERROR_NAME_TAKEN = "bed_template.name_taken"


class BedTemplateExchange(BaseModel):
    """The file of ``GET /bed-templates/{key}/export`` and the body of ``POST /bed-templates/import``.

    ``extra="ignore"`` on this level only: a key of the file is dropped, not stored (see the module docstring).
    """

    model_config = ConfigDict(extra="ignore")

    #: Required on import: a file without the marker is no template file.
    format: Literal["kamerplanter.bed_template"]
    #: Checked (and migrated) before this model sees the file; kept equal to :data:`SCHEMA_VERSION` by a unit test.
    schema_version: Literal["1"]
    name: str = Field(min_length=1, max_length=200)
    location_type_key: str = Field(min_length=1, max_length=200)
    default_geometry: BedFrameGeometry
    height_m: float | None = Field(default=None, ge=MIN_TEMPLATE_HEIGHT_M, le=MAX_TEMPLATE_HEIGHT_M)
    default_layout: DefaultLayout = Field(default_factory=DefaultLayout)
    soil_profile_defaults: SoilProfileDefaults | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("A template needs a name.")
        return stripped

    @field_validator("default_geometry")
    @classmethod
    def validate_default_geometry(cls, value: BedFrameGeometry) -> BedFrameGeometry:
        return check_default_geometry(value)

    @classmethod
    def of(cls, template: BedTemplate) -> BedTemplateExchange:
        """The file of a stored template: field by field, so a new field of ``BedTemplate`` never leaks into it."""
        return cls(
            format=EXCHANGE_FORMAT,
            schema_version=SCHEMA_VERSION,
            name=template.name,
            location_type_key=template.location_type_key,
            default_geometry=template.default_geometry,
            height_m=template.height_m,
            default_layout=template.default_layout,
            soil_profile_defaults=template.soil_profile_defaults,
        )


class BedTemplateImportReport(BaseModel):
    """What ``POST /bed-templates/import`` answers, for the dry run and the applied import alike."""

    dry_run: bool
    #: The ``schema_version`` the file was written in; ``migrated`` says whether it was lifted to the current one.
    schema_version: str
    migrated: bool
    #: The template as it is (or would be) stored - with the name it gets.
    template: BedTemplateExchange
    #: The new template's key; ``None`` on a dry run.
    created_key: str | None = None
    #: Known fields of the file that were dropped on purpose (keys, owner, author, task templates ...).
    dropped_fields: list[str] = Field(default_factory=list)
    #: How many further, unknown top-level fields were ignored (their names are not echoed).
    unknown_fields_ignored: int = 0
