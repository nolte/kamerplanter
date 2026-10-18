"""REQ-053 WP 4.1 (#2400) — NFR-011 R-25 / R-26: the periods, the patch and the two sweeps.

The periods are read from :class:`RetentionService` only; the repository is the double below, so the loop
(batches until a short one, photos deleted, bounded runs) is decided here and the AQL against a real database
in ``tests/integration/test_care_event_repository.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.data_access.arango.care_event_repository import retention_patch
from app.domain.interfaces.care_event_repository import AnonymizedBatch
from app.domain.models.care_event import ACCOUNT_FIELDS, ANONYMIZED_MARKER, FREE_TEXT_FIELDS, REDACTED
from app.domain.services.garden_plan_retention_service import BATCH_SIZE, MAX_BATCHES, GardenPlanRetentionService
from app.domain.services.retention_service import RetentionService

NOW = datetime(2026, 10, 18, 4, 55, tzinfo=UTC)


class TestThePeriods:
    def test_a_care_event_is_kept_five_calendar_years(self) -> None:
        assert RetentionService().care_event_anonymisation_cutoff(NOW) == datetime(2021, 10, 18, 4, 55, tzinfo=UTC)

    def test_five_years_back_from_a_leap_day_is_not_a_day_short(self) -> None:
        leap = datetime(2028, 2, 29, 4, 55, tzinfo=UTC)

        assert RetentionService().care_event_anonymisation_cutoff(leap) == datetime(2023, 2, 28, 4, 55, tzinfo=UTC)

    def test_pest_control_follows_the_longer_of_the_two_periods(self) -> None:
        assert RetentionService().care_event_pflschg_cutoff(NOW) == datetime(2021, 10, 18, 4, 55, tzinfo=UTC)
        longer = RetentionService(treatment_retention_years=7)
        assert longer.care_event_pflschg_cutoff(NOW) == datetime(2019, 10, 18, 4, 55, tzinfo=UTC)
        assert longer.care_event_anonymisation_cutoff(NOW) == datetime(2021, 10, 18, 4, 55, tzinfo=UTC)

    def test_the_plan_audit_is_kept_a_year_from_the_change(self) -> None:
        assert RetentionService().garden_plan_audit_purge_cutoff(NOW) == NOW - timedelta(days=365)
        assert RetentionService(garden_plan_audit_retention_days=30).garden_plan_audit_purge_cutoff(
            NOW
        ) == NOW - timedelta(days=30)

    @pytest.mark.parametrize("years", [1, 4, 6, 10])
    def test_the_care_event_period_is_exactly_five_years(self, years) -> None:
        with pytest.raises(ValueError, match="R-25|RETENTION_CARE_EVENT"):
            RetentionService(care_event_retention_years=years)

    def test_the_plan_audit_period_has_a_floor_and_a_ceiling(self) -> None:
        for days in (0, 366):
            with pytest.raises(ValueError, match="R-26"):
                RetentionService(garden_plan_audit_retention_days=days)

    def test_the_settings_carry_the_same_bounds(self) -> None:
        from pydantic import ValidationError

        from app.config.settings import Settings

        assert Settings().retention_care_event_retention_years == 5
        assert Settings().retention_garden_plan_audit_retention_days == 365
        for field, value in (
            ("retention_care_event_retention_years", 4),
            ("retention_care_event_retention_years", 6),
            ("retention_garden_plan_audit_retention_days", 366),
        ):
            with pytest.raises(ValidationError):
                Settings(**{field: value})


class TestThePatch:
    DOC = {
        "_key": "ce_1",
        "performed_by_user_key": "u_sabine",
        "performed_for_user_key": "u_tom",
        "created_by": "u_sabine",
        "voided_by": "u_lead",
        "summary": "Frau Mueller",
        "reason": "x",
        "performed_by_label": "neighbour",
        "photo_refs": ["att_1"],
        "category": "watering",
        "quantity": 2.0,
    }

    def test_every_account_field_present_becomes_the_marker_and_every_text_is_redacted(self) -> None:
        patch = retention_patch(self.DOC, "2026-10-18T04:55:00+00:00")

        for name in ("performed_by_user_key", "performed_for_user_key", "created_by", "voided_by"):
            assert patch[name] == ANONYMIZED_MARKER
        for name in ("summary", "reason", "performed_by_label"):
            assert patch[name] == REDACTED
        assert patch["photo_refs"] == [] and patch["retention_anonymized_at"] == "2026-10-18T04:55:00+00:00"

    def test_what_the_look_back_needs_is_not_in_the_patch(self) -> None:
        patch = retention_patch(self.DOC, "2026-10-18T04:55:00+00:00")

        for kept in ("category", "performed_at", "quantity", "location_key", "plant_keys", "unit"):
            assert kept not in patch

    def test_an_absent_attribute_stays_absent_except_the_summary(self) -> None:
        patch = retention_patch({"_key": "ce_2"}, "t")

        assert set(patch) == {"_key", "retention_anonymized_at", "photo_refs", "summary"}

    def test_the_patch_covers_the_same_fields_as_the_redaction_and_the_erasure(self) -> None:
        full = {name: "x" for name in (*ACCOUNT_FIELDS, *FREE_TEXT_FIELDS)} | {"_key": "k"}

        patch = retention_patch(full, "t")

        assert {name for name in patch if name in ACCOUNT_FIELDS} == set(ACCOUNT_FIELDS)
        assert {name for name in patch if name in FREE_TEXT_FIELDS} == set(FREE_TEXT_FIELDS)

    def test_the_marker_is_the_one_the_erasure_writes(self) -> None:
        from app.data_access.arango.attachment_repository import ANONYMIZED_MARKER as ATTACHMENT_MARKER
        from app.domain.engines.erasure_engine import ANONYMIZED_MARKER as ERASURE_MARKER

        assert ANONYMIZED_MARKER == ERASURE_MARKER == ATTACHMENT_MARKER


class _CareRepo:
    def __init__(self, batches: list[AnonymizedBatch]) -> None:
        self.batches = batches
        self.calls: list[dict] = []

    def anonymize_expired(self, **kwargs):
        self.calls.append(kwargs)
        return self.batches.pop(0) if self.batches else AnonymizedBatch()


class _PlanRepo:
    def __init__(self, removed: list[int]) -> None:
        self.removed = removed
        self.calls: list[tuple[datetime, int]] = []

    def purge_audit_before(self, cutoff, *, batch):
        self.calls.append((cutoff, batch))
        return self.removed.pop(0) if self.removed else 0


class _Attachments:
    def __init__(self, kept: set[str] | None = None) -> None:
        self.kept = kept or set()
        self.deleted: list[tuple[str, str]] = []

    async def delete_if_unreferenced(self, attachment_id, tenant_key):
        if attachment_id in self.kept:
            return False
        self.deleted.append((tenant_key, attachment_id))
        return True


def service(care=None, plan=None, attachments=None) -> GardenPlanRetentionService:
    return GardenPlanRetentionService(
        care or _CareRepo([]), plan or _PlanRepo([]), attachments or _Attachments(), RetentionService()
    )


class TestTheCareEventSweep:
    async def test_it_works_in_batches_until_a_short_one_and_deletes_the_photos(self) -> None:
        full = AnonymizedBatch(anonymized=BATCH_SIZE, detached_photos=[("t1", "att_1")])
        short = AnonymizedBatch(anonymized=3, detached_photos=[("t2", "att_2"), ("t2", "att_3")])
        care, attachments = _CareRepo([full, short]), _Attachments(kept={"att_3"})

        result = await service(care, attachments=attachments).anonymize_expired_care_events(NOW)

        assert result == {"anonymized": BATCH_SIZE + 3, "photos_deleted": 2}
        assert len(care.calls) == 2
        assert attachments.deleted == [("t1", "att_1"), ("t2", "att_2")]

    async def test_the_cutoffs_come_from_the_retention_service(self) -> None:
        care = _CareRepo([])

        await service(care).anonymize_expired_care_events(NOW)

        (call,) = care.calls
        assert call["cutoff"] == datetime(2021, 10, 18, 4, 55, tzinfo=UTC)
        assert call["pflschg_cutoff"] == datetime(2021, 10, 18, 4, 55, tzinfo=UTC)
        assert call["batch"] == BATCH_SIZE and call["now"] == NOW

    async def test_a_run_is_bounded(self) -> None:
        care = _CareRepo([AnonymizedBatch(anonymized=BATCH_SIZE) for _ in range(MAX_BATCHES + 5)])

        result = await service(care).anonymize_expired_care_events(NOW)

        assert len(care.calls) == MAX_BATCHES
        assert result["anonymized"] == BATCH_SIZE * MAX_BATCHES


class TestThePlanAuditSweep:
    def test_it_purges_in_batches_until_a_short_one(self) -> None:
        plan = _PlanRepo([BATCH_SIZE, 7])

        assert service(plan=plan).purge_expired_garden_plan_audit(NOW) == BATCH_SIZE + 7
        assert [cutoff for cutoff, _ in plan.calls] == [NOW - timedelta(days=365)] * 2

    def test_nothing_due_is_one_call(self) -> None:
        plan = _PlanRepo([])

        assert service(plan=plan).purge_expired_garden_plan_audit(NOW) == 0
        assert len(plan.calls) == 1
