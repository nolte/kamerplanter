"""MT-032 (#2128) — which queue every Celery task runs on, and how long it may run.

Until #2128 every task went to Celery's one default queue ``celery``, without a
time limit (except ``glossary.warm_cache``), and the worker reserved four
messages per process ahead of the one it was running. A long dataset or image
job therefore held a worker process for as long as it liked while the messages
reserved behind it — retention sweeps, care reminders, frost warnings of every
tenant — waited for it.

**Three queues.**

* ``critical`` — what has a legal deadline or a person waiting on a clock:
  retention and erasure (NFR-011), security/privacy sweeps, notifications, frost
  warnings, the actuator control loop.
* ``celery`` — Celery's default queue, kept under its old name on purpose: a
  worker started with an old configuration (no ``-Q``) still consumes it, and a
  task this table does not route (it cannot happen while the guard holds, but a
  message published by an older image can) lands there, never on a queue
  nobody reads.
* ``bulk`` — long, external, resumable work: dataset and reference-image
  acquisition, enrichment syncs, glossary warm-up, storage migrations.

Every queue is declared in ``task_queues``; a worker started without ``-Q``
consumes all of them, and the Helm chart names all three explicitly
(``scripts/ci/assert_chart_contracts.sh``). Running ``bulk`` in a worker of its
own is the next step (the audit's per-queue deployment); the routing below is
its precondition, and an operator can do it today with ``-Q bulk`` / ``-X bulk``.

**Time limits** are a backstop against a hung task, not a budget: a soft limit
raises ``SoftTimeLimitExceeded`` inside the task, the hard limit kills the
process five minutes later. :data:`LONG_RUNNING_TASKS` get three hours — work
that is resumable or operator-started and can legitimately run long. The Redis
``visibility_timeout`` is above the longest hard limit: with ``acks_late`` off a
message is acknowledged when its task starts, but a message *reserved* behind
a running task is not, and Redis hands it to another worker once the timeout
passes — a second run of the same task.

The guard ``tests/unit/guards/test_every_task_has_a_queue.py`` holds every
registered task to exactly one of the three sets below.
"""

from __future__ import annotations

from typing import Final

from kombu import Exchange, Queue

QUEUE_CRITICAL: Final = "critical"
QUEUE_DEFAULT: Final = "celery"
QUEUE_BULK: Final = "bulk"

#: Every queue a worker must consume. Order = the order the chart passes to ``-Q``.
QUEUES: Final[tuple[str, ...]] = (QUEUE_CRITICAL, QUEUE_DEFAULT, QUEUE_BULK)

CRITICAL_TASKS: Final = frozenset(
    {
        # NFR-011 retention and erasure
        "retention.anonymize_consent_ips",
        "retention.execute_scheduled_erasures",
        "retention.expire_data_exports",
        "retention.expire_email_change_requests",
        "retention.purge_expired_consent_records",
        "retention.purge_expired_erasure_records",
        "retention.purge_expired_legal_retention_rows",
        "retention.purge_expired_tenant_erasure_records",
        "retention.redispatch_stale_pending_exports",
        "retention.run_account_erasure",
        "app.tasks.tenant_tasks.cleanup_expired_invitations",
        "app.tasks.tenant_tasks.resume_tenant_erasures",
        "app.tasks.tenant_tasks.run_tenant_erasure",
        "app.tasks.auth_tasks.anonymize_old_ips",
        "app.tasks.auth_tasks.cleanup_expired_tokens",
        "app.tasks.auth_tasks.cleanup_unverified_accounts",
        "security_audit.purge_expired",
        "ai.cleanup_expired_audit_log",
        "ai.cleanup_expired_conversations",
        "mcp.cleanup_expired_audit_log",
        "mcp.cleanup_expired_idempotency",
        "glossary.cleanup_expired_cache",
        "pest_image.sweep_orphaned_prototypes",
        "app.tasks.pest_image_tasks.erase_pest_prototype_task",
        # people waiting on a clock
        "notifications.dispatch_due_care",
        "notifications.escalate_overdue",
        "notifications.send_daily_summary",
        "notifications.send_email_digests",
        "app.tasks.frost_forecast_tasks.evaluate_forecast_frost_warnings",
        # REQ-018 control loop (30 s cadence)
        "app.tasks.actuator_tasks.evaluate_control_rules",
        "app.tasks.actuator_tasks.expire_manual_overrides",
        "app.tasks.actuator_tasks.sync_actuator_states",
    }
)

BULK_TASKS: Final = frozenset(
    {
        "app.tasks.pest_dataset_tasks.acquire_pest_dataset_task",
        "app.tasks.reference_image_tasks.acquire_all_reference_images_task",
        "app.tasks.reference_image_tasks.acquire_reference_images_task",
        "app.tasks.reference_contribution_tasks.feed_user_reference",
        "app.tasks.pest_image_tasks.index_promoted_pest_image_task",
        "app.tasks.pest_image_tasks.retract_promoted_pest_image_task",
        "app.tasks.enrichment_tasks.sync_all_sources_task",
        "app.tasks.enrichment_tasks.sync_source_task",
        "glossary.warm_cache",
        "ai.knowledge_service_ingest",
        "app.tasks.storage_tasks.migrate_storage",
        "app.tasks.storage_tasks.migrate_photo_refs",
    }
)

