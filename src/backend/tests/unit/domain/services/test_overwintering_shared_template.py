"""Shared, reusable overwintering templates (REQ-022) — N subjects → 1 template.

Covers the service linking/resolution API and the auto-generation enrichment that
pulls species-accurate winter-quarter / storage values from the template, all with
in-memory fakes (no database).
"""

from types import SimpleNamespace

import pytest

from app.common.enums import (
    FrostTolerance,
    HardinessRating,
    TuberStatus,
    WinterAction,
    WinterWatering,
)
from app.common.exceptions import NotFoundError, ValidationError
from app.domain.interfaces.overwintering_profile_template_repository import (
    IOverwinteringProfileTemplateRepository,
)
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate
from app.domain.services.overwintering_profile_service import OverwinteringProfileService

from .test_overwintering_profile_service import FakeOverwinteringRepo

TENANT = "tenant_anna"


class FakeTemplateRepo(IOverwinteringProfileTemplateRepository):
    def __init__(self, templates: list[OverwinteringProfileTemplate] | None = None) -> None:
        self.by_key: dict[str, OverwinteringProfileTemplate] = {}
        for tpl in templates or []:
            self.by_key[tpl.key or tpl.species_scientific_name] = tpl
        #: subject-id ("plant/p1" | "run/r1") → template_key
        self.links: dict[str, str] = {}

    def get_template_by_key(self, key):
        return self.by_key.get(key)

    def get_template_by_species_key(self, species_key):
        return next((t for t in self.by_key.values() if t.species_key == species_key), None)

    def get_template_by_scientific_name(self, scientific_name):
        return next((t for t in self.by_key.values() if t.species_scientific_name == scientific_name), None)

    @staticmethod
    def _sid(plant_key, planting_run_key):
        return f"run/{planting_run_key}" if planting_run_key else (f"plant/{plant_key}" if plant_key else None)

    def link_subject(self, template_key, *, plant_key=None, planting_run_key=None):
        sid = self._sid(plant_key, planting_run_key)
        if sid is not None:
            self.links[sid] = template_key  # unique _from → replaces

    def get_template_for_subject(self, *, plant_key=None, planting_run_key=None):
        sid = self._sid(plant_key, planting_run_key)
        key = self.links.get(sid) if sid else None
        return self.by_key.get(key) if key else None

    def unlink_subject(self, *, plant_key=None, planting_run_key=None):
        sid = self._sid(plant_key, planting_run_key)
        return 1 if sid and self.links.pop(sid, None) is not None else 0

    def count_subjects(self, template_key):
        return sum(1 for v in self.links.values() if v == template_key)

    def list_links_for_tenant(self, tenant_key):
        out = []
        for sid, template_key in self.links.items():
            kind, _, key = sid.partition("/")
            plant_key = key if kind == "plant" else None
            planting_run_key = key if kind == "run" else None
            out.append((plant_key, planting_run_key, self.by_key[template_key]))
        return out


class FakePlantRepo:
    """Duck-typed plant repo: only ``get_by_key`` is exercised for ownership."""

    def __init__(self, plants: dict[str, str]) -> None:
        self._plants = plants  # plant_key → tenant_key

    def get_by_key(self, key):
        tenant = self._plants.get(key)
        return SimpleNamespace(tenant_key=tenant, species_key="sp1") if tenant else None


def _template(**overrides) -> OverwinteringProfileTemplate:
    data = {
        "_key": "aechmea_fasciata",
        "species_scientific_name": "Aechmea fasciata",
        "species_key": "sp1",
        "hardiness_rating": HardinessRating.FROST_FREE,
        "winter_action": WinterAction.MOVE_INDOORS,
        "winter_action_month": 9,
        "winter_quarter_temp_min": 15,
        "winter_quarter_temp_max": 20,
        "winter_watering": WinterWatering.REDUCED,
    }
    data.update(overrides)
    return OverwinteringProfileTemplate.model_validate(data)


def _service(templates=None, plants=None) -> OverwinteringProfileService:
    return OverwinteringProfileService(
        FakeOverwinteringRepo(),
        plant_repo=FakePlantRepo(plants or {"p1": TENANT, "p2": TENANT}),
        template_repo=FakeTemplateRepo(templates or [_template()]),
    )


class TestLinkSharedTemplate:
    def test_link_by_species_key(self):
        service = _service()
        tpl = service.link_shared_template(TENANT, plant_key="p1", species_key="sp1")
        assert tpl.key == "aechmea_fasciata"
        assert service.get_shared_template_for_subject(TENANT, plant_key="p1").key == "aechmea_fasciata"

    def test_one_template_reused_by_many_subjects(self):
        service = _service()
        service.link_shared_template(TENANT, plant_key="p1", species_key="sp1")
        service.link_shared_template(TENANT, plant_key="p2", species_key="sp1")
        repo = service._template_repo
        assert repo.count_subjects("aechmea_fasciata") == 2

    def test_link_by_scientific_name_fallback(self):
        service = _service()
        tpl = service.link_shared_template(TENANT, plant_key="p1", scientific_name="Aechmea fasciata")
        assert tpl.key == "aechmea_fasciata"

    def test_relink_replaces_previous(self):
        other = _template(_key="strelitzia_reginae", species_scientific_name="Strelitzia reginae", species_key="sp2")
        service = _service(templates=[_template(), other])
        service.link_shared_template(TENANT, plant_key="p1", species_key="sp1")
        service.link_shared_template(TENANT, plant_key="p1", species_key="sp2")
        assert service.get_shared_template_for_subject(TENANT, plant_key="p1").key == "strelitzia_reginae"
        assert service._template_repo.count_subjects("aechmea_fasciata") == 0

    def test_unknown_species_raises_not_found(self):
        service = _service()
        with pytest.raises(NotFoundError):
            service.link_shared_template(TENANT, plant_key="p1", species_key="does-not-exist")

    def test_requires_exactly_one_subject(self):
        service = _service()
        with pytest.raises(ValidationError):
            service.link_shared_template(TENANT, plant_key="p1", planting_run_key="r1", species_key="sp1")
        with pytest.raises(ValidationError):
            service.link_shared_template(TENANT, species_key="sp1")

    def test_cross_tenant_subject_rejected(self):
        service = _service(plants={"p1": "other_tenant"})
        with pytest.raises(NotFoundError):
            service.link_shared_template(TENANT, plant_key="p1", species_key="sp1")

    def test_unlink(self):
        service = _service()
        service.link_shared_template(TENANT, plant_key="p1", species_key="sp1")
        assert service.unlink_shared_template(TENANT, plant_key="p1") is True
        assert service.get_shared_template_for_subject(TENANT, plant_key="p1") is None
        assert service.unlink_shared_template(TENANT, plant_key="p1") is False


