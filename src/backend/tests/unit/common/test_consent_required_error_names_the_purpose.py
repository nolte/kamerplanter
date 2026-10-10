"""``CONSENT_REQUIRED`` names the missing purpose machine-readably (REQ-031 §5.1).

One route can refuse for either of two purposes — the knowledge question asks
for ``ai_knowledge_question`` and, with plant context, ``ai_tenant_data_access``
— and the client has to ask for exactly the one that is missing. Until now the
key stood only in the English ``message``, which a client may not parse. The
key is added as ``details[0].purpose``; ``field`` keeps its value.
"""

from __future__ import annotations

from app.common.error_schemas import ErrorDetail, ErrorResponse
from app.common.exceptions import ConsentRequiredError


def test_the_detail_carries_the_purpose_key() -> None:
    error = ConsentRequiredError("ai_knowledge_question")

    assert error.status_code == 403
    assert error.error_code == "CONSENT_REQUIRED"
    assert error.details == [
        {
            "field": "consent",
            "reason": "Grant consent for 'ai_knowledge_question' to use this feature.",
            "code": "CONSENT_REQUIRED",
            "purpose": "ai_knowledge_question",
        }
    ]
    assert error.purpose == "ai_knowledge_question"


def test_the_documented_envelope_keeps_the_purpose() -> None:
    """The typed envelope model (``error_schemas``) must not drop the key it now carries.

    The OpenAPI document's error envelope (``openapi_responses.ErrorResponse``)
    types ``details`` as free objects and carries the key without a change.
    """
    detail = ErrorDetail.model_validate(ConsentRequiredError("ai_cloud_processing").details[0])

    assert detail.purpose == "ai_cloud_processing"
    assert "purpose" in ErrorResponse.model_json_schema()["$defs"]["ErrorDetail"]["properties"]
