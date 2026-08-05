"""API tests for the tenant-wide diary overview (REQ-050 §2.5.2).

Covers the three things §2.5.2 says go wrong here:

* the row carries ``analysis_summary`` but **never** ``findings`` /
  ``recommended_actions`` (AK-18);
* ``can_request_analysis`` is evaluated server-side and is an *aid*, not an
  authorisation — a ``false`` row is still refused when actually marked (AK-18a);
* a filter for ``none`` must find the entries written before REQ-050, which
  carry no ``analysis_state`` attribute at all (AK-26).

Plus the filter/sort/paging contract, the ``null``-not-omitted rule and the
server-side 200-character excerpt.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.diary.schemas import EXCERPT_MAX_LENGTH
from app.api.v1.diary.tenant_router import router as diary_router
from app.api.v1.plant_instances.diary_router import router as plant_diary_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_plant_diary_service, get_plant_instance_service
from app.common.enums import DiaryAnalysisState, TenantRole
from app.common.exceptions import KamerplanterError
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.models.tenant_context import TenantContext
from app.domain.services.plant_diary_service import PlantDiaryService
from tests.support.diary_fakes import FakeDiaryRepository, FakePlantInstanceService

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"
AUTHOR = "user-author"
OTHER_USER = "user-other"
URL = f"/api/v1/t/{TENANT_SLUG}/diary"

COMPLETED_ANALYSIS = {
    "summary": "Vermutlich Staunässe nach dem Umtopfen, kein Pilzbefall erkennbar.",
    "findings": [
        {
            "label": "Staunässe / Wurzelstress",
            "confidence": 0.72,
            "rationale": "Saurer Substratgeruch und hängende untere Blätter.",
        }
    ],
    "recommended_actions": ["Substrat abtrocknen lassen", "Drainage prüfen"],
    "analyzed_photo_ids": ["photo-1"],
    "model": "claude-opus-5",
    "recipe_version": "1.0.0",
    "analyzed_at": "2026-08-04T07:14:52+00:00",
    "disclaimer": "Diese Einschätzung stammt von einem Sprachmodell.",
}


@pytest.fixture(autouse=True)
def _full_mode(monkeypatch):
    """Full mode, so §7.2 authorship really gates ``can_request_analysis``."""
    monkeypatch.setattr("app.domain.services.plant_diary_service.settings.kamerplanter_mode", "full")
    monkeypatch.setattr("app.domain.services.plant_diary_service.settings.jwt_secret_key", "api-test-secret-value")


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _plant(key: str, species_key: str = "solanum_lycopersicum", tenant_key: str = TENANT_KEY) -> PlantInstance:
    return PlantInstance(
        _key=key,
        tenant_key=tenant_key,
        instance_id=f"HOCHBEETA_{key.upper()}",
        species_key=species_key,
        plant_name=f"Tomate {key}",
        planted_on=date(2026, 4, 18),
    )


def _build(role: TenantRole = TenantRole.GROWER, user_key: str = AUTHOR):
    plants = {
        "plant-1": _plant("plant-1"),
        "plant-2": _plant("plant-2", species_key="ocimum_basilicum"),
    }
    # The repository double needs the plants too: the ``species_key`` filter is
    # a join in the real AQL, not a second lookup by the router.
    repo = FakeDiaryRepository(plants=plants)
    diary_service = PlantDiaryService(diary_repo=repo)
    plant_service = FakePlantInstanceService(
        plants=plants,
        species={
            "solanum_lycopersicum": Species(scientific_name="Solanum lycopersicum"),
            "ocimum_basilicum": Species(scientific_name="Ocimum basilicum"),
        },
    )

    app = FastAPI()
    app.include_router(diary_router, prefix="/api/v1/t/{tenant_slug}")
    app.include_router(plant_diary_router, prefix="/api/v1/t/{tenant_slug}")
    app.add_exception_handler(KamerplanterError, _error_handler)
    app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
        tenant_key=TENANT_KEY,
        tenant_slug=TENANT_SLUG,
        user_key=user_key,
        role=role,
    )
    app.dependency_overrides[get_plant_diary_service] = lambda: diary_service
    app.dependency_overrides[get_plant_instance_service] = lambda: plant_service
    return TestClient(app), repo


# ── Shape of the response (AK-15, AK-18) ─────────────────────────────────────


class TestOverviewShape:
    def test_row_carries_the_summary_but_never_the_findings(self):
        # AK-18 — a 50-row page must not ship 50 complete finding lists.
        client, repo = _build()
        repo.seed(
            "e1",
            plant_key="plant-1",
            photo_refs=["photo-1", "photo-2"],
            tags=["blatt", "substrat"],
            analysis_state=DiaryAnalysisState.COMPLETED.value,
            analysis=COMPLETED_ANALYSIS,
        )

        resp = client.get(URL)

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] == 1
        row = body["items"][0]
        assert row["analysis_summary"] == COMPLETED_ANALYSIS["summary"]
        assert row["analyzed_at"] is not None
        # The absence is the assertion: neither as a key on the row nor
        # anywhere in the serialised payload.
        assert "findings" not in row
        assert "recommended_actions" not in row
        assert "rationale" not in resp.text
        assert "Staunässe / Wurzelstress" not in resp.text
        assert "Drainage prüfen" not in resp.text

    def test_row_carries_the_plant_and_species_labels(self):
        # AK-15
        client, repo = _build()
        repo.seed("e1", plant_key="plant-1", photo_refs=["photo-1", "photo-2"], tags=["blatt"])

        row = client.get(URL).json()["items"][0]

        assert row["plant_key"] == "plant-1"
        assert row["plant_name"] == "Tomate plant-1"
        assert row["instance_id"] == "HOCHBEETA_PLANT-1"
        assert row["species_name"] == "Solanum lycopersicum"
        assert row["photo_count"] == 2
        assert row["preview_photo_id"] == "photo-1"
        assert row["tags"] == ["blatt"]

    def test_missing_values_are_null_not_omitted_keys(self):
        # §2.5.2 — the row shape stays identical across the page.
        client, repo = _build()
        repo.seed("e1", plant_key="plant-1", title=None)

        row = client.get(URL).json()["items"][0]

        for field in (
            "title",
            "analysis_summary",
            "analysis_error",
            "analysis_claimed_at",
            "analyzed_at",
            "preview_photo_id",
        ):
            assert field in row
            assert row[field] is None

    def test_excerpt_is_truncated_server_side(self):
        client, repo = _build()
        repo.seed("e1", plant_key="plant-1", text="x" * 900)

        row = client.get(URL).json()["items"][0]

        assert len(row["excerpt"]) == EXCERPT_MAX_LENGTH

    def test_an_empty_result_is_not_an_error(self):
        client, _repo = _build()

        resp = client.get(URL)

        assert resp.status_code == 200
        assert resp.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}

    def test_only_the_callers_tenant_is_listed(self):
        # AK-18, first sentence.
        client, repo = _build()
        repo.seed("own", plant_key="plant-1")
        repo.seed("foreign", tenant_key=FOREIGN_TENANT_KEY, plant_key="plant-1", text="Fremde Notiz")

        resp = client.get(URL)
        body = resp.json()

        assert [row["key"] for row in body["items"]] == ["own"]
        assert body["total"] == 1
        assert "Fremde" not in resp.text


# ── The moment of claiming (§2.5.2, `in_progress` row) ───────────────────────


def _as_utc(value: str | None) -> datetime | None:
    """Parse a serialised timestamp, whether it ends in ``Z`` or ``+00:00``."""
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class TestClaimTimestamp:
    def test_a_held_entry_carries_the_moment_it_was_claimed(self):
        # §2.5.2: the `in_progress` row reads "wird analysiert", *with* the
        # moment of claiming. Without this field the column could only say that
        # some agent has it, since when being the part a user actually asks.
        client, repo = _build()
        repo.seed(
            "held",
            plant_key="plant-1",
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_claimed_at="2026-08-04T07:10:00+00:00",
            analysis_claimed_by="goose-laptop",
            analysis_lease_expires_at="2099-01-01T00:00:00+00:00",
        )

        row = client.get(URL).json()["items"][0]

        assert row["analysis_state"] == "in_progress"
        assert _as_utc(row["analysis_claimed_at"]) == datetime(2026, 8, 4, 7, 10, tzinfo=UTC)
        # It is the *start* of the run, never the completion — confusing the two
        # would be worse than omitting the value.
        assert row["analyzed_at"] is None

    def test_a_run_out_lease_carries_no_claim_timestamp(self):
        # The decision this test pins down. The row's `analysis_state` is the
        # *displayed* one, so an expired lease reads as `requested` (AK-06).
        # Shipping the stored claim alongside would print a beginning of
        # analysis next to "wartet auf Analyse" — and this row carries neither
        # `analysis_claimed_by` nor `analysis_lease_expires_at`, so a reader has
        # nothing to resolve the contradiction with. The crashed-agent
        # diagnosis stays available on the single-entry read, which projects the
        # whole lease.
        client, repo = _build()
        repo.seed(
            "stale",
            plant_key="plant-1",
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_claimed_at="2026-08-04T07:10:00+00:00",
            analysis_claimed_by="goose-laptop",
            analysis_lease_expires_at="2020-01-01T00:00:00+00:00",
        )

        row = client.get(URL).json()["items"][0]

        assert row["analysis_state"] == "requested"
        # Suppressed as `null`, not as a missing key: the row shape stays the
        # same across the page (§2.5.2).
        assert "analysis_claimed_at" in row
        assert row["analysis_claimed_at"] is None
        # Reading did not write: the document is untouched, and the work queue
        # still finds the entry by its stored state.
        assert repo.docs["stale"]["analysis_claimed_at"] == "2026-08-04T07:10:00+00:00"
        assert repo.docs["stale"]["analysis_state"] == "in_progress"

    def test_a_completed_row_keeps_the_claim_of_the_run_it_shows(self):
        # `lease_expired` is false for every state but `in_progress`, so a
        # finished entry keeps the timestamp of exactly the run whose result the
        # row displays. Nothing here contradicts the state.
        client, repo = _build()
        repo.seed(
            "done",
            plant_key="plant-1",
            analysis_state=DiaryAnalysisState.COMPLETED.value,
            analysis_claimed_at="2026-08-04T07:10:00+00:00",
            analysis_claimed_by="goose-laptop",
            analysis_lease_expires_at="2026-08-04T07:25:00+00:00",
            analysis=COMPLETED_ANALYSIS,
        )

        row = client.get(URL).json()["items"][0]

        assert row["analysis_state"] == "completed"
        assert _as_utc(row["analysis_claimed_at"]) == datetime(2026, 8, 4, 7, 10, tzinfo=UTC)
        assert _as_utc(row["analyzed_at"]) == datetime(2026, 8, 4, 7, 14, 52, tzinfo=UTC)

    def test_re_marking_leaves_no_claim_timestamp_behind(self):
        # AK-21 — a repeat analysis puts the entry back to `requested`, and the
        # service clears the claim fields while doing so. The row must not show
        # the previous run's claim next to "wartet auf Analyse".
        client, repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)
        repo.seed(
            "again",
            plant_key="plant-1",
            created_by=AUTHOR,
            analysis_state=DiaryAnalysisState.COMPLETED.value,
            analysis_claimed_at="2026-08-04T07:10:00+00:00",
            analysis_claimed_by="goose-laptop",
            analysis=COMPLETED_ANALYSIS,
        )

        marked = client.post(f"/api/v1/t/{TENANT_SLUG}/plant-instances/plant-1/diary/again/request-analysis")
        assert marked.status_code == 200, marked.text

        row = client.get(URL).json()["items"][0]

        assert row["analysis_state"] == "requested"
        assert row["analysis_claimed_at"] is None
        # The previous *result* survives the re-marking on purpose (AK-21).
        assert row["analysis_summary"] == COMPLETED_ANALYSIS["summary"]


# ── can_request_analysis (AK-18a, AK-19) ─────────────────────────────────────


class TestCanRequestAnalysis:
    def test_true_for_the_author_with_write_access(self):
        client, repo = _build(role=TenantRole.GROWER, user_key=AUTHOR)
        repo.seed("e1", plant_key="plant-1", created_by=AUTHOR)

        assert client.get(URL).json()["items"][0]["can_request_analysis"] is True

    def test_false_for_a_viewer(self):
        client, repo = _build(role=TenantRole.VIEWER, user_key=AUTHOR)
        repo.seed("e1", plant_key="plant-1", created_by=AUTHOR)

        assert client.get(URL).json()["items"][0]["can_request_analysis"] is False

    def test_false_on_someone_elses_entry_for_a_grower(self):
        # AK-19 — foreign rows show the state but no switch.
        client, repo = _build(role=TenantRole.GROWER, user_key=OTHER_USER)
        repo.seed("e1", plant_key="plant-1", created_by=AUTHOR)

        assert client.get(URL).json()["items"][0]["can_request_analysis"] is False

    def test_true_on_someone_elses_entry_for_a_lead(self):
        client, repo = _build(role=TenantRole.LEAD, user_key=OTHER_USER)
        repo.seed("e1", plant_key="plant-1", created_by=AUTHOR)

        assert client.get(URL).json()["items"][0]["can_request_analysis"] is True

    def test_a_false_row_is_still_refused_when_marked(self):
        # AK-18a — the flag is a display aid, not the authorisation. A client
        # that ignores it (or a stale page) gets refused server-side.
        client, repo = _build(role=TenantRole.GROWER, user_key=OTHER_USER)
        repo.seed("e1", plant_key="plant-1", created_by=AUTHOR)
        assert client.get(URL).json()["items"][0]["can_request_analysis"] is False

        marked = client.post(f"/api/v1/t/{TENANT_SLUG}/plant-instances/plant-1/diary/e1/request-analysis")

        assert marked.status_code == 403, marked.text
        assert repo.docs["e1"]["analysis_state"] == "none"


# ── State filter, incl. the pre-REQ-050 documents (AK-17, AK-26) ─────────────


class TestAnalysisStateFilter:
    def test_pre_req050_entry_without_the_attribute_reads_as_none(self):
        # AK-26 — a missing attribute is ``null`` in AQL and never equal to
        # ``"none"``. A filter that did not expand for it would silently drop
        # exactly the entries that existed before the feature: the overview
        # would look empty on a real installation, without any error.
        client, repo = _build()
        legacy = repo.seed("legacy", plant_key="plant-1")
        legacy.pop("analysis_state")

        unfiltered = client.get(URL).json()
        assert [row["key"] for row in unfiltered["items"]] == ["legacy"]
        assert unfiltered["items"][0]["analysis_state"] == "none"

        filtered = client.get(URL, params={"analysis_state": "none"}).json()
        assert [row["key"] for row in filtered["items"]] == ["legacy"]
        assert filtered["total"] == 1

    def test_filter_for_completed_only(self):
        client, repo = _build()
        repo.seed("done", plant_key="plant-1", analysis_state=DiaryAnalysisState.COMPLETED.value)
        repo.seed("fresh", plant_key="plant-1")

        body = client.get(URL, params={"analysis_state": "completed"}).json()

        assert [row["key"] for row in body["items"]] == ["done"]
        assert body["total"] == 1

    def test_filter_accepts_several_states(self):
        client, repo = _build()
        repo.seed("done", plant_key="plant-1", analysis_state=DiaryAnalysisState.COMPLETED.value)
        repo.seed("failed", plant_key="plant-1", analysis_state=DiaryAnalysisState.FAILED.value)
        repo.seed("fresh", plant_key="plant-1")

        body = client.get(URL, params=[("analysis_state", "completed"), ("analysis_state", "failed")]).json()

        assert sorted(row["key"] for row in body["items"]) == ["done", "failed"]

    def test_a_run_out_lease_shows_and_filters_as_requested(self):
        # §2.2 / AK-06 — a crashed agent's entry is back in the queue. Filtering
        # for "nur wartend" must find it even though it is stored ``in_progress``.
        client, repo = _build()
        repo.seed(
            "stale",
            plant_key="plant-1",
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_claimed_by="goose-laptop",
            analysis_lease_expires_at="2020-01-01T00:00:00+00:00",
        )

        body = client.get(URL, params={"analysis_state": "requested"}).json()

        assert [row["key"] for row in body["items"]] == ["stale"]
        assert body["items"][0]["analysis_state"] == "requested"

    def test_a_live_lease_does_not_show_as_requested(self):
        client, repo = _build()
        repo.seed(
            "held",
            plant_key="plant-1",
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_claimed_by="goose-laptop",
            analysis_lease_expires_at="2099-01-01T00:00:00+00:00",
        )

        assert client.get(URL, params={"analysis_state": "requested"}).json()["total"] == 0
        held = client.get(URL, params={"analysis_state": "in_progress"}).json()
        assert [row["key"] for row in held["items"]] == ["held"]


# ── The remaining filters, sorting and paging (AK-17, AK-18) ─────────────────


class TestFiltersSortingAndPaging:
    def _seed_mixed(self, repo):
        repo.seed(
            "old",
            plant_key="plant-1",
            title="Umtopfen",
            text="Alles ruhig.",
            entry_type="observation",
            tags=["substrat"],
            created_at="2026-07-01T08:00:00+00:00",
        )
        repo.seed(
            "mid",
            plant_key="plant-2",
            title="Blattflecken",
            text="Braune Flecken unten.",
            entry_type="problem",
            tags=["Blatt"],
            created_at="2026-07-15T08:00:00+00:00",
            analysis_state=DiaryAnalysisState.COMPLETED.value,
            analysis=COMPLETED_ANALYSIS,
        )
        repo.seed(
            "new",
            plant_key="plant-1",
            title="Erste Blüte",
            text="Sieht gut aus.",
            entry_type="milestone",
            tags=[],
            created_at="2026-08-01T08:00:00+00:00",
        )

    def test_default_sort_is_created_at_descending(self):
        client, repo = _build()
        self._seed_mixed(repo)

        body = client.get(URL).json()

        assert [row["key"] for row in body["items"]] == ["new", "mid", "old"]

    def test_sort_by_analyzed_at_puts_unanalysed_rows_last(self):
        client, repo = _build()
        self._seed_mixed(repo)

        body = client.get(URL, params={"sort": "analyzed_at"}).json()

        assert body["items"][0]["key"] == "mid"
        assert body["total"] == 3

    def test_filter_by_plant(self):
        client, repo = _build()
        self._seed_mixed(repo)

        body = client.get(URL, params={"plant_key": "plant-2"}).json()

        assert [row["key"] for row in body["items"]] == ["mid"]

    def test_filter_by_species(self):
        client, repo = _build()
        self._seed_mixed(repo)

        body = client.get(URL, params={"species_key": "ocimum_basilicum"}).json()

        assert [row["key"] for row in body["items"]] == ["mid"]
        assert body["items"][0]["species_name"] == "Ocimum basilicum"

    def test_filter_by_entry_type(self):
        client, repo = _build()
        self._seed_mixed(repo)

        body = client.get(URL, params={"entry_type": "problem"}).json()

        assert [row["key"] for row in body["items"]] == ["mid"]

    def test_filter_by_tag_is_case_insensitive(self):
        client, repo = _build()
        self._seed_mixed(repo)

        body = client.get(URL, params={"tag": "blatt"}).json()

        assert [row["key"] for row in body["items"]] == ["mid"]

    def test_filter_by_date_range(self):
        client, repo = _build()
        self._seed_mixed(repo)

        body = client.get(URL, params={"from": "2026-07-10", "to": "2026-07-31"}).json()

        assert [row["key"] for row in body["items"]] == ["mid"]

    def test_free_text_search_covers_title_and_text(self):
        client, repo = _build()
        self._seed_mixed(repo)

        by_title = client.get(URL, params={"q": "blattflecken"}).json()
        assert [row["key"] for row in by_title["items"]] == ["mid"]

        by_text = client.get(URL, params={"q": "sieht gut"}).json()
        assert [row["key"] for row in by_text["items"]] == ["new"]

    def test_total_counts_every_match_across_pages(self):
        # AK-18 — ``total`` is independent of ``limit``.
        client, repo = _build()
        self._seed_mixed(repo)

        first = client.get(URL, params={"limit": 2}).json()
        assert first["total"] == 3
        assert first["limit"] == 2
        assert first["offset"] == 0
        assert [row["key"] for row in first["items"]] == ["new", "mid"]

        second = client.get(URL, params={"limit": 2, "offset": 2}).json()
        assert second["total"] == 3
        assert [row["key"] for row in second["items"]] == ["old"]

    def test_free_text_search_does_not_treat_wildcards_as_wildcards(self):
        # The search term goes into an AQL LIKE pattern. Unescaped, a term of
        # "%" matches every row and "_" matches any single character — a search
        # that looks like it works and silently answers a different question.
        client, repo = _build()
        repo.seed("percent", plant_key="plant-1", title="Rabatt", text="100% Bio-Substrat")
        repo.seed("underscore", plant_key="plant-1", title="Codename", text="Beet_A umgesetzt")
        repo.seed("plain", plant_key="plant-1", title="Ohne", text="Nichts Besonderes")

        by_percent = client.get(URL, params={"q": "100%"}).json()
        assert [row["key"] for row in by_percent["items"]] == ["percent"]
        assert by_percent["total"] == 1

        by_underscore = client.get(URL, params={"q": "Beet_A"}).json()
        assert [row["key"] for row in by_underscore["items"]] == ["underscore"]

        # A bare wildcard matches the one entry that literally contains it, not
        # all three.
        assert client.get(URL, params={"q": "%"}).json()["total"] == 1
        assert client.get(URL, params={"q": "_"}).json()["total"] == 1

    def test_two_filters_combine_conjunctively(self):
        client, repo = _build()
        self._seed_mixed(repo)
        repo.seed(
            "other-problem",
            plant_key="plant-1",
            title="Blattlaus",
            text="An Pflanze 1.",
            entry_type="problem",
            created_at="2026-07-20T08:00:00+00:00",
        )

        # entry_type AND plant: each alone matches two rows, together exactly one.
        assert client.get(URL, params={"entry_type": "problem"}).json()["total"] == 2
        assert client.get(URL, params={"plant_key": "plant-2"}).json()["total"] == 1
        both = client.get(URL, params={"entry_type": "problem", "plant_key": "plant-2"}).json()
        assert [row["key"] for row in both["items"]] == ["mid"]
        assert both["total"] == 1

    def test_state_and_date_range_combine(self):
        client, repo = _build()
        self._seed_mixed(repo)
        repo.seed(
            "old-done",
            plant_key="plant-1",
            created_at="2026-01-05T08:00:00+00:00",
            analysis_state=DiaryAnalysisState.COMPLETED.value,
            analysis=COMPLETED_ANALYSIS,
        )

        assert client.get(URL, params={"analysis_state": "completed"}).json()["total"] == 2
        combined = client.get(
            URL, params={"analysis_state": "completed", "from": "2026-07-01", "to": "2026-07-31"}
        ).json()
        assert [row["key"] for row in combined["items"]] == ["mid"]
        assert combined["total"] == 1

    def test_total_is_the_whole_match_count_not_the_page_length(self):
        # The failure this replaces reported a ``total`` derived from a scanned
        # window. With 120 matching entries and a page of 10, ``total`` is 120.
        client, repo = _build()
        for index in range(120):
            repo.seed(
                f"e{index:03d}",
                plant_key="plant-1",
                entry_type="note",
                created_at=f"2026-{(index % 12) + 1:02d}-{(index % 28) + 1:02d}T08:00:00+00:00",
            )

        body = client.get(URL, params={"limit": 10}).json()

        assert body["total"] == 120
        assert len(body["items"]) == 10

    def test_paging_walks_the_whole_set_without_losing_or_repeating_a_row(self):
        client, repo = _build()
        for index in range(25):
            repo.seed(f"e{index:02d}", plant_key="plant-1", created_at="2026-07-01T08:00:00+00:00")

        seen: list[str] = []
        for offset in range(0, 30, 10):
            page = client.get(URL, params={"limit": 10, "offset": offset}).json()
            assert page["total"] == 25
            seen.extend(row["key"] for row in page["items"])

        assert sorted(seen) == sorted(f"e{index:02d}" for index in range(25))

    def test_filters_apply_across_the_whole_set_not_within_one_page(self):
        # The failure mode this endpoint is most exposed to: narrowing a page
        # instead of the result set would return a short first page and a
        # ``total`` that counts rows the filter rejects.
        client, repo = _build()
        for index in range(30):
            repo.seed(
                f"noise-{index:02d}",
                plant_key="plant-1",
                entry_type="note",
                created_at=f"2026-07-{index + 1:02d}T08:00:00+00:00",
            )
        repo.seed(
            "needle",
            plant_key="plant-2",
            entry_type="problem",
            created_at="2026-06-01T08:00:00+00:00",  # oldest → last page by default
        )

        body = client.get(URL, params={"entry_type": "problem", "limit": 5}).json()

        assert body["total"] == 1
        assert [row["key"] for row in body["items"]] == ["needle"]
