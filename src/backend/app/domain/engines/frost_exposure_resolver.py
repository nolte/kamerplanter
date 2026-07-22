"""Location-first frost-exposure resolution (Issue #706, REQ-047).

Single source of truth for the question "is a plant at this location on this site
exposed to outdoor winter frost?". Historically every winter decision path
answered it purely via ``site.type in OVERWINTERING_SITE_TYPES``. Issue #706 adds
a per-:class:`~app.domain.models.site.Location` override
(:attr:`Location.frost_exposed`) so a frost-exposed balcony corner under an
otherwise indoor site — or a protected niche under an outdoor site — can be
classified correctly.

This resolver is the ONLY place that interprets the nullable override: a set
value (``True`` / ``False``) wins; ``None`` — or no location at all — inherits
the legacy site-type classification, reproducing the previous behaviour
bit-for-bit. Keeping the resolution in one pure function structurally prevents the
frost-logic drift between the winter services that Issue #706 set out to fix.

Placed in the engine layer because it is stateless, pure domain logic over
pre-loaded models (no repository / DB access), per the Service-vs-Engine split in
``spec/style-guides/BACKEND.md``. It cannot live next to
``OVERWINTERING_SITE_TYPES`` in ``app.common.enums`` without inverting the import
direction (the models import that module, so it must not import the models).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.common.enums import OVERWINTERING_SITE_TYPES

if TYPE_CHECKING:
    from app.domain.models.site import Location, Site


def resolve_frost_exposure(location: Location | None, site: Site) -> bool:
    """Return whether a plant at ``location`` on ``site`` is frost-exposed.

    Location-first: a :attr:`Location.frost_exposed` override (``True`` / ``False``)
    wins. ``None`` — or no location — inherits frost exposure from the site type
    via :data:`OVERWINTERING_SITE_TYPES` (the legacy, unchanged behaviour). ``None``
    is never collapsed to ``False``: it falls through to the site-type fallback.
    """
    if location is not None and location.frost_exposed is not None:
        return location.frost_exposed
    return site.type in OVERWINTERING_SITE_TYPES
