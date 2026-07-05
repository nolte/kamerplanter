"""Unit tests for ImportService create/update functions (#1, #2, #3).

Covers:
  * #2 — species import maps ALL 17 CSV-template columns to Species fields
    (previously only scientific_name/common_name/description);
  * #1 — cultivar import creates real Cultivar records (previously a noop);
  * #3 — the "update" duplicate strategy wires an update_fn so existing records
    are mutated instead of skipped.
"""

from unittest.mock import MagicMock

from app.common.enums import DuplicateStrategy, EntityType, GrowthHabit, PlantTrait, RootType, Suitability
from app.domain.models.species import Species
from app.domain.services.import_service import ImportService

_SPECIES_HEADER = (
    "scientific_name,common_name,family_name,growth_habit,cycle_type,root_type,"
    "description,container_suitable,recommended_container_volume_l,min_container_depth_cm,"
    "mature_height_cm,mature_width_cm,spacing_cm,indoor_suitable,balcony_suitable,"
    "greenhouse_recommended,support_required"
)
_SPECIES_ROW = (
    "Rosa canina,Dog rose,Rosaceae,shrub,perennial,fibrous,A wild rose,yes,5,30,100,80,50,limited,no,true,false"
)

_FULL_SPECIES_DATA = {
    "scientific_name": "Rosa canina",
    "common_name": "Dog rose",
    "family_name": "Rosaceae",
    "growth_habit": "shrub",
    "cycle_type": "perennial",
    "root_type": "fibrous",
    "description": "A wild rose",
    "container_suitable": "yes",
    "recommended_container_volume_l": "5",
    "min_container_depth_cm": "30",
    "mature_height_cm": "100",
    "mature_width_cm": "80",
    "spacing_cm": "50",
    "indoor_suitable": "limited",
    "balcony_suitable": "no",
    "greenhouse_recommended": "true",
    "support_required": "false",
}


def _service() -> tuple[ImportService, MagicMock, MagicMock]:
    species_repo = MagicMock()
    family_repo = MagicMock()
    svc = ImportService(MagicMock(), species_repo=species_repo, family_repo=family_repo)
    return svc, species_repo, family_repo


# ── #2 species full-column mapping ──────────────────────────────────────


def test_create_species_maps_all_template_columns():
    svc, species_repo, _ = _service()
    create_fn = svc._get_create_fn(EntityType.SPECIES)

    create_fn(_FULL_SPECIES_DATA)

    species_repo.create.assert_called_once()
    species: Species = species_repo.create.call_args[0][0]
    assert species.scientific_name == "Rosa canina"
    assert species.common_names == ["Dog rose"]
    assert species.family_key == "Rosaceae"  # family_name → family_key (best-effort)
    assert species.growth_habit == GrowthHabit.SHRUB
    assert species.root_type == RootType.FIBROUS
    assert species.description == "A wild rose"
    assert species.container_suitable == Suitability.YES
    assert species.recommended_container_volume_l == "5"
    assert species.min_container_depth_cm == 30
    assert species.mature_height_cm == "100"
    assert species.mature_width_cm == "80"
    assert species.spacing_cm == "50"
    assert species.indoor_suitable == Suitability.LIMITED
    assert species.balcony_suitable == Suitability.NO
    assert species.greenhouse_recommended is True
    assert species.support_required is False


def test_create_species_is_empty_tolerant():
    """Only scientific_name is required; empty cells fall back to model defaults."""
    svc, species_repo, _ = _service()
    create_fn = svc._get_create_fn(EntityType.SPECIES)

    create_fn({field: "" for field in _FULL_SPECIES_DATA} | {"scientific_name": "Mentha spicata"})

    species: Species = species_repo.create.call_args[0][0]
    assert species.scientific_name == "Mentha spicata"
    assert species.common_names == []
    assert species.family_key is None
    assert species.greenhouse_recommended is False
    assert species.support_required is False
    assert species.min_container_depth_cm is None


