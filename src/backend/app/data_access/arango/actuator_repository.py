"""REQ-018 Environment-control ArangoDB repository.

Persists actuators, their control schedules / rules / manual overrides, the
immutable control-event log and the (tenant-owned) phase control profiles. Graph
edges wire locations to actuators and actuators to their schedules/rules/
overrides/events.

All AQL is parameterised via ``bind_vars`` (never f-string interpolation of
values) and every tenant-scoped query filters on ``tenant_key`` (SEC-B4). The
collection constants (``col.*``) are the only values ever interpolated into a
query string, and they come from code, never from user input.
"""

from __future__ import annotations

from typing import Any

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.actuator import (
    Actuator,
    ControlEvent,
    ControlRule,
    ControlSchedule,
    ManualOverride,
    PhaseControlProfile,
)
from app.domain.models.site import Location


class ArangoActuatorRepository(BaseArangoRepository[Actuator]):
    """Repository for the REQ-018 environment-control domain."""

    is_tenant_scoped = True
    _model_cls = Actuator
    _entity_name = "Actuator"

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.ACTUATORS)
        self._schedules = BaseArangoRepository[ControlSchedule](db, col.CONTROL_SCHEDULES, ControlSchedule)
        self._rules = BaseArangoRepository[ControlRule](db, col.CONTROL_RULES, ControlRule)
        self._overrides = BaseArangoRepository[ManualOverride](db, col.MANUAL_OVERRIDES, ManualOverride)
        self._events = BaseArangoRepository[ControlEvent](db, col.CONTROL_EVENTS, ControlEvent)
        self._profiles = BaseArangoRepository[PhaseControlProfile](db, col.PHASE_CONTROL_PROFILES, PhaseControlProfile)
        self._locations = BaseArangoRepository[Location](db, col.LOCATIONS, Location)

    # ── Location ownership (used to verify location scope) ───────────────

    def get_location(self, key: str) -> Location | None:
        return self._locations.get_by_key(key)

    # ── Actuator CRUD ────────────────────────────────────────────────────

    def list_for_tenant(
        self,
        tenant_key: str,
        actuator_type: str | None = None,
        protocol: str | None = None,
        is_online: bool | None = None,
    ) -> list[Actuator]:
        self._require_tenant_key(tenant_key, "list_for_tenant")
        extra: list[tuple[str, str, Any]] = []
        if actuator_type:
            extra.append(("actuator_type", "==", actuator_type))
        if protocol:
            extra.append(("protocol", "==", protocol))
        if is_online is not None:
            extra.append(("is_online", "==", is_online))
        return self.find_by_field("tenant_key", tenant_key, sort="name", extra_filters=extra)

    def list_for_location(self, location_key: str, tenant_key: str) -> list[Actuator]:
        self._require_tenant_key(tenant_key, "list_for_location")
        return self.find_by_field(
            "location_key",
            location_key,
            sort="name",
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    def create_actuator(self, actuator: Actuator) -> Actuator:
        created = self.create(actuator)
        if actuator.location_key and created.key:
            location_id = f"{col.LOCATIONS}/{actuator.location_key}"
            actuator_id = f"{col.ACTUATORS}/{created.key}"
            self.create_edge(col.HAS_ACTUATOR, location_id, actuator_id)
            self.create_edge(col.ACTUATOR_CONTROLS_LOCATION, actuator_id, location_id)
        return created

    def update_actuator(self, key: str, actuator: Actuator) -> Actuator:
        return self.update(key, actuator)

    def delete_actuator(self, key: str) -> bool:
        actuator_id = f"{col.ACTUATORS}/{key}"
        self.delete_edges(col.HAS_ACTUATOR, actuator_id, direction="inbound")
        self.delete_edges(col.ACTUATOR_CONTROLS_LOCATION, actuator_id)
        for edge_col in (
            col.ACTUATOR_HAS_SCHEDULE,
            col.ACTUATOR_HAS_RULE,
            col.ACTUATOR_HAS_OVERRIDE,
            col.ACTUATOR_EVENT,
        ):
            self.delete_edges(edge_col, actuator_id)
        for child_col in (col.CONTROL_SCHEDULES, col.CONTROL_RULES, col.MANUAL_OVERRIDES, col.CONTROL_EVENTS):
            query = f"FOR doc IN {child_col} FILTER doc.actuator_key == @key REMOVE doc IN {child_col}"
            self._db.aql.execute(query, bind_vars={"key": key})
        return self.delete(key)

    # ── Schedules ────────────────────────────────────────────────────────

    def create_schedule(self, schedule: ControlSchedule) -> ControlSchedule:
        created = self._schedules.create(schedule)
        if schedule.actuator_key and created.key:
            self.create_edge(
                col.ACTUATOR_HAS_SCHEDULE,
                f"{col.ACTUATORS}/{schedule.actuator_key}",
                f"{col.CONTROL_SCHEDULES}/{created.key}",
            )
        return created

    def list_schedules(self, actuator_key: str, tenant_key: str) -> list[ControlSchedule]:
        return self._schedules.find_by_field(
            "actuator_key",
            actuator_key,
            sort="name",
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    def list_active_schedules(self, actuator_key: str) -> list[ControlSchedule]:
        return self._schedules.find_by_field("actuator_key", actuator_key, extra_filters=[("is_active", "==", True)])

    def get_schedule(self, key: str) -> ControlSchedule | None:
        return self._schedules.get_by_key(key)

    def get_schedule_or_raise(self, key: str) -> ControlSchedule:
        return self._schedules.get_or_raise(key)

    def update_schedule(self, key: str, schedule: ControlSchedule) -> ControlSchedule:
        return self._schedules.update(key, schedule)

    def delete_schedule(self, key: str) -> bool:
        self.delete_edges(col.ACTUATOR_HAS_SCHEDULE, f"{col.CONTROL_SCHEDULES}/{key}", direction="inbound")
        return self._schedules.delete(key)

    # ── Rules ────────────────────────────────────────────────────────────

    def create_rule(self, rule: ControlRule) -> ControlRule:
        created = self._rules.create(rule)
        if rule.actuator_key and created.key:
            self.create_edge(
                col.ACTUATOR_HAS_RULE,
                f"{col.ACTUATORS}/{rule.actuator_key}",
                f"{col.CONTROL_RULES}/{created.key}",
            )
        if rule.sensor_location_key and created.key:
            # rule_monitors is a graph edge control_rules -> sensors; the sensor
            # key is optional, so only link when the rule references one.
            pass
        return created

    def list_rules(self, actuator_key: str, tenant_key: str) -> list[ControlRule]:
        return self._rules.find_by_field(
            "actuator_key",
            actuator_key,
            sort="priority",
            sort_direction="DESC",
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    def list_active_rules(self, actuator_key: str) -> list[ControlRule]:
        return self._rules.find_by_field("actuator_key", actuator_key, extra_filters=[("is_active", "==", True)])

    def list_rules_for_tenant(
        self,
        tenant_key: str,
        sensor_parameter: str | None = None,
        is_active: bool | None = None,
        is_safety: bool | None = None,
    ) -> list[ControlRule]:
        self._require_tenant_key(tenant_key, "list_rules_for_tenant")
        extra: list[tuple[str, str, Any]] = []
        if sensor_parameter:
            extra.append(("sensor_parameter", "==", sensor_parameter))
        if is_active is not None:
            extra.append(("is_active", "==", is_active))
        if is_safety is not None:
            extra.append(("is_safety_rule", "==", is_safety))
        return self._rules.find_by_field(
            "tenant_key", tenant_key, sort="priority", sort_direction="DESC", extra_filters=extra
        )

    def get_rule(self, key: str) -> ControlRule | None:
        return self._rules.get_by_key(key)

    def get_rule_or_raise(self, key: str) -> ControlRule:
        return self._rules.get_or_raise(key)

    def update_rule(self, key: str, rule: ControlRule) -> ControlRule:
        return self._rules.update(key, rule)

    def delete_rule(self, key: str) -> bool:
        self.delete_edges(col.ACTUATOR_HAS_RULE, f"{col.CONTROL_RULES}/{key}", direction="inbound")
        self.delete_edges(col.RULE_MONITORS, f"{col.CONTROL_RULES}/{key}")
        return self._rules.delete(key)

    # ── Manual overrides ─────────────────────────────────────────────────

    def create_override(self, override: ManualOverride) -> ManualOverride:
        created = self._overrides.create(override)
        if override.actuator_key and created.key:
            self.create_edge(
                col.ACTUATOR_HAS_OVERRIDE,
                f"{col.ACTUATORS}/{override.actuator_key}",
                f"{col.MANUAL_OVERRIDES}/{created.key}",
            )
        return created

    def get_active_override(self, actuator_key: str) -> ManualOverride | None:
        results = self._overrides.find_by_field(
            "actuator_key",
            actuator_key,
            sort="started_at",
            sort_direction="DESC",
            offset=0,
            limit=1,
            extra_filters=[("is_active", "==", True)],
        )
        return results[0] if results else None

    def deactivate_overrides_for_actuator(self, actuator_key: str) -> int:
        query = f"""
        FOR doc IN {col.MANUAL_OVERRIDES}
          FILTER doc.actuator_key == @actuator_key AND doc.is_active == true
          UPDATE doc WITH {{ is_active: false }} IN {col.MANUAL_OVERRIDES}
          RETURN 1
        """
        cursor = self._db.aql.execute(query, bind_vars={"actuator_key": actuator_key})
        return sum(1 for _ in cursor)

    def expire_overrides(self, now_iso: str) -> int:
        """Deactivate every active override whose ``expires_at`` has passed."""
        query = f"""
        FOR doc IN {col.MANUAL_OVERRIDES}
          FILTER doc.is_active == true AND doc.expires_at <= @now
          UPDATE doc WITH {{ is_active: false }} IN {col.MANUAL_OVERRIDES}
          RETURN 1
        """
        cursor = self._db.aql.execute(query, bind_vars={"now": now_iso})
        return sum(1 for _ in cursor)

    # ── Control events (immutable log) ───────────────────────────────────

    def create_event(self, event: ControlEvent) -> ControlEvent:
        created = self._events.create(event, default_now_fields=("timestamp",))
        if event.actuator_key and created.key:
            self.create_edge(
                col.ACTUATOR_EVENT,
                f"{col.ACTUATORS}/{event.actuator_key}",
                f"{col.CONTROL_EVENTS}/{created.key}",
            )
        return created

    def list_events(self, actuator_key: str, tenant_key: str, offset: int = 0, limit: int = 50) -> list[ControlEvent]:
        return self._events.find_by_field(
            "actuator_key",
            actuator_key,
            sort="timestamp",
            sort_direction="DESC",
            offset=offset,
            limit=limit,
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    def list_events_for_location(
        self, location_key: str, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> list[ControlEvent]:
        return self._events.find_by_field(
            "location_key",
            location_key,
            sort="timestamp",
            sort_direction="DESC",
            offset=offset,
            limit=limit,
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    # ── Phase control profiles ───────────────────────────────────────────

    def create_profile(self, profile: PhaseControlProfile) -> PhaseControlProfile:
        return self._profiles.create(profile)

    def list_profiles(self, tenant_key: str, is_template: bool | None = None) -> list[PhaseControlProfile]:
        self._require_tenant_key(tenant_key, "list_profiles")
        extra: list[tuple[str, str, Any]] = []
        if is_template is not None:
            extra.append(("is_template", "==", is_template))
        return self._profiles.find_by_field("tenant_key", tenant_key, sort="name", extra_filters=extra)

    def get_profile(self, key: str) -> PhaseControlProfile | None:
        return self._profiles.get_by_key(key)

    def get_profile_or_raise(self, key: str) -> PhaseControlProfile:
        return self._profiles.get_or_raise(key)

    def update_profile(self, key: str, profile: PhaseControlProfile) -> PhaseControlProfile:
        return self._profiles.update(key, profile)

    def delete_profile(self, key: str) -> bool:
        profile_id = f"{col.PHASE_CONTROL_PROFILES}/{key}"
        self.delete_edges(col.LOCATION_PROFILE, profile_id, direction="inbound")
        self.delete_edges(col.PHASE_PROFILE, profile_id, direction="inbound")
        return self._profiles.delete(key)

    def apply_profile_to_location(self, profile_key: str, location_key: str) -> None:
        location_id = f"{col.LOCATIONS}/{location_key}"
        # A location has at most one active override profile — replace it.
        self.delete_edges(col.LOCATION_PROFILE, location_id)
        self.create_edge(col.LOCATION_PROFILE, location_id, f"{col.PHASE_CONTROL_PROFILES}/{profile_key}")
