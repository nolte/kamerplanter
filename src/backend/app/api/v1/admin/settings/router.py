import httpx
from fastapi import APIRouter, Depends

from app.api.v1.admin.settings.schemas import (
    HASettingsResponse,
    HASettingsUpdate,
    HATestRequest,
    HATestResponse,
    SystemSettingsResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_system_settings_service
from app.domain.models.user import User
from app.domain.services.system_settings_service import SystemSettingsService

router = APIRouter(prefix="/admin/settings", tags=["admin-settings"])


def _build_response(service: SystemSettingsService) -> SystemSettingsResponse:
    info = service.get_ha_settings_with_source()
    return SystemSettingsResponse(
        home_assistant=HASettingsResponse(
            ha_url=info["ha_url"] or "",
            ha_access_token_masked=service.mask_token(info["ha_access_token"]),
            ha_timeout=info["ha_timeout"],
            source_ha_url=info["source_ha_url"],
            source_ha_access_token=info["source_ha_access_token"],
            source_ha_timeout=info["source_ha_timeout"],
        ),
    )


@router.get("", response_model=SystemSettingsResponse)
def get_settings(
    _current_user: User = Depends(get_current_user),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    return _build_response(service)


@router.put("/home-assistant", response_model=SystemSettingsResponse)
def update_ha_settings(
    body: HASettingsUpdate,
    _current_user: User = Depends(get_current_user),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    service.update_ha_settings(
        ha_url=body.ha_url,
        ha_access_token=body.ha_access_token,
        ha_timeout=body.ha_timeout,
    )
    return _build_response(service)


@router.post("/home-assistant/test", response_model=HATestResponse)
def test_ha_connection(
    body: HATestRequest,
    _current_user: User = Depends(get_current_user),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    """Test HA connection using provided values or effective settings."""
    effective = service.get_effective_ha_settings()
    url = body.ha_url or effective["ha_url"]
    token = body.ha_access_token or effective["ha_access_token"]
    timeout = body.ha_timeout or effective["ha_timeout"]

    if not url:
        return HATestResponse(success=False, message="No Home Assistant URL configured.")

    try:
        resp = httpx.get(
            f"{str(url).rstrip('/')}/api/",
            headers={"Authorization": f"Bearer {token}"} if token else {},
            timeout=int(timeout),
        )
        resp.raise_for_status()
        data = resp.json()
        return HATestResponse(
            success=True,
            message=data.get("message", "Connection successful."),
            ha_version=data.get("version"),
        )
    except httpx.ConnectError:
        return HATestResponse(success=False, message=f"Cannot connect to {url}.")
    except httpx.TimeoutException:
        return HATestResponse(success=False, message=f"Connection to {url} timed out.")
    except httpx.HTTPStatusError as e:
        return HATestResponse(success=False, message=f"HTTP {e.response.status_code}: {e.response.text[:200]}")
    except Exception as e:
        return HATestResponse(success=False, message=str(e)[:300])


@router.delete("/home-assistant", status_code=204)
def delete_ha_settings(
    _current_user: User = Depends(get_current_user),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    service.delete_ha_settings()
