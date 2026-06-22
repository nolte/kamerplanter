"""REQ-044 WP-3 — iDigBio media-search pest source (secondary/optional).

Uses the iDigBio media search endpoint ``/v2/search/media/`` with a record-query
(``rq``) taxon filter. iDigBio has no media-native taxon field, so the taxon is
matched indirectly against the *record* taxonomy via ``scientificname`` /
``family`` / ``genus`` (pest-image-sources-analysis.md §4.1). License is
filterable server-side through the same ``rq`` query.

NOTE: iDigBio is specimen-/herbarium-biased; the live-pest yield for these 12
taxa (especially the <0.5 mm spider mite and beneficial nymphs) is historically
thin and largely untested. A zero-yield smoke test is acceptable — this adapter
exists for completeness and future coverage, not as a primary source.

Family-rank scientific names in the taxonomy (e.g. ``Aphididae``, ``Sciaridae``)
are matched on the ``family`` field; binomials on ``scientificname``. No real
network calls happen at import time.
"""

import json

import structlog
from httpx import Client, HTTPStatusError, RequestError

from app.common.exceptions import ExternalSourceError, RateLimitError, ValidationError
from app.common.url_safety import validate_server_side_url
from app.config.settings import settings
from app.domain.interfaces.pest_media_source import PestMediaSource
from app.domain.models.pest_taxonomy import PestTaxon
from app.domain.models.reference_image import MediaCandidate
from app.domain.services.reference_image_license import normalize_license

logger = structlog.get_logger()

_USER_AGENT = "Kamerplanter/1.0 (pest reference-image acquisition; +https://github.com/nolte/kamerplanter)"
_MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024

# Server-side license filter: only the redistributable CC classes. CC-BY-NC is
# included so the orchestrator's allow_noncommercial gate (not the wire query)
# remains the single decision point; rejected classes are dropped downstream.
_ACCEPTED_LICENSE_TOKENS = [
    "cc0",
    "http://creativecommons.org/publicdomain/zero/1.0/",
    "cc-by",
    "http://creativecommons.org/licenses/by/4.0/",
    "cc-by-nc",
    "http://creativecommons.org/licenses/by-nc/4.0/",
]


class IDigBioMediaClient(PestMediaSource):
    """Fetches CC-licensed media from iDigBio's specimen/media index."""

    source_key = "idigbio"

    def __init__(self, client: Client | None = None) -> None:
        self._client = client or Client(
            base_url=settings.idigbio_base_url,
            timeout=settings.idigbio_http_timeout,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )

    def list_media(self, taxon: PestTaxon, *, limit: int) -> list[MediaCandidate]:
        """Return media candidates whose record matches ``taxon`` by name/family."""
        name = taxon.scientific_name.strip()
        if not name:
            return []

        rq = {self._taxon_field(name): name.lower(), "hasImage": True}
        params = {
            "rq": self._json(rq),
            "mq": self._json({"dcterms:rights": _ACCEPTED_LICENSE_TOKENS}),
            "limit": limit,
        }
        payload = self._get("/search/media/", params)

        candidates: list[MediaCandidate] = []
        for item in payload.get("items", []):
            indexed = item.get("indexTerms", {})
            url = indexed.get("accessuri") or indexed.get("ac:accessURI")
            if not url:
                continue
            candidates.append(
                MediaCandidate(
                    url=url,
                    license=normalize_license(indexed.get("rights") or indexed.get("dcterms:rights")),
                    source="idigbio",
                    source_record_id=str(item.get("uuid", "")) or None,
                    attribution=indexed.get("rightsholder") or indexed.get("dc:rights"),
                    format=indexed.get("format"),
                )
            )
            if len(candidates) >= limit:
                break
        return candidates

    def download(self, url: str) -> bytes:
        """Download a single image; raises on transport errors, SSRF or oversize.

        The image URL is taken from a third-party record's ``accessuri`` and
        dialed server-side, so it passes the shared SSRF guard first (https + a
        public, routable address; blocks loopback/RFC1918/link-local incl. the
        cloud metadata 169.254.169.254). Redirects are NOT followed. NOTE: the
        https-only guard rejects plain-``http`` ``accessuri`` values — acceptable
        for this thin, secondary specimen source (pest-image-sources-analysis.md §4.1).
        """
        try:
            validate_server_side_url(url, field="idigbio_access_uri")
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

    @staticmethod
    def _taxon_field(name: str) -> str:
        """Family-rank names (single word ending in -idae/-aceae) → ``family``."""
        token = name.lower()
        if " " not in name and (token.endswith("idae") or token.endswith("inae")):
            return "family"
        return "scientificname"

    @staticmethod
    def _json(value: dict) -> str:
        return json.dumps(value)

    def _get(self, path: str, params: dict) -> dict:
        try:
            response = self._client.get(path, params=params)
            if response.status_code == 429:
                raise RateLimitError("idigbio", retry_after=60)
            response.raise_for_status()
            return response.json()
        except RateLimitError:
            raise
        except (HTTPStatusError, RequestError) as exc:
            raise ExternalSourceError(self.source_key, f"request to {path} failed: {exc}") from exc
