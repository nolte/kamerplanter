"""#1556 — the two token lookups ``AuthService`` used to hand-write as raw AQL.

``AuthService.verify_email`` and ``reset_password`` reached through
``IUserRepository`` into its private ``python-arango`` handle
(``self._user_repo._db  # type: ignore[attr-defined]``) and executed AQL inline,
skipping the Data Access layer NFR-001 puts between them and persistence. The
lookups now live here.

**What this pins, and what it deliberately does not.** The conversion is
``User(**self._from_doc(doc))`` — byte-for-byte what the service spelled out by
hand as ``{**doc, "_key": doc.get("_key", doc.get("_id", "").split("/")[-1])}``.
So #1556's third bullet ("a document the repository would refuse is accepted
here") does not reproduce: both paths construct through the same Pydantic model.
This move is a layering repair, not a validation repair, and the tests say so
rather than claiming a fix that was never there.

**The empty-token case is the one real behaviour change** and it is a
narrowing, not a widening: an AQL ``FILTER doc.password_reset_token == null``
matches every user that holds no token, so a ``None`` reaching the old inline
query would have handed back an arbitrary account as if it had presented a
credential. The type says ``str``, which is not an enforcement.
"""

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.user_repository import ArangoUserRepository
from app.domain.interfaces.user_repository import IUserRepository

VERIFY_TOKEN = "verify-me"  # noqa: S105 — a fixture value, not a credential
RESET_TOKEN = "reset-me"  # noqa: S105 — a fixture value, not a credential


class _FakeAql:
    """Returns ``rows`` for every query and records what it was asked."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.queries: list[str] = []
        self.bind_vars: list[dict[str, Any]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.queries.append(query)
        self.bind_vars.append(bind_vars or {})
        return iter(list(self._rows))


class _FakeDb:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.aql = _FakeAql(rows or [])


def _doc(**overrides: Any) -> dict[str, Any]:
    """A stored user document, shaped the way ArangoDB hands one back.

    Carries ``_id`` and no ``_key`` on purpose: that is the shape the ``_key``
    normalisation in ``_from_doc`` exists for, and a fixture that pre-supplies
    ``_key`` would certify nothing about it (the #1155 ``_FakeTenantRepo``
    class — a double that accepts a shape the real path never produces).
    """
    doc = {
        "_id": "users/u-1",
        "email": "someone@example.com",
        "display_name": "Someone",
        "password_hash": "x",
    }
    doc.update(overrides)
    return doc


def _repo(rows: list[dict[str, Any]] | None = None) -> tuple[ArangoUserRepository, _FakeDb]:
    db = _FakeDb(rows)
    return ArangoUserRepository(db), db  # type: ignore[arg-type]


class TestTheSeamExists:
    """The interface is the seam, so the interface has to declare it."""

    @pytest.mark.parametrize("method", ["get_by_email_verification_token", "get_by_password_reset_token"])
    def test_the_interface_declares_the_lookup(self, method: str) -> None:
        """A ``MagicMock`` answers any attribute, so the *interface* is what pins this.

        Without this assertion the service test below would pass against a
        repository that never grew the method — the vacuum the issue names.
        """
        assert method in IUserRepository.__abstractmethods__

    def test_the_arango_repository_satisfies_the_interface(self) -> None:
        """Concrete, not abstract: every abstract method has an implementation."""
        assert not getattr(ArangoUserRepository, "__abstractmethods__", frozenset())
        assert issubclass(ArangoUserRepository, IUserRepository)


class TestTheLookups:
    def test_the_verification_lookup_filters_on_its_own_attribute(self) -> None:
        repo, db = _repo([_doc(email_verification_token=VERIFY_TOKEN)])

        user = repo.get_by_email_verification_token(VERIFY_TOKEN)

        assert user is not None
        assert user.email == "someone@example.com"
        assert "doc.email_verification_token == @token" in db.aql.queries[0]
        assert db.aql.bind_vars[0] == {"@collection": col.USERS, "token": VERIFY_TOKEN}

    def test_the_reset_lookup_filters_on_its_own_attribute(self) -> None:
        repo, db = _repo([_doc(password_reset_token=RESET_TOKEN)])

        user = repo.get_by_password_reset_token(RESET_TOKEN)

        assert user is not None
        assert "doc.password_reset_token == @token" in db.aql.queries[0]
        assert db.aql.bind_vars[0] == {"@collection": col.USERS, "token": RESET_TOKEN}

    def test_the_token_is_bound_never_interpolated(self) -> None:
        """Only the attribute NAME is interpolated, and it is a code constant."""
        repo, db = _repo([])
        repo.get_by_password_reset_token("' OR 1==1 //")
        assert "OR 1==1" not in db.aql.queries[0]

    def test_no_match_is_none_not_an_exception(self) -> None:
        repo, _ = _repo([])
        assert repo.get_by_email_verification_token(VERIFY_TOKEN) is None
        assert repo.get_by_password_reset_token(RESET_TOKEN) is None

    def test_the_key_is_derived_from_the_id_when_arango_omits_it(self) -> None:
        """``_from_doc``'s normalisation, which the service used to duplicate."""
        repo, _ = _repo([_doc(password_reset_token=RESET_TOKEN)])
        user = repo.get_by_password_reset_token(RESET_TOKEN)
        assert user is not None
        assert user.key == "u-1"


class TestTheEmptyToken:
    """The one behaviour this move changes, and it changes it inwards."""

    @pytest.mark.parametrize("empty", ["", None])
    def test_an_empty_token_matches_nobody_without_reaching_the_database(self, empty: str | None) -> None:
        repo, db = _repo([_doc(), _doc(_id="users/u-2")])

        assert repo.get_by_password_reset_token(empty) is None  # type: ignore[arg-type]
        assert repo.get_by_email_verification_token(empty) is None  # type: ignore[arg-type]
        assert db.aql.queries == []
