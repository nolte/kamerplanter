"""REQ-016 InvenTree integration router.

The InvenTree integration is tenant-scoped (REQ-024): all endpoints live on the
tenant-scoped router in :mod:`app.api.v1.inventree.tenant_router` under
``/api/v1/t/{tenant_slug}/inventree`` (and equipment under
``/api/v1/t/{tenant_slug}/equipment``). There is deliberately no global
``/api/v1/inventree`` router — a connection, reference or equipment item always
belongs to exactly one tenant.
"""

from app.api.v1.inventree.tenant_router import router

__all__ = ["router"]
