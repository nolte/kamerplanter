"""Soil-hazard knowledge table read from its seed YAML (REQ-054 §5.2a, #2888 F-18).

The table is global reference data with no user edits, so it is not copied into a
collection: the source reads ``seed_data/soil_hazards.yaml`` directly. A
re-researched value (#3005) therefore takes effect through the data file alone —
edit value and evidence status, ship, and the next process reads it; no code and
no migration. The file is validated twice: against its JSON schema by the
``seed-schema-conformance`` pre-commit hook, and against the domain model here,
which also enforces the evidence invariants.
"""

from __future__ import annotations

from pathlib import Path

import structlog

from app.common.enums import SoilHazard
from app.domain.interfaces.soil_hazard_knowledge_source import ISoilHazardKnowledgeSource
from app.domain.models.soil_hazard_knowledge import SoilHazardKnowledge, SoilHazardKnowledgeTable
from app.migrations.yaml_loader import SEED_DATA_DIR, load_yaml_path

logger = structlog.get_logger(__name__)

#: The shipped table, next to ``ipm.yaml`` (operator decision 2026-11-17).
SOIL_HAZARDS_SEED_PATH: Path = SEED_DATA_DIR / "soil_hazards.yaml"


class YamlSoilHazardKnowledgeSource(ISoilHazardKnowledgeSource):
    """Reads and validates the table once per instance."""

    def __init__(self, path: Path = SOIL_HAZARDS_SEED_PATH) -> None:
        self._path = path
        self._table: SoilHazardKnowledgeTable | None = None

    def get_table(self) -> SoilHazardKnowledgeTable:
        """Return the validated table.

        Raises:
            pydantic.ValidationError: If the file violates the evidence invariants.
            OSError: If the file cannot be read.
        """
        if self._table is None:
            raw = load_yaml_path(self._path)
            self._table = SoilHazardKnowledgeTable.model_validate(raw)
            logger.info("soil_hazard_knowledge_loaded", path=self._path.name, hazards=len(self._table.hazards))
        return self._table

    def get(self, hazard: SoilHazard) -> SoilHazardKnowledge:
        """Return the row of ``hazard``; the table holds one row per hazard."""
        for row in self.get_table().hazards:
            if row.hazard is hazard:
                return row
        # Unreachable for a validated table (one row per SoilHazard is enforced).
        msg = f"no knowledge row for soil hazard {hazard}"
        raise LookupError(msg)
