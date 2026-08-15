"""A genuine MCP 500 says whether retrying can help (#1164).

Both #1145 defects — a `TypeError` from a missed keyword argument and a
`pydantic.ValidationError` from a schema mismatch — reached the operator as
`INTERNAL_ERROR` plus a bare reference ID and nothing else. Five such IDs were
collected across two tools before anyone could say more than "something is
wrong", and because the markers were identical the two *unrelated* defects read
as one incident. One of them (`assign_nutrient_plan`) was a permanent contract
mismatch that clients retried indefinitely, because nothing in the envelope told
them not to.

What these tests pin is the smallest thing that fixes that, and — just as
important — the three things that must **not** happen:

* the status stays **500**, never 4xx (#970's second horn: our own broken
  assembly is not a client error, and dressing it as one turns an unusable call
  into one the client keeps retrying);
* the exception text never reaches the caller;
* an *unrecognised* failure is called permanent, not transient.
"""

from __future__ import annotations

import pytest

from app.mcp_server.base import (
    INTERNAL_CONTRACT_MISMATCH,
    INTERNAL_UNAVAILABLE,
    McpToolError,
    classify_internal_failure,
    internal_failure_message,
)
from app.mcp_server.dispatcher import ToolDispatcher


class TestClassification:
    @pytest.mark.parametrize(
        "exc",
        [
            TypeError("run() missing 1 required keyword-only argument: 'tenant_key'"),
            ValueError("bad"),
            AttributeError("'NoneType' object has no attribute 'key'"),
            KeyError("species_key"),
        ],
    )
    def test_our_own_broken_assembly_is_permanent(self, exc: BaseException) -> None:
        """The #1145 shape. Retrying cannot fix a wrong call signature."""
        assert classify_internal_failure(exc) == INTERNAL_CONTRACT_MISMATCH

    @pytest.mark.parametrize("exc", [ConnectionError("refused"), TimeoutError("deadline"), OSError("no route")])
    def test_an_unreachable_dependency_is_transient(self, exc: BaseException) -> None:
        assert classify_internal_failure(exc) == INTERNAL_UNAVAILABLE

    def test_an_unrecognised_failure_is_called_permanent(self) -> None:
        """The asymmetry, stated as a test because it is a decision and not an
        accident.

        Calling a transient fault permanent costs one report. Calling a permanent
        fault transient costs an infinite retry loop against a call that can never
        succeed — which is what #1145's clients actually did. So the default is
        the safe-to-be-wrong direction.
        """

        class _ExoticError(Exception):
            pass

        assert classify_internal_failure(_ExoticError()) == INTERNAL_CONTRACT_MISMATCH


class TestTheEnvelope:
    @staticmethod
    def _error(exc: BaseException) -> McpToolError:
        return ToolDispatcher._as_internal_tool_error(exc, "assign_nutrient_plan")

    def test_a_genuine_500_stays_a_500(self) -> None:
        """Not 4xx. This is the whole point of #1164's "what this is not asking
        for" section: reclassifying would have made #1145 quieter and no less
        broken, and an MCP client would have retried a "client error" forever."""
        assert self._error(TypeError("boom")).status_code == 500
        assert self._error(ConnectionError("boom")).status_code == 500

    def test_the_class_and_the_retry_bit_reach_the_caller(self) -> None:
        permanent = self._error(TypeError("boom"))
        transient = self._error(ConnectionError("boom"))

        assert permanent.error_code == INTERNAL_CONTRACT_MISMATCH
        assert permanent.error_details["retryable"] is False
        assert transient.error_code == INTERNAL_UNAVAILABLE
        assert transient.error_details["retryable"] is True

    def test_the_tool_name_is_carried(self) -> None:
        """#1145's two defects were in two tools and looked like one incident.
        The name is what separates them without needing the server log."""
        assert self._error(TypeError("boom")).error_details["tool"] == "assign_nutrient_plan"

    def test_a_reference_id_is_still_issued_and_is_unique_per_call(self) -> None:
        """The ID keeps its job — joining the caller's report to the log line. It
        is minted here rather than by the REST catch-all, because raising a typed
        error means that handler no longer runs; if it were still minted there,
        the caller would quote an ID that appears in no log."""
        first = self._error(TypeError("boom")).error_details["reference_id"]
        second = self._error(TypeError("boom")).error_details["reference_id"]

        assert first.startswith("err_")
        assert first != second

    @pytest.mark.parametrize(
        "exc",
        [
            TypeError("run() missing 1 required keyword-only argument: 'tenant_key'"),
            ValueError("stored value 'Solanum lycopersicum' is not a valid NutrientDemand"),
            ConnectionError("tcp://arangodb:8529 refused"),
        ],
    )
    def test_the_exception_text_never_reaches_the_caller(self, exc: BaseException) -> None:
        """A ``TypeError`` repr names internal symbols; a ``ValidationError`` can
        quote stored field values. Both are in the parametrisation above, with
        payloads that would be visibly wrong to leak."""
        error = self._error(exc)
        serialised = f"{error.message} {error.error_details}"

        assert str(exc) not in serialised
        for fragment in ("tenant_key'", "Solanum", "arangodb:8529"):
            assert fragment not in serialised

    def test_each_class_has_its_own_sentence(self) -> None:
        """Distinct text, so an operator reading only the message still learns the
        one thing the class encodes."""
        permanent = internal_failure_message(INTERNAL_CONTRACT_MISMATCH)
        transient = internal_failure_message(INTERNAL_UNAVAILABLE)

        assert permanent != transient
        assert "not help" in permanent
        assert "may succeed" in transient
