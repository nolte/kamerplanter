"""A stored fertilizer reference must name a product the writing tenant can see (#1713).

Six domain models carry a key into the fertilizer catalogue —
``WateringLog``, ``FeedingEvent``, ``WateringEvent``, ``TankFillEvent`` (their
``fertilizers_used`` lines), ``NutrientPlanPhaseEntry`` (its channels' dosages)
and ``FertilizerStock``. The catalogue is hybrid: a tenant sees its own products
and the global seeds (``tenant_key == ""``), never another tenant's private ones.
#1708 applied that rule on the read side; until #1713 every writer stored whatever
key arrived, so a tenant's record could point at another tenant's private product,
and whether such a write was accepted answered whether the key existed.

This module is the one check every writer calls before it persists. It lives in
the business layer on purpose: REST routes, MCP tools and Celery all reach the
writers through the services, so a check here has no entry point that bypasses
it (``tests/unit/guards/test_fertilizer_references_are_verified_on_write.py``
derives the writers from the models and holds each to calling it).

**Unknown and foreign are one answer.** Both are refused with the same error; a
distinguishable refusal would be the existence oracle the rule exists to close.
Visibility is :meth:`IFertilizerRepository.list_visible_keys` — the read filter's
own union, not a second rendering of it.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository


def _invisible(
    fertilizer_repo: IFertilizerRepository | None, keys: Iterable[str | None], *, tenant_key: str, owner: str
) -> list[str]:
    wanted = sorted({key for key in keys if key})
    if not wanted:
        return []
    if fertilizer_repo is None:
        # A wiring defect, not a user error: every DI factory passes the
        # repository. Failing closed keeps an unwired service from storing an
        # unchecked reference — the "implemented but inert" shape.
        raise RuntimeError(f"{owner} needs a fertilizer repository to store fertilizer references")
    visible = fertilizer_repo.list_visible_keys(wanted, tenant_key=tenant_key)
    return [key for key in wanted if key not in visible]


def assert_fertilizers_visible(
    fertilizer_repo: IFertilizerRepository | None,
    keys: Iterable[str | None],
    *,
    tenant_key: str,
    field: str,
    owner: str,
) -> None:
    """Raise a 422 when any of ``keys`` is not a fertilizer ``tenant_key`` may see.

    ``None`` and ``""`` are skipped: a snapshot line without a ``product_key`` is
    a free-text product and references nothing. ``tenant_key`` is the owner of
    the record being written, not a request value.
    """
    unknown = _invisible(fertilizer_repo, keys, tenant_key=tenant_key, owner=owner)
    if unknown:
        raise ValidationError(
            f"Unknown fertilizer in {field}",
            details=[{"field": field, "message": f"Unknown fertilizer: {key}"} for key in unknown],
        )


def require_visible_fertilizer(
    fertilizer_repo: IFertilizerRepository | None, key: str, *, tenant_key: str, owner: str
) -> None:
    """Raise the catalogue's 404 when ``key`` is not a fertilizer ``tenant_key`` may see.

    For the writers whose contract already answered an unknown key with 404
    (they resolve the product up front); a foreign key now gets the same 404.
    """
    if _invisible(fertilizer_repo, [key], tenant_key=tenant_key, owner=owner):
        raise NotFoundError("Fertilizer", key)
