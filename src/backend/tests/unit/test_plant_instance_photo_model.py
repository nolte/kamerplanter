"""REQ-034 §2.1 — PlantInstance gallery fields."""

from datetime import date

from app.domain.models.plant_instance import PlantInstance


def _plant(**overrides) -> PlantInstance:
    base = {
        "instance_id": "P-1",
        "species_key": "species1",
        "planted_on": date(2026, 6, 1),
    }
    base.update(overrides)
    return PlantInstance(**base)


def test_photo_fields_default_empty():
    plant = _plant()
    assert plant.photo_refs == []
    assert plant.cover_photo_ref is None


def test_photo_refs_independent_per_instance():
    # default_factory must not share the list across instances.
    a = _plant()
    a.photo_refs.append("att1")
    b = _plant()
    assert b.photo_refs == []


def test_photo_fields_roundtrip_alias():
    plant = _plant(photo_refs=["att1", "att2"], cover_photo_ref="att2")
    dumped = plant.model_dump(by_alias=True)
    assert dumped["photo_refs"] == ["att1", "att2"]
    assert dumped["cover_photo_ref"] == "att2"
    restored = PlantInstance(**dumped)
    assert restored.photo_refs == ["att1", "att2"]
    assert restored.cover_photo_ref == "att2"
