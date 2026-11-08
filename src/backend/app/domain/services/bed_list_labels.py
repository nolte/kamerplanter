"""The readable labels of a bed list, one mapping for every download of it (REQ-053 GP-FR-145/175/176, SR-024).

The bed list as CSV (WP 8.25, #2668) and the parcel list of the garden-plan PDF (WP 9.10, #2750) show the same two
references of a bed by name: its irrigation zone and the members it is assigned to. Both resolve them here, so there
is exactly one place that turns an assignment into something printable (SR-024):

* **The assignment is display names, never an account key.** :func:`bed_assignee_names` reads
  ``location_assignments`` joined with the membership it names and that membership's user
  (:meth:`IGardenPlanRepository.location_assignees`: the tenant is checked on the assignment *and* on the membership,
  and only active memberships count). An account that was erased reads as ``anonymised_label`` - the caller's
  language. An assignment whose membership is gone or inactive yields **no name at all**: the bed then has no entry
  in the result, exactly like a bed nobody is assigned to.
* **Only the caller decides that names are read.** The functions here read when called; the opt-in
  (``include_assignment``) is checked by the caller, which does not call :func:`bed_assignee_names` without it.
* **The size of a list is bounded before any label is read** (:func:`require_bed_list_size`).

Every function takes ``*, tenant_key: str`` and filters on it; the beds handed in are already resolved under the
tenant anchor by the calling service.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.common.exceptions import PlanError
from app.common.types import SiteKey
from app.domain.interfaces.garden_plan_repository import IGardenPlanRepository
from app.domain.models.bed_list_export import ERROR_TOO_MANY_ROWS, MAX_BED_LIST_EXPORT_ROWS
from app.domain.models.care_event import PERFORMED_BY_ANONYMISED, display_performer
from app.domain.models.site import Location


def require_bed_list_size(count: int) -> None:
    """422 ``export.too_many_rows`` for a list longer than :data:`MAX_BED_LIST_EXPORT_ROWS` - refused, never cut."""
    if count > MAX_BED_LIST_EXPORT_ROWS:
        raise PlanError(
            ERROR_TOO_MANY_ROWS,
            f"The export would have more than {MAX_BED_LIST_EXPORT_ROWS} rows; narrow it by status.",
            status_code=422,
            limit=MAX_BED_LIST_EXPORT_ROWS,
        )


def irrigation_zone_names(
    plan_repo: IGardenPlanRepository, site_key: SiteKey, beds: Iterable[Location], *, tenant_key: str
) -> dict[str, str]:
    """``zone key → name`` of the site's irrigation zones; nothing is read when no bed names a zone."""
    if not any(bed.irrigation_zone_key for bed in beds):
        return {}
    return plan_repo.irrigation_zone_names(site_key, tenant_key=tenant_key)


def bed_assignee_names(
    plan_repo: IGardenPlanRepository,
    location_keys: Sequence[str],
    *,
    tenant_key: str,
    anonymised_label: str = PERFORMED_BY_ANONYMISED,
) -> dict[str, list[str]]:
    """``bed key → display names`` of the members each bed is assigned to, sorted case-insensitively.

    An erased account reads ``anonymised_label``; an assignment of a deleted or inactive membership gives no name
    (the repository does not return it), so such a bed is missing from the result. No account key leaves this
    function.
    """
    if not location_keys:
        return {}
    names: dict[str, list[str]] = {}
    for assignee in plan_repo.location_assignees(list(location_keys), tenant_key=tenant_key):
        name = display_performer(assignee.user_key, assignee.display_name, anonymised=anonymised_label)
        if not name:
            continue
        names.setdefault(assignee.location_key, []).append(name)
    return {key: sorted(values, key=str.casefold) for key, values in names.items()}
