"""REQ-010 P2 recognition — promote a user pest image into the few-shot index.

When a platform admin **promotes** a user-contributed pest image to global
visibility, that image is also a candidate reference for the self-hosted
few-shot pest-recognition index (REQ-044 / REQ-029-A inference-service
``/pest/reference`` + pgvector). These best-effort, async tasks bridge the
moderation decision to the index without ever blocking or failing the admin
request — :meth:`PestImageService._on_promotion_changed` only ``.delay(...)``s
them and ignores the result.

The wiring mirrors the WP-3 cold-start acquisition
(:class:`PestDatasetAcquisitionService`): the EXIF-stripped attachment bytes are
sent to ``/pest/reference`` and only the **embedding + provenance** are stored
service-side — no original pixel ever persists beyond the internal, self-hosted
inference service (REQ-044 §8, Default-Privacy). Provenance is recorded as
``source="user_contributed"`` plus the ``source_record_id`` /
``source_url`` carrying the contribution key and owning tenant.

Hard guards (a routine miss is a clean no-op, never an exception into Celery):

  Guard 1  ``settings.pest_detection_enabled``        → else no-op (Default-Privacy)
  Guard 2  contribution exists                        → else no-op
  Guard 3  the pest carries a ``detection_slug``      → else no-op (no class ⇒
           no embedding target; the gallery image stays untouched)

The recognition label is the pest's ``detection_slug``, which maps 1:1 to a
:class:`PestTaxon.slug` (the recognition class). Without it the image cannot be
attached to a recognition class, so indexing is impossible and the task logs a
clear no-op rather than guessing a class.
"""

from __future__ import annotations

import structlog

from app.common.async_bridge import run_async
from app.common.dependencies import (
    get_attachment_service,
    get_ipm_service,
    get_pest_image_repo,
    get_pest_inference_client,
)
from app.config.settings import settings
from app.domain.models.pest_taxonomy import get_taxon
from app.tasks import celery_app

logger = structlog.get_logger()

# Provenance source tag for index entries that originate from a promoted user
# contribution (distinct from the WP-3 ``gbif``/``wikimedia`` cold-start source).
USER_CONTRIBUTED_SOURCE = "user_contributed"


def _logsafe(outcome: dict) -> dict:
    """Drop keys that would collide with the explicit structlog fields."""
    return {k: v for k, v in outcome.items() if k != "contribution_key"}


async def _read_attachment_bytes(attachment_service, attachment) -> bytes:  # type: ignore[no-untyped-def]
    """Collect the (EXIF-stripped) attachment bytes from the proxy stream."""
    stream = await attachment_service.open_stream(attachment)
    out = bytearray()
    async for chunk in stream:
        out.extend(chunk)
    return bytes(out)


def _resolve_label_and_category(pest_key: str) -> tuple[str, str] | None:
    """Resolve a pest to its (recognition label, category) or ``None``.

    The label is the pest's ``detection_slug`` mapped to a :class:`PestTaxon`;
    the category is taken from that taxon (the inference-service stores it
    alongside the prototype). Returns ``None`` when the pest is gone, has no
    ``detection_slug``, or the slug is not a known taxon — every such case is a
    clean no-op (the gallery image is unaffected).
    """
    from app.common.exceptions import NotFoundError

    try:
        pest = get_ipm_service().get_pest(pest_key)
    except NotFoundError:
        return None
    slug = (pest.detection_slug or "").strip()
    if not slug:
        return None
    taxon = get_taxon(slug)
    if taxon is None:
        return None
    return taxon.slug, taxon.category.value


