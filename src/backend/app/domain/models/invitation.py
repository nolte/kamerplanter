from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.common.enums import InvitationStatus, InvitationType, TenantRole

#: The most uses one invitation link may grant (REQ-024 AK-07, #2182). The tenant's member
#: limit (AK-64) still decides every single join; this only bounds what one shared link can ask for.
INVITATION_MAX_USES_LIMIT = 100


class Invitation(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    invited_by_user_key: str
    invitation_type: InvitationType = InvitationType.EMAIL
    email: EmailStr | None = None
    role: TenantRole = TenantRole.VIEWER
    token_hash: str
    status: InvitationStatus = InvitationStatus.PENDING
    expires_at: datetime
    #: How many accounts may join with this invitation (REQ-024 AK-07, #2182). An e-mail invitation is
    #: bound to one address and always ``1``; a link may admit up to :data:`INVITATION_MAX_USES_LIMIT`.
    #: A row stored before #2182 carries neither field and reads as single use.
    max_uses: int = Field(default=1, ge=1, le=INVITATION_MAX_USES_LIMIT)
    #: Uses consumed so far. The invitation turns ``accepted`` with the use that reaches ``max_uses``.
    use_count: int = Field(default=0, ge=0)
    #: The account that consumed the **latest** use (for a single-use invitation: the one acceptor).
    accepted_by_user_key: str | None = None
    accepted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _count_the_use_of_a_row_accepted_before_use_count(self) -> Invitation:
        """A row accepted before #2182 stored no ``use_count``; its one use was consumed all the same."""
        if self.use_count == 0 and self.accepted_by_user_key is not None:
            self.use_count = 1
        return self


class InvitationLink(BaseModel):
    invitation_key: str
    token: str
    expires_at: datetime
    #: The link that opens the accept page with ``token`` (#2162) - what the inviter shares.
    accept_url: str = ""
    #: E-mail invitations only: whether the mail left (#2162). ``False`` means the invitation exists
    #: and ``accept_url`` is the only way it reaches the invitee; ``None`` for a link invitation.
    delivered: bool | None = None
    #: How many accounts may join with it (REQ-024 AK-07, #2182); ``1`` for an e-mail invitation.
    max_uses: int = 1
