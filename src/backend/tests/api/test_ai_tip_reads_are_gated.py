"""The two KI tip reads answer the REQ-031 §1.3 toggle (review SCR-001/SCR-002).

#1461 turned ``GET /ai/tips`` and ``GET /ai/daily-tip`` into pure reads and, in
doing so, dropped the ``ai_settings: AiTenantSettings = Depends(require_ai_tenant_enabled)``
**parameter** from both handlers — the reads no longer need the returned value,
because they no longer resolve a provider or call an LLM.

The independent review read that as the reads losing the gate: "200 with stored
KI content instead of 404/403". **Measured against the mounted router, that is not
what happens.** The gate is declared on the router
(`APIRouter(..., dependencies=[Depends(require_ai_tenant_enabled)])`), so it runs
for every route in it regardless of what any handler signature names. Removing
the parameter removed access to a *value*, not a dependency.

So this file is not a repair; it is the missing **pin**. The review was right that
nothing held the claim: the coverage rests on a router-level dependency that a
future edit could drop without a single handler changing, and no test would have
noticed. It does now, and it drives the refusals the way a client meets them —
through the mounted app, not by reading the decorator.

The fourth test is the control. Three assertions that a route refuses are all
satisfied by a route that refuses everything, so the same client with the toggle
**on** has to get its 200 here too.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.ki_assistent.tenant_router import router as ai_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_ai_assistant_service, get_tenant_repo
from app.common.enums import TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError
from app.config.settings import settings
from app.domain.models.tenant_context import TenantContext

TENANT_SLUG = "home"

TIPS = f"/api/v1/t/{TENANT_SLUG}/ai/tips?context_type=plant_instance&context_key=p-1"
DAILY_TIP = f"/api/v1/t/{TENANT_SLUG}/ai/daily-tip"

#: Both reads, so a gate that covers one and not the other is a failure and not a
#: coin flip. They are separate routes with separate signatures.
READS = pytest.mark.parametrize("path", [TIPS, DAILY_TIP], ids=["tips", "daily-tip"])


def _ctx() -> TenantContext:
    """A grower — the rank that *passes* `require_tenant_role(GROWER)`.

    Deliberately not a viewer: a viewer would be refused by the rank gate on some
    routes, and a refusal this file attributes to the KI toggle could then be the
    rank gate answering instead.
    """
    return TenantContext(tenant_key="t-1", tenant_slug=TENANT_SLUG, user_key="u-1", role=TenantRole.GROWER)


def _client(*, tenant_ai_enabled: bool) -> TestClient:
    app = FastAPI()
    app.include_router(ai_router, prefix=f"/api/v1/t/{TENANT_SLUG}")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[get_current_tenant] = _ctx

    tenant = MagicMock()
    tenant.settings = {"ai_features_enabled": tenant_ai_enabled}
    tenant_repo = MagicMock()
    tenant_repo.get_by_key.return_value = tenant
    app.dependency_overrides[get_tenant_repo] = lambda: tenant_repo

    service = MagicMock()
    service.get_tips.return_value = []
    service.get_daily_tip.return_value = None
    app.dependency_overrides[get_ai_assistant_service] = lambda: service
    return TestClient(app)


@READS
def test_the_operator_flag_off_answers_404(path: str, monkeypatch: pytest.MonkeyPatch):
    """Stage 1. 404, not 403 — §1.3: the KI API must look non-existent."""
    monkeypatch.setattr(settings, "ai_features_enabled", False)

    assert _client(tenant_ai_enabled=True).get(path).status_code == 404


@READS
def test_the_tenant_setting_off_answers_403(path: str, monkeypatch: pytest.MonkeyPatch):
    """Stage 2. The tenant admin has not turned KI on for this garden."""
    monkeypatch.setattr(settings, "ai_features_enabled", True)

    response = _client(tenant_ai_enabled=False).get(path)

    assert response.status_code == 403
    assert response.json()["error_code"] == "AI_DISABLED_FOR_TENANT"


@READS
def test_both_stages_on_answers_200(path: str, monkeypatch: pytest.MonkeyPatch):
    """The control. Without it the two refusals above are satisfied by a broken route."""
    monkeypatch.setattr(settings, "ai_features_enabled", True)

    assert _client(tenant_ai_enabled=True).get(path).status_code == 200


def test_the_gate_is_on_the_router_and_not_in_a_handler_signature(monkeypatch: pytest.MonkeyPatch):
    """Why the tests above go through the app rather than reading the signature.

    `inspect.signature` on either read handler names no AI dependency at all — the
    parameter is gone. Reading the module would therefore report both routes as
    ungated, which is exactly the conclusion the review drew. The effective
    dependency chain of the mounted route is where the truth is.
    """
    import inspect

    from app.api.v1.ki_assistent import tenant_router as module
    from app.api.v1.ki_assistent.deps import require_ai_tenant_enabled

    for handler in (module.get_tips, module.get_daily_tip):
        defaults = [parameter.default for parameter in inspect.signature(handler).parameters.values()]
        assert not any(getattr(default, "dependency", None) is require_ai_tenant_enabled for default in defaults), (
            f"{handler.__name__} names the gate; this test's premise is stale"
        )

    assert any(
        getattr(dependency, "dependency", None) is require_ai_tenant_enabled
        for dependency in (module.router.dependencies or [])
    ), "the router-level KI gate is gone — every read in this router is now ungated"
