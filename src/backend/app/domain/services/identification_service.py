"""REQ-029 §3.6 — identification service.

Coordinates adapter selection (config-driven, REQ-029-A §0.1.1 point 1), the
hard consent gate (REQ-029 §5 / REQ-029-A §10.1), per-user rate limiting, and
the engine calls. The service is the single place the API depends on.
"""

import structlog

from app.common.exceptions import (
    AdapterNotAvailableError,
    ConsentRequiredError,
    FeatureNotConfiguredError,
)
from app.config.settings import settings
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.identification_engine import IdentificationEngine
from app.domain.interfaces.consent_repository import IConsentRepository
from app.domain.interfaces.identification_repository import IIdentificationRepository
from app.domain.interfaces.plant_identification_adapter import (
    IdentificationResult,
    PlantIdentificationAdapter,
    PlantOrgan,
)
from app.domain.services.identification_rate_limiter import IdentificationRateLimiter
from app.domain.services.identification_registry import IdentificationAdapterRegistry

logger = structlog.get_logger()

_CONSENT_PURPOSE = "plant_identification"

# REQ-034 §4a.1 — adapter keys whose path sends the photo to a third party.
# The local DINOv2 adapter is self-hosted (no data egress), Pl@ntNet / Plant.id
# are external. Used to decide whether consent (full mode) or the operator
# opt-in (Light mode) is required before an assessment may run.
_EXTERNAL_ADAPTER_KEYS = frozenset({"plantnet", "plant_id"})