class TestAutoGenerateTemplateEnrichment:
    def test_relocation_path_uses_template_quarter(self):
        service = _service()
        profile = service.auto_generate_profile(
            TENANT, plant_key="p1", frost_sensitivity=FrostTolerance.SENSITIVE, species_key="sp1"
        )
        assert profile.winter_action == WinterAction.MOVE_INDOORS
        assert profile.winter_quarter_temp_min == 15
        assert profile.winter_quarter_temp_max == 20
        assert profile.winter_watering == WinterWatering.REDUCED

    def test_in_situ_path_ignores_template_quarter(self):
        service = _service()
        profile = service.auto_generate_profile(
            TENANT,
            plant_key="p1",
            frost_sensitivity=FrostTolerance.VERY_HARDY,
            species_zone="6a",
            site_zone="7a",
            species_key="sp1",
        )
        assert profile.winter_action == WinterAction.NONE
        # The curated indoor-quarter numbers must not leak onto a plant staying outside.
        assert profile.winter_quarter_temp_min is None
        assert profile.winter_quarter_temp_max is None

    def test_dig_store_path_copies_storage_and_tuber_status(self):
        tpl = _template(
            _key="solanum_tuberosum",
            species_scientific_name="Solanum tuberosum",
            species_key="sp1",
            hardiness_rating=HardinessRating.DIG_AND_STORE,
            winter_action=WinterAction.DIG_STORE,
            winter_quarter_temp_min=4,
            winter_quarter_temp_max=8,
            winter_watering=WinterWatering.NONE,
            storage_medium="dark cellar in crates",
            storage_check_interval_days=30,
            tuber_status=TuberStatus.STORED,
        )
        service = _service(templates=[tpl])
        profile = service.auto_generate_profile(
            TENANT,
            plant_key="p1",
            frost_sensitivity=FrostTolerance.SENSITIVE,
            is_geophyte=True,
            species_key="sp1",
        )
        assert profile.hardiness_rating == HardinessRating.DIG_AND_STORE
        assert profile.storage_medium == "dark cellar in crates"
        assert profile.storage_check_interval_days == 30
        assert profile.tuber_status == TuberStatus.STORED

    def test_no_template_repo_is_backward_compatible(self):
        service = OverwinteringProfileService(FakeOverwinteringRepo())  # no template_repo
        profile = service.auto_generate_profile(
            TENANT, plant_key="p1", frost_sensitivity=FrostTolerance.SENSITIVE, species_key="sp1"
        )
        assert profile.winter_action == WinterAction.MOVE_INDOORS
        assert profile.winter_quarter_temp_min is None


class TestHardinessOverviewSharedTemplates:
    def test_shared_linked_subject_counted(self):
        red = _template()  # frost_free → RED
        service = _service(templates=[red])
        service.link_shared_template(TENANT, plant_key="p1", species_key="sp1")
        overview = service.get_hardiness_overview(TENANT)
        assert overview.total == 1
        assert overview.red == 1
        assert overview.red_plants[0].plant_key == "p1"

    def test_instance_profile_overrides_shared_link_no_double_count(self):
        service = _service()
        # The same subject has both a per-instance profile AND a shared link.
        service._repo.create_profile(
            OverwinteringProfile(
                plant_key="p1",
                hardiness_rating=HardinessRating.HARDY,
                winter_action=WinterAction.NONE,
                winter_action_month=10,
                tenant_key=TENANT,
            )
        )
        service.link_shared_template(TENANT, plant_key="p1", species_key="sp1")
        overview = service.get_hardiness_overview(TENANT)
        assert overview.total == 1  # counted once (instance wins)

    def test_hardy_shared_template_counts_green(self):
        hardy = _template(
            _key="allium_sativum",
            species_scientific_name="Allium sativum",
            species_key="sp1",
            hardiness_rating=HardinessRating.HARDY,
            winter_action=WinterAction.MULCH,
            winter_quarter_temp_min=None,
            winter_quarter_temp_max=None,
            winter_watering=None,
        )
        service = _service(templates=[hardy])
        service.link_shared_template(TENANT, plant_key="p1", species_key="sp1")
        overview = service.get_hardiness_overview(TENANT)
        assert overview.green == 1
        assert overview.red == 0


def test_reuse_edge_registered():
    from app.data_access.arango import collections as col

    assert col.USES_OVERWINTERING_TEMPLATE == "uses_overwintering_template"
    assert col.USES_OVERWINTERING_TEMPLATE in col.EDGE_COLLECTIONS
    graph_edges = {d["edge_collection"] for d in col.GRAPH_EDGE_DEFINITIONS}
    assert col.USES_OVERWINTERING_TEMPLATE in graph_edges
