"""The parent chain of a location, within its site (REQ-053 §11.3a Nr. 5 v1.60, #2888 O3/O5).

Two rules read it: the irrigation system a location inherits (a shelf left at ``manual`` under a hydroponic room is
hydroponic) and the soil hazards the soil under a location carries (a walnut's juglone recorded at the garden reaches
the beds in it). Both read this one walk, so a reader cannot follow a chain the other does not.

**Why the site bounds the chain.** ``Location`` carries no ``tenant_key`` (#2107); the site is the tenant anchor
(``location_ownership``). The walk starts at a location the caller has already resolved under the tenant, and it
follows a parent only while the parent stands in that same site - so it never reaches another tenant's location, even
through a corrupt ``parent_location_key``. A stored parent that fails validation ends the chain like an absent parent
(REQ-053 v1.61 §11.3a Nr. 5): a 409 here would block the summary, the planting check and the soil-hazard entry of
every location below it, and for a row of another site it would also tell that the key exists. A broken parent of the
same site is logged (keys only), one of another site is not (it is no row of this tenant).

**Why it terminates.** A key seen before (a cycle) and :data:`MAX_LOCATION_ANCESTORS` levels end it.
"""

from typing import Protocol

import structlog

from app.common.exceptions import StoredDocumentInvalidError
from app.domain.models.site import Location

logger = structlog.get_logger(__name__)

#: The deepest parent chain walked. A stored hierarchy is a handful of levels (site area, room, tent, bed); the cap only
#: bounds a corrupt chain the cycle check cannot see (each parent another key).
MAX_LOCATION_ANCESTORS = 32


class LocationSource(Protocol):
    """The one read the walk needs; narrower than ``ISiteRepository`` on purpose (see ``location_ownership``)."""

    def get_location_by_key(self, key: str) -> Location | None: ...


def _parent(source: LocationSource, key: str, site_key: str) -> Location | None:
    """The parent ``key`` if it stands in ``site_key``; ``None`` when absent, broken or another site's."""
    try:
        parent = source.get_location_by_key(key)
    except StoredDocumentInvalidError as exc:
        if exc.stored is not None and exc.stored.get("site_key") == site_key:
            logger.warning("location_ancestry_parent_unreadable", parent_location_key=key, site_key=site_key)
        return None
    if parent is None or parent.site_key != site_key:
        return None
    return parent


def location_ancestors(source: LocationSource, location: Location) -> list[Location]:
    """The parents of ``location``, nearest first, as far as they stand in its site.

    ``location`` must be the caller's tenant's already (resolved through its site). The chain stops at a location
    without a parent, at a parent that is absent or stands in another site, at a key seen before and after
    :data:`MAX_LOCATION_ANCESTORS` levels.
    """
    chain: list[Location] = []
    if not location.site_key:
        return chain
    seen = {location.key}
    parent_key = location.parent_location_key
    while parent_key and parent_key not in seen and len(chain) < MAX_LOCATION_ANCESTORS:
        seen.add(parent_key)
        parent = _parent(source, parent_key, location.site_key)
        if parent is None:
            break
        chain.append(parent)
        parent_key = parent.parent_location_key
    return chain
