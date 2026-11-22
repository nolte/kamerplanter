"""REQ-053 WP 8.26 (#2669) - the CSV bed list import against the in-memory plan repository.

What is pinned: who may import and in which order a file is refused (SR-013), the line errors of the report
(line, column, code), that a dry run writes nothing, that a confirmation writes exactly the valid lines - through
:meth:`GardenPlanService.create_beds`, i.e. one batch write with the revision check and an ``import_csv`` change-log
row - and the mapping of ``Typ``, ``Sonne``, ``Bodenart`` and ``Zone``. The transaction itself is measured against
ArangoDB in ``tests/integration/test_bed_csv_import.py``.
"""

from __future__ import annotations

import pytest

from app.common.csv_export import BOM
from app.common.enums import SoilTexture, SunExposure, TenantRole
from app.common.exceptions import NotFoundError, PlanError, PlanRevisionConflictError, RequestBodyTooLargeError
from app.domain.models.bed_csv_import import BED_ROW_GAP_M, MAX_CSV_BYTES
from app.domain.models.garden_plan import ImportedBedData
from app.domain.models.site import SitePlan
from app.domain.services.bed_csv_import_service import BedCsvImportService
from app.domain.services.garden_plan_service import GardenPlanService
from tests.support.bed_csv_fakes import FakeLocationTypes, FakeZones, zone
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
    rect,
)

USER = "u_sabine"
FOREIGN_SITE = "site_foreign"
HEADER = "Name;Typ;Breite_m;Länge_m"


@pytest.fixture
def repo() -> FakePlanRepo:
    site = make_site()
    site.plan = SitePlan(
        boundary={"kind": "rect", "origin": [0, 0], "width_m": 10, "length_m": 10, "rotation_deg": 0}, plan_revision=3
    )
    foreign = make_site(tenant=OTHER_TENANT).model_copy(update={"key": FOREIGN_SITE})
    return FakePlanRepo(FakeSites(site, foreign))


@pytest.fixture
def zones() -> FakeZones:
    return FakeZones(
        zone("z_front", "Tropfer vorne"),
        zone("z_a", "Doppelt"),
        zone("z_b", "Doppelt"),
        zone("z_foreign", "Fremd", site=FOREIGN_SITE, tenant=OTHER_TENANT),
    )


@pytest.fixture
def service(repo: FakePlanRepo, zones: FakeZones) -> BedCsvImportService:
    plans = GardenPlanService(repo._sites, repo)
    return BedCsvImportService(repo._sites, repo, plans, FakeLocationTypes(), zones)


def csv(*lines: str, header: str = HEADER) -> bytes:
    return "\r\n".join([header, *lines, ""]).encode("utf-8")


def run(service: BedCsvImportService, content: bytes, **options):
    params = {
        "tenant_key": TENANT,
        "user_key": USER,
        "role": TenantRole.LEAD,
        "dry_run": True,
        "expected_revision": None,
    } | options
    return service.import_beds(SITE, content=content, **params)


def codes(report) -> list[tuple[int, str | None, str]]:
    return [(e.line, e.column, e.code) for e in report.errors]


class TestTheDryRun:
    def test_it_reports_the_beds_and_writes_nothing(self, service, repo) -> None:
        report = run(service, csv("Beet 1;Beet;2;1", "Hochbeet;Hochbeet;1,5;0.8"))

        assert report.dry_run is True and report.applied is False and report.plan_revision == 3
        assert [(r.line, r.name, r.location_type_key, r.width_m, r.length_m) for r in report.rows] == [
            (2, "Beet 1", "bed", 2.0, 1.0),
            (3, "Hochbeet", "raised_bed", 1.5, 0.8),
        ]
        assert report.rows_valid == 2 and report.rows_skipped == 0 and report.errors == []
        assert all(row.location_key is None for row in report.rows)
        assert repo.applied == [] and repo.locations == {}  # nothing reached the transaction

    def test_beds_stand_in_one_row_from_the_top_left_corner_with_the_gap(self, service) -> None:
        report = run(service, csv("A;Beet;2;1", "B;Beet;3;1,2"))

        # boundary 10 x 10: the top edge is y = 10; origin = lower-left corner (§9.2)
        assert [row.origin for row in report.rows] == [(0.0, 9.0), (2.0 + BED_ROW_GAP_M, 8.8)]

    def test_an_existing_bed_in_the_corner_is_stepped_over(self, service, repo) -> None:
        repo.locations["old"] = make_location("old", "Altes Beet", geometry=rect(0, 9, 2, 1))

        report = run(service, csv("A;Beet;2;1"))

        assert report.errors == [] and report.rows[0].origin == (2.5, 9.0)


