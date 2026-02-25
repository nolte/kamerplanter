"""Unit tests for the enrichment engine."""

from unittest.mock import MagicMock

import pytest

from app.common.enums import SyncStatus
from app.domain.engines.enrichment_engine import EnrichmentEngine
from app.domain.models.enrichment import ExternalMapping, ExternalSpeciesData, FieldMapping, SyncRun
from app.domain.models.species import Species


@pytest.fixture
def mock_species_repo():
    return MagicMock()


@pytest.fixture
def mock_mapping_repo():
    return MagicMock()


@pytest.fixture
def mock_sync_run_repo():
    repo = MagicMock()
    # Make create return a SyncRun with a key
    repo.create.side_effect = lambda run: SyncRun(
        **{**run.model_dump(), "_key": "run_1"}
    )
    # Make update return whatever was passed
    repo.update.side_effect = lambda key, run: run
    return repo


@pytest.fixture
def mock_family_repo():
    return MagicMock()


@pytest.fixture
def engine(mock_species_repo, mock_mapping_repo, mock_sync_run_repo):
    return EnrichmentEngine(mock_species_repo, mock_mapping_repo, mock_sync_run_repo)


@pytest.fixture
def engine_with_family(mock_species_repo, mock_mapping_repo, mock_sync_run_repo, mock_family_repo):
    return EnrichmentEngine(mock_species_repo, mock_mapping_repo, mock_sync_run_repo, mock_family_repo)


@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    adapter.source_key = "gbif"
    return adapter


@pytest.fixture
def sample_external_data():
    return ExternalSpeciesData(
        external_id="12345",
        scientific_name="Rosa canina",
        common_names=["Dog Rose"],
        genus="Rosa",
        family_name="Rosaceae",
        growth_habit="shrub",
        native_habitat="Europe",
        hardiness_zones=["5a", "9b"],
        synonyms=["Rosa canis"],
        description="A thorny shrub.",
        taxonomic_authority="L.",
        taxonomic_status="ACCEPTED",
    )


@pytest.fixture
def sample_species():
    return Species(
        _key="sp_1",
        scientific_name="Rosa canina",
        common_names=[],
        genus="",
        growth_habit="herb",
        root_type="fibrous",
    )


class TestIncrementalSync:
    def test_sync_unmapped_species(
        self, engine, mock_adapter, mock_mapping_repo, sample_external_data, mock_species_repo, sample_species,
    ):
        mock_mapping_repo.find_unmapped_species.return_value = [
            {"_key": "sp_1", "scientific_name": "Rosa canina"}
        ]
        mock_adapter.enrich_species.return_value = sample_external_data
        mock_species_repo.get_by_key.return_value = sample_species
        mock_mapping_repo.get_by_internal.return_value = None
        mock_mapping_repo.create.side_effect = lambda m: ExternalMapping(**{**m.model_dump(), "_key": "em_1"})

        run = engine.sync_source(mock_adapter, full_sync=False)

        assert run.status in (SyncStatus.SUCCESS, SyncStatus.PARTIAL)
        assert run.total_processed == 1
        assert run.new_mappings == 1

    def test_sync_no_results(self, engine, mock_adapter, mock_mapping_repo):
        mock_mapping_repo.find_unmapped_species.return_value = [
            {"_key": "sp_1", "scientific_name": "Unknown plantae"}
        ]
        mock_adapter.enrich_species.return_value = None

        run = engine.sync_source(mock_adapter, full_sync=False)

        assert run.status == SyncStatus.SUCCESS
        assert run.new_mappings == 0

    def test_sync_with_error(self, engine, mock_adapter, mock_mapping_repo):
        mock_mapping_repo.find_unmapped_species.return_value = [
            {"_key": "sp_1", "scientific_name": "Rosa canina"}
        ]
        mock_adapter.enrich_species.side_effect = Exception("API timeout")

        run = engine.sync_source(mock_adapter, full_sync=False)

        assert run.status == SyncStatus.PARTIAL
        assert len(run.errors) == 1


