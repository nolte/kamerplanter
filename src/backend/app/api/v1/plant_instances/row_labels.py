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


class PlantRowLabels:
    """Resolve species/cultivar summaries and phase names once per distinct key."""

    def __init__(
        self,
        *,
        resolve_species: Callable[[str], Species | None],
        resolve_cultivar: Callable[[str], Cultivar | None],
        resolve_phase_name: Callable[[str], str] | None = None,
    ) -> None:
        self._resolve_species = resolve_species
        self._resolve_cultivar = resolve_cultivar
        self._resolve_phase_name = resolve_phase_name
        self._species: dict[str, SpeciesSummary | None] = {}
        self._cultivars: dict[str, CultivarSummary | None] = {}
        self._phase_names: dict[str, str] = {}

    def species(self, species_key: str | None) -> SpeciesSummary | None:
        """Return the species summary for ``species_key``; ``None`` if absent or unreadable."""
        if not species_key:
            return None
        if species_key not in self._species:
            sp = self._resolve_species(species_key)
            self._species[species_key] = (
                SpeciesSummary(
                    scientific_name=sp.scientific_name,
                    common_names=sp.common_names,
                    common_names_i18n=sp.common_names_i18n,
                )
                if sp
                else None
            )
        return self._species[species_key]

    def cultivar(self, cultivar_key: str | None) -> CultivarSummary | None:
        """Return the cultivar summary for ``cultivar_key``; ``None`` if absent or unknown."""
        if not cultivar_key:
            return None
        if cultivar_key not in self._cultivars:
            cv = self._resolve_cultivar(cultivar_key)
            self._cultivars[cultivar_key] = CultivarSummary(name=cv.name) if cv else None
        return self._cultivars[cultivar_key]

    def phase_name(self, phase_key: str | None) -> str:
        """Return the phase name for ``phase_key``; ``""`` if absent or no resolver is configured."""
        if not phase_key or self._resolve_phase_name is None:
            return ""
        if phase_key not in self._phase_names:
            self._phase_names[phase_key] = self._resolve_phase_name(phase_key)
        return self._phase_names[phase_key]
