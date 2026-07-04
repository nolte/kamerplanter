from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import app.data_access.external.demo_pest_adapter  # noqa: F401  register REQ-044 demo adapter (opt-in preview)
import app.data_access.external.gbif_adapter  # noqa: F401  register adapter
import app.data_access.external.kindwise_pest_adapter  # noqa: F401  register REQ-044 cloud adapter (opt-in)
import app.data_access.external.local_embedding_adapter  # noqa: F401  register identification adapter (priority 1)
import app.data_access.external.local_pest_adapters  # noqa: F401  register REQ-044 self-hosted adapters
import app.data_access.external.perenual_adapter  # noqa: F401  register adapter
import app.data_access.external.plantnet_adapter  # noqa: F401  register REQ-029 adapter
import app.data_access.storage.registry  # noqa: F401  register NFR-013 storage adapter factories
from app.api.v1.auth.router import limiter
from app.api.v1.router import api_router
from app.common.dependencies import close_connection, get_connection, get_ha_client
from app.common.error_handlers import (
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.common.exceptions import KamerplanterError
from app.common.middleware import request_id_middleware
from app.config.logging import setup_logging
from app.config.settings import settings
from app.data_access.arango.collections import ensure_collections

logger = structlog.get_logger()

# NFR-011 §4: the erasure tombstone salt must be a high-entropy secret; a value
# shorter than this is treated as unset/insecure.
_MIN_TOMBSTONE_SALT_LENGTH = 32


def insecure_default_secrets() -> list[str]:
    """Return the names of default/missing secrets that block a secure startup.

    Empty list => safe to start. Extracted from the lifespan so it can be
    unit-tested directly (AP-4, INF-S5). Evaluated against the module-level
    ``settings`` singleton.
    """
    insecure: list[str] = []
    if settings.jwt_secret_key == "change-me-in-production-use-openssl-rand-hex-32":
        insecure.append("jwt_secret_key")
    if settings.arangodb_password == "rootpassword":
        insecure.append("arangodb_password")
    if settings.timescaledb_enabled and settings.timescaledb_password == "changeme":
        insecure.append("timescaledb_password")
    # INF-S5: OIDC provider-secret encryption key (Fernet). Must be provisioned.
    if not settings.fernet_key:
        insecure.append("fernet_key")
    # NFR-011 §4: GDPR erasure tombstone salt (>= 32 chars).
    if len(settings.erasure_tombstone_salt) < _MIN_TOMBSTONE_SALT_LENGTH:
        insecure.append("erasure_tombstone_salt")
    # AP-4: shared secret for the internal M2M services — required only when the
    # backend actually calls them.
    if (
        settings.knowledge_service_enabled or settings.inference_service_enabled
    ) and not settings.internal_service_token:
        insecure.append("internal_service_token")
    return insecure


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.debug)
    logger.info("startup", app=settings.app_name, version=settings.app_version)

    # Check for default secrets in production
    if not settings.debug:
        _insecure = insecure_default_secrets()
        if _insecure:
            msg = (
                "FATAL: Default secrets detected for: "
                f"{', '.join(_insecure)}. "
                "Set proper values via environment variables "
                "before running in production."
            )
            logger.critical("insecure_defaults", fields=_insecure)
            raise SystemExit(msg)

    conn = get_connection()
    db = conn.connect()
    ensure_collections(db)
    logger.info("database_ready")

    # NFR-016 / ADR-005: versioned, tracked, lock-guarded migrations run FIRST
    # (fatal on failure — a stale-enum volume must be repaired before any seed
    # reads it, e.g. the retired `harvest` phase from #306). Then the seed
    # registry runs with per-seed error isolation (a bad reference-data seed no
    # longer wedges the whole startup).
    from app.migrations.framework.runner import run_pending_migrations
    from app.migrations.seeds.registry import run_seeds

    run_pending_migrations(db)
    run_seeds(db)

    if settings.kamerplanter_mode == "light":
        logger.info("light_mode_active")

    # Register notification channels
    from app.domain.engines.notification_channel_registry import NotificationChannelRegistry

    ha_client = get_ha_client()
    if ha_client is not None:
        from app.data_access.external.ha_notification_channel import HomeAssistantNotificationChannel

        NotificationChannelRegistry.register(HomeAssistantNotificationChannel(ha_client))
        logger.info("notification_channel_registered", channel="home_assistant")

    from app.data_access.external.apprise_notification_channel import AppriseNotificationChannel

    NotificationChannelRegistry.register(AppriseNotificationChannel())
    logger.info("notification_channel_registered", channel="apprise")

    # Email channel (unconditional, best-effort — must not break startup)
    try:
        from app.common.dependencies import get_email_service
        from app.data_access.external.email_notification_channel import EmailNotificationChannel

        NotificationChannelRegistry.register(EmailNotificationChannel(get_email_service()))
        logger.info("notification_channel_registered", channel="email")
    except Exception:
        logger.warning("notification_channel_registration_failed", channel="email", exc_info=True)

    # Web Push (PWA / browser) channel — only if VAPID keys are configured
    if settings.vapid_public_key and settings.vapid_private_key:
        from app.data_access.external.pwa_notification_channel import PwaNotificationChannel

        NotificationChannelRegistry.register(
            PwaNotificationChannel(settings.vapid_private_key, settings.vapid_contact_email)
        )
        logger.info("notification_channel_registered", channel="pwa")

    # mDNS / Zeroconf Discovery (optional)
    mdns_announcer = None
    if settings.mdns_enabled:
        from app.common.mdns import MdnsAnnouncer, create_service_info, generate_instance_id

        instance_id = settings.instance_id or generate_instance_id()
        info = create_service_info(
            port=8000,
            version=settings.app_version,
            mode=settings.kamerplanter_mode,
            instance_id=instance_id,
        )
        mdns_announcer = MdnsAnnouncer(info)
        mdns_announcer.start()

    # TimescaleDB init (optional)
    if settings.timescaledb_enabled:
        from app.common.dependencies import get_timescale_connection
        from app.data_access.timescale.schema import ensure_timescale_schema

        ts_conn = get_timescale_connection()
        if ts_conn:
            ts_conn.connect()
            ensure_timescale_schema(ts_conn.pool)
            logger.info("timescaledb_ready")
        else:
            logger.warning("timescaledb_enabled_but_connection_failed")

    yield

    if mdns_announcer:
        mdns_announcer.stop()
    close_connection()
    logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
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
    # API responses are JSON. A `default-src 'none'` CSP is the strictest
    # safe option: nothing should be loaded from a JSON document. The
    # /docs and /redoc endpoints serve HTML+JS via FastAPI's bundled
    # CDN-based Swagger UI; relaxing CSP for them would defeat the
    # purpose, so the deployment is expected to disable those endpoints
    # in production (NFR-014 §3.2 / kamerplanter-debug-endpoints.yaml).
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


