"""REQ-031 KI-Assistent service scaffold (Pflanzenberatung)."""

from __future__ import annotations

from typing import Any


class KiAssistentService:
    """Scaffold service — pins the public surface for REQ-031."""

    def __init__(self, llm_adapter: Any | None = None, knowledge_client: Any | None = None) -> None:
        self._llm_adapter = llm_adapter
        self._knowledge_client = knowledge_client

    async def answer(self, question: str, plant_context: dict[str, Any] | None = None) -> str:
        raise NotImplementedError("REQ-031 KiAssistentService.answer — pending follow-up.")
