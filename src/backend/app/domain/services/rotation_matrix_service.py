"""The rotation matrix of a site: beds x years x season (REQ-053 GP-FR-135, ``GET /sites/{key}/rotation-matrix``).

Rows are the beds of the site, columns the years, a cell the list of what stood in that bed in that year. **There is
no second aggregation**: every bed is read through the same three calls of
:class:`~app.domain.engines.crop_rotation_validator.CropRotationValidator` as ``GET /locations/{key}/rotation``
(:meth:`~CropRotationValidator.bed_rotation_entries`, :meth:`~CropRotationValidator.timeline_years`,
:meth:`~CropRotationValidator.timeline_rows`), so a matrix cell is the timeline row of the same bed and year by
construction. Beds the rotation check is off for (``rotation_exempt`` or switched off)
are listed and marked (``rotation_applicable = false`` plus the reason), never silently dropped.

Future columns: the spec names ``CropRotationPlan`` as their source; that plan has no persisted store yet, so the
matrix stops at the current year and invents no planned crop (nothing without a source is shown).

Every method takes ``*, tenant_key: str`` without a default; the site is resolved through the ownership anchor
(:func:`~app.domain.services.location_ownership.require_owned_site`) before anything else is read.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.common.datetimes import today_utc
from app.config.constants import MAX_ROTATION_MATRIX_BEDS
from app.domain.engines.crop_rotation_validator import (
    CropRotationValidator,
    HistoryEntry,
    TimelineEntry,
    not_applicable_reason,
)
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.services.location_ownership import require_owned_site


@dataclass(frozen=True)
class RotationMatrixBed:
    """One row of the matrix: a bed and every timeline row of the matrix window, newest year first."""

    location_key: str
    name: str
    applicable: bool
    not_applicable_reason: str | None
    rotation_reset_at: date | None
    entries: list[TimelineEntry] = field(default_factory=list)


@dataclass(frozen=True)
class RotationMatrix:
    site_key: str
    years: int
    from_year: int
    to_year: int
    #: Beds counted for paging: all beds of the site, at most ``MAX_ROTATION_MATRIX_BEDS``.
    total: int
    #: ``True`` when the site holds more beds than the matrix reads (the surplus is not listed).
    truncated: bool
    offset: int
    limit: int
    beds: list[RotationMatrixBed]


class RotationMatrixService:
    def __init__(
        self, site_repo: ISiteRepository, plan_repo: IGardenPlanRepository, validator: CropRotationValidator
    ) -> None:
        self._sites = site_repo
        self._plan = plan_repo
        self._validator = validator

    def rotation_matrix(
        self, site_key: str, *, tenant_key: str, years: int | None = None, offset: int = 0, limit: int = 50
    ) -> RotationMatrix:
        """The matrix of the beds ``offset .. offset + limit`` of the site (name order, at most 500 beds).

        ``years`` defaults to ``max(longest pause named by the families of the listed beds, 5)``, at most 10
        (a larger value is 422 ``rotation.years_out_of_range``). The default is read from the page, so a client
        that pages passes the ``years`` of the first answer to keep the columns the same.
        """
        require_owned_site(self._sites, site_key, tenant_key, "Site", site_key)
        self._validator.check_timeline_years(years)
        # the whole hierarchy: a bed inside a greenhouse or an area hangs under its parent, not under the site
        locations = self._sites.get_location_tree(site_key, tenant_key=tenant_key)
        flags = self._plan.bed_type_flags(sorted({loc.location_type_key for loc in locations if loc.location_type_key}))
        beds = sorted(
            (loc for loc in locations if loc.key and flags.get(loc.location_type_key, False)),
            key=lambda loc: (loc.name.casefold(), loc.key or ""),
        )
        truncated = len(beds) > MAX_ROTATION_MATRIX_BEDS
        beds = beds[:MAX_ROTATION_MATRIX_BEDS]
        page = beds[offset : offset + limit]

        resolver = self._validator.timeline_resolver(tenant_key)
        history: dict[str, tuple[list[HistoryEntry], date | None]] = {
            loc.key or "": self._validator.bed_rotation_entries(loc, tenant_key=tenant_key) for loc in page
        }
        window = self._validator.timeline_years(
            [entry for entries, _ in history.values() for entry in entries], years, resolver
        )
        today_year = today_utc().year
        from_year = today_year - window + 1
        rows: list[RotationMatrixBed] = []
        for loc in page:
            entries, reset_at = history[loc.key or ""]
            reason = not_applicable_reason(loc)
            rows.append(
                RotationMatrixBed(
                    location_key=loc.key or "",
                    name=loc.name,
                    applicable=reason is None,
                    not_applicable_reason=reason,
                    rotation_reset_at=reset_at,
                    entries=self._validator.timeline_rows(entries, from_year=from_year, resolver=resolver),
                )
            )
        return RotationMatrix(site_key, window, from_year, today_year, len(beds), truncated, offset, limit, rows)