# Request-ID middleware — registered AFTER security_headers so it runs FIRST (LIFO)
@app.middleware("http")
async def _request_id_middleware(request: Request, call_next) -> Response:  # type: ignore[type-arg]
    return await request_id_middleware(request, call_next)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api/health", tags=["health"])
def root_health() -> dict:
    """Root-level health endpoint for M2M consumers (HA integration)."""
    result: dict = {
        "status": "healthy",
        "version": settings.app_version,
        "mode": settings.kamerplanter_mode,
    }
    if settings.timescaledb_enabled:
        from app.common.dependencies import get_observation_repo

        result["timescaledb"] = "available" if get_observation_repo().is_available() else "unavailable"
    if settings.knowledge_service_enabled:
        from app.common.dependencies import get_knowledge_client

        client = get_knowledge_client()
        result["knowledge_service"] = "available" if client and client.health() else "unavailable"
    return result


# Static file serving for task photo uploads.
# Mounting is best-effort: a non-writable upload location (e.g. a missing
# volume in local/CI environments) must not prevent the application from
# starting. The upload endpoints degrade gracefully when the directory is
# unavailable.
upload_dir = Path(settings.upload_dir)
try:
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads/tasks", StaticFiles(directory=str(upload_dir)), name="task_uploads")
except OSError as exc:
    logger.warning("upload_dir_unavailable", path=str(upload_dir), error=str(exc))

app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_error_handler)  # type: ignore[arg-type]
