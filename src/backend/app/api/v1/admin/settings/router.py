import httpx
from fastapi import APIRouter, Depends

from app.api.v1.admin.settings.schemas import (
    HASettingsResponse,
    HASettingsUpdate,
    HATestRequest,
    HATestResponse,
    PlantIdentificationSettingsResponse,
    PlantIdentificationSettingsUpdate,
    PlantIdentificationTestRequest,
    PlantIdentificationTestResponse,
    SystemSettingsResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_ha_client, get_system_settings_service
from app.config.settings import settings
from app.domain.models.user import User
from app.domain.services.system_settings_service import SystemSettingsService

router = APIRouter(prefix="/admin/settings", tags=["admin-settings"])


def _build_response(service: SystemSettingsService) -> SystemSettingsResponse:
    info = service.get_ha_settings_with_source()
    plantnet = service.get_plantnet_settings_with_source()
    return SystemSettingsResponse(
        home_assistant=HASettingsResponse(
            ha_url=info["ha_url"] or "",
            ha_access_token_masked=service.mask_token(info["ha_access_token"]),
            ha_timeout=info["ha_timeout"],
            source_ha_url=info["source_ha_url"],
            source_ha_access_token=info["source_ha_access_token"],
            source_ha_timeout=info["source_ha_timeout"],
        ),
        plant_identification=PlantIdentificationSettingsResponse(
            plantnet_api_key_masked=service.mask_token(plantnet["plantnet_api_key"]),
            source_plantnet_api_key=plantnet["source_plantnet_api_key"],
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
    _sync_ha_notification_channel()
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
        return HATestResponse(success=False, message="Cannot connect to Home Assistant.")
    except httpx.TimeoutException:
        return HATestResponse(success=False, message="Connection to Home Assistant timed out.")
    except httpx.HTTPStatusError as e:
        msg = f"HTTP {e.response.status_code}: Home Assistant returned an error."
        return HATestResponse(success=False, message=msg)
    except Exception:
        return HATestResponse(success=False, message="An unexpected error occurred while testing the connection.")


@router.delete("/home-assistant", status_code=204)
def delete_ha_settings(
    _current_user: User = Depends(get_current_user),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    service.delete_ha_settings()
    _sync_ha_notification_channel()


# ── REQ-029 Pl@ntNet / plant identification ─────────────────────────
#
# The Pl@ntNet key is instance-wide (free-tier key for the whole instance,
# not tenant-scoped), so write/test/delete require platform-admin rights —
# consistent with the ``admin/platform`` endpoints.


@router.put("/plant-identification", response_model=SystemSettingsResponse)
def update_plant_identification_settings(
    body: PlantIdentificationSettingsUpdate,
    _current_user: User = Depends(get_current_user),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    """Set the instance-wide Pl@ntNet API key (DB overrides the env value)."""
    service.update_plant_identification_settings(plantnet_api_key=body.plantnet_api_key)
    return _build_response(service)


@router.post("/plant-identification/test", response_model=PlantIdentificationTestResponse)
def test_plant_identification(
    body: PlantIdentificationTestRequest,
    _current_user: User = Depends(get_current_user),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    """Validate a Pl@ntNet key against the API (provided value or effective key)."""
    api_key = body.plantnet_api_key or service.get_effective_plantnet_api_key()
    if not api_key:
        return PlantIdentificationTestResponse(
            success=False,
            message="No Pl@ntNet API key configured.",
        )

    try:
        resp = httpx.get(
            f"{settings.plantnet_base_url.rstrip('/')}/projects",
            params={"api-key": api_key, "lang": "en"},
            timeout=settings.identification_http_timeout,
        )
        if resp.status_code in (401, 403):
            return PlantIdentificationTestResponse(
                success=False,
                message="Pl@ntNet rejected the API key.",
            )
        resp.raise_for_status()
        return PlantIdentificationTestResponse(
            success=True,
            message="Pl@ntNet API key is valid.",
        )
    except httpx.ConnectError:
        return PlantIdentificationTestResponse(success=False, message="Cannot connect to Pl@ntNet.")
    except httpx.TimeoutException:
        return PlantIdentificationTestResponse(success=False, message="Connection to Pl@ntNet timed out.")
    except httpx.HTTPStatusError as exc:
        # NEVER include str(exc): an httpx message embeds the request URL,
        # which carries the ``api-key`` query parameter (a secret).
        return PlantIdentificationTestResponse(
            success=False,
            message=f"HTTP {exc.response.status_code}: Pl@ntNet returned an error.",
        )
    except Exception:
        return PlantIdentificationTestResponse(
            success=False,
            message="An unexpected error occurred while testing the key.",
        )


@router.delete("/plant-identification", status_code=204)
def delete_plant_identification_settings(
    _current_user: User = Depends(get_current_user),
    service: SystemSettingsService = Depends(get_system_settings_service),
):
    """Remove the DB Pl@ntNet key so resolution falls back to the env value."""
    service.delete_plant_identification_settings()


def _sync_ha_notification_channel() -> None:
    """Re-register or remove the HA notification channel after settings change."""
    from app.data_access.external.ha_notification_channel import HomeAssistantNotificationChannel
    from app.domain.engines.notification_channel_registry import NotificationChannelRegistry

    ha_client = get_ha_client()
    if ha_client is not None:
        NotificationChannelRegistry.register(HomeAssistantNotificationChannel(ha_client))
    else:
        # Remove stale channel if HA was unconfigured
        NotificationChannelRegistry.unregister("home_assistant")
