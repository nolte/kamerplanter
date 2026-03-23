import structlog
from httpx import Client, HTTPStatusError, RequestError
from markdownify import markdownify

from app.common.exceptions import ExternalSourceError, RateLimitError
from app.config.settings import settings
from app.domain.interfaces.external_source_adapter import ExternalSourceAdapter
from app.domain.models.enrichment import ExternalSpeciesData, GBIFMatchResult
from app.domain.services.adapter_registry import AdapterRegistry

logger = structlog.get_logger()


@AdapterRegistry.register
class GBIFAdapter(ExternalSourceAdapter):
    source_key = "gbif"
    rate_limit_per_minute = 60

    def __init__(self) -> None:
        self._settings = settings.gbif
        self._client = Client(base_url=self._settings.base_url, timeout=self._settings.http_timeout)

    def match_species(self, scientific_name: str, kingdom: str = "Plantae") -> GBIFMatchResult | None:
        try:
            response = self._client.get(
                "/species/match",
                params={"name": scientific_name, "kingdom": kingdom, "strict": "false", "verbose": "true"},
            )
            if response.status_code == 429:
                raise RateLimitError("gbif", retry_after=60)
            response.raise_for_status()
            data = response.json()

            if data.get("matchType") == "NONE":
                return None

            return GBIFMatchResult(
                usage_key=data["usageKey"],
                scientific_name=data.get("scientificName", ""),
                canonical_name=data.get("canonicalName", data.get("scientificName", "")),
                authorship=data.get("authorship", ""),
                rank=data.get("rank", "SPECIES"),
                taxonomic_status=data.get("status", ""),
                confidence=data.get("confidence", 0),
                match_type=data.get("matchType", ""),
                kingdom=data.get("kingdom", ""),
                family=data.get("family", ""),
                genus=data.get("genus", ""),
                accepted_key=data.get("acceptedUsageKey"),
                accepted_name=data.get("accepted"),
            )
        except RateLimitError:
            raise
        except (HTTPStatusError, RequestError) as e:
            logger.warning("gbif_match_failed", name=scientific_name, error=str(e))
            raise ExternalSourceError("gbif", str(e)) from e

    def resolve_synonyms(self, usage_key: int) -> list[str]:
        try:
            response = self._client.get(f"/species/{usage_key}/synonyms", params={"limit": 100})
            response.raise_for_status()
            data = response.json()
            names: list[str] = []
            seen: set[str] = set()
            for entry in data.get("results", []):
                name = entry.get("canonicalName", "")
                if name and name not in seen:
                    seen.add(name)
                    names.append(name)
            return names
        except (HTTPStatusError, RequestError) as e:
            logger.warning("gbif_synonyms_failed", usage_key=usage_key, error=str(e))
            return []

    def get_vernacular_names(self, usage_key: int, languages: list[str] | None = None) -> list[str]:
        if languages is None:
            languages = self._settings.vernacular_languages
        lang_set = set(languages)
        try:
            response = self._client.get(f"/species/{usage_key}/vernacularNames", params={"limit": 200})
            response.raise_for_status()
            data = response.json()
            names: list[str] = []
            seen: set[str] = set()
            for entry in data.get("results", []):
                lang = entry.get("language", "")
                name = entry.get("vernacularName", "")
                if lang in lang_set and name and name not in seen:
                    seen.add(name)
                    names.append(name)
            return names
        except (HTTPStatusError, RequestError) as e:
            logger.warning("gbif_vernacular_failed", usage_key=usage_key, error=str(e))
            return []

    def get_descriptions(self, usage_key: int) -> tuple[str, str]:
        try:
            response = self._client.get(f"/species/{usage_key}/descriptions", params={"limit": 50})
            response.raise_for_status()
            data = response.json()

            description = ""
            habitat_parts: list[str] = []

            for entry in data.get("results", []):
                desc_type = entry.get("type", "")
                text = entry.get("description", "")
                if not text:
                    continue

                # Convert HTML to markdown if it contains HTML tags
                if "<" in text and ">" in text:
                    text = markdownify(text).strip()

                if desc_type == "" or desc_type is None:
                    if len(text) > len(description):
                        description = text
                elif desc_type == "native range":
                    habitat_parts.append(text)

            # Apply length limits
            max_desc = self._settings.max_description_length
            if len(description) > max_desc:
                description = description[: max_desc - 3] + "..."

            native_habitat = ", ".join(habitat_parts)
            max_habitat = self._settings.max_habitat_length
            if len(native_habitat) > max_habitat:
                native_habitat = native_habitat[: max_habitat - 3] + "..."

            return description, native_habitat
        except (HTTPStatusError, RequestError) as e:
            logger.warning("gbif_descriptions_failed", usage_key=usage_key, error=str(e))
            return "", ""

    def enrich_species(self, scientific_name: str, full_sync: bool = False) -> ExternalSpeciesData | None:
        match = self.match_species(scientific_name)
        if match is None:
            return None

        if not self._is_acceptable_match(match, full_sync):
            logger.info(
                "gbif_match_rejected",
                name=scientific_name,
                match_type=match.match_type,
                confidence=match.confidence,
                full_sync=full_sync,
            )
            return None

        # Synonym handling: redirect to accepted taxon
        usage_key = match.usage_key
        if match.taxonomic_status == "SYNONYM" and match.accepted_key:
            usage_key = match.accepted_key

        synonyms = self.resolve_synonyms(usage_key)
        vernacular_names = self.get_vernacular_names(usage_key)
        description, native_habitat = self.get_descriptions(usage_key)

        return ExternalSpeciesData(
            external_id=str(usage_key),
            scientific_name=match.scientific_name,
            canonical_name=match.canonical_name,
            common_names=vernacular_names,
            genus=match.genus,
            family_name=match.family,
            synonyms=synonyms,
            taxonomic_authority=match.authorship,
            taxonomic_status=match.taxonomic_status,
            description=description,
            native_habitat=native_habitat,
        )

    def _is_acceptable_match(self, match: GBIFMatchResult, full_sync: bool) -> bool:
        if match.match_type in ("HIGHERRANK", "NONE"):
            return False

        if full_sync:
            exact_threshold = self._settings.full_exact_threshold
            fuzzy_threshold = self._settings.full_fuzzy_threshold
        else:
            exact_threshold = self._settings.incremental_exact_threshold
            fuzzy_threshold = self._settings.incremental_fuzzy_threshold

        if match.match_type == "EXACT":
            return match.confidence >= exact_threshold
        if match.match_type == "FUZZY":
            return match.confidence >= fuzzy_threshold

        return False

    def search_species(self, query: str) -> list[ExternalSpeciesData]:
        try:
            response = self._client.get(
                "/species/search",
                params={
                    "q": query,
                    "rank": "SPECIES",
                    "datasetKey": self._settings.backbone_dataset_key,
                    "limit": 20,
                },
            )
            response.raise_for_status()
            data = response.json()
            return [self._map_species(r) for r in data.get("results", []) if r.get("scientificName")]
        except (HTTPStatusError, RequestError) as e:
            logger.warning("gbif_search_failed", query=query, error=str(e))
            raise ExternalSourceError("gbif", str(e)) from e

    def get_species_by_id(self, external_id: str) -> ExternalSpeciesData | None:
        try:
            response = self._client.get(f"/species/{external_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            if not data.get("scientificName"):
                return None
            return self._map_species(data)
        except (HTTPStatusError, RequestError) as e:
            logger.warning("gbif_get_species_failed", external_id=external_id, error=str(e))
            raise ExternalSourceError("gbif", str(e)) from e

    def get_species_list(self, page: int = 1, per_page: int = 30) -> tuple[list[ExternalSpeciesData], int]:
        offset = (page - 1) * per_page
        try:
            response = self._client.get(
                "/species/search",
                params={
                    "limit": per_page,
                    "offset": offset,
                    "rank": "SPECIES",
                    "datasetKey": self._settings.backbone_dataset_key,
                    "status": "ACCEPTED",
                    "highertaxonKey": self._settings.plantae_taxon_key,
                },
            )
            response.raise_for_status()
            data = response.json()
            total = data.get("count", 0)
            results = [self._map_species(r) for r in data.get("results", []) if r.get("scientificName")]
            return results, total
        except (HTTPStatusError, RequestError) as e:
            logger.warning("gbif_list_failed", error=str(e))
            raise ExternalSourceError("gbif", str(e)) from e

    def health_check(self) -> bool:
        try:
            response = self._client.get("/species/match", params={"name": "Plantae", "kingdom": "Plantae"})
            return response.status_code == 200
        except (HTTPStatusError, RequestError):  # fmt: skip
            return False

    @staticmethod
    def _map_species(data: dict) -> ExternalSpeciesData:
        return ExternalSpeciesData(
            external_id=str(data.get("key", data.get("usageKey", ""))),
            scientific_name=data.get("canonicalName", data.get("scientificName", "")),
            canonical_name=data.get("canonicalName", ""),
            common_names=[data["vernacularName"]] if data.get("vernacularName") else [],
            genus=data.get("genus", ""),
            family_name=data.get("family", ""),
            taxonomic_authority=data.get("authorship", ""),
            taxonomic_status=data.get("taxonomicStatus", ""),
            description=data.get("descriptions", [{}])[0].get("description", "")
            if isinstance(data.get("descriptions"), list) and data.get("descriptions")
            else "",
            native_habitat=data.get("habitat", ""),
        )
