"""Winter reminders resolve a shared overwintering template when no per-instance
profile exists (REQ-022 — reusable templates, N:1)."""

from app.common.enums import HardinessRating, TuberStatus, WinterAction, WinterWatering
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate
from app.domain.services.care_reminder_service import CareReminderService, _template_to_profile

from .test_overwintering_profile_service import FakeOverwinteringRepo
from .test_overwintering_shared_template import FakeTemplateRepo, _template


class TestTemplateToProfile:
    def test_adapts_template_with_month(self):
        profile = _template_to_profile(_template(), "p1")
        assert isinstance(profile, OverwinteringProfile)
        assert profile.plant_key == "p1"
        assert profile.hardiness_rating == HardinessRating.FROST_FREE
        assert profile.winter_action_month == 9
        assert profile.winter_quarter_temp_min == 15

    def test_none_template_returns_none(self):
        assert _template_to_profile(None, "p1") is None

    def test_template_without_month_returns_none(self):
        """A house plant that simply stays indoors (winter_action none, no month)
        must not schedule a phantom winter-protection reminder."""
        tpl = OverwinteringProfileTemplate.model_validate(
            {
                "_key": "monstera_deliciosa",
                "species_scientific_name": "Monstera deliciosa",
                "hardiness_rating": HardinessRating.FROST_FREE,
                "winter_action": WinterAction.NONE,
                "winter_action_month": None,
            }
        )
        assert _template_to_profile(tpl, "p1") is None

    def test_dig_and_store_template_preserves_tuber_status(self):
        tpl = OverwinteringProfileTemplate.model_validate(
            {
                "_key": "solanum_tuberosum",
                "species_scientific_name": "Solanum tuberosum",
                "hardiness_rating": HardinessRating.DIG_AND_STORE,
                "winter_action": WinterAction.DIG_STORE,
                "winter_action_month": 10,
                "winter_watering": WinterWatering.NONE,
                "storage_check_interval_days": 30,
                "tuber_status": TuberStatus.STORED,
            }
        )
        profile = _template_to_profile(tpl, "p1")
        assert profile is not None
        assert profile.tuber_status == TuberStatus.STORED
        assert profile.storage_check_interval_days == 30


def _service(instance_repo=None, template_repo=None) -> CareReminderService:
    return CareReminderService(
        care_repo=None,
        engine=CareReminderEngine(),
        overwintering_repo=instance_repo,
        overwintering_template_repo=template_repo,
    )


class TestResolveOverwinteringProfile:
    def test_falls_back_to_shared_template(self):
        template_repo = FakeTemplateRepo([_template()])
        template_repo.link_subject("aechmea_fasciata", plant_key="p1")
        service = _service(instance_repo=FakeOverwinteringRepo(), template_repo=template_repo)
        resolved = service._resolve_overwintering_profile("p1")
        assert resolved is not None
        assert resolved.hardiness_rating == HardinessRating.FROST_FREE
        assert resolved.plant_key == "p1"

    def test_instance_profile_wins_over_template(self):
        instance_repo = FakeOverwinteringRepo()
        instance_repo.create_profile(
            OverwinteringProfile(
                plant_key="p1",
                hardiness_rating=HardinessRating.NEEDS_PROTECTION,
                winter_action=WinterAction.MULCH,
                winter_action_month=11,
            )
        )
        template_repo = FakeTemplateRepo([_template()])
        template_repo.link_subject("aechmea_fasciata", plant_key="p1")
        service = _service(instance_repo=instance_repo, template_repo=template_repo)
        resolved = service._resolve_overwintering_profile("p1")
        # The per-instance override, not the frost_free template.
        assert resolved.hardiness_rating == HardinessRating.NEEDS_PROTECTION

    def test_no_link_returns_none(self):
        service = _service(instance_repo=FakeOverwinteringRepo(), template_repo=FakeTemplateRepo([_template()]))
        assert service._resolve_overwintering_profile("p1") is None
