from fastapi import APIRouter

from app.common.dependencies import get_connection

router = APIRouter(tags=["health"])


@router.get("/health/live")
def liveness():
    return {"status": "alive"}


@router.get("/health/ready")
def readiness():
    conn = get_connection()
    db_ok = conn.is_connected()
    return {"status": "ready" if db_ok else "not_ready", "database": db_ok}
