"""``create_linked_profile`` transaction plumbing: commit, conflict, abort (#1292).

The *behaviour* — one profile, one edge, nothing visible in between — is measured
against a real ArangoDB in ``tests/integration/test_care_profile_edge_concurrency.py``,
because no double can decide whether the server answers ``1200`` or ``1210`` under
contention. What is doubled here is the plumbing around that decision, which the
integration tier cannot reach on demand: a conflict raised by the *commit* rather
than by an insert, and an abort that itself fails.

Both are defensive branches, and a defensive branch nobody executes is where a
typo lives forever. They are small, so they are pinned rather than argued about.
"""

from __future__ import annotations

import itertools
from typing import Any

import pytest
from arango.exceptions import DocumentInsertError, TransactionCommitError

from app.common.exceptions import DuplicateError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.care_reminder_repository import ArangoCareReminderRepository
from app.domain.models.care_reminder import CareProfile

PLANT = "plant-1"


class _Response:
    """The attributes python-arango's ``ArangoServerError`` reads off a response."""

    def __init__(self, error_code: int, message: str) -> None:
        self.error_code = error_code
        self.error_message = message
        self.status_code = 409
        self.status_text = "Conflict"
        self.method = "post"
        self.url = "http://localhost:8529"
        self.headers: dict[str, str] = {}
        self.body = None


class _Request:
    method = "post"
    endpoint = "/_api/document"
    headers: dict[str, str] = {}
    params: dict[str, str] = {}
    data = None


def _insert_error(code: int) -> DocumentInsertError:
    return DocumentInsertError(
        _Response(code, "unique constraint violated - in index 42 over '[\"_from\"]'"), _Request()
    )


class _Collection:
    def __init__(
        self,
        name: str,
        store: list[dict[str, Any]],
        refuse: Exception | None,
        keys: itertools.count[int],
    ) -> None:
        self._name = name
        self._store = store
        self._refuse = refuse
        self._keys = keys

    def _next_key(self) -> str:
        return f"cp-{next(self._keys)}"

    def insert(self, data: dict[str, Any], return_new: bool = False):
        if self._refuse is not None:
            raise self._refuse
        document = dict(data)
        # ArangoDB assigns the key, and ``_to_doc`` pops any the caller sent — so a
        # double that honoured a supplied ``_key`` would accept a document the real
        # path cannot produce (the #1155 shape: a positive test certifying an
        # impossible input).
        document.pop("_key", None)
        document["_key"] = self._next_key()
        document["_id"] = f"{self._name}/{document['_key']}"
        self._store.append(document)
        return {"new": dict(document)} if return_new else {"_key": document["_key"]}


class _Transaction:
    def __init__(self, refusals: dict[str, Exception], commit_error: Exception | None, abort_error: Exception | None):
        self._refusals = refusals
        self._commit_error = commit_error
        self._abort_error = abort_error
        self.staged: dict[str, list[dict[str, Any]]] = {}
        self._keys = itertools.count(1)
        self.aborted = False
        self.committed = False

    def collection(self, name: str) -> _Collection:
        return _Collection(name, self.staged.setdefault(name, []), self._refusals.get(name), self._keys)

    def commit_transaction(self) -> None:
        if self._commit_error is not None:
            raise self._commit_error
        self.committed = True

    def abort_transaction(self) -> None:
        self.aborted = True
        if self._abort_error is not None:
            raise self._abort_error


class _Db:
    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = kwargs
        self.transaction: _Transaction | None = None
        self.declared_write: list[str] = []

    def collection(self, name: str) -> Any:  # pragma: no cover - the repo only reads through AQL here
        raise AssertionError(f"create_linked_profile must not write {name!r} outside the transaction")

    def begin_transaction(self, write: list[str] | None = None, **_: Any) -> _Transaction:
        self.declared_write = list(write or [])
        self.transaction = _Transaction(**self._kwargs)
        return self.transaction


def _repo(**kwargs: Any) -> tuple[ArangoCareReminderRepository, _Db]:
    db = _Db(
        refusals=kwargs.pop("refusals", {}),
        commit_error=kwargs.pop("commit_error", None),
        abort_error=kwargs.pop("abort_error", None),
    )
    return ArangoCareReminderRepository(db), db  # type: ignore[arg-type]


def _profile() -> CareProfile:
    return CareProfile(plant_key=PLANT, watering_interval_days=7)


