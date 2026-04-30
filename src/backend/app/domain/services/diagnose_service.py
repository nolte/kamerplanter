"""REQ-036 KI-Diagnose-Assistent service scaffold."""

from __future__ import annotations

from typing import Any


class DiagnoseService:
    """Scaffold service — pins the public surface for REQ-036."""

    def __init__(self, llm_adapter: Any | None = None, vision_engine: Any | None = None) -> None:
        self._llm_adapter = llm_adapter
        self._vision_engine = vision_engine

    async def diagnose(self, plant_key: str, photos: list[bytes], symptoms: str) -> dict[str, Any]:
        raise NotImplementedError("REQ-036 DiagnoseService.diagnose — pending follow-up.")
