"""REQ-044 WP-3 — iNaturalist direct-API pest media source.

A second/third acquisition source beside GBIF, using the iNaturalist REST API
(``https://api.inaturalist.org/v1``) directly. Two iNat specifics drive the
design (pest-image-sources-analysis.md §4.1):

1. **Per-photo license, not observation license.** iNat licenses each photo
   separately from its observation (observation default is CC-BY-NC). We filter
   on the per-photo ``photo_license`` query parameter AND re-check each photo's
   own ``license_code`` before accepting it — never the observation license.

2. **lifeStage annotation for the larvae gap.** iNat exposes life-stage as a
   controlled-term *annotation* (term ``Life Stage`` id=1, value ``Larva`` id=6).
   The observations endpoint accepts ``term_id`` + ``term_value_id`` to filter on
   it. Annotation coverage is voluntary and incomplete, so this *narrows* (never
   guarantees) results; ``PestTaxon.inat_life_stage`` opts a class in.

GBIF ``taxon_key``s are NOT iNat ids. We resolve the iNat ``taxon_id`` per taxon
via ``/v1/taxa?q=<scientific name>`` (cached per process), unless the taxon pins
an explicit ``inat_taxon_id``. Resolve-by-name is the more robust default: it
needs no hand-maintained id table and tolerates iNat id changes.

iNat asks for a descriptive User-Agent and rate-limits to ~60 req/min; this
client sends a polite UA and a conservative timeout. It performs NO real network
calls at import time.
"""

import structlog
from httpx import Client, HTTPStatusError, RequestError

from app.common.exceptions import ExternalSourceError, RateLimitError, ValidationError
from app.common.text import strip_html
from app.common.url_safety import validate_server_side_url
from app.config.settings import settings
from app.domain.interfaces.pest_media_source import PestMediaSource
from app.domain.models.pest_taxonomy import PestTaxon
from app.domain.models.reference_image import MediaCandidate
from app.domain.services.reference_image_license import normalize_license

logger = structlog.get_logger()

_USER_AGENT = "Kamerplanter/1.0 (pest reference-image acquisition; +https://github.com/nolte/kamerplanter)"
_MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024

# iNaturalist controlled-term "Life Stage" (term_id=1) and its value ids. These
# ids are stable iNat platform constants. TODO(REQ-044 §8): annotation coverage
# is voluntary/incomplete — if a class yields too few larvae here, fall back to
# the unfiltered taxon query (the orchestrator already tops up from GBIF).
_LIFE_STAGE_TERM_ID = 1
_LIFE_STAGE_VALUE_IDS: dict[str, int] = {
    "larva": 6,
    "nymph": 8,
    "adult": 2,
    "egg": 5,
    "pupa": 7,
}

# iNat license_code tokens map cleanly through normalize_license, but iNat omits
# the license for "all rights reserved" photos (license_code is null) — those
# normalise to UNKNOWN and are rejected downstream.


