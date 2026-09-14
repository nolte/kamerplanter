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

ADR-009's header resolution is what this case needs, and `companion_planting` and
`botanical_families` already use it through `get_active_tenant_key`; the frontend's
global client attaches `X-Active-Tenant` on every request, so no client change is
needed. This gate takes the `get_active_tenant_context` form of the same resolution
because the routes it guards also need the *role* (#1422), and two callables would
mean two `_resolve_active_tenant` runs FastAPI cannot dedupe.
"""

from typing import Annotated

from fastapi import Depends, Path

from app.common.auth import get_active_tenant_context
from app.common.dependencies import get_plant_instance_service
from app.common.exceptions import NotFoundError
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.tenant_context import TenantContext
from app.domain.services.plant_instance_service import PlantInstanceService


def require_owned_plant(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_active_tenant_context),
    plant_service: PlantInstanceService = Depends(get_plant_instance_service),
) -> PlantInstance:
    """Resolve the plant and refuse it unless it belongs to the caller's active tenant.

    Returns the plant, but **this costs a fetch rather than saving one**, and the
    docstring claimed the opposite until review round 1 of #1421. It is mounted as a
    router-level dependency, so its return value reaches no handler signature: every
    one of the eleven operations that needs the plant loads it again. The trade is
    deliberate — one lookup per request buys a gate that a newly added route on
    either router inherits without opting in, which is the #948 failure this whole
    issue is about. A handler that wants the saved fetch can take
    `plant: PlantInstance = Depends(require_owned_plant)` in its own signature; FastAPI
    caches the dependency per request, so that costs nothing extra.

    **Fails closed as 404, not 403** — `verify_tenant_ownership` raises
    `NotFoundError` for a foreign key. A 403 would confirm that the key names a real
    plant somewhere, which is the ownership oracle REQ-049 §2.4 closes; a caller who
    may not see it is told the same thing as a caller who asked for nothing.

    **An empty tenant key is refused here, not passed on**, and that line is the
    whole gate. `_resolve_active_tenant` answers `""` for a service account with no
    `X-Active-Tenant` header (`auth.py:251`, pinned deliberately so a header-less M2M
    call cannot silently act inside a tenant) and for any user without a personal
    tenant. `PlantInstanceService.get_plant` reads a falsy `tenant_key` as *skip the
    check* — its `if tenant_key:` is there for the unscoped system-context reads its
    own service makes.

    The same value therefore means "narrow to global-only" at one end and "do not
    narrow at all" at the other, and delegating the decision would have made this
    dependency **inert for exactly those callers**: measured before this guard, a
    service principal with no header read a foreign tenant's phase history with a
    200 and could `POST /transition` against it. A gate that admits everything for
    one class of caller is the failure this whole change exists to close, so the
    decision is made here rather than inherited.

    There is no plant that belongs to "no tenant": every `PlantInstance` carries a
    real `tenant_key`, unlike `Location` and `Slot` (#1397). So refusing is not a
    trade-off — an unresolvable tenant cannot own anything.
    """
    # Read off the shared context, so this gate and `require_active_tenant_role` share
    # one resolution. Two different callables — `get_active_tenant_key` here and
    # `get_active_tenant_context` there — are not deduped by FastAPI's per-request
    # cache, so each gated route would run `_resolve_active_tenant` twice. (That never
    # shipped: the rank gate and this line arrived in the same change, #1422.)
    #
    # Same value either way: both are `_resolve_active_tenant(...).key`. The cost is
    # not free in one direction — on the three read-only routes, which carry no rank
    # gate, the context form eagerly resolves the membership that the key-only form
    # skips. With the `X-Active-Tenant` header, the normal case, that membership has
    # already been fetched and validated, so it is one lookup either way.
    tenant_key = ctx.tenant_key
    if not tenant_key:
        raise NotFoundError("PlantInstance", plant_key)
    return plant_service.get_plant(plant_key, tenant_key=tenant_key)
