"""Import of a bed list from CSV: ``POST /sites/{key}/beds/import-csv`` (REQ-053 GP-FR-174, SR-016/SR-018; WP 8.26).

The file is a spreadsheet the user keeps: ``Name;Typ;Breite_m;Länge_m`` plus, optionally, ``Sonne``, ``Bodenart``
and ``Zone``. This service turns each line into the ``create_location`` of a batch and hands the valid ones to
:meth:`GardenPlanService.create_beds` - the batch path, with its containment and overlap rules, the site quota, the
revision check inside the transaction and a change-log row. There is no second write path: what the batch refuses,
this import refuses too.

**Check order (SR-013).** (1) authentication, the lead gate and the rate limits - the route; (2) tenant anchor: the
site of the path - the route resolves it through :meth:`BedCsvImportService.check_site` *before* it reads the body,
so a foreign site is a 404 before a byte of the file is read; then the content type (415); (3) the caller's role
(lead only, like the JSON import - SR-010); (4) the file: size, encoding, delimiter, header, the row bound (422
``plan.quota_exceeded`` above 500 rows); (5) every line on its own (line errors); (6) the site quota on the lines
that passed (5); (7) the placement and the plan rules, inside the batch's time budget (422 ``batch.too_complex``);
(8) unless ``dry_run``, the write.

**Line errors do not refuse the file.** A line that fails (5) or (6) is listed with its line number, its column and a
code, and is skipped; a confirmed import (``dry_run=false``) writes the other lines. A dry run and the confirmation
run the same checks, so the beds a dry run lists are the beds the confirmation writes - at the same positions.

**Mapping.** ``Typ`` is a *bed* type of the location-type catalogue, matched case-insensitively against its key, its
German and its English name. ``Sonne`` and ``Bodenart`` are the values of :class:`SunExposure` / :class:`SoilTexture`
or their German or English labels. ``Zone`` names an irrigation zone of the path site. Every other agronomic value
of the new bed stays unset (E-10): no soil profile beyond the texture, no sun profile beyond the coarse exposure.

**Logs carry no user text** (GP-NFR-060): site key, counts, codes and durations.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from time import perf_counter

import structlog
from pydantic import ValidationError as PydanticValidationError

from app.common.csv_import import (
    CsvReadError,
    CsvRecord,
    decode_csv,
    header_key,
    label_key,
    neutralise,
    neutralised_text,
    parse_decimal,
    read_table,
)
from app.common.enums import SoilTexture, SunExposure, TenantRole
from app.common.exceptions import PlanError, RequestBodyTooLargeError
from app.common.types import SiteKey
from app.domain.calculators.bed_row_placement_calculator import Box, PlacementTooComplexError, place_in_rows
from app.domain.calculators.geometry_calculator import bounding_box
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.irrigation_zone_repository import IIrrigationZoneRepository
from app.domain.interfaces.location_type_repository import ILocationTypeRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.bed_csv_import import (
    BED_ROW_GAP_M,
    ERROR_AMBIGUOUS_ZONE,
    ERROR_DOES_NOT_FIT,
    ERROR_DUPLICATE_COLUMN,
    ERROR_FORBIDDEN,
    ERROR_INVALID_NUMBER,
    ERROR_MISSING_COLUMN,
    ERROR_NOT_A_BED_TYPE,
    ERROR_OUT_OF_RANGE,
    ERROR_QUOTA,
    ERROR_REQUIRED,
    ERROR_TOO_COMPLEX,
    ERROR_TOO_LONG,
    ERROR_UNKNOWN_TYPE,
    ERROR_UNKNOWN_VALUE,
    ERROR_UNKNOWN_ZONE,
    MAX_CSV_BYTES,
    MAX_CSV_ROWS,
    MAX_IGNORED_COLUMNS,
    MAX_REPORTED_LINES,
    WARNING_FORMULA_STRIPPED,
    BedCsvImportReport,
    CsvBedRow,
    CsvLineFinding,
)
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import (
    BATCH_TIME_BUDGET_SECONDS,
    MAX_PLAN_OBJECTS_PER_SITE,
    MAX_PLAN_ZONES,
    ImportedBedData,
)
from app.domain.models.geometry import (
    GEOMETRY_INVALID,
    MAX_COORDINATE_M,
    MAX_DIMENSION_M,
    MIN_DIMENSION_M,
    round_length,
)
from app.domain.models.location_type import LocationType
from app.domain.models.site import Location, Site, SoilProfile
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.location_ownership import require_owned_site

logger = structlog.get_logger()

#: The longest bed name (``CreateLocationData.name``).
_MAX_NAME_CHARS = 200
#: How much of an unknown header cell the report echoes.
_HEADER_ECHO = 64
_TEMP_PREFIX = "csv_"

_NAME, _TYPE, _WIDTH, _LENGTH, _SUN, _SOIL, _ZONE = "name", "type", "width", "length", "sun", "soil", "zone"
#: Column → the header spellings it answers to (after :func:`header_key`): German as GP-FR-174 names them, English.
_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    _NAME: ("name",),
    _TYPE: ("typ", "type", "beettyp", "bed_type"),
    _WIDTH: ("breite_m", "width_m", "breite", "width"),
    _LENGTH: ("laenge_m", "length_m", "laenge", "length"),
    _SUN: ("sonne", "sun", "sun_exposure", "besonnung"),
    _SOIL: ("bodenart", "soil_texture", "soil"),
    _ZONE: ("zone", "bewaesserungszone", "irrigation_zone"),
}
_REQUIRED_COLUMNS: tuple[str, ...] = (_NAME, _TYPE, _WIDTH, _LENGTH)
#: The spelling a "missing column" refusal names (the file's own spelling is unknown when it is missing).
_CANONICAL_HEADER: dict[str, str] = {_NAME: "Name", _TYPE: "Typ", _WIDTH: "Breite_m", _LENGTH: "Länge_m"}
_HEADER_TO_COLUMN: dict[str, str] = {alias: column for column, aliases in _COLUMN_ALIASES.items() for alias in aliases}

#: The German and English labels of the UI (``enums.sunExposure`` / ``enums.soilTexture``) next to the values.
_SUN_LABELS: dict[SunExposure, tuple[str, ...]] = {
    SunExposure.FULL_SUN: ("Volle Sonne", "Vollsonne", "Sonne", "Full sun"),
    SunExposure.PARTIAL_SHADE: ("Halbschatten", "Partial shade"),
    SunExposure.SHADE: ("Schatten", "Shade"),
    SunExposure.DEEP_SHADE: ("Tiefschatten", "Deep shade"),
    SunExposure.UNKNOWN: ("Unbekannt", "Unknown"),
}
_SOIL_LABELS: dict[SoilTexture, tuple[str, ...]] = {
    SoilTexture.SAND: ("Sand",),
    SoilTexture.LOAMY_SAND: ("Lehmiger Sand", "Loamy sand"),
    SoilTexture.SANDY_LOAM: ("Sandiger Lehm", "Sandy loam"),
    SoilTexture.LOAM: ("Lehm", "Loam"),
    SoilTexture.SILT_LOAM: ("Schluffiger Lehm", "Silt loam"),
    SoilTexture.CLAY_LOAM: ("Toniger Lehm", "Clay loam"),
    SoilTexture.CLAY: ("Ton", "Clay"),
    SoilTexture.UNKNOWN: ("Unbekannt", "Unknown"),
}


def _label_index[TEnum: StrEnum](labels: dict[TEnum, tuple[str, ...]]) -> dict[str, TEnum]:
    index: dict[str, TEnum] = {}
    for value, names in labels.items():
        index[label_key(value.value)] = value
        for name in names:
            index[label_key(name)] = value
    return index


_SUN_INDEX = _label_index(_SUN_LABELS)
_SOIL_INDEX = _label_index(_SOIL_LABELS)


@dataclass
class _Line:
    """A line that passed the per-line checks (5), before the placement."""

    line: int
    name: str
    location_type_key: str
    width_m: float
    length_m: float
    sun_exposure: SunExposure
    soil_texture: SoilTexture | None
    irrigation_zone_key: str | None


@dataclass
class _Checked:
    lines: list[_Line] = field(default_factory=list)
    errors: list[CsvLineFinding] = field(default_factory=list)
    warnings: list[CsvLineFinding] = field(default_factory=list)

    def add_line(self, line: _Line) -> None:
        self.lines += [line]

    def add_error(self, line: int, code: str, column: str | None = None) -> None:
        self.errors += [CsvLineFinding(line=line, column=column, code=code)]

    def add_warning(self, line: int, code: str, column: str | None = None) -> None:
        self.warnings += [CsvLineFinding(line=line, column=column, code=code)]


@dataclass(frozen=True)
class _Header:
    #: column → position in the row
    positions: dict[str, int]
    #: column → the header cell as the file spells it (neutralised, cut)
    spelled: dict[str, str]
    ignored: list[str]


class BedCsvImportService:
    def __init__(
        self,
        site_repo: ISiteRepository,
        plan_repo: IGardenPlanRepository,
        plan_service: GardenPlanService,
        location_type_repo: ILocationTypeRepository,
        zone_repo: IIrrigationZoneRepository,
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._plans = plan_service
        self._types = location_type_repo
        self._zones = zone_repo

    # ── the entry ─────────────────────────────────────────────────────────────

    def check_site(self, site_key: SiteKey, *, tenant_key: str) -> None:
        """(2) alone: 404 for a site that is absent or another tenant's. The route calls it before it reads the body,
        so a foreign site never makes the server buffer a file (SEC-005); :meth:`import_beds` checks again."""
        require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)

    def import_beds(
        self,
        site_key: SiteKey,
        *,
        tenant_key: str,
        user_key: str,
        role: TenantRole,
        content: bytes,
        dry_run: bool,
        expected_revision: int | None = None,
    ) -> BedCsvImportReport:
        """Check the file and, unless ``dry_run``, write its valid lines. See the module docstring for the order.

        ``expected_revision`` (the ``plan_revision`` of the dry run) makes a plan changed in between a 409
        ``plan.revision_conflict``; without it the confirmation writes against the revision it reads.
        """
        started = perf_counter()
        site = require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)  # (2) tenant anchor
        if not MembershipEngine.can_delete_resource(role):  # (3) lead only (SR-010)
            raise PlanError(ERROR_FORBIDDEN, "Only a lead may import a bed list.", status_code=403)
        records, header = self._read(content)  # (4)
        checked = self._check_lines(records, header, site_key=site_key, tenant_key=tenant_key)  # (5)
        locations, objects = self._plan.load_structure(site_key, tenant_key=tenant_key)
        # (6) the site quota on the lines that passed (5), *before* the placement: what the placement and the plan
        # rules work on is then bounded by the quota itself - existing structure plus new beds <= 500 (SEC-001).
        current = len(locations) + len(objects) + len(checked.lines)
        if checked.lines and current > MAX_PLAN_OBJECTS_PER_SITE:
            raise PlanError(
                ERROR_QUOTA,
                f"A site holds at most {MAX_PLAN_OBJECTS_PER_SITE} locations and garden objects.",
                status_code=422,
                limit=MAX_PLAN_OBJECTS_PER_SITE,
                current=current,
            )
        rows = self._place(site, checked, locations, objects, tenant_key=tenant_key, started=started)  # (7)
        report = self._report(site, checked, rows, records=records, header=header, dry_run=dry_run)
        if dry_run or not rows:
            logger.info(
                "garden_plan.csv_import_checked",
                site_key=site_key,
                rows=len(records),
                valid=len(rows),
                errors=report.errors_total,
            )
            return report

        temp_keys = {row.line: f"{_TEMP_PREFIX}{row.line}" for row in rows}
        result = self._plans.create_beds(
            site_key,
            tenant_key=tenant_key,
            user_key=user_key,
            role=role,
            beds=[(temp_keys[row.line], _bed_data(row)) for row in rows],
            expected_revision=expected_revision,
            audit_summary=f"{len(rows)} beds from a CSV bed list",
        )
        for row in report.rows:
            row.location_key = result.key_map.get(temp_keys[row.line])
        report.applied = True
        report.plan_revision = result.plan_revision
        logger.info(
            "garden_plan.csv_import_applied",
            site_key=site_key,
            revision=result.plan_revision,
            created=len(rows),
            skipped=report.rows_skipped,
            duration_ms=round((perf_counter() - started) * 1000),
        )
        return report

    # ── (4) the file ──────────────────────────────────────────────────────────

    @staticmethod
    def _read(content: bytes) -> tuple[tuple[CsvRecord, ...], _Header]:
        if len(content) > MAX_CSV_BYTES:
            raise RequestBodyTooLargeError(MAX_CSV_BYTES)
        try:
            table = read_table(decode_csv(content), max_records=MAX_CSV_ROWS)
        except CsvReadError as exc:
            raise PlanError(exc.code, str(exc), status_code=422, field="file") from None
        if len(table.records) > MAX_CSV_ROWS:
            raise PlanError(
                ERROR_QUOTA,
                f"A bed list holds at most {MAX_CSV_ROWS} rows.",
                status_code=422,
                field="file",
                limit=MAX_CSV_ROWS,
                current=len(table.records),
            )
        return table.records, _header(table.header)

    # ── (5) every line ────────────────────────────────────────────────────────

    def _check_lines(
        self, records: Iterable[CsvRecord], header: _Header, *, site_key: str, tenant_key: str
    ) -> _Checked:
        bed_types = _type_index(self._types.get_all())
        zones = self._zone_index(site_key, tenant_key=tenant_key) if _ZONE in header.positions else {}
        checked = _Checked()
        for record in records:
            line = _LineReader(record, header, checked)
            name = line.text(_NAME)
            type_key = line.bed_type(bed_types)
            width = line.dimension(_WIDTH)
            length = line.dimension(_LENGTH)
            sun = line.choice(_SUN, _SUN_INDEX)
            soil = line.choice(_SOIL, _SOIL_INDEX)
            zone = line.zone(zones)
            if line.failed or name is None or type_key is None or width is None or length is None:
                continue
            checked.add_line(
                _Line(
                    line=record.line,
                    name=name,
                    location_type_key=type_key,
                    width_m=width,
                    length_m=length,
                    sun_exposure=sun or SunExposure.UNKNOWN,
                    soil_texture=None if soil == SoilTexture.UNKNOWN else soil,
                    irrigation_zone_key=zone,
                )
            )
        return checked

    def _zone_index(self, site_key: str, *, tenant_key: str) -> dict[str, list[str]]:
        """Zone name (case-folded) → the keys of the zones of the path site that carry it."""
        index: dict[str, list[str]] = {}
        for zone in self._zones.list_zones_by_site(site_key, tenant_key=tenant_key, offset=0, limit=MAX_PLAN_ZONES):
            if zone.key:
                index.setdefault(zone.name.strip().casefold(), []).append(zone.key)
        return index

    # ── (6) placement and the plan rules ──────────────────────────────────────

    def _place(
        self,
        site: Site,
        checked: _Checked,
        locations: list[Location],
        objects: list[GardenObject],
        *,
        tenant_key: str,
        started: float,
    ) -> list[CsvBedRow]:
        """The rows the import writes: placed in rows from the top-left, then checked like a batch would check them.

        A bed that finds no place inside the boundary is a ``csv.does_not_fit`` of its line and takes no space. A
        line the plan rules refuse after the placement (outside a non-rectangular boundary, overlapping a nested
        bed) is moved to the errors; its position stays taken, so the other lines keep the positions the dry run
        named.
        """
        if not checked.lines:
            return []
        boundary = site.plan.boundary if site.plan is not None else None
        sizes = [(line.width_m, line.length_m) for line in checked.lines]
        frame: Box = (
            bounding_box(boundary)
            if boundary is not None
            else (0.0, 0.0, MAX_COORDINATE_M, max(length for _, length in sizes))
        )
        flags = self._plan.bed_type_flags(sorted({loc.location_type_key for loc in locations if loc.location_type_key}))
        obstacles = [
            loc.bbox
            for loc in locations
            if loc.parent_location_key is None and loc.bbox is not None and flags.get(loc.location_type_key, False)
        ]
        try:
            positions = place_in_rows(sizes, frame=frame, obstacles=obstacles, gap=BED_ROW_GAP_M)
        except PlacementTooComplexError:
            raise _too_complex() from None
        _check_deadline(started)

        site_key = site.key or ""
        candidates: list[tuple[_Line, tuple[float, float], Location]] = []
        for line, origin in zip(checked.lines, positions, strict=True):
            if origin is None:
                checked.add_error(line.line, ERROR_DOES_NOT_FIT)
                continue
            try:
                location = Location(
                    name=line.name,
                    site_key=site_key,
                    location_type_key=line.location_type_key,
                    geometry=_rect(origin, line.width_m, line.length_m),
                    area_m2=0.0,
                )
            except PydanticValidationError:
                checked.add_error(line.line, GEOMETRY_INVALID)
                continue
            candidates += [(line, origin, location)]

        temp = [f"{_TEMP_PREFIX}{line.line}" for line, _, _ in candidates]
        structure = {loc.key: loc for loc in locations if loc.key}
        structure.update({key: location for key, (_, _, location) in zip(temp, candidates, strict=True)})
        findings = self._plans.check_imported_structure(
            site_key,
            tenant_key=tenant_key,
            locations=structure,
            objects={obj.key: obj for obj in objects if obj.key},
            imported_locations=temp,
            imported_objects=[],
            boundary=boundary,
            boundary_changed=False,
        )
        _check_deadline(started)
        refused: dict[int, set[str]] = {}
        for index, _field, code, _extra in findings:
            if index is not None and 0 <= index < len(candidates):
                refused.setdefault(index, set()).add(code)
        for index in sorted(refused):
            for code in sorted(refused[index]):
                checked.add_error(candidates[index][0].line, code)
        return [
            CsvBedRow(
                line=line.line,
                name=line.name,
                location_type_key=line.location_type_key,
                width_m=line.width_m,
                length_m=line.length_m,
                origin=origin,
                sun_exposure=line.sun_exposure,
                soil_texture=line.soil_texture,
                irrigation_zone_key=line.irrigation_zone_key,
            )
            for index, (line, origin, _) in enumerate(candidates)
            if index not in refused
        ]

    # ── the report ────────────────────────────────────────────────────────────

    @staticmethod
    def _report(
        site: Site,
        checked: _Checked,
        rows: list[CsvBedRow],
        *,
        records: tuple[CsvRecord, ...],
        header: _Header,
        dry_run: bool,
    ) -> BedCsvImportReport:
        errors = sorted(checked.errors, key=lambda finding: (finding.line, finding.column or "", finding.code))
        warnings = sorted(checked.warnings, key=lambda finding: (finding.line, finding.column or ""))
        return BedCsvImportReport(
            dry_run=dry_run,
            rows_total=len(records),
            rows=rows,
            rows_valid=len(rows),
            rows_skipped=len(records) - len(rows),
            errors=errors[:MAX_REPORTED_LINES],
            errors_total=len(errors),
            warnings=warnings[:MAX_REPORTED_LINES],
            warnings_total=len(warnings),
            ignored_columns=header.ignored[:MAX_IGNORED_COLUMNS],
            ignored_columns_total=len(header.ignored),
            plan_revision=site.plan.plan_revision if site.plan is not None else 0,
        )


# ── helpers ──────────────────────────────────────────────────────────────────


def _too_complex() -> PlanError:
    """The batch path's answer to a request past its budget (GP-NFR-013): 422 ``batch.too_complex``."""
    return PlanError(
        ERROR_TOO_COMPLEX,
        "The bed list took longer than its time budget; nothing was applied.",
        status_code=422,
        field="file",
        limit=int(BATCH_TIME_BUDGET_SECONDS),
    )


