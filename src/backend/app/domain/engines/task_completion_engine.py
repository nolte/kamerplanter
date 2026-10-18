"""What a task completion writes besides the task (REQ-053 §12.1, §12.3, GP-FR-083; WP 4.3).

Pure rules; the one read is the fertilizer-visibility check of the product a feeding document references (#1713):
the care-event service has resolved the product already, and the document that stores it checks again, so no writer
of a fertilizer reference depends on a check made elsewhere.

Two decisions live here, both as pure functions so they are testable without a database:

* **Which task is a bed task** (:meth:`TaskCompletionEngine.bed_location_key`) — the one whose completion is logged
  in the care log. ``entity_type = location`` is the bed itself; a ``plant_instance`` is logged in the bed it
  stands in. A ``care_reminder`` task is the reminder strand's (GP-FR-106) and keeps its own path.
* **Which specialist document the completion writes** (:meth:`TaskCompletionEngine.domain_document`) — §12.1's
  "Fachereignis bei Erledigung": ``watering_events`` for ``watering``, ``feeding_events`` for ``feeding`` and for a
  ``soil_amendment`` with a nutrient material, ``harvest_batches`` for ``harvest``. The care event carries the dose
  as the client typed it and, for an area dose (``l_per_m2``, ``g_per_m2``), the total for the bed
  (``quantity × area_m2``, computed by the care-event service); the specialist document takes that total.

A category without a specialist document in §12.1 (mulching, weeding, pruning, …) writes the care event alone.
``pest_control`` / ``ipm`` write the care event alone as well: the PflSchG section 11 proof is the
``treatment_applications`` row with its resistance and Karenz checks, which stays the IPM endpoint's (REQ-053
§13.2, v1.6).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.common.enums import ApplicationMethod, HarvestType, TaskCategory, WaterSource
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.models.care_event import CareEvent
from app.domain.models.feeding_event import FeedingEvent, FeedingEventFertilizer
from app.domain.models.harvest import HarvestBatch
from app.domain.models.task import Task
from app.domain.models.task_completion import DomainDocument
from app.domain.models.watering_event import WateringEvent
from app.domain.services.fertilizer_references import assert_fertilizers_visible

#: §12.1: materials with a nutrient effect; a ``soil_amendment`` with one of them also writes a ``feeding_event``
#: so the fertiliser balance (GP-FR-125) sees it (W-007).
NUTRIENT_MATERIALS: frozenset[str] = frozenset({"compost", "manure", "horn_shavings"})

#: The collection and edge names the documents are written into (``data_access/arango/collections.py`` spells the
#: same strings; ``tests/unit/domain/engines/test_task_completion_engine.py`` pins that they agree).
WATERING_EVENTS = "watering_events"
FEEDING_EVENTS = "feeding_events"
HARVEST_BATCHES = "harvest_batches"
PLANT_INSTANCES = "plant_instances"
FERTILIZERS = "fertilizers"
WATERED_PLANT = "watered_plant"
FED_BY = "fed_by"
FEEDING_USED = "feeding_used"
HARVESTED_AS = "harvested_as"

_LITRE_UNITS = {"l": 1.0, "ml": 0.001}
_DRY_UNITS = {"g": 1.0, "kg": 1000.0, "g_per_m2": 1.0}
_AREA_UNITS = ("l_per_m2", "g_per_m2")

#: Entity types a bed task can be bound to: the bed itself, or a plant standing in one.
_BED_ENTITY = "location"
_PLANT_ENTITY = "plant_instance"


def _doc_id(collection: str, key: str) -> str:
    return f"{collection}/{key}"


def _liters(event: CareEvent) -> float | None:
    """The liquid volume of the dose in litres, or ``None`` for a dry or absent dose."""
    if event.quantity is None or event.unit is None:
        return None
    if event.unit == "l_per_m2":
        return event.quantity_total if event.quantity_total_unit == "l" else None
    factor = _LITRE_UNITS.get(event.unit)
    return round(event.quantity * factor, 6) if factor is not None else None


def _grams(event: CareEvent) -> float | None:
    """The dry mass of the dose in grams, or ``None`` for a liquid or absent dose."""
    if event.quantity is None or event.unit is None:
        return None
    if event.unit == "g_per_m2":
        return event.quantity_total if event.quantity_total_unit == "g" else None
    factor = _DRY_UNITS.get(event.unit)
    return round(event.quantity * factor, 6) if factor is not None else None


def _dump(model: Any) -> dict[str, Any]:
    document: dict[str, Any] = model.model_dump(by_alias=True, exclude_none=True, mode="json")
    document.pop("_key", None)
    return document


class TaskCompletionEngine:
    """The rules of the completion transition.

    ``fertilizers`` is the catalogue read behind the visibility check of a feeding document's product; an engine
    built without it refuses a feeding that references one (fail closed, :func:`assert_fertilizers_visible`).
    """

    def __init__(self, fertilizers: IFertilizerRepository | None = None) -> None:
        self._fertilizers = fertilizers

    # ── Bed context ──────────────────────────────────────────────────────────

    @staticmethod
    def logs_into_a_bed(task: Task) -> bool:
        """Whether the completion of ``task`` is a care-log line at all (a reminder task is not, GP-FR-106)."""
        if task.category == TaskCategory.CARE_REMINDER:
            return False
        return task.entity_type in (_BED_ENTITY, _PLANT_ENTITY) and bool(task.entity_key)

    @staticmethod
    def bed_entity(task: Task) -> tuple[str, str] | None:
        """``(entity_type, entity_key)`` the bed is resolved from, or ``None`` for a task outside the care log."""
        if not TaskCompletionEngine.logs_into_a_bed(task):
            return None
        return task.entity_type or "", task.entity_key or ""

    # ── Specialist document ──────────────────────────────────────────────────

    @staticmethod
    def wants_feeding_event(event: CareEvent) -> bool:
        if event.quantity is None:
            return False
        if event.category == TaskCategory.FEEDING.value:
            return True
        return event.category == TaskCategory.SOIL_AMENDMENT.value and (event.material or "") in NUTRIENT_MATERIALS

    def domain_document(
        self,
        task: Task,
        event: CareEvent,
        *,
        plant_keys: list[str],
        now: datetime | None = None,
    ) -> DomainDocument | None:
        """The specialist document ``event`` is the log line of, or ``None`` when its category has none.

        ``plant_keys`` are the plants the dose is attributed to: the event's own, or — for an event on the whole
        bed — the plants standing in the bed (a whole-bed dose is every plant's, and a plant's history finds it).
        """
        stamp = (now or datetime.now(UTC)).isoformat()
        category = event.category
        if category == TaskCategory.WATERING.value:
            return self._watering(task, event, plant_keys, stamp)
        if self.wants_feeding_event(event):
            return self._feeding(task, event, plant_keys, stamp)
        if category == TaskCategory.HARVEST.value:
            return self._harvest(event, plant_keys, stamp)
        return None

    @staticmethod
    def _watering(task: Task, event: CareEvent, plant_keys: list[str], stamp: str) -> DomainDocument | None:
        litres = _liters(event)
        if litres is None or litres <= 0 or not plant_keys:
            return None  # a watering event is a volume on plants; a bare "gegossen" is the care event alone
        watering = WateringEvent(
            tenant_key=event.tenant_key,
            watered_at=event.performed_at,
            application_method=ApplicationMethod.DRENCH,
            volume_liters=litres,
            plant_keys=list(plant_keys),
            water_source=None if event.material is None else _water_source(event.material),
            task_key=task.key,
        )
        document = _dump(watering)
        document["created_at"] = stamp
        return DomainDocument(
            collection=WATERING_EVENTS,
            document=document,
            edges_out=tuple((WATERED_PLANT, _doc_id(PLANT_INSTANCES, key), {}) for key in plant_keys),
        )

    def _feeding(self, task: Task, event: CareEvent, plant_keys: list[str], stamp: str) -> DomainDocument:
        # What a dose means (the GP-FR-100 reading: ``quantity`` is the amount of the *product*):
        #   * ``l`` / ``l_per_m2`` of a feeding — the applied liquid (the nettle tea of GP-ACC-024): its litres are
        #     the applied volume and the product's ``ml_applied`` at once;
        #   * ``ml`` of a feeding — the amount of concentrate; the water it was diluted in is unknown, so no volume;
        #   * everything dry (``g`` / ``kg`` / ``g_per_m2``) and every soil amendment (compost "2 l" is a bulk
        #     volume, not a drench) — no volume, a top dress with the dose in the dose fields.
        is_feeding = event.category == TaskCategory.FEEDING.value
        product_litres = _liters(event) if is_feeding else None
        litres = product_litres if event.unit in ("l", "l_per_m2") else None
        product_ml = product_litres * 1000 if product_litres is not None else None
        product_key = str(event.product_ref["key"]) if event.product_ref and event.product_ref.get("key") else None
        assert_fertilizers_visible(
            self._fertilizers,
            [product_key],
            tenant_key=event.tenant_key,
            field="product_ref",
            owner="TaskCompletionEngine",
        )
        used: list[FeedingEventFertilizer] = []
        if product_key and product_ml is not None and product_ml > 0:
            used.append(FeedingEventFertilizer(fertilizer_key=product_key, ml_applied=round(product_ml, 3)))
        feeding = FeedingEvent(
            tenant_key=event.tenant_key,
            plant_key=plant_keys[0] if plant_keys else "",
            timestamp=event.performed_at,
            application_method=ApplicationMethod.DRENCH if product_ml is not None else ApplicationMethod.TOP_DRESS,
            volume_applied_liters=litres if litres is not None and litres > 0 else None,
            fertilizers_used=used,
            location_key=event.location_key,
            plant_keys=list(plant_keys),
            task_key=task.key,
            product_key=product_key,
            material=event.material,
            dose_quantity=event.quantity,
            dose_unit=event.unit,
            quantity_total=event.quantity_total,
            quantity_total_unit=event.quantity_total_unit,
        )
        document = _dump(feeding)
        document["created_at"] = stamp
        document["updated_at"] = stamp
        return DomainDocument(
            collection=FEEDING_EVENTS,
            document=document,
            edges_out=tuple(
                (FEEDING_USED, _doc_id(FERTILIZERS, line.fertilizer_key), {"ml_applied": line.ml_applied})
                for line in used
            ),
            edges_in=tuple((FED_BY, _doc_id(PLANT_INSTANCES, key), {}) for key in plant_keys),
        )

    @staticmethod
    def _harvest(event: CareEvent, plant_keys: list[str], stamp: str) -> DomainDocument:
        grams = _grams(event)
        # One plant: the batch is that plant's (and the Karenz gate, the CanG record and the yield walk find it).
        # Several or the whole bed: a bed-level batch, ``plant_key`` empty — the care event names the plants.
        plant_key = plant_keys[0] if len(plant_keys) == 1 else ""
        batch = HarvestBatch(
            tenant_key=event.tenant_key,
            plant_key=plant_key,
            harvest_date=event.performed_at,
            # A task completion does not end the plant's life; a final harvest is recorded through the harvest form.
            harvest_type=HarvestType.PARTIAL,
            wet_weight_g=grams,
            harvested_by_key=event.performed_by_user_key,
        )
        document = _dump(batch)
        document["created_at"] = stamp
        document["updated_at"] = stamp
        return DomainDocument(
            collection=HARVEST_BATCHES,
            document=document,
            edges_in=((HARVESTED_AS, _doc_id(PLANT_INSTANCES, plant_key), {}),) if plant_key else (),
        )


def _water_source(material: str) -> WaterSource | None:
    """``material`` of a watering task names the source when it is one of the known ones, else it is not a source."""
    try:
        return WaterSource(material)
    except ValueError:
        return None
