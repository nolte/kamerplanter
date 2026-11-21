"""`indexeddb_record_keys` names an IndexedDB open that never completes instead of a Selenium script timeout.

TC-053-087 (nightly 44931220064, `full`) and TC-053-088 (earlier nightlies) failed with a bare
"script timeout" in `_offline_helpers.py`: the store probe's `indexedDB.open` stayed pending,
and the script had no path that answered then. An open queued behind a version change or a
deletion that another connection blocks behaves exactly so (reproduced in headless Chrome:
the old probe hits the script timeout, the new one answers `{pending: true, ...}` with the
origin's databases). `wait_for_cached_record` then caught Selenium's `TimeoutException`
as its own and probed a second time for the message - a second 30 s hang.

Browser-free: the real helpers over a driver that answers the two async scripts.
"""

from __future__ import annotations

import pytest

from tests.e2e import _offline_helpers as offline

#: Selenium's default script timeout; the probe has to answer before it.
DRIVER_SCRIPT_TIMEOUT_MS = 30_000

PENDING = {
    "pending": True,
    "readyState": "pending",
    "waitedMs": 10_000,
    "databases": ["kp-plan-cache@20"],
}


class ProbeDriver:
    def __init__(self, store_answer: object) -> None:
        self.store_answer = store_answer
        self.store_probes: list[tuple[object, ...]] = []

    def execute_async_script(self, script: str, *args: object) -> object:
        if script == offline._DATABASE_NAMES:
            return {"names": [offline.PLAN_CACHE_DB]}
        if script == offline._STORE_KEYS:
            self.store_probes.append(args)
            return self.store_answer
        raise AssertionError(f"ProbeDriver got an unexpected script: {script[:60]!r}")


def test_a_pending_open_is_reported_as_such() -> None:
    driver = ProbeDriver(PENDING)

    with pytest.raises(offline.OfflineProbeError, match="did not complete") as raised:
        offline.indexeddb_record_keys(driver, offline.PLAN_CACHE_DB, "bedSheets")  # type: ignore[arg-type]

    assert "kp-plan-cache@20" in str(raised.value)


def test_the_probe_answers_before_the_driver_gives_up() -> None:
    driver = ProbeDriver({"keys": []})

    offline.indexeddb_record_keys(driver, offline.PLAN_CACHE_DB, "bedSheets")  # type: ignore[arg-type]

    (args,) = driver.store_probes
    assert len(args) == 3, f"the probe gets no pending limit: {args}"
    assert 0 < args[2] < DRIVER_SCRIPT_TIMEOUT_MS


def test_waiting_for_a_record_fails_at_once_naming_the_pending_open() -> None:
    driver = ProbeDriver(PENDING)

    with pytest.raises(offline.OfflineProbeError, match="did not complete"):
        offline.wait_for_cached_record(
            driver,  # type: ignore[arg-type]
            offline.PLAN_CACHE_DB,
            "bedSheets",
            "bed_1",
            "TC-053-087",
        )

    assert len(driver.store_probes) == 1


def test_a_written_record_is_still_found() -> None:
    driver = ProbeDriver({"keys": ["u:t:bed_1"]})

    key = offline.wait_for_cached_record(
        driver,  # type: ignore[arg-type]
        offline.PLAN_CACHE_DB,
        "bedSheets",
        "bed_1",
        "TC-053-087",
    )

    assert key == "u:t:bed_1"
