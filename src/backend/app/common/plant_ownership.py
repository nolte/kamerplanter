"""One anchor for the two global routers that address a plant by key (#1402 group C).

`/plant-instances/{plant_key}/phases/*` and `/care-reminders/plants/{plant_key}/*`
are mounted **globally**: they carry no `/t/{slug}` segment, so `get_current_tenant`
structurally cannot bind there, and until this module neither resolved a tenant at
all. Every operation on both — reads included — took a plant key from the path and
handed it straight to a by-key lookup.

Measured before the fix:

* all five phase operations, including `POST /transition` with `force: true` and
  `DELETE /history/{key}`, acted on any plant key an authenticated caller supplied;
* all six care-reminder operations likewise. `CareReminderService.confirm_reminder`
  *has* an ownership check — and it reads `if tenant_key and self._plant_repo is not
  None:`, while the REST router called it without a `tenant_key`. An opt-in guard
  that the one production caller does not opt into is the #1042 shape: documented as
  enforced, wired nowhere.

**A dependency, not a per-handler argument.** Threading `tenant_key` through eleven
signatures is exactly the opt-in-at-the-call-site drift this repository keeps paying
for (#948, #1385, #1399): ten would be correct and the eleventh, added next month,
would not. Mounted on the ROUTER, a new operation inherits the check without anyone
remembering.

`get_active_tenant_key` is the resolver ADR-009 built for this case and
`companion_planting` and `botanical_families` already use; the frontend's global
client attaches `X-Active-Tenant` on every request, so no client change is needed.
"""

from typing import Annotated

from fastapi import Depends, Path

from app.common.auth import get_active_tenant_key
from app.common.dependencies import get_plant_instance_service
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_instance_service import PlantInstanceService


def require_owned_plant(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    tenant_key: str = Depends(get_active_tenant_key),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
) -> PlantInstance:
    """Resolve the plant and refuse it unless it belongs to the caller's active tenant.

    Returns the plant so a handler that needs it does not fetch it twice; most
    handlers ignore the return value and take it purely as a gate.

    **Fails closed as 404, not 403** — `PlantInstanceService.get_plant` delegates to
    `verify_tenant_ownership`, which raises `NotFoundError` for a foreign key. A 403
    would confirm that the key names a real plant somewhere, which is the ownership
    oracle REQ-049 §2.4 closes; a caller who may not see it is told the same thing as
    a caller who asked for nothing.
    """
    return plant_service.get_plant(plant_key, tenant_key=tenant_key)
