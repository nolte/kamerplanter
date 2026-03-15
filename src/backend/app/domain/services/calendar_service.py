import secrets
from datetime import date, datetime

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine
from app.domain.engines.season_overview_engine import (
    SeasonOverview,
    SeasonOverviewEngine,
    TaskEvent,
)
from app.domain.engines.sowing_calendar_engine import (
    LIFECYCLE_PHASE_COLORS,
    FrostConfig,
    GrowingPeriodData,
    SowingBar,
    SowingCalendarEngine,
    SowingCalendarEntry,
    SpeciesData,
)
from app.domain.interfaces.calendar_feed_repository import ICalendarFeedRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.calendar import (
    CalendarEvent,
    CalendarEventsQuery,
    CalendarFeed,
)
from app.domain.services.ical_generator import ICalGenerator
from app.domain.services.planting_run_service import PlantingRunService


class CalendarService:
    def __init__(
        self,
        feed_repo: ICalendarFeedRepository,
        aggregation_engine: CalendarAggregationEngine,
        species_repo: ISpeciesRepository | None = None,
        site_repo: ISiteRepository | None = None,
        sowing_engine: SowingCalendarEngine | None = None,
        season_engine: SeasonOverviewEngine | None = None,
        planting_run_service=None,
    ) -> None:
        self._feed_repo = feed_repo
        self._engine = aggregation_engine
        self._ical = ICalGenerator()
        self._species_repo = species_repo
        self._site_repo = site_repo
        self._sowing_engine = sowing_engine or SowingCalendarEngine()
        self._season_engine = season_engine or SeasonOverviewEngine()
        self._run_service = planting_run_service

    def get_events(self, query: CalendarEventsQuery) -> list[CalendarEvent]:
        return self._engine.get_events(query)

    # ── Feed CRUD ────────────────────────────────────────────────────

    def create_feed(self, feed: CalendarFeed) -> CalendarFeed:
        feed.token = secrets.token_urlsafe(32)
        return self._feed_repo.save(feed)

    def get_feed(self, key: str) -> CalendarFeed:
        feed = self._feed_repo.get_by_key(key)
        if feed is None:
            raise NotFoundError("CalendarFeed", key)
        return feed

    def list_feeds(self, user_key: str, tenant_key: str) -> list[CalendarFeed]:
        return self._feed_repo.list_by_user(user_key, tenant_key)

    def update_feed(self, key: str, feed: CalendarFeed) -> CalendarFeed:
        existing = self.get_feed(key)
        feed.token = existing.token
        return self._feed_repo.update(key, feed)

    def delete_feed(self, key: str) -> bool:
        self.get_feed(key)
        return self._feed_repo.delete(key)

    def regenerate_token(self, key: str) -> CalendarFeed:
        feed = self.get_feed(key)
        feed.token = secrets.token_urlsafe(32)
        return self._feed_repo.update(key, feed)

    # ── Sowing calendar (REQ-015 §3.8) ─────────────────────────────

    def get_sowing_calendar(
        self,
        site_key: str | None,
        year: int,
    ) -> tuple[list[SowingCalendarEntry], FrostConfig]:
        frost_config = self._build_frost_config(site_key, year)

        run_entries: list[SowingCalendarEntry] = []
        if site_key and self._run_service:
            run_entries = self._build_entries_from_runs(site_key, year)

        # Theoretical species data
        species_list, _ = self._species_repo.get_all(offset=0, limit=5000) if self._species_repo else ([], 0)
        species_data = [
            SpeciesData(
                key=sp.key or "",
                scientific_name=sp.scientific_name,
                common_names=sp.common_names,
                allows_harvest=sp.allows_harvest,
                growing_periods=[
                    GrowingPeriodData(
                        label=gp.label,
                        sowing_indoor_weeks_before_last_frost=gp.sowing_indoor_weeks_before_last_frost,
                        sowing_outdoor_after_last_frost_days=gp.sowing_outdoor_after_last_frost_days,
                        direct_sow_months=gp.direct_sow_months,
                        harvest_months=gp.harvest_months,
                        bloom_months=gp.bloom_months,
                        harvest_from_year=gp.harvest_from_year,
                        bloom_from_year=gp.bloom_from_year,
                    )
                    for gp in sp.growing_periods
                ]
                if sp.growing_periods
                else [],
                sowing_indoor_weeks_before_last_frost=sp.sowing_indoor_weeks_before_last_frost,
                sowing_outdoor_after_last_frost_days=sp.sowing_outdoor_after_last_frost_days,
                direct_sow_months=sp.direct_sow_months,
                harvest_months=sp.harvest_months,
                bloom_months=sp.bloom_months,
                harvest_from_year=sp.harvest_from_year,
                bloom_from_year=sp.bloom_from_year,
                frost_sensitivity=sp.frost_sensitivity,
            )
            for sp in species_list
            if _has_sowing_data(sp)
        ]
        species_entries = self._sowing_engine.build_calendar(species_data, frost_config, year)

        if not run_entries:
            return species_entries, frost_config

        # Merge: run entries take precedence, add species not covered by runs
        run_species_keys = {e.species_key for e in run_entries}
        merged = run_entries + [e for e in species_entries if e.species_key not in run_species_keys]
        return merged, frost_config

    def _build_entries_from_runs(
        self,
        site_key: str,
        year: int,
    ) -> list[SowingCalendarEntry]:
        """Build calendar entries from actual PlantingRun phase timelines.

        Appends the Species' theoretical harvest/bloom period so the Gantt
        always extends to the expected harvest window.
        """

        run_svc: PlantingRunService = self._run_service
        runs = run_svc._repo.get_runs_at_site(site_key)
        if not runs:
            return []

        entries: list[SowingCalendarEntry] = []
        for run in runs:
            if run.key is None:
                continue
            timelines = run_svc.get_phase_timeline(run.key)
            bars = self._timeline_to_bars(timelines, year)

            # Append Species-level harvest/bloom window so the Gantt always
            # shows how far out the expected harvest is.
            run_entries = run_svc._repo.get_entries(run.key)
            for re in run_entries:
                bars.extend(self._species_harvest_bars(re.species_key, year))

            if not bars:
                continue
            entries.append(
                SowingCalendarEntry(
                    species_key=run.key,
                    species_name=run.name,
                    common_name=run.name,
                    bars=bars,
                )
            )

        entries.sort(key=lambda e: min(b.start_date for b in e.bars) if e.bars else date.max)
        return entries

    def _species_harvest_bars(self, species_key: str, year: int) -> list[SowingBar]:
        """Build harvest/bloom bars from Species stammdaten (harvest_months / bloom_months)."""
        if not self._species_repo:
            return []
        sp = self._species_repo.get_by_key(species_key)
        if sp is None:
            return []

        bars: list[SowingBar] = []
        is_ornamental = not sp.allows_harvest
        if is_ornamental and sp.bloom_months:
            for ps, pe in _split_months(sp.bloom_months):
                bars.append(
                    SowingBar(
                        phase="flowering",
                        color=LIFECYCLE_PHASE_COLORS.get("flowering", "#EC407A"),
                        start_date=date(year, ps, 1),
                        end_date=_month_end(year, pe),
                        label="flowering",
                    )
                )
        elif sp.harvest_months:
            for ps, pe in _split_months(sp.harvest_months):
                bars.append(
                    SowingBar(
                        phase="harvest",
                        color=LIFECYCLE_PHASE_COLORS.get("harvest", "#FFA726"),
                        start_date=date(year, ps, 1),
                        end_date=_month_end(year, pe),
                        label="harvest",
                    )
                )
        return bars

    @staticmethod
    def _timeline_to_bars(timelines: list[dict], year: int) -> list[SowingBar]:
        """Convert PlantingRun phase timeline dicts to SowingBar list."""
        bars: list[SowingBar] = []
        for tl in timelines:
            for phase in tl.get("phases", []):
                start_dt = phase.get("actual_entered_at") or phase.get("projected_start")
                end_dt = phase.get("actual_exited_at") or phase.get("projected_end")
                if start_dt is None or end_dt is None:
                    continue

                start_d = _to_date(start_dt)
                end_d = _to_date(end_dt)

                # Only include bars that overlap with the requested year
                if end_d.year < year or start_d.year > year:
                    continue

                # Clamp to year boundaries
                start_d = max(start_d, date(year, 1, 1))
                end_d = min(end_d, date(year, 12, 31))

                if start_d > end_d:
                    continue

                phase_name = phase.get("phase_name", "")
                color = LIFECYCLE_PHASE_COLORS.get(phase_name, "#9E9E9E")

                bars.append(
                    SowingBar(
                        phase=phase_name,
                        color=color,
                        start_date=start_d,
                        end_date=end_d,
                        label=phase.get("display_name", phase_name),
                    )
                )
        return bars

    def get_season_overview(
        self,
        site_key: str | None,
        year: int,
    ) -> SeasonOverview:
        entries, frost_config = self.get_sowing_calendar(site_key, year)
        site_name = ""
        if site_key and self._site_repo:
            site = self._site_repo.get_site_by_key(site_key)
            if site:
                site_name = site.name

        # For now, task_events is empty — can be expanded with AQL aggregation
        task_events: list[TaskEvent] = []
        return self._season_engine.build_overview(
            entries,
            task_events,
            site_key or "",
            site_name,
            year,
        )

    def _build_frost_config(self, site_key: str | None, year: int) -> FrostConfig:
        if site_key and self._site_repo:
            site = self._site_repo.get_site_by_key(site_key)
            if site:
                return FrostConfig(
                    last_frost_date=(site.last_frost_date_avg or date(year, 5, 15)).replace(year=year),
                    first_frost_date=(
                        site.first_frost_date_avg.replace(year=year) if site.first_frost_date_avg else None
                    ),
                    eisheilige_date=(site.eisheilige_date or date(year, 5, 15)).replace(year=year),
                )
        return FrostConfig(
            last_frost_date=date(year, 5, 15),
            eisheilige_date=date(year, 5, 15),
        )

    # ── iCal generation ──────────────────────────────────────────────

    def generate_ical_for_feed(self, feed_key: str, token: str) -> str:
        feed = self._feed_repo.get_by_token(token)
        if feed is None or feed.key != feed_key:
            raise ValidationError("Invalid feed token")
        if not feed.is_active:
            raise ValidationError("Feed is inactive")

        from datetime import timedelta

        query = CalendarEventsQuery(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=90),
            categories=feed.filters.categories,
            site_key=feed.filters.site_key,
            tenant_key=feed.tenant_key,
        )
        events = self._engine.get_events(query)
        return self._ical.generate(events, feed.name)


