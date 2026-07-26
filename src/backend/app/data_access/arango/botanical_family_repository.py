from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Species


class ArangoBotanicalFamilyRepository(BaseArangoRepository[BotanicalFamily]):
    _model_cls = BotanicalFamily

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.BOTANICAL_FAMILIES)

    def get_all_families(self, offset: int = 0, limit: int = 50) -> tuple[list[BotanicalFamily], int]:
        return super().get_all(offset, limit)

    def get_by_name(self, name: str) -> BotanicalFamily | None:
        return self.find_one_by_field("name", name)

    def create_family(self, family: BotanicalFamily) -> BotanicalFamily:
        return super().create(family)

    def update_family(self, key: str, family: BotanicalFamily) -> BotanicalFamily:
        return super().update(key, family)

    def delete_family(self, key: str) -> bool:
        return super().delete(key)

    def get_species_by_family(self, family_key: str) -> list[Species]:
        """Return every species assigned to ``family_key``.

        Species are related to their family through the scalar ``family_key``
        field written on every create/import/seed path — the ``belongs_to_family``
        graph edge is only produced by the dedup migration and is absent for the
        vast majority of species. Filtering on the scalar field is therefore the
        authoritative assignment and matches how the frontend groups species by
        family.
        """
        query = f"""
        FOR s IN {col.SPECIES}
          FILTER s.family_key == @family_key
          SORT s.scientific_name ASC
          RETURN s
        """
        bind_vars = {"family_key": family_key}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Species(**self._from_doc(doc)) for doc in cursor]

    def get_species_count_by_family(self, family_key: str) -> int:
        """Count species assigned to a single family via the scalar ``family_key``.

        See :meth:`get_species_by_family` for why the scalar field — not the
        ``belongs_to_family`` edge — is the source of truth. Used by the single
        family endpoints (``GET/POST/PUT /botanical-families[/{key}]``), which
        need exactly one count; the list endpoint uses the bulk
        :meth:`get_species_counts_by_family` to avoid one count query per row.
        """
        query = f"""
        RETURN LENGTH(
          FOR s IN {col.SPECIES}
            FILTER s.family_key == @family_key
            RETURN 1
        )
        """
        bind_vars = {"family_key": family_key}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, 0)

    def get_species_counts_by_family(self) -> dict[str, int]:
        """Return ``{family_key: species_count}`` for all families in one query.

        Aggregates the whole species collection by its scalar ``family_key`` so
        the list endpoint (``GET /botanical-families``) resolves every count in a
        single round-trip instead of one :meth:`get_species_count_by_family` call
        per row. Families with no species are simply absent from the map, so
        callers default a missing key to ``0``.
        """
        query = f"""
        FOR s IN {col.SPECIES}
          FILTER s.family_key != null AND s.family_key != ""
          COLLECT fam = s.family_key WITH COUNT INTO count
          RETURN {{ family_key: fam, count: count }}
        """
        cursor = self._db.aql.execute(query)
        return {row["family_key"]: row["count"] for row in cursor}
