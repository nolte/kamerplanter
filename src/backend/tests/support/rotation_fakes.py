"""In-memory doubles for the bed-level crop-rotation check (REQ-053 WP 3.4, #2394).

``FakeRotationHistory`` honours the same contract as ``ArangoRotationHistoryRepository``: every read names the
tenant, a plant or an event of another tenant is not part of the answer, a voided or superseded backfill is gone.
It reads backfills from the :class:`~tests.support.care_event_fakes.FakeCareEventRepo` it is handed, so a test of
the whole path (``backfill`` then ``rotation``) goes through the real care-event service.
"""

from __future__ import annotations

from datetime import date, datetime

from app.domain.interfaces.rotation_history_repository import (
    BackfillRow,
    IRotationHistoryRepository,
    PlantedRow,
)
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Species
from tests.support.care_event_fakes import FakeCareEventRepo


def make_species(key: str, family_key: str | None, *, tenant: str = "", **kwargs) -> Species:
    return Species(
        _key=key, scientific_name=f"Test {key}", genus="Test", family_key=family_key, tenant_key=tenant, **kwargs
    )


def make_family(key: str, *, pause: int | None, **kwargs) -> BotanicalFamily:
    return BotanicalFamily(_key=key, name=f"{key.capitalize()}aceae", rotation_pause_years=pause, **kwargs)


class FakeSpecies:
    def __init__(self, *species: Species) -> None:
        self.by_key = {s.key: s for s in species}
        self.grants: set[tuple[str, str]] = set()

    def get_by_key(self, key):
        return self.by_key.get(key)

    def is_granted_to(self, species_key, tenant_key):
        return (species_key, tenant_key) in self.grants

    def search(self, name=None, family_key=None, *, tenant_key=None):
        """The hybrid-catalogue union of the real read: global rows, the tenant's own and granted ones."""
        return [
            species
            for species in self.by_key.values()
            if (family_key is None or species.family_key == family_key)
            and (
                tenant_key is None or species.tenant_key in ("", tenant_key) or (species.key, tenant_key) in self.grants
            )
        ]


class FakeFamilies:
    def __init__(self, *families: BotanicalFamily) -> None:
        self.by_key = {f.key: f for f in families}

    def get_by_key(self, key):
        return self.by_key.get(key)


class FakeRotationHistory(IRotationHistoryRepository):
    def __init__(self, care_events: FakeCareEventRepo | None = None) -> None:
        #: (tenant, location_key, row)
        self.plants: list[tuple[str, str, PlantedRow]] = []
        self._events = care_events

    def add_plant(
        self,
        location_key: str,
        species_key: str,
        planted_on: date,
        *,
        removed_on: date | None = None,
        plan_role: str = "main_crop",
        tenant: str = "ten_own",
    ) -> None:
        row = PlantedRow(f"pi_{len(self.plants)}", species_key, planted_on, removed_on, plan_role)
        self.plants.append((tenant, location_key, row))

    def list_plantings(self, location_key, *, since, tenant_key):
        if not tenant_key:
            raise ValueError("tenant_key required")
        return [
            row
            for tenant, location, row in self.plants
            if tenant == tenant_key and location == location_key and (row.removed_on is None or row.removed_on >= since)
        ]

    def list_backfills(self, location_key, *, since: datetime, tenant_key):
        if not tenant_key:
            raise ValueError("tenant_key required")
        if self._events is None:
            return []
        rows = [
            BackfillRow(e.key or "", e.performed_at, e.rotation_entry, e.created_by)
            for e in self._events.events.values()
            if e.tenant_key == tenant_key
            and e.location_key == location_key
            and e.category == "planting"
            and e.trigger == "backfill"
            and e.voided_at is None
            and e.superseded_by_key is None
            and e.rotation_entry is not None
            and e.performed_at >= since
        ]
        return sorted(rows, key=lambda r: r.performed_at, reverse=True)