class TestFullSync:
    def test_full_sync_new_mapping(
        self, engine, mock_adapter, mock_species_repo, mock_mapping_repo, sample_external_data, sample_species,
    ):
        mock_species_repo.get_all.return_value = ([sample_species], 1)
        mock_adapter.enrich_species.return_value = sample_external_data
        mock_mapping_repo.get_by_internal.return_value = None
        mock_species_repo.get_by_key.return_value = sample_species
        mock_mapping_repo.create.side_effect = lambda m: ExternalMapping(**{**m.model_dump(), "_key": "em_1"})

        run = engine.sync_source(mock_adapter, full_sync=True)

        assert run.new_mappings == 1

    def test_full_sync_existing_unchanged(
        self, engine, mock_adapter, mock_species_repo, mock_mapping_repo, sample_external_data, sample_species,
    ):
        existing_mapping = ExternalMapping(
            _key="em_1",
            internal_collection="species",
            internal_key="sp_1",
            source_key="gbif",
            external_id="12345",
            checksum=EnrichmentEngine._compute_checksum(sample_external_data),
        )
        mock_species_repo.get_all.return_value = ([sample_species], 1)
        mock_adapter.enrich_species.return_value = sample_external_data
        mock_mapping_repo.get_by_internal.return_value = existing_mapping

        run = engine.sync_source(mock_adapter, full_sync=True)

        assert run.updated_mappings == 0


class TestApplyEnrichment:
    def test_auto_accept_empty_fields(
        self, engine, mock_species_repo, mock_mapping_repo, sample_species, sample_external_data,
    ):
        mock_species_repo.get_by_key.return_value = sample_species
        mock_mapping_repo.get_by_internal.return_value = None
        mock_mapping_repo.create.side_effect = lambda m: ExternalMapping(**{**m.model_dump(), "_key": "em_1"})

        mapping = engine._apply_enrichment("sp_1", "gbif", sample_external_data)

        # common_names was empty, should be auto-accepted
        assert mapping.field_mappings["common_names"].accepted is True
        assert mapping.field_mappings["common_names"].confidence == 0.9
        # genus was empty, should be auto-accepted
        assert mapping.field_mappings["genus"].accepted is True
        # growth_habit was "herb" (not empty), should be proposed only
        assert mapping.field_mappings["growth_habit"].accepted is False
        assert mapping.field_mappings["growth_habit"].confidence == 0.7

    def test_propose_only_for_existing_values(self, engine, mock_species_repo, mock_mapping_repo, sample_external_data):
        species_with_data = Species(
            _key="sp_1",
            scientific_name="Rosa canina",
            common_names=["Rose"],
            genus="Rosa",
            growth_habit="shrub",
            root_type="fibrous",
            native_habitat="Asia",
            hardiness_zones=["6a", "8b"],
            synonyms=["Rosa old"],
            description="Existing description.",
            taxonomic_authority="L.",
            taxonomic_status="ACCEPTED",
        )
        mock_species_repo.get_by_key.return_value = species_with_data
        mock_mapping_repo.get_by_internal.return_value = None
        mock_mapping_repo.create.side_effect = lambda m: ExternalMapping(**{**m.model_dump(), "_key": "em_1"})

        mapping = engine._apply_enrichment("sp_1", "gbif", sample_external_data)

        # All fields have local values, so all should be proposed only
        for field_name, fm in mapping.field_mappings.items():
            assert fm.accepted is False, f"Field {field_name} should not be auto-accepted"
            assert fm.confidence == 0.7

    def test_new_fields_enrichment(
        self, engine, mock_species_repo, mock_mapping_repo, sample_species, sample_external_data,
    ):
        mock_species_repo.get_by_key.return_value = sample_species
        mock_mapping_repo.get_by_internal.return_value = None
        mock_mapping_repo.create.side_effect = lambda m: ExternalMapping(**{**m.model_dump(), "_key": "em_1"})

        mapping = engine._apply_enrichment("sp_1", "gbif", sample_external_data)

        # New GBIF fields should be auto-accepted (empty on species)
        assert "synonyms" in mapping.field_mappings
        assert mapping.field_mappings["synonyms"].accepted is True
        assert mapping.field_mappings["synonyms"].external_value == ["Rosa canis"]

        assert "description" in mapping.field_mappings
        assert mapping.field_mappings["description"].accepted is True

        assert "taxonomic_authority" in mapping.field_mappings
        assert mapping.field_mappings["taxonomic_authority"].accepted is True
        assert mapping.field_mappings["taxonomic_authority"].external_value == "L."

        assert "taxonomic_status" in mapping.field_mappings
        assert mapping.field_mappings["taxonomic_status"].accepted is True

    def test_family_key_lookup(
        self, engine_with_family, mock_species_repo, mock_mapping_repo, mock_family_repo, sample_external_data,
    ):
        species_no_family = Species(
            _key="sp_1",
            scientific_name="Rosa canina",
            common_names=[],
            genus="",
            growth_habit="herb",
            root_type="fibrous",
            family_key=None,
        )
        mock_species_repo.get_by_key.return_value = species_no_family
        mock_mapping_repo.get_by_internal.return_value = None
        mock_mapping_repo.create.side_effect = lambda m: ExternalMapping(**{**m.model_dump(), "_key": "em_1"})

        mock_family = MagicMock()
        mock_family.key = "fam_rosaceae"
        mock_family_repo.get_by_name.return_value = mock_family

        mapping = engine_with_family._apply_enrichment("sp_1", "gbif", sample_external_data)

        mock_family_repo.get_by_name.assert_called_once_with("Rosaceae")
        mock_species_repo.update_field.assert_any_call("sp_1", "family_key", "fam_rosaceae")
        assert "family_key" in mapping.field_mappings

    def test_family_key_not_found(
        self, engine_with_family, mock_species_repo, mock_mapping_repo, mock_family_repo, sample_external_data,
    ):
        species_no_family = Species(
            _key="sp_1",
            scientific_name="Rosa canina",
            common_names=[],
            genus="",
            growth_habit="herb",
            root_type="fibrous",
            family_key=None,
        )
        mock_species_repo.get_by_key.return_value = species_no_family
        mock_mapping_repo.get_by_internal.return_value = None
        mock_mapping_repo.create.side_effect = lambda m: ExternalMapping(**{**m.model_dump(), "_key": "em_1"})

        mock_family_repo.get_by_name.return_value = None

        mapping = engine_with_family._apply_enrichment("sp_1", "gbif", sample_external_data)

        assert "family_key" not in mapping.field_mappings


