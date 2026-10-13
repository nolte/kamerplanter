"""Request and response bodies of the tenant's service-account routes (REQ-023 §5b, #2137)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.auth.schemas import ApiKeyControls, ApiKeyCreatedResponse, ApiKeySummaryResponse, CredentialStepUp
from app.common.enums import TenantRole
from app.common.validators import DisplayName
from app.domain.models.auth import API_KEY_MAX_LIFETIME_DAYS
from app.domain.models.service_account import MAX_ROTATION_OVERLAP_MINUTES


class ServiceAccountCreateRequest(ApiKeyControls, CredentialStepUp):
    """A new service account: its name, its role in the tenant, the controls of its first key, the step-up.

    The step-up is the *acting lead's* own (``service_account_change`` with the tenant's key as the
    target, for an account without a local password).
    """

    name: DisplayName = Field(description="Display name of the integration, e.g. 'Home Assistant'.")
    role: Literal[TenantRole.VIEWER, TenantRole.GROWER] = Field(
        default=TenantRole.GROWER,
        description="The account's role in the tenant: viewer or grower (never lead, REQ-023 §5b.3).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Home Assistant",
                    "role": "grower",
                    "ip_allowlist": ["192.168.1.0/24"],
                    "rate_limit_per_minute": 600,
                    "current_password": "<the acting lead's own current password>",
                }
            ]
        }
    )


class ServiceAccountRotateRequest(CredentialStepUp):
    """A key rotation: how long the previous keys keep working, the new key's expiry, the step-up."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"overlap_minutes": 30, "current_password": "<the acting lead's own current password>"},
                {"overlap_minutes": 0, "step_up_code": "48213907"},
            ]
        }
    )

    overlap_minutes: int = Field(
        default=0,
        ge=0,
        le=MAX_ROTATION_OVERLAP_MINUTES,
        description=(
            "Minutes the previous keys keep working after the rotation, so the integration can switch without a "
            "gap. 0 (default) revokes them at once — the compromised-key case."
        ),
    )
    expires_at: datetime | None = Field(
        default=None,
        description=(
            f"When the new key stops working; with a timezone, in the future, at most {API_KEY_MAX_LIFETIME_DAYS} "
            "days ahead. Omitted: the new key does not expire."
        ),
    )


class ServiceAccountRemovalRequest(CredentialStepUp):
    """The acting lead's step-up for removing a service account (``service_account_change``)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"current_password": "<the acting lead's own current password>"}]}
    )


class ServiceAccountResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "8f3c90",
                    "display_name": "Home Assistant",
                    "role": "grower",
                    "membership_key": "51a0e2",
                    "joined_at": "2026-10-05T10:00:00Z",
                    "api_keys": [
                        {
                            "key": "a7d2c1",
                            "label": "Home Assistant",
                            "key_prefix": "kp_Xy1aB",
                            "tenant_scope": "t-garden",
                            "revoked": False,
                            "last_used_at": "2026-10-05T10:15:00Z",
                            "created_at": "2026-10-05T10:00:00Z",
                            "ip_allowlist": ["192.168.1.0/24"],
                            "rate_limit_per_minute": 600,
                            "expires_at": "2027-03-31T22:00:00Z",
                        }
                    ],
                }
            ]
        }
    )

    key: str
    display_name: str
    role: TenantRole
    membership_key: str
    joined_at: datetime | None = None
    api_keys: list[ApiKeySummaryResponse]


class ServiceAccountCreatedResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "8f3c90",
                    "display_name": "Home Assistant",
                    "role": "grower",
                    "membership_key": "51a0e2",
                    "api_key": {
                        "key": "a7d2c1",
                        "label": "Home Assistant",
                        "raw_key": "kp_<shown once>",
                        "key_prefix": "kp_Xy1aB",
                        "tenant_scope": "t-garden",
                        "created_at": "2026-10-05T10:00:00Z",
                        "ip_allowlist": ["192.168.1.0/24"],
                        "rate_limit_per_minute": 600,
                        "expires_at": None,
                    },
                }
            ]
        }
    )

    key: str
    display_name: str
    role: TenantRole
    membership_key: str
    api_key: ApiKeyCreatedResponse = Field(description="The first API key; raw_key is shown this once.")


class ServiceAccountKeyRotatedResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "api_key": {
                        "key": "a7d2c1",
                        "label": "Home Assistant",
                        "raw_key": "kp_<shown once>",
                        "key_prefix": "kp_Xy1aB",
                        "tenant_scope": "t-garden",
                        "created_at": "2026-10-05T10:00:00Z",
                        "ip_allowlist": ["192.168.1.0/24"],
                        "rate_limit_per_minute": 600,
                        "expires_at": None,
                    },
                    "previous_keys_end_at": "2026-10-05T10:30:00Z",
                    "replaced_key_count": 1,
                }
            ]
        }
    )

    api_key: ApiKeyCreatedResponse = Field(description="The new API key; raw_key is shown this once.")
    previous_keys_end_at: datetime | None = Field(
        description="When the replaced keys stop working; null when they were revoked at once."
    )
    replaced_key_count: int
