"""REQ-034 §4 — DINOv2 user-reference contribution hook (best-effort, async).

When a gallery photo is uploaded to a plant instance with a **known species**,
this task may contribute the photo as an additional ``user_contributed``
reference for the self-hosted DINOv2 recognition index (REQ-029-A). It is built
now but stays a **full no-op until Phase 2** of the recognition feature: the
default :class:`NoopReferenceIndexStore` never computes an embedding and never
persists anything, and ``inference_service_enabled`` defaults to ``False``.

Hard guards (REQ-034 §4.1 — ALL must pass, otherwise a clean no-op / abort):

  Guard 1  ``settings.inference_service_enabled``      → else no-op (Phase 1 default)
  Guard 2  NOT light-mode (REQ-027)                    → else abort (§4.1)
  Guard 3  contributor consent ``reference_contribution`` granted → else abort
  Guard 4  ``species_key`` present and species exists  → else abort
  Guard 5  tenant's open ``pending_review`` backlog < ``REFERENCE_CONTRIBUTION_PENDING_LIMIT``

On all-pass the contribution is stored via the reference-index store with
``is_active = False`` (curation gate, §4.3), ``source = "user_contributed"`` and
the provenance ``tenant_key`` / ``contributed_by`` (SR-003). Only the embedding
vector is persisted — the original image never leaves the Kamerplanter instance
beyond the internal, self-hosted inference service (§4.2, ClusterIP/TLS-only).

The hook **never** triggers an identification and **never** blocks the upload —
the API dispatches it ``.delay(...)`` and ignores the result.
"""

from __future__ import annotations

import structlog

from app.common.async_bridge import run_async
from app.common.dependencies import (
    get_attachment_service,
    get_consent_engine,
    get_consent_repo,
    get_plant_repo,
    get_reference_index_store,
    get_species_repo,
)
from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger()

_REFERENCE_CONTRIBUTION_PURPOSE = "reference_contribution"


def _evaluate(attachment_id: str, plant_instance_key: str, tenant_key: str, user_key: str) -> dict:
    """Run the five guards and, when all pass, store the contribution.

    Returns a structured outcome (``status`` ∈ no-op / abort / stored) for the
    Celery result and the audit log. Never raises on a routine guard failure.
    """
    # Guard 1 — inference disabled (Phase 1 default) ⇒ complete no-op (AC-10).
    if not settings.inference_service_enabled:
        return {"status": "noop", "reason": "inference_service_disabled"}

    # Guard 2 — light-mode (REQ-027) ⇒ abort (§4.1; no consent path exists).
    if settings.kamerplanter_mode == "light":
        return {"status": "abort", "reason": "light_mode"}

    # Guard 3 — contributor consent must be granted (REQ-025).
    consent = get_consent_repo().get_by_user_and_purpose(user_key, _REFERENCE_CONTRIBUTION_PURPOSE)
    if not get_consent_engine().is_processing_allowed(_REFERENCE_CONTRIBUTION_PURPOSE, consent):
        return {"status": "abort", "reason": "no_consent"}

    # Guard 4 — plant must have a known, resolvable species.
    plant = get_plant_repo().get_by_key(plant_instance_key)
    if plant is None or plant.tenant_key != tenant_key:
        return {"status": "abort", "reason": "plant_not_found"}
    if not plant.species_key:
        return {"status": "abort", "reason": "no_species"}
    species = get_species_repo().get_by_key(plant.species_key)
    if species is None:
        return {"status": "abort", "reason": "species_not_found"}

    # Guard 5 — per-tenant pending-review backlog cap (anti-poisoning, §4.3).
    store = get_reference_index_store()
    pending = store.count_pending_contributions(tenant_key)
    limit = settings.reference_contribution_pending_limit
    if limit > 0 and pending >= limit:
        return {"status": "abort", "reason": "pending_backlog_full", "pending": pending}

    # All guards passed — fetch the (EXIF-stripped) bytes and contribute. The
    # store computes the embedding via the self-hosted inference service and
    # persists only the vector + provenance, is_active=False (§4.3).
    attachment_service = get_attachment_service()
    attachment = attachment_service.get_attachment(attachment_id, tenant_key)
    image_data = run_async(_read_bytes(attachment_service, attachment))

    stored = store.add_user_contribution(
        species_key=plant.species_key,
        scientific_name=species.scientific_name,
        image_data=image_data,
        tenant_key=tenant_key,
        contributed_by=user_key,
    )
    if not stored:
        # Store is the no-op binding (physical index absent) — Phase-1 no-op.
        return {"status": "noop", "reason": "reference_store_noop"}
    return {"status": "stored", "species_key": plant.species_key}


async def _read_bytes(attachment_service, attachment) -> bytes:  # type: ignore[no-untyped-def]
    stream = await attachment_service.open_stream(attachment)
    out = bytearray()
    async for chunk in stream:
        out.extend(chunk)
    return bytes(out)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120, rate_limit="30/m")  # type: ignore[misc]
def feed_user_reference(  # type: ignore[no-untyped-def]
    self,
    attachment_id: str,
    plant_instance_key: str,
    tenant_key: str,
    user_key: str,
) -> dict:
    """REQ-034 §4 — best-effort DINOv2 reference contribution for a gallery photo.

    Rate-limited per worker (``30/m``, SR-005a). Retries only on unexpected
    transport errors *after* the guards passed — a guard failure is a clean,
    non-retried no-op/abort so the curation backlog is never flooded.
    """
    try:
        outcome = _evaluate(attachment_id, plant_instance_key, tenant_key, user_key)
    except Exception as exc:  # noqa: BLE001 — retry transient errors past the guards
        logger.warning(
            "feed_user_reference_failed",
            attachment_id=attachment_id,
            plant_instance_key=plant_instance_key,
            tenant_key=tenant_key,
            error=type(exc).__name__,
        )
        raise self.retry(exc=exc) from exc

    logger.info(
        "feed_user_reference",
        attachment_id=attachment_id,
        plant_instance_key=plant_instance_key,
        tenant_key=tenant_key,
        **outcome,
    )
    return outcome
