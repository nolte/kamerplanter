import re
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

from app.api.v1.auth.router import limiter
from app.api.v1.openapi_tags import OPENAPI_TAGS
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
from app.data_access.external.registration import register_external_adapters
from app.observability.error_tracking import init_error_tracking, resolve_release

logger = structlog.get_logger()

# Optional error tracking (#777). Called at process entry, before the app object
# exists and long before the first request, so a failure raised during startup is
# already captured. Without SENTRY_DSN this is a no-op and nothing about the
# process changes — which is why it is unconditional here rather than hidden
# behind a settings flag.
init_error_tracking(
    component="backend",
    release=resolve_release("kamerplanter-backend", settings.app_version),
)

# Register every self-registering adapter (weather, pest, identification, storage
# factories) so they are available to the FastAPI process. The Celery worker does
# the same in :mod:`app.tasks`; both share one central list.
register_external_adapters()

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

    # Home Assistant is optional — a missing, unreachable or unresolvable HA_URL
    # must never break startup (graceful degradation, REQ-018). Any failure here
    # just skips the HA notification channel.
    try:
        ha_client = get_ha_client()
        if ha_client is not None:
            from app.data_access.external.ha_notification_channel import HomeAssistantNotificationChannel

            NotificationChannelRegistry.register(HomeAssistantNotificationChannel(ha_client))
            logger.info("notification_channel_registered", channel="home_assistant")
    except Exception:
        logger.warning("notification_channel_registration_failed", channel="home_assistant", exc_info=True)

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
    description=(
        "REST API of Kamerplanter, an agricultural technology system for plant "
        "lifecycle management (houseplants, vegetables, herbs, cannabis): master "
        "data, sites and locations, phase-driven growing logic, fertilization and "
        "watering, hybrid sensing, tasks, harvest and post-harvest, IPM, "
        "multi-tenancy and GDPR self-service. Authentication uses Bearer tokens "
        "(JWT access tokens or `kp_`-prefixed service-account API keys); "
        "operations marked with an empty security list are deliberately public."
    ),
    contact={"name": "Kamerplanter", "url": "https://github.com/nolte/kamerplanter"},
    license_info={"name": "MIT", "identifier": "MIT"},
    servers=[
        {"url": "/", "description": "Current deployment (same origin)"},
        {"url": "http://localhost:8000", "description": "Local development backend"},
    ],
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# OpenAPI post-processing (documentation only, spec/project/api-documentation/):
#  1. FastAPI only emits a `security` requirement on operations whose dependency
#     tree contains a security scheme (HTTPBearer in app.common.auth). An
#     operation without any requirement is deliberately public — stamp it with
#     an explicit `security: []` so document consumers can tell "public by
#     design" from "forgotten security".
#  2. A router mounted under a parameterised prefix (e.g. /t/{tenant_slug})
#     whose operations never consume that path parameter still matches it at
#     runtime, but FastAPI omits it from the generated parameter list — declare
#     it so the document satisfies the OpenAPI path-params contract.
_fastapi_openapi = app.openapi
_PATH_PARAM_RE = re.compile(r"\{([^}]+)\}")


def _openapi_postprocessed() -> dict:
    """Fill in path parameters FastAPI cannot see, and nothing else.

    Deliberately absent: response schemas for the ~31 operations that return
    without one. Those are streaming, file, redirect and SSE responses plus
    dynamic passthrough dicts — a response schema would be a lie about what the
    endpoint sends, so they are documented gaps with a reason rather than
    missing work (#850, from the 2026-07-24 API documentation audit). An audit
    that re-reports them should be pointed at this note instead of at the
    operations.
    """
    schema = _fastapi_openapi()
    http_methods = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
    for path, path_item in schema.get("paths", {}).items():
        template_params = _PATH_PARAM_RE.findall(path)
        for method, operation in path_item.items():
            if method not in http_methods:
                continue
            if "security" not in operation:
                operation["security"] = []
            declared = {p["name"] for p in operation.get("parameters", []) if p.get("in") == "path"}
            for name in template_params:
                if name not in declared:
                    operation.setdefault("parameters", []).append(
                        {
                            "name": name,
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "title": name.replace("_", " ").title()},
                            "description": "Path segment matched by the mount prefix.",
                        }
                    )
    return schema


app.openapi = _openapi_postprocessed  # type: ignore[method-assign]

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
