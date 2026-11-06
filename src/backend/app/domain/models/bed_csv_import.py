"""The CSV bed list import and its report (REQ-053 GP-FR-174, SR-016/SR-018, GP-NFR-017; WP 8.26, #2669).

One report serves the ``dry_run`` and the confirmed import, so the wizard's "check" step and the answer after the
write read the same fields. A line error names the line (the header is line 1), the column as the file spells it
and a published code - never the cell's value: the file is the user's own, and the report must not become a place
where a crafted cell travels back into a page.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.common.enums import SoilTexture, SunExposure
from app.domain.models.garden_plan import MAX_PLAN_OBJECTS_PER_SITE

#: GP-FR-174: the file is bounded by 1 MiB (the global ceiling of a non-multipart body, ``app/common/body_limit.py``).
MAX_CSV_BYTES = 1024 * 1024
#: GP-NFR-017 (decision bundle #2643, question 6): one file holds at most as many beds as a site may hold at all.
MAX_CSV_ROWS = MAX_PLAN_OBJECTS_PER_SITE
#: Decision bundle #2643, question 6: the gap between two placed beds and between two rows - a layout value of the
#: editor's arrangement, not an agronomic one (no path width, no working width is implied).
BED_ROW_GAP_M = 0.5
#: How many line errors and warnings one answer lists; the totals stay exact.
MAX_REPORTED_LINES = 500

# ── published codes ───────────────────────────────────────────────────────────
ERROR_FORBIDDEN = "import.forbidden"
ERROR_QUOTA = "plan.quota_exceeded"
ERROR_MISSING_COLUMN = "csv.missing_column"
ERROR_DUPLICATE_COLUMN = "csv.duplicate_column"
ERROR_REQUIRED = "csv.required"
ERROR_TOO_LONG = "csv.too_long"
ERROR_INVALID_NUMBER = "csv.invalid_number"
ERROR_OUT_OF_RANGE = "csv.out_of_range"
ERROR_UNKNOWN_TYPE = "csv.unknown_type"
#: The type exists but is no bed type (``Gewächshaus``, ``Zimmer`` ...): the list creates beds only.
ERROR_NOT_A_BED_TYPE = "csv.not_a_bed_type"
ERROR_UNKNOWN_VALUE = "csv.unknown_value"
ERROR_UNKNOWN_ZONE = "csv.unknown_zone"
ERROR_AMBIGUOUS_ZONE = "csv.ambiguous_zone"
#: The bed finds no place in the rows inside the garden boundary (wider than it, or no row left): GP-FR-174 leaves the
#: arrangement to the editor, so the line is skipped rather than placed outside.
ERROR_DOES_NOT_FIT = "csv.does_not_fit"
#: A warning, not an error: the cell began with a formula character, which was discarded (SR-016).
WARNING_FORMULA_STRIPPED = "csv.formula_stripped"


class CsvLineFinding(BaseModel):
    """One problem of one line: ``column`` as the header spells it (``None`` for the placement of the whole row)."""

    line: int
    column: str | None = None
    code: str


class CsvBedRow(BaseModel):
    """A line that is (or would be) written: what the bed receives and where it is placed.

    ``origin`` is the lower-left corner of the ``rect`` in the plan frame (``+y`` up, §9.2); ``location_key`` is the
    new bed's key once the import was applied, ``None`` in a dry run.
    """

    line: int
    name: str
    location_type_key: str
    width_m: float
    length_m: float
    origin: tuple[float, float]
    sun_exposure: SunExposure = SunExposure.UNKNOWN
    soil_texture: SoilTexture | None = None
    irrigation_zone_key: str | None = None
    location_key: str | None = None


class BedCsvImportReport(BaseModel):
    dry_run: bool
    #: Data lines of the file (rows of empty cells not counted).
    rows_total: int = 0
    #: Lines that pass every check - written by a confirmed import, in file order.
    rows: list[CsvBedRow] = Field(default_factory=list)
    rows_valid: int = 0
    #: Lines with at least one error: never written, also not by a confirmed import.
    rows_skipped: int = 0
    errors: list[CsvLineFinding] = Field(default_factory=list)
    errors_total: int = 0
    warnings: list[CsvLineFinding] = Field(default_factory=list)
    warnings_total: int = 0
    #: Header cells the import does not know; they are ignored (cut to 64 characters).
    ignored_columns: list[str] = Field(default_factory=list)
    #: ``True`` once the valid lines were written; a dry run and an import without a valid line leave it ``False``.
    applied: bool = False
    #: The plan revision the check ran against (dry run) or the one the write produced.
    plan_revision: int = 0
