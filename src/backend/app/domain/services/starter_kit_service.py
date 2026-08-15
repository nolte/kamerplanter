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
        """List the starter kits a tenant can actually use.

        A kit is offered when the tenant can **see** at least one of its species.
        Visibility is the hybrid-catalogue union the rest of the system uses —
        the global seed catalogue (``tenant_key == ""``) plus the tenant's own
        rows plus anything explicitly granted (#1092) — not the grants alone.

        That distinction is the #1178 regression, and it is worth spelling out
        because the wrong version looked stricter and therefore safer:

        Before #1092 this asked ``tenant_has_access`` for the tenant's granted
        species. The collection did not exist, the lookup returned ``None``, and
        the method showed every kit. #1092 *created* the collection — and from
        that moment the lookup returned an **empty set** for every tenant, because
        nobody has been granted anything. The filter then kept only kits with no
        species at all. Every seeded kit names species, so the onboarding wizard
        showed **zero cards to everyone**, and the e2e-smoke lane went from seven
        consecutive greens to failing on the merge commit itself.

        The mistake was not the empty-set handling — "no grants" really is an
        answer, and an absent store must never reveal more than a populated one.
        The mistake was treating a *grant* as the only source of visibility. A
        grant is **additive**: it opens a row the tenant could not otherwise see.
        Every starter-kit species is global seed data, visible to everyone, with
        no grant involved.
        """
        visible_species = self._visible_species_keys(tenant_key)
        all_kits = self.list_kits(difficulty)

        if visible_species is None:
            # The species collection is unreachable. Degrading to "show everything"
            # is deliberate and is *not* the failure above: a starter kit names
            # nothing tenant-private — it is a seed-data suggestion of what to
            # plant — so the fail-open direction costs no isolation. Failing closed
            # here would leave a new user staring at an empty wizard because of an
            # infrastructure hiccup.
            return all_kits

        return [
            kit for kit in all_kits if not kit.species_keys or any(sk in visible_species for sk in kit.species_keys)
        ]

    def _visible_species_keys(self, tenant_key: str) -> set[str] | None:
        """Species keys this tenant can see: global ∪ own ∪ granted.

        One query rather than a lookup per kit, and deliberately the *same* three
        arms the species reads use — a fourth notion of "visible" is how the two
        would drift into disagreeing about which rows a tenant has.

        Returns ``None`` only when the species collection itself is unreachable,
        which the caller degrades on. An empty *set* is a real answer and is
        treated as one.
        """
        try:
            if not self._db.has_collection("species"):
                return None
            cursor = self._db.aql.execute(
                """
                FOR doc IN species
                    FILTER doc.tenant_key == @tenant_key
                        OR doc.tenant_key == ""
                        OR doc.tenant_key == null
                        OR LENGTH(
                            FOR edge IN tenant_has_access
                                FILTER edge._from == CONCAT("tenants/", @tenant_key)
                                FILTER edge._to == doc._id
                                LIMIT 1
                                RETURN 1
                        ) > 0
                    RETURN doc._key
                """,
                bind_vars={"tenant_key": tenant_key},
            )
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
