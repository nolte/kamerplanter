from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import CalendarEventCategory, CalendarEventSource
from app.data_access.arango.calendar_source_repository import ArangoCalendarSourceRepository
from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine, CalendarSourceRows
from app.domain.models.calendar import CalendarEventsQuery
from app.domain.services.calendar_service import CalendarService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def calendar(mock_db):
    """The production pipeline over a driver double (#1638).

    The engine no longer reads anything: ``CalendarService`` loads the rows
    through ``ArangoCalendarSourceRepository`` and hands them to the stateless
    engine. The queries run in the same order as before, so each test's
    ``side_effect`` list still reads tasks, phases, maintenance, watering,
    forecast.
    """
    return CalendarService(MagicMock(), CalendarAggregationEngine(), ArangoCalendarSourceRepository(mock_db))


class TestGetEvents:
    def test_returns_task_events(self, calendar, mock_db):
        task_doc = {
            "_key": "t1",
            "name": "Water plants",
            "instruction": "Do it",
            "category": "feeding",
            "due_date": "2026-03-01T10:00:00+00:00",
            "plant_key": "p1",
            "tenant_key": "tenant1",
        }
        mock_db.aql.execute.side_effect = [
            iter([task_doc]),  # tasks
            iter([]),  # phase_histories
            iter([]),  # maintenance_logs
            iter([]),  # watering_events
            iter([]),  # watering_forecast
        ]

        query = CalendarEventsQuery(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            tenant_key="tenant1",
        )
        events = calendar.get_events(query)

        assert len(events) == 1
        assert events[0].id == "task:t1"
        assert events[0].title == "Water plants"
        assert events[0].category == CalendarEventCategory.FEEDING
        assert events[0].source == CalendarEventSource.TASK

    def test_returns_phase_transition_events(self, calendar, mock_db):
        plant_doc = {
            "plant_key": "p2",
            "instance_id": "monstera-1",
            "plant_name": "My Monstera",
            "species_key": "sp1",
            "current_phase": "flowering",
            "run_key": None,
            "run_name": None,
            "growth_phases": [
                {
                    "_key": "gp1",
                    "_id": "growth_phases/gp1",
                    "name": "vegetative",
                    "sequence_order": 1,
                    "typical_duration_days": 30,
                },
                {
                    "_key": "gp2",
                    "_id": "growth_phases/gp2",
                    "name": "flowering",
                    "sequence_order": 2,
                    "typical_duration_days": 60,
                },
            ],
            "phase_histories": [
                {
                    "_key": "ph0",
                    "phase_name": "vegetative",
                    "entered_at": "2026-02-01T00:00:00+00:00",
                    "exited_at": "2026-03-01T00:00:00+00:00",
                    "plant_instance_key": "p2",
                },
                {
                    "_key": "ph1",
                    "phase_name": "flowering",
                    "entered_at": "2026-03-01T00:00:00+00:00",
                    "exited_at": None,
                    "plant_instance_key": "p2",
                },
            ],
        }
        mock_db.aql.execute.side_effect = [
            iter([]),  # tasks
            iter([plant_doc]),  # phase_transitions (complex join)
            iter([]),  # maintenance_logs
            iter([]),  # watering_events
            iter([]),  # watering_forecast
        ]

        query = CalendarEventsQuery(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            tenant_key="",
        )
        events = calendar.get_events(query)

        phase_events = [e for e in events if e.category == CalendarEventCategory.PHASE_TRANSITION]
        assert len(phase_events) >= 1
        assert phase_events[0].source == CalendarEventSource.PHASE_TRANSITION

    def test_returns_maintenance_events(self, calendar, mock_db):
        maint_doc = {
            "_key": "m1",
            "action": "Tank cleaning",
            "notes": "Monthly clean",
            "performed_at": "2026-03-15T14:00:00+00:00",
        }
        mock_db.aql.execute.side_effect = [
            iter([]),
            iter([]),
            iter([maint_doc]),
            iter([]),
            iter([]),  # watering_forecast
        ]

        query = CalendarEventsQuery(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            tenant_key="",
        )
        events = calendar.get_events(query)

        assert len(events) == 1
        assert events[0].category == CalendarEventCategory.TANK_MAINTENANCE

    def test_returns_watering_events(self, calendar, mock_db):
        water_doc = {
            "_key": "w1",
            "notes": "Light watering",
            "watered_at": "2026-03-05T09:00:00+00:00",
        }
        mock_db.aql.execute.side_effect = [
            iter([]),
            iter([]),
            iter([]),
            iter([water_doc]),
            iter([]),  # watering_forecast
        ]

        query = CalendarEventsQuery(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            tenant_key="",
        )
        events = calendar.get_events(query)

        assert len(events) == 1
        assert events[0].category == CalendarEventCategory.FEEDING
        assert events[0].source == CalendarEventSource.WATERING

    def test_category_filter(self, calendar, mock_db):
        task1 = {
            "_key": "t1",
            "name": "Feed",
            "category": "feeding",
            "due_date": "2026-03-01T10:00:00+00:00",
            "tenant_key": "",
        }
        task2 = {
            "_key": "t2",
            "name": "Prune",
            "category": "pruning",
            "due_date": "2026-03-02T10:00:00+00:00",
            "tenant_key": "",
        }
        mock_db.aql.execute.side_effect = [
            iter([task1, task2]),
            iter([]),
            iter([]),
            iter([]),
            iter([]),  # watering_forecast
        ]

        query = CalendarEventsQuery(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            categories=[CalendarEventCategory.PRUNING],
            tenant_key="",
        )
        events = calendar.get_events(query)

        assert len(events) == 1
        assert events[0].category == CalendarEventCategory.PRUNING

    def test_empty_results(self, calendar, mock_db):
        mock_db.aql.execute.side_effect = [
            iter([]),
            iter([]),
            iter([]),
            iter([]),
            iter([]),  # watering_forecast
        ]

        query = CalendarEventsQuery(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            tenant_key="",
        )
        events = calendar.get_events(query)
        assert events == []

    def test_events_sorted_by_start(self, calendar, mock_db):
        task_late = {
            "_key": "t1",
            "name": "Late",
            "category": "feeding",
            "due_date": "2026-03-20T10:00:00+00:00",
            "tenant_key": "",
        }
        task_early = {
            "_key": "t2",
            "name": "Early",
            "category": "pruning",
            "due_date": "2026-03-05T10:00:00+00:00",
            "tenant_key": "",
        }
        mock_db.aql.execute.side_effect = [
            iter([task_late, task_early]),
            iter([]),
            iter([]),
            iter([]),
            iter([]),  # watering_forecast
        ]

        query = CalendarEventsQuery(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            tenant_key="",
        )
        events = calendar.get_events(query)
        assert len(events) == 2
        assert events[0].title == "Early"
        assert events[1].title == "Late"


