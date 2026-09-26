from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.auth.schemas import CredentialStepUp
from app.common.enums import OidcProviderType
from app.domain.models.oidc_config import ProviderScopeCheck, ProviderTypeCheck


class OidcProviderCreateRequest(CredentialStepUp):
    """Body of ``POST /admin/oidc-providers``.

    Carries the requesting admin's own step-up (#1883) — ``current_password``, or
    ``step_up_token`` / ``step_up_code`` obtained for the act ``oidc_provider_change``
    with the target ``new:<slug>``. Never written to the configuration.

    ``provider_type`` is a closed vocabulary here, not on the domain model
    (#1497): the engine dispatches on the exact spelling, so ``GitHub`` used to be
    stored happily and then served by the generic OIDC branch — no well-known
    endpoints, no GitHub address-list request, no complaint. The boundary is the
    place to refuse it, because the domain model is also what the repository
    constructs when READING, and an enum there would make a record stored before
    this gate unreadable rather than repairable.
    """

    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    display_name: str = Field(min_length=1, max_length=200)
    provider_type: OidcProviderType = OidcProviderType.OIDC
    issuer_url: str
    client_id: str
    client_secret: str
    scopes: list[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    authorization_url: str | None = None
    token_url: str | None = None
    userinfo_url: str | None = None
    auto_discover: bool = True
    enabled: bool = False
    icon_url: str | None = None
    default_tenant_key: str | None = None


class OidcProviderUpdateRequest(CredentialStepUp):
    """Body of ``PUT /admin/oidc-providers/{key}``.

    The step-up fields (#1883, target: the configuration's key) are needed unless the
    update changes only ``display_name``, ``icon_url`` or switches the provider off.

    The vocabulary matters more here than on create: the router writes the body
    fields onto the loaded model with ``setattr``, and pydantic does not validate
    on assignment, so an unknown value would be persisted first and only then take
    effect — invisibly, on every later sign-in.
    """

    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    provider_type: OidcProviderType | None = None
    issuer_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] | None = None
    authorization_url: str | None = None
    token_url: str | None = None
    userinfo_url: str | None = None
    auto_discover: bool | None = None
    enabled: bool | None = None
    icon_url: str | None = None
    default_tenant_key: str | None = None


class OidcProviderDeleteRequest(CredentialStepUp):
    """Body of ``DELETE /admin/oidc-providers/{key}``: the admin's step-up (#1883, target: the key)."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"current_password": "<your current password>"}, {"step_up_code": "04829175"}]}
    )


class OidcProviderResponse(BaseModel):
    """A configuration as it is stored.

    ``provider_type`` stays ``str`` on the way OUT (#1497): a record written
    before the write gate may carry any spelling, and it has to remain visible to
    be repairable. ``POST /{key}/test`` says whether it is one the sign-in flow
    dispatches on.
    """

    key: str
    slug: str
    display_name: str
    provider_type: str = OidcProviderType.OIDC.value
    issuer_url: str
    client_id: str
    scopes: list[str]
    enabled: bool
    icon_url: str | None
    auto_discover: bool = True
    discovery_refreshed_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class OidcProviderTestResponse(BaseModel):
    """Result of ``POST /admin/oidc-providers/{key}/test``.

    ``provider_type_check`` (#1497) is the sibling verdict: since #1497 the write
    routes refuse a provider type outside the vocabulary, so a record carrying one
    predates the gate and this endpoint is the only place it reports itself. There
    is no migration — the read-only measurement that would justify rewriting
    operator data found no stored provider at all.

    ``scope_check`` is a field of its own rather than a sentence inside
    ``message`` (#1477): the scope verdict is the part a client has to act on,
    and it is reported on every path — a GitHub provider publishes no OIDC
    discovery document at all, so the discovery step always fails for exactly
    the provider type the check is about.
    """

    message: str
    scope_check: ProviderScopeCheck
    provider_type_check: ProviderTypeCheck
