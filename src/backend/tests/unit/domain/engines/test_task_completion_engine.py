"""REQ-053 WP 4.3 — which specialist document a task completion writes (§12.1) and which task is logged (GP-FR-083).

Pure functions, no database. The documents are asserted in the shape the readers of ``watering_events``,
``feeding_events`` and ``harvest_batches`` parse (the model round-trip), and the collection / edge names in the
domain layer are pinned against the persistence layer's.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.common.enums import TaskCategory
from app.common.exceptions import ValidationError
from app.data_access.arango import collections as col
from app.domain.engines import task_completion_engine as engine_module
from app.domain.engines.task_completion_engine import NUTRIENT_MATERIALS, TaskCompletionEngine
from app.domain.models.care_event import CareEvent
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.harvest import HarvestBatch
from app.domain.models.task import Task
from app.domain.models.watering_event import WateringEvent
from tests.support.care_event_fakes import FakeFertilizers

TENANT = "ten_own"
ENGINE = TaskCompletionEngine(FakeFertilizers())
WHEN = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)


def task(category: TaskCategory = TaskCategory.WATERING, **overrides) -> Task:
    data = {
        "_key": "t1",
        "tenant_key": TENANT,
        "name": "Bed 3",
        "category": category,
        "entity_type": "location",
        "entity_key": "bed",
    }
    return Task(**{**data, **overrides})


def event(category: str, **overrides) -> CareEvent:
    data = {
        "tenant_key": TENANT,
        "site_key": "site",
        "location_key": "bed",
        "category": category,
        "summary": "x",
        "performed_at": WHEN,
        "performed_by_user_key": "u1",
        "trigger": "task",
        "task_key": "t1",
    }
    return CareEvent(**{**data, **overrides})


class TestWhichTaskIsLogged:
    @pytest.mark.parametrize(
        ("entity_type", "logged"),
        [
            ("location", True),
            ("plant_instance", True),
            ("planting_run", False),
            ("garden_object", False),
            (None, False),
        ],
    )
    def test_only_a_bed_or_a_plant_is_a_bed_task(self, entity_type, logged):
        assert TaskCompletionEngine.logs_into_a_bed(task(entity_type=entity_type)) is logged

    def test_a_task_without_an_entity_key_is_not_logged(self):
        assert TaskCompletionEngine.logs_into_a_bed(task(entity_key=None)) is False

    def test_a_care_reminder_keeps_its_own_strand(self):
        # GP-FR-106: the reminder confirmation writes its own line; the completion must not write a second one.
        reminder = task(TaskCategory.CARE_REMINDER, entity_type="plant_instance", entity_key="pi")
        assert TaskCompletionEngine.logs_into_a_bed(reminder) is False
        assert TaskCompletionEngine.bed_entity(reminder) is None


class TestWatering:
    def test_litres_become_a_watering_event_on_the_plants(self):
        doc = ENGINE.domain_document(task(), event("watering", quantity=12, unit="l"), plant_keys=["p1", "p2"])

        assert doc is not None
        assert doc.collection == "watering_events"
        parsed = WateringEvent.model_validate(doc.document)
        assert (parsed.volume_liters, parsed.plant_keys, parsed.task_key, parsed.tenant_key) == (
            12.0,
            ["p1", "p2"],
            "t1",
            TENANT,
        )
        assert [(edge, to) for edge, to, _ in doc.edges_out] == [
            ("watered_plant", "plant_instances/p1"),
            ("watered_plant", "plant_instances/p2"),
        ]

    def test_millilitres_are_converted(self):
        doc = ENGINE.domain_document(task(), event("watering", quantity=500, unit="ml"), plant_keys=["p1"])
        assert doc is not None
        assert doc.document["volume_liters"] == 0.5

    def test_an_area_dose_takes_the_total_for_the_bed(self):
        # quantity × area_m2 is computed by the care-event service; the document takes that total (GP-ACC-024).
        doc = ENGINE.domain_document(
            task(),
            event("watering", quantity=4, unit="l_per_m2", quantity_total=10.0, quantity_total_unit="l"),
            plant_keys=["p1"],
        )
        assert doc is not None
        assert doc.document["volume_liters"] == 10.0

    @pytest.mark.parametrize(
        "overrides",
        [{}, {"quantity": 0, "unit": "l"}, {"quantity": 3, "unit": "cm"}, {"quantity": 3, "unit": "g"}],
    )
    def test_no_volume_means_the_care_event_alone(self, overrides):
        assert ENGINE.domain_document(task(), event("watering", **overrides), plant_keys=["p1"]) is None

    def test_a_bed_without_plants_has_nobody_to_water(self):
        assert ENGINE.domain_document(task(), event("watering", quantity=5, unit="l"), plant_keys=[]) is None


class TestFeeding:
    def test_an_area_dose_of_a_liquid_product_is_one_feeding_event(self):
        # GP-ACC-024: 2 l/m² of fertilizer X on plants p1, p2 → quantity_total = 2 × area_m2, ONE document.
        doc = ENGINE.domain_document(
            task(TaskCategory.FEEDING),
            event(
                "feeding",
                quantity=2,
                unit="l_per_m2",
                quantity_total=5.0,
                quantity_total_unit="l",
                product_ref={"kind": "fertilizer", "key": "fert_global"},
                plant_keys=["p1", "p2"],
            ),
            plant_keys=["p1", "p2"],
        )

        assert doc is not None
        assert doc.collection == "feeding_events"
        parsed = FeedingEvent.model_validate(doc.document)
        assert parsed.plant_key == "p1"
        assert parsed.plant_keys == ["p1", "p2"]
        assert parsed.volume_applied_liters == 5.0
        assert (parsed.quantity_total, parsed.quantity_total_unit) == (5.0, "l")
        assert (parsed.dose_quantity, parsed.dose_unit, parsed.product_key) == (2, "l_per_m2", "fert_global")
        assert [(line.fertilizer_key, line.ml_applied) for line in parsed.fertilizers_used] == [("fert_global", 5000.0)]
        assert [edge for edge, _, _ in doc.edges_in] == ["fed_by", "fed_by"]
        assert [(edge, to, attrs) for edge, to, attrs in doc.edges_out] == [
            ("feeding_used", "fertilizers/fert_global", {"ml_applied": 5000.0})
        ]

    @pytest.mark.parametrize("product", ["fert_foreign", "fert_unknown"])
    def test_a_product_the_tenant_cannot_see_is_refused_alike(self, product):
        # #1713: the document that stores a fertilizer key checks it, whatever the care-event service did before.
        with pytest.raises(ValidationError):
            ENGINE.domain_document(
                task(TaskCategory.FEEDING),
                event("feeding", quantity=1, unit="l", product_ref={"kind": "fertilizer", "key": product}),
                plant_keys=["p1"],
            )

    def test_an_engine_without_a_catalogue_refuses_a_product_rather_than_store_it_unchecked(self):
        with pytest.raises(RuntimeError, match="fertilizer repository"):
            TaskCompletionEngine().domain_document(
                task(TaskCategory.FEEDING),
                event("feeding", quantity=1, unit="l", product_ref={"kind": "fertilizer", "key": "fert_global"}),
                plant_keys=["p1"],
            )

    def test_a_dry_dose_has_no_volume_and_is_a_top_dress(self):
        doc = ENGINE.domain_document(
            task(TaskCategory.FEEDING),
            event("feeding", quantity=50, unit="g_per_m2", quantity_total=125.0, quantity_total_unit="g"),
            plant_keys=[],
        )

        assert doc is not None
        parsed = FeedingEvent.model_validate(doc.document)
        assert parsed.volume_applied_liters is None
        assert parsed.application_method.value == "top_dress"
        assert parsed.plant_key == ""  # the whole bed, no first plant
        assert parsed.quantity_total == 125.0
        assert doc.edges_in == () and doc.edges_out == ()

    def test_a_feeding_without_a_quantity_is_the_care_event_alone(self):
        assert ENGINE.domain_document(task(TaskCategory.FEEDING), event("feeding"), plant_keys=["p"]) is None

    @pytest.mark.parametrize("material", sorted(NUTRIENT_MATERIALS))
    def test_a_soil_amendment_with_a_nutrient_material_also_feeds(self, material):
        # W-007: the fertiliser balance (GP-FR-125) must see compost, manure and horn shavings.
        doc = ENGINE.domain_document(
            task(TaskCategory.SOIL_AMENDMENT),
            event("soil_amendment", material=material, quantity=3, unit="kg"),
            plant_keys=[],
        )
        assert doc is not None and doc.collection == "feeding_events"
        assert FeedingEvent.model_validate(doc.document).material == material

    def test_a_soil_amendment_without_a_nutrient_effect_is_the_care_event_alone(self):
        assert (
            ENGINE.domain_document(
                task(TaskCategory.SOIL_AMENDMENT),
                event("soil_amendment", material="sand", quantity=3, unit="kg"),
                plant_keys=[],
            )
            is None
        )


class TestHarvest:
    def test_one_plant_gets_its_own_batch_with_the_weight(self):
        doc = ENGINE.domain_document(
            task(TaskCategory.HARVEST), event("harvest", quantity=1.5, unit="kg"), plant_keys=["p1"]
        )

        assert doc is not None and doc.collection == "harvest_batches"
        parsed = HarvestBatch.model_validate(doc.document)
        assert (parsed.plant_key, parsed.wet_weight_g, parsed.harvested_by_key) == ("p1", 1500.0, "u1")
        assert parsed.harvest_type.value == "partial"
        assert [(edge, frm) for edge, frm, _ in doc.edges_in] == [("harvested_as", "plant_instances/p1")]

    def test_several_plants_make_a_bed_level_batch(self):
        doc = ENGINE.domain_document(
            task(TaskCategory.HARVEST), event("harvest", quantity=300, unit="g"), plant_keys=["p1", "p2"]
        )

        assert doc is not None
        assert doc.document["plant_key"] == ""
        assert doc.edges_in == ()

    def test_a_harvest_without_a_weight_still_records_the_batch(self):
        doc = ENGINE.domain_document(task(TaskCategory.HARVEST), event("harvest"), plant_keys=[])

        assert doc is not None
        assert "wet_weight_g" not in doc.document


@pytest.mark.parametrize(
    "category",
    ["mulching", "weeding", "pruning", "pest_control", "ipm", "flush", "observation", "sowing", "liming"],
)
def test_a_category_without_a_specialist_document_writes_the_care_event_alone(category):
    # pest_control / ipm: the PflSchG section 11 proof stays the treatment_applications row (REQ-053 v1.6).
    assert ENGINE.domain_document(task(), event(category, quantity=2, unit="kg"), plant_keys=["p"]) is None


def test_the_domain_layer_spells_the_persistence_names_the_same():
    assert engine_module.WATERING_EVENTS == col.WATERING_EVENTS
    assert engine_module.FEEDING_EVENTS == col.FEEDING_EVENTS
    assert engine_module.HARVEST_BATCHES == col.HARVEST_BATCHES
    assert engine_module.PLANT_INSTANCES == col.PLANT_INSTANCES
    assert engine_module.FERTILIZERS == col.FERTILIZERS
    assert engine_module.WATERED_PLANT == col.WATERED_PLANT
    assert engine_module.FED_BY == col.FED_BY
    assert engine_module.FEEDING_USED == col.FEEDING_USED
    assert engine_module.HARVESTED_AS == col.HARVESTED_AS
