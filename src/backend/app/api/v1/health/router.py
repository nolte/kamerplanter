from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.v1.health.schemas import LivenessResponse, ReadinessResponse
from app.common.dependencies import get_connection, get_object_storage
from app.migrations.support.retired_indexes import last_enforcement

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=LivenessResponse)
def liveness() -> LivenessResponse:
    """Liveness probe: reports that the process is up."""
    return LivenessResponse(status="alive")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse, "description": "Database or object storage is unreachable."}},
)
async def readiness():
    """Readiness probe (NFR-013 AC-08).

    Reports ``ready`` only when both the primary database and the configured
    object-storage backend are reachable. A storage outage flips readiness to
    HTTP 503 so the pod is taken out of rotation until storage recovers.

    ``retired_indexes_refused`` counts the retired indexes this replica's boot found
    re-created and could not retire again (#2064); it is reported, not gated on. A
    count, not the names: the probe is unauthenticated, the boot log names them.
    """
    conn = get_connection()
    db_ok = conn.is_connected()

    try:
        storage_status = await get_object_storage().health_check()
        storage_ok = bool(storage_status.get("ready"))
    except Exception:  # noqa: BLE001 — any storage failure means not-ready
        storage_ok = False

    overall_ok = db_ok and storage_ok
    enforcement = last_enforcement()
    body = {
        "status": "ready" if overall_ok else "not_ready",
        "database": db_ok,
        "object_storage": storage_ok,
        "retired_indexes_refused": len(enforcement.refused) if enforcement is not None else 0,
    }
    if overall_ok:
        return body
    return JSONResponse(status_code=503, content=body)
