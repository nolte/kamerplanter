"""#2077 — the command line of the legacy-reading cleanup: defaults, exit codes, and what it prints."""

from __future__ import annotations

import pytest

from app.domain.interfaces.legacy_reading_store import LegacySeriesCounts
from app.domain.services.legacy_reading_cleanup import CleanupResult, CleanupStatus
from app.migrations import purge_orphan_ha_readings as cmd
from tests.unit.domain.services.test_legacy_reading_cleanup import FakeSensors, FakeStore


def _wire(monkeypatch: pytest.MonkeyPatch, store: FakeStore | None, sensors: FakeSensors) -> None:
    monkeypatch.setattr(cmd, "_build", lambda: (store, sensors))


def test_the_default_is_a_dry_run_and_prints_the_confirmation_command(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    store = FakeStore({"gone": LegacySeriesCounts(raw=3, hourly=2, daily=1)})
    _wire(monkeypatch, store, FakeSensors(live=set()))

    code = cmd.main([])

    out = capsys.readouterr().out
    assert code == 0
    assert store.purged == []
    assert "--confirm-delete-orphans 6" in out
    assert "gone" not in out


def test_a_wrong_confirmation_exits_nonzero_and_deletes_nothing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    store = FakeStore({"gone": LegacySeriesCounts(raw=3)})
    _wire(monkeypatch, store, FakeSensors(live=set()))

    code = cmd.main(["--confirm-delete-orphans", "99"])

    assert code == cmd.EXIT_REFUSED
    assert store.purged == []
    assert "re-run the dry run" in capsys.readouterr().out.lower()


def test_the_right_confirmation_deletes_and_exits_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    store = FakeStore({"gone": LegacySeriesCounts(raw=3)})
    _wire(monkeypatch, store, FakeSensors(live=set()))

    assert cmd.main(["--confirm-delete-orphans", "3"]) == 0
    assert store.purged == ["gone"]


def test_a_negative_confirmation_is_a_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        cmd.main(["--confirm-delete-orphans", "-1"])
    assert exc.value.code == 2


def test_not_applicable_exits_zero_with_a_clear_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _wire(monkeypatch, None, FakeSensors(live=set()))

    assert cmd.main([]) == 0
    assert "not applicable" in capsys.readouterr().out.lower()


def test_an_outage_exits_nonzero(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    store = FakeStore({"gone": LegacySeriesCounts(raw=3)}, available=False)
    _wire(monkeypatch, store, FakeSensors(live=set()))

    assert cmd.main(["--confirm-delete-orphans", "3"]) == cmd.EXIT_UNAVAILABLE
    assert store.purged == []
    assert "unreachable" in capsys.readouterr().out.lower()


def test_every_status_has_an_exit_code() -> None:
    assert {s for s in CleanupStatus} == set(cmd.EXIT_CODES)
    assert isinstance(CleanupResult, type)
