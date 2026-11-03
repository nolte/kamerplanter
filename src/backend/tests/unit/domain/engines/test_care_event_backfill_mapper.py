"""The M4 backfill mapper (REQ-053 GP-FR-105, WP 8.1, #2644): which bed, which tenant, which event.

Pure rules. Every rule has a counter-case that flips it, so a mapper that ignored the rule fails the pair.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.engines.care_event_backfill_mapper import (
    CATEGORIES,
    FEEDING_EVENTS,
    HARVEST_BATCHES,
    SOURCE_COLLECTIONS,
    TIME_FIELDS,
    TREATMENT_APPLICATIONS,
    WATERING_EVENTS,
    BedAnchor,
    SkipReason,
    account_of,
    map_document,
    performed_at_of,
    resolve_anchor,
    window_start,
)
from app.domain.models.care_event import CARE_EVENT_CATEGORIES
from app.domain.services.retention_service import RetentionService

T1, T2 = "t1", "t2"
WHEN = datetime(2025, 6, 1, 8, 30, tzinfo=UTC)


def _location(key: str = "L1", *, site_tenant: str | None = T1, found: bool = True, site_found: bool = True) -> dict:
    return {
        "key": key,
        "found": found,
        "site_key": "S1",
        "site_found": site_found,
        "site_tenant": site_tenant,
    }


def _ref(ref: str, kind: str | None = "plant", location_key: str | None = "L1", plant_tenant: str | None = T1) -> dict:
    return {"ref": ref, "kind": kind, "location_key": location_key, "plant_tenant": plant_tenant}


def _row(doc: dict | None = None, refs: list[dict] | None = None, locations: list[dict] | None = None, **extra) -> dict:
    return {
        "doc": {"_key": "d1", "tenant_key": T1} | (doc or {}),
        "refs": [_ref("p1")] if refs is None else refs,
        "own_location_key": extra.pop("own_location_key", None),
        "locations": [_location()] if locations is None else locations,
        "present": False,
    }


class TestResolveAnchor:
    def test_a_plant_in_a_bed_of_the_same_tenant_resolves_with_the_site_and_the_tenant_of_the_bed(self) -> None:
        anchor = resolve_anchor(_row())

        assert anchor == BedAnchor(tenant_key=T1, site_key="S1", location_key="L1", plant_keys=("p1",))

    def test_the_tenant_is_the_beds_site_not_the_stamp_of_the_document(self) -> None:
        # counter-case of the rule: the document says t2, the bed's site says t1 -> never written
        assert resolve_anchor(_row(doc={"tenant_key": T2})) is SkipReason.TENANT_MISMATCH
        # and the same document under the matching stamp resolves, so the first result is the tenant rule
        assert isinstance(resolve_anchor(_row(doc={"tenant_key": T1})), BedAnchor)

    def test_a_document_without_a_tenant_is_never_written(self) -> None:
        assert resolve_anchor(_row(doc={"tenant_key": ""})) is SkipReason.TENANT_MISMATCH
        assert resolve_anchor(_row(doc={"tenant_key": None})) is SkipReason.TENANT_MISMATCH

    def test_a_plant_of_another_tenant_blocks_the_document(self) -> None:
        row = _row(refs=[_ref("p1"), _ref("p2", plant_tenant=T2)])

        assert resolve_anchor(row) is SkipReason.TENANT_MISMATCH

    def test_a_site_without_a_tenant_is_a_reason_of_its_own(self) -> None:
        for tenant in (None, ""):
            assert resolve_anchor(_row(locations=[_location(site_tenant=tenant)])) is SkipReason.SITE_WITHOUT_TENANT

    def test_no_reference_at_all_is_counted_not_resolved(self) -> None:
        assert resolve_anchor(_row(refs=[], locations=[])) is SkipReason.NO_REFERENCE

    def test_a_reference_that_points_at_nothing_is_unresolved(self) -> None:
        row = _row(refs=[_ref("p1", kind=None, location_key=None, plant_tenant=None)], locations=[])

        assert resolve_anchor(row) is SkipReason.UNRESOLVED

    def test_a_plant_without_a_bed_is_unresolved(self) -> None:
        row = _row(refs=[_ref("p1", location_key=None)], locations=[])

        assert resolve_anchor(row) is SkipReason.UNRESOLVED

    def test_one_resolved_and_one_unresolved_reference_is_never_guessed(self) -> None:
        row = _row(refs=[_ref("p1"), _ref("p2", kind=None, location_key=None)])

        assert resolve_anchor(row) is SkipReason.PARTLY_UNRESOLVED

    def test_two_beds_are_not_split_into_one_source_ref(self) -> None:
        row = _row(refs=[_ref("p1"), _ref("p2", location_key="L2")], locations=[_location("L1"), _location("L2")])

        assert resolve_anchor(row) is SkipReason.MULTIPLE_BEDS

    def test_a_missing_location_or_site_is_unresolved(self) -> None:
        assert resolve_anchor(_row(locations=[_location(found=False)])) is SkipReason.UNRESOLVED
        assert resolve_anchor(_row(locations=[_location(site_found=False)])) is SkipReason.UNRESOLVED

    def test_a_slot_reference_names_the_bed_and_no_plant(self) -> None:
        anchor = resolve_anchor(_row(refs=[_ref("s1", kind="slot")]))

        assert isinstance(anchor, BedAnchor)
        assert anchor.plant_keys == ()

    def test_the_own_location_of_the_document_is_enough_on_its_own(self) -> None:
        anchor = resolve_anchor(_row(refs=[], own_location_key="L1"))

        assert isinstance(anchor, BedAnchor)
        assert anchor.location_key == "L1"

    def test_an_own_location_that_disagrees_with_the_plants_bed_is_two_beds(self) -> None:
        row = _row(own_location_key="L9", locations=[_location("L1"), _location("L9")])

        assert resolve_anchor(row) is SkipReason.MULTIPLE_BEDS

    def test_plant_keys_are_sorted_and_unique(self) -> None:
        anchor = resolve_anchor(_row(refs=[_ref("p2"), _ref("p1"), _ref("p2")]))

        assert isinstance(anchor, BedAnchor)
        assert anchor.plant_keys == ("p1", "p2")


class TestWindow:
    def test_window_start_is_the_expression_of_the_retention_sweep(self) -> None:
        """Pinned against the production sweep: an event inside this window is never anonymised right away."""
        service = RetentionService.__new__(RetentionService)
        service._care_event_retention_years = 5
        for now in (
            datetime(2026, 11, 3, 12, 0, 0, 999, tzinfo=UTC),
            datetime(2028, 2, 29, 23, 59, 59, tzinfo=UTC),  # 29 February lands on 28 February
            datetime(2026, 1, 1, tzinfo=UTC),
        ):
            assert window_start(now, 5) == service.care_event_anonymisation_cutoff(now)

    def test_window_start_is_five_calendar_years_back_not_365_times_five_days(self) -> None:
        now = datetime(2026, 11, 3, tzinfo=UTC)

        assert window_start(now, 5) == datetime(2021, 11, 3, tzinfo=UTC)
        assert window_start(now, 5) != now - timedelta(days=5 * 365)

    @pytest.mark.parametrize("collection", SOURCE_COLLECTIONS)
    def test_every_source_reads_its_own_time_field(self, collection: str) -> None:
        field = TIME_FIELDS[collection]

        assert performed_at_of({field: "2025-06-01T08:30:00+00:00"}, collection) == WHEN
        # the time field of another source is not this source's instant
        other = next(f for f in TIME_FIELDS.values() if f != field)
        assert performed_at_of({other: "2025-06-01T08:30:00+00:00"}, collection) is None

    def test_a_naive_instant_is_read_as_utc_and_an_offset_is_normalised(self) -> None:
        assert performed_at_of({"watered_at": "2025-06-01T08:30:00"}, WATERING_EVENTS) == WHEN
        assert performed_at_of({"watered_at": "2025-06-01T10:30:00+02:00"}, WATERING_EVENTS) == WHEN

    @pytest.mark.parametrize("raw", [None, "", "   ", "not a date", 17])
    def test_an_unreadable_instant_is_none(self, raw: object) -> None:
        assert performed_at_of({"watered_at": raw}, WATERING_EVENTS) is None


class TestAccount:
    def test_only_an_account_reference_names_the_performer(self) -> None:
        assert account_of({"applied_by_key": "u1", "applied_by": "Anna Beispiel"}, TREATMENT_APPLICATIONS) == "u1"
        assert account_of({"harvested_by_key": "u2", "harvester": "Bob"}, HARVEST_BATCHES) == "u2"

    def test_a_display_text_is_not_an_account(self) -> None:
        assert account_of({"applied_by": "Anna Beispiel"}, TREATMENT_APPLICATIONS) is None
        assert account_of({"harvester": "Bob"}, HARVEST_BATCHES) is None
        # watering and feeding have no account reference; their free-text ``performed_by`` is not one
        assert account_of({"performed_by": "u1"}, WATERING_EVENTS) is None
        assert account_of({"performed_by": "u1"}, FEEDING_EVENTS) is None

    @pytest.mark.parametrize("raw", [None, "", "  "])
    def test_a_blank_account_reference_is_none(self, raw: object) -> None:
        assert account_of({"applied_by_key": raw}, TREATMENT_APPLICATIONS) is None


class TestMapDocument:
    ANCHOR = BedAnchor(tenant_key=T1, site_key="S1", location_key="L1", plant_keys=("p1",))

    def test_every_event_is_a_backfill_that_names_its_source(self) -> None:
        event = map_document(
            WATERING_EVENTS,
            {"_key": "w1", "watered_at": "2025-06-01T08:30:00+00:00", "volume_liters": 2.5},
            self.ANCHOR,
            WHEN,
        )

        assert event.trigger == "backfill"
        assert event.source_ref == {"collection": "watering_events", "key": "w1"}
        assert (event.tenant_key, event.site_key, event.location_key) == (T1, "S1", "L1")
        assert event.plant_keys == ["p1"]
        assert event.performed_at == WHEN
        assert event.created_by is None
        assert event.performed_by_user_key is None

    def test_the_categories_exist_and_a_treatment_keeps_the_pflschg_category(self) -> None:
        assert set(CATEGORIES.values()) <= CARE_EVENT_CATEGORIES
        assert CATEGORIES[TREATMENT_APPLICATIONS] == "pest_control"

    def test_a_watering_carries_its_volume_in_litres(self) -> None:
        event = map_document(WATERING_EVENTS, {"_key": "w1", "volume_liters": 2.5}, self.ANCHOR, WHEN)

        assert (event.category, event.quantity, event.unit) == ("watering", 2.5, "l")

    def test_a_feeding_prefers_the_dose_it_states_then_the_applied_volume(self) -> None:
        dosed = map_document(
            FEEDING_EVENTS,
            {
                "_key": "f1",
                "dose_quantity": 30,
                "dose_unit": "g_per_m2",
                "quantity_total": 60,
                "quantity_total_unit": "g",
            },
            self.ANCHOR,
            WHEN,
        )
        volume = map_document(FEEDING_EVENTS, {"_key": "f2", "volume_applied_liters": 1.5}, self.ANCHOR, WHEN)

        assert (dosed.quantity, dosed.unit, dosed.quantity_total, dosed.quantity_total_unit) == (
            30,
            "g_per_m2",
            60,
            "g",
        )
        assert (volume.quantity, volume.unit) == (1.5, "l")

    def test_an_unknown_dose_unit_is_dropped_not_converted(self) -> None:
        event = map_document(
            FEEDING_EVENTS, {"_key": "f1", "dose_quantity": 3, "dose_unit": "tablespoon"}, self.ANCHOR, WHEN
        )

        assert (event.quantity, event.unit) == (None, None)

    def test_a_treatment_dosage_has_no_unit_so_the_event_has_no_quantity(self) -> None:
        """E-10: a number without a unit is not a quantity; nothing is invented."""
        event = map_document(
            TREATMENT_APPLICATIONS, {"_key": "t1", "dosage": 5.0, "water_volume_liters": 10.0}, self.ANCHOR, WHEN
        )

        assert (event.quantity, event.unit) == (None, None)

    def test_a_harvest_carries_the_wet_weight_in_grams(self) -> None:
        event = map_document(HARVEST_BATCHES, {"_key": "h1", "wet_weight_g": 120.5}, self.ANCHOR, WHEN)

        assert (event.category, event.quantity, event.unit) == ("harvest", 120.5, "g")

    def test_free_text_of_the_source_is_never_copied(self) -> None:
        event = map_document(
            TREATMENT_APPLICATIONS,
            {"_key": "t1", "notes": "Anna Beispiel, Tel. 0123", "applied_by": "Anna Beispiel"},
            self.ANCHOR,
            WHEN,
        )

        dumped = event.model_dump_json()
        assert "Anna" not in dumped and "0123" not in dumped

    def test_the_account_reference_becomes_the_performer(self) -> None:
        event = map_document(HARVEST_BATCHES, {"_key": "h1", "harvested_by_key": "u7"}, self.ANCHOR, WHEN)

        assert event.performed_by_user_key == "u7"

    def test_a_document_without_a_key_cannot_be_referenced(self) -> None:
        with pytest.raises(ValueError, match="source_ref"):
            map_document(WATERING_EVENTS, {"volume_liters": 1.0}, self.ANCHOR, WHEN)
