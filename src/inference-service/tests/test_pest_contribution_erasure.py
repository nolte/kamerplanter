"""REQ-025 / REQ-024 — erasure of user-contributed pest prototypes (issue #1759).

A promoted pest-image contribution is indexed into ``pest_embeddings`` with
``source = 'user_contributed'``, ``source_record_id = <contribution key>`` and
``source_url = contribution://<tenant key>/<contribution key>``
(backend ``app/tasks/pest_image_tasks.py``). The Art. 17 erasure and the tenant
deletion used to *deactivate* those rows; these routes delete them.

Pinned on the HTTP surface and on the SQL the real repository sends:

* only ``user_contributed`` rows are reached, whatever else shares a key;
* a blank or empty filter is refused instead of matching nothing (a "successful"
  erasure that erased nothing) or everything;
* no key travels in a path (#1700).
"""

from __future__ import annotations

import pytest

from app.vectordb.pest_repository import PestEmbeddingRepository

_BY_KEYS = "/pest/reference/contributions/erase"
_BY_TENANT = "/pest/reference/contributions/erase-by-tenant"


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
    rows = [
        # The subject's contributions: one active, one demoted (deactivated).
        _row("spider_mite", "user_contributed", "c-1", "t-1"),
        _row("aphid", "user_contributed", "c-2", "t-1", active=False),
        # Another user's contribution in the same tenant, and one in another
        # tenant whose key starts like the first ("t-1" vs "t-10").
        _row("aphid", "user_contributed", "c-3", "t-1"),
        _row("aphid", "user_contributed", "c-4", "t-10"),
        # Curated rows that share a record id with a contribution.
        _row("spider_mite", "gbif", "c-1"),
        _row("thrips", "inaturalist", "c-9"),
    ]
    fake_pest_repo.rows.extend(rows)


def _remaining(fake_pest_repo) -> list[tuple[str, str]]:
    return sorted((r["source"], r["source_record_id"]) for r in fake_pest_repo.rows)


# -- by contribution keys (Art. 17 user erasure, single contribution delete) --


def test_erase_by_keys_deletes_active_and_deactivated_contributions(client, fake_pest_repo):
    _seed(fake_pest_repo)

    resp = client.post(_BY_KEYS, json={"contribution_keys": ["c-1", "c-2"]})

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "deleted": 2}
    assert _remaining(fake_pest_repo) == [
        ("gbif", "c-1"),
        ("inaturalist", "c-9"),
        ("user_contributed", "c-3"),
        ("user_contributed", "c-4"),
    ]


def test_erase_by_keys_with_no_matching_rows_reports_zero(client, fake_pest_repo):
    _seed(fake_pest_repo)

    resp = client.post(_BY_KEYS, json={"contribution_keys": ["c-unknown"]})

    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0
    assert len(fake_pest_repo.rows) == 6


@pytest.mark.parametrize("keys", [[], [""], ["c-1", " "], None])
def test_erase_by_keys_refuses_an_empty_or_blank_filter(client, fake_pest_repo, keys):
    _seed(fake_pest_repo)

    resp = client.post(_BY_KEYS, json={"contribution_keys": keys})

    assert resp.status_code == 422
    assert len(fake_pest_repo.rows) == 6


# -- by tenant (REQ-024 tenant deletion) --------------------------------------


def test_erase_by_tenant_deletes_only_that_tenants_contributions(client, fake_pest_repo):
    _seed(fake_pest_repo)

    resp = client.post(_BY_TENANT, json={"tenant_key": "t-1"})

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "deleted": 3}
    # "t-10" is another tenant, not a prefix match of "t-1".
    assert _remaining(fake_pest_repo) == [
        ("gbif", "c-1"),
        ("inaturalist", "c-9"),
        ("user_contributed", "c-4"),
    ]


@pytest.mark.parametrize("tenant_key", ["", " ", None, "t-1/c-1", "t-1/"])
def test_erase_by_tenant_refuses_a_blank_or_malformed_tenant(client, fake_pest_repo, tenant_key):
    _seed(fake_pest_repo)

    resp = client.post(_BY_TENANT, json={"tenant_key": tenant_key})

    assert resp.status_code == 422
    assert len(fake_pest_repo.rows) == 6


# -- routing, auth, logging ---------------------------------------------------


@pytest.mark.parametrize(
    ("path", "body"),
    [(_BY_KEYS, {"contribution_keys": ["c-1"]}), (_BY_TENANT, {"tenant_key": "t-1"})],
)
def test_erasure_requires_the_service_token(unauth_client, fake_pest_repo, path, body):
    _seed(fake_pest_repo)

    resp = unauth_client.post(path, json=body)

    assert resp.status_code == 401
    assert len(fake_pest_repo.rows) == 6


def test_a_class_labelled_contributions_is_not_touched_by_the_erasure(client, fake_pest_repo):
    """``/pest/reference/{label}`` must not capture the erasure paths or vice versa."""
    fake_pest_repo.rows.append(_row("contributions", "gbif", "g-1"))
    fake_pest_repo.rows.append(_row("aphid", "user_contributed", "c-1", "t-1"))

    resp = client.post(_BY_TENANT, json={"tenant_key": "t-1"})

    assert resp.status_code == 200
    assert _remaining(fake_pest_repo) == [("gbif", "g-1")]


def test_a_refused_body_does_not_echo_a_key(client, fake_pest_repo):
    resp = client.post(_BY_TENANT, json={"tenant_key": "t-secret/x"})

    assert resp.status_code == 422
    assert "t-secret" not in resp.text


# -- the real repository's SQL ------------------------------------------------


class _Result:
    rowcount = 2


class _RecordingPool:
    """Captures the SQL the real repository sends; no database involved."""

    def __init__(self) -> None:
        self.calls: list = []

    def connection(self):  # type: ignore[no-untyped-def]
        calls = self.calls

        class _Conn:
            def execute(self, sql, params=None):  # type: ignore[no-untyped-def]
                calls.append((" ".join(str(sql).split()), params))
                return _Result()

        class _Ctx:
            def __enter__(self):  # type: ignore[no-untyped-def]
                return _Conn()

            def __exit__(self, *exc):  # type: ignore[no-untyped-def]
                return False

        return _Ctx()


def test_repository_sql_is_source_bound_and_parameterised():
    pool = _RecordingPool()
    repo = PestEmbeddingRepository(pool)  # type: ignore[arg-type]

    assert repo.delete_contributions(["c-1", "c-2"]) == 2
    assert repo.delete_tenant_contributions("t-1") == 2

    (keys_sql, keys_params), (tenant_sql, tenant_params) = pool.calls
    for sql in (keys_sql, tenant_sql):
        assert sql.startswith("DELETE FROM pest_embeddings WHERE source = 'user_contributed' AND")
        assert "c-1" not in sql and "t-1" not in sql
    assert "source_record_id = ANY(%s)" in keys_sql
    assert keys_params == (["c-1", "c-2"],)
    assert "starts_with(source_url, %s)" in tenant_sql
    assert tenant_params == ("contribution://t-1/",)


@pytest.mark.parametrize(
    ("method", "arg"),
    [("delete_contributions", []), ("delete_contributions", [" "]), ("delete_tenant_contributions", "a/b")],
)
def test_repository_refuses_an_unscoped_delete(method, arg):
    pool = _RecordingPool()
    repo = PestEmbeddingRepository(pool)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        getattr(repo, method)(arg)
    assert pool.calls == []
