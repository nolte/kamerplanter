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

import ast
import inspect
from pathlib import Path
from typing import Any

import pytest

from app.domain.services.nutrient_plan_service import NutrientPlanService

#: Root of the test tree the double scan walks.
_TESTS_ROOT = Path(__file__).resolve().parents[2]


def _binds(func: Any, *args: Any, **kwargs: Any) -> bool:
    """Whether ``func`` would accept this call, ignoring `self`."""
    try:
        inspect.signature(func).bind(*args, **kwargs)
    except TypeError:
        return False
    return True


#: Methods of the real services whose doubles must not drift. Keyed by service
#: class so a double is matched to the right contract by *name*.
_GUARDED_SERVICES: dict[type, frozenset[str]] = {
    NutrientPlanService: frozenset({"assign_to_plant", "get_plan", "get_plant_plan"}),
}


def _discovered_doubles() -> list[tuple[Path, str, str, type]]:
    """Find every hand-written double of a guarded method, anywhere under ``tests/``.

    **Discovered, not listed — and that distinction is the whole lesson of #1145.**
    The first version of this file carried a three-row table naming the doubles in
    one module. There was a *second* copy of the same obsolete `assign_to_plant`
    in ``tests/api/test_mcp_analysis_tools_endpoints.py``; the table did not name
    it, so the guard walked straight past it and it went red only when the
    production call site was corrected. A guard against drift that has to be kept
    in sync by hand is the thing it is guarding against.

    Returns ``(file, class name, method name, service class)`` per double found.
    Source-level so no test module has to be imported (importing them all would
    make this guard depend on every fixture in the suite).
    """
    guarded = {name: cls for cls, names in _GUARDED_SERVICES.items() for name in names}
    found: list[tuple[Path, str, str, type]] = []
    for path in sorted(_TESTS_ROOT.rglob("test_*.py")):
        if path.name == Path(__file__).name:
            continue  # this file names the methods in prose and in _GUARDED_SERVICES
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:  # pragma: no cover - a syntax error fails the build anyway
            raise AssertionError(f"{path} does not parse — the double scan cannot run.") from exc
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name in guarded:
                    found.append((path, node.name, item.name, guarded[item.name]))
    return found


def _required_params(sig: inspect.Signature) -> set[str]:
    return {
        name
        for name, p in sig.parameters.items()
        if name != "self"
        and p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    }


def _double_signature(path: Path, class_name: str, method_name: str) -> inspect.Signature:
    """Build a Signature from the double's *source*, without importing its module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == class_name)
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef) and n.name == method_name)
    params: list[inspect.Parameter] = []
    args = fn.args
    n_defaults = len(args.defaults)
    positional = args.posonlyargs + args.args
    for i, a in enumerate(positional):
        has_default = i >= len(positional) - n_defaults
        params.append(
            inspect.Parameter(
                a.arg,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=None if has_default else inspect.Parameter.empty,
            )
        )
    for a, d in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        params.append(
            inspect.Parameter(
                a.arg,
                inspect.Parameter.KEYWORD_ONLY,
                default=inspect.Parameter.empty if d is None else None,
            )
        )
    return inspect.Signature(params)


def test_at_least_one_double_is_discovered() -> None:
    """T3: an empty scan would make every parametrised case below silently vanish."""
    assert _discovered_doubles(), "no doubles found — the scanner is broken, not the suite"


@pytest.mark.parametrize(
    ("path", "class_name", "method_name", "service_cls"),
    _discovered_doubles(),
    ids=[f"{p.name}::{c}.{m}" for p, c, m, _ in _discovered_doubles()],
)
def test_the_double_requires_every_argument_the_service_requires(
    path: Path, class_name: str, method_name: str, service_cls: type
) -> None:
    """Every parameter the service requires must be required on the double too.

    Stated as *missing-or-optional*, not merely *optional* — and the difference is
    not academic. The first version of this rule intersected "required on the real"
    with "optional on the fake", which is empty when the fake does not name the
    parameter **at all**. That is exactly the obsolete double's shape, so the guard
    was inert against the one signature it was written for, and a counterfactual
    (restore the old double, expect red) is what surfaced it — the rule's own
    falsifiability test had been checking `_binds`, a different proposition, and
    passed regardless.
    """
    real = inspect.signature(getattr(service_cls, method_name))
    fake = _double_signature(path, class_name, method_name)
    where = f"{path.name}::{class_name}.{method_name}"

    drifted = sorted(_required_params(real) - _required_params(fake))
    assert not drifted, (
        f"{where} does not require {drifted}, but {service_cls.__name__}.{method_name} does — "
        "a caller omitting it passes here and raises TypeError in production (#1145)"
    )


def test_the_rule_rejects_the_signature_that_actually_shipped() -> None:
    """Falsifiability, applied to the rule itself rather than to a neighbour of it.

    Rebuilds the pre-#950 double verbatim and asserts the **same expression** the
    parametrised test asserts. The previous version of this test exercised
    `_binds`, which is true of the obsolete signature for reasons unrelated to the
    rule — so it passed while the rule it claimed to protect was inert.
    """

    def pre_950_double(self, plant_key, plan_key, assigned_by=""):  # noqa: ANN001, ANN202, ARG001
        pass

    real = inspect.signature(NutrientPlanService.assign_to_plant)
    assert "tenant_key" in _required_params(real), "precondition: the service still requires tenant_key"

    drifted = _required_params(real) - _required_params(inspect.signature(pre_950_double))

    assert "tenant_key" in drifted, "the rule must flag the exact declaration that shipped the bug"


def test_the_rule_accepts_a_faithful_double() -> None:
    """The other half: a double that matches must not be reported.

    Without this the rule would be satisfied just as well by one that flags
    everything, which would be a guard nobody can keep green.
    """

    def faithful(self, plant_key, plan_key, assigned_by="", *, tenant_key):  # noqa: ANN001, ANN202, ARG001
        pass

    real = inspect.signature(NutrientPlanService.assign_to_plant)

    assert not _required_params(real) - _required_params(inspect.signature(faithful))


def test_the_mcp_tool_passes_the_tenant_to_the_write() -> None:
    """The call site itself, read from source — the one line #1145 came down to.

    Asserted separately from the behavioural tests because those go through the
    double: if the double ever regresses again, this still fails.
    """
    from app.mcp_server.tools import nutrition

    source = inspect.getsource(nutrition.AssignNutrientPlan.execute)

    assert "assign_to_plant" in source
    assert "tenant_key=" in source, "the write must be scoped to the acting tenant"
