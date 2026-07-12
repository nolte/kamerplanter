"""REQ-036 KI-Diagnose-Assistent — router package entry point.

The real endpoints are tenant-scoped and live in :mod:`tenant_router`; they are
mounted under ``/api/v1/t/{tenant_slug}/diagnosis`` by the tenant-scoped router.
This module re-exports the tenant router for discoverability.
"""

from app.api.v1.diagnose.tenant_router import router as tenant_router

__all__ = ["tenant_router"]
