from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.admin.oidc_providers.schemas import (
    OidcProviderCreateRequest,
    OidcProviderDeleteRequest,
    OidcProviderResponse,
    OidcProviderTestResponse,
    OidcProviderUpdateRequest,
)
from app.api.v1.auth.schemas import CREDENTIAL_STEP_UP_FIELDS
from app.common.auth import get_authenticated_with_api_key, require_platform_admin
from app.common.dependencies import get_oauth_engine, get_oidc_config_repo, get_oidc_provider_admin_service
from app.common.exceptions import NotFoundError
from app.common.openapi_responses import (
    CONFLICT_RESPONSE,
    CRUD_RESPONSES,
    FORBIDDEN_RESPONSE,
    STEP_UP_RESPONSES,
    UNAUTHORIZED_RESPONSE,
)
from app.common.request_ip import resolve_client_ip
from app.data_access.arango.oidc_config_repository import ArangoOidcConfigRepository
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User
from app.domain.services.oidc_provider_admin_service import OidcProviderAdminService

# Every operation here configures installation-wide identity federation and is
# platform-admin only (#1399). Until then all six resolved their caller through
# ``get_current_user``, so any authenticated member of any tenant could register a
# provider pointing at a server they controlled — and the OAuth callback's
# auto-link path matches an asserted email against an existing verified account,
# which turns that into a login as that account. The sibling ``admin/platform``
# router, mounted on the next line of ``api/v1/router.py``, gates every operation.
#
# The two reads are gated too: ``client_id`` and ``issuer_url`` are the
# installation's federation topology, and #1385 made the same call for the HA URL.
#
# The writes pass the admin's own step-up in ``OidcProviderAdminService`` (#1883): the
# platform-admin gate alone is passed by a hijacked admin session and by an admin's
# leaked ``kp_`` key, and a provider under an attacker's control signs in as anyone
# whose address it asserts.
#
# A new endpoint here inherits nothing automatically. ``tests/unit/api/test_write_route_gates.py``
# sweeps the write surface; add read endpoints to that judgement by hand.
router = APIRouter(
    prefix="/admin/oidc-providers",
    tags=["admin-oidc"],
    responses={**UNAUTHORIZED_RESPONSE, **CRUD_RESPONSES},
)


def _plain[T](value: T) -> T:
    """Strip an enum member down to the value the domain model is annotated for.

    ONE conversion rule for both write routes (#1497). The request schemas carry
    `OidcProviderType`; `OidcProviderConfig.provider_type` is a `str`, and the
    update (``OidcProviderAdminService.update_provider``, #1883) merges the body into
    the stored model — so whatever is handed over is what gets stored. A `StrEnum` member would compare
    equal to its value and still be a different object in the document.

    Deliberately narrow. `model_dump(mode="json")` would do the same job and
    rather more: it would also turn a future `datetime` field into a string and
    set THAT on the domain model, silently, through the same unvalidated
    `setattr`.

    **Measured (2026-09-18), because only one of the two call sites needs it.**
    `OidcProviderConfig(provider_type=OidcProviderType.GITHUB)` stores a plain
    `str` — the constructor validates and coerces. `config.provider_type = member`
    stores the MEMBER. So the create route is already safe through its own
    construction, and the update route is not; applying the same rule at both
    keeps them from answering the question differently, and keeps the create route
    safe if it ever stops constructing the model itself.
    """
    return value.value if isinstance(value, Enum) else value


def _write_fields(body: OidcProviderCreateRequest | OidcProviderUpdateRequest) -> dict:
    """The configuration fields of a write body: sent ones only, plain values, never the step-up.

    ``exclude_none`` keeps a partial update partial; the step-up fields are the
    admin's confirmation and never reach the configuration (#1883).
    """
    data = body.model_dump(exclude_none=True, exclude=CREDENTIAL_STEP_UP_FIELDS)
    return {field: _plain(value) for field, value in data.items()}


def _response(c: OidcProviderConfig) -> OidcProviderResponse:
    return OidcProviderResponse(
        key=c.key or "",
        slug=c.slug,
        display_name=c.display_name,
        provider_type=c.provider_type,
        issuer_url=c.issuer_url,
        client_id=c.client_id,
        scopes=c.scopes,
        enabled=c.enabled,
        icon_url=c.icon_url,
        auto_discover=c.auto_discover,
        discovery_refreshed_at=c.discovery_refreshed_at,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[OidcProviderResponse])
