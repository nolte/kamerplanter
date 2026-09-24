from abc import ABC, abstractmethod


class ICalendarSourceRepository(ABC):
    """The reads the aggregated calendar (REQ-015) is built from (#1638).

    Each method returns the raw rows one event source contributes; turning them
    into :class:`~app.domain.models.calendar.CalendarEvent` objects is the job of
    the stateless
    :class:`~app.domain.engines.calendar_aggregation_engine.CalendarAggregationEngine`.
    Window bounds are ISO-8601 strings, compared lexicographically against the
    stored ISO timestamps exactly as the queries always did.
    """

    @abstractmethod
    def list_tasks_due(self, start: str, end: str, *, tenant_key: str) -> list[dict]:
        """Tasks of ``tenant_key`` whose ``due_date`` lies in ``[start, end]``."""
        ...

    @abstractmethod
    def list_phase_timeline_rows(self) -> list[dict]:
        """One row per active plant: its lifecycle growth phases and phase histories."""
        ...

    @abstractmethod
    def list_maintenance_logs(self, start: str, end: str) -> list[dict]:
        """Tank maintenance logs performed in ``[start, end]``."""
        ...

    @abstractmethod
    def list_watering_logs(self, start: str, end: str) -> list[dict]:
        """Watering logs in ``[start, end]``, each with ``resolved_plant_names``."""
        ...

    @abstractmethod
    def list_watering_forecast_rows(self, *, tenant_key: str) -> list[dict]:
        """One row per active plant of ``tenant_key`` that has a care profile.

        Carries the care profile, the last confirmed watering, the lifecycle
        phases and histories, the cultivar's phase overrides and the followed
        nutrient plan with its phase entries.
        """
        ...

    @abstractmethod
    def get_fertilizer_product_names(self, keys: list[str]) -> dict[str, str]:
        """``{fertilizer_key: product_name}`` for the keys that exist; missing keys are omitted."""
        ...
