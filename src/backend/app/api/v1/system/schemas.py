"""Request and response bodies of the light-to-full take-over (REQ-027 §7a, #1855)."""

from pydantic import BaseModel, ConfigDict

from app.api.v1.auth.schemas import CredentialStepUp


class TakeoverResourceCountsResponse(BaseModel):
    """How much the light-mode garden holds (plants counted alive only)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"plants": 30, "sites": 3, "planting_runs": 2, "nutrient_plans": 1, "tasks": 12}]
        }
    )

    plants: int
    sites: int
    planting_runs: int
    nutrient_plans: int
    tasks: int


class TakeoverStatusResponse(BaseModel):
    """Whether a take-over is open; tenant and counts only for an account that may decide it."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "pending": True,
                    "eligible": True,
                    "tenant_key": "system-tenant",
                    "tenant_name": "Mein Garten",
                    "tenant_slug": "mein-garten",
                    "resource_counts": {"plants": 30, "sites": 3, "planting_runs": 2, "nutrient_plans": 1, "tasks": 12},
                },
                {
                    "pending": True,
                    "eligible": False,
                    "tenant_key": None,
                    "tenant_name": None,
                    "tenant_slug": None,
                    "resource_counts": None,
                },
            ]
        }
    )

    pending: bool
    eligible: bool
    #: The key the decision's step-up factor is bound to (``light_mode_takeover``).
    tenant_key: str | None = None
    tenant_name: str | None = None
    tenant_slug: str | None = None
    resource_counts: TakeoverResourceCountsResponse | None = None


class TakeoverDecisionRequest(CredentialStepUp):
    """``accept``: take the light-mode data over (``true``) or start with an empty garden (``false``).

    Carries the deciding account's step-up (``light_mode_takeover``, bound to the light-mode tenant's key,
    #1855 SEC-003): ``current_password`` for an account with a local password, otherwise
    ``step_up_token`` / ``step_up_code``.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"accept": True, "current_password": "<your current password>"}]},
    )

    accept: bool


class TakeoverResultResponse(BaseModel):
    """The decided take-over; ``tenant_slug`` names the garden that is now the caller's."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"accepted": True, "tenant_slug": "mein-garten", "platform_admin_granted": True}]
        }
    )

    accepted: bool
    tenant_slug: str | None = None
    platform_admin_granted: bool
