from typing import Any

from arango.database import StandardDatabase

from app.common.types import CultivarKey, FamilyKey, SpeciesKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.query_builder import AQLBuilder
from app.domain.calculators.scientific_name import normalize_scientific_name
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.species import Cultivar, Species


class ArangoSpeciesRepository(BaseArangoRepository[Species], ISpeciesRepository):
    _model_cls = Species

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.SPECIES)
        self._cultivars = BaseArangoRepository[Cultivar](db, col.CULTIVARS, Cultivar)

    def get_all(self, offset: int = 0, limit: int = 50) -> tuple[list[Species], int]:
        return super().get_all(offset, limit)

    def get_by_scientific_name(self, name: str) -> Species | None:
        return self.find_one_by_field("scientific_name", name)

    def get_by_normalized_scientific_name(self, name: str) -> Species | None:
        """Look up a species by the canonical dedup key (REQ-048 Stufe 1).

        The incoming ``name`` is run through the same
        :func:`normalize_scientific_name` utility that fills
        ``scientific_name_normalized`` on write, so a hybrid-marker/casing/
        whitespace variant (``Fragaria × ananassa``) resolves to the stored
        record (``Fragaria x ananassa``). This stays a fast indexed equality
        lookup — the persistent index on ``scientific_name_normalized``
        (``ensure_collections``) backs it, so it never degrades to a scan.
        """
        return self.find_one_by_field("scientific_name_normalized", normalize_scientific_name(name))

    def upsert_by_normalized_scientific_name(self, species: Species) -> Species:
        """Insert ``species`` or return the existing row with the same dedup key.

        A single atomic AQL ``UPSERT`` on ``scientific_name_normalized`` collapses
        the check-then-insert into one server round-trip (REQ-048 R5, SEC-003):
        on a match the existing document is returned unchanged (``UPDATE {}``),
        otherwise the new species is inserted. Behaviour is identical to the prior
        lookup-then-create, but the window between check and insert is closed
        server-side. The remaining TOCTOU-race guarantee against two simultaneous
        inserts of the same normalized key is provided by the DB-level *unique*
        index on ``scientific_name_normalized`` — promoted from the non-unique
        bootstrap index by migration v0025 once v0010 has de-duplicated every
        volume (Issue #624). All three create paths (service, import, seed) route
        through this UPSERT so no path bypasses the dedup.
        """
        doc = self._to_doc(species)
        now = self._now()
        doc["created_at"] = now
        doc["updated_at"] = now
        query = f"""
        UPSERT {{ scientific_name_normalized: @norm }}
        INSERT @doc
        UPDATE {{}} IN {col.SPECIES}
        RETURN NEW
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"norm": species.scientific_name_normalized, "doc": doc},
        )
        return Species(**self._from_doc(next(cursor)))

    def set_representative_image(
        self,
        key: SpeciesKey,
        *,
        url: str | None,
        attribution: str | None,
        license: str | None,  # noqa: A002 — matches the model field name
    ) -> None:
        """Partial update of only the representative-image fields (REQ-029-A §4).

        Used by the acquisition pipeline so it never clobbers other species data.
        """
        self.collection.update(
            {
                "_key": key,
                "representative_image_url": url,
                "representative_image_attribution": attribution,
                "representative_image_license": license,
            }
        )

    def search(self, name: str | None = None, family_key: FamilyKey | None = None) -> list[Species]:
        builder = AQLBuilder(col.SPECIES)
        if name:
            builder.filter("scientific_name", "LIKE", f"%{name}%")
        query, bind_vars = builder.build_list()
        # If family_key filter needed, use graph traversal
        if family_key and not name:
            query = """
            FOR v, e IN 1..1 OUTBOUND @family_id GRAPH 'kamerplanter_graph'
              OPTIONS {edgeCollections: ['belongs_to_family']}
              RETURN v
            """
            bind_vars = {"family_id": f"{col.BOTANICAL_FAMILIES}/{family_key}"}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Species(**self._from_doc(doc)) for doc in cursor]

    def get_cultivars(self, species_key: SpeciesKey) -> list[Cultivar]:
        return self._cultivars.find_by_field("species_key", species_key)

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        created = self._cultivars.create(cultivar)
        species_id = f"{col.SPECIES}/{cultivar.species_key}"
        cultivar_id = f"{col.CULTIVARS}/{created.key}"
        self.create_edge(col.HAS_CULTIVAR, species_id, cultivar_id)
        return created

    def get_cultivar_by_key(self, key: CultivarKey) -> Cultivar | None:
        return self._cultivars.get_by_key(key)

    def get_cultivar_or_raise(self, key: CultivarKey) -> Cultivar:
        return self._cultivars.get_or_raise(key)

    def update_cultivar(self, key: CultivarKey, cultivar: Cultivar) -> Cultivar:
        return self._cultivars.update(key, cultivar)

    def delete_cultivar(self, key: CultivarKey) -> bool:
        return self._cultivars.delete(key)

    def update_field(self, key: SpeciesKey, field: str, value: Any) -> None:
        self.collection.update({"_key": key, field: value, "updated_at": self._now()})
