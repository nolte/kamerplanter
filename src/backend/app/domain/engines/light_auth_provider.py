"""Light-mode auth provider with optional per-worker E2E isolation.

In light mode every request resolves to a single ``system-user``.  When the
incoming request carries an ``X-E2E-Worker-Id`` header the provider instead
returns a dedicated user keyed by that worker id, auto-creating both the
user and a personal tenant on first sight.

This isolates parallel E2E test workers (pytest-xdist) so that backend
state mutations made by one worker (onboarding state, plant instances,
favorites …) cannot pollute another worker's tests.

The mechanism is a no-op in production because no client sends the
``X-E2E-Worker-Id`` header.
"""

from __future__ import annotations

import re
import threading
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.domain.interfaces.auth_provider import IAuthProvider
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User

if TYPE_CHECKING:
    from arango.database import StandardDatabase

_SYSTEM_USER_KEY = "system-user"
_SYSTEM_TENANT_KEY = "system-tenant"

# Restrict worker ids to a small ASCII charset to keep them safe as
# ArangoDB ``_key`` values and as URL slug fragments.
_WORKER_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")


class LightAuthProvider(IAuthProvider):
    def __init__(
        self,
        user_repo: IUserRepository,
        db: StandardDatabase | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._db = db
        self._cached_user: User | None = None
        self._cached_worker_users: dict[str, User] = {}
        self._lock = threading.Lock()

    # ── Public API ──────────────────────────────────────────────────────

    def resolve_user(
        self,
        authorization: str | None,
        worker_id: str | None = None,
    ) -> User:
        del authorization
        if worker_id and _WORKER_ID_RE.match(worker_id):
            return self._get_or_create_worker_user(worker_id)
        return self._get_system_user()

    def resolve_user_optional(
        self,
        authorization: str | None,
        worker_id: str | None = None,
    ) -> User | None:
        return self.resolve_user(authorization, worker_id)

    def is_authentication_required(self) -> bool:
        return False

    # ── System user (default) ───────────────────────────────────────────

    def _get_system_user(self) -> User:
        if self._cached_user is not None:
            return self._cached_user
        user = self._user_repo.get_by_key(_SYSTEM_USER_KEY)
        if user is None:
            msg = "System user not found. Run seed_light_mode to create the system user."
            raise RuntimeError(msg)
        self._cached_user = user
        return user

    # ── Per-worker users (E2E isolation) ────────────────────────────────

    def _get_or_create_worker_user(self, worker_id: str) -> User:
        # Fast path: cached
        cached = self._cached_worker_users.get(worker_id)
        if cached is not None:
            return cached

        with self._lock:
            cached = self._cached_worker_users.get(worker_id)
            if cached is not None:
                return cached

            user_key = f"system-user-{worker_id}"
            user = self._user_repo.get_by_key(user_key)
            if user is None:
                user = self._provision_worker_user(worker_id)
            self._cached_worker_users[worker_id] = user
            return user

    def _provision_worker_user(self, worker_id: str) -> User:
        """Create user + personal tenant + admin membership for a worker.

        Uses direct collection inserts (mirroring ``seed_light_mode``) so
        that ``_key`` values are deterministic and predictable from the
        worker id.
        """
        if self._db is None:
            msg = (
                "LightAuthProvider was constructed without a DB connection; "
                "per-worker user provisioning is not available."
            )
            raise RuntimeError(msg)

        user_key = f"system-user-{worker_id}"
        tenant_key = f"system-tenant-{worker_id}"
        tenant_slug = f"mein-garten-{worker_id}"
        membership_key = f"{user_key}--{tenant_key}"
        now = datetime.now(UTC).isoformat()

        users = self._db.collection(col.USERS)
        tenants = self._db.collection(col.TENANTS)
        memberships = self._db.collection(col.MEMBERSHIPS)

        if not users.has(user_key):
            users.insert(
                {
                    "_key": user_key,
                    "email": f"{user_key}@kamerplanter.example",
                    "display_name": f"E2E Worker {worker_id}",
                    "password_hash": None,
                    "email_verified": True,
                    "is_active": True,
                    "failed_login_attempts": 0,
                    "locale": "de",
                    "timezone": "Europe/Berlin",
                    "created_at": now,
                    "updated_at": now,
                }
            )

        if not tenants.has(tenant_key):
            tenants.insert(
                {
                    "_key": tenant_key,
                    "name": f"Mein Garten ({worker_id})",
                    "slug": tenant_slug,
                    "tenant_type": "personal",
                    "owner_user_key": user_key,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
            )

        if not memberships.has(membership_key):
            memberships.insert(
                {
                    "_key": membership_key,
                    "user_key": user_key,
                    "tenant_key": tenant_key,
                    "role": "admin",
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
            )

        user = self._user_repo.get_by_key(user_key)
        if user is None:
            msg = f"Failed to provision worker user {user_key}"
            raise RuntimeError(msg)
        return user