class TestLineErrors:
    def test_each_faulty_line_is_reported_with_line_column_and_code(self, service) -> None:
        report = run(
            service,
            csv(
                "Gut;Beet;2;1",
                ";Beet;2;1",
                "Breit;Beet;zwei;1",
                "Negativ;Beet;-2;1",
                "Riesig;Beet;2000;1",
                "Typlos;Kartoffelacker;2;1",
                "Haus;Gewächshaus;2;1",
                "Kurz;Beet;2",
            ),
        )

        assert codes(report) == [
            (3, "Name", "csv.required"),
            (4, "Breite_m", "csv.invalid_number"),
            (5, "Breite_m", "csv.invalid_number"),
            (6, "Breite_m", "csv.out_of_range"),
            (7, "Typ", "csv.unknown_type"),
            (8, "Typ", "csv.not_a_bed_type"),
            (9, "Länge_m", "csv.required"),
        ]
        assert [row.line for row in report.rows] == [2]
        assert report.rows_total == 8 and report.rows_skipped == 7 and report.errors_total == 7

    def test_a_cell_value_is_never_echoed_in_an_error(self, service) -> None:
        report = run(service, csv("Geheim;<script>x</script>;2;1"))

        assert "<script>" not in report.model_dump_json(include={"errors"})

    def test_a_bed_that_finds_no_place_in_the_boundary_is_a_line_error_of_its_row(self, service) -> None:
        report = run(service, csv("Passt;Beet;4;4", "Passt nicht;Beet;9;8", "Passt auch;Beet;4;4"))

        assert codes(report) == [(3, None, "csv.does_not_fit")]
        assert [(row.line, row.origin) for row in report.rows] == [(2, (0.0, 6.0)), (4, (4.5, 6.0))]

    def test_a_bed_outside_a_non_rectangular_boundary_is_refused_by_containment(self, service, repo) -> None:
        """The rows follow the boundary's bounding box; the batch's containment rule decides for the shape itself."""
        # the area x <= y: the top-left corner lies inside, the lower right half of the bounding box does not
        triangle = {"kind": "polygon", "points": [[0, 0], [10, 10], [0, 10]]}
        repo._sites.sites[SITE].plan = SitePlan(boundary=triangle, plan_revision=3)

        report = run(service, csv("Ecke oben links;Beet;1;1", "Lang daneben;Beet;8;1"))

        assert codes(report) == [(3, None, "geometry.outside_parent")]
        assert [row.line for row in report.rows] == [2]

    def test_a_name_longer_than_a_bed_name_is_too_long(self, service) -> None:
        assert codes(run(service, csv(f"{'x' * 201};Beet;1;1"))) == [(2, "Name", "csv.too_long")]


class TestTheConfirmation:
    def test_the_valid_lines_are_written_in_one_batch_and_the_faulty_skipped(self, service, repo) -> None:
        report = run(service, csv("A;Beet;2;1", "Kaputt;Beet;x;1", "B;Hochbeet;1;1"), dry_run=False)

        assert report.applied is True and report.plan_revision == 4
        assert codes(report) == [(3, "Breite_m", "csv.invalid_number")]
        assert len(repo.applied) == 1  # one transaction for every bed
        write = repo.applied[0]
        assert [location.name for _, location in write.location_inserts] == ["A", "B"]
        assert write.audit == [
            {"op": "import_csv", "entity": "site", "key": SITE, "summary": "2 beds from a CSV bed list"}
        ]
        created = {row.name: row.location_key for row in report.rows}
        assert set(created) == {"A", "B"} and all(created.values())
        assert {repo.locations[key].name for key in created.values()} == {"A", "B"}
        assert {loc.geometry.kind for loc in repo.locations.values()} == {"rect"}

    def test_the_confirmation_writes_the_positions_of_the_dry_run(self, service, repo) -> None:
        content = csv("A;Beet;2;1", "B;Beet;3;2")
        planned = [row.origin for row in run(service, content).rows]

        run(service, content, dry_run=False)

        assert [tuple(loc.geometry.origin) for loc in repo.locations.values()] == planned

    def test_a_file_without_a_valid_line_writes_nothing(self, service, repo) -> None:
        report = run(service, csv(";Beet;1;1"), dry_run=False)

        assert report.applied is False and report.rows == [] and repo.applied == []

    def test_a_plan_changed_since_the_dry_run_is_a_409(self, service, repo) -> None:
        with pytest.raises(PlanRevisionConflictError):
            run(service, csv("A;Beet;2;1"), dry_run=False, expected_revision=2)

        assert repo.applied == []
        run(service, csv("A;Beet;2;1"), dry_run=False, expected_revision=3)  # the positive control
        assert len(repo.applied) == 1

    def test_the_create_goes_through_the_batch_path(self, service, repo, monkeypatch) -> None:
        """No second write path: the only writer the import reaches is ``GardenPlanService.create_beds``."""
        calls: list[list[tuple[str, ImportedBedData]]] = []
        original = GardenPlanService.create_beds

        def spy(self, site_key, **kwargs):
            calls.append(kwargs["beds"])
            return original(self, site_key, **kwargs)

        monkeypatch.setattr(GardenPlanService, "create_beds", spy)

        run(service, csv("A;Beet;2;1"), dry_run=False)

        assert len(calls) == 1 and [data.name for _, data in calls[0]] == ["A"]