def list_providers(
    _current_user: User = Depends(require_platform_admin),
    repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    """List all configured OIDC/OAuth providers."""
    return [_response(c) for c in repo.list_all()]


@router.post(
    "",
    response_model=OidcProviderResponse,
    status_code=201,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **STEP_UP_RESPONSES},
)
def create_provider(
    body: OidcProviderCreateRequest,
    current_user: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: OidcProviderAdminService = Depends(get_oidc_provider_admin_service),
):
    """Create a new OIDC/OAuth provider configuration.

    **Step-up (#1883):** the requesting admin's own — ``current_password``, or
    ``step_up_token`` / ``step_up_code`` obtained for ``oidc_provider_change`` with the
    target ``new:<slug>``; 401 without it, 403 from an API-key request, 429
    ``STEP_UP_LOCKED``. A GitHub provider whose scopes cannot read the address list
    is refused with 422 (#1477), a taken slug with 409 — both before the step-up.
    """
    created = service.create_provider(
        _write_fields(body),
        requester=current_user,
        current_password=body.current_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return _response(created)


@router.get("/{key}", response_model=OidcProviderResponse)
def get_provider(
    key: Annotated[str, Path(description="Document key of the OIDC provider configuration.")],
    _current_user: User = Depends(require_platform_admin),
    repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    """Return a single OIDC/OAuth provider configuration by key."""
    config = repo.get_by_key(key)
    if config is None:
        raise NotFoundError("OidcProviderConfig", key)
    return _response(config)


@router.put(
    "/{key}",
    response_model=OidcProviderResponse,
    responses={**FORBIDDEN_RESPONSE, **STEP_UP_RESPONSES},
)
def update_provider(
    key: Annotated[str, Path(description="Document key of the OIDC provider configuration.")],
    body: OidcProviderUpdateRequest,
    current_user: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: OidcProviderAdminService = Depends(get_oidc_provider_admin_service),
):
    """Update an existing OIDC/OAuth provider configuration.

    **Step-up (#1883):** needed unless the update changes only ``display_name``,
    ``icon_url`` (switching it on *or off* needs it too) — the requesting admin's own
    confirmation for ``oidc_provider_change`` with the configuration's key as the
    target; 401 without it, 403 from an API-key request, 429 ``STEP_UP_LOCKED``.

    The scope check (#1477) runs on the MERGED result, not on the request body:
    a request may switch `provider_type` to `github` without touching `scopes`,
    or add `user:email` while leaving the type alone, and only the state that
    would be stored answers whether sign-in can read the address list.
    """
    updated = service.update_provider(
        key,
        _write_fields(body),
        requester=current_user,
        current_password=body.current_password,
        step_up_code=body.step_up_code,
        step_up_token=body.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )
    return _response(updated)


@router.delete("/{key}", status_code=204, responses={**FORBIDDEN_RESPONSE, **STEP_UP_RESPONSES})
def delete_provider(
    key: Annotated[str, Path(description="Document key of the OIDC provider configuration.")],
    body: OidcProviderDeleteRequest | None = None,
    current_user: User = Depends(require_platform_admin),
    via_api_key: bool = Depends(get_authenticated_with_api_key),
    client_ip: str | None = Depends(resolve_client_ip),
    service: OidcProviderAdminService = Depends(get_oidc_provider_admin_service),
):
    """Delete an OIDC/OAuth provider configuration.

    **Step-up (#1883):** the requesting admin's own confirmation for
    ``oidc_provider_change`` with the configuration's key as the target, in the
    body; 401 without it, 403 from an API-key request, 429 ``STEP_UP_LOCKED``.
    """
    step_up = body or OidcProviderDeleteRequest()
    service.delete_provider(
        key,
        requester=current_user,
        current_password=step_up.current_password,
        step_up_code=step_up.step_up_code,
        step_up_token=step_up.step_up_token,
        authenticated_with_api_key=via_api_key,
        client_ip=client_ip,
    )


@router.post("/{key}/test", response_model=OidcProviderTestResponse)
def test_provider(
    key: Annotated[str, Path(description="Document key of the OIDC provider configuration.")],
    _current_user: User = Depends(require_platform_admin),
    repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
    oauth_engine: OAuthEngine = Depends(get_oauth_engine),
):
    """Fetch and validate the OIDC discovery document, and judge type and scopes.

    Both verdicts — the scope one (#1477) and the provider-type one (#1497) — are
    reported on EVERY path, before the discovery fetch. A provider stored before
    the write gate existed can only learn of the missing `user:email` scope — or
    of its own unusable provider type — here, and GitHub publishes no
    `.well-known/openid-configuration` at all, so the discovery step always fails
    for exactly the provider type the check is about. Computing the verdict after
    an early return would have left it unreachable for GitHub.
    """
    config = repo.get_by_key(key)
    if config is None:
        raise NotFoundError("OidcProviderConfig", key)

    scope_check = oauth_engine.check_provider_scopes(config)
    provider_type_check = oauth_engine.check_provider_type(config)

    try:
        discovery = oauth_engine.fetch_discovery_document(config.issuer_url)
    except Exception as e:
        return OidcProviderTestResponse(
            message=f"Discovery fetch failed: {e}",
            scope_check=scope_check,
            provider_type_check=provider_type_check,
        )

    # Validate required fields
    required = ["authorization_endpoint", "token_endpoint", "issuer"]
    missing = [f for f in required if f not in discovery]
    if missing:
        return OidcProviderTestResponse(
            message=f"Discovery document missing fields: {', '.join(missing)}",
            scope_check=scope_check,
            provider_type_check=provider_type_check,
        )

    # Save the discovery document — and only it (#1883 security review SEC-002).
    # The fetch above may take its full timeout, paced by the issuer; a write of
    # the whole snapshot read before it would revert any change made meanwhile,
    # including a step-up'd one (issuer, secret, switching the provider off).
    from datetime import UTC, datetime

    repo.update_fields(key, {"discovery_document": discovery, "discovery_refreshed_at": datetime.now(UTC).isoformat()})

    return OidcProviderTestResponse(
        message=f"OIDC discovery for '{config.slug}' validated successfully. "
        f"Endpoints: authorization={discovery.get('authorization_endpoint', 'N/A')}, "
        f"token={discovery.get('token_endpoint', 'N/A')}",
        scope_check=scope_check,
        provider_type_check=provider_type_check,
    )
