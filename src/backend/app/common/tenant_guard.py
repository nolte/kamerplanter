from app.common.exceptions import NotFoundError


def verify_tenant_ownership(resource, tenant_key: str, resource_name: str) -> None:
    """Verify that a resource belongs to the given tenant.

    Raises NotFoundError (not ForbiddenError) to avoid information leakage.
    """
    if hasattr(resource, "tenant_key") and resource.tenant_key != tenant_key:
        raise NotFoundError(resource_name, resource.key or "unknown")


def verify_tenant_read_access(resource, tenant_key: str, resource_name: str) -> None:
    """Grant read access to a hybrid-catalog resource.

    Like :func:`verify_tenant_ownership`, but additionally admits globally
    seeded catalog entries (empty ``tenant_key``) alongside the caller's own
    rows — mirroring the hybrid-catalog union the list queries emit. A foreign
    tenant's rows still raise NotFoundError. Write ownership must stay with
    :func:`verify_tenant_ownership` (or an explicit ``is_system`` guard); this
    helper only widens *read* visibility.
    """
    if not tenant_key or not hasattr(resource, "tenant_key"):
        return
    if resource.tenant_key not in ("", tenant_key):
        raise NotFoundError(resource_name, resource.key or "unknown")