class INaturalistMediaClient(PestMediaSource):
    """Fetches research-grade, per-photo-CC-licensed images from iNaturalist."""

    source_key = "inaturalist"

    def __init__(self, client: Client | None = None) -> None:
        self._client = client or Client(
            base_url=settings.inaturalist_base_url,
            timeout=settings.inaturalist_http_timeout,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )
        # Per-process cache of scientific name → iNat taxon_id to avoid repeat
        # /taxa lookups within a single acquisition run.
        self._taxon_id_cache: dict[str, int | None] = {}

    def list_media(self, taxon: PestTaxon, *, limit: int) -> list[MediaCandidate]:
        """Return research-grade image candidates for ``taxon`` (per-photo license)."""
        taxon_id = self._resolve_taxon_id(taxon)
        if taxon_id is None:
            return []

        params: dict[str, str | int] = {
            "taxon_id": taxon_id,
            "quality_grade": "research",
            "photos": "true",
            "per_page": min(limit, settings.inaturalist_per_page),
            "order_by": "votes",
            "order": "desc",
            # Per-PHOTO license filter (not observation license). iNat accepts a
            # comma-separated list of photo_license tokens.
            "photo_license": "cc0,cc-by,cc-by-nc",
        }
        # lifeStage annotation filter for the beneficial-larvae gap.
        value_id = self._life_stage_value_id(taxon.inat_life_stage)
        if value_id is not None:
            params["term_id"] = _LIFE_STAGE_TERM_ID
            params["term_value_id"] = value_id

        payload = self._get("/observations", params)
        candidates: list[MediaCandidate] = []
        for obs in payload.get("results", []):
            record_id = str(obs.get("id", "")) or None
            attribution = self._observation_attribution(obs)
            for photo in obs.get("photos", []):
                candidate = self._photo_to_candidate(photo, record_id, attribution)
                if candidate is not None:
                    candidates.append(candidate)
                if len(candidates) >= limit:
                    return candidates
        return candidates

    def download(self, url: str) -> bytes:
        """Download a single image; raises on transport errors, SSRF or oversize.

        The photo URL is supplied by the iNaturalist API response and dialed
        server-side, so it passes the shared SSRF guard first (https + a public,
        routable address; blocks loopback/RFC1918/link-local incl. the cloud
        metadata 169.254.169.254). Redirects are NOT followed — a 3xx could
        otherwise bounce to an internal target after the check passed.
        """
        try:
            validate_server_side_url(url, field="inaturalist_photo_url")
        except ValidationError as exc:
            raise ExternalSourceError(self.source_key, f"image url rejected by SSRF guard: {exc}") from exc
        try:
            response = self._client.get(url, follow_redirects=False)
            response.raise_for_status()
        except (HTTPStatusError, RequestError) as exc:
            raise ExternalSourceError(self.source_key, f"image download failed: {exc}") from exc
        if response.is_redirect:
            raise ExternalSourceError(self.source_key, f"image url redirected; not followed (SSRF guard): {url}")
        data = response.content
        if len(data) > _MAX_DOWNLOAD_BYTES:
            raise ExternalSourceError(self.source_key, f"image exceeds {_MAX_DOWNLOAD_BYTES} bytes")
        return data

    def close(self) -> None:
        self._client.close()

    # ── internals ──────────────────────────────────────────────────────

    def _resolve_taxon_id(self, taxon: PestTaxon) -> int | None:
        """Return the iNat taxon_id: explicit pin, cache, or /taxa name lookup."""
        if taxon.inat_taxon_id is not None:
            return taxon.inat_taxon_id
        name = taxon.scientific_name.strip()
        if not name:
            return None
        if name in self._taxon_id_cache:
            return self._taxon_id_cache[name]

        payload = self._get("/taxa", {"q": name, "per_page": 1})
        results = payload.get("results", [])
        resolved = int(results[0]["id"]) if results and results[0].get("id") is not None else None
        if resolved is None:
            logger.info("inat_taxon_unresolved", scientific_name=name)
        self._taxon_id_cache[name] = resolved
        return resolved

    @staticmethod
    def _life_stage_value_id(life_stage: str | None) -> int | None:
        if not life_stage:
            return None
        return _LIFE_STAGE_VALUE_IDS.get(life_stage.strip().lower())

    @staticmethod
    def _photo_to_candidate(photo: dict, record_id: str | None, attribution: str | None) -> MediaCandidate | None:
        """Build a candidate from a single iNat photo, honouring its OWN license."""
        url = INaturalistMediaClient._photo_url(photo)
        if not url:
            return None
        # Re-check the per-photo license even though we filtered server-side:
        # license_code is the photo's own license, not the observation's.
        license_value = normalize_license(photo.get("license_code"))
        return MediaCandidate(
            url=url,
            license=license_value,
            source="inaturalist",
            source_record_id=str(photo.get("id", "")) or record_id,
            attribution=strip_html(photo.get("attribution")) or attribution,
        )

    @staticmethod
    def _photo_url(photo: dict) -> str | None:
        """Prefer a medium-sized derivative; iNat stores a ``square`` thumb url."""
        url = photo.get("url")
        if not url:
            return None
        # iNat photo urls embed the size as ``/square.jpg``; request a usable size.
        return url.replace("/square.", "/medium.")

    @staticmethod
    def _observation_attribution(obs: dict) -> str | None:
        user = obs.get("user") or {}
        name = user.get("name") or user.get("login")
        return strip_html(name)

    def _get(self, path: str, params: dict) -> dict:
        try:
            response = self._client.get(path, params=params)
            if response.status_code == 429:
                raise RateLimitError("inaturalist", retry_after=60)
            response.raise_for_status()
            return response.json()
        except RateLimitError:
            raise
        except (HTTPStatusError, RequestError) as exc:
            raise ExternalSourceError(self.source_key, f"request to {path} failed: {exc}") from exc
