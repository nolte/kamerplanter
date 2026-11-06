"""WP 8.25 (#2668) — the bed list as CSV rows: default columns, selectable site features, assignment opt-in only.

What is pinned here (REQ-053 GP-FR-145, GP-FR-175, SR-016, SR-024):

* the default selection is GP-FR-145's seven columns, and a selection writes them in one fixed order;
* the assignment column exists only through ``include_assignment`` - naming it in ``columns`` is refused, and a
  row that carries names writes none of them unless the column was resolved;
* text cells are neutralised (a bed named ``=HYPERLINK(...)``), numbers are not (``-`` of a number stays);
* the Excel variant writes the decimal comma.
"""

from __future__ import annotations

import pytest

from app.common.enums import (
    AccessSide,
    BedStatus,
    FrostRisk,
    HeatRetention,
    SiteFlag,
    SoilTexture,
    SunExposure,
    SunWindow,
    WindExposure,
)
from app.common.exceptions import PlanError
from app.domain.engines.bed_list_csv_engine import (
    ASSIGNMENT_COLUMN,
    DEFAULT_COLUMNS,
    ERROR_NO_COLUMNS,
    ERROR_UNKNOWN_COLUMN,
    SELECTABLE_COLUMNS,
    SITE_CONDITION_COLUMNS,
    bed_list_csv_rows,
    resolve_bed_list_columns,
)
from app.domain.models.bed_list_export import BedListExportRow
from app.domain.models.garden_plan import BedCounters
from app.domain.models.site import Location, Microclimate, SiteConditions, SoilProfile, SunProfile


def _row(**fields) -> BedListExportRow:  # type: ignore[no-untyped-def]
    location = Location(
        _key=fields.pop("key", "loc_1"),
        name=fields.pop("name", "Hochbeet 3"),
        site_key="site_1",
        location_type_key="raised_bed",
        area_m2=fields.pop("area_m2", 2.4),
        bed_status=fields.pop("bed_status", BedStatus.ACTIVE),
        sun_exposure=fields.pop("sun_exposure", SunExposure.FULL_SUN),
        soil_profile=fields.pop("soil_profile", SoilProfile(soil_texture=SoilTexture.LOAM)),
        site_conditions=fields.pop("site_conditions", None),
        irrigation_zone_key="zone_1",
    )
    return BedListExportRow(
        location=location,
        counters=fields.pop("counters", BedCounters(active_plant_count=6)),
        type_name=fields.pop("type_name", "Hochbeet"),
        zone_name=fields.pop("zone_name", "Tropf Ost"),
        assignees=fields.pop("assignees", None),
    )


def _cells(row: BedListExportRow, columns: tuple[str, ...], *, decimal_comma: bool = False) -> dict[str, str]:
    return dict(zip(columns, bed_list_csv_rows([row], columns, decimal_comma=decimal_comma)[0], strict=True))


# ── the column selection ───────────────────────────────────────────────────────────────────────────


class TestTheColumnSelection:
    def test_no_selection_is_the_seven_columns_of_gp_fr_145(self) -> None:
        assert resolve_bed_list_columns(None, include_assignment=False) == (
            "name",
            "type",
            "area_m2",
            "status",
            "soil_texture",
            "irrigation_zone",
            "active_plants",
        )

    def test_a_selection_is_written_in_the_fixed_order_once(self) -> None:
        columns = resolve_bed_list_columns("frost_risk, name,frost_risk,,status", include_assignment=False)
        assert columns == ("name", "status", "frost_risk")

    def test_every_site_feature_of_section_10_2_is_selectable(self) -> None:
        columns = resolve_bed_list_columns(",".join(SITE_CONDITION_COLUMNS), include_assignment=False)
        assert columns == SITE_CONDITION_COLUMNS

    def test_an_unknown_column_is_refused_with_its_name(self) -> None:
        with pytest.raises(PlanError) as refused:
            resolve_bed_list_columns("name,gps_coordinates", include_assignment=False)
        assert refused.value.status_code == 422
        assert refused.value.details[0]["code"] == ERROR_UNKNOWN_COLUMN
        assert refused.value.details[0]["columns"] == ["gps_coordinates"]

    def test_the_assignment_cannot_be_picked_as_a_column(self) -> None:
        """SR-024: the only way to member names is the explicit opt-in, not a column name in the query."""
        with pytest.raises(PlanError) as refused:
            resolve_bed_list_columns(f"name,{ASSIGNMENT_COLUMN}", include_assignment=False)
        assert refused.value.details[0]["code"] == ERROR_UNKNOWN_COLUMN
        assert ASSIGNMENT_COLUMN not in SELECTABLE_COLUMNS

    def test_an_empty_selection_is_refused(self) -> None:
        with pytest.raises(PlanError) as refused:
            resolve_bed_list_columns(" , ", include_assignment=False)
        assert refused.value.details[0]["code"] == ERROR_NO_COLUMNS

    def test_the_opt_in_appends_the_assignment_last(self) -> None:
        assert resolve_bed_list_columns(None, include_assignment=True) == (*DEFAULT_COLUMNS, ASSIGNMENT_COLUMN)
        assert resolve_bed_list_columns("site_flags,name", include_assignment=True) == (
            "name",
            "site_flags",
            ASSIGNMENT_COLUMN,
        )


# ── the cells ──────────────────────────────────────────────────────────────────────────────────────


