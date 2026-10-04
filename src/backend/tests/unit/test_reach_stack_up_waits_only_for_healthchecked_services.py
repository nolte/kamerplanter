"""``reach:stack:up`` waits only for services that have a healthcheck.

``docker compose up --wait`` refuses a service without a healthcheck on current
Compose versions ("has no healthcheck configured"): the Celery worker disables
its inherited HTTP check (nothing depends on it), so a GitHub runner failed the
whole stack with exit 201 while a workstation with an older Compose accepted it.
The first ``up`` starts everything; only the second one waits, and it must not
name the worker.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.support.repo_scripts import load_repo_script

stack = load_repo_script("reach/stack")
common = load_repo_script("reach/_reach_common")


def test_the_waiting_up_names_no_service_without_a_healthcheck(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    seen: list[list[str]] = []

    def fake_compose_command(*args: str) -> list[str]:
        return ["docker", "compose", *args]

    def fake_run(command: list[str], **_: Any) -> Any:
        seen.append(command)
        if command[:3] == ["docker", "compose", "port"]:
            return type("R", (), {"stdout": b"0.0.0.0:1234\n"})()
        return type("R", (), {"stdout": b""})()

    monkeypatch.setattr(stack, "compose_command", fake_compose_command)
    monkeypatch.setattr(stack, "run", fake_run)
    monkeypatch.setattr(stack, "reach_dir", lambda: tmp_path)
    monkeypatch.setattr(stack, "wait_until", lambda *a, **k: None)
    monkeypatch.setattr(stack, "Arango", lambda *_: type("A", (), {"request": lambda *a, **k: None})())
    monkeypatch.setattr(stack, "stack_file", lambda: tmp_path / "stack.json")

    stack.up()

    ups = [c for c in seen if c[2:3] == ["up"]]
    waiting = [c for c in ups if "--wait" in c]
    assert waiting, "the stack must still wait for the services that have a healthcheck"
    for command in waiting:
        assert common.WORKER_SERVICE not in command
    started = [c for c in ups if "--wait" not in c]
    assert started
    assert common.WORKER_SERVICE in started[0]
