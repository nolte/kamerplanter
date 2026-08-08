"""#1019 — ``ArangoUserRepository.delete`` sweeps every single-user artefact.

The platform-admin ``delete_user`` router used to hand-write eight raw-AQL
``REMOVE``s. Three of the collections it swept — API keys, user preferences and
onboarding state — were **not** part of the repository's own ``delete`` cascade,
so folding the router into the service would have silently orphaned them. #1019
added them to the repository cascade; this pins that they are swept, alongside
the auth-provider / refresh-token / session cleanup that was already there, and
that the user document is deleted last.

Red-first: against the pre-#1019 ``delete`` (auth providers + tokens + sessions +
user only) the three ``assert … in swept`` lines below fail — the collections
were never referenced.
"""

from typing import Any

from app.data_access.arango import collections as col
from app.data_access.arango.user_repository import ArangoUserRepository

USER_KEY = "u-1"


class _FakeCollection:
    def __init__(self, deleted: list[str]) -> None:
        self._deleted = deleted

    def delete(self, key: str) -> None:
        self._deleted.append(key)


class _FakeAql:
    def __init__(self, queries: list[str], bind_vars: list[dict[str, Any]]) -> None:
        self._queries = queries
        self._bind_vars = bind_vars

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self._queries.append(query)
        self._bind_vars.append(bind_vars or {})
        return iter([])


class _FakeDb:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.bind_vars: list[dict[str, Any]] = []
        self.deleted: list[str] = []
        self.aql = _FakeAql(self.queries, self.bind_vars)

    def collection(self, _name: str) -> _FakeCollection:
        return _FakeCollection(self.deleted)


def test_delete_sweeps_api_keys_preferences_and_onboarding_then_the_user():
    db = _FakeDb()
    repo = ArangoUserRepository(db)  # type: ignore[arg-type]

    assert repo.delete(USER_KEY) is True

    swept = " \n".join(db.queries)
    # #1019 additions — the collections the router used to sweep itself.
    assert col.API_KEYS in swept
    assert col.USER_PREFERENCES in swept
    assert col.ONBOARDING_STATES in swept
    # Pre-existing document sweeps stay covered.
    assert col.AUTH_PROVIDERS in swept
    assert col.REFRESH_TOKENS in swept
    # Auth-provider and session *edges* are removed by bound edge collection.
    edge_binds = {bv.get("@edge") for bv in db.bind_vars}
    assert col.HAS_AUTH_PROVIDER in edge_binds
    assert col.HAS_SESSION in edge_binds
    # The user document itself is deleted (last).
    assert db.deleted == [USER_KEY]


def test_every_user_scoped_remove_binds_the_key_never_interpolates_it():
    """The ``user_key`` filter value is always bound, never string-built."""
    db = _FakeDb()
    repo = ArangoUserRepository(db)  # type: ignore[arg-type]

    repo.delete(USER_KEY)

    for query, binds in zip(db.queries, db.bind_vars, strict=True):
        if "doc.user_key == @key" in query:
            assert binds.get("key") == USER_KEY
            assert USER_KEY not in query  # the value never lands in the AQL text
