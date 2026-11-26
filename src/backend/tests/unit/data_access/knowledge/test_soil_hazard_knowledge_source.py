"""The soil-hazard knowledge table as the loader reads it (REQ-054 §5.2a, #2888 F-18).

F-18 acceptance-3: the research start values are loaded with their evidence status,
and only 3/3 values resolve to a duration usable for a time statement.
F-18 acceptance-4: a re-researched value takes effect through a data change alone —
the tests copy the shipped YAML, change one value's status, and read it through the
unchanged production loader and engine.

Both run the production path (``YamlSoilHazardKnowledgeSource`` over the shipped
file, then ``SoilHazardKnowledgeEngine.resolve_durations``), not a hand-built model,
so a loader that dropped the status or an engine that ignored it fails here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from app.common.enums import EvidenceKind, EvidenceStatus, SoilHazard
from app.data_access.knowledge.soil_hazard_knowledge_source import (
    SOIL_HAZARDS_SEED_PATH,
    YamlSoilHazardKnowledgeSource,
)
from app.domain.engines.soil_hazard_knowledge_engine import SoilHazardKnowledgeEngine

ENGINE = SoilHazardKnowledgeEngine()

#: Research start values (§7.11, pause of cyst_nematode per operator decision
#: 2026-11-22): (stored pause, pause status, stored survival, survival status).
START_VALUES: dict[SoilHazard, tuple[int | None, EvidenceStatus, int | None, EvidenceStatus]] = {
    SoilHazard.CLUBROOT: (7, EvidenceStatus.EVIDENCED, 15, EvidenceStatus.EVIDENCED),
    SoilHazard.CYST_NEMATODE: (3, EvidenceStatus.EVIDENCED, None, EvidenceStatus.CONTRADICTORY),
    SoilHazard.ROOT_KNOT_NEMATODE: (3, EvidenceStatus.INSUFFICIENT, None, EvidenceStatus.CONTRADICTORY),
    SoilHazard.WHITE_ROT: (None, EvidenceStatus.INSUFFICIENT, 15, EvidenceStatus.EVIDENCED),
    SoilHazard.PEA_ROOT_ROT: (8, EvidenceStatus.CONTRADICTORY, 10, EvidenceStatus.EVIDENCED),
    SoilHazard.SCLEROTINIA: (5, EvidenceStatus.EVIDENCED, 10, EvidenceStatus.INSUFFICIENT),
    SoilHazard.VERTICILLIUM: (4, EvidenceStatus.EVIDENCED, 10, EvidenceStatus.EVIDENCED),
    SoilHazard.JUGLONE: (5, EvidenceStatus.CONTRADICTORY, None, EvidenceStatus.NOT_FOUND),
}

#: What a warning may state as a duration: only the 3/3 values above.
USABLE: dict[SoilHazard, tuple[int | None, int | None]] = {
    SoilHazard.CLUBROOT: (7, 15),
    SoilHazard.CYST_NEMATODE: (3, None),
    SoilHazard.ROOT_KNOT_NEMATODE: (None, None),
    SoilHazard.WHITE_ROT: (None, 15),
    SoilHazard.PEA_ROOT_ROT: (None, 10),
    SoilHazard.SCLEROTINIA: (5, None),
    SoilHazard.VERTICILLIUM: (4, 10),
    SoilHazard.JUGLONE: (None, None),
}


def _shipped_raw() -> dict[str, Any]:
    raw = yaml.safe_load(SOIL_HAZARDS_SEED_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def _row(raw: dict[str, Any], hazard: SoilHazard) -> dict[str, Any]:
    for row in raw["hazards"]:
        if row["hazard"] == hazard.value:
            return row
    raise AssertionError(f"{hazard} missing from the fixture")


def _write(tmp_path: Path, raw: dict[str, Any]) -> Path:
    path = tmp_path / "soil_hazards.yaml"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


class TestShippedStartValues:
    """acceptance-3 — the start values are loaded with their status."""

    def test_every_hazard_has_exactly_one_row(self) -> None:
        table = YamlSoilHazardKnowledgeSource().get_table()

        assert sorted(row.hazard for row in table.hazards) == sorted(SoilHazard)

    @pytest.mark.parametrize("hazard", list(SoilHazard))
    def test_start_value_and_status_are_loaded(self, hazard: SoilHazard) -> None:
        row = YamlSoilHazardKnowledgeSource().get(hazard)
        pause, pause_status, survival, survival_status = START_VALUES[hazard]

        assert row.soil_persistence_years.years == pause
        assert row.soil_persistence_years.evidence.status is pause_status
        assert row.max_survival_years.years == survival
        assert row.max_survival_years.evidence.status is survival_status

    @pytest.mark.parametrize("hazard", list(SoilHazard))
    def test_only_evidenced_values_resolve_to_a_usable_duration(self, hazard: SoilHazard) -> None:
        resolved = ENGINE.resolve_durations(YamlSoilHazardKnowledgeSource().get(hazard))

        assert (resolved.soil_persistence_years, resolved.max_survival_years) == USABLE[hazard]

    def test_a_recorded_but_unevidenced_value_is_not_usable(self) -> None:
        """The table keeps 2/3 and 1/3 figures informative; none of them becomes a duration."""
        source = YamlSoilHazardKnowledgeSource()
        recorded_not_usable = [
            source.get(SoilHazard.ROOT_KNOT_NEMATODE).soil_persistence_years,  # 3 y, 1/3
            source.get(SoilHazard.PEA_ROOT_ROT).soil_persistence_years,  # 8 y, contradictory
            source.get(SoilHazard.SCLEROTINIA).max_survival_years,  # 10 y, 2/3
            source.get(SoilHazard.JUGLONE).soil_persistence_years,  # 5 y, contradictory
        ]

        assert all(value.years is not None for value in recorded_not_usable)
        assert [ENGINE.usable_years(value) for value in recorded_not_usable] == [None, None, None, None]

    def test_ranges_count_as_evidenced_with_their_kind(self) -> None:
        """Operator decision 2026-11-22: a value inside all three ranges is 3/3, kind ``range``."""
        source = YamlSoilHazardKnowledgeSource()
        for hazard in (SoilHazard.CLUBROOT, SoilHazard.CYST_NEMATODE, SoilHazard.SCLEROTINIA, SoilHazard.VERTICILLIUM):
            pause = source.get(hazard).soil_persistence_years
            assert pause.evidence.kind is EvidenceKind.RANGE, hazard
            assert ENGINE.usable_years(pause) == pause.years, hazard

    def test_soft_hazards_are_root_knot_nematode_and_sclerotinia(self) -> None:
        table = YamlSoilHazardKnowledgeSource().get_table()

        assert {row.hazard for row in table.hazards if row.soft} == {
            SoilHazard.ROOT_KNOT_NEMATODE,
            SoilHazard.SCLEROTINIA,
        }


class TestDataChangeAlone:
    """acceptance-4 — changing a value's status in the data changes the resolved duration."""

    def test_raising_a_status_to_evidenced_makes_the_duration_usable(self, tmp_path: Path) -> None:
        raw = _shipped_raw()
        pause = _row(raw, SoilHazard.PEA_ROOT_ROT)["soil_persistence_years"]
        assert (
            ENGINE.resolve_durations(
                YamlSoilHazardKnowledgeSource().get(SoilHazard.PEA_ROOT_ROT)
            ).soil_persistence_years
            is None
        )
        pause["evidence"].update(status="evidenced", sources=3, kind="range")

        changed = YamlSoilHazardKnowledgeSource(path=_write(tmp_path, raw)).get(SoilHazard.PEA_ROOT_ROT)

        assert ENGINE.resolve_durations(changed).soil_persistence_years == 8

    def test_lowering_a_status_withdraws_the_duration(self, tmp_path: Path) -> None:
        raw = _shipped_raw()
        _row(raw, SoilHazard.CLUBROOT)["soil_persistence_years"]["evidence"].update(status="insufficient", sources=2)

        changed = YamlSoilHazardKnowledgeSource(path=_write(tmp_path, raw)).get(SoilHazard.CLUBROOT)

        assert ENGINE.resolve_durations(changed).soil_persistence_years is None
        assert ENGINE.resolve_durations(changed).max_survival_years == 15

    def test_a_newly_researched_value_takes_effect(self, tmp_path: Path) -> None:
        """#3005-shape change: white rot gets a 3/3 pause where the table had none."""
        raw = _shipped_raw()
        _row(raw, SoilHazard.WHITE_ROT)["soil_persistence_years"] = {
            "years": 10,
            "evidence": {
                "status": "evidenced",
                "sources": 3,
                "kind": "range",
                "basis": "fixture: three re-researched sources",
                "ref": "fixture",
            },
        }

        changed = YamlSoilHazardKnowledgeSource(path=_write(tmp_path, raw)).get(SoilHazard.WHITE_ROT)

        assert ENGINE.resolve_durations(changed).soil_persistence_years == 10

    def test_a_status_claiming_three_sources_it_lacks_is_refused(self, tmp_path: Path) -> None:
        """The data change cannot skip the evidence: 'evidenced' with two sources does not load."""
        raw = _shipped_raw()
        _row(raw, SoilHazard.PEA_ROOT_ROT)["soil_persistence_years"]["evidence"].update(
            status="evidenced", kind="range"
        )

        with pytest.raises(ValidationError, match="needs 3 sources"):
            YamlSoilHazardKnowledgeSource(path=_write(tmp_path, raw)).get_table()
