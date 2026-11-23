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


#: What the page's IndexedDB trace (#3082) holds when the probe's open is queued: a deletion the app asked for,
#: blocked by a connection that got ``versionchange`` and never closed.
TRACE = [
    {
        "id": 1,
        "db": "kp-plan-cache",
        "op": "open",
        "version": 20,
        "t": 812,
        "wall": 1,
        "stack": "Dexie.open < app",
    },
    {"id": 1, "db": "kp-plan-cache", "ev": "success", "t": 830},
    {
        "id": 2,
        "db": "kp-plan-cache",
        "op": "delete",
        "version": None,
        "t": 1500,
        "wall": 2,
        "stack": "wipe < app",
    },
    {"id": 1, "db": "kp-plan-cache", "ev": "versionchange 20->null", "t": 1502},
    {"id": 2, "db": "kp-plan-cache", "ev": "blocked 20->null", "t": 1503},
]


class ProbeDriver:
    def __init__(self, store_answer: object, trace: object = None) -> None:
        self.store_answer = store_answer
        self.trace = trace
        self.store_probes: list[tuple[object, ...]] = []

    def execute_async_script(self, script: str, *args: object) -> object:
        if script == offline._DATABASE_NAMES:
            return {"names": [offline.PLAN_CACHE_DB]}
        if script == offline._STORE_KEYS:
            self.store_probes.append(args)
            return self.store_answer
        if script == offline._TRACE_ENTRIES:
            return {"entries": self.trace}
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


def test_a_pending_open_names_the_requests_ahead_of_it() -> None:
    driver = ProbeDriver({**PENDING, "trace": TRACE})

    with pytest.raises(offline.OfflineProbeError) as raised:
        offline.indexeddb_record_keys(driver, offline.PLAN_CACHE_DB, "bedSheets")  # type: ignore[arg-type]

    message = str(raised.value)
    assert "#2 kp-plan-cache t=1500 delete (no version) from wipe < app" in message
    assert "#2 kp-plan-cache t=1503 -> blocked 20->null" in message
    assert "#1 kp-plan-cache t=1502 -> versionchange 20->null" in message
    assert "#1 kp-plan-cache t=812 open (version 20) from Dexie.open < app" in message


def test_a_pending_open_in_an_untraced_document_says_so() -> None:
    driver = ProbeDriver({**PENDING, "trace": None})

    with pytest.raises(
        offline.OfflineProbeError, match="install_indexeddb_trace was not registered"
    ):
        offline.indexeddb_record_keys(driver, offline.PLAN_CACHE_DB, "bedSheets")  # type: ignore[arg-type]


def test_a_record_that_never_came_quotes_the_trace() -> None:
    driver = ProbeDriver({"keys": []}, trace=TRACE)

    with pytest.raises(AssertionError) as raised:
        offline.wait_for_cached_record(
            driver,  # type: ignore[arg-type]
            offline.PLAN_CACHE_DB,
            "bedSheets",
            "bed_1",
            "TC-053-087",
            timeout=1,
        )

    assert "holds no record" in str(raised.value)
    assert "-> blocked 20->null" in str(raised.value)


def test_the_trace_quotes_only_the_newest_entries() -> None:
    entries = [{"id": n, "db": "kp-plan-cache", "ev": "success", "t": n} for n in range(100)]

    text = offline.format_indexeddb_trace(entries)

    assert f"last {offline.TRACE_QUOTED} of 100" in text
    first_quoted = 100 - offline.TRACE_QUOTED
    assert "#99 " in text and f"#{first_quoted} " in text
    assert f"#{first_quoted - 1} " not in text


def test_the_trace_is_a_pass_through_for_the_two_app_databases() -> None:
    script = offline._IDB_TRACE

    assert '["kp-plan-cache", "kp-write-queue"]' in script
    assert "originalOpen.apply(this, arguments)" in script
    assert "originalDelete.apply(this, arguments)" in script
    assert f"LIMIT = {offline.TRACE_LIMIT}" in script
    # The probe opens through the saved original, so its polling is not traced.
    assert "trace ? trace.open : IDBFactory.prototype.open" in offline._STORE_KEYS


def test_the_trace_names_the_document_of_every_entry() -> None:
    entries = [
        {"id": 0, "db": "-", "ev": "document /dashboard", "t": 3, "doc": 1},
        {
            "id": 2,
            "db": "kp-plan-cache",
            "op": "delete",
            "version": None,
            "t": 900,
            "stack": "wipe",
            "doc": 1,
        },
        {"id": 0, "db": "-", "ev": "pagehide persisted", "t": 1200, "doc": 1},
        {
            "id": 3,
            "db": "kp-plan-cache",
            "op": "open",
            "version": 20,
            "t": 98,
            "stack": "app",
            "doc": 2,
        },
    ]

    text = offline.format_indexeddb_trace(entries)

    assert "across the tab's documents" in text
    assert "d1 #2 kp-plan-cache t=900 delete (no version)" in text
    assert "d1 #0 - t=1200 -> pagehide persisted" in text
    assert "d2 #3 kp-plan-cache t=98 open (version 20)" in text


def test_the_trace_spans_the_tab_and_records_the_page_lifecycle() -> None:
    script = offline._IDB_TRACE

    # Earlier documents of the tab survive a navigation (#3082: the request ahead was issued before the failing
    # document existed), and a refused storage only loses that history.
    assert "window.sessionStorage.getItem(KEY)" in script
    assert "window.sessionStorage.setItem(KEY" in script
    assert "['pagehide', 'pageshow']" in script and "e.persisted" in script
    assert "['freeze', 'resume']" in script
