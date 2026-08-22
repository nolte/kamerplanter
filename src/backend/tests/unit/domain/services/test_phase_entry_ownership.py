"""A phase entry is authorised through its OWN plan, not the URL's (#1263).

`PUT/DELETE /nutrient-plans/{key}/entries/{ek}` verified that the caller may
write plan `key`, then edited entry `ek` — without ever checking that `ek`
belongs to `key`. `NutrientPlanPhaseEntry` carries no `tenant_key`, and
`get_phase_entry_or_raise` is a bare document fetch, so nothing downstream
caught it either. Naming an own plan in the path therefore gave write access to
any entry in the installation, including one inside a global system template —
the exact mutation `for_write=True` exists to refuse.

The double answers only what the real repository answers: an entry lookup
returns the stored `plan_key`, and plan lookups go through the real
`get_plan`, whose `for_write` branch is the rule under test. A double that
returned a plan for every key would certify nothing.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry
from app.domain.services.nutrient_plan_service import NutrientPlanService

OWN_PLAN = "plan-own"
FOREIGN_PLAN = "plan-foreign"
GLOBAL_PLAN = "plan-global"
TENANT = "tenant-a"


def _service(entries: dict[str, str], plans: dict[str, str]) -> tuple[NutrientPlanService, MagicMock]:
    """`entries` maps entry key -> its plan_key; `plans` maps plan key -> tenant_key."""
    repo = MagicMock()

    def _entry(key: str) -> NutrientPlanPhaseEntry:
        if key not in entries:
            raise NotFoundError("nutrient plan phase entry", key)
        # The real required shape: `phase_name` is a PhaseName enum and the week
        # bounds are mandatory. An invented shorthand ('veg', no weeks) is
        # rejected by the model — which is why the double uses the real one.
        return NutrientPlanPhaseEntry(
            _key=key,
            plan_key=entries[key],
            phase_name="vegetative",
            sequence_order=1,
            week_start=1,
            week_end=4,
        )

    def _plan(key: str) -> NutrientPlan | None:
        if key not in plans:
            return None
        return NutrientPlan(_key=key, name="p", tenant_key=plans[key])

    repo.get_phase_entry_or_raise.side_effect = _entry

    # `get_plan` reads through `get_or_raise`, not `get_by_key` — wiring the
    # wrong one would make every plan lookup return a MagicMock that passes
    # every ownership check.
    def _plan_or_raise(key: str) -> NutrientPlan:
        plan = _plan(key)
        if plan is None:
            raise NotFoundError("NutrientPlan", key)
        return plan

    repo.get_or_raise.side_effect = _plan_or_raise
    repo.update_phase_entry.side_effect = lambda key, entry: entry
    repo.delete_phase_entry.return_value = True
    service = NutrientPlanService(repo, MagicMock(), MagicMock())
    return service, repo


@pytest.fixture
def wired():
    return _service(
        entries={"e-own": OWN_PLAN, "e-foreign": FOREIGN_PLAN, "e-global": GLOBAL_PLAN},
        plans={OWN_PLAN: TENANT, FOREIGN_PLAN: "tenant-b", GLOBAL_PLAN: ""},
    )


class TestUpdate:
    def test_an_own_entry_is_updated(self, wired) -> None:
        service, repo = wired

        service.update_phase_entry("e-own", {"target_ec_ms": 1.4}, plan_key=OWN_PLAN, tenant_key=TENANT)

        assert repo.update_phase_entry.called

    def test_a_foreign_tenants_entry_is_refused(self, wired) -> None:
        """The defect: reachable by naming an own plan in the path."""
        service, repo = wired

        with pytest.raises(NotFoundError):
            service.update_phase_entry("e-foreign", {"target_ec_ms": 9.9}, plan_key=OWN_PLAN, tenant_key=TENANT)

        assert not repo.update_phase_entry.called

    def test_a_global_templates_entry_is_refused(self, wired) -> None:
        """`for_write=True` refuses the global catalogue — including through an entry."""
        service, repo = wired

        with pytest.raises(NotFoundError):
            service.update_phase_entry("e-global", {"target_ec_ms": 9.9}, plan_key=OWN_PLAN, tenant_key=TENANT)

        assert not repo.update_phase_entry.called

    def test_naming_the_wrong_plan_for_an_own_entry_is_refused(self, wired) -> None:
        """The URL may not lie about which plan it edits, even within one tenant.

        Not a security property on its own — both plans here are the caller's —
        but a route that accepts a mismatched pair is one whose path segment
        means nothing, and the next reader will assume it does.
        """
        service, _ = _service(
            entries={"e-own": OWN_PLAN},
            plans={OWN_PLAN: TENANT, "plan-other-own": TENANT},
        )

        with pytest.raises(NotFoundError):
            service.update_phase_entry("e-own", {}, plan_key="plan-other-own", tenant_key=TENANT)


class TestDelete:
    def test_an_own_entry_is_deleted(self, wired) -> None:
        service, repo = wired

        assert service.delete_phase_entry("e-own", plan_key=OWN_PLAN, tenant_key=TENANT) is True

    def test_a_foreign_tenants_entry_is_refused(self, wired) -> None:
        service, repo = wired

        with pytest.raises(NotFoundError):
            service.delete_phase_entry("e-foreign", plan_key=OWN_PLAN, tenant_key=TENANT)

        assert not repo.delete_phase_entry.called

    def test_a_global_templates_entry_is_refused(self, wired) -> None:
        service, repo = wired

        with pytest.raises(NotFoundError):
            service.delete_phase_entry("e-global", plan_key=OWN_PLAN, tenant_key=TENANT)

        assert not repo.delete_phase_entry.called


class TestTheGuardIsMandatory:
    """Keyword-only, so a caller that forgets fails loudly rather than unscoped.

    This is the #948 convention, and it is the actual repair: the two channel
    routes were safe because they opted into `_owned_phase_entry_or_raise`, and
    these two were not because opting in was possible to forget.
    """

    @pytest.mark.parametrize("method", ["update_phase_entry", "delete_phase_entry"])
    def test_plan_and_tenant_cannot_be_passed_positionally(self, wired, method) -> None:
        import inspect

        service, _ = wired
        params = inspect.signature(getattr(service, method)).parameters
        for name in ("plan_key", "tenant_key"):
            assert params[name].kind is inspect.Parameter.KEYWORD_ONLY
            assert params[name].default is inspect.Parameter.empty, f"{name} must have no default"
