"""The vector-database step recreates the API and the worker but waits only for the API.

Same defect as ``reach:stack:up``: ``docker compose up --wait`` refuses the worker
(its healthcheck is disabled) on current Compose versions, so ``reach:vectordb:up``
failed with exit 201 on a GitHub runner.
"""

from __future__ import annotations

import pytest

from tests.support.repo_scripts import load_repo_script

vectordb = load_repo_script("reach/vectordb")


def test_the_waiting_call_names_no_service_without_a_healthcheck(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []
    monkeypatch.setattr(vectordb, "run", lambda command, **_: seen.append(command) or type("R", (), {"stdout": b""})())

    vectordb._recreate_backend(["docker", "compose", "-p", "p"])

    waiting = [c for c in seen if "--wait" in c]
    assert waiting, "the API must still be waited for"
    for command in waiting:
        assert vectordb.WORKER_SERVICE not in command
        assert vectordb.BACKEND_SERVICE in command
    recreated = [c for c in seen if "--wait" not in c]
    assert recreated
    assert vectordb.WORKER_SERVICE in recreated[0]
    assert vectordb.BACKEND_SERVICE in recreated[0]