def _check_deadline(started: float) -> None:
    """The batch's time budget for the dry-run work too: placement and plan rules run before ``_apply`` (SEC-001)."""
    if perf_counter() - started > BATCH_TIME_BUDGET_SECONDS:
        raise _too_complex()


def _header(cells: tuple[str, ...]) -> _Header:
    positions: dict[str, int] = {}
    spelled: dict[str, str] = {}
    ignored: list[str] = []
    aliases: dict[str, str] = _HEADER_TO_COLUMN
    for position, cell in enumerate(cells):
        column = aliases.get(header_key(cell))
        if column is None:
            if cell.strip():
                ignored.append(neutralised_text(cell)[:_HEADER_ECHO])
            continue
        if column in positions:
            raise PlanError(
                ERROR_DUPLICATE_COLUMN,
                "A column is named twice in the header.",
                status_code=422,
                field="file",
                column=neutralised_text(cell)[:_HEADER_ECHO],
            )
        positions[column] = position
        spelled[column] = neutralised_text(cell)[:_HEADER_ECHO]
    missing = [_CANONICAL_HEADER[column] for column in _REQUIRED_COLUMNS if column not in positions]
    if missing:
        raise PlanError(
            ERROR_MISSING_COLUMN,
            "The header lacks a required column (Name;Typ;Breite_m;Länge_m).",
            status_code=422,
            field="file",
            columns=missing,
        )
    return _Header(positions=positions, spelled=spelled, ignored=ignored)


