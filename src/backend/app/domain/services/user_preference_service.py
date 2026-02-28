from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.user_preference import UserPreference


class UserPreferenceService:
    def __init__(self, db) -> None:
        from app.data_access.arango import collections as col
        self._repo = BaseArangoRepository(db, col.USER_PREFERENCES)

    def get_preferences(self, user_key: str) -> UserPreference:
        docs = self._repo.find_by_field("user_key", user_key)
        if docs:
            return UserPreference(**docs[0])
        # Auto-create defaults
        pref = UserPreference(user_key=user_key)
        doc = self._repo.create(pref)
        return UserPreference(**doc)

    def update_preferences(self, user_key: str, updates: dict) -> UserPreference:
        pref = self.get_preferences(user_key)
        data = pref.model_dump()
        data.update(updates)
        updated = UserPreference(**data)
        doc = self._repo.update(pref.key or "", updated)
        return UserPreference(**doc)