#: Routed to ``celery`` — listed rather than implied, so a new task needs a decision.
DEFAULT_TASKS: Final = frozenset(
    {
        "app.tasks.auth_tasks.rotate_oidc_discovery",
        "app.tasks.auth_tasks.send_duplicate_registration_notice",
        "app.tasks.care_tasks.generate_due_care_reminders",
        "app.tasks.climate_tasks.fetch_climate_normals",
        "app.tasks.hardiness_tasks.refresh_site_hardiness_zones",
        "app.tasks.irrigation_tasks.compute_irrigation_demand",
        "app.tasks.season_tasks.evaluate_quarter_climate",
        "app.tasks.season_tasks.evaluate_season_states",
        "app.tasks.sensor_ingestion_tasks.ingest_ha_readings",
        "app.tasks.storage_tasks.cleanup_orphaned_task_photos",
        "app.tasks.storage_tasks.generate_thumbnails",
        "app.tasks.storage_tasks.reconcile_orphaned_storage_objects",
        "app.tasks.tank_maintenance_tasks.check_runoff_trends",
        "app.tasks.tank_maintenance_tasks.check_tank_alerts",
        "app.tasks.tank_maintenance_tasks.generate_tank_maintenance_tasks",
        "app.tasks.tank_maintenance_tasks.sync_tank_states_from_ha",
        "app.tasks.watering_tasks.generate_watering_tasks",
        "app.tasks.weather_tasks.fetch_weather_forecasts",
        "check_auto_transitions",
        "check_dormancy_triggers",
        "update_vernalization_progress",
        "glossary.invalidate_after_reingest",
        "inventree.push_pending_transactions",
        "inventree.sync_stock_levels",
        "retention.process_data_export",
    }
)

#: Default backstop for every task without a limit of its own.
SOFT_TIME_LIMIT_SECONDS: Final = 30 * 60
TIME_LIMIT_SECONDS: Final = SOFT_TIME_LIMIT_SECONDS + 5 * 60

#: Resumable or operator-started work that may legitimately run for hours.
LONG_SOFT_TIME_LIMIT_SECONDS: Final = 3 * 60 * 60
LONG_TIME_LIMIT_SECONDS: Final = LONG_SOFT_TIME_LIMIT_SECONDS + 5 * 60
LONG_RUNNING_TASKS: Final = frozenset(
    {
        "app.tasks.pest_dataset_tasks.acquire_pest_dataset_task",
        "app.tasks.enrichment_tasks.sync_source_task",
        "app.tasks.storage_tasks.migrate_storage",
        "app.tasks.storage_tasks.migrate_photo_refs",
        "retention.process_data_export",
        "retention.execute_scheduled_erasures",
        "retention.run_account_erasure",
        "app.tasks.tenant_tasks.run_tenant_erasure",
        "app.tasks.tenant_tasks.resume_tenant_erasures",
    }
)

#: Above the longest hard limit, so a message reserved behind a running task is not redelivered.
VISIBILITY_TIMEOUT_SECONDS: Final = LONG_TIME_LIMIT_SECONDS + 55 * 60


def _queue_of(name: str) -> str:
    if name in CRITICAL_TASKS:
        return QUEUE_CRITICAL
    if name in BULK_TASKS:
        return QUEUE_BULK
    return QUEUE_DEFAULT


def task_routes() -> dict[str, dict[str, str]]:
    """``task_routes`` for every listed task (the default queue explicitly, too)."""
    names = CRITICAL_TASKS | BULK_TASKS | DEFAULT_TASKS
    return {name: {"queue": _queue_of(name)} for name in sorted(names)}


def task_annotations() -> dict[str, dict[str, int]]:
    """Per-task limits for :data:`LONG_RUNNING_TASKS`; every other task takes the global default."""
    return {
        name: {"soft_time_limit": LONG_SOFT_TIME_LIMIT_SECONDS, "time_limit": LONG_TIME_LIMIT_SECONDS}
        for name in sorted(LONG_RUNNING_TASKS)
    }


def celery_queue_config() -> dict[str, object]:
    """The Celery settings this module owns, for ``celery_app.conf.update``."""
    return {
        "task_default_queue": QUEUE_DEFAULT,
        # Exchange and routing key named after the queue: for ``celery`` that is
        # exactly Celery's own default declaration, so messages an older image
        # publishes still reach it.
        "task_queues": tuple(Queue(name, Exchange(name, type="direct"), routing_key=name) for name in QUEUES),
        "task_routes": task_routes(),
        "task_annotations": task_annotations(),
        "task_soft_time_limit": SOFT_TIME_LIMIT_SECONDS,
        "task_time_limit": TIME_LIMIT_SECONDS,
        # One reserved message per process: a long task no longer holds four
        # messages of other tasks hostage behind it.
        "worker_prefetch_multiplier": 1,
        "broker_transport_options": {"visibility_timeout": VISIBILITY_TIMEOUT_SECONDS},
    }
