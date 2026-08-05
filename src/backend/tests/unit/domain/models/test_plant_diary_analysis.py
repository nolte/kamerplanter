"""Tests for the REQ-050 analysis fields on ``PlantDiaryEntry`` (#921, WP-1).

Three things are pinned here:

* **AK-26** — a document written before REQ-050 (no analysis attributes at all,
  and the second case of an explicitly stored ``null``) still validates, still
  serialises, and reads as ``analysis_state == none``. This is what makes the
  change additive: no data migration, no unreadable rows on an existing volume.
* **§5 / §4.5 length bounds** — every single one of them, because the numbers are
  the contract an external agent is validated against and a silently widened
  bound would only surface as an oversized document in the database.
* **``confidence`` outside 0.0–1.0 is rejected**, in both directions.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.common.enums import DiaryAnalysisState, DiaryEntryType
from app.domain.models.plant_diary_entry import DiaryAnalysis, DiaryFinding, PlantDiaryEntry

_ANALYZED_AT = datetime(2026, 8, 4, 7, 14, 52, tzinfo=UTC)

#: A diary entry exactly as it is stored on a volume that predates REQ-050:
#: not one analysis attribute present.
_LEGACY_DOC: dict = {
    "_key": "8271634",
    "tenant_key": "t1",
    "plant_key": "5512099",
    "entry_type": "problem",
    "title": "Braune Flecken unten",
    "text": "Seit dem Umtopfen hängen die unteren Blätter, Substrat riecht sauer.",
    "photo_refs": ["01HQ8X9V3J7P5K2N4M6T8R0S2W"],
    "tags": ["blatt", "substrat"],
    "measurements": {"height_cm": 84},
    "created_by": "4471023",
    "created_at": "2026-08-03T18:22:11Z",
    "updated_at": "2026-08-03T18:22:11Z",
}


def _finding(**overrides) -> dict:
    return {"label": "Staunässe", "confidence": 0.72, "rationale": "Saurer Substratgeruch.", **overrides}


def _analysis(**overrides) -> dict:
    return {
        "summary": "Vermutlich Staunässe nach dem Umtopfen.",
        "findings": [_finding()],
        "recommended_actions": ["Substrat abtrocknen lassen"],
        "analyzed_photo_ids": ["01HQ8X9V3J7P5K2N4M6T8R0S2W"],
        "model": "claude-opus-5",
        "recipe_version": "1.0.0",
        "analyzed_at": _ANALYZED_AT,
        "disclaimer": "Diese Einschätzung stammt von einem Sprachmodell.",
        **overrides,
    }


class TestLegacyDocumentsStayValid:
    """AK-26 — no migration needed for entries written before REQ-050."""

    def test_document_without_analysis_fields_validates(self):
        entry = PlantDiaryEntry(**_LEGACY_DOC)

        assert entry.key == "8271634"
        assert entry.text.startswith("Seit dem Umtopfen")

    def test_missing_analysis_state_reads_as_none(self):
        entry = PlantDiaryEntry(**_LEGACY_DOC)

        assert entry.analysis_state is DiaryAnalysisState.NONE
        assert entry.analysis_state == "none"

    def test_every_other_analysis_field_defaults_to_none(self):
        entry = PlantDiaryEntry(**_LEGACY_DOC)

        assert entry.analysis_requested_at is None
        assert entry.analysis_requested_by is None
        assert entry.analysis_claimed_at is None
        assert entry.analysis_claimed_by is None
        assert entry.analysis_lease_expires_at is None
        assert entry.analysis is None
        assert entry.analysis_error is None

    def test_explicit_null_analysis_state_reads_as_none(self):
        # The partial-update path writes with keep_none=True, so a stored null is
        # reachable; without the before-validator this document would stop
        # validating and the entry would become unreadable.
        entry = PlantDiaryEntry(**{**_LEGACY_DOC, "analysis_state": None})

        assert entry.analysis_state is DiaryAnalysisState.NONE

    def test_legacy_document_round_trips_through_serialisation(self):
        entry = PlantDiaryEntry(**_LEGACY_DOC)

        dumped = entry.model_dump(by_alias=True, mode="json")
        reloaded = PlantDiaryEntry(**dumped)

        assert reloaded.analysis_state is DiaryAnalysisState.NONE
        assert reloaded.text == entry.text
        assert reloaded.photo_refs == entry.photo_refs

    def test_repository_write_shape_drops_the_unset_analysis_fields(self):
        # ``BaseArangoRepository._to_doc`` dumps with exclude_none=True, so the
        # only analysis attribute a re-written legacy entry gains is the state
        # itself — the seven optional ones stay absent instead of littering the
        # document with nulls.
        entry = PlantDiaryEntry(**_LEGACY_DOC)

        dumped = entry.model_dump(by_alias=True, exclude_none=True, mode="json")

        assert dumped["analysis_state"] == "none"
        assert "analysis" not in dumped
        assert "analysis_requested_at" not in dumped
        assert "analysis_error" not in dumped

    def test_analysis_state_is_serialised_as_a_plain_string(self):
        # The stored value has to be the bare string the AQL filter binds, not a
        # repr of the enum member.
        entry = PlantDiaryEntry(**{**_LEGACY_DOC, "analysis_state": "requested"})

        assert entry.model_dump(mode="json")["analysis_state"] == "requested"


class TestAnalysisStateTransitionsAreRepresentable:
    @pytest.mark.parametrize(
        "state",
        ["none", "requested", "in_progress", "completed", "failed"],
    )
    def test_every_state_of_the_machine_is_accepted(self, state: str):
        entry = PlantDiaryEntry(**{**_LEGACY_DOC, "analysis_state": state})

        assert entry.analysis_state == state

    def test_unknown_state_is_rejected(self):
        with pytest.raises(ValidationError):
            PlantDiaryEntry(**{**_LEGACY_DOC, "analysis_state": "analysing"})

    def test_a_completed_entry_carries_the_full_result(self):
        entry = PlantDiaryEntry(
            **{
                **_LEGACY_DOC,
                "analysis_state": "completed",
                "analysis_requested_at": "2026-08-04T07:05:00Z",
                "analysis_requested_by": "4471023",
                "analysis_claimed_at": "2026-08-04T07:10:00Z",
                "analysis_claimed_by": "goose-laptop",
                "analysis_lease_expires_at": "2026-08-04T07:25:00Z",
                "analysis": _analysis(),
            }
        )

        assert entry.analysis is not None
        assert entry.analysis.findings[0].label == "Staunässe"
        assert entry.analysis.analyzed_at == _ANALYZED_AT
        assert entry.analysis_claimed_by == "goose-laptop"

    def test_a_failed_entry_carries_the_error_text_and_no_result(self):
        entry = PlantDiaryEntry(
            **{**_LEGACY_DOC, "analysis_state": "failed", "analysis_error": "model refused the image"}
        )

        assert entry.analysis is None
        assert entry.analysis_error == "model refused the image"


class TestFindingBounds:
    """REQ-050 §5 / §4.5 — the per-finding bounds."""

    def test_label_at_the_limit_is_accepted(self):
        assert DiaryFinding(**_finding(label="x" * 200)).label == "x" * 200

    def test_label_over_the_limit_is_rejected(self):
        with pytest.raises(ValidationError):
            DiaryFinding(**_finding(label="x" * 201))

    def test_rationale_at_the_limit_is_accepted(self):
        assert len(DiaryFinding(**_finding(rationale="y" * 2000)).rationale) == 2000

    def test_rationale_over_the_limit_is_rejected(self):
        with pytest.raises(ValidationError):
            DiaryFinding(**_finding(rationale="y" * 2001))

    @pytest.mark.parametrize("confidence", [0.0, 0.5, 1.0])
    def test_confidence_inside_the_range_is_accepted(self, confidence: float):
        assert DiaryFinding(**_finding(confidence=confidence)).confidence == confidence

    @pytest.mark.parametrize("confidence", [-0.01, -1.0, 1.01, 42.0])
    def test_confidence_outside_the_range_is_rejected(self, confidence: float):
        with pytest.raises(ValidationError):
            DiaryFinding(**_finding(confidence=confidence))

    def test_confidence_is_mandatory(self):
        payload = _finding()
        del payload["confidence"]
        with pytest.raises(ValidationError):
            DiaryFinding(**payload)


class TestAnalysisBounds:
    """REQ-050 §5 / §4.5 — the bounds on the result document itself."""

    def test_summary_at_the_limit_is_accepted(self):
        assert len(DiaryAnalysis(**_analysis(summary="s" * 2000)).summary) == 2000

    def test_summary_over_the_limit_is_rejected(self):
        with pytest.raises(ValidationError):
            DiaryAnalysis(**_analysis(summary="s" * 2001))

    def test_ten_findings_are_accepted(self):
        assert len(DiaryAnalysis(**_analysis(findings=[_finding()] * 10)).findings) == 10

    def test_eleven_findings_are_rejected(self):
        with pytest.raises(ValidationError):
            DiaryAnalysis(**_analysis(findings=[_finding()] * 11))

    def test_a_finding_bound_is_enforced_through_the_parent(self):
        # The nested bound must not be lost when the finding arrives as a plain
        # dict inside the analysis, which is how it comes off the wire.
        with pytest.raises(ValidationError):
            DiaryAnalysis(**_analysis(findings=[_finding(label="x" * 201)]))

    def test_ten_recommended_actions_are_accepted(self):
        assert len(DiaryAnalysis(**_analysis(recommended_actions=["a"] * 10)).recommended_actions) == 10

    def test_eleven_recommended_actions_are_rejected(self):
        with pytest.raises(ValidationError):
            DiaryAnalysis(**_analysis(recommended_actions=["a"] * 11))

    def test_five_analyzed_photo_ids_are_accepted(self):
        # Five is the ceiling because an entry carries at most five photos
        # (REQ-013 photo_refs).
        assert len(DiaryAnalysis(**_analysis(analyzed_photo_ids=["p"] * 5)).analyzed_photo_ids) == 5

    def test_six_analyzed_photo_ids_are_rejected(self):
        with pytest.raises(ValidationError):
            DiaryAnalysis(**_analysis(analyzed_photo_ids=["p"] * 6))

    def test_model_at_the_limit_is_accepted(self):
        assert len(DiaryAnalysis(**_analysis(model="m" * 200)).model) == 200

    def test_model_over_the_limit_is_rejected(self):
        with pytest.raises(ValidationError):
            DiaryAnalysis(**_analysis(model="m" * 201))

    def test_recipe_version_at_the_limit_is_accepted(self):
        assert len(DiaryAnalysis(**_analysis(recipe_version="v" * 50)).recipe_version) == 50

    def test_recipe_version_over_the_limit_is_rejected(self):
        with pytest.raises(ValidationError):
            DiaryAnalysis(**_analysis(recipe_version="v" * 51))

    @pytest.mark.parametrize("field", ["summary", "model", "recipe_version", "analyzed_at", "disclaimer"])
    def test_mandatory_fields_are_mandatory(self, field: str):
        payload = _analysis()
        del payload[field]
        with pytest.raises(ValidationError):
            DiaryAnalysis(**payload)

    def test_the_list_fields_default_to_empty(self):
        analysis = DiaryAnalysis(
            summary="Kein Befund.",
            model="claude-opus-5",
            recipe_version="1.0.0",
            analyzed_at=_ANALYZED_AT,
            disclaimer="Hypothese.",
        )

        assert analysis.findings == []
        assert analysis.recommended_actions == []
        assert analysis.analyzed_photo_ids == []

    def test_a_bound_violation_inside_the_entry_is_rejected(self):
        # The entry embeds the result, so the bounds must survive the nesting —
        # otherwise an oversized agent payload would only be caught (if at all) at
        # the tool boundary.
        with pytest.raises(ValidationError):
            PlantDiaryEntry(
                **{
                    **_LEGACY_DOC,
                    "analysis_state": "completed",
                    "analysis": _analysis(summary="s" * 2001),
                }
            )


class TestEntryStillBehavesAsBefore:
    def test_the_pre_existing_bounds_are_untouched(self):
        with pytest.raises(ValidationError):
            PlantDiaryEntry(**{**_LEGACY_DOC, "title": "t" * 201})
        with pytest.raises(ValidationError):
            PlantDiaryEntry(**{**_LEGACY_DOC, "text": ""})

    def test_a_minimal_new_entry_starts_unmarked(self):
        entry = PlantDiaryEntry(entry_type=DiaryEntryType.NOTE, text="Umgetopft.")

        assert entry.analysis_state is DiaryAnalysisState.NONE
        assert entry.analysis is None
