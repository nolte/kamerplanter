"""REQ-035 KI-Fachbegriff-Glossar router scaffold."""

from fastapi import APIRouter

router = APIRouter(prefix="/glossar", tags=["glossar"])