def _has_sowing_data(sp) -> bool:
    """Check whether a Species has any sowing/harvest fields populated."""
    return bool(
        sp.growing_periods
        or sp.sowing_indoor_weeks_before_last_frost is not None
        or sp.sowing_outdoor_after_last_frost_days is not None
        or sp.direct_sow_months
        or sp.harvest_months
        or sp.bloom_months
    )


def _to_date(dt: datetime | date | str) -> date:
    """Convert datetime, date, or ISO string to date."""
    if isinstance(dt, datetime):
        return dt.date()
    if isinstance(dt, date):
        return dt
    if isinstance(dt, str):
        return datetime.fromisoformat(dt).date()
    return date.today()


def _split_months(months: list[int]) -> list[tuple[int, int]]:
    """Split a list of months into contiguous period tuples.

    Example: [3, 4, 5, 6, 9, 10] → [(3, 6), (9, 10)]
    """
    if not months:
        return []

    sorted_months = sorted(set(months))
    periods: list[tuple[int, int]] = []
    start = sorted_months[0]
    prev = sorted_months[0]
    for m in sorted_months[1:]:
        if m == prev + 1:
            prev = m
        else:
            periods.append((start, prev))
            start = m
            prev = m
    periods.append((start, prev))
    return periods


def _month_end(year: int, month: int) -> date:
    """Last day of the given month."""
    from datetime import timedelta as _td  # noqa: F811

    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - _td(days=1)
