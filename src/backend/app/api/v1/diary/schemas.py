"""REQ-050 §2.5.2 — schemas of the tenant-wide diary overview.

The overview row is deliberately **not** ``DiaryEntryResponse``. It carries from
the analysis result only the summary; ``findings`` and ``recommended_actions``
never appear here (AK-18). A page of 50 rows would otherwise ship 50 complete
finding lists with their rationales — up to 10 findings of 2000 characters each,
per row — for a view that shows one line of it. The full result is what the
single-entry read is for.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import DiaryAnalysisState, DiaryEntryType

#: Maximum length of the server-side excerpt of ``text`` (§2.5.2).
EXCERPT_MAX_LENGTH = 200


class DiaryOverviewItem(BaseModel):
    """One row of the tenant-wide diary overview (REQ-050 §2.5.2)."""

    key: str
    # §5/§2.5.2 spell this ``datetime``; it is nullable here because the domain
    # model is (``PlantDiaryEntry.created_at: datetime | None``) and a single
    # legacy document without a timestamp must not turn the whole page into a
    # 500. Rendering it as ``null`` is the same promise AK-26 makes for the
    # missing ``analysis_state``.
    created_at: datetime | None
    entry_type: DiaryEntryType
    title: str | None
    #: Beginning of ``text``, truncated **server-side** — the client is not
    #: trusted to shorten what it was sent, and sending the full text would
    #: defeat the point of the slim row.
    excerpt: str = Field(max_length=EXCERPT_MAX_LENGTH)
    tags: list[str]

    plant_key: str
    plant_name: str | None
    instance_id: str
    species_name: str | None

    photo_count: int
    preview_photo_id: str | None

    analysis_state: DiaryAnalysisState
    #: The summary only — never ``findings`` or ``recommended_actions`` (AK-18).
    analysis_summary: str | None
    analysis_error: str | None
    #: When an agent took the entry, for the ``in_progress`` row §2.5.2 asks to
    #: show "wird analysiert" *with* that moment. Not ``analyzed_at``: this is
    #: the start of the lease, that one is the completion of the run.
    #:
    #: **It carries the claim of the run the row's state describes, and nothing
    #: else.** ``analysis_state`` here is the *displayed* state, so an entry
    #: whose lease has run out reads as ``requested`` — and this field is
    #: ``null`` for it, even though the document still stores a claim. The
    #: alternative would put a beginning-of-analysis next to "wartet auf
    #: Analyse" on a row that carries neither ``analysis_claimed_by`` nor
    #: ``analysis_lease_expires_at``, leaving a reader no way to tell the
    #: contradiction from a rendering bug. The crashed-agent diagnosis is not
    #: lost by that: the single-entry read (``DiaryEntryResponse``) projects all
    #: three lease fields raw, which is where "claimed by X, expired at Y" is
    #: legible as a whole. A ``completed`` or ``failed`` row keeps its value —
    #: it is the claim of exactly the run whose outcome the row shows.
    analysis_claimed_at: datetime | None
    analyzed_at: datetime | None

    #: §7.2 evaluated **server-side** (AK-18a). A display aid, not an
    #: authorisation: marking re-evaluates the same rule and refuses a row whose
    #: flag says ``false``, whatever the client believed.
    can_request_analysis: bool

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "8271634",
                    "created_at": "2026-08-03T18:22:11Z",
                    "entry_type": "problem",
                    "title": "Braune Flecken unten",
                    "excerpt": "Seit dem Umtopfen hängen die unteren Blätter, Substrat riecht sauer.",
                    "tags": ["blatt", "substrat"],
                    "plant_key": "5512099",
                    "plant_name": "Tomate Beet 2 #05",
                    "instance_id": "HOCHBEETA_TOM_05",
                    "species_name": "Solanum lycopersicum",
                    "photo_count": 2,
                    "preview_photo_id": "01HQ8X9V3J7P5K2N4M6T8R0S2W",
                    "analysis_state": "completed",
                    "analysis_summary": "Vermutlich Staunässe nach dem Umtopfen, kein Pilzbefall erkennbar.",
                    "analysis_error": None,
                    "analysis_claimed_at": "2026-08-04T07:10:00Z",
                    "analyzed_at": "2026-08-04T07:14:52Z",
                    "can_request_analysis": True,
                }
            ]
        }
    )


class DiaryOverviewResponse(BaseModel):
    """A page of the tenant-wide diary overview (REQ-050 §2.5.2, AK-18)."""

    items: list[DiaryOverviewItem]
    #: Matches across **all** pages, independent of ``limit``. An empty result is
    #: not an error: ``items: []`` with ``total: 0``.
    total: int
    limit: int
    offset: int

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [],
                    "total": 137,
                    "limit": 50,
                    "offset": 0,
                }
            ]
        }
    )
