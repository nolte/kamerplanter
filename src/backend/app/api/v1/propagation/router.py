"""REQ-017 Propagation router scaffold."""

from fastapi import APIRouter

router = APIRouter(prefix="/propagation", tags=["propagation"])
