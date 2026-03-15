from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import app.data_access.external.gbif_adapter  # noqa: F401  register adapter
import app.data_access.external.perenual_adapter  # noqa: F401  register adapter
from app.api.v1.auth.router import limiter
from app.api.v1.router import api_router
from app.common.dependencies import close_connection, get_connection
from app.common.error_handlers import (
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.common.exceptions import KamerplanterError
from app.config.logging import setup_logging
from app.config.settings import settings
from app.data_access.arango.collections import ensure_collections

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.debug)
    logger.info("startup", app=settings.app_name, version=settings.app_version)

    conn = get_connection()
    db = conn.connect()
    ensure_collections(db)
    logger.info("database_ready")

    from app.migrations.seed_location_types import seed_location_types

    seed_location_types(db)

    from app.migrations.seed_data import run_seed

    run_seed()

    from app.migrations.seed_adventskalender import run_seed_adventskalender

    run_seed_adventskalender()

    from app.migrations.seed_plant_info import run_seed_plant_info

    run_seed_plant_info()

    from app.migrations.seed_plant_info_extended import run_seed_plant_info_extended

    run_seed_plant_info_extended()

    from app.migrations.seed_plagron import run_seed_plagron

    run_seed_plagron()

    from app.migrations.seed_gardol import run_seed_gardol

    run_seed_gardol()

    from app.migrations.seed_nutrient_plans_outdoor import (
        run_seed_nutrient_plans_outdoor,
    )

    run_seed_nutrient_plans_outdoor()

    from app.migrations.seed_activities import run_seed_activities

    run_seed_activities()

    from app.migrations.seed_lifecycles_outdoor import run_seed_lifecycles_outdoor

    run_seed_lifecycles_outdoor()

    if settings.kamerplanter_mode == "light":
        from app.migrations.seed_light_mode import run_seed_light_mode

        run_seed_light_mode()
        logger.info("light_mode_active")

    yield

    close_connection()
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next) -> Response:  # type: ignore[type-arg]
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not settings.debug:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/health", tags=["health"])
def root_health() -> dict[str, str]:
    """Root-level health endpoint for M2M consumers (HA integration)."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "mode": settings.kamerplanter_mode,
    }


# Static file serving for task photo uploads
upload_dir = Path(settings.upload_dir)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/tasks", StaticFiles(directory=str(upload_dir)), name="task_uploads")

app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]
