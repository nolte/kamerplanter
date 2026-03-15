import re

from app.common.enums import (
    CycleType,
    EntityType,
    GrowthHabit,
    RootType,
    RowStatus,
    Suitability,
)
from app.domain.engines.csv_parser import COLUMN_DEFINITIONS
from app.domain.models.import_job import PreviewRow, RowValidationError

SCIENTIFIC_NAME_PATTERN = re.compile(r"^[A-Z][a-z]+ [a-z]+")

ENUM_VALIDATORS: dict[str, type] = {
    "growth_habit": GrowthHabit,
    "cycle_type": CycleType,
    "root_type": RootType,
    "container_suitable": Suitability,
    "indoor_suitable": Suitability,
    "balcony_suitable": Suitability,
}


class RowValidator:
    """Validate individual CSV rows against entity schema."""

    def validate_row(
        self,
        row: dict,
        entity_type: EntityType,
        row_number: int,
        existing_keys: set[str] | None = None,
    ) -> PreviewRow:
        errors: list[RowValidationError] = []
        duplicate_key: str | None = None

        col_defs = COLUMN_DEFINITIONS[entity_type]

        # Required field validation
        for field, required in col_defs.items():
            if required and not row.get(field, "").strip():
                errors.append(RowValidationError(
                    row=row_number,
                    field=field,
                    message=f"Required field '{field}' is empty",
                ))

        # Scientific name pattern for species
        if entity_type == EntityType.SPECIES:
            name = row.get("scientific_name", "").strip()
            if name and not SCIENTIFIC_NAME_PATTERN.match(name):
                errors.append(RowValidationError(
                    row=row_number,
                    field="scientific_name",
                    message="Scientific name must match 'Genus species' format",
                ))

        # Enum validation
        for field, enum_cls in ENUM_VALIDATORS.items():
            value = row.get(field, "").strip()
            if value:
                valid_values = {e.value for e in enum_cls}
                if value.lower() not in valid_values:
                    errors.append(RowValidationError(
                        row=row_number,
                        field=field,
                        message=f"Invalid value '{value}'. Must be one of: {', '.join(sorted(valid_values))}",
                    ))

        # Duplicate check
        status = RowStatus.VALID
        if existing_keys is not None:
            key_field = self._get_key_field(entity_type)
            key_value = row.get(key_field, "").strip()
            if key_value and key_value in existing_keys:
                status = RowStatus.DUPLICATE
                duplicate_key = key_value

        if errors:
            status = RowStatus.INVALID

        return PreviewRow(
            row_number=row_number,
            data=row,
            status=status,
            errors=errors,
            duplicate_key=duplicate_key,
        )

    @staticmethod
    def _get_key_field(entity_type: EntityType) -> str:
        if entity_type == EntityType.SPECIES:
            return "scientific_name"
        if entity_type == EntityType.CULTIVAR:
            return "cultivar_name"
        return "name"
