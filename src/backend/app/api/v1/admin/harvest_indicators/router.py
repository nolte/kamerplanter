"""REQ-007 §4 — platform-admin API for the global harvest-indicator catalogue.

`HarvestIndicator` is global master data: it carries no `tenant_key`, hangs off
`species_key`, and `get_indicators_for_species` reads it with no tenant
predicate. REQ-007's rights table has said so since it was written —
`HarvestIndicators (globale Stammdaten) | Alle Rollen, auch ohne Mandant |
Plattform-Admin | Plattform-Admin | Plattform-Admin`.

The create endpoint nevertheless lived on the tenant-scoped mount behind
`require_permission(HARVEST, CREATE)` (#1249), so a grower in any tenant could
write a species-level record every tenant then reads, authorised by a permission
that tenant granted them. That is the catalogue-role-gate shape of #1110/#1120:
a tenant-scoped role authorising a write to a shared catalogue.

Its sibling in the same file, `HarvestObservation`, is genuinely tenant-scoped
(`create_observation(..., *, tenant_key)`, #948) — the model was consistent
about the distinction all along; only the route was not.

Reads stay where they are, on the tenant mount. REQ-007 grants them to
"Alle Rollen, auch ohne Mandant", so requiring membership is *stricter* than the
spec rather than wrong, and relaxing it is an API change with frontend
consumers. Recorded here so the difference is deliberate rather than forgotten.
"""

from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.harvest.schemas import HarvestIndicatorCreate, HarvestIndicatorResponse
from app.common.auth import require_platform_admin
from app.common.dependencies import get_harvest_service
from app.common.openapi_responses import AUTH_RESPONSES
from app.domain.models.harvest import HarvestIndicator
from app.domain.models.user import User
from app.domain.services.harvest_service import HarvestService

router = APIRouter(
    prefix="/admin/harvest-indicators",
    tags=["admin-harvest-indicators"],
    responses={**AUTH_RESPONSES},
)


@router.post("", response_model=HarvestIndicatorResponse, status_code=201)
def create_indicator(
    body: HarvestIndicatorCreate,
    _user: User = Depends(require_platform_admin),
    service: HarvestService = Depends(get_harvest_service),
) -> HarvestIndicatorResponse:
    """Create a harvest-readiness indicator in the global catalogue."""
    indicator = HarvestIndicator(**body.model_dump())
    created = service.create_indicator(indicator)
    return to_response(created, HarvestIndicatorResponse)
