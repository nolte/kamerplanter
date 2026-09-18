import re
from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import OidcProviderType

#: The one spelling of "this provider is GitHub". ``OAuthEngine.extract_user_info``
#: dispatches on it and the #1477 scope gate refuses on it; two literals would let
#: the gate and the branch it guards drift apart. Derived from the vocabulary the
#: API boundary enforces (#1497) so there is one spelling, not two.
GITHUB_PROVIDER_TYPE = OidcProviderType.GITHUB.value

#: Scopes that let a GitHub token read ``GET /user/emails``, the only place GitHub
#: exposes the per-address ``verified`` flag that ``should_auto_link`` needs (#1403).
#: ``user`` is the parent scope and includes ``user:email``; either one works.
GITHUB_EMAIL_SCOPES = frozenset({"user:email", "user"})

#: The scope an operator is told to add. ``user`` also works but grants far more.
GITHUB_REQUIRED_SCOPE = "user:email"

#: OAuth delimits a scope string with spaces; GitHub historically also accepted
#: commas. ``scopes`` is a ``list[str]``, but the value an operator pastes is a
#: scope *string*, so a single entry may carry several scopes.
_SCOPE_SEPARATORS = re.compile(r"[\s,]+")


def is_github_provider(provider_type: str) -> bool:
    """Whether this provider takes the GitHub branch of ``extract_user_info``.

    Deliberately an exact comparison, matching that dispatch: a provider typed as
    ``GitHub`` is served by the generic OIDC branch today and never requests
    ``/user/emails``, so the scope gate must not refuse it for a scope it does
    not use.
    """
    return provider_type == GITHUB_PROVIDER_TYPE


def is_known_provider_type(provider_type: str) -> bool:
    """Whether this spelling is one the engine actually dispatches on (#1497).

    Since #1497 the API boundary refuses anything else on create and update, so
    this answers ``False`` only for a record stored before that gate existed.
    ``POST /admin/oidc-providers/{key}/test`` reports it; nothing rewrites it,
    because a stored value is the operator's data and the read-only measurement
    that would justify a migration found no record at all.
    """
    return provider_type in {member.value for member in OidcProviderType}


def scope_tokens(scopes: list[str]) -> list[str]:
    """Flatten a configured scope list into individual scope tokens.

    ``["read:user user:email"]`` and ``["read:user", "user:email"]`` are the same
    authorization request — ``build_authorization_url`` joins the list with a
    space either way — so a membership test against the list alone reads as
    complete while refusing a working configuration.

    Case is preserved on purpose: GitHub's scope names are lower-case, and
    ``USER:EMAIL`` is not one of them. Normalising it here would wave through a
    configuration that still answers 403 on ``/user/emails``.
    """
    return [token for entry in scopes for token in _SCOPE_SEPARATORS.split(entry.strip()) if token]


def scopes_grant_github_email(scopes: list[str]) -> bool:
    """Whether these scopes let the token read the GitHub address list."""
    return any(token in GITHUB_EMAIL_SCOPES for token in scope_tokens(scopes))


class ProviderScopeCheck(BaseModel):
    """Structured verdict on a provider's scope list (#1477).

    Carried by ``POST /admin/oidc-providers/{key}/test`` as its own field rather
    than woven into the prose message: a machine-readable verdict is what a
    client can act on, and the message already carries the discovery endpoints.
    """

    ok: bool
    provider_type: str
    configured_scopes: list[str] = Field(default_factory=list)
    missing_scopes: list[str] = Field(default_factory=list)
    detail: str = ""


class ProviderTypeCheck(BaseModel):
    """Structured verdict on a stored ``provider_type`` (#1497).

    Since #1497 the API boundary refuses a spelling outside
    :class:`~app.common.enums.OidcProviderType`, so this can only be ``ok=False``
    for a record written before that gate existed. It is carried by
    ``POST /admin/oidc-providers/{key}/test`` — the same shape #1477 used for the
    scope verdict, and for the same reason: the gate protects the next write, and
    a record already stored has no other place to report itself.
    """

    ok: bool
    provider_type: str
    known_provider_types: list[str] = Field(default_factory=list)
    detail: str = ""


class OidcProviderConfig(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    display_name: str = Field(min_length=1, max_length=200)
    # DELIBERATELY ``str``, not ``OidcProviderType`` (#1497). The vocabulary is
    # enforced on the REQUEST schemas; this model is also what ``repo.get_by_key``
    # constructs from a stored document, so an enum here would raise on reading a
    # record written before the gate existed. That record would then answer 500 on
    # every read — list, get, delete, and the ``/{key}/test`` endpoint meant to
    # report the very finding — leaving the operator unable to see or repair it.
    # The lesson is #1477's: the read path constructs this model.
    provider_type: str = OidcProviderType.OIDC.value
    issuer_url: str
    client_id: str
    client_secret_encrypted: str = ""
    scopes: list[str] = Field(default_factory=lambda: ["openid", "email", "profile"])
    authorization_url: str | None = None  # Override from discovery
    token_url: str | None = None
    userinfo_url: str | None = None
    jwks_url: str | None = None
    auto_discover: bool = True
    enabled: bool = False
    icon_url: str | None = None
    default_tenant_key: str | None = None
    discovery_document: dict | None = None
    discovery_refreshed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class OidcProviderConfigCreate(BaseModel):
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


class OidcProviderConfigUpdate(BaseModel):
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
