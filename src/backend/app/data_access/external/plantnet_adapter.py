"""REQ-029 §3.3 — Pl@ntNet API v2 adapter (Phase-1 fallback).

Documentation: https://my.plantnet.org/doc/openapi
Account: https://my.plantnet.org
Constraints: species identification only (no health assessment).
Free tier: 500 requests/day (non-commercial).

The adapter is registered as a fallback. A future ``LocalEmbeddingAdapter``
(WS-3) registers ahead of it as priority 1; the registry's
``identification_primary_adapter`` setting decides precedence.
"""

import time
from datetime import date
from typing import Any

import httpx
import structlog

from app.config.settings import settings
from app.domain.interfaces.plant_identification_adapter import PlantIdentificationAdapter
from app.domain.models.identification import (
    HealthAssessment,
    IdentificationResult,
    IdentificationSuggestion,
    PlantOrgan,
)
from app.domain.services.identification_adapter_registry import IdentificationAdapterRegistry

logger = structlog.get_logger()


@IdentificationAdapterRegistry.register
class PlantNetAdapter(PlantIdentificationAdapter):
    """Adapter for the Pl@ntNet v2 identification API."""

    adapter_key = "plantnet"
    supports_health_assessment = False
    rate_limit_per_day = 500

    # Class-level daily counter shared across instances (per process).
    _request_date: date | None = None
    _request_count: int = 0

    def __init__(self) -> None:
        self._base_url = settings.plantnet_base_url
        # An explicitly disabled adapter reports no key and is thus unavailable.
        self._api_key = settings.plantnet_api_key if settings.plantnet_enabled else ""
        self._timeout = settings.identification_http_timeout

    # ── Rate-limit tracking ────────────────────────────────────────────

    @classmethod
    def _reset_if_new_day(cls) -> None:
        today = date.today()  # noqa: DTZ011 — local calendar day for daily quota
        if cls._request_date != today:
            cls._request_date = today
            cls._request_count = 0

    @classmethod
    def _remaining_today(cls) -> int:
        cls._reset_if_new_day()
        return max(0, cls.rate_limit_per_day - cls._request_count)

    @classmethod
    def _increment(cls) -> None:
        cls._reset_if_new_day()
        cls._request_count += 1

    # ── Identification ─────────────────────────────────────────────────

    async def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        start = time.monotonic()
        organ_param = organ.value if organ != PlantOrgan.AUTO else "auto"

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/identify/all",
                params={
                    "api-key": self._api_key,
                    "include-related-images": "true",
                    "nb-results": max_results,
                    "lang": language,
                },
                files={"images": ("plant.jpg", image_data, "image/jpeg")},
                data={"organs": organ_param},
            )
            resp.raise_for_status()
            data = resp.json()

        self._increment()
        elapsed_ms = int((time.monotonic() - start) * 1000)

        suggestions: list[IdentificationSuggestion] = []
        for i, result in enumerate(data.get("results", [])[:max_results], start=1):
            species = result.get("species", {})
            gbif = species.get("gbif") or {}
            suggestions.append(
                IdentificationSuggestion(
                    rank=i,
                    scientific_name=species.get("scientificNameWithoutAuthor", ""),
                    common_names=species.get("commonNames", []),
                    family=(species.get("family") or {}).get("scientificNameWithoutAuthor"),
                    genus=(species.get("genus") or {}).get("scientificNameWithoutAuthor"),
                    confidence=result.get("score", 0.0),
                    external_id=str(gbif.get("id", "")),
                    image_url=self._first_image_url(result.get("images")),
                    gbif_id=gbif.get("id"),
                    raw_data=result,
                )
            )

        return IdentificationResult(
            suggestions=suggestions,
            health_assessment=None,  # Pl@ntNet has no health assessment
            is_plant=len(suggestions) > 0,
            api_response_time_ms=elapsed_ms,
        )

    async def diagnose(
        self,
        image_data: bytes,
        *,
        language: str = "de",
    ) -> HealthAssessment:
        raise NotImplementedError(
            "Pl@ntNet does not support health assessment. Use a health-capable adapter for diagnosis."
        )

    async def health_check(self) -> bool:
        return bool(self._api_key)

    @staticmethod
    def _first_image_url(images: list[dict[str, Any]] | None) -> str | None:
        if not images:
            return None
        url = images[0].get("url")
        if isinstance(url, dict):
            return url.get("m") or url.get("o") or url.get("s")
        return url
