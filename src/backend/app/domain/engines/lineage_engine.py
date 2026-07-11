"""REQ-017 Lineage engine.

Graph traversal over the ``descended_from`` edge (child -> mother) and the
taxonomy-based graft-compatibility heuristic (genus / family level, §3). The
engine holds a lineage repository (for the tenant-scoped graph traversal) and a
species repository (for genus / family resolution), mirroring the established
domain-engine composition pattern (CompanionPlantingEngine).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.common.enums import GraftCompatibilityLevel
from app.data_access.repositories.propagation_repository import PropagationRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.plant_instance import PlantInstance


@dataclass(frozen=True)
class LineagePath:
    """Single ancestor chain (immediate parent first, root last)."""

    plant_keys: tuple[str, ...]


@dataclass(frozen=True)
class GraftCompatibilityResult:
    """Outcome of a graft-compatibility check (REQ-017 §3)."""

    scion_species_key: str
    rootstock_species_key: str
    compatible: bool
    level: GraftCompatibilityLevel
    same_genus: bool
    same_family: bool
    message: str


class LineageEngine:
    """Genetic-lineage traversal and graft-compatibility rules (REQ-017)."""

    def __init__(self, lineage_repo: PropagationRepository, species_repo: ISpeciesRepository) -> None:
        self._repo = lineage_repo
        self._species_repo = species_repo

    # ── Ancestry / descendants ────────────────────────────────────────────────

    def trace_ancestors(self, plant_key: str, tenant_key: str, max_depth: int = 10) -> list[LineagePath]:
        """Return the plant's ancestor chains via ``descended_from`` (multi-level).

        Traversal is tenant-scoped and cycle-safe (``uniqueVertices: 'path'`` +
        ``max_depth`` cap). Each :class:`LineagePath` is a maximal chain from the
        immediate parent up to a root ancestor.
        """
        paths = self._repo.trace_ancestor_paths(plant_key, tenant_key, max_depth)
        return [LineagePath(plant_keys=tuple(p)) for p in paths]

    def list_ancestors(self, plant_key: str, tenant_key: str, max_depth: int = 10) -> list[PlantInstance]:
        """Flat, de-duplicated ancestor list (nearest first)."""
        return self._repo.list_ancestors(plant_key, tenant_key, max_depth)

    def trace_descendants(self, plant_key: str, tenant_key: str, max_depth: int = 10) -> list[PlantInstance]:
        """Flat, de-duplicated descendant (clone-tree) list."""
        return self._repo.list_descendants(plant_key, tenant_key, max_depth)

    # ── Graft compatibility (taxonomy heuristic, §3) ──────────────────────────

    def is_graft_compatible(self, scion_species_key: str, rootstock_species_key: str) -> bool:
        """Boolean shortcut for :meth:`check_graft_compatibility`."""
        return self.check_graft_compatibility(scion_species_key, rootstock_species_key).compatible

    def check_graft_compatibility(self, scion_species_key: str, rootstock_species_key: str) -> GraftCompatibilityResult:
        """Genus / family taxonomy heuristic (REQ-017 §3 check_graft_compatibility).

        * same genus  -> ``compatible``
        * same family -> ``possibly_compatible`` (rejection risk raised)
        * otherwise   -> ``incompatible``

        Both species must resolve; an unknown key raises ``NotFoundError`` via the
        species repository ``get_or_raise`` contract.
        """
        scion = self._species_repo.get_or_raise(scion_species_key)
        rootstock = self._species_repo.get_or_raise(rootstock_species_key)

        scion_genus = (scion.genus or "").strip().lower()
        rootstock_genus = (rootstock.genus or "").strip().lower()
        same_genus = bool(scion_genus) and scion_genus == rootstock_genus
        same_family = bool(scion.family_key) and scion.family_key == rootstock.family_key

        if same_genus:
            level = GraftCompatibilityLevel.COMPATIBLE
            compatible = True
            message = (
                f"Gleiche Gattung ({scion.genus}) — Veredelung wahrscheinlich kompatibel (taxonomische Heuristik)."
            )
        elif same_family:
            level = GraftCompatibilityLevel.POSSIBLY_COMPATIBLE
            compatible = True
            message = "Gleiche Familie, unterschiedliche Gattung — Veredelung möglich, aber erhöhtes Abstoßungsrisiko."
        else:
            level = GraftCompatibilityLevel.INCOMPATIBLE
            compatible = False
            message = "Unterschiedliche Familien — Veredelung nicht empfohlen."

        return GraftCompatibilityResult(
            scion_species_key=scion_species_key,
            rootstock_species_key=rootstock_species_key,
            compatible=compatible,
            level=level,
            same_genus=same_genus,
            same_family=same_family,
            message=message,
        )
