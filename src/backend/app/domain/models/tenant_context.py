from pydantic import BaseModel

from app.common.enums import TenantRole


class TenantContext(BaseModel):
    tenant_key: str
    tenant_slug: str
    user_key: str
    role: TenantRole

    @property
    def is_admin(self) -> bool:
        return self.role == TenantRole.ADMIN

    @property
    def can_edit(self) -> bool:
        return self.role in (TenantRole.ADMIN, TenantRole.GROWER)
