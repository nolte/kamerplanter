"""REQ-029 §3.3 / REQ-029-A Phase 1 — Pl@ntNet API v2 adapter.

Pl@ntNet is the Phase-1 **primary** identification adapter: free tier
(<=500 requests/day, non-commercial), API key passed as a query parameter.
It performs species identification only — health/disease assessment is not
supported and ``diagnose`` raises ``NotImplementedError`` (REQ-029 §3.3).

Documentation: https://my.plantnet.org/doc/openapi
Account:       https://my.plantnet.org

The adapter follows the established sync-``httpx.Client`` pattern of the
REQ-011 external adapters (``GBIFAdapter``, ``PerenualAdapter``).
"""

import time

import structlog
from httpx import Client, HTTPStatusError, RequestError

from app.common.exceptions import ExternalSourceError, RateLimitError
from app.config.settings import settings
from app.domain.interfaces.plant_identification_adapter import (
    HealthAssessment,
    IdentificationResult,
    IdentificationSuggestion,
    PlantIdentificationAdapter,
    PlantOrgan,
)
from app.domain.services.identification_registry import IdentificationAdapterRegistry

logger = structlog.get_logger()

ADAPTER_KEY = "plantnet"


@IdentificationAdapterRegistry.register
class PlantNetAdapter(PlantIdentificationAdapter):
    """Adapter for the Pl@ntNet v2 identification API (species only)."""

    adapter_key = ADAPTER_KEY
    supports_health_assessment = False
    rate_limit_per_day = 500  # free, non-commercial tier
    is_external = True  # hosted service — the photo leaves the instance (REQ-034 §4a.1)

    def __init__(self) -> None:
        self._base_url = settings.plantnet_base_url
        self._timeout = settings.identification_http_timeout

    def _resolve_api_key(self) -> str:
        """Resolve the effective Pl@ntNet key at call time (DB overrides env).

        A key set via the admin UI is stored in ``system_settings`` and must
        take effect immediately, without a pod restart. This mirrors the
        ``get_ha_client()`` resolution pattern: query the DB-backed settings
        service and fall back to the environment variable if the collection
        does not exist yet (fresh install / migration not yet run).
        """
        try:
            from app.common.dependencies import get_system_settings_service

            return get_system_settings_service().get_effective_plantnet_api_key()
        except Exception:
            # Collection may not exist yet — fall back to env.
            return settings.plantnet_api_key

    def is_configured(self) -> bool:
        return bool(self._resolve_api_key())

    def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        api_key = self._resolve_api_key()
        if not api_key:
            raise ExternalSourceError(ADAPTER_KEY, "Pl@ntNet API key is not configured.")

        organ_param = "auto" if organ == PlantOrgan.AUTO else organ.value
        start = time.monotonic()

        try:
            with Client(base_url=self._base_url, timeout=self._timeout) as client:
                response = client.post(
                    "/identify/all",
                    params={
                        "api-key": api_key,
                        "include-related-images": "true",
                        "nb-results": max_results,
                        "lang": language,
                    },
                    files={"images": ("plant.jpg", image_data, "image/jpeg")},
                    data={"organs": organ_param},
                )
                if response.status_code == 429:
                    raise RateLimitError(ADAPTER_KEY, retry_after=86400)
                if response.status_code in (401, 403):
                    raise ExternalSourceError(ADAPTER_KEY, "Pl@ntNet rejected the API key.")
                if response.status_code == 404:
                    # Pl@ntNet returns 404 when nothing could be matched.
                    elapsed_ms = int((time.monotonic() - start) * 1000)
                    return IdentificationResult(
                        suggestions=[],
                        health_assessment=None,
                        is_plant=False,
                        api_response_time_ms=elapsed_ms,
                    )
                response.raise_for_status()
                data = response.json()
        except RateLimitError:
            raise
        except (HTTPStatusError, RequestError) as exc:
            # NEVER log str(exc): an httpx exception message typically embeds the
            # full request URL, which includes the ``api-key`` query parameter
            # (a secret). Log only the exception class and, for HTTP status
            # errors, the response status code.
            status_code = exc.response.status_code if isinstance(exc, HTTPStatusError) else None
            logger.warning(
                "plantnet_identify_failed",
                error_type=exc.__class__.__name__,
                status_code=status_code,
            )
            raise ExternalSourceError(
                ADAPTER_KEY,
                "Pl@ntNet request failed: " + exc.__class__.__name__,
            ) from exc

        elapsed_ms = int((time.monotonic() - start) * 1000)
        suggestions = self._map_suggestions(data, max_results)

        return IdentificationResult(
            suggestions=suggestions,
            health_assessment=None,  # Pl@ntNet has no health assessment
            is_plant=len(suggestions) > 0,
            api_response_time_ms=elapsed_ms,
        )

    def diagnose(
        self,
        image_data: bytes,
        *,
        language: str = "de",
    ) -> HealthAssessment:
        raise NotImplementedError(
            "Pl@ntNet does not support health assessment. Use a health-capable adapter (e.g. Plant.id) for diagnosis."
        )

    def health_check(self) -> bool:
        return self.is_configured()

    @staticmethod
    def _map_suggestions(data: dict, max_results: int) -> list[IdentificationSuggestion]:
        """Map a Pl@ntNet response onto rank-sorted ``IdentificationSuggestion``s.

        ``external_id`` is namespaced ``plantnet:<gbifId>`` to keep the contract
        adapter-neutral (REQ-029-A §0.1.1 point 5). When no GBIF id is present a
        slugged scientific name is used as a stable fallback.
        """
        suggestions: list[IdentificationSuggestion] = []
        for index, result in enumerate(data.get("results", [])[:max_results], start=1):
            species = result.get("species", {})
            scientific_name = species.get("scientificNameWithoutAuthor", "")
            gbif = species.get("gbif") or {}
            gbif_id_raw = gbif.get("id")
            gbif_id = int(gbif_id_raw) if gbif_id_raw not in (None, "") else None

            if gbif_id is not None:
                external_id = f"plantnet:{gbif_id}"
            else:
                slug = scientific_name.strip().lower().replace(" ", "_") or f"rank{index}"
                external_id = f"plantnet:{slug}"

            family = (species.get("family") or {}).get("scientificNameWithoutAuthor")
            genus = (species.get("genus") or {}).get("scientificNameWithoutAuthor")
            images = result.get("images") or []
            image_url = (images[0].get("url") or {}).get("m") if images else None

            suggestions.append(
                IdentificationSuggestion(
                    rank=index,
                    scientific_name=scientific_name,
                    common_names=species.get("commonNames", []) or [],
                    family=family,
                    genus=genus,
                    confidence=float(result.get("score", 0.0)),
                    external_id=external_id,
                    image_url=image_url,
                    gbif_id=gbif_id,
                    raw_data=result,
                )
            )
        return suggestions
