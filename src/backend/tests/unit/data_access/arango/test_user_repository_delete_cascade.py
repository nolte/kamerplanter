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

Since #1664 ``delete`` runs the ``account_cascade`` slice through the shared
``ArangoErasureExecutor`` instead of its own walk, so the double models the
executor's driver surface (``has_collection``, one stream transaction).
"""

from typing import Any

from app.data_access.arango import collections as col
from app.data_access.arango.user_repository import ArangoUserRepository

USER_KEY = "u-1"


class _FakeAql:
    def __init__(self, queries: list[str], bind_vars: list[dict[str, Any]]) -> None:
        self._queries = queries
        self._bind_vars = bind_vars

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self._queries.append(query)
        self._bind_vars.append(bind_vars or {})
        # Every executor write is a counting ``COLLECT WITH COUNT``; one row each.
        return iter([1])


class _FakeTransaction:
    def __init__(self, aql: _FakeAql) -> None:
        self.aql = aql
        self.committed = False

    def commit_transaction(self) -> None:
        self.committed = True

    def abort_transaction(self) -> None:  # pragma: no cover - only on failure
        pass


class _FakeDb:
    """The driver surface ``ArangoErasureExecutor`` uses (#1664).

    Since #1664 ``delete`` runs through the shared executor, which writes inside
    one stream transaction; the fake records every AQL write made through it.
    """

    def __init__(self) -> None:
        self.queries: list[str] = []
        self.bind_vars: list[dict[str, Any]] = []
        self.aql = _FakeAql(self.queries, self.bind_vars)
        self.transactions: list[_FakeTransaction] = []

    def has_collection(self, _name: str) -> bool:
        return True

    def begin_transaction(self, write: list[str], allow_implicit: bool) -> _FakeTransaction:
        transaction = _FakeTransaction(self.aql)
        self.transactions.append(transaction)
        return transaction

    @property
    def swept(self) -> list[str]:
        return [bv.get("@collection") for bv in self.bind_vars]


def test_delete_sweeps_api_keys_preferences_and_onboarding_then_the_user():
    db = _FakeDb()
    repo = ArangoUserRepository(db)  # type: ignore[arg-type]

    assert repo.delete(USER_KEY) is True

    swept = db.swept
    # #1019 additions — the collections the router used to sweep itself.
    assert col.API_KEYS in swept
    assert col.USER_PREFERENCES in swept
    assert col.ONBOARDING_STATES in swept
    # Pre-existing document sweeps stay covered.
    assert col.AUTH_PROVIDERS in swept
    assert col.REFRESH_TOKENS in swept
    # Auth-provider and session *edges* are removed by bound edge collection.
    assert col.HAS_AUTH_PROVIDER in swept
    assert col.HAS_SESSION in swept
    # #1663 — ``api_key_repository.create`` writes ``users -> api_keys`` beside
    # every key; the cascade removed the documents and left these edges behind.
    assert col.HAS_API_KEY in swept
    # The user document itself is deleted (last), inside one committed transaction.
    assert swept[-1] == col.USERS
    assert [t.committed for t in db.transactions] == [True]


def test_delete_stays_the_narrow_cascade():
    """#1664 — the unverified-account cleanup keeps its narrow slice.

    ``delete`` runs only the ``account_cascade`` slice: no memberships, no
    anonymisation, no audit hashing (which would need a tombstone salt this path
    does not have). The full erasure is ``PrivacyService.erase_account``.
    """
    db = _FakeDb()
    ArangoUserRepository(db).delete(USER_KEY)  # type: ignore[arg-type]

    assert col.MEMBERSHIPS not in db.swept
    assert not any("patch" in bv for bv in db.bind_vars)


def test_every_user_scoped_remove_binds_the_key_never_interpolates_it():
    """The ``user_key`` filter value is always bound, never string-built."""
    db = _FakeDb()
    repo = ArangoUserRepository(db)  # type: ignore[arg-type]

    repo.delete(USER_KEY)

    assert db.queries
    for query, binds in zip(db.queries, db.bind_vars, strict=True):
        assert USER_KEY not in query  # the value never lands in the AQL text
        assert binds.get("value") in (USER_KEY, f"{col.USERS}/{USER_KEY}")


def test_the_cascade_attribution_still_covers_every_account_owned_artefact():
    """#1622 — the inventory, not the method, decides what the cascade removes.

    Deliberately asserted on the *engine*, not on the swept queries. A test that
    compared the swept set against ``steps_for("account_cascade")`` would be a
    tautology: the method reads that very slice, so moving an entry out of the
    slice moves it out of both sides at once and the assertion never fails.
    Measured — re-attributing ``api_keys`` to ``retention_worker`` (then the
    "declared, not yet executed" slice) left such a comparison green while the
    collection stopped being swept.

    What is worth pinning is therefore the inventory content: the seven
    account-owned artefacts #1019 established, plus the user document last.
    Re-attributing any of them to ``account_erasure`` (#1645) would keep it in
    the full account erasure but silently drop it from the unverified-account
    cleanup, which runs only this slice — and goes red here.
    """
    from app.domain.engines.erasure_engine import ErasureEngine

    steps = ErasureEngine.steps_for("account_cascade")
    assert {s.collection for s in steps} == {
        col.HAS_AUTH_PROVIDER,
        col.HAS_SESSION,
        col.HAS_API_KEY,
        col.AUTH_PROVIDERS,
        col.REFRESH_TOKENS,
        col.API_KEYS,
        col.USER_PREFERENCES,
        col.ONBOARDING_STATES,
        col.USERS,
    }
    assert steps[-1].collection == col.USERS
    assert steps[-1].kind == "user"
