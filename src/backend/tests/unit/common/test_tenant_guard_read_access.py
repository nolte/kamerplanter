"""``verify_tenant_read_access`` widens read visibility to the hybrid catalog.

Unlike the strict ``verify_tenant_ownership``, the read-access guard admits
globally seeded catalog entries (empty ``tenant_key``) in addition to the
caller's own rows, while still hiding a foreign tenant's rows behind
``NotFoundError``. This is what lets the detail/instantiate/duplicate routes
work for the system templates the list query restores (SEC-B4).
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


def test_empty_caller_tenant_key_skips_check() -> None:
    # System-context reads (no tenant_key) stay unfiltered, like the list query.
    verify_tenant_read_access(_res("tenant_b"), "", "WorkflowTemplate")


def test_resource_without_tenant_key_is_admitted() -> None:
    verify_tenant_read_access(SimpleNamespace(key="r1"), "tenant_a", "WorkflowTemplate")
