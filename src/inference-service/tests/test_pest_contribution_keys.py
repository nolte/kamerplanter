"""REQ-025 — listing the contribution keys that have a pest prototype (issue #1771).

Before #1766, deleting a pest-image contribution left its prototype in
``pest_embeddings``. Those rows name a contribution whose document is gone, so
the account erasure (which resolves prototypes through the documents) cannot
reach them. The backend's orphan sweep needs the keys the index holds to find
them; this route returns exactly that and nothing else.

Pinned on the HTTP surface and on the SQL the real repository sends:

* only ``user_contributed`` keys are listed, each once, ascending;
* keyset paging: ``after`` excludes itself, a full page names its last key;
* the cursor travels in the body, never in the URL, and a refused body is not
  echoed (#1700);
* the route sits behind the service token.
"""

from __future__ import annotations

import pytest

from app.vectordb.pest_repository import MAX_CONTRIBUTION_KEYS, PestEmbeddingRepository

_KEYS = "/pest/reference/contributions/keys"


def _row(label, source, record_id, tenant=None, *, active=True):  # type: ignore[no-untyped-def]
    url = f"contribution://{tenant}/{record_id}" if source == "user_contributed" else f"https://gbif.org/{record_id}"
    return {
        "label": label,
        "category": "pest",
        "source": source,
        "source_record_id": record_id,
        "source_url": url,
        "is_active": active,
    }


def _seed(fake_pest_repo) -> None:
    fake_pest_repo.rows.extend(
        [
            _row("spider_mite", "user_contributed", "c-2", "t-1"),
            # One contribution under two labels (its pest's class changed) → listed once.
            _row("aphid", "user_contributed", "c-1", "t-1"),
            _row("thrips", "user_contributed", "c-1", "t-1", active=False),
            _row("aphid", "user_contributed", "c-3", "t-2", active=False),
            # A blank key the erase route would refuse: never listed (it would stop
            # every sweep on its first page).
            _row("aphid", "user_contributed", " ", "t-2"),
            # Curated rows, also one sharing a contribution's record id: never listed.
            _row("spider_mite", "gbif", "c-1"),
            _row("thrips", "inaturalist", "g-9"),
        ]
    )


def test_lists_each_contributed_key_once_in_ascending_order(client, fake_pest_repo):
    _seed(fake_pest_repo)

    resp = client.post(_KEYS, json={})

    assert resp.status_code == 200
    assert resp.json() == {"contribution_keys": ["c-1", "c-2", "c-3"], "next_after": None}


def test_pages_by_keyset_until_a_short_page(client, fake_pest_repo):
    _seed(fake_pest_repo)

    first = client.post(_KEYS, json={"limit": 2}).json()
    second = client.post(_KEYS, json={"limit": 2, "after": first["next_after"]}).json()

    assert first == {"contribution_keys": ["c-1", "c-2"], "next_after": "c-2"}
    assert second == {"contribution_keys": ["c-3"], "next_after": None}


def test_an_empty_index_is_one_empty_last_page(client, fake_pest_repo):
    resp = client.post(_KEYS, json={"limit": 5})

    assert resp.status_code == 200
    assert resp.json() == {"contribution_keys": [], "next_after": None}


@pytest.mark.parametrize("limit", [0, -1, MAX_CONTRIBUTION_KEYS + 1])
def test_refuses_a_limit_outside_the_bound_without_echoing_the_cursor(client, fake_pest_repo, limit):
    _seed(fake_pest_repo)

    resp = client.post(_KEYS, json={"limit": limit, "after": "cursor-key-7f3a"})

    assert resp.status_code == 422
    assert "cursor-key-7f3a" not in resp.text


def test_listing_requires_the_service_token(unauth_client, fake_pest_repo):
    _seed(fake_pest_repo)

    resp = unauth_client.post(_KEYS, json={})

    assert resp.status_code == 401
    assert "c-1" not in resp.text


class _Result:
    def __init__(self, rows):  # type: ignore[no-untyped-def]
        self._rows = rows

    def fetchall(self):  # type: ignore[no-untyped-def]
        return self._rows


class _RecordingPool:
    def __init__(self, rows) -> None:  # type: ignore[no-untyped-def]
        self.calls: list = []
        self._rows = rows

    def connection(self):  # type: ignore[no-untyped-def]
        calls, rows = self.calls, self._rows

        class _Conn:
            def execute(self, sql, params=None):  # type: ignore[no-untyped-def]
                calls.append((" ".join(str(sql).split()), params))
                return _Result(rows)

        class _Ctx:
            def __enter__(self):  # type: ignore[no-untyped-def]
                return _Conn()

            def __exit__(self, *exc):  # type: ignore[no-untyped-def]
                return False

        return _Ctx()


def test_repository_sql_is_source_bound_and_parameterised():
    pool = _RecordingPool([("c-1",), ("c-2",)])
    repo = PestEmbeddingRepository(pool)  # type: ignore[arg-type]

    assert repo.list_contribution_keys(after="c-0", limit=2) == ["c-1", "c-2"]

    ((sql, params),) = pool.calls
    assert sql.startswith("SELECT DISTINCT source_record_id FROM pest_embeddings WHERE source = 'user_contributed'")
    assert "source_record_id > %(after)s::text" in sql
    assert "source_record_id ~ '[^[:space:]]'" in sql
    assert "ORDER BY source_record_id LIMIT %(limit)s" in sql
    assert "c-0" not in sql
    assert params == {"after": "c-0", "limit": 2}


def test_repository_refuses_an_out_of_bound_limit_before_querying():
    pool = _RecordingPool([])
    repo = PestEmbeddingRepository(pool)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        repo.list_contribution_keys(limit=0)
    assert pool.calls == []
