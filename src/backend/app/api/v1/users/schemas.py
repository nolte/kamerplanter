from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.auth.schemas import CredentialStepUp
from app.common.validators import DisplayName
from app.domain.services.step_up_service import StepUpAction


class ProviderUnlinkRequest(CredentialStepUp):
    """The step-up of removing a sign-in method (#1847)."""


class ProfileUpdateRequest(BaseModel):
    display_name: DisplayName | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"current_password": "<your current password>", "new_password": "<a new passphrase of 10+ characters>"},
                {"new_password": "<a new passphrase of 10+ characters>", "step_up_code": "48213907"},
            ]
        }
    )

    current_password: str | None = Field(
        default=None,
        description=(
            "The current password. Required when the account has one; an account that signs in only through a "
            "federated provider (setting its first password) omits it and sends step_up_code."
        ),
    )
    new_password: str = Field(min_length=10, max_length=128)
    step_up_code: str | None = Field(
        default=None,
        max_length=32,
        description=(
            "The one-time code mailed by POST /users/me/step-up-code. Required when the account has no local "
            "password; 401 STEP_UP_CODE_REQUIRED without it (#1815)."
        ),
    )
    step_up_token: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "The one-time token of a fresh sign-in at the account's identity provider, from the fragment of "
            "/auth/step-up/callback after POST /users/me/step-up/oidc (#1815). Required instead of step_up_code "
            "when the account has no local password but a provider that can re-authenticate "
            "(401 STEP_UP_REAUTH_REQUIRED without it); valid five minutes, for one act, once."
        ),
    )


class StepUpCodeRequest(BaseModel):
    """Which act the mailed code is to confirm (review SEC-003) — a code confirms that act only."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"action": "account_erasure"}]})

    action: StepUpAction = Field(
        description=(
            "The act the code confirms: account_erasure, admin_account_erasure, tenant_deletion, "
            "password_change or email_change."
        )
    )


class StepUpReauthRequest(BaseModel):
    """Start a fresh sign-in at a linked identity provider for one act (#1815)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"action": "account_erasure"}, {"action": "tenant_deletion", "provider_key": "prov-17"}]
        },
    )

    action: StepUpAction = Field(
        description=(
            "The act the re-authentication confirms: account_erasure, admin_account_erasure, tenant_deletion, "
            "password_change or email_change."
        )
    )
    provider_key: str | None = Field(
        default=None,
        max_length=64,
        description=(
            "Key of one of the account's linked providers (GET /users/me/providers). Omitted: the first linked "
            "provider that supports a fresh sign-in."
        ),
    )
    client_nonce: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{32}$",
        description=(
            "32 lowercase hex characters the client generated for this re-authentication. Returned unchanged "
            "next to the step-up token (or the error) on the frontend callback, so the page that started the "
            "re-authentication can tell its own result from a planted one."
        ),
    )


class StepUpReauthStart(BaseModel):
    """Where to send the browser for the fresh sign-in (#1815)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "authorization_url": (
                        "https://accounts.google.com/o/oauth2/v2/auth?client_id=kamerplanter&response_type=code"
                        "&prompt=login&max_age=0&state=4Kc9...&nonce=Qm2x...&code_challenge_method=S256"
                    )
                }
            ]
        }
    )

    authorization_url: str = Field(description="The provider's authorization URL; open it in the browser.")


class StepUpCodeResponse(BaseModel):
    """A step-up code was mailed to the account's address (#1815). The code itself is never in a response."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"expires_at": "2026-09-25T18:40:00Z", "expires_in": 600}]}
    )

    expires_at: datetime = Field(description="When the mailed code stops being accepted (UTC).")
    expires_in: int = Field(description="Seconds until the code expires.")
