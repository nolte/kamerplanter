"""REQ-008 Post-Harvest router scaffold.

The actual endpoints (POST /post-harvest/start-drying, GET
/post-harvest/{key}, POST /post-harvest/{key}/advance) land with the
REQ-008 follow-up PR. Today the router is a placeholder so wiring
elsewhere can already reference it.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/post-harvest", tags=["post-harvest"])
