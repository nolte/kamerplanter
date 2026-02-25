"""Unit tests for enrichment domain models."""

from datetime import UTC, datetime

import pytest

from app.common.enums import AuthType, SyncStatus, SyncTrigger
from app.domain.models.enrichment import (
    ExternalCultivarData,
    ExternalMapping,
    ExternalSource,
    ExternalSpeciesData,
    FieldMapping,
    GBIFMatchResult,
    SyncResult,
    SyncRun,
)


class TestFieldMapping:
    def test_defaults(self):
        fm = FieldMapping()
        assert fm.external_value is None
        assert fm.local_value is None
        assert fm.confidence == 0.0
        assert fm.accepted is False
        assert fm.accepted_at is None

    def test_with_values(self):
        fm = FieldMapping(
            external_value="Herb",
            local_value=None,
            confidence=0.9,
            accepted=True,
            accepted_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        assert fm.external_value == "Herb"
        assert fm.confidence == 0.9
        assert fm.accepted is True

    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            FieldMapping(confidence=1.5)
        with pytest.raises(ValueError):
            FieldMapping(confidence=-0.1)


class TestExternalSource:
    def test_creation(self):
        source = ExternalSource(
            name="GBIF",
            source_key="gbif",
            base_url="https://api.gbif.org/v1",
            auth_type=AuthType.NONE,
            rate_limit_per_minute=60,
            priority=1,
        )
        assert source.name == "GBIF"
        assert source.source_key == "gbif"
        assert source.enabled is True
        assert source.key is None

    def test_populate_by_name(self):
        source = ExternalSource(
            _key="src_1",
            name="GBIF",
            source_key="gbif",
            base_url="https://api.gbif.org/v1",
        )
        assert source.key == "src_1"

    def test_serialization(self):
        source = ExternalSource(
            name="Perenual",
            source_key="perenual",
            base_url="https://perenual.com/api/v2",
            auth_type=AuthType.API_KEY,
        )
        data = source.model_dump(by_alias=True)
        assert data["source_key"] == "perenual"
        assert data["auth_type"] == "api_key"


class TestExternalMapping:
    def test_creation(self):
        mapping = ExternalMapping(
            internal_collection="species",
            internal_key="sp_1",
            source_key="gbif",
            external_id="12345",
        )
        assert mapping.internal_collection == "species"
        assert mapping.field_mappings == {}
        assert mapping.checksum == ""

    def test_with_field_mappings(self):
        mapping = ExternalMapping(
            internal_collection="species",
            internal_key="sp_1",
            source_key="gbif",
            external_id="12345",
            field_mappings={
                "genus": FieldMapping(external_value="Rosa", confidence=0.9, accepted=True),
            },
        )
        assert "genus" in mapping.field_mappings
        assert mapping.field_mappings["genus"].external_value == "Rosa"


class TestSyncRun:
    def test_defaults(self):
        run = SyncRun(source_key="gbif")
        assert run.status == SyncStatus.RUNNING
        assert run.triggered_by == SyncTrigger.MANUAL
        assert run.full_sync is False
        assert run.total_processed == 0
        assert run.errors == []

    def test_serialization(self):
        run = SyncRun(
            source_key="gbif",
            status=SyncStatus.SUCCESS,
            total_processed=10,
            new_mappings=5,
        )
        data = run.model_dump()
        assert data["status"] == "success"
        assert data["total_processed"] == 10


class TestExternalSpeciesData:
    def test_creation(self):
        data = ExternalSpeciesData(
            external_id="123",
            scientific_name="Rosa canina",
            common_names=["Dog Rose"],
            genus="Rosa",
            family_name="Rosaceae",
        )
        assert data.scientific_name == "Rosa canina"
        assert data.common_names == ["Dog Rose"]

    def test_defaults(self):
        data = ExternalSpeciesData(external_id="1", scientific_name="Test sp")
        assert data.common_names == []
        assert data.genus == ""
        assert data.image_url == ""
        assert data.synonyms == []
        assert data.taxonomic_authority == ""
        assert data.taxonomic_status == ""
        assert data.canonical_name == ""


class TestGBIFMatchResult:
    def test_creation(self):
        result = GBIFMatchResult(
            usage_key=5361880,
            scientific_name="Cannabis sativa L.",
            canonical_name="Cannabis sativa",
            authorship="L.",
            rank="SPECIES",
            taxonomic_status="ACCEPTED",
            confidence=99,
            match_type="EXACT",
            kingdom="Plantae",
            family="Cannabaceae",
            genus="Cannabis",
        )
        assert result.usage_key == 5361880
        assert result.scientific_name == "Cannabis sativa L."
        assert result.canonical_name == "Cannabis sativa"
        assert result.confidence == 99
        assert result.match_type == "EXACT"
        assert result.accepted_key is None
        assert result.accepted_name is None

    def test_synonym_fields(self):
        result = GBIFMatchResult(
            usage_key=9999999,
            scientific_name="Cannabis indica Lam.",
            canonical_name="Cannabis indica",
            taxonomic_status="SYNONYM",
            confidence=98,
            match_type="EXACT",
            accepted_key=5361880,
            accepted_name="Cannabis sativa L.",
        )
        assert result.taxonomic_status == "SYNONYM"
        assert result.accepted_key == 5361880
        assert result.accepted_name == "Cannabis sativa L."


class TestExternalCultivarData:
    def test_creation(self):
        data = ExternalCultivarData(
            external_id="c1",
            name="Heidesand",
            species_external_id="123",
        )
        assert data.name == "Heidesand"


class TestSyncResult:
    def test_defaults(self):
        result = SyncResult()
        assert result.total_processed == 0
        assert result.new_mappings == 0
        assert result.errors == []
