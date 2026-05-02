"""REQ-016 InvenTree router scaffold (optional integration).

Concrete endpoints (GET /inventree/parts/{id}, POST /inventree/reserve)
follow with the implementation PR.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/inventree", tags=["inventree"])
