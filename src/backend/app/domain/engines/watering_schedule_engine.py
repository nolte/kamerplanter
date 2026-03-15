from datetime import date, timedelta
from typing import TYPE_CHECKING

from app.common.enums import ScheduleMode

if TYPE_CHECKING:
    from app.domain.models.nutrient_plan import DeliveryChannel, NutrientPlanPhaseEntry, WateringSchedule


class WateringScheduleEngine:
    """Pure domain logic for watering schedule calculations."""

    @staticmethod
    def is_watering_due(
        schedule: WateringSchedule,
        check_date: date,
        last_watering_date: date | None = None,
    ) -> bool:
        """Check whether watering is due on the given date."""
        if schedule.schedule_mode == ScheduleMode.WEEKDAYS:
            return check_date.weekday() in schedule.weekday_schedule

        # INTERVAL mode
        if schedule.interval_days is None:
            return False
        if last_watering_date is None:
            return True
        days_since = (check_date - last_watering_date).days
        return days_since >= schedule.interval_days

    @staticmethod
    def get_next_watering_dates(
        schedule: WateringSchedule,
        from_date: date,
        days_ahead: int = 14,
        last_watering_date: date | None = None,
    ) -> list[date]:
        """Return upcoming watering dates within the look-ahead window."""
        dates: list[date] = []

        if schedule.schedule_mode == ScheduleMode.WEEKDAYS:
            for offset in range(days_ahead):
                d = from_date + timedelta(days=offset)
                if d.weekday() in schedule.weekday_schedule:
                    dates.append(d)
            return dates

        # INTERVAL mode
        if schedule.interval_days is None:
            return dates
        if last_watering_date is None:
            next_date = from_date
        else:
            days_since = (from_date - last_watering_date).days
            remaining = schedule.interval_days - (days_since % schedule.interval_days)
            if remaining == schedule.interval_days and days_since > 0:
                next_date = from_date
            else:
                next_date = from_date + timedelta(days=remaining)

        end = from_date + timedelta(days=days_ahead)
        while next_date < end:
            dates.append(next_date)
            next_date += timedelta(days=schedule.interval_days)
        return dates

    @staticmethod
    def get_due_channels(
        entry: NutrientPlanPhaseEntry,
        check_date: date,
        last_dates_per_channel: dict[str, date | None] | None = None,
    ) -> list[DeliveryChannel]:
        """Return channels that are due on check_date.

        Channels with no schedule are always returned (defers to caller).
        Disabled channels are skipped.
        """
        if last_dates_per_channel is None:
            last_dates_per_channel = {}

        channels = entry.delivery_channels
        due: list[DeliveryChannel] = []

        for ch in channels:
            if not ch.enabled:
                continue
            if ch.schedule is None:
                due.append(ch)
                continue
            last_date = last_dates_per_channel.get(ch.channel_id)
            if WateringScheduleEngine.is_watering_due(ch.schedule, check_date, last_date):
                due.append(ch)

        return due

    @staticmethod
    def resolve_dosages_for_run(
        plan_entries: list[dict],
        plants_by_phase: dict[str, list[str]],
    ) -> dict[str, dict]:
        """Map phase → channels + plant_keys from plan entries and plant phases.

        Returns: {phase_name: {"channels": [...], "plant_keys": [...]}}
        """
        result: dict[str, dict] = {}
        for entry in plan_entries:
            phase = entry.get("phase_name", "")
            if phase in plants_by_phase:
                result[phase] = {
                    "channels": entry.get("delivery_channels", []),
                    "plant_keys": plants_by_phase[phase],
                }
        return result
