"""The two tenant checks a service runs on a document it loaded by key.

Both fail **closed** (#2107, MT-010). They used to return silently in two cases,
and each silent return was a guard that did not run:

* a resource **without** a ``tenant_key`` attribute — nothing was compared, the
  caller read the absence of an exception as "owned". A model that carries no
  tenant of its own (``Sensor``, ``Location``, ``Slot``) is tenant-resolved through
  its parent, and handing it to these checks is a programming error: ``TypeError``.
* an **empty** caller tenant — ``""`` matched every legacy or global row whose own
  ``tenant_key`` is ``""`` (ownership), or skipped the check entirely (read access).
  ``""`` is what the resolver yields for a service account without a header or an
  API key with a foreign scope; it means "no tenant", never "every tenant", so it
  is answered like a foreign row: ``NotFoundError`` (no existence oracle).

A system-context caller that genuinely needs every tenant's row does not pass an
empty tenant here; it reads through a repository method that says so
(``all_tenants=True``) and calls neither check.
"""

from typing import Any

from app.common.exceptions import NotFoundError


def _owner_of(resource: Any, resource_name: str) -> str:
    if not hasattr(resource, "tenant_key"):
        raise TypeError(f"{resource_name} carries no tenant_key; check its parent's ownership instead (#2107)")
    return resource.tenant_key or ""


def verify_tenant_ownership(resource: Any, tenant_key: str, resource_name: str) -> None:
    """Verify that a resource belongs to the given tenant.

    Raises NotFoundError (not ForbiddenError) to avoid information leakage — for a
    foreign row, a global row (``tenant_key == ""``) and an empty caller tenant
    alike. Raises TypeError for a resource that carries no ``tenant_key`` at all.
    """
    owner = _owner_of(resource, resource_name)
    if not tenant_key or owner != tenant_key:
        raise NotFoundError(resource_name, resource.key or "unknown")


def verify_tenant_read_access(resource: Any, tenant_key: str, resource_name: str) -> None:
    """Grant read access to a hybrid-catalog resource.

    Like :func:`verify_tenant_ownership`, but additionally admits globally
    seeded catalog entries (empty or absent ``tenant_key``) alongside the caller's
    own rows — mirroring the hybrid-catalog union the list queries emit. A foreign
    tenant's rows, and any row for an empty caller tenant, raise NotFoundError.
    Write ownership must stay with :func:`verify_tenant_ownership` (or an explicit
    ``is_system`` / shared-row guard); this helper only widens *read* visibility.
    """
    owner = _owner_of(resource, resource_name)
    if not tenant_key or owner not in ("", tenant_key):
        raise NotFoundError(resource_name, resource.key or "unknown")
