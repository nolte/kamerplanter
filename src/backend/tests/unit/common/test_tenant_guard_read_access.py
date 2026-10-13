"""``verify_tenant_read_access`` widens read visibility to the hybrid catalog.

Unlike the strict ``verify_tenant_ownership``, the read-access guard admits
globally seeded catalog entries (empty ``tenant_key``) in addition to the
caller's own rows, while still hiding a foreign tenant's rows behind
``NotFoundError``. This is what lets the detail/instantiate/duplicate routes
work for the system templates the list query restores (SEC-B4).

#2107 (MT-010): the guard used to *return* for an empty caller tenant and for a
resource without a ``tenant_key`` attribute. Both were silent passes — an empty
tenant (a service account without a header, an internal caller that forgot it)
read any tenant's row, and a model that never carried the field was "admitted"
without anything being compared. Both now fail closed.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.common.exceptions import NotFoundError
from app.common.tenant_guard import verify_tenant_read_access


def _res(tenant_key: str, key: str = "r1") -> SimpleNamespace:
    return SimpleNamespace(tenant_key=tenant_key, key=key)


def test_global_resource_is_readable_by_any_tenant() -> None:
    # Empty tenant_key = globally seeded catalog entry — must be admitted.
    verify_tenant_read_access(_res(""), "tenant_a", "WorkflowTemplate")


def test_own_resource_is_readable() -> None:
    verify_tenant_read_access(_res("tenant_a"), "tenant_a", "WorkflowTemplate")


def test_foreign_tenant_resource_raises_not_found() -> None:
    with pytest.raises(NotFoundError):
        verify_tenant_read_access(_res("tenant_b"), "tenant_a", "WorkflowTemplate")


@pytest.mark.parametrize("owner", ["tenant_b", ""])
def test_an_empty_caller_tenant_is_refused(owner: str) -> None:
    """#2107: ``""`` is no tenant, not "every tenant" — a foreign row and a global one alike."""
    with pytest.raises(NotFoundError):
        verify_tenant_read_access(_res(owner), "", "WorkflowTemplate")


def test_a_resource_without_tenant_key_is_a_programming_error() -> None:
    """#2107: a model without the field cannot be ownership-checked; saying so beats admitting it."""
    with pytest.raises(TypeError):
        verify_tenant_read_access(SimpleNamespace(key="r1"), "tenant_a", "WorkflowTemplate")
