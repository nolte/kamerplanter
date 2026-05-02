"""REQ-018 Actuators router scaffold."""

from fastapi import APIRouter

router = APIRouter(prefix="/actuators", tags=["actuators"])
