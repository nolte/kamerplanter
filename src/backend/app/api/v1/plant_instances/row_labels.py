"""Per-request memo for the denormalised labels of plant rows (#3032).

A plant list response embeds a species summary, a cultivar summary and the
current phase name per row. Resolving each of them per row turns a 200-row page
into hundreds of database reads, although the rows of one tenant typically share
a handful of species, cultivars and phases. ``PlantRowLabels`` resolves each
distinct key once per request and serves every further row from the memo.

The memo takes the resolver callables instead of a repository, so each router
keeps its own tenant-scoped resolution — in particular the ``readable_species``
rule (#2082): a species key the tenant cannot read resolves to ``None``, and that
``None`` is memoised like any other result. One instance MUST NOT outlive the
request it was created for.
"""

from collections.abc import Callable

from app.api.v1.plant_instances.schemas import CultivarSummary, SpeciesSummary
from app.domain.models.species import Cultivar, Species


def _memoised[T](memo: dict[str, T], key: str, resolve: Callable[[str], T]) -> T:
    """``resolve(key)`` once per ``memo``; every later call for ``key`` is served from it."""
    if key not in memo:
        memo[key] = resolve(key)
    return memo[key]


def _species_summary(species: Species | None) -> SpeciesSummary | None:
    if species is None:
        return None
    return SpeciesSummary(
        scientific_name=species.scientific_name,
        common_names=species.common_names,
        common_names_i18n=species.common_names_i18n,
    )


def _cultivar_summary(cultivar: Cultivar | None) -> CultivarSummary | None:
    return CultivarSummary(name=cultivar.name) if cultivar else None


class PlantRowLabels:
    """Resolve species/cultivar summaries and phase names once per distinct key."""

    def __init__(
        self,
        *,
        resolve_species: Callable[[str], Species | None],
        resolve_cultivar: Callable[[str], Cultivar | None],
        resolve_phase_name: Callable[[str], str] | None = None,
    ) -> None:
        self._summarise_species: Callable[[str], SpeciesSummary | None] = lambda key: _species_summary(
            resolve_species(key)
        )
        self._summarise_cultivar: Callable[[str], CultivarSummary | None] = lambda key: _cultivar_summary(
            resolve_cultivar(key)
        )
        self._resolve_phase_name = resolve_phase_name
        self._species: dict[str, SpeciesSummary | None] = {}
        self._cultivars: dict[str, CultivarSummary | None] = {}
        self._phase_names: dict[str, str] = {}

    def species(self, species_key: str | None) -> SpeciesSummary | None:
        """Return the species summary for ``species_key``; ``None`` if absent or unreadable."""
        if not species_key:
            return None
        return _memoised(self._species, species_key, self._summarise_species)

    def cultivar(self, cultivar_key: str | None) -> CultivarSummary | None:
        """Return the cultivar summary for ``cultivar_key``; ``None`` if absent or unknown."""
        if not cultivar_key:
            return None
        return _memoised(self._cultivars, cultivar_key, self._summarise_cultivar)

    def phase_name(self, phase_key: str | None) -> str:
        """Return the phase name for ``phase_key``; ``""`` if absent or no resolver is configured."""
        if not phase_key or self._resolve_phase_name is None:
            return ""
        return _memoised(self._phase_names, phase_key, self._resolve_phase_name)
