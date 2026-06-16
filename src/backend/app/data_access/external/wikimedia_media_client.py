"""REQ-029-A §4.1 — Wikimedia Commons media client for reference images.

A second acquisition source besides GBIF (``gbif_media_client``), aimed at
rare/exotic species whose GBIF occurrence coverage is thin. It resolves the
species' Commons category (``Category:<scientific name>``) and returns the
contained still images with normalised license metadata.

Wikimedia requires a descriptive ``User-Agent``; requests without one are
rejected. License normalisation reuses
:mod:`app.domain.services.reference_image_license`.
"""

import structlog
from httpx import Client, HTTPStatusError, RequestError

from app.common.exceptions import ExternalSourceError
from app.config.settings import settings
from app.domain.models.reference_image import MediaCandidate
from app.domain.services.reference_image_license import normalize_license

logger = structlog.get_logger()

_USER_AGENT = "Kamerplanter/1.0 (plant reference-image acquisition; +https://github.com/nolte/kamerplanter)"
_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp")
_MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024


class WikimediaCommonsMediaClient:
    """Fetches CC-licensed images from a species' Wikimedia Commons category."""

    def __init__(self) -> None:
        self._client = Client(
            base_url=settings.wikimedia_commons_api_url,
            timeout=settings.gbif.http_timeout,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )

    def list_media(self, scientific_name: str, *, limit: int = 40) -> list[MediaCandidate]:
        """Return image candidates from ``Category:<scientific_name>``.

        Uses a single ``generator=categorymembers`` query that also pulls each
        file's ``imageinfo`` (URL + ``extmetadata`` license/attribution).
        """
        try:
            response = self._client.get(
                "",
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "categorymembers",
                    "gcmtitle": f"Category:{scientific_name}",
                    "gcmtype": "file",
                    "gcmlimit": limit,
                    "prop": "imageinfo",
                    "iiprop": "url|extmetadata",
                    "iiurlwidth": 1024,
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (HTTPStatusError, RequestError) as exc:
            raise ExternalSourceError(f"Wikimedia Commons query failed: {exc}") from exc

        pages = payload.get("query", {}).get("pages", {})
        candidates: list[MediaCandidate] = []
        for page in pages.values():
            info_list = page.get("imageinfo")
            if not info_list:
                continue
            info = info_list[0]
            url = info.get("thumburl") or info.get("url")
            if not url or not url.lower().endswith(_IMAGE_EXTENSIONS):
                continue
            meta = info.get("extmetadata", {})
            raw_license = meta.get("License", {}).get("value") or meta.get("LicenseShortName", {}).get("value")
            candidates.append(
                MediaCandidate(
                    url=url,
                    license=normalize_license(raw_license),
                    source="wikimedia",
                    source_record_id=str(page.get("pageid", "")) or None,
                    attribution=meta.get("Artist", {}).get("value"),
                )
            )
        return candidates

    def download(self, url: str) -> bytes:
        """Download a single image; raises on transport errors or oversize."""
        try:
            response = self._client.get(url)
            response.raise_for_status()
        except (HTTPStatusError, RequestError) as exc:
            raise ExternalSourceError(f"Wikimedia image download failed: {exc}") from exc
        data = response.content
        if len(data) > _MAX_DOWNLOAD_BYTES:
            raise ExternalSourceError(f"Image exceeds {_MAX_DOWNLOAD_BYTES} bytes")
        return data

    def close(self) -> None:
        self._client.close()
