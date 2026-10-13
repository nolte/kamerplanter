"""``verify_tenant_ownership`` fails closed on the two inputs it used to wave through (#2107, MT-010).

``hasattr(resource, "tenant_key") and resource.tenant_key != tenant_key`` made the
guard a no-op twice over:

* a resource **without** a ``tenant_key`` attribute (``Sensor`` — tenant-resolved
  through its parent) passed without anything being compared;
* an **empty** caller tenant matched every legacy or global row whose own
  ``tenant_key`` is ``""`` — the ambiguity the audit names for service accounts
  without a header, API keys with a foreign scope, and internal callers.

A model without the field is a programming error (``TypeError``), an empty tenant
is "no tenant", answered like a foreign row (``NotFoundError`` — no oracle).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.common.exceptions import NotFoundError
from app.common.tenant_guard import verify_tenant_ownership
from app.domain.models.sensor import Sensor


def _res(tenant_key: str, key: str = "r1") -> SimpleNamespace:
    return SimpleNamespace(tenant_key=tenant_key, key=key)


def test_an_own_resource_passes() -> None:
    verify_tenant_ownership(_res("t1"), "t1", "Tank")


@pytest.mark.parametrize("owner", ["t2", ""])
def test_a_foreign_or_global_resource_is_not_found(owner: str) -> None:
    with pytest.raises(NotFoundError):
        verify_tenant_ownership(_res(owner), "t1", "Tank")


@pytest.mark.parametrize("owner", ["t1", ""])
def test_an_empty_caller_tenant_is_not_found(owner: str) -> None:
    """``""`` used to equal a legacy row's ``""`` and pass."""
    with pytest.raises(NotFoundError):
        verify_tenant_ownership(_res(owner), "", "Tank")


def test_a_model_without_the_field_is_a_type_error() -> None:
    """The audit's own example: a ``Sensor`` carries no tenant; the guard used to return."""
    sensor = Sensor(_key="s1", name="EC", metric_type="ec_ms", tank_key="tank-1")
    with pytest.raises(TypeError):
        verify_tenant_ownership(sensor, "t1", "Sensor")


def test_the_not_found_names_the_resource_and_key() -> None:
    with pytest.raises(NotFoundError) as caught:
        verify_tenant_ownership(_res("t2", key="tank-9"), "t1", "Tank")
    assert "tank-9" in str(caught.value)
