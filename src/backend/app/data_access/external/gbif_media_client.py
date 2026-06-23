"""REQ-029-A §4.2 — GBIF Occurrence media client for reference-image acquisition.

Separate from ``GBIFAdapter`` (which serves taxonomic enrichment, REQ-011):
this client queries the GBIF Occurrence API for ``StillImage`` media of a
given ``taxonKey`` and downloads candidate images. License normalisation and
filtering happen in :mod:`app.domain.services.reference_image_license`.
"""

import structlog
from httpx import Client, HTTPStatusError, RequestError

from app.common.exceptions import ExternalSourceError, RateLimitError, ValidationError
from app.common.text import strip_html
from app.common.url_safety import validate_server_side_url
from app.config.settings import settings
from app.domain.models.reference_image import MediaCandidate
from app.domain.services.reference_image_license import normalize_license

logger = structlog.get_logger()

_MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024  # guard against oversized downloads


class GBIFMediaClient:
    """Fetches CC-licensed occurrence images from GBIF."""

    def __init__(self) -> None:
        self._client = Client(
            base_url=settings.gbif.base_url,
            timeout=settings.gbif.http_timeout,
            follow_redirects=True,
        )

    def list_media(self, taxon_key: int, *, limit: int = 40) -> list[MediaCandidate]:
        """Return image candidates (with normalised license) for a taxon.

        Queries occurrences that carry still images. The occurrence-level
        ``license`` is authoritative; the per-media ``license`` is a fallback.
        """
        try:
            response = self._client.get(
                "/occurrence/search",
                params={
                    "taxonKey": taxon_key,
                    "mediaType": "StillImage",
                    "limit": limit,
                },
            )
            if response.status_code == 429:
                raise RateLimitError("gbif", retry_after=60)
            response.raise_for_status()
            payload = response.json()
        except RateLimitError:
            raise
        except (HTTPStatusError, RequestError) as exc:
            raise ExternalSourceError("gbif", f"occurrence search failed: {exc}") from exc

        candidates: list[MediaCandidate] = []
        for occ in payload.get("results", []):
            occ_license = occ.get("license")
            record_id = str(occ.get("key", "")) or None
            for media in occ.get("media", []):
                if media.get("type") and media["type"] != "StillImage":
                    continue
                url = media.get("identifier")
                if not url:
                    continue
                license_value = normalize_license(media.get("license") or occ_license)
                candidates.append(
                    MediaCandidate(
                        url=url,
                        license=license_value,
                        source="gbif",
                        source_record_id=record_id,
                        # Defensive: GBIF rightsHolder/creator are normally plain
                        # text, but strip any stray markup to keep captions clean.
                        attribution=strip_html(media.get("rightsHolder") or media.get("creator")),
                        format=media.get("format"),
                    )
                )
        return candidates

    def download(self, url: str) -> bytes:
        """Download a single image; raises on transport errors, SSRF or oversize.

        The occurrence-media URL is supplied by the GBIF response and dialed
        server-side, so it passes the shared SSRF guard first (https + a public,
        routable address; blocks loopback/RFC1918/link-local incl. the cloud
        metadata 169.254.169.254). Redirects are NOT followed.
        """
        try:
            validate_server_side_url(url, field="gbif_media_url")
        except ValidationError as exc:
            raise ExternalSourceError("gbif", f"image url rejected by SSRF guard: {exc}") from exc
        try:
            response = self._client.get(url, follow_redirects=False)
            response.raise_for_status()
        except (HTTPStatusError, RequestError) as exc:
            raise ExternalSourceError("gbif", f"image download failed: {exc}") from exc
        if response.is_redirect:
            raise ExternalSourceError("gbif", f"image url redirected; not followed (SSRF guard): {url}")
        data = response.content
        if len(data) > _MAX_DOWNLOAD_BYTES:
            raise ExternalSourceError("gbif", f"image exceeds {_MAX_DOWNLOAD_BYTES} bytes")
        return data

    def close(self) -> None:
        self._client.close()
