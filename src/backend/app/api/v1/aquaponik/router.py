"""REQ-026 Aquaponik router scaffold."""

from fastapi import APIRouter

router = APIRouter(prefix="/aquaponik", tags=["aquaponik"])
