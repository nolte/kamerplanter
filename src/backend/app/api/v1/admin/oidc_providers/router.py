from fastapi import APIRouter, Depends

from app.api.v1.admin.oidc_providers.schemas import (
    OidcProviderCreateRequest,
    OidcProviderResponse,
    OidcProviderUpdateRequest,
)
from app.api.v1.auth.schemas import MessageResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_oidc_config_repo
from app.common.exceptions import DuplicateError, NotFoundError
from app.data_access.arango.oidc_config_repository import ArangoOidcConfigRepository
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User

router = APIRouter(prefix="/admin/oidc-providers", tags=["admin-oidc"])


def _response(c: OidcProviderConfig) -> OidcProviderResponse:
    return OidcProviderResponse(
        key=c.key or "",
        slug=c.slug,
        display_name=c.display_name,
        issuer_url=c.issuer_url,
        client_id=c.client_id,
        scopes=c.scopes,
        enabled=c.enabled,
        icon_url=c.icon_url,
        discovery_refreshed_at=c.discovery_refreshed_at,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[OidcProviderResponse])
def list_providers(
    _current_user: User = Depends(get_current_user),
    repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    return [_response(c) for c in repo.list_all()]


@router.post("", response_model=OidcProviderResponse, status_code=201)
def create_provider(
    body: OidcProviderCreateRequest,
    _current_user: User = Depends(get_current_user),
    repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    existing = repo.get_by_slug(body.slug)
    if existing:
        raise DuplicateError("OidcProviderConfig", "slug", body.slug)

    config = OidcProviderConfig(
        slug=body.slug,
        display_name=body.display_name,
        issuer_url=body.issuer_url,
        client_id=body.client_id,
        client_secret_encrypted=body.client_secret,  # TODO: encrypt with Fernet
        scopes=body.scopes,
        enabled=body.enabled,
        icon_url=body.icon_url,
    )
    created = repo.create(config)
    return _response(created)


@router.get("/{key}", response_model=OidcProviderResponse)
def get_provider(
    key: str,
    _current_user: User = Depends(get_current_user),
    repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    config = repo.get_by_key(key)
    if config is None:
        raise NotFoundError("OidcProviderConfig", key)
    return _response(config)


@router.put("/{key}", response_model=OidcProviderResponse)
def update_provider(
    key: str,
    body: OidcProviderUpdateRequest,
    _current_user: User = Depends(get_current_user),
    repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    config = repo.get_by_key(key)
    if config is None:
        raise NotFoundError("OidcProviderConfig", key)

    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        if field == "client_secret":
            config.client_secret_encrypted = value  # TODO: encrypt with Fernet
        else:
            setattr(config, field, value)

    updated = repo.update(key, config)
    return _response(updated)


@router.delete("/{key}", status_code=204)
def delete_provider(
    key: str,
    _current_user: User = Depends(get_current_user),
    repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    config = repo.get_by_key(key)
    if config is None:
        raise NotFoundError("OidcProviderConfig", key)
    repo.delete(key)


@router.post("/{key}/test", response_model=MessageResponse)
def test_provider(
    key: str,
    _current_user: User = Depends(get_current_user),
    repo: ArangoOidcConfigRepository = Depends(get_oidc_config_repo),
):
    config = repo.get_by_key(key)
    if config is None:
        raise NotFoundError("OidcProviderConfig", key)
    return MessageResponse(message=f"OIDC provider '{config.slug}' configuration test not yet implemented.")
