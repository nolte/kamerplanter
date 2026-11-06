"""The bed list as CSV rows (REQ-053 GP-FR-145, GP-FR-175; WP 8.25, #2668).

Pure: :class:`BedListExportRow` objects and a column selection in, header and rows out; the file itself (BOM,
quoting, formula hardening of text cells) is :mod:`app.common.csv_export`.

**Columns.** :data:`DEFAULT_COLUMNS` are GP-FR-145's (name, type, area, status, soil texture, irrigation zone, active
plants). :data:`SITE_CONDITION_COLUMNS` are the selectable site features of §10.2 (GP-FR-175). The column ids are
the header of the file and stable machine names; enum cells carry the API's values (``full_sun``, ``loam``), as the
care-log CSV does.

**The assignment is not a column to pick** (SR-024). :data:`ASSIGNMENT_COLUMN` is appended only by
``include_assignment`` - naming it in ``columns`` is refused like any unknown column, so there is exactly one way to
put member names into the file, and it is the explicit opt-in. Its cells are display names (or ``anonymisiert``),
never an account key: the row carries no key to write.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from app.common.csv_export import csv_number, csv_text
from app.common.exceptions import PlanError
from app.domain.models.bed_list_export import BedListExportRow
from app.domain.models.site import SiteConditions

#: Separator of several values inside one cell (assignees, access sides, flags), as the care log's plant names.
VALUE_SEPARATOR = " | "

#: The columns whose cells need a read of their own (the service skips it when the column is not selected).
COLUMN_TYPE = "type"
COLUMN_IRRIGATION_ZONE = "irrigation_zone"
COLUMN_ACTIVE_PLANTS = "active_plants"

DEFAULT_COLUMNS: tuple[str, ...] = (
    "name",
    COLUMN_TYPE,
    "area_m2",
    "status",
    "soil_texture",
    COLUMN_IRRIGATION_ZONE,
    COLUMN_ACTIVE_PLANTS,
)

#: §10.2 site features of a bed (plus the coarse ``sun_exposure`` of §10.1 they refine), selectable (GP-FR-175).
SITE_CONDITION_COLUMNS: tuple[str, ...] = (
    "sun_exposure",
    "sun_window",
    "direct_sun_hours_summer",
    "foliage_shade_in_summer",
    "frost_risk",
    "cold_air_pocket",
    "heat_retention",
    "wind_exposure",
    "slope_deg",
    "aspect_deg",
    "access_sides",
    "site_flags",
)

#: Every column ``columns=`` may name, in the order the file writes them.
SELECTABLE_COLUMNS: tuple[str, ...] = DEFAULT_COLUMNS + SITE_CONDITION_COLUMNS

#: The member names of the bed - only with ``include_assignment=true`` (SR-024), always the last column.
ASSIGNMENT_COLUMN = "assigned_to"

ERROR_UNKNOWN_COLUMN = "export.unknown_column"
ERROR_NO_COLUMNS = "export.no_columns"
#: ``format=csv`` with ``is_bed=false``: the download is the bed list, not every location of the site.
ERROR_BEDS_ONLY = "export.beds_only"


def resolve_bed_list_columns(columns: str | None, *, include_assignment: bool) -> tuple[str, ...]:
    """The columns of the file, in :data:`SELECTABLE_COLUMNS` order, the assignment last when opted in.

    ``columns`` is a comma-separated selection; ``None`` is :data:`DEFAULT_COLUMNS`. A repeated name counts once.
    An unknown name - :data:`ASSIGNMENT_COLUMN` included - is 422 ``export.unknown_column``; a selection without a
    single name is 422 ``export.no_columns``.
    """
    if columns is None:
        chosen: set[str] = set(DEFAULT_COLUMNS)
    else:
        names = [name for name in map(str.strip, columns.split(",")) if name]
        if not names:
            raise PlanError(ERROR_NO_COLUMNS, "Select at least one column.", status_code=422, field="columns")
        unknown = sorted({name for name in names if name not in SELECTABLE_COLUMNS})
        if unknown:
            raise PlanError(
                ERROR_UNKNOWN_COLUMN,
                "Unknown column in the selection; the assignment is added with include_assignment=true only.",
                status_code=422,
                field="columns",
                columns=unknown[:10],
                allowed=list(SELECTABLE_COLUMNS),
            )
        chosen = set(names)
    ordered = tuple(name for name in SELECTABLE_COLUMNS if name in chosen)
    return (*ordered, ASSIGNMENT_COLUMN) if include_assignment else ordered


def _flag(value: bool | None) -> str:
    """A yes/no cell; empty when the bed has no site features recorded at all."""
    if value is None:
        return ""
    return "yes" if value else "no"


def _cells(decimal: str) -> dict[str, Callable[[BedListExportRow], str]]:
    """One cell writer per column id."""

    def conditions(row: BedListExportRow) -> SiteConditions | None:
        return row.location.site_conditions

    def soil_texture(row: BedListExportRow) -> str:
        profile = row.location.soil_profile
        return csv_text(profile.soil_texture.value) if profile is not None else ""

    def active_plants(row: BedListExportRow) -> str:
        return csv_number(row.counters.active_plant_count) if row.counters is not None else ""

    def condition_text(read: Callable[[SiteConditions], str]) -> Callable[[BedListExportRow], str]:
        def cell(row: BedListExportRow) -> str:
            value = conditions(row)
            return csv_text(read(value)) if value is not None else ""

        return cell

    def condition_number(read: Callable[[SiteConditions], float | None]) -> Callable[[BedListExportRow], str]:
        def cell(row: BedListExportRow) -> str:
            value = conditions(row)
            return csv_number(read(value), decimal=decimal) if value is not None else ""

        return cell

    def condition_flag(read: Callable[[SiteConditions], bool]) -> Callable[[BedListExportRow], str]:
        def cell(row: BedListExportRow) -> str:
            value = conditions(row)
            return _flag(read(value) if value is not None else None)

        return cell

    def assigned_to(row: BedListExportRow) -> str:
        return csv_text(VALUE_SEPARATOR.join(row.assignees or []))

    return {
        "name": lambda row: csv_text(row.location.name),
        "type": lambda row: csv_text(row.type_name or row.location.location_type_key),
        "area_m2": lambda row: csv_number(round(row.location.area_m2, 2), decimal=decimal),
        "status": lambda row: csv_text(row.location.bed_status.value),
        "soil_texture": soil_texture,
        "irrigation_zone": lambda row: csv_text(row.zone_name),
        "active_plants": active_plants,
        "sun_exposure": lambda row: csv_text(row.location.sun_exposure.value),
        "sun_window": condition_text(lambda value: value.sun_profile.sun_window.value),
        "direct_sun_hours_summer": condition_number(lambda value: value.sun_profile.direct_sun_hours_summer),
        "foliage_shade_in_summer": condition_flag(lambda value: value.sun_profile.foliage_shade_in_summer),
        "frost_risk": condition_text(lambda value: value.microclimate.frost_risk.value),
        "cold_air_pocket": condition_flag(lambda value: value.microclimate.cold_air_pocket),
        "heat_retention": condition_text(lambda value: value.microclimate.heat_retention.value),
        "wind_exposure": condition_text(lambda value: value.wind_exposure.value),
        "slope_deg": condition_number(lambda value: value.slope_deg),
        "aspect_deg": condition_number(lambda value: value.aspect_deg),
        "access_sides": condition_text(lambda value: VALUE_SEPARATOR.join(side.value for side in value.access_sides)),
        "site_flags": condition_text(lambda value: VALUE_SEPARATOR.join(flag.value for flag in value.flags)),
        ASSIGNMENT_COLUMN: assigned_to,
    }


def bed_list_csv_rows(
    rows: Iterable[BedListExportRow], columns: tuple[str, ...], *, decimal_comma: bool = False
) -> list[list[str]]:
    """The cells of the download, one row per bed, in ``columns`` order (from :func:`resolve_bed_list_columns`).

    ``decimal_comma`` writes the numbers with a comma (the semicolon variant for Excel in a decimal-comma locale).
    The assignment column is written only when it is in ``columns``: a row's ``assignees`` alone never adds it.
    """
    writers = _cells("," if decimal_comma else ".")
    selected = [writers[name] for name in columns]
    return [[write(row) for write in selected] for row in rows]
