from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.enums import DiaryAnalysisState, DiaryEntryType


class DiaryFinding(BaseModel):
    """A single finding of an AI analysis of a diary entry (REQ-050 §5).

    The bounds are the contract an external agent has to satisfy
    (REQ-050 §4.5) — they are deliberately spelled out in both places, because a
    recipe written against §4 alone would otherwise run blind into
    ``validation.error``.
    """

    label: str = Field(max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(max_length=2000)


class DiaryAnalysis(BaseModel):
    """The most recent AI analysis result of a diary entry (REQ-050 §2.4, §5).

    Exactly one result is kept per entry: a re-analysis overwrites the previous
    one. A history would justify its own collection and is deferred (§9, O-01).

    ``disclaimer`` is set **server-side** and never taken from the agent
    (§4.5) — otherwise a recipe could omit or soften it, and the UI is required
    to display it unconditionally (AK-11, AK-20).
    """

    summary: str = Field(max_length=2000)
    findings: list[DiaryFinding] = Field(default_factory=list, max_length=10)
    recommended_actions: list[str] = Field(default_factory=list, max_length=10)
    analyzed_photo_ids: list[str] = Field(default_factory=list, max_length=5)
    model: str = Field(max_length=200)
    recipe_version: str = Field(max_length=50)
    analyzed_at: datetime
    disclaimer: str


class PlantDiaryEntry(BaseModel):
    """A diary entry for a plant instance, tracking observations, problems, and milestones."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    plant_key: str = ""
    entry_type: DiaryEntryType
    title: str | None = Field(default=None, max_length=200)
    text: str = Field(min_length=1, max_length=5000)
    #: REQ-013 §2.3 — at most five ``attachment_id`` references (never raw S3
    #: URLs; migration ``v0003`` normalised the legacy ones). The bound lives on
    #: the domain model and not only on the request schema, because REQ-050 §4.4
    #: turns every one of these into an image content block handed to an external
    #: language model: an unbounded list is an unbounded payload to assemble, and
    #: the §4.4 ceiling only decides what may *leave*, not what gets loaded.
    photo_refs: list[str] = Field(default_factory=list, max_length=5)
    tags: list[str] = Field(default_factory=list)
    measurements: dict | None = None
    created_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # ── REQ-050: AI analysis (additive, no data migration required) ───────────
    # Every field below is optional and defaults to today's behaviour, so a
    # document written before REQ-050 validates unchanged and round-trips through
    # the repository without acquiring a meaning it did not have (AK-26).
    analysis_state: DiaryAnalysisState = DiaryAnalysisState.NONE
    analysis_requested_at: datetime | None = None
    analysis_requested_by: str | None = None
    analysis_claimed_at: datetime | None = None
    analysis_claimed_by: str | None = None
    analysis_lease_expires_at: datetime | None = None
    analysis: DiaryAnalysis | None = None
    analysis_error: str | None = None

    model_config = {"populate_by_name": True}

    @field_validator("analysis_state", mode="before")
    @classmethod
    def _default_missing_analysis_state(cls, value: Any) -> Any:
        """Read a missing/``null`` ``analysis_state`` as ``none`` (AK-26).

        The default already covers the *absent* attribute of a pre-REQ-050
        document. An explicit stored ``null`` is a second, distinct case: the
        partial-update path writes with ``keep_none=True``
        (``BaseArangoRepository._update_doc_fields``), so a caller that resets an
        analysis field can leave ``analysis_state: null`` in the document. Without
        this coercion that document would stop validating and the entry would
        become unreadable — the opposite of what AK-26 promises.
        """
        return DiaryAnalysisState.NONE if value is None else value