class TestMapping:
    @pytest.mark.parametrize("cell", ["Hochbeet", "HOCHBEET", "raised_bed", "Raised Bed", "raised bed", " hochbeet "])
    def test_the_type_reads_its_key_and_both_names_case_insensitively(self, service, cell) -> None:
        assert run(service, csv(f"A;{cell};1;1")).rows[0].location_type_key == "raised_bed"

    @pytest.mark.parametrize(
        ("cell", "value"),
        [
            ("Volle Sonne", SunExposure.FULL_SUN),
            ("full sun", SunExposure.FULL_SUN),
            ("partial_shade", SunExposure.PARTIAL_SHADE),
            ("Halbschatten", SunExposure.PARTIAL_SHADE),
            ("Tiefschatten", SunExposure.DEEP_SHADE),
            ("", SunExposure.UNKNOWN),
        ],
    )
    def test_the_sun_reads_values_and_labels(self, service, cell, value) -> None:
        report = run(service, csv(f"A;Beet;1;1;{cell}", header=f"{HEADER};Sonne"))

        assert report.errors == [] and report.rows[0].sun_exposure == value

    @pytest.mark.parametrize(
        ("cell", "value"),
        [("Lehm", SoilTexture.LOAM), ("Sandy loam", SoilTexture.SANDY_LOAM), ("clay", SoilTexture.CLAY)],
    )
    def test_the_soil_texture_reads_values_and_labels(self, service, repo, cell, value) -> None:
        report = run(service, csv(f"A;Beet;1;1;{cell}", header=f"{HEADER};Bodenart"), dry_run=False)

        assert report.rows[0].soil_texture == value
        (location,) = repo.locations.values()
        assert location.soil_profile is not None and location.soil_profile.soil_texture == value

    def test_without_a_soil_texture_no_soil_profile_is_invented(self, service, repo) -> None:
        """E-10: an agronomic value without a source stays unset - no profile, not a profile of defaults."""
        run(service, csv("A;Beet;1;1;", "B;Beet;1;1;Unbekannt", header=f"{HEADER};Bodenart"), dry_run=False)

        assert [location.soil_profile for location in repo.locations.values()] == [None, None]

    def test_an_unknown_sun_or_soil_value_is_a_line_error(self, service) -> None:
        report = run(service, csv("A;Beet;1;1;grell;Matsch", header=f"{HEADER};Sonne;Bodenart"))

        assert codes(report) == [(2, "Bodenart", "csv.unknown_value"), (2, "Sonne", "csv.unknown_value")]

    def test_the_zone_is_a_zone_of_the_path_site_by_name(self, service, repo, zones) -> None:
        report = run(
            service,
            csv("A;Beet;1;1;tropfer VORNE", "B;Beet;1;1;Doppelt", "C;Beet;1;1;Fremd", header=f"{HEADER};Zone"),
            dry_run=False,
        )

        assert [r.irrigation_zone_key for r in report.rows] == ["z_front"]
        assert codes(report) == [(3, "Zone", "csv.ambiguous_zone"), (4, "Zone", "csv.unknown_zone")]
        assert zones.reads == [(SITE, TENANT)]  # read under the caller's tenant and the path site only
        (location,) = repo.locations.values()
        assert location.irrigation_zone_key == "z_front"

    def test_english_headers_and_unknown_columns(self, service) -> None:
        report = run(service, csv("A;bed;2.5;1;egal", header="name;type;width_m;length_m;Notiz"))

        assert report.errors == [] and report.rows[0].width_m == 2.5 and report.ignored_columns == ["Notiz"]


