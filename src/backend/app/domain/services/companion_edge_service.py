"""Global companion edges (REQ-028) — written by a platform admin, only between global species (MT-054, #2144).

A ``compatible_with`` / ``incompatible_with`` edge is reference data every tenant
reads. One ending at a tenant-owned species showed that species to all tenants
reading the global anchor. The readers filter the far end since #2144; this
service refuses the shape at the write. The routes are ``require_platform_admin``.
"""

from __future__ import annotations

from app.common.exceptions import ValidationError
from app.common.types import SpeciesKey
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.species_repository import ISpeciesRepository


class CompanionEdgeService:
    """Write the global companion graph."""

    def __init__(self, species_repo: ISpeciesRepository, graph_repo: IGraphRepository) -> None:
        self._species = species_repo
        self._graph = graph_repo

    def set_compatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, score: float) -> None:
        self._require_global_pair(from_key, to_key)
        self._graph.set_compatibility(from_key, to_key, score)

    def set_incompatibility(self, from_key: SpeciesKey, to_key: SpeciesKey, reason: str) -> None:
        self._require_global_pair(from_key, to_key)
        self._graph.set_incompatibility(from_key, to_key, reason)

    def _require_global_pair(self, from_key: SpeciesKey, to_key: SpeciesKey) -> None:
        """Both ends must be global species; an unknown key is 404 (``NotFoundError``)."""
        for key in (from_key, to_key):
            if self._species.get_or_raise(key).tenant_key:
                raise ValidationError(
                    "A companion edge joins two global species; a tenant's own species cannot carry one."
                )
