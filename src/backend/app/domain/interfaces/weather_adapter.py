"""REQ-046 §3.1 — ``WeatherAdapter`` ABC (SSOT for weather data sources).

Abstract base for every weather data source, public (DWD / OpenWeatherMap /
Open-Meteo / NASA POWER) or Home Assistant. Concrete adapters register
themselves via ``@WeatherAdapterRegistry.register`` and are the only place that
talks to an external weather API or the HA REST client.
"""

from abc import ABC, abstractmethod

from app.domain.models.weather import ClimateNormal, WeatherForecast


class WeatherAdapter(ABC):
    """Abstract base for all weather data sources (public or Home Assistant).

    Implementations register via ``@WeatherAdapterRegistry.register``.
    - Public services (DWD / OpenWeatherMap / Open-Meteo / NASA POWER) call HTTP
      APIs.
    - The ``HomeAssistantWeatherAdapter`` reads through the HA REST client.
    """

    #: Unique registry key; matches ``WeatherForecast.source``.
    source_name: str
    #: Coarse class for UI switching / config discrimination
    #: (``'public'`` | ``'home_assistant'``).
    kind: str
    #: Whether this adapter needs a secret (API key).
    requires_api_key: bool = False

    @abstractmethod
    async def fetch_daily(
        self, *, latitude: float, longitude: float, config: object | None = None
    ) -> list[WeatherForecast]:
        """Return daily values / forecast for a location.

        ``config`` is the source-specific ``WeatherSourceEntry.config`` (e.g. an
        HA mapping or an OpenWeatherMap key reference).
        """

    async def fetch_climate_normals(self, *, latitude: float, longitude: float) -> ClimateNormal | None:
        """Optional — only adapters with climate normals (REQ-041 / REQ-039)
        override this. Default: no climate normals available."""
        return None

    async def health_check(self, *, config: object | None = None) -> bool:
        """Connectivity test for the UI ("test source").

        The default is intentionally unimplemented so concrete adapters provide a
        lightweight probe (they may reuse ``fetch_daily`` at a reference point).
        """
        raise NotImplementedError
