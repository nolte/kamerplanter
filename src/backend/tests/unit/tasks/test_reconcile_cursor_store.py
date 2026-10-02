"""#1834 — the reconciliation's resume point only means something to the backend that issued it."""

from __future__ import annotations

from app.tasks.storage_tasks import _RedisCursorStore


class _Redis:
    def __init__(self):
        self.values: dict[str, str] = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, ex=None):
        self.values[key] = value

    def delete(self, key):
        self.values.pop(key, None)


class _DownRedis:
    def get(self, key):
        raise ConnectionError("down")

    set = delete = get


def test_a_token_round_trips_for_its_own_backend():
    client = _Redis()
    store = _RedisCursorStore(client, "s3")
    store.set("tok")
    assert store.get() == "tok"


def test_a_token_from_another_backend_is_ignored():
    client = _Redis()
    _RedisCursorStore(client, "local-fs").set("t/some/key.jpg")
    assert _RedisCursorStore(client, "s3").get() is None


def test_an_unreachable_cursor_means_start_over_not_fail():
    store = _RedisCursorStore(_DownRedis(), "s3")
    assert store.get() is None
    store.set("tok")
    store.clear()
