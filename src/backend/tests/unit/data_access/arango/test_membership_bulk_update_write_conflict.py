"""A bulk membership ``UPDATE`` that meets a write-write conflict (1200) retries, then says so as a 409.

The erasure deactivates every membership of a tenant while a join may be rolling its own back; the
driver answers the clash with a raw ``AQLQueryExecuteError`` 1200, which the erasure's retry contract
(:class:`WriteConflictError`) never saw (flake of ``test_erasure_late_join_race``).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from arango.exceptions import AQLQueryExecuteError

from app.common.exceptions import WriteConflictError
from app.data_access.arango.membership_repository import ArangoMembershipRepository


def _error(code: int) -> AQLQueryExecuteError:
    exc = AQLQueryExecuteError.__new__(AQLQueryExecuteError)
    exc.error_code = code
    return exc


def _repo(side_effect: list) -> tuple[ArangoMembershipRepository, MagicMock]:
    db = MagicMock()
    db.aql.execute.side_effect = side_effect
    return ArangoMembershipRepository(db), db


def test_a_conflict_that_clears_on_the_retry_returns_the_count():
    repo, db = _repo([_error(1200), iter([2])])

    assert repo.deactivate_all_for_tenant("t1") == 2
    assert db.aql.execute.call_count == 2


def test_a_conflict_that_outlasts_the_attempts_is_a_write_conflict():
    repo, db = _repo([_error(1200)] * ArangoMembershipRepository._ROLLBACK_ATTEMPTS)

    with pytest.raises(WriteConflictError):
        repo.deactivate_all_for_tenant("t1")
    assert db.aql.execute.call_count == ArangoMembershipRepository._ROLLBACK_ATTEMPTS


def test_any_other_driver_error_is_not_swallowed():
    repo, _ = _repo([_error(1210)])

    with pytest.raises(AQLQueryExecuteError):
        repo.deactivate_all_for_tenant("t1")


def test_the_importing_activation_takes_the_same_path():
    repo, _ = _repo([_error(1200)] * ArangoMembershipRepository._ROLLBACK_ATTEMPTS)

    with pytest.raises(WriteConflictError):
        repo.activate_all_for_importing_tenant("t1")
