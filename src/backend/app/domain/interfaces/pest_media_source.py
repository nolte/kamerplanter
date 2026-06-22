"""REQ-044 WP-3 — ABC for pest reference-image media sources.

Each acquisition source (GBIF, iNaturalist, iDigBio, …) implements this
interface so :class:`PestDatasetAcquisitionService` can iterate a configured
list of sources uniformly. Unlike the plant ``GBIFMediaClient`` (keyed by a
GBIF ``taxonKey``), pest sources receive the full :class:`PestTaxon` so each can
resolve its own taxon identifier (GBIF key vs. iNat taxon_id) and apply
per-source filters such as iNaturalist's ``lifeStage`` annotation.

License normalisation lives in
:mod:`app.domain.services.reference_image_license`; concrete clients must return
candidates with an already-normalised :class:`ReferenceLicense`.
"""

from abc import ABC, abstractmethod

from app.domain.models.pest_taxonomy import PestTaxon
from app.domain.models.reference_image import MediaCandidate


class PestMediaSource(ABC):
    """A license-aware media source for pest/beneficial reference images."""

    #: Stable identifier used in settings (``pest_reference_sources``) and in the
    #: attribution manifest's ``source`` field.
    source_key: str

    @abstractmethod
    def list_media(self, taxon: PestTaxon, *, limit: int) -> list[MediaCandidate]:
        """Return up to ``limit`` candidate images for ``taxon``.

        Each candidate carries a normalised :class:`ReferenceLicense`; the
        caller applies the license/attribution/quality gate. Implementations
        must raise on transport errors so the orchestrator can fall back to the
        next source rather than silently dropping a class.
        """

    @abstractmethod
    def download(self, url: str) -> bytes:
        """Download a single candidate image; raises on transport errors/oversize."""

    def close(self) -> None:
        """Release any held HTTP resources. Default no-op for stateless sources."""
        return None
