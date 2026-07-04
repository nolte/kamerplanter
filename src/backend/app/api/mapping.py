"""Domain-model to API-response mapping helpers (AP-18a / DUP-B4).

The trivial idiom ``Resp(key=m.key or "", **m.model_dump(exclude={"key"}))`` was
copied across ~30 routers. Mapping a domain model onto an API response schema is
API-layer concern, so the shared helper lives here.
"""

from typing import Any

from pydantic import BaseModel


def to_response[TResponse: BaseModel](
    model: BaseModel,
    response_cls: type[TResponse],
    **overrides: Any,
) -> TResponse:
    """Map a domain model onto an API response schema.

    Replaces the copied ``Resp(key=m.key or "", **m.model_dump(exclude={"key"}))``
    idiom. The ``key`` field is coalesced to ``""`` when absent (matching the
    previous behaviour). Only fields declared on ``response_cls`` are passed
    through — this is explicit where the old idiom relied on Pydantic's implicit
    ``extra='ignore'`` and survives a future switch to ``extra='forbid'``.
    ``overrides`` win over the dumped values (e.g. computed fields).
    """

    data = model.model_dump()
    data["key"] = data.get("key") or ""
    data.update(overrides)
    allowed = response_cls.model_fields.keys()
    return response_cls(**{key: value for key, value in data.items() if key in allowed})
