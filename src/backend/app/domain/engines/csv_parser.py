import csv
import io
import re

from app.common.enums import EntityType

# SEC-M-008: Security constants
MAX_DATA_ROWS = 10_000
CSV_INJECTION_PREFIXES = frozenset({"=", "+", "-", "@", "\t", "\r"})

COLUMN_DEFINITIONS: dict[EntityType, dict[str, bool]] = {
    EntityType.SPECIES: {
        "scientific_name": True,
        "common_name": False,
        "family_name": False,
        "growth_habit": False,
        "cycle_type": False,
        "root_type": False,
        "description": False,
        "container_suitable": False,
        "recommended_container_volume_l": False,
        "min_container_depth_cm": False,
        "mature_height_cm": False,
        "mature_width_cm": False,
        "spacing_cm": False,
        "indoor_suitable": False,
        "balcony_suitable": False,
        "greenhouse_recommended": False,
        "support_required": False,
    },
    EntityType.CULTIVAR: {
        "species_key": True,
        "cultivar_name": True,
        "breeder": False,
        "description": False,
        "traits": False,
    },
    EntityType.BOTANICAL_FAMILY: {
        "name": True,
        "common_name": False,
        "order_name": False,
        "description": False,
    },
}


class CsvParser:
    """Parse CSV files for species/cultivar/family import."""

    @staticmethod
    def detect_encoding(file_bytes: bytes) -> str:
        try:
            file_bytes.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            return "latin-1"

    @staticmethod
    def detect_delimiter(sample: str) -> str:
        for delim in [";", "\t", ","]:
            if delim in sample:
                return delim
        return ","

    @staticmethod
    def get_template(entity_type: EntityType) -> str:
        columns = list(COLUMN_DEFINITIONS[entity_type].keys())
        return ",".join(columns) + "\n"

    def parse(
        self,
        file_bytes: bytes,
        entity_type: EntityType,
    ) -> tuple[list[dict], list[str]]:
        """Parse CSV bytes into row dicts.

        Returns:
            Tuple of (rows, warnings). Warnings include CSV injection sanitization notices.
        """
        encoding = self.detect_encoding(file_bytes)
        text = file_bytes.decode(encoding)
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        stripped = text.strip()
        if not stripped:
            return [], []
        lines = stripped.split("\n")

        delimiter = self.detect_delimiter(lines[0])
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

        # Validate header
        expected_cols = set(COLUMN_DEFINITIONS[entity_type].keys())
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")
        actual_cols = {self._normalize_header(h) for h in reader.fieldnames}
        required = {k for k, v in COLUMN_DEFINITIONS[entity_type].items() if v}
        missing_required = required - actual_cols
        if missing_required:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing_required))}")

        rows: list[dict] = []
        warnings: list[str] = []
        for row_idx, row in enumerate(reader, start=1):
            # SEC-M-008: Row count limit
            if row_idx > MAX_DATA_ROWS:
                raise ValueError(f"CSV file exceeds maximum of {MAX_DATA_ROWS} data rows")

            normalized = {}
            for key, value in row.items():
                norm_key = self._normalize_header(key)
                if norm_key in expected_cols:
                    raw = value or ""
                    # SEC-M-008: CSV injection sanitization (check before strip)
                    if raw and raw[0] in CSV_INJECTION_PREFIXES:
                        warnings.append(
                            f"Row {row_idx}, field '{norm_key}': SUSPICIOUS_CONTENT — leading character stripped"
                        )
                        raw = raw[1:]
                    normalized[norm_key] = raw.strip()
            rows.append(normalized)

        return rows, warnings

    @staticmethod
    def _normalize_header(header: str) -> str:
        h = header.strip().lower()
        h = re.sub(r"[^a-z0-9]+", "_", h)
        return h.strip("_")
