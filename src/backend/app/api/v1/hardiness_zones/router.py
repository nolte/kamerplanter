"""REQ-039 — global, read-only hardiness-zone catalog endpoints.

The catalog is reference data shared across all tenants (like botanical
families), so it lives at ``/api/v1/hardiness-zones`` without a tenant prefix and
is only ``get_current_user``-gated. Per-site resolution is tenant-scoped and
lives on the site router.
"""

from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.hardiness_zones.schemas import HardinessZoneResponse
from app.common.auth import get_current_user
from app.common.dependencies import get_hardiness_zone_service
from app.domain.services.hardiness_zone_service import HardinessZoneService

router = APIRouter(prefix="/hardiness-zones", tags=["hardiness-zones"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[HardinessZoneResponse])
def list_hardiness_zones(service: HardinessZoneService = Depends(get_hardiness_zone_service)):
    """List all hardiness zones (``1a`` … ``13b``), coldest first."""
    return [to_response(z, HardinessZoneResponse) for z in service.list_zones()]


@router.get("/{zone}", response_model=HardinessZoneResponse)
def get_hardiness_zone(zone: str, service: HardinessZoneService = Depends(get_hardiness_zone_service)):
    """Get a single hardiness zone by its label (e.g. ``7a``)."""
    return to_response(service.get_zone(zone), HardinessZoneResponse)
