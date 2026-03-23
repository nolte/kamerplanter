from datetime import UTC, datetime, time, timedelta

from arango.database import StandardDatabase

from app.common.enums import (
    CATEGORY_COLORS,
    CalendarEventCategory,
    CalendarEventSource,
)
from app.data_access.arango import collections as col
from app.domain.engines.watering_volume_engine import SUBSTRATE_WATERING_RATIO as _SUBSTRATE_WATERING_RATIO
from app.domain.models.calendar import CalendarEvent, CalendarEventsQuery


class CalendarAggregationEngine:
    """Aggregate calendar events from multiple sources (tasks, phase transitions, maintenance, watering)."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def get_events(self, query: CalendarEventsQuery) -> list[CalendarEvent]:
        start_dt = datetime.combine(query.start_date, time.min, tzinfo=UTC)
        end_dt = datetime.combine(query.end_date, time(23, 59, 59), tzinfo=UTC)

        events: list[CalendarEvent] = []
        events.extend(self._task_events(start_dt, end_dt, query))
        events.extend(self._phase_transition_events(start_dt, end_dt, query))
        events.extend(self._maintenance_events(start_dt, end_dt, query))
        events.extend(self._watering_events(start_dt, end_dt, query))
        events.extend(self._watering_forecast_events(query))

        if query.categories:
            events = [e for e in events if e.category in query.categories]

        events.sort(key=lambda e: e.start or datetime.min.replace(tzinfo=UTC))
        return events

    def _task_events(
        self,
        start: datetime,
        end: datetime,
        query: CalendarEventsQuery,
    ) -> list[CalendarEvent]:
        aql = f"""
        FOR t IN {col.TASKS}
          FILTER t.due_date != null
          FILTER t.due_date >= @start AND t.due_date <= @end
          FILTER t.tenant_key == @tenant_key
          RETURN t
        """
        bind = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "tenant_key": query.tenant_key,
        }
        cursor = self._db.aql.execute(aql, bind_vars=bind)
        events = []
        for doc in cursor:
            category = self._task_category_map(doc.get("category", ""))
            events.append(
                CalendarEvent(
                    id=f"task:{doc['_key']}",
                    title=doc.get("name", ""),
                    description=doc.get("instruction", ""),
                    category=category,
                    source=CalendarEventSource.TASK,
                    color=CATEGORY_COLORS.get(category, "#607D8B"),
                    start=self._parse_dt(doc.get("due_date")),
                    all_day=True,
                    plant_key=doc.get("plant_key"),
                    task_key=doc.get("_key"),
                )
            )
        return events

    def _phase_transition_events(
        self,
        start: datetime,
        end: datetime,
        query: CalendarEventsQuery,
    ) -> list[CalendarEvent]:
        """Return phase spans (actual + projected) that overlap the requested date range.

        For each active plant:
        1. Load its lifecycle growth phases (sorted by sequence_order)
        2. Load its phase history (actual transitions)
        3. Build a full timeline: completed → current → projected
        4. Emit CalendarEvents for phases overlapping [start, end]
        """
        # Single AQL: fetch active plants with phase histories, species, run, lifecycle
        aql = f"""
        FOR pi IN {col.PLANT_INSTANCES}
          FILTER pi.removed_on == null
          LET run_edge = FIRST(
            FOR e IN {col.RUN_CONTAINS}
              FILTER e._to == pi._id
              RETURN e
          )
          LET run = run_edge != null ? DOCUMENT(run_edge._from) : null
          FILTER run == null OR run.status IN ["active", "harvesting"]
          LET lc_edge = FIRST(
            FOR e IN {col.HAS_LIFECYCLE}
              FILTER e._from == CONCAT("{col.SPECIES}/", pi.species_key)
              RETURN e
          )
          LET lc = lc_edge != null ? DOCUMENT(lc_edge._to) : null
          FILTER lc != null
          LET gps = (
            FOR e IN {col.CONSISTS_OF}
              FILTER e._from == lc._id
              LET gp = DOCUMENT(e._to)
              FILTER gp != null
              SORT gp.sequence_order ASC
              RETURN gp
          )
          FILTER LENGTH(gps) > 0
          LET histories = (
            FOR ph IN {col.PHASE_HISTORIES}
              FILTER ph.plant_instance_key == pi._key
              RETURN ph
          )
          LET current_gp = DOCUMENT(CONCAT("{col.GROWTH_PHASES}/", pi.current_phase_key))
          RETURN {{
            plant_key: pi._key,
            instance_id: pi.instance_id,
            plant_name: pi.plant_name,
            species_key: pi.species_key,
            current_phase: current_gp != null ? current_gp.name : '',
            run_key: run._key,
            run_name: run.name,
            growth_phases: gps,
            phase_histories: histories
          }}
        """
        cursor = self._db.aql.execute(aql)
        now = datetime.now(UTC)
        cat = CalendarEventCategory.PHASE_TRANSITION
        color = CATEGORY_COLORS.get(cat, "#9C27B0")
        events: list[CalendarEvent] = []

        for doc in cursor:
            plant_key = doc.get("plant_key", "")
            plant_label = doc.get("plant_name") or doc.get("instance_id") or ""
            run_key = doc.get("run_key")
            run_name = doc.get("run_name", "")

            base_meta: dict = {
                "plant_instance_key": plant_key,
                "instance_id": doc.get("instance_id", ""),
                "plant_name": plant_label,
            }
            if run_key:
                base_meta["run_key"] = run_key
                base_meta["run_name"] = run_name

            # Build history lookup by phase_name
            history_by_name: dict[str, dict] = {}
            for h in doc.get("phase_histories", []):
                history_by_name[h.get("phase_name", "")] = h

            current_phase = doc.get("current_phase", "")
            growth_phases = doc.get("growth_phases", [])
            last_end: datetime | None = None

            for gp in growth_phases:
                gp_name = gp.get("name", "")
                gp_key = gp.get("_key", "")
                typical_days = gp.get("typical_duration_days", 14)
                h = history_by_name.get(gp_name)

                entered = self._parse_dt(h.get("entered_at")) if h else None
                exited = self._parse_dt(h.get("exited_at")) if h else None
                exited_in_past = exited is not None and exited <= now

                if h and entered and exited_in_past:
                    # Completed phase
                    phase_start = entered
                    phase_end = exited
                    status = "completed"
                    last_end = exited
                elif gp_name == current_phase or (h and entered and not exited_in_past):
                    # Current phase
                    phase_start = entered or last_end
                    if exited and not exited_in_past:
                        phase_end = exited
                    elif phase_start:
                        phase_end = phase_start + timedelta(days=typical_days)
                    else:
                        continue
                    status = "current"
                    last_end = phase_end
                else:
                    # Projected phase
                    if last_end is None:
                        continue
                    phase_start = last_end
                    phase_end = phase_start + timedelta(days=typical_days)
                    status = "projected"
                    last_end = phase_end

                # Check overlap with requested range
                if phase_start > end or phase_end < start:
                    continue

                title = f"{plant_label}: {gp_name}" if plant_label else f"Phase: {gp_name}"
                meta = {**base_meta, "phase_name": gp_name, "status": status}

                ev_id = f"phase:{plant_key}:{gp_key}" if status != "completed" else f"phase:{h['_key']}"
                events.append(
                    CalendarEvent(
                        id=ev_id,
                        title=title,
                        description="",
                        category=cat,
                        source=CalendarEventSource.PHASE_TRANSITION,
                        color=color,
                        start=phase_start,
                        end=phase_end,
                        all_day=True,
                        plant_key=plant_key,
                        metadata=meta,
                    )
                )

        return events

    def _maintenance_events(
        self,
        start: datetime,
        end: datetime,
        query: CalendarEventsQuery,
    ) -> list[CalendarEvent]:
        aql = f"""
        FOR m IN {col.MAINTENANCE_LOGS}
          FILTER m.performed_at != null
          FILTER m.performed_at >= @start AND m.performed_at <= @end
          RETURN m
        """
        bind = {"start": start.isoformat(), "end": end.isoformat()}
        cursor = self._db.aql.execute(aql, bind_vars=bind)
        events = []
        for doc in cursor:
            cat = CalendarEventCategory.TANK_MAINTENANCE
            events.append(
                CalendarEvent(
                    id=f"maint:{doc['_key']}",
                    title=doc.get("action", "Maintenance"),
                    description=doc.get("notes", ""),
                    category=cat,
                    source=CalendarEventSource.MAINTENANCE_LOG,
                    color=CATEGORY_COLORS.get(cat, "#00BCD4"),
                    start=self._parse_dt(doc.get("performed_at")),
                    all_day=False,
                )
            )
        return events

    def _watering_events(
        self,
        start: datetime,
        end: datetime,
        query: CalendarEventsQuery,
    ) -> list[CalendarEvent]:
        aql = f"""
        FOR w IN {col.WATERING_LOGS}
          FILTER w.logged_at != null
          FILTER w.logged_at >= @start AND w.logged_at <= @end
          LET plant_names = (
            FOR pk IN (w.plant_keys || [])
              LET pi = DOCUMENT(CONCAT("{col.PLANT_INSTANCES}/", pk))
              FILTER pi != null
              RETURN pi.plant_name || pi.instance_id || pk
          )
          RETURN MERGE(w, {{ resolved_plant_names: plant_names }})
        """
        bind = {"start": start.isoformat(), "end": end.isoformat()}
        cursor = self._db.aql.execute(aql, bind_vars=bind)
        events = []
        for doc in cursor:
            cat = CalendarEventCategory.FEEDING
            plant_names = doc.get("resolved_plant_names", [])
            plant_label = ", ".join(plant_names) if plant_names else ""
            has_ferts = len(doc.get("fertilizers_used", [])) > 0
            action = "Feeding" if has_ferts else "Watering"
            title = f"{plant_label}: {action}" if plant_label else action
            plant_keys = doc.get("plant_keys", [])
            events.append(
                CalendarEvent(
                    id=f"water:{doc['_key']}",
                    title=title,
                    description=doc.get("notes", ""),
                    category=cat,
                    source=CalendarEventSource.WATERING,
                    color=CATEGORY_COLORS.get(cat, "#2196F3"),
                    start=self._parse_dt(doc.get("logged_at")),
                    all_day=False,
                    plant_key=plant_keys[0] if plant_keys else None,
                    metadata={
                        "volume_liters": doc.get("volume_liters"),
                        "application_method": doc.get("application_method"),
                        "plant_names": plant_names,
                    },
                )
            )
        return events

    def _watering_forecast_events(
        self,
        query: CalendarEventsQuery,
    ) -> list[CalendarEvent]:
        """Project future watering dates from CareProfiles of active plant instances.

        Phase-aware interval resolution:
          1. Cultivar.phase_watering_overrides[phase_name]  (user-maintained per cultivar)
          2. GrowthPhase.watering_interval_days              (species lifecycle default)
          3. CareProfile.watering_interval_days               (flat fallback)
        """
        from app.domain.engines.watering_forecast_engine import WateringForecastEngine
        from app.domain.models.care_reminder import CareProfile

        forecast_engine = WateringForecastEngine()

        # Query: active plants + care profile + last watering + lifecycle phases + cultivar overrides
        aql = f"""
        FOR pi IN {col.PLANT_INSTANCES}
          FILTER pi.removed_on == null
          FILTER pi.tenant_key == @tenant_key
          LET cp = FIRST(
            FOR c IN {col.CARE_PROFILES}
              FILTER c.plant_key == pi._key
              RETURN c
          )
          FILTER cp != null
          LET last_confirm = FIRST(
            FOR cc IN {col.CARE_CONFIRMATIONS}
              FILTER cc.plant_key == pi._key
              FILTER cc.reminder_type == "watering"
              FILTER cc.action == "confirmed"
              SORT cc.confirmed_at DESC
              LIMIT 1
              RETURN cc
          )
          LET lc_edge = FIRST(
            FOR e IN {col.HAS_LIFECYCLE}
              FILTER e._from == CONCAT("{col.SPECIES}/", pi.species_key)
              RETURN e
          )
          LET lc = lc_edge != null ? DOCUMENT(lc_edge._to) : null
          LET gps = lc != null ? (
            FOR e IN {col.CONSISTS_OF}
              FILTER e._from == lc._id
              LET gp = DOCUMENT(e._to)
              FILTER gp != null
              SORT gp.sequence_order ASC
              RETURN gp
          ) : []
          LET histories = (
            FOR ph IN {col.PHASE_HISTORIES}
              FILTER ph.plant_instance_key == pi._key
              RETURN ph
          )
          LET cultivar = pi.cultivar_key != null ? DOCUMENT(CONCAT("{col.CULTIVARS}/", pi.cultivar_key)) : null
          LET plan_edge = FIRST(
            FOR e IN {col.FOLLOWS_PLAN}
              FILTER e._from == pi._id
              RETURN e
          )
          LET plan = plan_edge != null ? DOCUMENT(plan_edge._to) : null
          LET plan_entries = plan != null ? (
            FOR pe IN {col.NUTRIENT_PLAN_PHASE_ENTRIES}
              FILTER pe.plan_key == plan._key
              SORT pe.sequence_order ASC
              RETURN pe
          ) : []
          LET current_gp2 = DOCUMENT(CONCAT("{col.GROWTH_PHASES}/", pi.current_phase_key))
          RETURN {{
            plant_key: pi._key,
            plant_name: pi.plant_name,
            instance_id: pi.instance_id,
            species_key: pi.species_key,
            current_phase: current_gp2 != null ? current_gp2.name : '',
            planted_on: pi.planted_on,
            container_volume_liters: pi.container_volume_liters,
            substrate_type_override: pi.substrate_type_override,
            care_profile: cp,
            last_watering: last_confirm.confirmed_at,
            growth_phases: gps,
            phase_histories: histories,
            cultivar_phase_overrides: cultivar.phase_watering_overrides,
            plan_name: plan.name,
            plan_cycle_restart: plan.cycle_restart_from_sequence,
            plan_entries: plan_entries
          }}
        """
        bind = {"tenant_key": query.tenant_key}
        try:
            cursor = self._db.aql.execute(aql, bind_vars=bind)
        except Exception:
            return []

        now = datetime.now(UTC)
        events: list[CalendarEvent] = []
        cat = CalendarEventCategory.WATERING_FORECAST
        color = CATEGORY_COLORS.get(cat, "#42A5F5")

        for doc in cursor:
            cp_data = doc.get("care_profile")
            if not cp_data:
                continue

            try:
                profile = CareProfile(**{k: v for k, v in cp_data.items() if not k.startswith("_") or k == "_key"})
            except Exception:
                continue

            # Determine last watering date
            last_raw = doc.get("last_watering")
            if last_raw:
                last_date = self._parse_dt(last_raw)
                base_date = last_date.date() if last_date else query.start_date
            else:
                base_date = query.start_date

            # Build phase intervals from lifecycle + cultivar overrides
            phase_intervals = self._build_phase_intervals(
                doc.get("growth_phases", []),
                doc.get("phase_histories", []),
                doc.get("current_phase", ""),
                doc.get("cultivar_phase_overrides"),
                now,
            )

            forecast_dates = forecast_engine.generate_forecast(
                profile=profile,
                last_watering_date=base_date,
                forecast_start=query.start_date,
                forecast_end=query.end_date,
                phase_intervals=phase_intervals or None,
            )

            plant_label = doc.get("plant_name") or doc.get("instance_id") or ""
            # Find the effective interval for metadata (current phase or fallback)
            current_interval = profile.watering_interval_days
            if phase_intervals:
                for pi in phase_intervals:
                    if pi.start_date <= now.date() <= pi.end_date:
                        current_interval = pi.interval_days
                        break

            # Resolve active nutrient plan phase entry for dosage hints
            dosage_meta = self._resolve_dosage_metadata(doc, now)

            for d in forecast_dates:
                events.append(
                    CalendarEvent(
                        id=f"wf:{doc['plant_key']}:{d.isoformat()}",
                        title=f"{plant_label}: Watering",
                        description="",
                        category=cat,
                        source=CalendarEventSource.WATERING_FORECAST,
                        color=color,
                        start=datetime.combine(d, time(9, 0), tzinfo=UTC),
                        all_day=True,
                        plant_key=doc.get("plant_key"),
                        metadata={
                            "plant_instance_key": doc.get("plant_key", ""),
                            "instance_id": doc.get("instance_id", ""),
                            "plant_name": plant_label,
                            "species_key": doc.get("species_key", ""),
                            "interval_days": current_interval,
                            **dosage_meta,
                        },
                    )
                )

        return events

    def _resolve_dosage_metadata(self, doc: dict, now: datetime) -> dict:
        """Extract dosage hints from the active nutrient plan phase entry."""
        entries = doc.get("plan_entries", [])
        if not entries:
            return {}

        current_phase = doc.get("current_phase", "")
        planted_on_raw = doc.get("planted_on")

        # Compute current week (same logic as frontend computeCurrentWeek)
        if planted_on_raw:
            try:
                if isinstance(planted_on_raw, str):
                    planted_date = datetime.fromisoformat(planted_on_raw).date()
                else:
                    planted_date = planted_on_raw
                diff_days = (now.date() - planted_date).days
                current_week = diff_days // 7 + 1 if diff_days >= 0 else None
            except (ValueError, TypeError):
                current_week = None
        else:
            current_week = None

        if current_week is None:
            return {}

        # Resolve matching entry (simplified resolve_effective_entry for raw dicts)
        sorted_entries = sorted(entries, key=lambda e: e.get("sequence_order", 0))
        active_entry = None

        # 1. Direct match: phase name + week range
        for e in sorted_entries:
            if e.get("phase_name") == current_phase and e.get("week_start", 0) <= current_week <= e.get("week_end", 0):
                active_entry = e
                break

        # 2. Fallback: week range only
        if not active_entry:
            for e in sorted_entries:
                if e.get("week_start", 0) <= current_week <= e.get("week_end", 0):
                    active_entry = e
                    break

        # 3. Cycle restart logic
        if not active_entry:
            cycle_restart = doc.get("plan_cycle_restart")
            if cycle_restart is not None:
                recurring = [e for e in sorted_entries if e.get("sequence_order", 0) >= cycle_restart]
                if recurring:
                    cycle_start = recurring[0].get("week_start", 0)
                    cycle_end = recurring[-1].get("week_end", 0)
                    cycle_len = cycle_end - cycle_start + 1
                    if cycle_len > 0 and current_week > cycle_end:
                        offset = (current_week - cycle_end - 1) % cycle_len
                        eff_week = cycle_start + offset
                        for e in recurring:
                            phase_match = e.get("phase_name") == current_phase
                            week_match = e.get("week_start", 0) <= eff_week <= e.get("week_end", 0)
                            if phase_match and week_match:
                                active_entry = e
                                break
                        if not active_entry:
                            for e in recurring:
                                if e.get("week_start", 0) <= eff_week <= e.get("week_end", 0):
                                    active_entry = e
                                    break

        if not active_entry:
            return {}

        # Extract EC, pH targets and fertilizer dosages from enabled delivery channels
        target_ec: float | None = None
        target_ph: float | None = None
        dosages: list[dict] = []

        for ch in active_entry.get("delivery_channels", []):
            if not ch.get("enabled", True):
                continue
            if target_ec is None and ch.get("target_ec_ms") is not None:
                target_ec = ch["target_ec_ms"]
            if target_ph is None and ch.get("target_ph") is not None:
                target_ph = ch["target_ph"]
            for d in ch.get("fertilizer_dosages", []):
                if not d.get("optional", False):
                    dosages.append(
                        {
                            "fertilizer_key": d.get("fertilizer_key", ""),
                            "ml_per_liter": d.get("ml_per_liter", 0),
                        }
                    )

        # Resolve fertilizer names
        if dosages:
            fert_keys = [d["fertilizer_key"] for d in dosages]
            fert_docs = {}
            try:
                for fk in fert_keys:
                    fdoc = self._db.collection(col.FERTILIZERS).get(fk)
                    if fdoc:
                        fert_docs[fk] = fdoc.get("product_name", fk)
            except Exception:
                pass
            for d in dosages:
                d["product_name"] = fert_docs.get(d["fertilizer_key"], d["fertilizer_key"])

        meta: dict = {
            "phase_name": active_entry.get("phase_name", ""),
            "plan_name": doc.get("plan_name", ""),
        }
        if target_ec is not None:
            meta["target_ec_ms"] = target_ec
        if target_ph is not None:
            meta["target_ph"] = target_ph
        if dosages:
            meta["dosages"] = dosages

        # Watering volume hint from container + substrate
        container_l = doc.get("container_volume_liters")
        substrate_type = doc.get("substrate_type_override")
        if container_l and container_l > 0:
            ratio = _SUBSTRATE_WATERING_RATIO.get(substrate_type or "", 0.15)
            meta["volume_liters"] = round(container_l * ratio, 1)

        return meta

    def _build_phase_intervals(
        self,
        growth_phases: list[dict],
        phase_histories: list[dict],
        current_phase: str,
        cultivar_overrides: dict[str, int] | None,
        now: datetime,
    ) -> list:
        """Build PhaseInterval list from lifecycle phases + cultivar overrides.

        Resolution: cultivar override > growth phase default.
        Only returns intervals for phases that have a watering_interval_days.
        """
        from app.domain.engines.watering_forecast_engine import PhaseInterval

        if not growth_phases:
            return []

        # History lookup by phase name
        history_by_name: dict[str, dict] = {}
        for h in phase_histories:
            history_by_name[h.get("phase_name", "")] = h

        cultivar_map = cultivar_overrides or {}
        intervals: list[PhaseInterval] = []
        last_end: datetime | None = None

        for gp in growth_phases:
            if gp is None:
                continue
            gp_name = gp.get("name", "")
            typical_days = gp.get("typical_duration_days", 14)
            h = history_by_name.get(gp_name)

            entered = self._parse_dt(h.get("entered_at")) if h else None
            exited = self._parse_dt(h.get("exited_at")) if h else None
            exited_in_past = exited is not None and exited <= now

            if h and entered and exited_in_past:
                phase_start = entered
                phase_end = exited
                last_end = exited
            elif gp_name == current_phase or (h and entered and not exited_in_past):
                phase_start = entered or last_end
                if exited and not exited_in_past:
                    phase_end = exited
                elif phase_start:
                    phase_end = phase_start + timedelta(days=typical_days)
                else:
                    continue
                last_end = phase_end
            else:
                if last_end is None:
                    continue
                phase_start = last_end
                phase_end = phase_start + timedelta(days=typical_days)
                last_end = phase_end

            # Resolve effective watering interval: cultivar > phase > skip
            interval = cultivar_map.get(gp_name) or gp.get("watering_interval_days")
            if interval is None:
                continue

            intervals.append(
                PhaseInterval(
                    phase_name=gp_name,
                    start_date=phase_start.date() if isinstance(phase_start, datetime) else phase_start,
                    end_date=phase_end.date() if isinstance(phase_end, datetime) else phase_end,
                    interval_days=interval,
                )
            )

        return intervals

    @staticmethod
    def _task_category_map(category: str) -> CalendarEventCategory:
        mapping = {
            "training": CalendarEventCategory.TRAINING,
            "pruning": CalendarEventCategory.PRUNING,
            "transplanting": CalendarEventCategory.TRANSPLANTING,
            "feeding": CalendarEventCategory.FEEDING,
            "ipm": CalendarEventCategory.IPM,
            "harvest": CalendarEventCategory.HARVEST,
            "maintenance": CalendarEventCategory.MAINTENANCE,
        }
        return mapping.get(category, CalendarEventCategory.CUSTOM)

    @staticmethod
    def _parse_dt(value: str | datetime | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
