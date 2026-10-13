"""Tenant access to nutrient plans spans the hybrid catalog (SEC-B4 follow-up).

Globally seeded system plans carry ``tenant_key == ""`` (there is no is_system
flag — empty tenant_key IS the global marker). The catalog-union list (#400)
restores them for every tenant, so ``get_plan`` must let a tenant *read* and
*clone* a global plan (detail, entries, clone routes) while every *write* path
stays owner-only and a clone becomes a private, tenant-scoped plan.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.nutrient_plan import NutrientPlan
from app.domain.services.nutrient_plan_service import NutrientPlanService
from tests.conftest import wire_get_or_raise


def _service(plan: NutrientPlan) -> tuple[NutrientPlanService, MagicMock]:
    repo = wire_get_or_raise(MagicMock(), "NutrientPlan")
    repo.get_by_key.return_value = plan
    return NutrientPlanService(repo, MagicMock(), MagicMock(), MagicMock()), repo


def _plan(key: str, tenant_key: str) -> NutrientPlan:
    return NutrientPlan(_key=key, tenant_key=tenant_key, name="Plan")


class TestNutrientPlanReadAccess:
    def test_global_plan_is_readable_by_tenant(self) -> None:
        service, _ = _service(_plan("sys1", ""))
        assert service.get_plan("sys1", tenant_key="tenant_a").key == "sys1"

    def test_own_plan_is_readable(self) -> None:
        service, _ = _service(_plan("a1", "tenant_a"))
        assert service.get_plan("a1", tenant_key="tenant_a").key == "a1"

    def test_foreign_plan_read_raises_not_found(self) -> None:
        service, _ = _service(_plan("b1", "tenant_b"))
        with pytest.raises(NotFoundError):
            service.get_plan("b1", tenant_key="tenant_a")


class TestNutrientPlanWriteAccess:
    def test_global_plan_write_is_rejected(self) -> None:
        # A tenant may read a global plan but not mutate it: for_write is strict.
        service, _ = _service(_plan("sys1", ""))
        with pytest.raises(NotFoundError):
            service.get_plan("sys1", tenant_key="tenant_a", for_write=True)

    def test_own_plan_write_is_allowed(self) -> None:
        service, _ = _service(_plan("a1", "tenant_a"))
        assert service.get_plan("a1", tenant_key="tenant_a", for_write=True).key == "a1"

    def test_foreign_plan_write_raises_not_found(self) -> None:
        service, _ = _service(_plan("b1", "tenant_b"))
        with pytest.raises(NotFoundError):
            service.get_plan("b1", tenant_key="tenant_a", for_write=True)


class TestNutrientPlanClone:
    def test_clone_of_global_plan_is_owned_by_cloning_tenant(self) -> None:
        # Cloning a global plan must produce a private tenant-scoped copy, never
        # inherit the source's empty tenant_key (which would leak it globally).
        service, repo = _service(_plan("sys1", ""))
        repo.clone.side_effect = lambda source_key, new_name, author, tenant_key="": _plan("clone1", tenant_key)

        result = service.clone_plan("sys1", "My Copy", author="me", tenant_key="tenant_a")

        assert result.tenant_key == "tenant_a"
        assert repo.clone.call_args.kwargs["tenant_key"] == "tenant_a"


class TestTheWritesResolveTheTenantThemselves:
    """#2107 (MT-010): ``update_plan`` / ``delete_plan`` / ``create_phase_entry`` reloaded the
    plan **without** a tenant and relied on the router's ``get_plan(…, for_write=True)``.
    They take ``*, tenant_key`` now and refuse a global or foreign plan themselves."""

    @staticmethod
    def _writes(service: NutrientPlanService, key: str, tenant: str):
        from app.domain.models.nutrient_plan import NutrientPlanPhaseEntry

        return [
            ("update", lambda: service.update_plan(key, {"name": "X"}, tenant_key=tenant)),
            ("delete", lambda: service.delete_plan(key, tenant_key=tenant)),
            (
                "create_phase_entry",
                lambda: service.create_phase_entry(
                    key,
                    NutrientPlanPhaseEntry(
                        plan_key=key, phase_name="vegetative", sequence_order=1, week_start=1, week_end=2
                    ),
                    tenant_key=tenant,
                ),
            ),
        ]

    @pytest.mark.parametrize(("owner", "caller"), [("", "tenant_a"), ("tenant_b", "tenant_a"), ("tenant_a", "")])
    def test_a_global_foreign_or_tenantless_write_is_not_found_and_writes_nothing(self, owner, caller) -> None:
        service, repo = _service(_plan("p1", owner))
        for name, write in self._writes(service, "p1", caller):
            with pytest.raises(NotFoundError):
                write()
            assert not repo.update.called and not repo.delete.called and not repo.create_phase_entry.called, name

    def test_the_owner_writes(self) -> None:
        service, repo = _service(_plan("p1", "tenant_a"))
        for _, write in self._writes(service, "p1", "tenant_a"):
            write()
        assert repo.update.called and repo.delete.called and repo.create_phase_entry.called