def _type_index(types: Iterable[LocationType]) -> dict[str, tuple[str, bool]]:
    """Key, German and English name (reduced) → ``(location_type_key, is_bed)``; a key wins over a name."""
    index: dict[str, tuple[str, bool]] = {}
    ordered = sorted((t for t in types if t.key), key=lambda t: (t.sort_order, t.key or ""))
    for location_type in ordered:
        for name in (location_type.name, location_type.name_en):
            if name:
                index.setdefault(label_key(name), (location_type.key or "", location_type.is_bed))
    for location_type in ordered:
        index[label_key(location_type.key or "")] = (location_type.key or "", location_type.is_bed)
    return index


def _rect(origin: tuple[float, float], width: float, length: float) -> dict[str, object]:
    return {"kind": "rect", "origin": [origin[0], origin[1]], "width_m": width, "length_m": length, "rotation_deg": 0.0}


def _bed_data(row: CsvBedRow) -> ImportedBedData:
    fields: dict[str, object] = {
        "name": row.name,
        "location_type_key": row.location_type_key,
        "geometry": _rect(row.origin, row.width_m, row.length_m),
        "sun_exposure": row.sun_exposure,
        "soil_profile": SoilProfile(soil_texture=row.soil_texture) if row.soil_texture is not None else None,
        "irrigation_zone_key": row.irrigation_zone_key,
    }
    return ImportedBedData(**fields)  # the geometry mapping is validated by Pydantic


