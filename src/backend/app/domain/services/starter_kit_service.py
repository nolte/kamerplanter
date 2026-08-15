from app.common.exceptions import NotFoundError
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.starter_kit import StarterKit


class StarterKitService:
    def __init__(self, db) -> None:
        from app.data_access.arango import collections as col

        # Service-embedded dict view: methods below wrap the raw dict into
        # StarterKit themselves, so opt into raw mode (FR-002 A3).
        self._repo = BaseArangoRepository(db, col.STARTER_KITS, raw=True)
        self._db = db

    def list_kits(self, difficulty: str | None = None) -> list[StarterKit]:
        if difficulty:
            docs = self._repo.find_by_field("difficulty", difficulty)
        else:
            docs, _ = self._repo.get_all(offset=0, limit=100)
        kits = [StarterKit(**doc) for doc in docs]
        kits.sort(key=lambda k: (k.difficulty.value, k.sort_order))
        return kits

    def get_kit_by_id(self, kit_id: str) -> StarterKit:
        docs = self._repo.find_by_field("kit_id", kit_id)
        if not docs:
            raise NotFoundError("StarterKit", kit_id)
        return StarterKit(**docs[0])

    def list_kits_for_tenant(self, tenant_key: str, difficulty: str | None = None) -> list[StarterKit]:
        """List kits accessible to a tenant. Graceful: returns all kits if tenant_has_access doesn't exist."""
        accessible_species = self._get_accessible_species_keys(tenant_key)
        all_kits = self.list_kits(difficulty)

        if accessible_species is None:
            # The collection is genuinely absent (a volume predating #1092). Showing
            # everything is the pre-grant behaviour and stays correct there: with no
            # grant mechanism, kit visibility was never restricted.
            #
            # What is NOT this branch any more: an *empty* grant set. That used to
            # land here too and meant "no grants yet -> show everything", which is
            # the wrong direction the moment grants are real — a missing store must
            # never reveal more than a populated one.
            return all_kits

        # Filter kits: show if at least one species is accessible
        return [
            kit for kit in all_kits if not kit.species_keys or any(sk in accessible_species for sk in kit.species_keys)
        ]

    def _get_accessible_species_keys(self, tenant_key: str) -> set[str] | None:
        """Get species keys accessible to a tenant. Returns None if collection doesn't exist."""
        try:
            if not self._db.has_collection("tenant_has_access"):
                return None
            cursor = self._db.aql.execute(
                """
                FOR edge IN tenant_has_access
                    FILTER edge._from == CONCAT("tenants/", @tenant_key)
                    FILTER STARTS_WITH(edge._to, "species/")
                    RETURN PARSE_IDENTIFIER(edge._to).key
                """,
                bind_vars={"tenant_key": tenant_key},
            )
            # An empty result is an answer: this tenant has been granted nothing.
            # Returning None here (the pre-#1092 behaviour) turned "no grants" into
            # "all kits", i.e. the absence of a permission granted it.
            return set(cursor)
        except Exception:
            return None

    def get_kit_detail_for_tenant(self, kit_id: str, tenant_key: str) -> dict:
        """Get a single kit with per-species availability flags for a tenant."""
        kit = self.get_kit_by_id(kit_id)
        accessible_species = self._get_accessible_species_keys(tenant_key)
        availability = []
        for sk in kit.species_keys:
            available = accessible_species is None or sk in accessible_species
            availability.append({"species_key": sk, "available": available})
        return {
            "kit": kit,
            "species_availability": availability,
        }

    def create_kit(self, kit: StarterKit) -> StarterKit:
        doc = self._repo.create(kit)
        return StarterKit(**doc)
