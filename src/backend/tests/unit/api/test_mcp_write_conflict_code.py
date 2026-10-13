"""REQ-050 §4.0 — a write-write conflict reaches MCP as its own published code (#1458).

``_CONTRACT_ERROR_CODES`` maps Kamerplanter's internal SCREAMING_CASE error codes
onto the lowercase dotted codes the MCP contract publishes. ``WRITE_CONFLICT``
carried no entry, so a recipe that hit the ArangoDB ``1200`` race received the
fallback — the internal code lower-cased — which is not part of the documented
§4.0 set and which a recipe therefore cannot branch on.

The entry is **additive**: no existing code changes meaning. It is deliberately
NOT ``conflict.duplicate``, and that distinction is the point of the test below:
``conflict.duplicate`` says an equivalent record exists (change the input),
``conflict.write`` says a concurrent transaction held the key (re-read and retry
the same call). Published under one code the retry-safe case would be
indistinguishable from the terminal one.
"""

from __future__ import annotations

from app.api.v1.mcp.router import _CONTRACT_ERROR_CODES, _contract_error_code
from app.common.exceptions import DuplicateError, WriteConflictError


def test_a_write_conflict_publishes_the_documented_code():
    assert _contract_error_code(WriteConflictError("care_profiles")) == "conflict.write"


def test_it_is_not_published_as_a_duplicate():
    """The two 409s stay distinguishable on the wire, as they are in the domain."""
    conflict = _contract_error_code(WriteConflictError("care_profiles"))
    duplicate = _contract_error_code(DuplicateError("care_profiles", "plant_key", "p1"))

    assert duplicate == "conflict.duplicate"
    assert conflict != duplicate


def test_the_mapping_is_keyed_on_the_error_code_the_exception_really_carries():
    """The table is a dict of strings; a typo in the key is a silent fallback.

    ``_contract_error_code`` falls back to ``exc.error_code.lower()`` for anything
    unmapped, so a key that does not match the exception's own ``error_code``
    would still return *something* plausible-looking — ``write_conflict`` — and
    only a comparison against the real attribute catches it.
    """
    assert WriteConflictError("care_profiles").error_code in _CONTRACT_ERROR_CODES


def test_the_additive_claim_is_measured_rather_than_asserted_in_prose():
    """Every code that was published before #1458 still publishes the same string."""
    before = {
        "ENTITY_NOT_FOUND": "not_found",
        "FORBIDDEN": "permission.denied",
        "UNAUTHORIZED": "permission.denied",
        "VALIDATION_ERROR": "validation.error",
        "PAYLOAD_TOO_LARGE": "payload.too_large",
        "DUPLICATE_ENTRY": "conflict.duplicate",
        "RATE_LIMIT_EXCEEDED": "rate_limit.exceeded",
    }
    assert {code: _CONTRACT_ERROR_CODES[code] for code in before} == before