def _index_promoted(contribution_key: str) -> dict:
    """Upsert a promoted contribution's image as a user-contributed prototype."""
    if not settings.pest_detection_enabled:
        return {"status": "noop", "reason": "pest_detection_disabled"}

    contribution = get_pest_image_repo().get_by_key(contribution_key)
    if contribution is None:
        return {"status": "noop", "reason": "contribution_not_found"}

    resolved = _resolve_label_and_category(contribution.pest_key)
    if resolved is None:
        return {"status": "noop", "reason": "no_detection_slug", "pest_key": contribution.pest_key}
    label, category = resolved

    attachment_service = get_attachment_service()
    attachment = attachment_service.get_attachment(contribution.attachment_id, contribution.tenant_key)
    image_data = run_async(_read_attachment_bytes(attachment_service, attachment))

    get_pest_inference_client().upsert_prototype(
        image_data,
        label=label,
        category=category,
        source=USER_CONTRIBUTED_SOURCE,
        source_record_id=contribution_key,
        source_url=f"contribution://{contribution.tenant_key}/{contribution_key}",
    )
    return {"status": "indexed", "label": label, "contribution_key": contribution_key}


def _retract_promoted(contribution_key: str) -> dict:
    """Deactivate the prototype that a demoted contribution had indexed."""
    if not settings.pest_detection_enabled:
        return {"status": "noop", "reason": "pest_detection_disabled"}

    contribution = get_pest_image_repo().get_by_key(contribution_key)
    if contribution is None:
        return {"status": "noop", "reason": "contribution_not_found"}

    resolved = _resolve_label_and_category(contribution.pest_key)
    if resolved is None:
        return {"status": "noop", "reason": "no_detection_slug", "pest_key": contribution.pest_key}
    label, _category = resolved

    deactivated = get_pest_inference_client().retract_prototype(
        label=label,
        source=USER_CONTRIBUTED_SOURCE,
        source_record_id=contribution_key,
    )
    return {"status": "retracted", "label": label, "deactivated": deactivated}


@celery_app.task(  # type: ignore[misc]
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    autoretry_for=(ConnectionError, TimeoutError),
    rate_limit="30/m",
)
def index_promoted_pest_image_task(self, contribution_key: str) -> dict:  # type: ignore[no-untyped-def]
    """REQ-010 P2 — index a promoted user pest image as a few-shot prototype.

    Best-effort and async: a transient transport error retries, but a guard miss
    (feature off / unknown contribution / no ``detection_slug``) is a clean
    no-op. Any unexpected failure is swallowed into a warning so the admin
    promotion flow is never affected.
    """
    try:
        outcome = _index_promoted(contribution_key)
    except ConnectionError, TimeoutError:
        raise  # autoretry_for handles transient transport errors
    except Exception as exc:  # noqa: BLE001 — never propagate into the admin flow
        logger.warning(
            "index_promoted_pest_image_failed",
            contribution_key=contribution_key,
            error=type(exc).__name__,
        )
        return {"status": "error", "reason": type(exc).__name__}

    logger.info("index_promoted_pest_image", contribution_key=contribution_key, **_logsafe(outcome))
    return outcome


@celery_app.task(  # type: ignore[misc]
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    autoretry_for=(ConnectionError, TimeoutError),
    rate_limit="30/m",
)
def retract_promoted_pest_image_task(self, contribution_key: str) -> dict:  # type: ignore[no-untyped-def]
    """REQ-010 P2 — retract a demoted user pest image from the few-shot index.

    The inference-service has no delete-by-provenance route, so the retract
    deactivates the matching prototype(s) (curation gate). Same best-effort
    semantics as :func:`index_promoted_pest_image_task`.
    """
    try:
        outcome = _retract_promoted(contribution_key)
    except ConnectionError, TimeoutError:
        raise
    except Exception as exc:  # noqa: BLE001 — never propagate into the admin flow
        logger.warning(
            "retract_promoted_pest_image_failed",
            contribution_key=contribution_key,
            error=type(exc).__name__,
        )
        return {"status": "error", "reason": type(exc).__name__}

    logger.info("retract_promoted_pest_image", contribution_key=contribution_key, **_logsafe(outcome))
    return outcome