class TestFormulaPrefixes:
    def test_a_formula_prefix_is_discarded_and_reported_as_a_warning(self, service, repo) -> None:
        report = run(service, csv("=HYPERLINK(evil);Beet;1;1", "'@Beet Nord;Beet;1;1"), dry_run=False)

        assert [row.name for row in report.rows] == ["HYPERLINK(evil)", "Beet Nord"]
        assert [(w.line, w.column, w.code) for w in report.warnings] == [
            (2, "Name", "csv.formula_stripped"),
            (3, "Name", "csv.formula_stripped"),
        ]
        assert not any(loc.name.startswith(("=", "+", "-", "@", "'")) for loc in repo.locations.values())

    def test_a_formula_in_a_number_cell_is_no_number(self, service) -> None:
        assert codes(run(service, csv("A;Beet;=1+1;1"))) == [(2, "Breite_m", "csv.invalid_number")]


class TestTheFile:
    def test_a_bom_is_tolerated(self, service) -> None:
        report = run(service, (BOM + "Name;Typ;Breite_m;Länge_m\r\nA;Beet;1;1\r\n").encode("utf-8"))

        assert report.rows_valid == 1

    @pytest.mark.parametrize(
        ("content", "code"),
        [
            ("Name;Typ;Länge_m\r\nA;Beet;1\r\n".encode(), "csv.missing_column"),
            ("Name;Typ;Breite_m;Länge_m;Breite\r\n".encode(), "csv.duplicate_column"),
            ("Name,Typ,Breite_m,Länge_m\r\n".encode(), "csv.invalid_delimiter"),
            ("Name;Länge_m\r\nÄ;1\r\n".encode("latin-1"), "csv.invalid_encoding"),
            (b"", "csv.empty"),
        ],
    )
    def test_a_file_that_cannot_be_read_is_a_422_with_its_code(self, service, repo, content, code) -> None:
        with pytest.raises(PlanError) as caught:
            run(service, content, dry_run=False)

        assert caught.value.status_code == 422 and caught.value.error_code == code
        assert repo.applied == []

    def test_the_missing_columns_are_named(self, service) -> None:
        with pytest.raises(PlanError) as caught:
            run(service, b"Name;Typ\r\n")

        assert caught.value.details[0]["columns"] == ["Breite_m", "Länge_m"]

    def test_more_than_500_rows_is_the_plan_quota(self, service, repo) -> None:
        content = csv(*[f"B{n};Beet;0,1;0,1" for n in range(501)])

        with pytest.raises(PlanError) as caught:
            run(service, content)

        assert caught.value.status_code == 422 and caught.value.error_code == "plan.quota_exceeded"
        assert caught.value.details[0]["limit"] == 500
        assert run(service, csv(*[f"B{n};Beet;0,1;0,1" for n in range(500)])).rows_total == 500  # the bound itself

    def test_a_site_that_would_exceed_its_quota_is_a_422(self, service, repo) -> None:
        for n in range(499):
            repo.locations[f"l{n}"] = make_location(f"l{n}", f"Fläche {n}", geometry=None)

        with pytest.raises(PlanError) as caught:
            run(service, csv("A;Beet;1;1", "B;Beet;1;1"))

        assert caught.value.error_code == "plan.quota_exceeded" and caught.value.details[0]["current"] == 501
        assert run(service, csv("A;Beet;1;1")).rows_valid == 1  # 499 + 1 = 500 is allowed

    def test_a_file_above_1_mib_is_refused(self, service) -> None:
        with pytest.raises(RequestBodyTooLargeError):
            run(service, b"x" * (MAX_CSV_BYTES + 1))


class TestWhoMayImport:
    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
    def test_a_grower_or_viewer_is_refused_before_the_file_is_read(self, service, repo, role) -> None:
        with pytest.raises(PlanError) as caught:
            run(service, b"not a csv file at all", role=role, dry_run=False)

        assert caught.value.status_code == 403 and caught.value.error_code == "import.forbidden"
        assert repo.applied == []

    def test_a_foreign_site_is_a_404_before_the_file_is_read(self, service, repo) -> None:
        with pytest.raises(NotFoundError):
            service.import_beds(
                FOREIGN_SITE,
                tenant_key=TENANT,
                user_key=USER,
                role=TenantRole.LEAD,
                content=b"garbage",
                dry_run=False,
            )

        assert repo.applied == []

    def test_an_empty_tenant_is_no_tenant(self, service) -> None:
        with pytest.raises(NotFoundError):
            run(service, csv("A;Beet;1;1"), tenant_key="")


