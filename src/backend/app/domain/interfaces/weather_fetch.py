"""REQ-046 §3.6a (#2934) — ports of the weather fetch schedule.

Two concerns, two ports:

* :class:`IWeatherFetchStatusRepository` — the dedicated status document the fetch
  task writes after every run (newest run, newest successful run). The interval
  counts from the newest success, the admin status reads both.
* :class:`IWeatherFetchGate` — the "a fetch is running" lock the fetch task holds
  while it runs, and the cooldown after a manual fetch. Both live in Valkey so the
  API process and every worker see the same state.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Protocol

from app.domain.models.weather_fetch import WeatherFetchRun, WeatherFetchStatus


class WeatherFetchGateUnavailableError(Exception):
    """The lock/cooldown store cannot be reached — the state is unknown."""


class IWeatherFetchSettings(Protocol):
    """The two settings the schedule reads on every call (DB over env), so changes need no restart."""

    def fetch_interval_hours(self) -> int: ...

    def weather_enabled(self) -> bool: ...


class IWeatherFetchClock(Protocol):
    """Where the schedule reads the time — a seam for tests."""

    def now(self) -> datetime: ...


class IWeatherFetchStatusRepository(ABC):
    """The weather fetch status document (written only by the fetch task)."""

    @abstractmethod
    def get_status(self) -> WeatherFetchStatus:
        """The stored status; an empty one when no run was recorded or the document is unreadable."""
        ...

    @abstractmethod
    def record_run(self, run: WeatherFetchRun) -> int:
        """Store ``run`` as the newest run, and as the newest success when it succeeded.

        One statement, so a concurrent reader never sees a half-written document.

        Returns:
            The failed runs in a row after this one (``0`` after a success).
        """
        ...


class IWeatherFetchGate(ABC):
    """Running lock and manual-fetch cooldown, shared across processes."""

    @abstractmethod
    def acquire_run_lock(self, ttl_seconds: int) -> str | None:
        """Take the running lock for at most ``ttl_seconds``.

        Returns:
            A token to release the lock with, or ``None`` when another run holds it.

        Raises:
            WeatherFetchGateUnavailableError: the store cannot be reached.
        """
        ...

    @abstractmethod
    def release_run_lock(self, token: str) -> None:
        """Release the lock if ``token`` still holds it (never another run's lock)."""
        ...

    @abstractmethod
    def is_running(self) -> bool:
        """Whether some run holds the lock.

        Raises:
            WeatherFetchGateUnavailableError: the store cannot be reached.
        """
        ...

    @abstractmethod
    def claim_manual_cooldown(self, seconds: int) -> int:
        """Atomically start the manual-fetch cooldown.

        Returns:
            ``0`` when the cooldown was free and is now claimed; otherwise the
            seconds until it ends (at least 1).

        Raises:
            WeatherFetchGateUnavailableError: the store cannot be reached.
        """
        ...

    @abstractmethod
    def release_manual_cooldown(self) -> None:
        """Drop the cooldown again (a manual fetch that could not be queued)."""
        ...

    @abstractmethod
    def manual_cooldown_remaining(self) -> int:
        """Seconds until the next manual fetch is allowed, ``0`` when it is now.

        Raises:
            WeatherFetchGateUnavailableError: the store cannot be reached.
        """
        ...
