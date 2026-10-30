"""The merge rule of a bed's site conditions (REQ-053 §10.2, WP 3.9 and the plan batch of WP 7.20).

Two write paths change ``Location.site_conditions``: ``PATCH /locations/{key}`` (every part) and the plan
batch's ``update_fields`` (the sun profile only, #2538). Both send *the keys that changed* and must keep
everything else, so both merge through :func:`merge_site_conditions` - one rule, not two copies that drift.

Placed in the engine layer because it is stateless, pure domain logic over pre-loaded models (no repository
access), per the Service-vs-Engine split in ``spec/style-guides/BACKEND.md``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.domain.models.site import SiteConditions

#: The two parts of ``SiteConditions`` that are objects of their own (merged key by key).
NESTED_SITE_PARTS: frozenset[str] = frozenset({"sun_profile", "microclimate"})


def sent_fields(model: BaseModel) -> dict[str, Any]:
    """The fields a request body set explicitly (``model_fields_set``), by name."""
    return {name: getattr(model, name) for name in model.model_fields_set}


def merge_site_conditions(stored: SiteConditions | None, sent: BaseModel) -> SiteConditions:
    """The stored value with exactly the keys of *sent* laid over it.

    A request that sends ``{"wind_exposure": "exposed"}`` changes the wind and nothing else: a replace
    would reset the sun window, the risk and the slope to their defaults. The two nested parts are merged
    by their own sent keys; a list (``access_sides``, ``flags``) is replaced whole. *sent* is any model whose
    fields are a subset of :class:`SiteConditions` (the PATCH body or the narrower batch body); the result is
    validated as a whole, so a bound of the stored model holds even where the request model is looser.
    """
    merged = (stored if stored is not None else SiteConditions()).model_dump()
    for name in sent.model_fields_set:
        value = getattr(sent, name)
        if name in NESTED_SITE_PARTS and isinstance(value, BaseModel):
            merged[name] = {**merged[name], **sent_fields(value)}
        else:
            merged[name] = value
    return SiteConditions(**merged)
