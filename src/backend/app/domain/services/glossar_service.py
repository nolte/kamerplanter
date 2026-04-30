"""REQ-035 KI-Fachbegriff-Glossar service scaffold."""

from __future__ import annotations

from typing import Any


class GlossarService:
    """Scaffold service — pins the public surface for REQ-035."""

    def __init__(self, knowledge_client: Any | None = None) -> None:
        self._knowledge_client = knowledge_client

    def explain(self, term: str, locale: str = "de") -> dict[str, Any]:
        raise NotImplementedError("REQ-035 GlossarService.explain — pending follow-up.")
