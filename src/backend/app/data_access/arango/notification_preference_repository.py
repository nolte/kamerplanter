"""ArangoDB repository for notification preferences.

#2113 — the Apprise URLs are sealed here, on the one path every preference write
and read takes: ``upsert`` stores ``channels.apprise.config.urls`` as Fernet
ciphertext under ``urls_encrypted`` (and removes a plaintext ``urls`` the merge
would otherwise keep), and the readers decrypt it back into ``urls`` for the
channel that sends. Rows stored in clear before #2113 are encrypted once by
migration v0083; a read never writes (``GET …/notifications/preferences`` must not
persist), so a row still in clear is served as stored and sealed by its next save.
The domain model never sees the ciphertext; the API masks the plaintext
(``app.domain.engines.apprise_url_secrets``).
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.engines.apprise_url_secrets import APPRISE_CHANNEL, URLS, URLS_ENCRYPTED, open_config, seal_config
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.interfaces.notification_preference_repository import (
    INotificationPreferenceRepository,
)
from app.domain.models.notification import NotificationPreferences

logger = structlog.get_logger()

# Collection constant
NOTIFICATION_PREFERENCES = "notification_preferences"


class ArangoNotificationPreferenceRepository(
    BaseArangoRepository[NotificationPreferences], INotificationPreferenceRepository
):
    """ArangoDB-backed notification preference repository.

    Uses deterministic _key = 'notifpref_{user_key}' for upsert semantics.
    """

    _model_cls = NotificationPreferences

    def __init__(self, db: StandardDatabase, encryption: EncryptionEngine) -> None:
        super().__init__(db, NOTIFICATION_PREFERENCES)
        self._encryption = encryption

    def _opened(self, doc: dict[str, Any]) -> NotificationPreferences:
        """The domain model of a stored document, Apprise URLs decrypted (*doc* is not mutated)."""
        channels = doc.get("channels")
        apprise = channels.get(APPRISE_CHANNEL) if isinstance(channels, dict) else None
        if isinstance(channels, dict) and isinstance(apprise, dict) and isinstance(apprise.get("config"), dict):
            opened = {**apprise, "config": open_config(apprise["config"], self._encryption)}
            doc = {**doc, "channels": {**channels, APPRISE_CHANNEL: opened}}
        return NotificationPreferences(**self._from_doc(dict(doc)))

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
        return self._opened(doc)

    def upsert(self, preferences: NotificationPreferences) -> NotificationPreferences:
        """Create or update notification preferences for a user.

        Uses the deterministic _key to perform an upsert.
        """
        key = self._make_key(preferences.user_key)
        now = datetime.now(UTC).isoformat()

        data = self._to_doc(preferences)
        data["user_key"] = preferences.user_key
        apprise = data.get("channels", {}).get(APPRISE_CHANNEL)
        if apprise is not None:
            apprise["config"] = seal_config(apprise.get("config") or {}, self._encryption)

        existing = self.collection.get(key)
        if existing is None:
            data["_key"] = key
            data["created_at"] = now
            data["updated_at"] = now
            result = self.collection.insert(data, return_new=True)
            return self._opened(result["new"])

        data["updated_at"] = now
        if apprise is not None and URLS_ENCRYPTED in apprise["config"]:
            # The update merges nested objects: a plaintext ``urls`` stored before
            # #2113 would survive beside the ciphertext. ``None`` plus
            # ``keep_none=False`` removes it; ``_to_doc`` dropped every other None.
            apprise["config"][URLS] = None
        result = self.collection.update({"_key": key, **data}, return_new=True, keep_none=False)
        return self._opened(result["new"])

    def remove_subscriptions(self, user_key: str, channel_key: str, endpoints: list[str]) -> int:
        """Drop the subscriptions with these endpoints in one AQL ``UPDATE`` (#1827).

        ``FOR … FILTER doc._key == @key`` finds nothing for a deleted document,
        so nothing is inserted (an ``upsert`` would have recreated it — with
        the rest of the channel config — after an erasure). The new list is
        computed inside the same statement from the stored one, and the update
        merges only ``channels.<key>.config.subscriptions``, so a concurrent
        change elsewhere in the document is not overwritten.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
          LET current = doc.channels[@channel].config.subscriptions || []
          LET kept = (FOR s IN current FILTER s.endpoint NOT IN @gone RETURN s)
          FILTER LENGTH(kept) < LENGTH(current)
          UPDATE doc WITH {
            channels: { [@channel]: { config: { subscriptions: kept } } },
            updated_at: @now
          } IN @@collection
          RETURN LENGTH(current) - LENGTH(kept)
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": NOTIFICATION_PREFERENCES,
                "key": self._make_key(user_key),
                "channel": channel_key,
                "gone": list(endpoints),
                "now": datetime.now(UTC).isoformat(),
            },
        )
        return sum(cursor)

    def list_users_with_digest_enabled(self) -> list[NotificationPreferences]:
        """Return preferences of all users with the email digest opted in.

        Matches documents whose ``channels.email.enabled`` and
        ``channels.email.config.digest`` are both true. Documents without the
        ``digest`` key do not match (digest off by default).
        """
        query = """
        FOR p IN @@collection
          FILTER p.channels.email.enabled == true
          FILTER p.channels.email.config.digest == true
          RETURN p
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": NOTIFICATION_PREFERENCES},
        )
        return [self._opened(doc) for doc in cursor]
