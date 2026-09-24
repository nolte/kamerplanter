"""REQ-025 AK-OS-05 / issue #1753 — erasure of user-contributed reference vectors.

The backend's Art. 17 erasure (Phase 0.5) and the REQ-024 tenant deletion remove
a user's / tenant's ``source = 'user_contributed'`` rows from
``species_embeddings``. Two properties carry the whole feature and are pinned
here on both the HTTP surface and the SQL the real repository sends:

* the delete never reaches a row whose ``source`` is anything else (curated
  GBIF / Wikimedia / manual references stay), and
* a blank filter never widens into a mass delete — it is refused.
"""

from __future__ import annotations

import pytest

from app.vectordb.repository import SpeciesEmbeddingRepository

_BY_CONTRIBUTOR = "/reference/contributions/by-contributor"
_BY_TENANT = "/reference/contributions/by-tenant"


def _seed(fake_repo) -> None:
    """Three contributors across two tenants plus a curated row per identity."""
    rows = [
        # The subject's own contributions in two tenants.
        {"species_key": "sp-a", "source": "user_contributed", "contributed_by": "user-a", "tenant_key": "t-1"},
        {"species_key": "sp-b", "source": "user_contributed", "contributed_by": "user-a", "tenant_key": "t-2"},
        # Another contributor in the subject's tenant.
        {"species_key": "sp-a", "source": "user_contributed", "contributed_by": "user-b", "tenant_key": "t-1"},
        # A curated row that (wrongly or by import) carries the same identities:
        # the source filter alone must keep it.
        {"species_key": "sp-a", "source": "gbif", "contributed_by": "user-a", "tenant_key": "t-1"},
        {"species_key": "sp-c", "source": "wikimedia", "contributed_by": None, "tenant_key": None},
    ]
    for row in rows:
        fake_repo.upsert_reference(**row)


def _remaining(fake_repo) -> list[tuple]:
    return sorted(
        (r["source"], r.get("contributed_by") or "", r.get("tenant_key") or "", r["species_key"])
        for r in fake_repo.rows
    )


# -- by contributor (Art. 17 user erasure) ----------------------------------


def test_delete_by_contributor_removes_only_that_users_contributions(client, fake_repo):
    _seed(fake_repo)

    resp = client.delete(f"{_BY_CONTRIBUTOR}/user-a")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "deleted": 2}
    assert _remaining(fake_repo) == [
        ("gbif", "user-a", "t-1", "sp-a"),
        ("user_contributed", "user-b", "t-1", "sp-a"),
        ("wikimedia", "", "", "sp-c"),
    ]


def test_delete_by_contributor_scoped_to_one_tenant_keeps_the_other_tenant(client, fake_repo):
    _seed(fake_repo)

    resp = client.delete(f"{_BY_CONTRIBUTOR}/user-a", params={"tenant_key": "t-1"})

    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1
    remaining = _remaining(fake_repo)
    assert ("user_contributed", "user-a", "t-2", "sp-b") in remaining
    assert ("user_contributed", "user-a", "t-1", "sp-a") not in remaining


def test_delete_by_contributor_with_no_rows_reports_zero(client, fake_repo):
    _seed(fake_repo)

    resp = client.delete(f"{_BY_CONTRIBUTOR}/nobody")

    assert resp.status_code == 200
    assert resp.json()["deleted"] == 0
    assert len(fake_repo.rows) == 5


@pytest.mark.parametrize("path_key", ["%20", "%09"])
def test_delete_by_contributor_refuses_a_blank_contributor(client, fake_repo, path_key):
    _seed(fake_repo)

    resp = client.delete(f"{_BY_CONTRIBUTOR}/{path_key}")

    assert resp.status_code == 422
    assert len(fake_repo.rows) == 5


def test_delete_by_contributor_refuses_a_blank_tenant_scope(client, fake_repo):
    _seed(fake_repo)

    resp = client.delete(f"{_BY_CONTRIBUTOR}/user-a", params={"tenant_key": " "})

    assert resp.status_code == 422
    assert len(fake_repo.rows) == 5


# -- by tenant (REQ-024 tenant deletion) -------------------------------------


def test_delete_by_tenant_removes_only_that_tenants_contributions(client, fake_repo):
    _seed(fake_repo)

    resp = client.delete(f"{_BY_TENANT}/t-1")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "deleted": 2}
    assert _remaining(fake_repo) == [
        ("gbif", "user-a", "t-1", "sp-a"),
        ("user_contributed", "user-a", "t-2", "sp-b"),
        ("wikimedia", "", "", "sp-c"),
    ]


