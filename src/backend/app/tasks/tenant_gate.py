"""Whether a beat may still write into or notify about a tenant (#2166, REQ-056 §5.2).

A tenant that is ``suspended``, ``pending_deletion``, ``orphaned`` or ``deleted``
resolves for nobody (#2105), while its memberships stay active on purpose — a
cancelled deletion restores them unchanged (#2123). A beat that asks only for the
membership therefore went on writing care tasks into such a tenant and notifying its
members of plants and due dates they cannot open. The stored tenant decides.
"""

from __future__ import annotations

from app.common.enums import TenantStatus
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.models.tenant import Tenant


class ActiveTenants:
    """``Tenant.is_active`` of each tenant, read once per beat run.

    ``is_active`` is ``status == active`` and nothing else. A tenant that cannot be
    found (its erasure already removed the document) is not active either.
    """

    def __init__(self, tenant_repo: ITenantRepository) -> None:
        self._repo = tenant_repo
        self._tenants: dict[str, Tenant | None] = {}

    def _tenant(self, tenant_key: str) -> Tenant | None:
        if tenant_key not in self._tenants:
            self._tenants[tenant_key] = self._repo.get_by_key(tenant_key)
        return self._tenants[tenant_key]

    def __call__(self, tenant_key: str) -> bool:
        if not tenant_key:
            return False
        tenant = self._tenant(tenant_key)
        return tenant is not None and bool(tenant.is_active)

    def status(self, tenant_key: str) -> TenantStatus | None:
        """The stored state of *tenant_key* (``None``: no key, or no such tenant), from the same one lookup."""
        if not tenant_key:
            return None
        tenant = self._tenant(tenant_key)
        return tenant.status if tenant is not None else None


#: The states in which a tenant's hardware is driven to a safe state instead of being left as it was
#: (REQ-056 §5.2, SEC-003): closed, but its devices still exist. ``deleted`` is excluded — the erasure
#: removes the actuators.
CLOSED_WITH_HARDWARE = frozenset({TenantStatus.SUSPENDED, TenantStatus.PENDING_DELETION, TenantStatus.ORPHANED})


#: Every periodic task that writes **into** a tenant (tasks, readings, weather, stock,
#: actuator events, site attributes) or notifies **about** one (REQ-056 §5.2). Each asks
#: :class:`ActiveTenants` — or, for ``notifications.escalate_overdue``, which walks the
#: tenants themselves, compares their ``status`` with ``active``; the actuator, tank and
#: quarter-climate beats walk only the tenants ``ITenantRepository.keys_in_status`` names
#: (MT-032, #2128) — and leaves every tenant
#: that is not ``active`` alone — except that ``evaluate_control_rules`` drives the devices of a
#: suspended, pending-deletion or orphaned tenant to a safe state (SEC-003, ``ActuatorService.
#: drive_to_safe_state``) instead of leaving the last command latched.
#: ``tests/unit/guards/test_beats_skip_inactive_tenants.py``
#: holds every ``beat_schedule`` entry to exactly one of the two classifications.
TENANT_WRITING_BEATS: frozenset[str] = frozenset(
    {
        "app.tasks.actuator_tasks.evaluate_control_rules",
        "app.tasks.actuator_tasks.sync_actuator_states",
        "app.tasks.care_tasks.generate_due_care_reminders",
        "app.tasks.climate_tasks.fetch_climate_normals",
        "app.tasks.frost_forecast_tasks.evaluate_forecast_frost_warnings",
        "app.tasks.hardiness_tasks.refresh_site_hardiness_zones",
        "app.tasks.irrigation_tasks.compute_irrigation_demand",
        "app.tasks.season_tasks.evaluate_quarter_climate",
        "app.tasks.season_tasks.evaluate_season_states",
        "app.tasks.sensor_ingestion_tasks.ingest_ha_readings",
        "app.tasks.tank_maintenance_tasks.check_runoff_trends",
        "app.tasks.tank_maintenance_tasks.check_tank_alerts",
        "app.tasks.tank_maintenance_tasks.generate_tank_maintenance_tasks",
        "app.tasks.tank_maintenance_tasks.sync_tank_states_from_ha",
        "app.tasks.watering_tasks.generate_watering_tasks",
        "app.tasks.weather_tasks.fetch_weather_forecasts",
        "inventree.push_pending_transactions",
        "inventree.sync_stock_levels",
        "notifications.dispatch_due_care",
        "notifications.escalate_overdue",
        "notifications.send_daily_summary",
        "notifications.send_email_digests",
    }
)

_RETENTION = "retention or erasure: NFR-011 periods run out during a suspension as well (REQ-056 §5.2)"
_GLOBAL = "global, no tenant data: runs regardless of any tenant's state"
_STORAGE = "storage reconciliation: collects what nothing references, whatever the owner's state"

#: Every periodic task that runs regardless of a tenant's state, with the reason (REQ-056 §5.2).
TENANT_AGNOSTIC_BEATS: dict[str, str] = {
    "ai.cleanup_expired_audit_log": _RETENTION,
    "ai.cleanup_expired_conversations": _RETENTION,
    "ai.knowledge_service_ingest": _GLOBAL + " (the shared knowledge base)",
    "app.tasks.actuator_tasks.expire_manual_overrides": (
        "a deadline, not processing: an override past its expiry is over in every state, so a "
        "reactivated tenant does not get back an override its user set to end"
    ),
    "app.tasks.auth_tasks.anonymize_old_ips": _RETENTION + " (R-03)",
    "app.tasks.auth_tasks.cleanup_expired_tokens": _RETENTION + " (R-11)",
    "app.tasks.auth_tasks.cleanup_unverified_accounts": _RETENTION + " (R-02, accounts, not tenants)",
    "app.tasks.auth_tasks.rotate_oidc_discovery": _GLOBAL + " (OIDC provider metadata)",
    "app.tasks.enrichment_tasks.sync_all_sources_task": _GLOBAL + " (species catalogue enrichment)",
    "app.tasks.storage_tasks.cleanup_orphaned_task_photos": _STORAGE,
    "app.tasks.storage_tasks.reconcile_orphaned_storage_objects": _STORAGE,
    "app.tasks.tenant_tasks.cleanup_expired_invitations": _RETENTION + " (R-12, invitation expiry)",
    "app.tasks.tenant_tasks.resume_tenant_erasures": _RETENTION + " (it is what erases a pending tenant)",
    "glossary.cleanup_expired_cache": _GLOBAL + " (glossary cache)",
    "mcp.cleanup_expired_audit_log": _RETENTION,
    "mcp.cleanup_expired_idempotency": _RETENTION,
    "pest_image.sweep_orphaned_prototypes": _STORAGE + " (contributed pest prototypes)",
    "retention.anonymize_consent_ips": _RETENTION + " (R-04a)",
    "retention.execute_scheduled_erasures": _RETENTION,
    "retention.expire_data_exports": _RETENTION + " (export expiry)",
    "retention.expire_email_change_requests": _RETENTION,
    "retention.purge_expired_consent_records": _RETENTION + " (R-04)",
    "retention.purge_expired_erasure_records": _RETENTION + " (R-06)",
    "retention.purge_expired_legal_retention_rows": _RETENTION + " (R-16/R-17/R-18)",
    "retention.purge_expired_tenant_erasure_records": _RETENTION + " (R-06a)",
    "retention.redispatch_stale_pending_exports": (
        "finishes an account's own Art. 15/20 export, which REQ-056 §5.5 keeps possible in a suspension"
    ),
    "security_audit.purge_expired": _RETENTION + " (R-38)",
}