class TestTheCells:
    def test_the_default_row(self) -> None:
        assert _cells(_row(), DEFAULT_COLUMNS) == {
            "name": "Hochbeet 3",
            "type": "Hochbeet",
            "area_m2": "2.4",
            "status": "active",
            "soil_texture": "loam",
            "irrigation_zone": "Tropf Ost",
            "active_plants": "6",
        }

    def test_one_cell_per_column(self) -> None:
        everything = resolve_bed_list_columns(",".join(SELECTABLE_COLUMNS), include_assignment=True)
        assert len(bed_list_csv_rows([_row()], everything)[0]) == len(everything)

    def test_the_type_key_stands_in_for_a_type_that_does_not_resolve(self) -> None:
        assert _cells(_row(type_name=None), ("type",)) == {"type": "raised_bed"}

    def test_missing_references_are_empty_cells(self) -> None:
        row = _row(soil_profile=None, zone_name=None, counters=None)
        assert _cells(row, ("soil_texture", "irrigation_zone", "active_plants")) == {
            "soil_texture": "",
            "irrigation_zone": "",
            "active_plants": "",
        }

    def test_the_area_is_rounded_to_square_centimetres(self) -> None:
        assert _cells(_row(area_m2=2.9999999999), ("area_m2",)) == {"area_m2": "3.0"}

    def test_the_excel_variant_writes_the_decimal_comma(self) -> None:
        conditions = SiteConditions(slope_deg=12.5)
        cells = _cells(_row(site_conditions=conditions), ("area_m2", "slope_deg"), decimal_comma=True)
        assert cells == {"area_m2": "2,4", "slope_deg": "12,5"}

    def test_the_site_features(self) -> None:
        conditions = SiteConditions(
            sun_profile=SunProfile(
                sun_window=SunWindow.MORNING, direct_sun_hours_summer=5.5, foliage_shade_in_summer=True
            ),
            microclimate=Microclimate(
                frost_risk=FrostRisk.HIGH, cold_air_pocket=False, heat_retention=HeatRetention.WALL
            ),
            wind_exposure=WindExposure.EXPOSED,
            slope_deg=8.0,
            aspect_deg=180.0,
            access_sides=[AccessSide.NORTH, AccessSide.SOUTH],
            flags=[SiteFlag.ROOT_COMPETITION],
        )
        assert _cells(_row(site_conditions=conditions), SITE_CONDITION_COLUMNS) == {
            "sun_exposure": "full_sun",
            "sun_window": "morning",
            "direct_sun_hours_summer": "5.5",
            "foliage_shade_in_summer": "yes",
            "frost_risk": "high",
            "cold_air_pocket": "no",
            "heat_retention": "wall",
            "wind_exposure": "exposed",
            "slope_deg": "8.0",
            "aspect_deg": "180.0",
            "access_sides": "N | S",
            "site_flags": "root_competition",
        }

    def test_a_bed_without_site_features_has_empty_feature_cells(self) -> None:
        cells = _cells(_row(site_conditions=None), SITE_CONDITION_COLUMNS)
        assert cells.pop("sun_exposure") == "full_sun"  # §10.1's coarse class lives on the location itself
        assert set(cells.values()) == {""}


# ── SR-016 / SR-024 ────────────────────────────────────────────────────────────────────────────────


class TestTheHardening:
    @pytest.mark.parametrize("name", ['=HYPERLINK("http://x")', "+1", "-2+3", "@SUM(A1)", "\tcmd", "\rcmd"])
    def test_a_formula_looking_name_is_neutralised(self, name: str) -> None:
        assert _cells(_row(name=name), ("name",)) == {"name": f"'{name}"}

    def test_formula_looking_labels_and_member_names_are_neutralised(self) -> None:
        row = _row(type_name="=cmd", zone_name="@zone", assignees=["=Mallory", "Sabine"])
        cells = _cells(row, ("type", "irrigation_zone", ASSIGNMENT_COLUMN))
        assert cells == {"type": "'=cmd", "irrigation_zone": "'@zone", ASSIGNMENT_COLUMN: "'=Mallory | Sabine"}

    def test_a_negative_number_is_never_prefixed(self) -> None:
        """Numbers go through ``csv_number``: no value written here is a text cell that starts with ``-``."""
        conditions = SiteConditions(slope_deg=0.0, aspect_deg=0.0)
        cells = _cells(_row(site_conditions=conditions), ("slope_deg", "aspect_deg", "area_m2"))
        assert all(not value.startswith("'") for value in cells.values())

    def test_names_on_the_row_are_not_written_without_the_column(self) -> None:
        row = _row(assignees=["Sabine Gärtner"])
        written = bed_list_csv_rows([row], resolve_bed_list_columns(None, include_assignment=False))[0]
        assert "Sabine Gärtner" not in written

    def test_the_assignment_cell_joins_the_display_names(self) -> None:
        cells = _cells(_row(assignees=["Anna", "Ben"]), (ASSIGNMENT_COLUMN,))
        assert cells == {ASSIGNMENT_COLUMN: "Anna | Ben"}

    def test_a_bed_nobody_is_assigned_to_has_an_empty_cell(self) -> None:
        assert _cells(_row(assignees=[]), (ASSIGNMENT_COLUMN,)) == {ASSIGNMENT_COLUMN: ""}