def test_delete_by_tenant_refuses_a_blank_tenant(client, fake_repo):
    _seed(fake_repo)

    resp = client.delete(f"{_BY_TENANT}/%20")

    assert resp.status_code == 422
    assert len(fake_repo.rows) == 5


# -- routing and auth ------------------------------------------------------


def test_contribution_delete_is_not_captured_by_the_species_delete(client, fake_repo):
    """``DELETE /reference/{species_key}`` must not swallow the contribution paths.

    A species literally keyed ``contributions`` would be wiped wholesale if the
    router resolved the new path to the species delete.
    """
    fake_repo.upsert_reference(species_key="contributions", source="gbif")
    fake_repo.upsert_reference(species_key="by-tenant", source="gbif")
    fake_repo.upsert_reference(species_key="sp-a", source="user_contributed", contributed_by="u", tenant_key="t-9")

    resp = client.delete(f"{_BY_TENANT}/t-9")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "deleted": 1}
    assert {r["species_key"] for r in fake_repo.rows} == {"contributions", "by-tenant"}


def test_species_delete_still_resolves(client, fake_repo):
    fake_repo.upsert_reference(species_key="sp-x", source="gbif")

    resp = client.delete("/reference/sp-x")

    assert resp.status_code == 200
    assert resp.json()["deleted"] == 1


@pytest.mark.parametrize("path", [f"{_BY_CONTRIBUTOR}/user-a", f"{_BY_TENANT}/t-1"])
def test_contribution_delete_requires_the_service_token(unauth_client, fake_repo, path):
    _seed(fake_repo)

    resp = unauth_client.delete(path)

    assert resp.status_code == 401
    assert len(fake_repo.rows) == 5


# -- the real repository's SQL ---------------------------------------------


class _Result:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class _RecordingConnection:
    def __init__(self, calls: list) -> None:
        self._calls = calls

    def execute(self, sql, params=None):
        self._calls.append((" ".join(str(sql).split()), params))
        return _Result(3)


class _RecordingPool:
    """Captures the SQL the real repository sends; no database involved."""

    def __init__(self) -> None:
        self.calls: list = []

    def connection(self):
        pool = self

        class _Ctx:
            def __enter__(self):
                return _RecordingConnection(pool.calls)

            def __exit__(self, *exc):
                return False

        return _Ctx()


def test_repository_delete_by_contributor_sql_is_source_bound_and_parameterised():
    pool = _RecordingPool()
    repo = SpeciesEmbeddingRepository(pool)  # type: ignore[arg-type]

    assert repo.delete_user_contributions("user-a") == 3
    assert repo.delete_user_contributions("user-a", tenant_key="t-1") == 3

    (unscoped_sql, unscoped_params), (scoped_sql, scoped_params) = pool.calls
    for sql in (unscoped_sql, scoped_sql):
        assert sql.startswith("DELETE FROM species_embeddings WHERE")
        assert "source = 'user_contributed'" in sql
        assert "user-a" not in sql and "t-1" not in sql
    assert "contributed_by = %s" in unscoped_sql and "tenant_key" not in unscoped_sql
    assert unscoped_params == ("user-a",)
    assert "contributed_by = %s AND tenant_key = %s" in scoped_sql
    assert scoped_params == ("user-a", "t-1")


def test_repository_delete_by_tenant_sql_is_source_bound_and_parameterised():
    pool = _RecordingPool()
    repo = SpeciesEmbeddingRepository(pool)  # type: ignore[arg-type]

    assert repo.delete_tenant_contributions("t-1") == 3

    ((sql, params),) = pool.calls
    assert sql.startswith("DELETE FROM species_embeddings WHERE")
    assert "source = 'user_contributed'" in sql
    assert "tenant_key = %s" in sql and "contributed_by" not in sql
    assert params == ("t-1",)


@pytest.mark.parametrize("blank", ["", " ", "\t\n"])
def test_repository_refuses_blank_keys_before_touching_the_pool(blank):
    pool = _RecordingPool()
    repo = SpeciesEmbeddingRepository(pool)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        repo.delete_user_contributions(blank)
    with pytest.raises(ValueError):
        repo.delete_user_contributions("user-a", tenant_key=blank)
    with pytest.raises(ValueError):
        repo.delete_tenant_contributions(blank)
    assert pool.calls == []


@pytest.mark.parametrize("blank", ["", " "])
def test_fake_repository_refuses_what_the_real_one_refuses(fake_repo, blank):
    """The API tests run on the fake; it must not accept what production refuses."""
    with pytest.raises(ValueError):
        fake_repo.delete_user_contributions(blank)
    with pytest.raises(ValueError):
        fake_repo.delete_user_contributions("user-a", tenant_key=blank)
    with pytest.raises(ValueError):
        fake_repo.delete_tenant_contributions(blank)
