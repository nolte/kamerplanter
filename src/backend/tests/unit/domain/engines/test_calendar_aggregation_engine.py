from datetime import UTC, date, datetime
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
        phase_doc = {
            "_key": "ph1",
            "to_phase": "flowering",
            "notes": "Switched",
            "transitioned_at": "2026-03-10T08:00:00+00:00",
            "plant_key": "p2",
        }
        mock_db.aql.execute.side_effect = [
            iter([]),  # tasks
            iter([phase_doc]),
            iter([]),
            iter([]),
        ]

        query = CalendarEventsQuery(
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 31),
            tenant_key="",
        )
        events = engine.get_events(query)

        assert len(events) == 1
        assert events[0].category == CalendarEventCategory.PHASE_TRANSITION
        assert events[0].source == CalendarEventSource.PHASE_TRANSITION

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
        assert (
            CalendarAggregationEngine._task_category_map("training")
            == CalendarEventCategory.TRAINING
        )

    def test_unknown_category(self):
        assert (
            CalendarAggregationEngine._task_category_map("unknown")
            == CalendarEventCategory.CUSTOM
        )
