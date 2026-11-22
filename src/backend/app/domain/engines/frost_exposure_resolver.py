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

from app.common.enums import OVERWINTERING_SITE_TYPES, FrostRisk

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


def frost_risk_from_exposed(frost_exposed: bool | None) -> FrostRisk:
    """The bed-level risk a legacy ``frost_exposed`` override stands for (REQ-053 §10.2, migration v0098).

    ``True`` → ``high`` (the spec's mapping); ``False`` — "forced protected" — → ``normal`` (operator
    decision 2026-10-19, #2454 item 1 / #2464); ``None`` ("inherit from the site type") → ``unknown``.

    Not the inverse of :func:`frost_exposed_from_risk`: ``normal`` forces no boolean there (#2454 item 2),
    so the risk alone cannot tell a protected bed from an inheriting one. The write paths therefore never
    let ``normal`` take a ``False`` away: ``PUT /locations`` mirrors a *changed* boolean into the risk, ``PATCH
    /locations`` a *changed* risk into the boolean, where a change to ``normal`` clears only a stored
    ``True``; the plan export carries ``frost_exposed`` and the import stores it as sent (#2512, the
    decision on #2503).
    """
    if frost_exposed is None:
        return FrostRisk.UNKNOWN
    return FrostRisk.HIGH if frost_exposed else FrostRisk.NORMAL


def frost_exposed_from_risk(frost_risk: FrostRisk) -> bool | None:
    """The legacy override a bed-level risk implies: ``high`` → ``True``, ``low`` → ``False``, else inherit.

    ``normal`` and ``unknown`` say nothing about the site-type fallback, so they never force a value. The
    boolean stays what every winter reader reads until those are moved to ``microclimate.frost_risk``;
    the write paths keep the two in step on a risk change (``PATCH /locations``). There ``normal`` is not
    applied blindly: it clears a stored ``True`` but keeps a forced ``False`` (#2512). The plan import uses
    this mapping only for a file written before the export carried ``frost_exposed``.
    """
    if frost_risk is FrostRisk.HIGH:
        return True
    if frost_risk is FrostRisk.LOW:
        return False
    return None
