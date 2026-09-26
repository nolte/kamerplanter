"""Activity plans are generated only for readable species; a private species never yields a shared plan — #1871 B10.

``POST /t/{slug}/activity-plans/generate`` resolved ``species_key`` with an
unscoped ``get_or_raise``. For another tenant's private species it generated a
**global** workflow template (``tenant_key == ""``) named after that species —
readable by every tenant. ``POST /t/{slug}/tasks/workflows`` stored a body
``species_key`` as given.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.services.activity_plan_service import ActivityPlanService
from tests.unit.domain.services.test_activity_plan_service import (
    _make_activity,
    _make_lifecycle,
    _make_phase,
    _make_species,
)


def _service(species_owner: str, *, granted: bool = False) -> ActivityPlanService:
    species_repo = MagicMock()
    species = _make_species()
    species.tenant_key = species_owner
    species_repo.get_or_raise.return_value = species
    species_repo.get_by_key.return_value = species
    species_repo.is_granted_to.return_value = granted
    phase_repo = MagicMock()
    phase_repo.get_lifecycle_by_species.return_value = _make_lifecycle()
    phase_repo.get_phases_by_lifecycle.return_value = [_make_phase()]
    activity_repo = MagicMock()
    activity_repo.get_all.return_value = ([_make_activity()], 1)
    task_repo = MagicMock()
    task_repo.get_auto_generated_workflow_for_species.return_value = None
    task_repo.create_workflow_template.side_effect = lambda wt: wt.model_copy(update={"key": "wf_new"})
    return ActivityPlanService(
        engine=__import__(
            "app.domain.engines.activity_plan_engine", fromlist=["ActivityPlanEngine"]
        ).ActivityPlanEngine(),
        activity_repo=activity_repo,
        phase_repo=phase_repo,
        task_repo=task_repo,
        planting_run_repo=MagicMock(),
        species_repo=species_repo,
    )


@pytest.mark.parametrize("path", ["get_or_generate_for_species", "regenerate_for_species"])
def test_another_tenants_private_species_is_refused(path: str) -> None:
    service = _service("t_b")

    with pytest.raises(NotFoundError):
        getattr(service, path)("sp1", tenant_key="t_a")

    service._task_repo.create_workflow_template.assert_not_called()


@pytest.mark.parametrize("owner,granted", [("t_a", False), ("t_b", True)], ids=["own", "granted"])
def test_a_private_species_yields_a_plan_owned_by_the_caller_not_a_shared_one(owner: str, granted: bool) -> None:
    service = _service(owner, granted=granted)

    plan = service.get_or_generate_for_species("sp1", tenant_key="t_a")

    assert plan.tenant_key == "t_a"


def test_a_global_species_still_yields_the_shared_plan() -> None:
    service = _service("")

    plan = service.get_or_generate_for_species("sp1", tenant_key="t_a")

    assert plan.tenant_key == ""


def test_a_workflow_template_is_not_bound_to_another_tenants_species() -> None:
    # The direct create route (POST /t/{slug}/tasks/workflows) stored the body's
    # species_key as given. Through the deployed app: the real route, the real
    # SpeciesService.get_species over a repository double.
    from types import SimpleNamespace

    from fastapi.testclient import TestClient

    from app.common.auth import get_current_user
    from app.common.dependencies import get_species_service, get_task_service, get_tenant_service
    from app.common.enums import TenantRole
    from app.domain.models.user import User
    from app.domain.services.species_service import SpeciesService
    from app.main import app

    class _Tenants:
        def get_tenant_by_slug(self, slug):
            return SimpleNamespace(key="t_a", slug=slug)

        def get_membership(self, user_key, tenant_key):
            return SimpleNamespace(role=TenantRole.LEAD, admin_scopes=[], is_active=True)

        def get_personal_tenant(self, user_key):
            return None

    species_repo = MagicMock()
    species_repo.get_or_raise.return_value = SimpleNamespace(key="sp_b", tenant_key="t_b")
    species_repo.is_granted_to.return_value = False
    tasks = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: User(_key="u", email="u@example.org", display_name="U")
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_species_service] = lambda: SpeciesService(species_repo, MagicMock())  # type: ignore[arg-type]
    app.dependency_overrides[get_task_service] = lambda: tasks
    try:
        response = TestClient(app).post("/api/v1/t/a/tasks/workflows", json={"name": "WF", "species_key": "sp_b"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    tasks.create_workflow_template.assert_not_called()
