"""#2142 (REQ-056 §7.4) — every check of a limited resource asks the entitlement service.

The issue's acceptance criterion "guard green": each place that admits one more of a
limited resource must decide through ``EntitlementService``, and each production
provider must wire the plan resolution into the service that holds the check. Without
the second half a check could call ``self._entitlements.require`` on a service built
with the plan-less fallback (instance settings only) and every plan would be inert in
production - the "implemented but inert" shape.

Three predicates over the source:

1. **The checks.** Each function of :data:`CHECKS` calls
   ``self._entitlements.require(<tenant>, EntitlementDimension.<D>, ...)`` with its
   declared dimension.
2. **The doors.** Every way in to a check passes it: the member joins already go
   through ``_create_membership_unless_erasing`` (``test_joins_and_invitations_ask_the_erasure_freeze``);
   here the upload, the photo paths and the service-account creation are pinned, and the
   one attachment door without a check (``presign_upload``) is allowlisted with its reason.
3. **The wiring.** ``get_tenant_service``, ``get_attachment_service`` and
   ``get_plant_photo_service`` pass ``entitlements=get_entitlement_service()``;
   ``get_ai_call_budget`` passes ``get_entitlement_service().ai_budget_limits``;
   ``get_entitlement_service`` wires the plan repository.

Traces to issue #2142 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

import app
from app.common.enums import EntitlementDimension

_APP = Path(app.__file__).resolve().parent

#: ``(module, Class.method)`` → the dimension the method decides.
CHECKS: dict[tuple[str, str], EntitlementDimension] = {
    ("domain/services/tenant_service.py", "TenantService._refuse_beyond_member_limit"): EntitlementDimension.MEMBERS,
    (
        "domain/services/tenant_service.py",
        "TenantService.create_service_account",
    ): EntitlementDimension.SERVICE_ACCOUNTS,
    ("domain/services/attachment_service.py", "AttachmentService._enforce_quota"): EntitlementDimension.STORAGE_MB,
    (
        "domain/services/plant_photo_service.py",
        "PlantPhotoService._enforce_photo_quota",
    ): EntitlementDimension.PHOTOS_PER_INSTANCE,
}

#: ``(module, Class.method)`` → the check it must call: the doors through which one more is admitted.
DOORS: dict[tuple[str, str], str] = {
    ("domain/services/attachment_service.py", "AttachmentService.upload"): "_enforce_quota",
    ("domain/services/plant_photo_service.py", "PlantPhotoService.assert_can_add_photo"): "_enforce_photo_quota",
    ("domain/services/plant_photo_service.py", "PlantPhotoService.link_photo"): "_enforce_photo_quota",
    ("domain/services/tenant_service.py", "TenantService._create_membership_unless_erasing"): (
        "_refuse_beyond_member_limit"
    ),
    ("domain/services/tenant_service.py", "TenantService.create_service_account"): "_refuse_beyond_member_limit",
}

#: Writers of a limited resource that do not pass a check, each with the reason.
ALLOWLIST: dict[tuple[str, str], str] = {
    ("domain/services/attachment_service.py", "AttachmentService.presign_upload"): (
        "Has no caller under app/ (asserted below); a presigned S3 PUT bypasses the whole upload pipeline, "
        "not only the quota. A caller added later must run the quota first."
    ),
}

#: Providers that must hand the plan resolution to their service.
WIRED_PROVIDERS = ("get_tenant_service", "get_attachment_service", "get_plant_photo_service")


def _functions(relative: str) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse((_APP / relative).read_text())
    found: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    found[f"{node.name}.{item.name}"] = item
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found[node.name] = node
    return found


def required_dimensions(function: ast.AST) -> list[str]:
    """The ``EntitlementDimension.<X>`` of every ``self._entitlements.require(...)`` call in *function*."""
    dimensions: list[str] = []
    for node in ast.walk(function):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "require"):
            continue
        owner = node.func.value
        if not (isinstance(owner, ast.Attribute) and owner.attr == "_entitlements"):
            continue
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Attribute):
            dimensions.append(node.args[1].attr)
    return dimensions


def _calls_self(function: ast.AST, name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == name
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        for node in ast.walk(function)
    )


@pytest.mark.parametrize(("where", "dimension"), list(CHECKS.items()), ids=lambda v: str(v))
def test_each_check_asks_the_entitlement_service_for_its_dimension(
    where: tuple[str, str], dimension: EntitlementDimension
) -> None:
    module, qualname = where
    function = _functions(module)[qualname]

    assert dimension.name in required_dimensions(function), f"{qualname} does not require {dimension}"


@pytest.mark.parametrize(("where", "check"), list(DOORS.items()), ids=lambda v: str(v))
def test_each_door_passes_its_check(where: tuple[str, str], check: str) -> None:
    module, qualname = where

    assert _calls_self(_functions(module)[qualname], check), f"{qualname} does not call self.{check}"


def test_the_allowlisted_writers_have_no_caller() -> None:
    for (_, qualname), _reason in ALLOWLIST.items():
        method = qualname.split(".")[-1]
        callers = [
            str(path.relative_to(_APP))
            for path in _APP.rglob("*.py")
            if any(
                isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == method
                for node in ast.walk(ast.parse(path.read_text()))
            )
        ]
        assert callers == [], f"{qualname} gained a caller ({callers}); run the quota check there"


def _keyword(provider: str, keyword: str) -> ast.expr | None:
    function = _functions("common/dependencies.py")[provider]
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == keyword:
                    return kw.value
    return None


@pytest.mark.parametrize("provider", WIRED_PROVIDERS)
def test_each_provider_wires_the_plan_resolution(provider: str) -> None:
    value = _keyword(provider, "entitlements")

    assert isinstance(value, ast.Call) and isinstance(value.func, ast.Name), f"{provider} wires no entitlements"
    assert value.func.id == "get_entitlement_service"


def test_the_ki_budget_reads_its_limits_from_the_plan() -> None:
    function = _functions("common/dependencies.py")["get_ai_call_budget"]
    budget = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "AiCallBudget"
    )
    limits = budget.args[1]

    assert isinstance(limits, ast.Attribute) and limits.attr == "ai_budget_limits"
    assert isinstance(limits.value, ast.Call) and getattr(limits.value.func, "id", None) == "get_entitlement_service"


def test_the_entitlement_service_is_built_with_the_plan_catalogue() -> None:
    value = _keyword("get_entitlement_service", "plan_repo")

    assert isinstance(value, ast.Call) and getattr(value.func, "id", None) == "get_plan_repo"


def test_the_predicate_tells_a_check_from_a_bare_read() -> None:
    """Self-test: the dimension is read from the call; a call on another object does not count."""
    asks = ast.parse("def f(self):\n    self._entitlements.require(t, EntitlementDimension.MEMBERS, projected=1)\n")
    other = ast.parse("def f(self):\n    self._other.require(t, EntitlementDimension.MEMBERS, projected=1)\n")
    bare = ast.parse("def f(self):\n    return self._settings.tenant_max_members_ceiling\n")

    assert required_dimensions(asks) == ["MEMBERS"]
    assert required_dimensions(other) == []
    assert required_dimensions(bare) == []