class TestTheHappyPath:
    def test_both_documents_are_written_inside_one_declared_transaction(self):
        repo, db = _repo()

        stored = repo.create_linked_profile(_profile(), PLANT)

        assert sorted(db.declared_write) == sorted([col.CARE_PROFILES, col.HAS_CARE_PROFILE]), (
            "a collection written inside a stream transaction but not declared makes ArangoDB refuse the write"
        )
        assert db.transaction is not None
        assert db.transaction.committed and not db.transaction.aborted
        assert stored.key == "cp-1"
        edge = db.transaction.staged[col.HAS_CARE_PROFILE][0]
        assert edge["_from"] == f"{col.PLANT_INSTANCES}/{PLANT}"
        assert edge["_to"] == f"{col.CARE_PROFILES}/cp-1"


class TestARejectionIsTypedAndRollsBack:
    @pytest.mark.parametrize(
        ("code", "expected"),
        [(1210, DuplicateError), (1200, WriteConflictError)],
        ids=["unique-constraint-violated", "write-write-conflict"],
    )
    def test_an_edge_rejection_becomes_the_domain_error_and_aborts(self, code: int, expected: type[Exception]):
        repo, db = _repo(refusals={col.HAS_CARE_PROFILE: _insert_error(code)})

        with pytest.raises(expected):
            repo.create_linked_profile(_profile(), PLANT)

        assert db.transaction is not None
        assert db.transaction.aborted and not db.transaction.committed

    def test_an_unrecognised_driver_code_keeps_propagating_unchanged(self):
        """Only 1200/1210 are answers this caller can resolve; the rest are failures."""
        repo, db = _repo(refusals={col.CARE_PROFILES: _insert_error(1104)})

        with pytest.raises(DocumentInsertError):
            repo.create_linked_profile(_profile(), PLANT)

        assert db.transaction is not None and db.transaction.aborted

    def test_a_conflict_raised_by_the_commit_is_mapped_too(self):
        """Not reached on a single server here, but the server's choice, not ours.

        Left unmapped it is a raw ``TransactionCommitError`` — the exact shape of the
        500 #1292 began as, one layer further in.
        """
        repo, db = _repo(commit_error=TransactionCommitError(_Response(1210, "unique constraint violated"), _Request()))

        with pytest.raises(DuplicateError):
            repo.create_linked_profile(_profile(), PLANT)

        assert db.transaction is not None and db.transaction.aborted


class TestTheChecksCreateDoesAreStillDone:
    """SCR-007: this writer bypasses ``BaseArangoRepository.create``, so it inherits nothing.

    ``create_profile`` *was* ``super().create(profile)``, and ``create`` calls
    ``_verify_owned_references`` before anything is persisted (#948). The first
    draft of ``create_linked_profile`` dropped that silently — the repository
    declares no owned references today, so nothing would have failed and the loss
    would only have surfaced the day somebody added a declaration.
    """

    def test_a_reference_the_caller_does_not_own_is_refused_before_the_transaction(self, monkeypatch):
        """Declared here rather than in production: the check must *run*, not the policy change.

        Adding ``_owned_reference_fields`` to the repository for real would change
        behaviour (a profile for an unknown plant would start failing) and belongs
        to its own decision. What is measured is that a declaration, once made,
        takes effect on this path — and that it takes effect *before*
        ``begin_transaction``, so a rejected write opens no transaction at all.
        """
        repo, db = _repo()
        monkeypatch.setattr(type(repo), "_owned_reference_fields", {"plant_key": col.PLANT_INSTANCES}, raising=False)
        refused = RuntimeError("plant belongs to another tenant")
        monkeypatch.setattr(
            type(repo), "_verify_owned_references", lambda _self, _model, **_kw: (_ for _ in ()).throw(refused)
        )

        with pytest.raises(RuntimeError):
            repo.create_linked_profile(_profile(), PLANT)

        assert db.transaction is None, "the ownership check ran after the transaction was opened"


class TestAFailingAbortNeverMasksTheRealError:
    def test_the_caller_still_sees_the_conflict(self):
        """The abort is cleanup; the conflict is the answer. Cleanup may not win.

        A dropped connection surfaces as a plain ``ConnectionError`` — deliberately
        not an ``ArangoError`` — so a narrow handler here would replace a resolvable
        ``DuplicateError`` with a transport failure and put the 500 back.
        """
        repo, _db = _repo(
            refusals={col.HAS_CARE_PROFILE: _insert_error(1210)},
            abort_error=ConnectionError("connection reset"),
        )

        with pytest.raises(DuplicateError):
            repo.create_linked_profile(_profile(), PLANT)
