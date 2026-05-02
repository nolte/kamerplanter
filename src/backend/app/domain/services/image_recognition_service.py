"""REQ-029 Image-recognition service scaffold (KI Bilderkennung).

Calls the Knowledge Service (`src/knowledge-service/`) for Plant.id-
style species identification from photos. Concrete adapter wiring
lands with the REQ-029 follow-up PR.
"""

from __future__ import annotations

from typing import Any


class ImageRecognitionService:
    """Scaffold service — pins the public surface for REQ-029."""

    def __init__(self, knowledge_client: Any | None = None) -> None:
        self._knowledge_client = knowledge_client

    async def identify_from_photo(self, image_bytes: bytes) -> list[dict[str, Any]]:
        raise NotImplementedError("REQ-029 ImageRecognitionService.identify_from_photo — pending follow-up.")
