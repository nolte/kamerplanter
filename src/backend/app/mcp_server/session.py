"""REQ-033 §4.3a — MCP Streamable-HTTP session handling.

The Streamable-HTTP transport lets a server hand the client an ``Mcp-Session-Id``
on ``initialize``; the client then echoes it on every subsequent request, and the
server may expire it (answering HTTP 404, at which point the client re-runs
``initialize``). A ``DELETE`` on the MCP endpoint terminates it explicitly.

**A session is not an authentication mechanism.** Authorisation hangs entirely on
the API key (§4.3): a valid session with no key is rejected, and a valid key with
no session still works. The session only carries protocol continuity — which is
why this store degrades *open* on a Valkey/Redis outage rather than closed, the
opposite of :class:`app.mcp_server.rate_limit.McpRateLimiter`. Failing closed here
would log every client out on a cache blip while protecting nothing, since the
key check has already happened by then.

Sessions are bound to the account that created them, so a leaked session id
cannot be replayed by a different key.
"""

from __future__ import annotations

import secrets

import structlog

logger = structlog.get_logger(__name__)

#: Session lifetime. Long enough for a working day of LLM-client usage, short
#: enough that abandoned sessions do not accumulate in the store.
_TTL_SECONDS = 12 * 60 * 60

_KEY_PREFIX = "mcp_session:"


class McpSessionStore:
    """Redis-backed store for Streamable-HTTP session ids."""

    def __init__(self, redis_client) -> None:  # noqa: ANN001 - redis client is duck-typed
        self._redis = redis_client

    def create(self, *, account_key: str) -> str | None:
        """Mint a session id for ``account_key``; ``None`` when unavailable.

        Returning ``None`` puts the transport into the stateless mode the MCP
        spec explicitly permits — the server simply omits the ``Mcp-Session-Id``
        header and the client proceeds without one.
        """

        # Visible-ASCII only, per the transport's session-id constraints.
        session_id = secrets.token_urlsafe(32)
        try:
            self._redis.setex(f"{_KEY_PREFIX}{session_id}", _TTL_SECONDS, account_key)
        except Exception as exc:  # noqa: BLE001 - degrade to stateless, see module docstring
            logger.warning("mcp_session_store_unavailable", op="create", error=str(exc))
            return None
        return session_id

    def is_valid(self, session_id: str, *, account_key: str) -> bool:
        """Whether ``session_id`` exists and belongs to ``account_key``.

        On a store outage this returns ``True``: the session is protocol
        bookkeeping, and the caller has already proven possession of a valid API
        key, so refusing here would break working clients without denying an
        attacker anything.
        """

        try:
            owner = self._redis.get(f"{_KEY_PREFIX}{session_id}")
        except Exception as exc:  # noqa: BLE001 - degrade open, see module docstring
            logger.warning("mcp_session_store_unavailable", op="get", error=str(exc))
            return True
        if owner is None:
            return False
        # Bind the session to its creator: a leaked id is useless under another key.
        return owner == account_key

    def terminate(self, session_id: str) -> None:
        """Drop ``session_id`` (client sent DELETE). Missing ids are a no-op."""

        try:
            self._redis.delete(f"{_KEY_PREFIX}{session_id}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("mcp_session_store_unavailable", op="delete", error=str(exc))
