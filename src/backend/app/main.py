from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

import app.data_access.external.gbif_adapter  # noqa: F401  register adapter
import app.data_access.external.perenual_adapter  # noqa: F401  register adapter
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

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.debug)
    logger.info("startup", app=settings.app_name, version=settings.app_version)

    conn = get_connection()
    db = conn.connect()
    ensure_collections(db)
    logger.info("database_ready")

    yield

    close_connection()
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]
