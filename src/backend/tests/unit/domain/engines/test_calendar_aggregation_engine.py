from datetime import date
from unittest.mock import MagicMock

import pytest

from app.common.enums import CalendarEventCategory, CalendarEventSource
from app.domain.engines.calendar_aggregation_engine import CalendarAggregationEngine
from app.domain.models.calendar import CalendarEventsQuery


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def engine(mock_db):
    return CalendarAggregationEngine(mock_db)


class TestGetEvents:
    def test_returns_task_events(self, engine, mock_db):
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
        events = engine.get_events(query)

        assert len(events) == 1
        assert events[0].id == "task:t1"
        assert events[0].title == "Water plants"
        assert events[0].category == CalendarEventCategory.FEEDING
        assert events[0].source == CalendarEventSource.TASK

    def test_returns_phase_transition_events(self, engine, mock_db):
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
        events = engine.get_events(query)

        phase_events = [e for e in events if e.category == CalendarEventCategory.PHASE_TRANSITION]
        assert len(phase_events) >= 1
        assert phase_events[0].source == CalendarEventSource.PHASE_TRANSITION

    def test_returns_maintenance_events(self, engine, mock_db):
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
        events = engine.get_events(query)

        assert len(events) == 1
        assert events[0].category == CalendarEventCategory.TANK_MAINTENANCE

    def test_returns_watering_events(self, engine, mock_db):
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
        events = engine.get_events(query)

        assert len(events) == 1
        assert events[0].category == CalendarEventCategory.FEEDING
        assert events[0].source == CalendarEventSource.WATERING

    def test_category_filter(self, engine, mock_db):
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
        events = engine.get_events(query)

        assert len(events) == 1
        assert events[0].category == CalendarEventCategory.PRUNING

    def test_empty_results(self, engine, mock_db):
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
        events = engine.get_events(query)
        assert events == []

    def test_events_sorted_by_start(self, engine, mock_db):
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
        events = engine.get_events(query)
        assert len(events) == 2
        assert events[0].title == "Early"
        assert events[1].title == "Late"


class TestTaskCategoryMap:
    def test_known_category(self):
        assert CalendarAggregationEngine._task_category_map("training") == CalendarEventCategory.TRAINING

    def test_unknown_category(self):
        assert CalendarAggregationEngine._task_category_map("unknown") == CalendarEventCategory.CUSTOM
