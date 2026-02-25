import structlog
from httpx import Client, HTTPStatusError, RequestError

from app.common.exceptions import ExternalSourceError
from app.config.settings import settings
from app.domain.interfaces.external_source_adapter import ExternalSourceAdapter
from app.domain.models.enrichment import ExternalSpeciesData
from app.domain.services.adapter_registry import AdapterRegistry

logger = structlog.get_logger()


@AdapterRegistry.register
class PerenualAdapter(ExternalSourceAdapter):
    source_key = "perenual"
    rate_limit_per_minute = 30

    BASE_URL = "https://perenual.com/api/v2"

    def __init__(self) -> None:
        self._client = Client(base_url=self.BASE_URL, timeout=settings.enrichment_http_timeout)

    @property
    def _api_key(self) -> str:
        return settings.perenual_api_key

    def _params(self, **extra: str | int) -> dict[str, str | int]:
        params: dict[str, str | int] = {"key": self._api_key}
        params.update(extra)
        return params

    def search_species(self, query: str) -> list[ExternalSpeciesData]:
        if not self._api_key:
            return []
        try:
            response = self._client.get("/species-list", params=self._params(q=query))
            response.raise_for_status()
            data = response.json()
            return [self._map_species(r) for r in data.get("data", []) if r.get("scientific_name")]
        except (HTTPStatusError, RequestError) as e:
            logger.warning("perenual_search_failed", query=query, error=str(e))
            raise ExternalSourceError("perenual", str(e)) from e

    def get_species_by_id(self, external_id: str) -> ExternalSpeciesData | None:
        if not self._api_key:
            return None
        try:
            response = self._client.get(f"/species/details/{external_id}", params=self._params())
            response.raise_for_status()
            data = response.json()
            if not data.get("scientific_name"):
                return None
            return self._map_species(data)
        except (HTTPStatusError, RequestError) as e:
            logger.warning("perenual_get_species_failed", external_id=external_id, error=str(e))
            raise ExternalSourceError("perenual", str(e)) from e

    def get_species_list(self, page: int = 1, per_page: int = 30) -> tuple[list[ExternalSpeciesData], int]:
        if not self._api_key:
            return [], 0
        try:
            response = self._client.get("/species-list", params=self._params(page=page))
            response.raise_for_status()
            data = response.json()
            total = data.get("total", 0)
            results = [self._map_species(r) for r in data.get("data", []) if r.get("scientific_name")]
            return results, total
        except (HTTPStatusError, RequestError) as e:
            logger.warning("perenual_list_failed", error=str(e))
            raise ExternalSourceError("perenual", str(e)) from e

    def health_check(self) -> bool:
        if not self._api_key:
            return False
        try:
            response = self._client.get("/species-list", params=self._params(q="Rosa", page=1))
            return response.status_code == 200
        except (HTTPStatusError, RequestError):
            return False

    @staticmethod
    def _map_species(data: dict) -> ExternalSpeciesData:
        common_names = data.get("common_name", "")
        if isinstance(common_names, str) and common_names:
            common_names_list = [common_names]
        elif isinstance(common_names, list):
            common_names_list = common_names
        else:
            common_names_list = []

        sunlight = data.get("sunlight", [])
        if isinstance(sunlight, str):
            sunlight = [sunlight]

        return ExternalSpeciesData(
            external_id=str(data.get("id", "")),
            scientific_name=data.get("scientific_name", "") or "",
            common_names=common_names_list,
            genus=_extract_genus(data.get("scientific_name", "")),
            family_name=data.get("family", ""),
            growth_habit=data.get("type", ""),
            hardiness_zones=_parse_hardiness(data.get("hardiness", {})),
            description=data.get("description", "") or "",
            image_url=_safe_image_url(data.get("default_image")),
            sunlight=sunlight,
            watering=data.get("watering", "") or "",
            cycle=data.get("cycle", "") or "",
        )


def _extract_genus(scientific_name: str) -> str:
    parts = scientific_name.strip().split()
    return parts[0] if parts else ""


def _parse_hardiness(hardiness: dict | None) -> list[str]:
    if not hardiness or not isinstance(hardiness, dict):
        return []
    min_zone = str(hardiness.get("min", ""))
    max_zone = str(hardiness.get("max", ""))
    zones = []
    if min_zone:
        zones.append(min_zone)
    if max_zone and max_zone != min_zone:
        zones.append(max_zone)
    return zones


def _safe_image_url(image_data: dict | None) -> str:
    if not image_data or not isinstance(image_data, dict):
        return ""
    return str(image_data.get("regular_url", image_data.get("original_url", "")))
