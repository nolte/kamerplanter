"""In-memory doubles of the weather fetch ports (REQ-046 §3.6a, #2934)."""

from __future__ import annotations

from app.domain.interfaces.weather_fetch import (
    IWeatherFetchGate,
    IWeatherFetchStatusRepository,
    WeatherFetchGateUnavailableError,
)
from app.domain.models.weather_fetch import WeatherFetchRun, WeatherFetchStatus


class InMemoryWeatherFetchStatusRepo(IWeatherFetchStatusRepository):
    def __init__(self, status: WeatherFetchStatus | None = None) -> None:
        self.status = status or WeatherFetchStatus()
        self.recorded: list[WeatherFetchRun] = []

    def get_status(self) -> WeatherFetchStatus:
        return self.status

    def record_run(self, run: WeatherFetchRun) -> None:
        self.recorded.append(run)
        self.status = WeatherFetchStatus(last_run=run, last_success=run if run.success else self.status.last_success)


class FakeWeatherFetchGate(IWeatherFetchGate):
    def __init__(self, *, running: bool = False, cooldown: int = 0, down: bool = False) -> None:
        self.running = running
        self.cooldown = cooldown
        self.down = down
        self.claimed: list[int] = []
        self.released_cooldown = False
        self.lock_ttls: list[int] = []
        self.released_tokens: list[str] = []

    def _check(self) -> None:
        if self.down:
            raise WeatherFetchGateUnavailableError("down")

    def acquire_run_lock(self, ttl_seconds: int) -> str | None:
        self._check()
        self.lock_ttls.append(ttl_seconds)
        if self.running:
            return None
        self.running = True
        return "token"

    def release_run_lock(self, token: str) -> None:
        self.released_tokens.append(token)
        self.running = False

    def is_running(self) -> bool:
        self._check()
        return self.running

    def claim_manual_cooldown(self, seconds: int) -> int:
        self._check()
        if self.cooldown:
            return self.cooldown
        self.claimed.append(seconds)
        self.cooldown = seconds
        return 0

    def release_manual_cooldown(self) -> None:
        self.released_cooldown = True
        self.cooldown = 0

    def manual_cooldown_remaining(self) -> int:
        self._check()
        return self.cooldown