class TestAcceptRejectFields:
    def test_accept_fields(self, engine, mock_species_repo, mock_mapping_repo):
        mapping = ExternalMapping(
            _key="em_1",
            internal_collection="species",
            internal_key="sp_1",
            source_key="gbif",
            external_id="123",
            field_mappings={
                "genus": FieldMapping(external_value="Rosa", confidence=0.7, accepted=False),
            },
        )
        mock_mapping_repo.get_by_internal.return_value = mapping
        mock_mapping_repo.update.side_effect = lambda key, m: m

        result = engine.accept_fields("sp_1", "gbif", ["genus"])

        assert result.field_mappings["genus"].accepted is True
        mock_species_repo.update_field.assert_called_once_with("sp_1", "genus", "Rosa")

    def test_reject_fields(self, engine, mock_mapping_repo):
        mapping = ExternalMapping(
            _key="em_1",
            internal_collection="species",
            internal_key="sp_1",
            source_key="gbif",
            external_id="123",
            field_mappings={
                "genus": FieldMapping(external_value="Rosa", confidence=0.7, accepted=False),
                "native_habitat": FieldMapping(external_value="Europe", confidence=0.7, accepted=False),
            },
        )
        mock_mapping_repo.get_by_internal.return_value = mapping
        mock_mapping_repo.update.side_effect = lambda key, m: m

        result = engine.reject_fields("sp_1", "gbif", ["genus"])

        assert "genus" not in result.field_mappings
        assert "native_habitat" in result.field_mappings


class TestChecksum:
    def test_deterministic(self, sample_external_data):
        c1 = EnrichmentEngine._compute_checksum(sample_external_data)
        c2 = EnrichmentEngine._compute_checksum(sample_external_data)
        assert c1 == c2

    def test_different_data_different_checksum(self, sample_external_data):
        c1 = EnrichmentEngine._compute_checksum(sample_external_data)
        other = ExternalSpeciesData(external_id="99999", scientific_name="Other sp")
        c2 = EnrichmentEngine._compute_checksum(other)
        assert c1 != c2
