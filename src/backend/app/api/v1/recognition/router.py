"""REQ-029 KI-Bilderkennung router scaffold."""

from fastapi import APIRouter

router = APIRouter(prefix="/recognition", tags=["recognition"])