class IdentificationService:
    """Service layer for plant identification (Phase 1, Pl@ntNet-first)."""

    def __init__(
        self,
        engine: IdentificationEngine,
        identification_repo: IIdentificationRepository,
        consent_repo: IConsentRepository,
        consent_engine: ConsentEngine,
        rate_limiter: IdentificationRateLimiter,
        registry: type[IdentificationAdapterRegistry] = IdentificationAdapterRegistry,
    ) -> None:
        self._engine = engine
        self._identification_repo = identification_repo
        self._consent_repo = consent_repo
        self._consent_engine = consent_engine
        self._rate_limiter = rate_limiter
        self._registry = registry

    # ── availability / status ───────────────────────────────────────────

    def is_available(self) -> bool:
        """True when at least one identification adapter is configured."""
        return self._registry.get_preferred() is not None

    def get_status(self) -> dict:
        """Status payload used by the frontend to toggle the camera UI.

        Reports the configured primary adapter, overall availability, and the
        per-adapter configuration/health state. No auth required.
        """
        preferred = self._registry.get_preferred()
        adapters: dict[str, dict] = {}
        for key in self._registry.all_keys():
            adapter = self._registry.get(key)
            adapters[key] = {
                "configured": adapter.is_configured(),
                "supports_health": adapter.supports_health_assessment,
                "rate_limit_per_day": adapter.rate_limit_per_day,
            }
        return {
            "available": preferred is not None,
            "primary_adapter": settings.identification_primary_adapter,
            "active_adapter": preferred.adapter_key if preferred else None,
            "supports_health": preferred.supports_health_assessment if preferred else False,
            "adapters": adapters,
        }

    # ── consent gate ────────────────────────────────────────────────────

    def _require_consent(self, user_key: str) -> None:
        """Block identification unless the user granted ``plant_identification``.

        In Phase 1 Pl@ntNet is the primary path, so the photo always leaves the
        instance — consent is a hard precondition (REQ-029-A §0.1.1 point 2).

        Mode-aware: this hard backend gate only applies in the ``full`` mode. In
        the Light mode (REQ-027) there are no user accounts and no consent
        subsystem (``privacy_router`` is not even registered), so there is no
        record a consent could be bound to. There the transparency notice and
        the opt-in are handled client-side (see the frontend's
        ``PlantIdentificationDialog`` / ``IdentificationConsentGate``), and the
        photo transparency (third-country transfer, EXIF strip, no persisting)
        is preserved. We therefore skip the backend consent check in Light mode.
        """
        if settings.kamerplanter_mode != "full":
            return
        record = self._consent_repo.get_by_user_and_purpose(user_key, _CONSENT_PURPOSE)
        if not self._consent_engine.is_processing_allowed(_CONSENT_PURPOSE, record):
            raise ConsentRequiredError(_CONSENT_PURPOSE)

    # ── identify ────────────────────────────────────────────────────────

    def identify_plant(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        language: str = "de",
        tenant_key: str,
        user_key: str,
        adapter_key: str | None = None,
    ) -> dict:
        """Identify a plant from an uploaded image.

        Raises:
            FeatureNotConfiguredError: no identification adapter is configured.
            ConsentRequiredError: the user has not granted consent.
            RateLimitError: the per-user daily limit was reached.
            PayloadTooLargeError / UnsupportedMediaTypeError: invalid image.
        """
        self._require_consent(user_key)

        if adapter_key:
            try:
                adapter = self._registry.get(adapter_key)
            except KeyError as exc:
                raise FeatureNotConfiguredError(
                    "plant_identification",
                    hint=f"Adapter '{adapter_key}' is not registered.",
                ) from exc
            if not adapter.is_configured():
                raise FeatureNotConfiguredError(
                    "plant_identification",
                    hint=f"Adapter '{adapter_key}' is not configured.",
                )
        else:
            adapter = self._registry.get_preferred()

        if adapter is None:
            raise FeatureNotConfiguredError(
                "plant_identification",
                hint="Set PLANTNET_API_KEY to enable image-based identification.",
            )

        configured_limit = settings.identification_rate_limit_per_user_day
        limit = configured_limit if configured_limit > 0 else (adapter.rate_limit_per_day or 0)
        if limit > 0:
            self._rate_limiter.check_and_increment(
                key=f"identify:{adapter.adapter_key}:{user_key}",
                limit=limit,
            )

        return self._engine.identify(
            adapter,
            image_data,
            organ=organ,
            language=language,
            tenant_key=tenant_key,
            user_key=user_key,
        )

    # ── quality assessment (REQ-034 §4a) ────────────────────────────────

    @staticmethod
    def _is_external(adapter_key: str) -> bool:
        """Whether the adapter sends the photo to a third party (REQ-034 §4a.1)."""
        return adapter_key in _EXTERNAL_ADAPTER_KEYS

    def _resolve_assessment_adapter(self, adapter_key: str) -> PlantIdentificationAdapter:
        """Resolve and authorise an explicitly-chosen adapter for an assessment.

        REQ-034 §4a.1/§4a.3 — unlike ``identify_plant`` the photo-quality
        assessment is always adapter-*specific* (the user picks Pl@ntNet or
        DINOv2 in the UI), so a missing/unconfigured adapter is a 409 conflict
        with the current configuration rather than a silent fall-back. In Light
        mode the external path additionally needs the operator opt-in.
        """
        try:
            adapter = self._registry.get(adapter_key)
        except KeyError as exc:
            raise AdapterNotAvailableError(adapter_key, "adapter is not registered") from exc

        if not adapter.is_configured():
            raise AdapterNotAvailableError(
                adapter_key,
                "adapter is not configured (the self-hosted inference service may be disabled until Phase 2)",
            )

        if (
            self._is_external(adapter_key)
            and settings.kamerplanter_mode != "full"
            and not settings.identification_external_in_light_mode
        ):
            raise AdapterNotAvailableError(
                adapter_key,
                "the external recognition path is disabled in Light mode (operator opt-in required)",
            )
        return adapter

    def assess_quality(
        self,
        image_data: bytes,
        *,
        adapter_key: str,
        tenant_key: str,
        user_key: str,
        organ: PlantOrgan = PlantOrgan.AUTO,
        language: str = "de",
    ) -> IdentificationResult:
        """Run an adapter-specific recognition for a *quality* assessment (REQ-034 §4a).

        Reuses the identification gates — adapter availability (409), the
        ``plant_identification`` consent for the external path (403, full mode
        only) and the per-user rate limit — then returns the **raw**
        recognition result. The Ampel verdict is derived and persisted by the
        caller (``PlantPhotoService``); no identification-history record is
        written (the verdict lives on the photo, §4a vs §4).

        Raises:
            AdapterNotAvailableError: the chosen adapter cannot be used here (409).
            ConsentRequiredError: external path without consent (full mode, 403).
            RateLimitError: the per-user daily limit was reached.
        """
        adapter = self._resolve_assessment_adapter(adapter_key)

        # Consent only gates the external path — the self-hosted DINOv2 adapter
        # has no data egress and therefore needs no third-party-transfer consent.
        if self._is_external(adapter_key):
            self._require_consent(user_key)

        configured_limit = settings.identification_rate_limit_per_user_day
        limit = configured_limit if configured_limit > 0 else (adapter.rate_limit_per_day or 0)
        if limit > 0:
            self._rate_limiter.check_and_increment(
                key=f"assess:{adapter.adapter_key}:{user_key}",
                limit=limit,
            )

        logger.info(
            "photo_quality_assessment_requested",
            tenant_key=tenant_key,
            user_key=user_key,
            adapter=adapter.adapter_key,
            external=self._is_external(adapter_key),
        )
        return self._engine.identify_raw(adapter, image_data, organ=organ, language=language)

    def list_assessment_adapters(self) -> list[dict]:
        """Adapter choices for the quality-assessment UI (REQ-034 §4a.1).

        Reports every registered adapter with the data the frontend needs to
        render the picker: its key, whether it is currently usable here
        (configuration + Light-mode external gate), and whether choosing it
        requires the third-party-transfer consent. Disabled adapters are still
        returned so the UI can show them greyed-out with a hint instead of
        hiding the (future) DINOv2 option entirely (§4a.1 — "kein toter Code").
        """
        light_blocks_external = (
            settings.kamerplanter_mode != "full" and not settings.identification_external_in_light_mode
        )
        adapters: list[dict] = []
        for key in self._registry.all_keys():
            adapter = self._registry.get(key)
            external = self._is_external(key)
            available = adapter.is_configured() and not (external and light_blocks_external)
            adapters.append(
                {
                    "key": key,
                    "available": available,
                    "external": external,
                    "requires_consent": external and settings.kamerplanter_mode == "full",
                }
            )
        return adapters

    # ── select result ───────────────────────────────────────────────────

    def select_result(
        self,
        request_key: str,
        selected_rank: int,
        *,
        tenant_key: str,
    ) -> dict:
        """Persist the user's explicit candidate selection."""
        return self._engine.select_result(request_key, selected_rank, tenant_key=tenant_key)

    # ── history ─────────────────────────────────────────────────────────

    def get_history(self, *, tenant_key: str, user_key: str, limit: int = 20) -> list[dict]:
        """Return the user's recent identification requests (no images)."""
        requests = self._identification_repo.list_for_user(
            tenant_key=tenant_key,
            user_key=user_key,
            limit=limit,
        )
        return [r.model_dump(by_alias=False) for r in requests]
