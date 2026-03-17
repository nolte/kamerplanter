from app.common.exceptions import NotFoundError


def verify_tenant_ownership(resource, tenant_key: str, resource_name: str) -> None:
    """Verify that a resource belongs to the given tenant.

    Raises NotFoundError (not ForbiddenError) to avoid information leakage.
    """
    if hasattr(resource, "tenant_key") and resource.tenant_key != tenant_key:
        raise NotFoundError(resource_name, resource.key or "unknown")