class TestTheWorkIsBounded:
    """#2669 SEC-001/SEC-002: the dry run's own work - placement and plan rules - is bounded like a batch."""

    def test_the_site_quota_is_checked_before_the_placement(self, service, repo, monkeypatch) -> None:
        import app.domain.services.bed_csv_import_service as module

        for n in range(499):
            repo.locations[f"l{n}"] = make_location(f"l{n}", f"Fläche {n}", geometry=None)

        def must_not_run(*_args, **_kwargs):
            raise AssertionError("the placement ran before the quota")

        monkeypatch.setattr(module, "place_in_rows", must_not_run)

        with pytest.raises(PlanError) as caught:
            run(service, csv("A;Beet;1;1", "B;Beet;1;1"))

        assert caught.value.error_code == "plan.quota_exceeded"

    def test_a_placement_past_its_step_budget_is_batch_too_complex(self, service, repo, monkeypatch) -> None:
        import app.domain.services.bed_csv_import_service as module
        from app.domain.calculators.bed_row_placement_calculator import PlacementTooComplexError

        def too_complex(*_args, **_kwargs):
            raise PlacementTooComplexError("budget")

        monkeypatch.setattr(module, "place_in_rows", too_complex)

        with pytest.raises(PlanError) as caught:
            run(service, csv("A;Beet;1;1"), dry_run=False)

        assert caught.value.status_code == 422 and caught.value.error_code == "batch.too_complex"
        assert repo.applied == []

    def test_a_check_past_the_batch_time_budget_is_batch_too_complex(self, service, repo, monkeypatch) -> None:
        import app.domain.services.bed_csv_import_service as module

        clock = iter([0.0, 0.0, 11.0, 11.0, 11.0])
        monkeypatch.setattr(module, "perf_counter", lambda: next(clock))

        with pytest.raises(PlanError) as caught:
            run(service, csv("A;Beet;1;1"), dry_run=False)

        assert caught.value.error_code == "batch.too_complex" and caught.value.details[0]["limit"] == 10
        assert repo.applied == []

    def test_a_crafted_plan_and_list_end_inside_the_budget(self, service, repo) -> None:
        """250 beds on the plan blocking every row, 250 lines of beds that fit nowhere: bounded, not minutes."""
        import time

        repo._sites.sites[SITE].plan = SitePlan(
            boundary={"kind": "rect", "origin": [0, 0], "width_m": 60, "length_m": 10, "rotation_deg": 0},
            plan_revision=3,
        )
        for n in range(250):
            row, col = divmod(n, 25)
            repo.locations[f"p{n}"] = make_location(f"p{n}", f"Pfosten {n}", geometry=rect(2.4 * col, row, 0.1, 1))
        started = time.perf_counter()

        try:
            report = run(service, csv(*[f"B{n};Beet;3;1" for n in range(250)]))
        except PlanError as exc:
            assert exc.error_code == "batch.too_complex"
        else:
            assert report.rows_valid == 0 and {e.code for e in report.errors} == {"csv.does_not_fit"}

        assert time.perf_counter() - started < 10.0

    def test_ignored_columns_are_listed_up_to_50_and_counted_exactly(self, service) -> None:
        header = HEADER + "".join(f";Extra{n}" for n in range(60))

        report = run(service, csv("A;Beet;1;1", header=header))

        assert len(report.ignored_columns) == 50 and report.ignored_columns_total == 60

    def test_a_header_of_more_than_100_columns_is_refused(self, service) -> None:
        header = HEADER + "".join(f";Extra{n}" for n in range(97))

        with pytest.raises(PlanError) as caught:
            run(service, csv("A;Beet;1;1", header=header))

        assert caught.value.status_code == 422 and caught.value.error_code == "csv.too_many_columns"


class TestTheSiteCheck:
    def test_check_site_answers_404_for_a_foreign_and_nothing_for_the_own_site(self, service) -> None:
        service.check_site(SITE, tenant_key=TENANT)  # the positive control

        with pytest.raises(NotFoundError):
            service.check_site(FOREIGN_SITE, tenant_key=TENANT)
