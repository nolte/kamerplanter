"""In-memory doubles of the weather fetch ports (REQ-046 §3.6a, #2934).

The gate mirrors the Valkey gate's semantics: ``acquire_run_lock`` hands out a fresh
token per call and ``release_run_lock`` frees the lock only for the token that holds
it (compare-and-delete), so a test can tell "released my lock" from "released
whatever lock there is".
"""

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

    def record_run(self, run: WeatherFetchRun) -> int:
        self.recorded.append(run)
        failures = 0 if run.success else self.status.consecutive_failures + 1
        self.status = WeatherFetchStatus(
            last_run=run,
            last_success=run if run.success else self.status.last_success,
            consecutive_failures=failures,
        )
        return failures


class FakeWeatherFetchGate(IWeatherFetchGate):
    def __init__(self, *, running: bool = False, cooldown: int = 0, down: bool = False) -> None:
        #: Token of the run that holds the lock, ``None`` when free.
        self.holder: str | None = "someone-else" if running else None
        self.cooldown = cooldown
        self.down = down
        self.claimed: list[int] = []
        self.released_cooldown = False
        self.lock_ttls: list[int] = []
        self.issued: list[str] = []
        self.released_tokens: list[str] = []

    @property
    def running(self) -> bool:
        return self.holder is not None

    def _check(self) -> None:
        if self.down:
            raise WeatherFetchGateUnavailableError("down")

    def acquire_run_lock(self, ttl_seconds: int) -> str | None:
        self._check()
        self.lock_ttls.append(ttl_seconds)
        if self.holder is not None:
            return None
        token = f"token-{len(self.issued) + 1}"
        self.issued.append(token)
        self.holder = token
        return token

    def release_run_lock(self, token: str) -> None:
        self.released_tokens.append(token)
        if self.holder == token:
            self.holder = None

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
