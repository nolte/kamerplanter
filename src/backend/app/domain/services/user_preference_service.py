import structlog

from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.user_preference import UserPreference

logger = structlog.get_logger()

KNOWN_MODULE_KEYS: frozenset[str] = frozenset(
    {
        "dashboard",
        "plants",
        "locations",
        "settings",
        "onboarding",
        "care",
        "calendar",
        "watering",
        "tasks",
        "nutrition",
        "tanks",
        "substrates",
        "calculators",
        "ipm",
        "harvest",
        "post_harvest",
        "runs",
        "propagation",
        "master_data",
        "companion",
        "sensors",
        "automation",
        "smart_home",
        "ai",
    }
)


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
        mv = updates.get("module_visibility")
        if mv:
            unknown = set(mv) - KNOWN_MODULE_KEYS
            if unknown:
                logger.warning("unknown_module_visibility_keys", keys=sorted(unknown))
        pref = self.get_preferences(user_key)
        data = pref.model_dump()
        data.update(updates)
        updated = UserPreference(**data)
        doc = self._repo.update(pref.key or "", updated)
        return UserPreference(**doc)
