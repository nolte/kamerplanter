"""REQ-029 KI-Bilderkennung router.

The identification endpoints are tenant-scoped and mounted under
/api/v1/t/{tenant_slug}/identification/ via ``tenant_router``. This module
re-exports that router so the aggregation point can import it consistently.
"""

from app.api.v1.recognition.tenant_router import router as tenant_recognition_router

__all__ = ["tenant_recognition_router"]
