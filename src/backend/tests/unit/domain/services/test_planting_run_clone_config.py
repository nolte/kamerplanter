"""REQ-013 §2 (Z.160) — clone_from_run_key copies configuration, not plants."""

from unittest.mock import MagicMock

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.services.planting_run_service import PlantingRunService
from tests.conftest import wire_get_or_raise

TEMPLATE_KEY = "run_template"
TENANT = "tenant_lisa"


def _template_run() -> PlantingRun:
    return PlantingRun(
        _key=TEMPLATE_KEY,
        tenant_key=TENANT,
        name="Salat 2025",
        run_type=PlantingRunType.MONOCULTURE,
        status=PlantingRunStatus.COMPLETED,
        location_key="loc_beet_c",
        substrate_batch_key="batch_1",
        lifecycle_config_key="lc_lettuce",
        nutrient_plan_key="plan_lettuce",
    )


def _template_entries() -> list[PlantingRunEntry]:
    return [
        PlantingRunEntry(
            _key="e_tmpl",
            run_key=TEMPLATE_KEY,
            species_key="species_lactuca_sativa",
            cultivar_key="cultivar_lollo_rosso",
            quantity=12,
            id_prefix="LAC",
        )
    ]


def _service():
    repo = MagicMock()
    repo.get_by_key.return_value = _template_run()
    wire_get_or_raise(repo, "PlantingRun")
    repo.get_entries.return_value = _template_entries()

    captured: dict[str, PlantingRun] = {}

    def _create(run: PlantingRun) -> PlantingRun:
        captured["run"] = run
        return run.model_copy(update={"key": "run_new"})

    repo.create.side_effect = _create
    repo.create_entry.side_effect = lambda entry: entry

    plant_repo = MagicMock()
    service = PlantingRunService(run_repo=repo, plant_repo=plant_repo, engine=PlantingRunEngine())
    return service, repo, plant_repo, captured


class TestCloneConfig:
    def test_copies_config_fields_from_template(self):
        service, _repo, _plant_repo, captured = _service()

        new_run = PlantingRun(
            tenant_key=TENANT,
            name="Salat 2026",
            run_type=PlantingRunType.MONOCULTURE,
            clone_from_run_key=TEMPLATE_KEY,
        )
        created = service.create_run(new_run)

        persisted = captured["run"]
        assert persisted.location_key == "loc_beet_c"
        assert persisted.substrate_batch_key == "batch_1"
        assert persisted.lifecycle_config_key == "lc_lettuce"
        assert persisted.nutrient_plan_key == "plan_lettuce"
        assert created.key == "run_new"

    def test_copies_entries_but_no_plants(self):
        service, repo, plant_repo, _captured = _service()

        new_run = PlantingRun(
            tenant_key=TENANT,
            name="Salat 2026",
            run_type=PlantingRunType.MONOCULTURE,
            clone_from_run_key=TEMPLATE_KEY,
        )
        service.create_run(new_run)

        # entry composition copied from the template ...
        assert repo.create_entry.call_count == 1
        copied_entry = repo.create_entry.call_args.args[0]
        assert copied_entry.species_key == "species_lactuca_sativa"
        assert copied_entry.cultivar_key == "cultivar_lollo_rosso"
        # ... but not a single PlantInstance was created.
        plant_repo.create.assert_not_called()

    def test_explicit_override_wins_over_template(self):
        service, _repo, _plant_repo, captured = _service()

        new_run = PlantingRun(
            tenant_key=TENANT,
            name="Salat 2026",
            run_type=PlantingRunType.MONOCULTURE,
            clone_from_run_key=TEMPLATE_KEY,
            location_key="loc_beet_d",
        )
        service.create_run(new_run)

        assert captured["run"].location_key == "loc_beet_d"

    def test_caller_entries_replace_template_composition(self):
        service, repo, _plant_repo, _captured = _service()

        new_run = PlantingRun(
            tenant_key=TENANT,
            name="Salat 2026",
            run_type=PlantingRunType.MONOCULTURE,
            clone_from_run_key=TEMPLATE_KEY,
        )
        own_entry = PlantingRunEntry(species_key="species_spinacia", quantity=8, id_prefix="SPI")
        service.create_run(new_run, [own_entry])

        repo.get_entries.assert_not_called()
        created_entry = repo.create_entry.call_args.args[0]
        assert created_entry.species_key == "species_spinacia"
