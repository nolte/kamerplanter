"""REQ-036 KI-Diagnose-Assistent router scaffold."""

from fastapi import APIRouter

router = APIRouter(prefix="/diagnose", tags=["diagnose"])
