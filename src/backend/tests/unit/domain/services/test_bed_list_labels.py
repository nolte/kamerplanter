"""The one SR-024 mapping of a bed list (REQ-053 #2668, #2750): zone names, member names, the row bound."""

from __future__ import annotations

import pytest

from app.common.exceptions import PlanError
from app.domain.engines.print_engine import format_decimal, print_label
from app.domain.models.bed_list_export import MAX_BED_LIST_EXPORT_ROWS, BedAssignee
from app.domain.models.care_event import ANONYMIZED_MARKER
from app.domain.services.bed_list_labels import bed_assignee_names, irrigation_zone_names, require_bed_list_size
from tests.support.garden_plan_fakes import (
    OTHER_TENANT,
    SITE,
    TENANT,
    FakePlanRepo,
    FakeSites,
    make_location,
    make_site,
)


@pytest.fixture
def repo() -> FakePlanRepo:
    return FakePlanRepo(FakeSites(make_site()))


class TestBedAssigneeNames:
    def test_names_are_sorted_per_bed_and_never_keys(self, repo) -> None:
        repo.assignees = [
            (TENANT, BedAssignee("b1", "u_z", "zora")),
            (TENANT, BedAssignee("b1", "u_a", "Anna")),
            (TENANT, BedAssignee("b2", "u_k", "Karl")),
            (OTHER_TENANT, BedAssignee("b1", "u_m", "Mallory")),
        ]

        names = bed_assignee_names(repo, ["b1", "b2"], tenant_key=TENANT)

        assert names == {"b1": ["Anna", "zora"], "b2": ["Karl"]}

    @pytest.mark.parametrize("user_key, display_name", [("u_gone", None), (ANONYMIZED_MARKER, "Was Sabine")])
    def test_an_erased_account_takes_the_callers_label(self, repo, user_key, display_name) -> None:
        repo.assignees = [(TENANT, BedAssignee("b1", user_key, display_name))]

        assert bed_assignee_names(repo, ["b1"], tenant_key=TENANT) == {"b1": ["anonymisiert"]}
        assert bed_assignee_names(repo, ["b1"], tenant_key=TENANT, anonymised_label="anonymised") == {
            "b1": ["anonymised"]
        }

    def test_an_assignment_without_an_account_gives_no_name(self, repo) -> None:
        repo.assignees = [(TENANT, BedAssignee("b1", None, None))]

        assert bed_assignee_names(repo, ["b1"], tenant_key=TENANT) == {}

    def test_no_bed_reads_nothing(self, repo) -> None:
        assert bed_assignee_names(repo, [], tenant_key=TENANT) == {}
        assert repo.assignee_reads == []


class TestIrrigationZoneNames:
    def test_nothing_is_read_when_no_bed_names_a_zone(self, repo) -> None:
        assert irrigation_zone_names(repo, SITE, [make_location("b1")], tenant_key=TENANT) == {}
        assert "zone_names" not in repo.label_reads

    def test_the_tenants_zone_names(self, repo) -> None:
        beds = [make_location("b1", irrigation_zone_key="zone_1")]

        assert irrigation_zone_names(repo, SITE, beds, tenant_key=TENANT) == {"zone_1": "Tropf Ost"}
        assert irrigation_zone_names(repo, SITE, beds, tenant_key=OTHER_TENANT) == {}


class TestTheBound:
    def test_the_bound_itself_passes_and_one_more_is_refused(self) -> None:
        require_bed_list_size(MAX_BED_LIST_EXPORT_ROWS)

        with pytest.raises(PlanError) as refused:
            require_bed_list_size(MAX_BED_LIST_EXPORT_ROWS + 1)

        assert refused.value.status_code == 422
        assert refused.value.details[0]["code"] == "export.too_many_rows"


class TestPrintFormatting:
    @pytest.mark.parametrize("locale, expected", [("de", "2,5"), ("en", "2.5")])
    def test_a_decimal_follows_the_locale(self, locale, expected) -> None:
        assert format_decimal(2.5, locale) == expected

    def test_an_unknown_locale_takes_the_german_label(self) -> None:
        assert print_label("fr", "garden_plan_assignee_anonymised") == "anonymisiert"
        assert print_label("en", "garden_plan_assignee_anonymised") == "anonymised"
