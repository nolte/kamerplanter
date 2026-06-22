"""REQ-044 WP-3 — GBIF pest media source.

Thin :class:`PestMediaSource` adapter over the existing :class:`GBIFMediaClient`
(plant reference-image acquisition). It maps a :class:`PestTaxon` to the GBIF
``taxonKey`` and delegates the occurrence-media query/download unchanged, so the
plant pipeline keeps using ``GBIFMediaClient`` directly while the pest
orchestrator sees a uniform source interface.

GBIF has no ``lifeStage`` query parameter, so ``inat_life_stage`` is ignored
here (it is honoured by the iNaturalist source instead).
"""

from app.data_access.external.gbif_media_client import GBIFMediaClient
from app.domain.interfaces.pest_media_source import PestMediaSource
from app.domain.models.pest_taxonomy import PestTaxon
from app.domain.models.reference_image import MediaCandidate


class GBIFPestMediaSource(PestMediaSource):
    """GBIF occurrence images, keyed by the taxon's GBIF ``taxonKey``."""

    source_key = "gbif"

    def __init__(self, client: GBIFMediaClient | None = None) -> None:
        self._client = client or GBIFMediaClient()

    def list_media(self, taxon: PestTaxon, *, limit: int) -> list[MediaCandidate]:
        if not taxon.gbif_taxon_key:
            return []
        return self._client.list_media(int(taxon.gbif_taxon_key), limit=limit)

    def download(self, url: str) -> bytes:
        return self._client.download(url)

    def close(self) -> None:
        self._client.close()
