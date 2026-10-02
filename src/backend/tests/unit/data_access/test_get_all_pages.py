"""``get_all_pages`` reads every page, forwards scope unchanged and cannot loop forever (#2012)."""

import pytest

from app.data_access.arango.base_repository import PagingCeilingError, get_all_pages


class _Repo:
    def __init__(self, n: int, *, scoped: bool = True) -> None:
        self.rows = [f"row{i:05d}" for i in range(n)]
        self.scoped = scoped
        self.calls: list[dict] = []

    def get_all(self, offset=0, limit=50, tenant_key=None, *, all_tenants=False):
        if self.scoped and not tenant_key and not all_tenants:
            raise ValueError("tenant-scoped")
        self.calls.append({"offset": offset, "limit": limit, "tenant_key": tenant_key, "all_tenants": all_tenants})
        return self.rows[offset : offset + limit], len(self.rows)


@pytest.mark.parametrize("n", [0, 1, 999, 1000, 1001, 2500])
def test_returns_every_row_once_in_order(n: int) -> None:
    repo = _Repo(n)

    rows = get_all_pages(repo, all_tenants=True)

    assert rows == repo.rows


def test_one_call_per_page_and_scope_forwarded() -> None:
    repo = _Repo(2500)

    get_all_pages(repo, all_tenants=True)

    assert [c["offset"] for c in repo.calls] == [0, 1000, 2000]
    assert all(c["limit"] == 1000 and c["all_tenants"] is True for c in repo.calls)


def test_tenant_key_is_forwarded_and_all_tenants_is_not_invented() -> None:
    repo = _Repo(3)

    get_all_pages(repo, tenant_key="t1")

    assert repo.calls == [{"offset": 0, "limit": 1000, "tenant_key": "t1", "all_tenants": False}]


def test_scope_is_not_widened_for_the_caller() -> None:
    with pytest.raises(ValueError, match="tenant-scoped"):
        get_all_pages(_Repo(3))


def test_empty_page_with_a_larger_total_stops() -> None:
    class Shrunk(_Repo):
        def get_all(self, offset=0, limit=50, tenant_key=None, *, all_tenants=False):
            rows, _ = super().get_all(offset, limit, tenant_key, all_tenants=all_tenants)
            return rows, 10_000  # total claims more than exists (rows deleted meanwhile)

    assert len(get_all_pages(Shrunk(5), all_tenants=True)) == 5


def test_ceiling_raises_instead_of_looping() -> None:
    class Endless:
        def get_all(self, offset=0, limit=50, tenant_key=None, *, all_tenants=False):
            return ["x"] * limit, 10**12

    with pytest.raises(PagingCeilingError):
        get_all_pages(Endless(), all_tenants=True, page_size=10, max_pages=5)