class _LineReader:
    """Reads the cells of one record and records what is wrong with them."""

    def __init__(self, record: CsvRecord, header: _Header, checked: _Checked) -> None:
        self._record = record
        self._header = header
        self._checked = checked
        self.failed = False

    def _column(self, column: str) -> str | None:
        """The header cell of ``column`` as the file spells it."""
        spelled: dict[str, str] = self._header.spelled
        return spelled.get(column)

    def _cell(self, column: str) -> str | None:
        """The raw cell, ``None`` when the file has no such column; a short row reads as empty cells."""
        position = self._header.positions.get(column)
        if position is None:
            return None
        cells = self._record.cells
        return cells[position] if position < len(cells) else ""

    def _error(self, column: str, code: str) -> None:
        self.failed = True
        self._checked.add_error(self._record.line, code, self._column(column))

    def _value(self, column: str) -> str:
        """The neutralised text of a cell; a stripped formula prefix is a warning of the line."""
        value, stripped = neutralise(self._cell(column) or "")
        if stripped:
            self._checked.add_warning(self._record.line, WARNING_FORMULA_STRIPPED, self._column(column))
        return value

    def text(self, column: str) -> str | None:
        value = self._value(column)
        if not value:
            self._error(column, ERROR_REQUIRED)
            return None
        if len(value) > _MAX_NAME_CHARS:
            self._error(column, ERROR_TOO_LONG)
            return None
        return value

    def bed_type(self, index: dict[str, tuple[str, bool]]) -> str | None:
        value = self._value(_TYPE)
        if not value:
            self._error(_TYPE, ERROR_REQUIRED)
            return None
        found = index.get(label_key(value))
        if found is None:
            self._error(_TYPE, ERROR_UNKNOWN_TYPE)
            return None
        key, is_bed = found
        if not is_bed:
            self._error(_TYPE, ERROR_NOT_A_BED_TYPE)
            return None
        return key

    def dimension(self, column: str) -> float | None:
        """A number cell: read as it stands (a number is never neutralised - ``=2`` is no number)."""
        raw = (self._cell(column) or "").strip()
        if not raw:
            self._error(column, ERROR_REQUIRED)
            return None
        try:
            value = round_length(parse_decimal(raw))  # stored in millimetres (§9.2): the report shows that value
        except ValueError:
            self._error(column, ERROR_INVALID_NUMBER)
            return None
        if not MIN_DIMENSION_M <= value <= MAX_DIMENSION_M:
            self._error(column, ERROR_OUT_OF_RANGE)
            return None
        return value

    def choice[TEnum: StrEnum](self, column: str, index: dict[str, TEnum]) -> TEnum | None:
        if column not in self._header.positions:
            return None
        value = self._value(column)
        if not value:
            return None
        found = index.get(label_key(value))
        if found is None:
            self._error(column, ERROR_UNKNOWN_VALUE)
        return found

    def zone(self, zones: dict[str, list[str]]) -> str | None:
        if _ZONE not in self._header.positions:
            return None
        value = self._value(_ZONE)
        if not value:
            return None
        keys = zones.get(value.casefold())
        if not keys:
            self._error(_ZONE, ERROR_UNKNOWN_ZONE)
            return None
        if len(keys) > 1:
            self._error(_ZONE, ERROR_AMBIGUOUS_ZONE)
            return None
        return keys[0]
