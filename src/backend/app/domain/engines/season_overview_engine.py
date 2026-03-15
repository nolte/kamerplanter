"""Season overview engine — aggregates sowing/harvest/task counts per month."""

from datetime import date

from pydantic import BaseModel

from app.domain.engines.sowing_calendar_engine import SowingCalendarEntry


class MonthSummary(BaseModel):
    month: int  # 1-12
    month_name: str = ""
    sowing_count: int = 0
    harvest_count: int = 0
    bloom_count: int = 0
    task_count: int = 0
    top_tasks: list[str] = []
    is_current: bool = False


class SeasonOverview(BaseModel):
    site_key: str = ""
    site_name: str = ""
    year: int
    months: list[MonthSummary] = []


class TaskEvent(BaseModel):
    """Minimal task info for aggregation."""

    month: int  # 1-12
    title: str = ""
    priority: int = 0  # higher = more important


class SeasonOverviewEngine:
    """Builds a 12-month season overview from sowing entries and task events."""

    def build_overview(
        self,
        sowing_entries: list[SowingCalendarEntry],
        task_events: list[TaskEvent],
        site_key: str,
        site_name: str,
        year: int,
    ) -> SeasonOverview:
        today = date.today()
        current_month = today.month if today.year == year else 0

        # Aggregate task events by month
        task_by_month: dict[int, list[TaskEvent]] = {m: [] for m in range(1, 13)}
        for te in task_events:
            if 1 <= te.month <= 12:
                task_by_month[te.month].append(te)

        months: list[MonthSummary] = []
        for m in range(1, 13):
            sowing_count = 0
            harvest_count = 0
            bloom_count = 0
            for entry in sowing_entries:
                for bar in entry.bars:
                    bar_start_month = bar.start_date.month
                    bar_end_month = bar.end_date.month
                    if bar_start_month <= m <= bar_end_month:
                        if bar.phase in (
                            "indoor_sowing",
                            "outdoor_planting",
                            "germination",
                            "seedling",
                        ):
                            sowing_count += 1
                        elif bar.phase in ("harvest", "ripening"):
                            harvest_count += 1
                        elif bar.phase in ("flowering", "bloom"):
                            bloom_count += 1

            month_tasks = task_by_month[m]
            top_sorted = sorted(month_tasks, key=lambda t: t.priority, reverse=True)
            top_tasks = [t.title for t in top_sorted[:3]]

            months.append(
                MonthSummary(
                    month=m,
                    sowing_count=sowing_count,
                    harvest_count=harvest_count,
                    bloom_count=bloom_count,
                    task_count=len(month_tasks),
                    top_tasks=top_tasks,
                    is_current=(m == current_month),
                )
            )

        return SeasonOverview(
            site_key=site_key,
            site_name=site_name,
            year=year,
            months=months,
        )
