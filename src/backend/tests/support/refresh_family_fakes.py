"""The #2116 family half of an in-memory ``IRefreshTokenRepository`` (REQ-023 §3.2a).

Mixed into the per-module ``_MemoryRefreshTokenRepository`` doubles, which keep
their sessions in ``self._docs`` (key → :class:`RefreshToken`). It models the
token side only: the account's ``session_generation`` / ``access_token_generation``
live on the user document and are moved by ``ArangoRefreshTokenRepository`` in the
same AQL statement; that half is measured against a real server in
``tests/integration/test_session_family_and_access_cutoff.py``, not here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.models.auth import RefreshToken


class RefreshFamilyMemoryMixin:
    _docs: dict[str, RefreshToken]

    def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        return next((doc for doc in self._docs.values() if doc.token_hash == token_hash), None)

    def claim_rotation(self, key: str, family_key: str, rotated_at: datetime) -> bool:
        doc = self._docs.get(key)
        if doc is None or doc.revoked or doc.rotated_at is not None:
            return False
        self._docs[key] = doc.model_copy(update={"revoked": True, "rotated_at": rotated_at, "family_key": family_key})
        return True

    def set_successor(self, key: str, successor_key: str) -> None:
        doc = self._docs[key]
        self._docs[key] = doc.model_copy(update={"successor_key": successor_key})

    def family_is_live(self, user_key: str, family_key: str) -> bool:
        now = datetime.now(UTC)
        return any(
            doc.user_key == user_key and doc.family_key == family_key and not doc.revoked and doc.expires_at > now
            for doc in self._docs.values()
        )

    def revoke_family(self, user_key: str, family_key: str) -> int:
        revoked = 0
        for key, doc in list(self._docs.items()):
            if doc.user_key == user_key and (doc.family_key == family_key or key == family_key) and not doc.revoked:
                self._docs[key] = doc.model_copy(update={"revoked": True})
                revoked += 1
        return revoked

    # ── test-side helpers ──────────────────────────────────────────────────

    def age_rotations(self, *, seconds: int) -> None:
        """Move every ``rotated_at`` back by ``seconds`` — past the grace window, say."""
        for key, doc in list(self._docs.items()):
            if doc.rotated_at is not None:
                self._docs[key] = doc.model_copy(update={"rotated_at": doc.rotated_at - timedelta(seconds=seconds)})

    def active_count(self) -> int:
        return sum(1 for doc in self._docs.values() if not doc.revoked)