def test_create_species_end_to_end_accepts_17_column_csv():
    """The CsvParser accepts the full 17-column template and confirm() persists it."""
    svc, species_repo, _ = _service()
    csv = (_SPECIES_HEADER + "\n" + _SPECIES_ROW + "\n").encode()
    job = svc._engine.upload_and_validate(csv, EntityType.SPECIES, "t.csv", DuplicateStrategy.SKIP)

    svc._repo.get_or_raise.return_value = job
    svc._repo.update.side_effect = lambda key, j: j
    result = svc.confirm("job-1")

    assert result.result is not None
    assert result.result.created == 1
    assert result.result.failed == 0
    species_repo.create.assert_called_once()


# ── #1 cultivar create (no longer a noop) ───────────────────────────────


def test_create_cultivar_persists_record():
    svc, species_repo, _ = _service()
    create_fn = svc._get_create_fn(EntityType.CULTIVAR)

    create_fn(
        {
            "species_key": "rosa_canina",
            "cultivar_name": "Red Beauty",
            "breeder": "ACME Seeds",
            "description": "ignored — no model field",
            "traits": "high_yield, disease_resistant | heirloom",
        }
    )

    species_repo.create_cultivar.assert_called_once()
    cultivar = species_repo.create_cultivar.call_args[0][0]
    assert cultivar.name == "Red Beauty"
    assert cultivar.species_key == "rosa_canina"
    assert cultivar.breeder == "ACME Seeds"
    assert set(cultivar.traits) == {
        PlantTrait.HIGH_YIELD,
        PlantTrait.DISEASE_RESISTANT,
        PlantTrait.HEIRLOOM,
    }


def test_create_cultivar_minimal_required_only():
    svc, species_repo, _ = _service()
    create_fn = svc._get_create_fn(EntityType.CULTIVAR)

    create_fn({"species_key": "rosa_canina", "cultivar_name": "Plain", "breeder": "", "traits": ""})

    cultivar = species_repo.create_cultivar.call_args[0][0]
    assert cultivar.name == "Plain"
    assert cultivar.breeder is None
    assert cultivar.traits == []


# ── #3 update duplicate strategy ────────────────────────────────────────


def test_update_species_mutates_existing_without_clobbering():
    svc, species_repo, _ = _service()
    existing = Species(scientific_name="Rosa canina", description="old", genus="Rosa")
    existing.key = "sp-1"
    species_repo.get_by_scientific_name.return_value = existing

    update_fn = svc._get_update_fn(EntityType.SPECIES)
    update_fn({"scientific_name": "Rosa canina", "description": "new desc", "common_name": "Dog rose"})

    species_repo.update.assert_called_once()
    key, updated = species_repo.update.call_args[0]
    assert key == "sp-1"
    assert updated.description == "new desc"
    assert updated.common_names == ["Dog rose"]
    assert updated.genus == "Rosa"  # untouched column preserved


def test_confirm_update_strategy_updates_duplicates():
    svc, species_repo, _ = _service()
    csv = b"scientific_name,description\nRosa canina,Updated\n"
    job = svc._engine.upload_and_validate(csv, EntityType.SPECIES, "t.csv", DuplicateStrategy.UPDATE, {"Rosa canina"})
    svc._repo.get_or_raise.return_value = job
    svc._repo.update.side_effect = lambda key, j: j
    species_repo.get_by_scientific_name.return_value = Species(scientific_name="Rosa canina")

    result = svc.confirm("job-1")

    assert result.result is not None
    assert result.result.updated == 1
    assert result.result.created == 0
    species_repo.update.assert_called_once()


def test_confirm_skip_strategy_does_not_update():
    svc, species_repo, _ = _service()
    csv = b"scientific_name,description\nRosa canina,Updated\n"
    job = svc._engine.upload_and_validate(csv, EntityType.SPECIES, "t.csv", DuplicateStrategy.SKIP, {"Rosa canina"})
    svc._repo.get_or_raise.return_value = job
    svc._repo.update.side_effect = lambda key, j: j

    result = svc.confirm("job-1")

    assert result.result is not None
    assert result.result.skipped == 1
    species_repo.get_by_scientific_name.assert_not_called()
    species_repo.update.assert_not_called()
