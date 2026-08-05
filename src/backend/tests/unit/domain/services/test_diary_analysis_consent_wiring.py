"""REQ-050 §7.1 / §7.5 — the ``diary_ai_analysis`` consent, as actually wired.

``test_plant_diary_analysis_service.py`` proves the *rule* with a hand-injected
checker. This module proves the **wiring**: it builds the service through the
real provider ``app.common.dependencies.get_plant_diary_service`` and answers the
consent question from the real :class:`ConsentGuard` + :class:`ConsentEngine`
over a consent-store double. Without that, a green rule test would say nothing
about a service that still carries the ``_consent_not_evaluated`` placeholder —
which is exactly what it did until this work package.

Only the two repositories are doubled (diary + consent); the guard, the engine
and the purpose registry are the production objects.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common import dependencies as deps
from app.common.enums import DiaryAnalysisState, TenantRole
from app.common.exceptions import ConsentRequiredError
from app.domain.engines.consent_engine import DIARY_AI_ANALYSIS
from app.domain.models.privacy import ConsentRecord
from app.domain.services.plant_diary_service import _consent_not_evaluated
from tests.unit.domain.services.test_plant_diary_analysis_service import (
    AUTHOR,
    TENANT,
    FakeDiaryRepository,
)


class FakeConsentRepository:
    """Consent store double that counts its reads.

    Holds at most one record per (user, purpose) — the shape
    ``ArangoConsentRepository.get_by_user_and_purpose`` returns.
    """

    def __init__(self) -> None:
        self.records: dict[tuple[str, str], ConsentRecord] = {}
        self.reads = 0

    def grant(self, user_key: str, purpose: str = DIARY_AI_ANALYSIS) -> None:
        self.records[(user_key, purpose)] = ConsentRecord(
            user_key=user_key,
            purpose=purpose,
            granted=True,
            granted_at=datetime.now(UTC),
        )

    def revoke(self, user_key: str, purpose: str = DIARY_AI_ANALYSIS) -> None:
        """Revoke as the production path does: keep the record, flip the flag."""
        self.records[(user_key, purpose)] = ConsentRecord(
            user_key=user_key,
            purpose=purpose,
            granted=False,
            granted_at=datetime.now(UTC),
            revoked_at=datetime.now(UTC),
        )

    def get_by_user_and_purpose(self, user_key: str, purpose: str) -> ConsentRecord | None:
        self.reads += 1
        return self.records.get((user_key, purpose))


@pytest.fixture
def diary_repo() -> FakeDiaryRepository:
    return FakeDiaryRepository()


@pytest.fixture
def consent_repo() -> FakeConsentRepository:
    return FakeConsentRepository()


@pytest.fixture
def build_service(monkeypatch, diary_repo, consent_repo):
    """Return a factory that builds the service exactly like a request does."""
    monkeypatch.setattr(deps, "get_plant_diary_repo", lambda: diary_repo)
    monkeypatch.setattr(deps, "get_consent_repo", lambda: consent_repo)
    monkeypatch.setattr(deps, "get_planting_run_repo", lambda: MagicMock())
    monkeypatch.setattr(deps, "get_plant_repo", lambda: MagicMock())
    # SEC-003 — the provider resolves the attachment catalogue too now. Left
    # unpatched it opens a real ArangoDB connection, which is not what this
    # module is about (and takes the connection timeout to find out).
    monkeypatch.setattr(deps, "get_attachment_repo", lambda: MagicMock())
    return deps.get_plant_diary_service


def _completed_entry(repo: FakeDiaryRepository, key: str) -> None:
    """Seed an entry that already carries a finished analysis result."""
    repo.seed(
        key,
        analysis_state=DiaryAnalysisState.COMPLETED.value,
        analysis_requested_by=AUTHOR,
        analysis={
            "summary": "Mangelverdacht Stickstoff",
            "findings": [],
            "recommended_actions": [],
            "analyzed_photo_ids": [],
            "model": "some-model",
            "recipe_version": "1.0",
            "analyzed_at": datetime.now(UTC).isoformat(),
            "disclaimer": "Kein Ersatz für eine fachliche Diagnose.",
        },
    )


class TestConsentIsWiredAtAll:
    def test_provider_injects_a_real_checker(self, build_service):
        """The placeholder must be gone — it answered ``True`` unconditionally."""
        service = build_service()

        assert service._consent_checker is not _consent_not_evaluated

    def test_checker_asks_the_consent_store(self, build_service, consent_repo, diary_repo):
        diary_repo.seed("d1")
        service = build_service()
        entry, _rev = diary_repo.get_with_revision("d1")

        service.evaluate_request_permission(entry, user_key=AUTHOR, role=TenantRole.GROWER)

        assert consent_repo.reads == 1


class TestMarkingFollowsConsent:
    def test_marking_is_refused_without_and_succeeds_after_granting(self, build_service, consent_repo, diary_repo):
        """AK-13, both halves."""
        diary_repo.seed("d1")

        with pytest.raises(ConsentRequiredError) as exc:
            build_service().request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)
        assert exc.value.error_code == "CONSENT_REQUIRED"
        assert diary_repo.docs["d1"].get("analysis_state") is None

        consent_repo.grant(AUTHOR)
        # A fresh request builds a fresh service — like the next HTTP call.
        updated = build_service().request_analysis("d1", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        assert updated.analysis_state == DiaryAnalysisState.REQUESTED
        assert updated.analysis_requested_by == AUTHOR

    def test_revocation_blocks_new_marking_and_keeps_the_existing_result(self, build_service, consent_repo, diary_repo):
        """AK-13 / AK-25 — a withdrawal is not a deletion order.

        Both halves are asserted on the same store: the marking of a fresh entry
        is refused, *and* the analysis of an entry that was analysed while the
        consent stood is still there, byte for byte. A revocation that dropped
        existing results would be data loss without a legal basis.
        """
        consent_repo.grant(AUTHOR)
        _completed_entry(diary_repo, "done")
        diary_repo.seed("fresh")
        stored_before = dict(diary_repo.docs["done"]["analysis"])

        consent_repo.revoke(AUTHOR)
        service = build_service()

        with pytest.raises(ConsentRequiredError):
            service.request_analysis("fresh", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)
        # Re-marking the analysed entry is a *new* marking and is refused too.
        with pytest.raises(ConsentRequiredError):
            service.request_analysis("done", tenant_key=TENANT, user_key=AUTHOR, role=TenantRole.GROWER)

        assert diary_repo.docs["done"]["analysis"] == stored_before
        assert diary_repo.docs["done"]["analysis_state"] == DiaryAnalysisState.COMPLETED.value
        # Reading the result stays possible without consent.
        assert build_service().get_entry_for_tenant("done", TENANT).analysis.summary == stored_before["summary"]

    def test_light_mode_marks_without_any_consent(self, build_service, consent_repo, diary_repo, monkeypatch):
        """AK-25 / §7.5 — no one can grant there, so the purpose counts as granted.

        The probe is *not* short-circuited: it still asks the store and still
        answers ``False``. The exemption lives in the permission rule, where §7.5
        puts it — the distinction matters, because the opposite implementation
        would also silently exempt ``ai_cloud_processing``-style purposes that
        REQ-027 blocks hard in Light mode.
        """
        monkeypatch.setattr("app.domain.services.plant_diary_service.settings.kamerplanter_mode", "light")
        diary_repo.seed("d1")
        service = build_service()

        updated = service.request_analysis("d1", tenant_key=TENANT, user_key="system", role=TenantRole.GROWER)

        assert updated.analysis_state == DiaryAnalysisState.REQUESTED
        assert consent_repo.reads >= 1
        assert consent_repo.records == {}


class TestDisplayFlagFollowsConsent:
    def test_can_request_analysis_mirrors_the_consent_state(self, build_service, consent_repo, diary_repo):
        """AK-18a — the overview flag and the enforcement share one rule."""
        diary_repo.seed("d1")
        entry, _rev = diary_repo.get_with_revision("d1")

        denied = build_service().evaluate_request_permission(entry, user_key=AUTHOR, role=TenantRole.GROWER)
        assert denied.allowed is False
        assert denied.reason == "consent"

        consent_repo.grant(AUTHOR)
        allowed = build_service().evaluate_request_permission(entry, user_key=AUTHOR, role=TenantRole.GROWER)
        assert allowed.allowed is True
        assert allowed.reason is None

    def test_consent_is_read_once_per_service_not_once_per_row(self, build_service, consent_repo, diary_repo):
        """The overview evaluates the rule per row — that must not be N queries."""
        consent_repo.grant(AUTHOR)
        for key in ("d1", "d2", "d3"):
            diary_repo.seed(key)
        service = build_service()

        for key in ("d1", "d2", "d3"):
            entry, _rev = diary_repo.get_with_revision(key)
            assert service.evaluate_request_permission(entry, user_key=AUTHOR, role=TenantRole.GROWER).allowed

        assert consent_repo.reads == 1