class TestTaskCategoryMap:
    def test_known_category(self):
        assert CalendarAggregationEngine._task_category_map("training") == CalendarEventCategory.TRAINING

    def test_unknown_category(self):
        assert CalendarAggregationEngine._task_category_map("unknown") == CalendarEventCategory.CUSTOM


class TestTheEngineIsPure:
    """#1638: the engine aggregates rows it is handed and reads nothing itself."""

    def test_it_holds_no_collaborator(self):
        assert vars(CalendarAggregationEngine()) == {}

    def test_it_aggregates_preloaded_rows(self):
        rows = CalendarSourceRows(
            tasks=[{"_key": "t1", "name": "Prune", "category": "pruning", "due_date": "2026-03-02T10:00:00+00:00"}],
            maintenance_logs=[{"_key": "m1", "action": "Clean", "performed_at": "2026-03-01T10:00:00+00:00"}],
        )
        query = CalendarEventsQuery(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31), tenant_key="t")

        events = CalendarAggregationEngine().aggregate(query, rows)

        assert [e.id for e in events] == ["maint:m1", "task:t1"]

    def test_dosage_names_come_from_the_preloaded_map_and_fall_back_to_the_key(self):
        doc = {
            "current_phase": "veg",
            "planted_on": "2026-03-01",
            "plan_entries": [
                {
                    "phase_name": "veg",
                    "sequence_order": 1,
                    "week_start": 1,
                    "week_end": 4,
                    "delivery_channels": [
                        {
                            "fertilizer_dosages": [
                                {"fertilizer_key": "f-known", "ml_per_liter": 1.0},
                                {"fertilizer_key": "f-unknown", "ml_per_liter": 2.0},
                            ]
                        }
                    ],
                }
            ],
        }
        now = datetime(2026, 3, 8, tzinfo=UTC)

        meta = CalendarAggregationEngine()._resolve_dosage_metadata(doc, now, {"f-known": "Known Grow"})

        assert [d["product_name"] for d in meta["dosages"]] == ["Known Grow", "f-unknown"]
        assert CalendarAggregationEngine.forecast_fertilizer_keys([doc]) == ["f-known", "f-unknown"]


class TestTheServiceLoadsThroughTheRepository:
    def test_a_failing_forecast_read_degrades_to_no_forecast(self):
        sources = MagicMock()
        sources.list_tasks_due.return_value = [
            {"_key": "t1", "name": "Feed", "category": "feeding", "due_date": "2026-03-02T10:00:00+00:00"}
        ]
        sources.list_phase_timeline_rows.return_value = []
        sources.list_maintenance_logs.return_value = []
        sources.list_watering_logs.return_value = []
        sources.list_watering_forecast_rows.side_effect = RuntimeError("down")
        service = CalendarService(MagicMock(), CalendarAggregationEngine(), sources)
        query = CalendarEventsQuery(start_date=date(2026, 3, 1), end_date=date(2026, 3, 31), tenant_key="t1")

        events = service.get_events(query)

        assert [e.id for e in events] == ["task:t1"]
        sources.list_tasks_due.assert_called_once_with(
            "2026-03-01T00:00:00+00:00", "2026-03-31T23:59:59+00:00", tenant_key="t1"
        )
        sources.list_watering_forecast_rows.assert_called_once_with(tenant_key="t1")
        sources.get_fertilizer_product_names.assert_not_called()
