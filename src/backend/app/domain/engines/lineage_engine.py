"""REQ-017 Lineage engine scaffold.

Pure-logic graph traversal over `descended_from` edges (clones,
crosses, grafts, divisions). Concrete graft-compatibility checks at
genus/family level land with the implementation PR.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LineagePath:
    """Single ancestor->descendant chain."""

    plant_keys: tuple[str, ...]


class LineageEngine:
    """Scaffold engine — pins the lineage / graft API for REQ-017."""

    def trace_ancestors(self, plant_key: str, max_depth: int = 10) -> list[LineagePath]:
        raise NotImplementedError("REQ-017 LineageEngine.trace_ancestors — pending follow-up.")

    def is_graft_compatible(self, scion_species_key: str, rootstock_species_key: str) -> bool:
        raise NotImplementedError("REQ-017 LineageEngine.is_graft_compatible — pending follow-up.")
