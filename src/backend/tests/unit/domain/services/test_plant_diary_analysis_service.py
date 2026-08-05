"""REQ-050 §2.2 — the diary analysis state machine and its lease.

Solitary unit tests against an in-memory repository double. The double
implements the *contract* of ``IPlantDiaryRepository`` that matters here — a
revision that changes on every write, a compare-and-set that refuses a stale
one, and partial writes that keep ``None`` — so the tests exercise the state
machine rather than ArangoDB. That the real repository actually asks ArangoDB
for those semantics is proven separately in
``tests/unit/data_access/arango/test_plant_diary_repository.py``; a fake that
merely agrees with itself would prove nothing about either.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from app.common.enums import DiaryAnalysisState, DiaryEntryType, TenantRole
from app.common.exceptions import (
    ConsentRequiredError,
    DiaryAnalysisAlreadyClaimedError,
    DiaryAnalysisConcurrentUpdateError,
    DiaryAnalysisLeaseExpiredError,
    DiaryAnalysisNotClaimedError,
    DiaryAnalysisStateError,
    DiaryAnalysisValidationError,
    ForbiddenError,
    NotFoundError,
)
from app.data_access.arango.plant_diary_repository import analysis_state_bind_values
from app.domain.interfaces.plant_diary_repository import DiaryOverviewFilter
from app.domain.models.plant_diary_entry import PlantDiaryEntry
from app.domain.services import plant_diary_service as pds
from app.domain.services.plant_diary_service import (
    ANALYSIS_DISCLAIMER,
    MAX_LEASE_SECONDS,
    PlantDiaryService,
    effective_analysis_state,
)

TENANT = "tenant-a"
AUTHOR = "user-author"
OTHER_USER = "user-other"


class FakeDiaryRepository:
    """In-memory stand-in with a revision counter and CAS semantics.

    ``_rev`` moves on every write, ``update_fields_checked`` refuses a stale one,
    ``None`` values are written rather than dropped (``keep_none``) and a nested
    object replaces the stored one instead of merging into it (``merge=False``) —
    the three storage flags the state machine depends on.
    """

    def __init__(self) -> None:
        self.docs: dict[str, dict[str, Any]] = {}
        self._rev_counter = 0
        #: Hook fired after every read, to stage a concurrent writer.
        self.after_read: Any = None

    # ── helpers used by the tests ────────────────────────────────────────
    def seed(self, key: str, **fields: Any) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "_key": key,
            "tenant_key": TENANT,
            "plant_key": "plant-1",
            "entry_type": DiaryEntryType.PROBLEM.value,
            "text": "Braune Flecken unten",
            "created_by": AUTHOR,
            "photo_refs": ["photo-1", "photo-2"],
        }
        doc.update(fields)
        doc["_rev"] = self._next_rev()
        self.docs[key] = doc
        return doc

    def _next_rev(self) -> str:
        self._rev_counter += 1
        return f"rev-{self._rev_counter}"

    def bump_rev(self, key: str, **fields: Any) -> None:
        """Simulate a foreign writer touching the document."""
        doc = self.docs[key]
        doc.update(fields)
        doc["_rev"] = self._next_rev()

    # ── IPlantDiaryRepository (analysis subset) ──────────────────────────
    def get_with_revision(self, key: str) -> tuple[PlantDiaryEntry, str] | None:
        doc = self.docs.get(key)
        if doc is None:
            return None
        snapshot = PlantDiaryEntry(**dict(doc)), str(doc["_rev"])
        if self.after_read is not None:
            hook, self.after_read = self.after_read, None
            hook()
        return snapshot

    def update_fields_checked(
        self, key: str, fields: dict[str, Any], *, expected_rev: str
    ) -> tuple[PlantDiaryEntry, str]:
        doc = self.docs.get(key)
        if doc is None:
            raise NotFoundError("PlantDiaryEntry", key)
        if doc["_rev"] != expected_rev:
            raise DiaryAnalysisConcurrentUpdateError(key)
        doc.update(fields)  # keep_none: an explicit None is written
        doc["_rev"] = self._next_rev()
        return PlantDiaryEntry(**dict(doc)), str(doc["_rev"])

    def list_pending_analyses(
        self,
        tenant_key: str,
        *,
        limit: int = 20,
        include_stale: bool = True,
        now: datetime | None = None,
    ) -> tuple[list[PlantDiaryEntry], int]:
        moment = now or datetime.now(UTC)
        matches: list[dict[str, Any]] = []
        for doc in self.docs.values():
            if doc.get("tenant_key") != tenant_key:
                continue
            state = doc.get("analysis_state")
            if state == DiaryAnalysisState.REQUESTED.value:
                matches.append(doc)
            elif include_stale and state == DiaryAnalysisState.IN_PROGRESS.value:
                expires = doc.get("analysis_lease_expires_at")
                if expires is None or datetime.fromisoformat(expires) <= moment:
                    matches.append(doc)
        matches.sort(key=lambda doc: doc.get("analysis_requested_at") or "")
        entries = [PlantDiaryEntry(**dict(doc)) for doc in matches[:limit]]
        return entries, len(matches)

    def list_overview(
        self,
        tenant_key: str,
        filters: DiaryOverviewFilter | None = None,
        *,
        offset: int = 0,
        limit: int = 50,
        now: datetime | None = None,
    ) -> tuple[list[PlantDiaryEntry], int]:
        spec = filters or DiaryOverviewFilter()
        wanted = analysis_state_bind_values(spec.analysis_states) if spec.analysis_states else None
        matches = [
            doc
            for doc in self.docs.values()
            if doc.get("tenant_key") == tenant_key and (wanted is None or doc.get("analysis_state") in wanted)
        ]
        page = matches[offset : offset + limit]
        return [PlantDiaryEntry(**dict(doc)) for doc in page], len(matches)


@pytest.fixture(autouse=True)
def _strong_lease_secret(monkeypatch):
    """A configured secret, so lease tokens are stable within the test process."""
    monkeypatch.setattr("app.domain.services.plant_diary_service.settings.jwt_secret_key", "unit-test-secret-value")
    monkeypatch.setattr("app.domain.services.plant_diary_service.settings.kamerplanter_mode", "full")


@pytest.fixture
def repo() -> FakeDiaryRepository:
    return FakeDiaryRepository()


@pytest.fixture
def service(repo: FakeDiaryRepository) -> PlantDiaryService:
    return PlantDiaryService(diary_repo=repo)


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat()


def _claimed(repo: FakeDiaryRepository, key: str, *, worker: str = "goose-laptop", expires_in: int = 900) -> None:
    """Seed an entry that is already claimed, with a lease that may be stale."""
    now = datetime.now(UTC)
    repo.seed(
        key,
        analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
        analysis_requested_at=_iso(now - timedelta(minutes=30)),
        analysis_requested_by=AUTHOR,
        analysis_claimed_at=_iso(now - timedelta(seconds=max(0, -expires_in))),
        analysis_claimed_by=worker,
        analysis_lease_expires_at=_iso(now + timedelta(seconds=expires_in)),
    )


# ── Marking / un-marking (AK-01, AK-03, AK-21) ───────────────────────────────


class TestRequestAnalysis:
    def test_marks_a_fresh_entry(self, service, repo):
        repo.seed("d1")

        updated = service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        assert updated.analysis_state == DiaryAnalysisState.REQUESTED
        assert updated.analysis_requested_by == AUTHOR
        assert updated.analysis_requested_at is not None

    def test_marks_a_pre_req050_entry_without_state_attribute(self, service, repo):
        # AK-26: an entry written before REQ-050 has no analysis_state at all.
        doc = repo.seed("d1")
        doc.pop("analysis_state", None)

        updated = service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        assert updated.analysis_state == DiaryAnalysisState.REQUESTED

    def test_re_marks_a_completed_entry_keeping_the_old_result(self, service, repo):
        # AK-21: the previous result stays visible while the entry waits; it is
        # replaced only when a new result actually arrives.
        repo.seed(
            "d1",
            analysis_state=DiaryAnalysisState.COMPLETED.value,
            analysis={
                "summary": "old",
                "disclaimer": "x",
                "model": "m",
                "recipe_version": "1",
                "analyzed_at": _iso(datetime.now(UTC)),
            },
        )

        updated = service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        assert updated.analysis_state == DiaryAnalysisState.REQUESTED
        assert updated.analysis is not None
        assert updated.analysis.summary == "old"

    def test_re_marking_a_failed_entry_clears_the_previous_error(self, service, repo):
        repo.seed("d1", analysis_state=DiaryAnalysisState.FAILED.value, analysis_error="model timeout")

        updated = service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        assert updated.analysis_state == DiaryAnalysisState.REQUESTED
        assert updated.analysis_error is None

    def test_marking_an_already_marked_entry_is_refused(self, service, repo):
        repo.seed("d1", analysis_state=DiaryAnalysisState.REQUESTED.value)

        with pytest.raises(DiaryAnalysisStateError) as exc:
            service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        assert exc.value.error_code == "conflict.invalid_state"

    def test_foreign_tenant_entry_is_not_found_never_forbidden(self, service, repo):
        # AK-12: the error must not reveal that the entry exists elsewhere.
        repo.seed("d1", tenant_key="tenant-b")

        with pytest.raises(NotFoundError):
            service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.LEAD)


class TestCancelAnalysisRequest:
    def test_unmarking_while_requested_succeeds(self, service, repo):
        repo.seed(
            "d1",
            analysis_state=DiaryAnalysisState.REQUESTED.value,
            analysis_requested_at=_iso(datetime.now(UTC)),
            analysis_requested_by=AUTHOR,
        )

        updated = service.cancel_analysis_request("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        assert updated.analysis_state == DiaryAnalysisState.NONE
        assert updated.analysis_requested_at is None
        assert updated.analysis_requested_by is None

    def test_unmarking_while_in_progress_is_refused(self, service, repo):
        # AK-03: once an agent holds the entry the data has already left the
        # instance — "un-marking" would be a promise the server cannot keep.
        _claimed(repo, "d1")

        with pytest.raises(DiaryAnalysisStateError) as exc:
            service.cancel_analysis_request("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        assert exc.value.error_details["analysis_state"] == DiaryAnalysisState.IN_PROGRESS.value
        assert repo.docs["d1"]["analysis_state"] == DiaryAnalysisState.IN_PROGRESS.value


# ── §7.2 / §7.5 permission rule ──────────────────────────────────────────────


class TestMarkingPermission:
    def test_viewer_may_not_mark(self, service, repo):
        repo.seed("d1")

        with pytest.raises(ForbiddenError):
            service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.VIEWER)

    def test_grower_may_not_mark_a_foreign_entry(self, service, repo):
        repo.seed("d1")  # created_by == AUTHOR

        with pytest.raises(ForbiddenError):
            service.request_analysis("d1", tenant_key=TENANT, user_key=OTHER_USER, role=TenantRole.GROWER)

    def test_lead_may_mark_a_foreign_entry(self, service, repo):
        repo.seed("d1")

        updated = service.request_analysis("d1", tenant_key=TENANT, user_key=OTHER_USER, role=TenantRole.LEAD)

        assert updated.analysis_state == DiaryAnalysisState.REQUESTED

    def test_missing_consent_blocks_marking(self, repo):
        repo.seed("d1")
        service = PlantDiaryService(diary_repo=repo, consent_checker=lambda _user: False)

        with pytest.raises(ConsentRequiredError):
            service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

    def test_light_mode_drops_consent_and_authorship(self, repo, monkeypatch):
        # AK-25 / §7.5: nobody can grant a consent there, and every entry belongs
        # to the same system user.
        monkeypatch.setattr("app.domain.services.plant_diary_service.settings.kamerplanter_mode", "light")
        repo.seed("d1")
        service = PlantDiaryService(diary_repo=repo, consent_checker=lambda _user: False)

        updated = service.request_analysis("d1", tenant_key=TENANT, user_key=OTHER_USER, role=TenantRole.GROWER)

        assert updated.analysis_state == DiaryAnalysisState.REQUESTED

    def test_display_flag_and_enforcement_agree(self, service, repo):
        # AK-18a: one server-side rule feeds both the overview flag and the
        # enforcement, so they cannot drift apart.
        repo.seed("d1")
        entry, _rev = repo.get_with_revision("d1")

        assert service.evaluate_request_permission(entry, user_key=AUTHOR, role=TenantRole.GROWER).allowed is True
        denied = service.evaluate_request_permission(entry, user_key=OTHER_USER, role=TenantRole.GROWER)
        assert denied.allowed is False
        assert denied.reason == "authorship"
        with pytest.raises(ForbiddenError):
            service.request_analysis("d1", tenant_key=TENANT, user_key=OTHER_USER, role=TenantRole.GROWER)


# ── Claiming: the compare-and-set (AK-05) ────────────────────────────────────


class TestClaimAnalysis:
    def _requested(self, repo: FakeDiaryRepository, key: str = "d1") -> None:
        repo.seed(
            key,
            analysis_state=DiaryAnalysisState.REQUESTED.value,
            analysis_requested_at=_iso(datetime.now(UTC) - timedelta(minutes=5)),
            analysis_requested_by=AUTHOR,
        )

    def test_claim_sets_state_and_lease(self, service, repo):
        self._requested(repo)

        claim = service.claim_analysis("d1", tenant_key=TENANT, worker_id="goose-laptop", lease_seconds=900)

        assert claim.entry.analysis_state == DiaryAnalysisState.IN_PROGRESS
        assert claim.entry.analysis_claimed_by == "goose-laptop"
        assert claim.lease_token
        assert claim.lease_expires_at > datetime.now(UTC)
        assert claim.photo_count == 2

    def test_second_claim_fails_and_leaves_the_state_untouched(self, service, repo):
        # AK-05. The second agent must not get the entry, and must not damage
        # the first one's claim on its way out.
        self._requested(repo)
        first = service.claim_analysis("d1", tenant_key=TENANT, worker_id="agent-a")
        state_after_first = dict(repo.docs["d1"])

        with pytest.raises(DiaryAnalysisAlreadyClaimedError) as exc:
            service.claim_analysis("d1", tenant_key=TENANT, worker_id="agent-b")

        assert exc.value.error_code == "conflict.already_claimed"
        assert exc.value.error_details["claimed_by"] == "agent-a"
        assert exc.value.error_details["lease_expires_at"] is not None
        assert repo.docs["d1"] == state_after_first
        # ... and the first agent's token still works.
        assert service._lease_token_matches(first.entry, first.lease_token) is True

    def test_revision_change_between_read_and_write_is_a_concurrent_update(self, service, repo):
        # The other half of AK-05: both agents saw `requested`, so both pass the
        # state check — only the compare-and-set separates them. The loser gets
        # `conflict.concurrent_update` (retry now), NOT `already_claimed`
        # (come back later); an agent reacts differently to each.
        self._requested(repo)
        repo.after_read = lambda: repo.bump_rev(
            "d1",
            analysis_state=DiaryAnalysisState.IN_PROGRESS.value,
            analysis_claimed_by="agent-b",
            analysis_lease_expires_at=_iso(datetime.now(UTC) + timedelta(seconds=900)),
        )

        with pytest.raises(DiaryAnalysisConcurrentUpdateError) as exc:
            service.claim_analysis("d1", tenant_key=TENANT, worker_id="agent-a")

        assert exc.value.error_code == "conflict.concurrent_update"
        assert repo.docs["d1"]["analysis_claimed_by"] == "agent-b"

    def test_claiming_a_completed_entry_is_already_claimed(self, service, repo):
        repo.seed("d1", analysis_state=DiaryAnalysisState.COMPLETED.value)

        with pytest.raises(DiaryAnalysisAlreadyClaimedError):
            service.claim_analysis("d1", tenant_key=TENANT, worker_id="agent-a")

    def test_empty_worker_id_is_rejected(self, service, repo):
        self._requested(repo)

        with pytest.raises(DiaryAnalysisValidationError) as exc:
            service.claim_analysis("d1", tenant_key=TENANT, worker_id="   ")

        assert exc.value.error_code == "validation.error"

    def test_lease_seconds_above_the_ceiling_is_rejected(self, service, repo):
        self._requested(repo)

        with pytest.raises(DiaryAnalysisValidationError):
            service.claim_analysis("d1", tenant_key=TENANT, worker_id="a", lease_seconds=MAX_LEASE_SECONDS + 1)

    def test_two_claims_yield_different_tokens(self, service, repo):
        # A re-claim must invalidate the previous token: the derivation is bound
        # to the live lease, so the old holder cannot submit afterwards.
        self._requested(repo)
        first = service.claim_analysis("d1", tenant_key=TENANT, worker_id="agent-a", lease_seconds=1)
        repo.bump_rev("d1", analysis_lease_expires_at=_iso(datetime.now(UTC) - timedelta(seconds=1)))
        second = service.claim_analysis("d1", tenant_key=TENANT, worker_id="agent-b")

        assert first.lease_token != second.lease_token


# ── Lease expiry (AK-06) ─────────────────────────────────────────────────────


class TestExpiredLease:
    def test_stale_entry_is_back_in_the_work_queue(self, service, repo):
        _claimed(repo, "d1", expires_in=-60)

        entries, total = service.list_pending_analyses(TENANT, include_stale=True)

        assert total == 1
        assert entries[0].key == "d1"

    def test_stale_entry_is_hidden_when_include_stale_is_off(self, service, repo):
        _claimed(repo, "d1", expires_in=-60)

        entries, total = service.list_pending_analyses(TENANT, include_stale=False)

        assert (entries, total) == ([], 0)

    def test_stale_entry_is_claimable_again(self, service, repo):
        _claimed(repo, "d1", worker="crashed-agent", expires_in=-60)

        claim = service.claim_analysis("d1", tenant_key=TENANT, worker_id="fresh-agent")

        assert claim.entry.analysis_state == DiaryAnalysisState.IN_PROGRESS
        assert claim.entry.analysis_claimed_by == "fresh-agent"

    def test_write_access_actually_clears_the_dead_lease(self, service, repo):
        # The trap: the full-model write drops None (exclude_none=True), so a
        # lease "reset" that way leaves the crashed agent's name on the document
        # while everybody is free to claim it. The fields must be gone for real.
        _claimed(repo, "d1", worker="crashed-agent", expires_in=-60)

        service.cancel_analysis_request("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        doc = repo.docs["d1"]
        assert doc["analysis_claimed_by"] is None
        assert doc["analysis_claimed_at"] is None
        assert doc["analysis_lease_expires_at"] is None
        assert doc["analysis_state"] == DiaryAnalysisState.NONE.value

    def test_effective_state_reports_requested_without_writing(self, repo):
        _claimed(repo, "d1", expires_in=-60)
        entry, _rev = repo.get_with_revision("d1")

        assert effective_analysis_state(entry) == DiaryAnalysisState.REQUESTED
        assert repo.docs["d1"]["analysis_state"] == DiaryAnalysisState.IN_PROGRESS.value


# ── Submitting a result (AK-10, AK-11, AK-21, AK-22) ─────────────────────────


class TestSubmitAnalysis:
    def _claim(self, service, repo, *, worker: str = "goose-laptop", lease_seconds: int = 900):
        repo.seed(
            "d1",
            analysis_state=DiaryAnalysisState.REQUESTED.value,
            analysis_requested_at=_iso(datetime.now(UTC)),
            analysis_requested_by=AUTHOR,
        )
        return service.claim_analysis("d1", tenant_key=TENANT, worker_id=worker, lease_seconds=lease_seconds)

    def test_completed_persists_the_result(self, service, repo):
        claim = self._claim(service, repo)

        updated = service.submit_analysis(
            "d1",
            tenant_key=TENANT,
            lease_token=claim.lease_token,
            status="completed",
            summary="Vermutlich Staunässe nach dem Umtopfen.",
            findings=[{"label": "Staunässe", "confidence": 0.72, "rationale": "Saurer Substratgeruch"}],
            recommended_actions=["Substrat abtrocknen lassen"],
            analyzed_photo_ids=["photo-1"],
            model="claude-opus-5",
            recipe_version="1.0.0",
        )

        assert updated.analysis_state == DiaryAnalysisState.COMPLETED
        assert updated.analysis is not None
        assert updated.analysis.findings[0].confidence == 0.72
        assert updated.analysis_lease_expires_at is None
        # Provenance survives the submission (§7.3/§7.4 anonymise it, so it must
        # still be there to anonymise).
        assert updated.analysis_claimed_by == "goose-laptop"

    def test_disclaimer_is_set_even_though_the_agent_sent_none(self, service, repo):
        # AK-11 — the whole reason the server owns this field.
        claim = self._claim(service, repo)

        updated = service.submit_analysis(
            "d1",
            tenant_key=TENANT,
            lease_token=claim.lease_token,
            status="completed",
            summary="Kein Pilzbefall erkennbar.",
            model="m",
            recipe_version="1",
        )

        assert updated.analysis is not None
        assert updated.analysis.disclaimer == ANALYSIS_DISCLAIMER

    def test_failed_records_the_error_and_keeps_the_previous_result(self, service, repo):
        claim = self._claim(service, repo)
        service.submit_analysis(
            "d1",
            tenant_key=TENANT,
            lease_token=claim.lease_token,
            status="completed",
            summary="Erste Einschätzung",
            model="m",
            recipe_version="1",
        )
        service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)
        second = service.claim_analysis("d1", tenant_key=TENANT, worker_id="goose-laptop")

        updated = service.submit_analysis(
            "d1",
            tenant_key=TENANT,
            lease_token=second.lease_token,
            status="failed",
            error="model timeout after 3 retries",
        )

        assert updated.analysis_state == DiaryAnalysisState.FAILED
        assert updated.analysis_error == "model timeout after 3 retries"
        assert updated.analysis is not None and updated.analysis.summary == "Erste Einschätzung"

    def test_re_analysis_replaces_the_previous_result_wholesale(self, service, repo):
        # AK-21: no findings are merged in from the earlier run.
        claim = self._claim(service, repo)
        service.submit_analysis(
            "d1",
            tenant_key=TENANT,
            lease_token=claim.lease_token,
            status="completed",
            summary="Erste Einschätzung",
            findings=[{"label": "Pilzbefall", "confidence": 0.9, "rationale": "weiße Flecken"}],
            recommended_actions=["Fungizid prüfen"],
            model="m",
            recipe_version="1",
        )
        service.request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)
        second = service.claim_analysis("d1", tenant_key=TENANT, worker_id="goose-laptop")

        updated = service.submit_analysis(
            "d1",
            tenant_key=TENANT,
            lease_token=second.lease_token,
            status="completed",
            summary="Zweite Einschätzung",
            model="m",
            recipe_version="2",
        )

        assert updated.analysis is not None
        assert updated.analysis.summary == "Zweite Einschätzung"
        assert updated.analysis.findings == []
        assert updated.analysis.recommended_actions == []

    def test_submitting_an_unclaimed_entry_is_not_claimed(self, service, repo):
        repo.seed("d1", analysis_state=DiaryAnalysisState.REQUESTED.value)

        with pytest.raises(DiaryAnalysisNotClaimedError) as exc:
            service.submit_analysis("d1", tenant_key=TENANT, lease_token="whatever", status="completed", summary="x")

        assert exc.value.error_code == "conflict.not_claimed"

    def test_wrong_token_is_lease_expired(self, service, repo):
        self._claim(service, repo)

        with pytest.raises(DiaryAnalysisLeaseExpiredError) as exc:
            service.submit_analysis(
                "d1", tenant_key=TENANT, lease_token="forged-token", status="completed", summary="x"
            )

        assert exc.value.error_code == "conflict.lease_expired"
        assert repo.docs["d1"]["analysis_state"] == DiaryAnalysisState.IN_PROGRESS.value

    def test_expired_lease_is_rejected_and_the_lease_is_freed(self, service, repo):
        claim = self._claim(service, repo)
        repo.bump_rev("d1", analysis_lease_expires_at=_iso(datetime.now(UTC) - timedelta(seconds=1)))

        with pytest.raises(DiaryAnalysisLeaseExpiredError):
            service.submit_analysis(
                "d1",
                tenant_key=TENANT,
                lease_token=claim.lease_token,
                status="completed",
                summary="zu spät",
            )

        doc = repo.docs["d1"]
        assert doc["analysis_state"] == DiaryAnalysisState.REQUESTED.value
        assert doc["analysis_claimed_by"] is None
        assert doc["analysis_lease_expires_at"] is None


class TestSubmitValidation:
    """Every AK-22 case on its own — a shared "invalid payload" test would not
    tell which rule is actually enforced."""

    @pytest.fixture
    def claim(self, service, repo):
        repo.seed(
            "d1",
            analysis_state=DiaryAnalysisState.REQUESTED.value,
            analysis_requested_at=_iso(datetime.now(UTC)),
            analysis_requested_by=AUTHOR,
        )
        return service.claim_analysis("d1", tenant_key=TENANT, worker_id="goose-laptop")

    def _submit(self, service, claim, **kwargs):
        payload = {
            "tenant_key": TENANT,
            "lease_token": claim.lease_token,
            "status": "completed",
            "model": "m",
            "recipe_version": "1",
        }
        payload.update(kwargs)
        return service.submit_analysis("d1", **payload)

    def test_completed_without_summary(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError) as exc:
            self._submit(service, claim, summary=None)
        assert exc.value.error_code == "validation.error"

    def test_failed_without_error(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(service, claim, status="failed", error=None)

    def test_summary_too_long(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(service, claim, summary="x" * 2001)

    def test_confidence_out_of_range(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(
                service,
                claim,
                summary="ok",
                findings=[{"label": "l", "confidence": 1.2, "rationale": "r"}],
            )

    def test_too_many_findings(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(
                service,
                claim,
                summary="ok",
                findings=[{"label": "l", "confidence": 0.5, "rationale": "r"}] * 11,
            )

    def test_finding_label_too_long(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(
                service,
                claim,
                summary="ok",
                findings=[{"label": "x" * 201, "confidence": 0.5, "rationale": "r"}],
            )

    def test_too_many_recommended_actions(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(service, claim, summary="ok", recommended_actions=["a"] * 11)

    def test_photo_id_not_attached_to_the_entry(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError) as exc:
            self._submit(service, claim, summary="ok", analyzed_photo_ids=["photo-9"])
        assert exc.value.error_details["field"] == "analyzed_photo_ids"

    def test_too_many_photo_ids(self, service, repo, claim):
        # Every id hangs on the entry, so the "unknown id" rule cannot be what
        # fires — only ``DiaryAnalysis.analyzed_photo_ids``' max_length of 5
        # (§4.5). They are repeats of one reference because an entry itself now
        # carries at most five photos (REQ-013 §2.3, enforced on the domain model
        # since SEC-003), so six *distinct* attached photos cannot exist.
        repo.docs["d1"]["photo_refs"] = ["photo-1"]
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(service, claim, summary="ok", analyzed_photo_ids=["photo-1"] * 6)

    def test_model_name_too_long(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(service, claim, summary="ok", model="m" * 201)

    def test_unknown_status(self, service, claim):
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(service, claim, status="in_progress", summary="ok")

    def test_a_rejected_payload_leaves_the_lease_intact(self, service, repo, claim):
        with pytest.raises(DiaryAnalysisValidationError):
            self._submit(service, claim, summary=None)

        assert repo.docs["d1"]["analysis_state"] == DiaryAnalysisState.IN_PROGRESS.value
        # The agent may fix the payload and submit again with the same token.
        updated = self._submit(service, claim, summary="korrigiert")
        assert updated.analysis_state == DiaryAnalysisState.COMPLETED


# ── Work queue (AK-04, AK-26) ────────────────────────────────────────────────


class TestWorkQueue:
    def test_orders_by_request_time_and_counts_beyond_the_limit(self, service, repo):
        now = datetime.now(UTC)
        for index, minutes in enumerate([5, 30, 1]):
            repo.seed(
                f"d{index}",
                analysis_state=DiaryAnalysisState.REQUESTED.value,
                analysis_requested_at=_iso(now - timedelta(minutes=minutes)),
            )

        entries, total = service.list_pending_analyses(TENANT, limit=1)

        assert total == 3, "total must count every waiting entry, not the page"
        assert [entry.key for entry in entries] == ["d1"], "oldest request first"

    def test_other_tenants_are_invisible(self, service, repo):
        repo.seed("d1", analysis_state=DiaryAnalysisState.REQUESTED.value, tenant_key="tenant-b")

        assert service.list_pending_analyses(TENANT) == ([], 0)

    def test_limit_above_the_ceiling_is_rejected(self, service):
        with pytest.raises(DiaryAnalysisValidationError):
            service.list_pending_analyses(TENANT, limit=101)

    def test_legacy_entry_is_not_pending_but_is_found_as_unmarked(self, service, repo):
        # The trap in one test: a pre-REQ-050 document carries no analysis_state
        # attribute at all. It must not show up as waiting for analysis, but a
        # "not marked" filter has to find it (AK-26) — an `== 'none'` filter
        # would silently skip exactly these entries.
        doc = repo.seed("legacy")
        doc.pop("analysis_state", None)

        assert service.list_pending_analyses(TENANT) == ([], 0)

        entries, total = service.list_overview(TENANT, DiaryOverviewFilter(analysis_states=(DiaryAnalysisState.NONE,)))
        assert total == 1
        assert entries[0].key == "legacy"
        assert entries[0].analysis_state == DiaryAnalysisState.NONE


# ── The generic update path must not touch analysis state (Befund 6) ─────────


def test_generic_update_cannot_write_analysis_fields(repo):
    class _CapturingRepo(FakeDiaryRepository):
        def get_or_raise(self, key: str) -> PlantDiaryEntry:
            return PlantDiaryEntry(**dict(self.docs[key]))

        def update(self, key: str, entry: PlantDiaryEntry) -> PlantDiaryEntry:
            self.captured = entry
            return entry

    capturing = _CapturingRepo()
    capturing.seed("d1", analysis_state=DiaryAnalysisState.REQUESTED.value)
    service = PlantDiaryService(diary_repo=capturing)

    result = service.update_entry(
        "d1",
        {
            "text": "korrigierter Text",
            "analysis_state": DiaryAnalysisState.COMPLETED.value,
            "analysis_claimed_by": "attacker",
        },
        tenant_key="tenant-a",
        user_key="user-author",
        actor_role=TenantRole.GROWER,
    )

    assert result.text == "korrigierter Text"
    assert result.analysis_state == DiaryAnalysisState.REQUESTED
    assert result.analysis_claimed_by is None


def test_generic_update_is_tenant_scoped(repo):
    """SEC-002/SEC-003 — the update refuses a foreign entry on its own.

    The routers already scope the load, but the service is the layer every
    caller shares. ``NotFoundError`` and never a permission error, so the
    endpoint cannot be used as an oracle (AK-12).
    """
    repo.seed("d1", tenant_key="tenant-b")

    with pytest.raises(NotFoundError):
        PlantDiaryService(diary_repo=repo).update_entry(
            "d1",
            {"text": "übernommen"},
            tenant_key="tenant-a",
            user_key="user-author",
            actor_role=TenantRole.GROWER,
        )

    assert repo.docs["d1"]["text"] == "Braune Flecken unten"


# ── SEC-009 — how the lease-signing secret is resolved and separated ──────────


class TestLeaseSigningSecret:
    """The documented chain is ``jwt_secret_key`` → ``fernet_key`` → ephemeral.

    Written as ``settings.jwt_secret_key or settings.fernet_key`` it silently
    lost its middle link: the shipped placeholder is a *truthy* first operand, so
    ``or`` short-circuits before the comparison and ``fernet_key`` is never
    reached. An instance that had left ``JWT_SECRET_KEY`` untouched but
    configured a Fernet key therefore signed every lease with a process-local
    secret — invalid after a restart and different on every replica.
    """

    @staticmethod
    def _set(monkeypatch, *, jwt: str, fernet: str) -> None:
        monkeypatch.setattr("app.domain.services.plant_diary_service.settings.jwt_secret_key", jwt)
        monkeypatch.setattr("app.domain.services.plant_diary_service.settings.fernet_key", fernet)
        # The ephemeral fallback is memoised for the process; clear it so a test
        # measures this configuration and not a leftover from the previous one.
        pds._ephemeral_lease_secret.cache_clear()

    def test_the_fernet_key_is_reached_when_the_jwt_secret_is_the_placeholder(self, monkeypatch):
        self._set(monkeypatch, jwt=pds._KNOWN_DEFAULT_JWT_SECRET, fernet="a-configured-fernet-key")

        assert pds._lease_signing_secret() == "a-configured-fernet-key"

    def test_the_fernet_key_is_reached_when_the_jwt_secret_is_empty(self, monkeypatch):
        self._set(monkeypatch, jwt="", fernet="a-configured-fernet-key")

        assert pds._lease_signing_secret() == "a-configured-fernet-key"

    def test_a_strong_jwt_secret_still_wins(self, monkeypatch):
        self._set(monkeypatch, jwt="a-strong-jwt-secret", fernet="a-configured-fernet-key")

        assert pds._lease_signing_secret() == "a-strong-jwt-secret"

    def test_neither_configured_falls_back_to_the_ephemeral_secret(self, monkeypatch):
        self._set(monkeypatch, jwt=pds._KNOWN_DEFAULT_JWT_SECRET, fernet="")

        secret = pds._lease_signing_secret()

        assert secret not in ("", pds._KNOWN_DEFAULT_JWT_SECRET)
        # Stable within the process, so a claim and its submit agree.
        assert secret == pds._lease_signing_secret()

    def test_the_derivation_is_domain_separated(self, monkeypatch):
        """The same key in a second protocol must not produce the same digest.

        The signing secret is shared (the local-fs download tokens resolve the
        same chain), so the payload carries a purpose label. Asserted against a
        plain HMAC over the unlabelled payload — the shape the derivation had.
        """
        import hashlib
        import hmac

        self._set(monkeypatch, jwt="a-strong-jwt-secret", fernet="")
        claimed_at = datetime(2026, 8, 4, 7, 10, tzinfo=UTC)
        expires_at = datetime(2026, 8, 4, 7, 25, tzinfo=UTC)

        token = pds.derive_lease_token(
            entry_key="d1",
            claimed_by="goose-laptop",
            claimed_at=claimed_at,
            lease_expires_at=expires_at,
        )

        unlabelled_payload = "|".join(["d1", "goose-laptop", claimed_at.isoformat(), expires_at.isoformat()])
        unlabelled = hmac.new(b"a-strong-jwt-secret", unlabelled_payload.encode("utf-8"), hashlib.sha256).hexdigest()

        assert token != unlabelled
        # …and the token is still deterministic for one lease, which is what the
        # submit path compares against.
        assert token == pds.derive_lease_token(
            entry_key="d1",
            claimed_by="goose-laptop",
            claimed_at=claimed_at,
            lease_expires_at=expires_at,
        )
