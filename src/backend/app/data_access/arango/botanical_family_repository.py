from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.botanical_family import BotanicalFamily


class ArangoBotanicalFamilyRepository(BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.BOTANICAL_FAMILIES)

    def get_all_families(self, offset: int = 0, limit: int = 50) -> tuple[list[BotanicalFamily], int]:
        docs, total = super().get_all(offset, limit)
        return [BotanicalFamily(**doc) for doc in docs], total

    def get_by_key(self, key: str) -> BotanicalFamily | None:
        doc = super().get_by_key(key)
        return BotanicalFamily(**doc) if doc else None

    def get_by_name(self, name: str) -> BotanicalFamily | None:
        docs = self.find_by_field("name", name)
        return BotanicalFamily(**docs[0]) if docs else None

    def create_family(self, family: BotanicalFamily) -> BotanicalFamily:
        doc = super().create(family)
        return BotanicalFamily(**doc)

    def update_family(self, key: str, family: BotanicalFamily) -> BotanicalFamily:
        doc = super().update(key, family)
        return BotanicalFamily(**doc)

    def delete_family(self, key: str) -> bool:
        return super().delete(key)