class FakeRotationGraph:
    """The graph reads the bed-level check makes: pest risk, adjacency and the companion edges."""

    def __init__(self) -> None:
        self.pest_risks: dict[str, list[dict]] = {}
        #: family key -> [(successor family key, benefit_score, benefit_reason)], the ``rotation_after`` edges
        self.successors: dict[str, list[tuple[str, float, str]]] = {}
        self.adjacent: dict[str, list[str]] = {}
        self.incompatible: dict[str, list[str]] = {}
        self.compatible: dict[str, dict[str, float]] = {}
        #: ``(from, to)`` -> the curated reason of an ``incompatible_with`` edge
        self.reasons: dict[tuple[str, str], str] = {}
        #: ``(a, b)`` with ``a < b`` -> ``adjacent_to.distance_cm``
        self.distances: dict[tuple[str, str], float] = {}
        #: species the reading tenant may not see (another tenant's private species, #927)
        self.hidden: set[str] = set()
        #: the batched reads, in call order (no read per edge)
        self.calls: list[str] = []
        #: the ``limit`` of every adjacency read, and the species keys of every companion read
        self.adjacency_limits: list[int] = []
        self.relation_species: list[list[str]] = []

    def get_pest_risks(self, family_key):
        return self.pest_risks.get(family_key, [])

    def get_rotation_successors(self, family_key):
        return [
            {"family": {"_key": key}, "wait_years": 1, "benefit_score": score, "benefit_reason": reason}
            for key, score, reason in self.successors.get(family_key, [])
        ]

    def get_adjacent_slots(self, slot_key):
        return [{"slot": {"_key": key}} for key in self.adjacent.get(slot_key, [])]

    def get_incompatible_species(self, species_key, *, tenant_key):
        return [{"species": {"_key": key}} for key in self.incompatible.get(species_key, [])]

    def get_compatible_species(self, species_key, *, tenant_key):
        return [
            {"species": {"_key": key}, "score": score} for key, score in self.compatible.get(species_key, {}).items()
        ]

    # ── The batched reads of the companion overlay (REQ-053 WP 8.15) ──────────────────────────────────────
    #
    # Over the SAME dictionaries as the per-species reads above, so one arranged world answers the engine, the
    # planting dialog and the overlay alike - the equality test compares the paths, not two fixtures.

    def get_slot_adjacency(self, location_key, slot_keys, *, tenant_key, limit):
        """Like the AQL: fold, sort by slot keys, cut at *limit*; ``total`` counts every pair."""
        from app.domain.interfaces.graph_repository import SlotAdjacency, SlotAdjacencyWindow

        assert tenant_key and location_key, "the overlay reads the adjacency anchored on a tenant's bed (#706)"
        self.calls.append("get_slot_adjacency")
        self.adjacency_limits.append(limit)
        keys = set(slot_keys)
        pairs = {
            tuple(sorted((a, b)))
            for a, neighbours in self.adjacent.items()
            for b in neighbours
            if a in keys and b in keys and a != b
        }
        ordered = sorted(pairs)
        return SlotAdjacencyWindow(
            [SlotAdjacency(a, b, self.distances.get((a, b))) for a, b in ordered[:limit]], total=len(ordered)
        )

    def load_companion_relations(self, species_keys, *, tenant_key, limit):
        from app.domain.interfaces.graph_repository import CompanionRelation, CompanionRelations

        assert tenant_key, "the overlay reads companion edges under a tenant (#927)"
        self.calls.append("load_companion_relations")
        self.relation_species.append(sorted(species_keys))
        keys = set(species_keys) - self.hidden
        relations = [
            CompanionRelation(a, b, incompatible=True, reason=self.reasons.get((a, b)))
            for a, others in sorted(self.incompatible.items())
            for b in others
            if a in keys and b in keys
        ] + [
            CompanionRelation(a, b, incompatible=False, score=score)
            for a, others in sorted(self.compatible.items())
            for b, score in others.items()
            if a in keys and b in keys
        ]
        incompatible = [r for r in relations if r.incompatible]
        compatible = [r for r in relations if not r.incompatible]
        return CompanionRelations(
            incompatible[:limit] + compatible[:limit],
            {key: f"Test {key}" for key in sorted(keys)},
            complete=len(incompatible) <= limit and len(compatible) <= limit,
        )
