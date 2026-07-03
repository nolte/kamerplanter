"""REQ-013 GAP-B9 — partial entry update must not overwrite fields with placeholders.

Service-level tests for ``PlantingRunService.update_entry``. The run repository is
doubled with MagicMock (an owned I/O boundary); assertions target the merged entry
handed to ``repo.update_entry`` and the error behaviour for nulled required fields.
"""

from unittest.mock import MagicMock

import pytest

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.common.exceptions import InvalidRunStateError, ValidationError
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.services.planting_run_service import PlantingRunService

RUN_KEY = "r1"
ENTRY_KEY = "e1"


def _run(status: PlantingRunStatus = PlantingRunStatus.PLANNED) -> PlantingRun:
    return PlantingRun(_key=RUN_KEY, name="Tomato batch", run_type=PlantingRunType.MONOCULTURE, status=status)


def _entry(**overrides) -> PlantingRunEntry:
    data = {
        "_key": ENTRY_KEY,
        "run_key": RUN_KEY,
        "species_key": "species_tomato",
        "quantity": 3,
        "id_prefix": "TO",
    }
    data.update(overrides)
    return PlantingRunEntry(**data)


def _service(existing: PlantingRunEntry, run: PlantingRun | None = None):
    """Build a service whose repo echoes back the merged entry from update_entry."""
    run = run or _run()
    repo = MagicMock()
    repo.get_by_key.return_value = run
    repo.get_entry_by_key.return_value = existing

    captured: dict[str, PlantingRunEntry] = {}

    def _update_entry(entry_key, entry):
        captured["merged"] = entry
        return entry

    repo.update_entry.side_effect = _update_entry
    repo.get_entries.side_effect = lambda _key: [captured.get("merged", existing)]
    repo.update.side_effect = lambda _key, r: r

    service = PlantingRunService(run_repo=repo, plant_repo=MagicMock(), engine=MagicMock())
    return service, repo, captured


class TestPartialEntryUpdate:
    def test_partial_quantity_update_preserves_species(self):
        service, repo, captured = _service(_entry(quantity=3))

        updated = service.update_entry(RUN_KEY, ENTRY_KEY, {"quantity": 5})

        assert updated.species_key == "species_tomato"
        assert updated.quantity == 5
        assert captured["merged"].id_prefix == "TO"
        # planned_quantity resummed from the (single) merged entry.
        persisted_run = repo.update.call_args.args[1]
        assert persisted_run.planned_quantity == 5

    def test_partial_update_never_writes_placeholder(self):
        service, repo, captured = _service(_entry())

        service.update_entry(RUN_KEY, ENTRY_KEY, {"notes": "watered"})

        merged = captured["merged"]
        assert merged.species_key == "species_tomato"
        assert merged.species_key != "placeholder"
        assert merged.id_prefix == "TO"
        assert merged.id_prefix != "XX"
        assert merged.quantity == 3
        assert merged.notes == "watered"

    def test_explicit_null_clears_notes(self):
        service, _repo, captured = _service(_entry(notes="old note"))

        updated = service.update_entry(RUN_KEY, ENTRY_KEY, {"notes": None})

        assert updated.notes is None
        assert captured["merged"].notes is None

    def test_explicit_null_clears_cultivar(self):
        service, _repo, captured = _service(_entry(cultivar_key="cultivar_roma"))

        updated = service.update_entry(RUN_KEY, ENTRY_KEY, {"cultivar_key": None})

        assert updated.cultivar_key is None
        assert captured["merged"].cultivar_key is None

    def test_null_required_species_raises_422(self):
        service, repo, _ = _service(_entry())

        with pytest.raises(ValidationError) as exc:
            service.update_entry(RUN_KEY, ENTRY_KEY, {"species_key": None})

        assert exc.value.status_code == 422
        assert "species_key" in exc.value.message
        repo.update_entry.assert_not_called()

    def test_null_required_quantity_raises_422(self):
        service, repo, _ = _service(_entry())

        with pytest.raises(ValidationError) as exc:
            service.update_entry(RUN_KEY, ENTRY_KEY, {"quantity": None})

        assert exc.value.status_code == 422
        repo.update_entry.assert_not_called()

    def test_invalid_id_prefix_rejected(self):
        from pydantic import ValidationError as PydanticValidationError

        service, _repo, _ = _service(_entry())

        with pytest.raises(PydanticValidationError):
            service.update_entry(RUN_KEY, ENTRY_KEY, {"id_prefix": "xx"})

    def test_species_change_is_merged(self):
        service, _repo, captured = _service(_entry(species_key="species_tomato"))

        updated = service.update_entry(RUN_KEY, ENTRY_KEY, {"species_key": "species_basil"})

        assert updated.species_key == "species_basil"
        assert captured["merged"].quantity == 3  # untouched

    def test_update_entry_rejected_when_run_active(self):
        service, repo, _ = _service(_entry(), run=_run(PlantingRunStatus.ACTIVE))

        with pytest.raises(InvalidRunStateError):
            service.update_entry(RUN_KEY, ENTRY_KEY, {"quantity": 5})

        repo.update_entry.assert_not_called()

    def test_unknown_field_is_ignored(self):
        service, _repo, captured = _service(_entry())

        # ``run_key`` is not in ENTRY_UPDATABLE_FIELDS and must be dropped.
        service.update_entry(RUN_KEY, ENTRY_KEY, {"run_key": "other-run", "quantity": 7})

        assert captured["merged"].run_key == RUN_KEY
        assert captured["merged"].quantity == 7
