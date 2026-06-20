"""REQ-034 §2.1 / AC-08 — gallery cascade on plant-instance removal.

When a plant instance is removed, its gallery photos must be hard-deleted via
the injected ``photo_cleanup`` callback so no orphan storage bytes remain.
"""

from datetime import date
from unittest.mock import MagicMock

from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_instance_service import PlantInstanceService


def _plant(photo_refs: list[str]) -> PlantInstance:
    return PlantInstance(
        _key="plant-1",
        tenant_key="tenant_anna",
        instance_id="P-1",
        species_key="species1",
        planted_on=date(2026, 6, 1),
        photo_refs=list(photo_refs),
        cover_photo_ref=photo_refs[0] if photo_refs else None,
    )


def _service(plant: PlantInstance, cleanup):
    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant
    plant_repo.update.side_effect = lambda _key, p: p
    return PlantInstanceService(
        plant_repo,
        MagicMock(),
        MagicMock(),
        MagicMock(),
        photo_cleanup=cleanup,
    )


class TestPhotoCascadeOnRemove:
    def test_cleanup_invoked_and_refs_cleared(self):
        plant = _plant(["att1", "att2"])
        # Capture the refs *at call time* (the callback runs before they clear).
        seen: list[list[str]] = []
        service = _service(plant, lambda p: seen.append(list(p.photo_refs)))

        updated = service.remove_plant("plant-1")

        # Cleanup ran with the plant that still held the refs.
        assert seen == [["att1", "att2"]]
        # Refs are cleared after the cascade.
        assert updated.photo_refs == []
        assert updated.cover_photo_ref is None
        assert updated.removed_on == date.today()

    def test_no_cleanup_when_no_photos(self):
        plant = _plant([])
        cleanup = MagicMock()
        service = _service(plant, cleanup)

        service.remove_plant("plant-1")

        cleanup.assert_not_called()

    def test_no_cleanup_callback_is_noop(self):
        plant = _plant(["att1"])
        service = _service(plant, None)

        updated = service.remove_plant("plant-1")

        # No callback wired → photos are left untouched (still removable later).
        assert updated.removed_on == date.today()
