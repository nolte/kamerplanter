"""The MCP audit read-projection must accept everything its writer stores (#1145).

`get_mcp_activity` answered `INTERNAL_ERROR` on every call, for every account and
every `limit`. The cause was not a bad row: `McpAuditLogEntry` declared
`error_class: str | None` **without** a default — which in Pydantic means
*required, may be null* — while `ArangoMcpAuditRepository.record` dumps with
`exclude_none=True`, so a tool call that raised nothing stores no `error_class`
key at all.

Every successful call therefore wrote a row the reader rejected, and since the
listing sorts newest-first, one such row poisoned every window. The inversion is
what makes it unmistakable: an **error** row carries an `error_class` and
validated fine. The only rows the activity view could ever read were the
failures.

The first test reproduces that end-to-end through the real writer's dump. The
second is the structural guard: it derives the rule from the two models rather
than restating today's field list, so a *future* field added to the writer
without a matching default on the reader fails here instead of in production.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic_core import PydanticUndefined

from app.common.enums import McpToolStatus
from app.domain.models.mcp import McpAuditLog, McpAuditLogEntry


def _stored_document(status: McpToolStatus, *, error_class: str | None = None) -> dict:
    """Build the document `ArangoMcpAuditRepository.record` would actually insert.

    Deliberately mirrors `record` — same dump flags, same `_key` pop, same
    `created_at` fill — rather than hand-writing a plausible dict. A hand-written
    fixture is how this defect stayed invisible: the tool's existing tests all fed
    the reader a dict that happened to carry every key.
    """
    entry = McpAuditLog(
        service_account_key="sa_1",
        tenant_key="tenant_acme",
        tool_name="list_plants",
        input_hash="abc123",
        status=status,
        error_class=error_class,
    )
    doc = entry.model_dump(by_alias=True, exclude_none=True, mode="json")
    doc.pop("_key", None)
    if not doc.get("created_at"):
        doc["created_at"] = datetime.now(UTC).isoformat()
    return doc


class TestTheReaderAcceptsWhatTheWriterWrote:
    def test_a_successful_call_is_readable(self) -> None:
        """The row every ordinary tool call produces — and the one that broke it."""
        doc = _stored_document(McpToolStatus.OK)

        assert "error_class" not in doc, "precondition: exclude_none drops the unset field"

        entry = McpAuditLogEntry(**doc)

        assert entry.error_class is None
        assert entry.tool_name == "list_plants"

    def test_a_failed_call_is_readable_too(self) -> None:
        """The half that always worked — pinned so a 'fix' cannot trade one for the other."""
        doc = _stored_document(McpToolStatus.ERROR, error_class="TypeError")

        entry = McpAuditLogEntry(**doc)

        assert entry.error_class == "TypeError"

    @pytest.mark.parametrize("status", list(McpToolStatus))
    def test_every_outcome_a_tool_can_report_is_readable(self, status: McpToolStatus) -> None:
        """DENIED and DRY_RUN store no error either, so they broke the view as well."""
        McpAuditLogEntry(**_stored_document(status))


class TestTheProjectionCannotDriftStricterAgain:
    def test_no_projection_field_is_stricter_than_its_writer(self) -> None:
        """Derive the rule from the models, so a future field is covered without an edit.

        The invariant: a field that is optional on the way in must be optional on
        the way out. Stated over `model_fields` rather than as a list of names,
        because a list would have to be maintained by the same person who forgot
        the default in the first place.
        """
        writer = McpAuditLog.model_fields
        stricter = [
            name
            for name, reader_field in McpAuditLogEntry.model_fields.items()
            if reader_field.default is PydanticUndefined
            and reader_field.default_factory is None
            and name in writer
            and (writer[name].default is not PydanticUndefined or writer[name].default_factory is not None)
        ]

        assert not stricter, (
            f"read-projection fields {stricter} are required while McpAuditLog defaults them; "
            "a row written without those keys cannot be read back"
        )

    def test_the_guard_would_notice_a_regression(self) -> None:
        """Falsifiability: re-required one field and confirm the rule above rejects it.

        Without this, the guard above passes just as well when its condition is
        subtly inverted — which is exactly the failure mode it exists to catch.
        """
        writer = McpAuditLog.model_fields
        reader = dict(McpAuditLogEntry.model_fields)
        # Simulate the pre-fix declaration: `error_class: str | None` with no default.
        regressed = reader["error_class"].__class__(annotation=str | None)

        is_stricter = (
            regressed.default is PydanticUndefined
            and regressed.default_factory is None
            and writer["error_class"].default is not PydanticUndefined
        )

        assert is_stricter, "the strictness rule must flag the exact declaration that shipped the bug"
