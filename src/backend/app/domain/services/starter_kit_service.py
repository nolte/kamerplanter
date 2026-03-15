from app.common.exceptions import NotFoundError
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.starter_kit import StarterKit


class StarterKitService:
    def __init__(self, db) -> None:
        from app.data_access.arango import collections as col

        self._repo = BaseArangoRepository(db, col.STARTER_KITS)
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

    def create_kit(self, kit: StarterKit) -> StarterKit:
        doc = self._repo.create(kit)
        return StarterKit(**doc)
