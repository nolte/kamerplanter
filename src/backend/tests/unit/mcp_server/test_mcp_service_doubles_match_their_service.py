"""MCP test doubles must accept the calls their real service accepts (#1145).

`assign_nutrient_plan` answered `INTERNAL_ERROR` on every non-dry-run call from
the moment #950 merged. #950 made `tenant_key` required and keyword-only on
`NutrientPlanService.assign_to_plant` and updated the REST router; the MCP call
site was missed, so it raised `TypeError` before touching anything.

Six tests covered that tool, four of them driving `execute`. All six were green,
because the hand-written double still modelled the **pre-#950** signature. The
double did not follow the service, so the suite measured agreement between two
copies of an obsolete contract — the "green test measuring something other than
what it claims" shape (#956), caused here by drift rather than a weak assertion.

Fixing the call site does not fix that. The next keyword-only argument added to
any of these services will do exactly the same thing, silently. So this file
checks the *doubles against the real signatures*: a call the double accepts and
the service rejects fails here, at the seam where the drift happens, instead of
in production.

Deliberately signature-level rather than `autospec`: the doubles carry recording
behaviour the tools' tests assert on, so they cannot be replaced by mocks — what
must be pinned is that their parameter contract has not diverged.
"""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from app.domain.services.nutrient_plan_service import NutrientPlanService
from tests.unit.mcp_server import test_analysis_write_tools as write_tools


def _binds(func: Any, *args: Any, **kwargs: Any) -> bool:
    """Whether ``func`` would accept this call, ignoring `self`."""
    try:
        inspect.signature(func).bind(*args, **kwargs)
    except TypeError:
        return False
    return True


#: (double class, double attribute, real service, real attribute).
#: One row per method an MCP tool calls through a hand-written double.
_DOUBLED_METHODS = [
    (write_tools._NutrientPlanService, "assign_to_plant", NutrientPlanService, "assign_to_plant"),
    (write_tools._NutrientPlanService, "get_plan", NutrientPlanService, "get_plan"),
    (write_tools._NutrientPlanService, "get_plant_plan", NutrientPlanService, "get_plant_plan"),
]


@pytest.mark.parametrize(
    ("double_cls", "double_attr", "service_cls", "service_attr"),
    _DOUBLED_METHODS,
    ids=[f"{d.__name__}.{a}" for d, a, _, _ in _DOUBLED_METHODS],
)
def test_the_double_requires_every_argument_the_service_requires(
    double_cls: type, double_attr: str, service_cls: type, service_attr: str
) -> None:
    """A parameter the service requires must not be optional on the double.

    That asymmetry is precisely what shipped the bug: the tool omitted
    `tenant_key`, the double accepted the omission, and the service did not.
    """
    real = inspect.signature(getattr(service_cls, service_attr))
    fake = inspect.signature(getattr(double_cls, double_attr))

    required_on_real = {
        name
        for name, p in real.parameters.items()
        if name != "self"
        and p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    }
    optional_on_fake = {
        name for name, p in fake.parameters.items() if name != "self" and p.default is not inspect.Parameter.empty
    }

    drifted = required_on_real & optional_on_fake
    assert not drifted, (
        f"{double_cls.__name__}.{double_attr} makes {sorted(drifted)} optional, "
        f"but {service_cls.__name__}.{service_attr} requires it — a tool omitting it "
        "passes here and raises TypeError in production"
    )


def test_the_guard_catches_the_signature_that_actually_shipped() -> None:
    """Falsifiability: the pre-#1145 double must be rejected by the rule above.

    Without this the test above would pass just as well if its set intersection
    were empty for the wrong reason — an inverted condition, a name mismatch, a
    `self` that was not filtered. Here the exact obsolete signature is rebuilt and
    the rule is required to flag it.
    """

    def pre_950_double(self, plant_key, plan_key, assigned_by=""):  # noqa: ANN001, ANN202, ARG001
        pass

    real = inspect.signature(NutrientPlanService.assign_to_plant)
    assert real.parameters["tenant_key"].default is inspect.Parameter.empty, (
        "precondition: the service still requires tenant_key"
    )
    # The obsolete double does not even name the parameter, so the call the tool
    # used to make binds against it and not against the service.
    assert _binds(pre_950_double, None, "p1", "np-1", "mcp:sa")
    assert not _binds(NutrientPlanService.assign_to_plant, None, "p1", "np-1", "mcp:sa")


def test_the_mcp_tool_passes_the_tenant_to_the_write() -> None:
    """The call site itself, read from source — the one line #1145 came down to.

    Asserted separately from the behavioural tests because those go through the
    double: if the double ever regresses again, this still fails.
    """
    from app.mcp_server.tools import nutrition

    source = inspect.getsource(nutrition.AssignNutrientPlan.execute)

    assert "assign_to_plant" in source
    assert "tenant_key=" in source, "the write must be scoped to the acting tenant"
