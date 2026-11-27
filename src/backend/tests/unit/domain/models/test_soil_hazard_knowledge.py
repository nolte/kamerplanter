"""Evidence invariants of the soil-hazard knowledge table (REQ-054 §5.2a, #2888 F-18).

The invariants are what keeps a data change honest: a value can only become usable
for a time statement by being recorded as 3/3 with three sources and an evidence
shape. Each test names one way a row could claim more than it carries.
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.common.enums import EvidenceKind, EvidenceStatus, SoilHazard
from app.domain.engines.soil_hazard_knowledge_engine import SoilHazardKnowledgeEngine
from app.domain.models.soil_hazard_knowledge import (
    Evidence,
    EvidencedYears,
    SoilHazardKnowledge,
    SoilHazardKnowledgeTable,
)


def _evidence(status: str = "evidenced", sources: int = 3, kind: str | None = "number") -> dict[str, Any]:
    return {"status": status, "sources": sources, "kind": kind, "basis": "test", "ref": "test"}


def _row(hazard: str, **overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "hazard": hazard,
        "pathogens": ["Testus pathogenus"],
        "soil_persistence_years": {"years": 4, "evidence": _evidence()},
        "max_survival_years": {"years": None, "evidence": _evidence("not_found", 0, None)},
        "hosts": [{"level": "family", "name": "Brassicaceae", "evidence": _evidence(kind=None)}],
    }
    row.update(overrides)
    return row


class TestEvidence:
    def test_evidenced_needs_three_sources(self) -> None:
        with pytest.raises(ValidationError, match="needs 3 sources"):
            Evidence.model_validate(_evidence(sources=2))

    def test_insufficient_cannot_have_three_sources(self) -> None:
        with pytest.raises(ValidationError, match="fewer than three"):
            Evidence.model_validate(_evidence("insufficient", 3))

    def test_not_found_cannot_name_sources(self) -> None:
        with pytest.raises(ValidationError, match="not_found"):
            Evidence.model_validate(_evidence("not_found", 1, None))

    def test_sources_are_capped_at_three(self) -> None:
        with pytest.raises(ValidationError):
            Evidence.model_validate(_evidence(sources=4))


class TestEvidencedYears:
    def test_evidenced_duration_needs_a_value(self) -> None:
        with pytest.raises(ValidationError, match="needs a value"):
            EvidencedYears.model_validate({"years": None, "evidence": _evidence()})

    def test_evidenced_duration_needs_a_kind(self) -> None:
        with pytest.raises(ValidationError, match="evidence.kind"):
            EvidencedYears.model_validate({"years": 4, "evidence": _evidence(kind=None)})

    def test_not_found_cannot_carry_a_value(self) -> None:
        with pytest.raises(ValidationError, match="cannot carry a value"):
            EvidencedYears.model_validate({"years": 4, "evidence": _evidence("not_found", 0, None)})

    @pytest.mark.parametrize(
        ("status", "sources", "expected"),
        [
            ("evidenced", 3, 4),
            ("insufficient", 2, None),
            ("contradictory", 3, None),
        ],
    )
    def test_only_evidenced_is_usable(self, status: str, sources: int, expected: int | None) -> None:
        value = EvidencedYears.model_validate({"years": 4, "evidence": _evidence(status, sources)})

        assert SoilHazardKnowledgeEngine().usable_years(value) == expected


class TestRowAndTable:
    def test_a_taxon_cannot_be_host_and_non_host(self) -> None:
        host = {"level": "family", "name": "Poaceae", "evidence": _evidence(kind=None)}

        with pytest.raises(ValidationError, match="host and non-host"):
            SoilHazardKnowledge.model_validate(_row("clubroot", hosts=[host], non_hosts=[host]))

    def test_a_host_cannot_be_listed_twice(self) -> None:
        host = {"level": "genus", "name": "Allium", "evidence": _evidence(kind=None)}

        with pytest.raises(ValidationError, match="listed twice"):
            SoilHazardKnowledge.model_validate(_row("white_rot", hosts=[host, host]))

    def test_a_row_needs_at_least_one_host(self) -> None:
        with pytest.raises(ValidationError):
            SoilHazardKnowledge.model_validate(_row("clubroot", hosts=[]))

    def test_unknown_fields_are_refused(self) -> None:
        with pytest.raises(ValidationError):
            SoilHazardKnowledge.model_validate(_row("clubroot", affected_families=["Brassicaceae"]))

    def test_table_needs_every_hazard(self) -> None:
        rows = [_row(hazard.value) for hazard in SoilHazard if hazard is not SoilHazard.JUGLONE]

        with pytest.raises(ValidationError, match="without a row"):
            SoilHazardKnowledgeTable.model_validate({"hazards": rows})

    def test_table_refuses_a_duplicate_hazard(self) -> None:
        rows = [_row(hazard.value) for hazard in SoilHazard] + [_row("clubroot")]

        with pytest.raises(ValidationError, match="more than once"):
            SoilHazardKnowledgeTable.model_validate({"hazards": rows})

    def test_resolved_durations_follow_the_status(self) -> None:
        row = SoilHazardKnowledge.model_validate(
            _row(
                "verticillium",
                max_survival_years={"years": 10, "evidence": _evidence("insufficient", 2)},
                soft=True,
            )
        )

        resolved = SoilHazardKnowledgeEngine().resolve_durations(row)

        assert (resolved.soil_persistence_years, resolved.max_survival_years, resolved.soft) == (4, None, True)
        # The recorded kind of an unusable duration does not leak into the result.
        assert (resolved.soil_persistence_kind, resolved.max_survival_kind) == (EvidenceKind.NUMBER, None)
        assert row.max_survival_years.evidence.status is EvidenceStatus.INSUFFICIENT
