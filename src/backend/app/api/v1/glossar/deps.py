"""REQ-035 — FastAPI dependency wiring for the glossary service."""

from __future__ import annotations

from app.common.dependencies import get_glossary_service

__all__ = ["get_glossary_service"]
