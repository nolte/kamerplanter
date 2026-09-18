from datetime import datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """One entry of the NFR-006 ``details`` list.

    ``field``/``reason``/``code`` describe *where* and *why*. ``entity`` is the
    optional structured name of the missing resource, set by ``NotFoundError`` and
    every subclass of it (#1437): two 404s on the same route — the parent is gone
    versus the child is gone — otherwise carry an identical ``ENTITY_NOT_FOUND``
    and differ only in the English ``message``, which a client may not parse.
    """

    field: str | None = None
    reason: str
    code: str
    entity: str | None = None


class ErrorResponse(BaseModel):
    error_id: str = Field(description="Unique tracking ID (format: err_<uuid4>)")
    error_code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error description")
    details: list[ErrorDetail] = Field(default_factory=list)
    timestamp: datetime
    path: str
    method: str
