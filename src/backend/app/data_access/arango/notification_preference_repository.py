"""ArangoDB repository for notification preferences."""

from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.notification_preference_repository import (
    INotificationPreferenceRepository,
)
from app.domain.models.notification import NotificationPreferences

# Collection constant
NOTIFICATION_PREFERENCES = "notification_preferences"


class ArangoNotificationPreferenceRepository(INotificationPreferenceRepository, BaseArangoRepository):
    """ArangoDB-backed notification preference repository.

    Uses deterministic _key = 'notifpref_{user_key}' for upsert semantics.
    """

    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, NOTIFICATION_PREFERENCES)

    @staticmethod
    def _make_key(user_key: str) -> str:
        """Build deterministic document key from user_key."""
        return f"notifpref_{user_key}"

    def get_by_user(self, user_key: str) -> NotificationPreferences | None:
        """Get notification preferences for a user."""
        key = self._make_key(user_key)
        doc = self.collection.get(key)
        if doc is None:
            return None
        return NotificationPreferences(**self._from_doc(doc))

    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences:
        """Create or update notification preferences for a user.

        Uses the deterministic _key to perform an upsert.
        """
        key = self._make_key(preferences.user_key)
        now = datetime.now(UTC).isoformat()

        data = self._to_doc(preferences)
        data["user_key"] = preferences.user_key

        existing = self.collection.get(key)
        if existing is None:
            data["_key"] = key
            data["created_at"] = now
            data["updated_at"] = now
            result = self.collection.insert(data, return_new=True)
            return NotificationPreferences(**self._from_doc(result["new"]))

        data["updated_at"] = now
        result = self.collection.update({"_key": key, **data}, return_new=True)
        return NotificationPreferences(**self._from_doc(result["new"]))
