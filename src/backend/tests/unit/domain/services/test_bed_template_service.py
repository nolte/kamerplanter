"""REQ-053 WP 7.8 (#2474) - the bed-template service: who may read and write which row, and the references.

The repository is the in-memory double of ``tests/support/bed_template_fakes.py``. Every refusal test also asserts
that nothing was written: a refusal that still wrote is the defect, not the status code (SR-010, SR-013).
"""

from __future__ import annotations

import pytest
from structlog.testing import capture_logs

from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, PlanError, PlanValidationError
from app.domain.models.bed_template import (
    MAX_TEMPLATES_PER_TENANT,
    BedTemplate,
    BedTemplateInput,
    BedTemplatePatch,
)
from app.domain.services.bed_template_service import BedTemplateService
from tests.support.bed_template_fakes import FakeTemplates

TENANT = "ten_own"
OTHER = "ten_other"
USER = "u_sabine"
_RECT = {"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 0}


def _template(key: str, tenant: str | None, name: str = "Bed") -> BedTemplate:
    return BedTemplate(_key=key, tenant_key=tenant, name=name, location_type_key="bed", default_geometry=_RECT)


def _input(**overrides) -> BedTemplateInput:
    return BedTemplateInput(
        **{"name": "Herb bed", "location_type_key": "raised_bed", "default_geometry": _RECT, **overrides}
    )


@pytest.fixture
def world() -> tuple[BedTemplateService, FakeTemplates]:
    repo = FakeTemplates()
    repo.add(_template("sys_bed", None, "A system bed"))
    repo.add(_template("own", TENANT, "Own bed"))
    repo.add(_template("theirs", OTHER, "Their bed"))
    repo.task_templates = {"tt_global": "", "tt_own": TENANT, "tt_foreign": OTHER}
    return BedTemplateService(repo), repo


class TestReading:
    def test_the_list_holds_the_system_templates_and_the_tenants_own_never_another_tenants(self, world) -> None:
        service, _ = world

        listed = service.list_templates(tenant_key=TENANT, offset=0, limit=50)

        assert [t.key for t in listed] == ["sys_bed", "own"]

    def test_the_list_is_a_window(self, world) -> None:
        service, _ = world

        assert [t.key for t in service.list_templates(tenant_key=TENANT, offset=1, limit=1)] == ["own"]

    def test_another_tenants_template_answers_404_like_an_absent_one(self, world) -> None:
        service, _ = world

        with pytest.raises(NotFoundError) as foreign:
            service.get_template("theirs", tenant_key=TENANT)
        with pytest.raises(NotFoundError) as absent:
            service.get_template("nope", tenant_key=TENANT)

        assert foreign.value.status_code == absent.value.status_code == 404
        assert foreign.value.message.replace("theirs", "x") == absent.value.message.replace("nope", "x")


class TestCreating:
    def test_a_grower_creates_a_template_of_the_tenant_stamped_with_the_author(self, world) -> None:
        service, repo = world

        created = service.create_template(tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER, data=_input())

        assert (created.tenant_key, created.created_by, created.is_system) == (TENANT, USER, False)
        assert repo.templates[created.key or ""] is created

    def test_a_viewer_creates_nothing(self, world) -> None:
        service, repo = world

        with pytest.raises(ForbiddenError):
            service.create_template(tenant_key=TENANT, user_key=USER, role=TenantRole.VIEWER, data=_input())

        assert repo.writes == []

    def test_the_location_type_must_exist(self, world) -> None:
        service, repo = world

        with pytest.raises(PlanValidationError) as refused:
            service.create_template(
                tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER, data=_input(location_type_key="nope")
            )

        assert refused.value.codes == ["reference.not_found"]
        assert repo.writes == []

    def test_the_location_type_must_be_a_bed_type(self, world) -> None:
        service, repo = world

        with pytest.raises(PlanError) as refused:
            service.create_template(
                tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER, data=_input(location_type_key="greenhouse")
            )

        assert (refused.value.error_code, refused.value.status_code) == ("bed_template.not_a_bed_type", 422)
        assert repo.writes == []

    def test_a_task_template_of_another_tenant_cannot_be_parked_on_a_template(self, world) -> None:
        service, repo = world

        with pytest.raises(PlanValidationError) as refused:
            service.create_template(
                tenant_key=TENANT,
                user_key=USER,
                role=TenantRole.GROWER,
                data=_input(recurring_task_templates=["tt_global", "tt_foreign", "tt_own", "tt_absent"]),
            )

        details = refused.value.details
        assert [d["field"] for d in details] == ["recurring_task_templates[1]", "recurring_task_templates[3]"]
        assert repo.writes == []

    def test_a_global_and_an_own_task_template_are_accepted(self, world) -> None:
        service, _ = world

        created = service.create_template(
            tenant_key=TENANT,
            user_key=USER,
            role=TenantRole.GROWER,
            data=_input(recurring_task_templates=["tt_global", "tt_own"]),
        )

        assert created.recurring_task_templates == ["tt_global", "tt_own"]

    def test_a_tenant_owns_at_most_the_ceiling(self, world) -> None:
        service, repo = world
        for index in range(MAX_TEMPLATES_PER_TENANT - 2):  # with "own", one below the ceiling
            repo.add(_template(f"bulk_{index}", TENANT))

        service.create_template(tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER, data=_input())
        with pytest.raises(PlanError) as refused:
            service.create_template(tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER, data=_input())

        assert (refused.value.error_code, refused.value.status_code) == ("bed_template.quota_exceeded", 422)

    def test_the_log_carries_no_template_name(self, world) -> None:
        service, _ = world

        with capture_logs() as logs:
            service.create_template(
                tenant_key=TENANT, user_key=USER, role=TenantRole.GROWER, data=_input(name="Sabine's secret bed")
            )

        assert logs and "Sabine" not in repr(logs)


class TestChanging:
    def test_a_grower_changes_a_template_of_the_tenant(self, world) -> None:
        service, repo = world

        updated = service.patch_template(
            "own", tenant_key=TENANT, role=TenantRole.GROWER, patch=BedTemplatePatch(name="Renamed", height_m=0.4)
        )

        assert (updated.name, updated.height_m, updated.tenant_key) == ("Renamed", 0.4, TENANT)
        assert repo.writes == ["update:own"]

    def test_null_clears_the_height(self, world) -> None:
        service, _ = world
        service.patch_template("own", tenant_key=TENANT, role=TenantRole.GROWER, patch=BedTemplatePatch(height_m=0.4))

        cleared = service.patch_template(
            "own", tenant_key=TENANT, role=TenantRole.GROWER, patch=BedTemplatePatch(height_m=None)
        )

        assert cleared.height_m is None

    def test_a_patch_that_changes_nothing_writes_nothing(self, world) -> None:
        service, repo = world

        service.patch_template("own", tenant_key=TENANT, role=TenantRole.GROWER, patch=BedTemplatePatch(name="Own bed"))

        assert repo.writes == []

    def test_a_viewer_changes_nothing(self, world) -> None:
        service, repo = world

        with pytest.raises(ForbiddenError):
            service.patch_template("own", tenant_key=TENANT, role=TenantRole.VIEWER, patch=BedTemplatePatch(name="x"))

        assert repo.writes == []

    def test_another_tenants_template_is_a_404_before_anything_else(self, world) -> None:
        service, repo = world

        with pytest.raises(NotFoundError):
            service.patch_template(
                "theirs",
                tenant_key=TENANT,
                role=TenantRole.LEAD,
                patch=BedTemplatePatch(name="x"),
                is_platform_admin=True,
            )

        assert repo.writes == []

    @pytest.mark.parametrize("role", [TenantRole.VIEWER, TenantRole.GROWER, TenantRole.LEAD])
    def test_a_tenant_cannot_change_a_system_template_whatever_its_role(self, world, role: TenantRole) -> None:
        service, repo = world

        with pytest.raises(ForbiddenError):
            service.patch_template("sys_bed", tenant_key=TENANT, role=role, patch=BedTemplatePatch(name="Mine now"))

        assert repo.writes == [] and repo.templates["sys_bed"].name == "A system bed"

    def test_a_platform_admin_changes_a_system_template_and_it_stays_global(self, world) -> None:
        service, repo = world

        updated = service.patch_template(
            "sys_bed",
            tenant_key=TENANT,
            role=TenantRole.GROWER,
            patch=BedTemplatePatch(name="Curated"),
            is_platform_admin=True,
        )

        assert (updated.name, updated.tenant_key) == ("Curated", None)
        assert repo.writes == ["update:sys_bed"]

    def test_a_changed_location_type_is_resolved_again(self, world) -> None:
        service, repo = world

        with pytest.raises(PlanValidationError):
            service.patch_template(
                "own", tenant_key=TENANT, role=TenantRole.GROWER, patch=BedTemplatePatch(location_type_key="nope")
            )

        assert repo.writes == []


class TestDeleting:
    def test_only_the_lead_deletes_a_template_of_the_tenant(self, world) -> None:
        service, repo = world

        for role in (TenantRole.VIEWER, TenantRole.GROWER):
            with pytest.raises(ForbiddenError):
                service.delete_template("own", tenant_key=TENANT, role=role)
        assert "own" in repo.templates

        service.delete_template("own", tenant_key=TENANT, role=TenantRole.LEAD)
        assert "own" not in repo.templates

    @pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.LEAD])
    def test_a_tenant_cannot_delete_a_system_template(self, world, role: TenantRole) -> None:
        service, repo = world

        with pytest.raises(ForbiddenError):
            service.delete_template("sys_bed", tenant_key=TENANT, role=role)

        assert "sys_bed" in repo.templates

    def test_a_platform_admin_deletes_a_system_template(self, world) -> None:
        service, repo = world

        service.delete_template("sys_bed", tenant_key=TENANT, role=TenantRole.LEAD, is_platform_admin=True)

        assert "sys_bed" not in repo.templates

    def test_another_tenants_template_is_a_404_and_survives(self, world) -> None:
        service, repo = world

        with pytest.raises(NotFoundError):
            service.delete_template("theirs", tenant_key=TENANT, role=TenantRole.LEAD, is_platform_admin=True)

        assert "theirs" in repo.templates
