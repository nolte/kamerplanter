import pytest

from app.common.enums import EntityType, RowStatus
from app.domain.engines.row_validator import RowValidator


@pytest.fixture
def validator():
    return RowValidator()


class TestValidateSpeciesRow:
    def test_valid_row(self, validator):
        row = {"scientific_name": "Rosa canina", "common_name": "Dog rose"}
        result = validator.validate_row(row, EntityType.SPECIES, 1)
        assert result.status == RowStatus.VALID
        assert len(result.errors) == 0

    def test_missing_required_field(self, validator):
        row = {"scientific_name": "", "common_name": "Dog rose"}
        result = validator.validate_row(row, EntityType.SPECIES, 1)
        assert result.status == RowStatus.INVALID
        assert any(e.field == "scientific_name" for e in result.errors)

    def test_invalid_scientific_name(self, validator):
        row = {"scientific_name": "rosa canina"}  # lowercase genus
        result = validator.validate_row(row, EntityType.SPECIES, 1)
        assert result.status == RowStatus.INVALID
        assert any("Genus species" in e.message for e in result.errors)

    def test_valid_scientific_name(self, validator):
        row = {"scientific_name": "Cannabis sativa"}
        result = validator.validate_row(row, EntityType.SPECIES, 1)
        assert result.status == RowStatus.VALID

    def test_invalid_enum_value(self, validator):
        row = {"scientific_name": "Rosa canina", "growth_habit": "flying"}
        result = validator.validate_row(row, EntityType.SPECIES, 1)
        assert result.status == RowStatus.INVALID
        assert any(e.field == "growth_habit" for e in result.errors)

    def test_valid_enum_value(self, validator):
        row = {"scientific_name": "Rosa canina", "growth_habit": "shrub"}
        result = validator.validate_row(row, EntityType.SPECIES, 1)
        assert result.status == RowStatus.VALID


class TestDuplicateDetection:
    def test_duplicate_detected(self, validator):
        existing = {"Rosa canina"}
        row = {"scientific_name": "Rosa canina"}
        result = validator.validate_row(row, EntityType.SPECIES, 1, existing)
        assert result.status == RowStatus.DUPLICATE
        assert result.duplicate_key == "Rosa canina"

    def test_no_duplicate(self, validator):
        existing = {"Rosa canina"}
        row = {"scientific_name": "Cannabis sativa"}
        result = validator.validate_row(row, EntityType.SPECIES, 1, existing)
        assert result.status == RowStatus.VALID


class TestFamilyRow:
    def test_valid_family(self, validator):
        row = {"name": "Rosaceae", "common_name": "Rose family"}
        result = validator.validate_row(row, EntityType.BOTANICAL_FAMILY, 1)
        assert result.status == RowStatus.VALID

    def test_missing_name(self, validator):
        row = {"name": "", "common_name": "Rose family"}
        result = validator.validate_row(row, EntityType.BOTANICAL_FAMILY, 1)
        assert result.status == RowStatus.INVALID
