"""``KeyedLocks`` serialises one key, leaves other keys alone and keeps no entry for an idle key (#2062)."""

from __future__ import annotations

import threading

from app.common.keyed_lock import KeyedLocks


def test_one_key_is_held_by_one_thread_at_a_time() -> None:
    locks = KeyedLocks()
    inside = 0
    peak = 0
    guard = threading.Lock()

    def work() -> None:
        nonlocal inside, peak
        with locks.hold("a"):
            with guard:
                inside += 1
                peak = max(peak, inside)
            threading.Event().wait(0.01)
            with guard:
                inside -= 1

    threads = [threading.Thread(target=work) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert peak == 1


def test_another_key_does_not_wait() -> None:
    locks = KeyedLocks()
    with locks.hold("a"):
        done = threading.Event()

        def other() -> None:
            with locks.hold("b"):
                done.set()

        thread = threading.Thread(target=other)
        thread.start()
        assert done.wait(timeout=2)
        thread.join(timeout=2)


def test_the_table_is_empty_when_nobody_holds_or_waits() -> None:
    locks = KeyedLocks()
    for key in ("a", "b", "a"):
        with locks.hold(key):
            assert len(locks) >= 1

    assert len(locks) == 0


def test_a_raising_body_releases_the_key() -> None:
    locks = KeyedLocks()
    try:
        with locks.hold("a"):
            raise RuntimeError
    except RuntimeError:
        pass

    with locks.hold("a"):
        assert len(locks) == 1
    assert len(locks) == 0
