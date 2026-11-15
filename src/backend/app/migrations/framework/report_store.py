"""Persisted reports of the privacy migrations (spec/privacy/09 §2, PRIV-701/PRIV-702).

A migration that declares a :attr:`~app.migrations.framework.base.Migration.kind` has every
report it returns — dry run and real run — written to ``migration_reports``: the operator's proof
of what a privacy correction found and did, kept beside the release record (PRIV-704).

**The redaction filter.** The collection is a platform collection that holds *no personal data*
(``TenantErasureEngine.NOT_TENANT_SCOPED``), so a report passes :func:`redact_details` before it is
stored or written out. The filter keeps only a fixed shape:

* counts (``int``) and flags (``bool``);
* a ``status`` out of :data:`REPORT_STATUSES`;
* identifiers — collection/field names, bucket names, tenant **keys** and sample **row** keys —
  in the places the shape names, and only when they look like an identifier: no blank, no
  tombstone of either generation, not the erasure marker, nothing longer than an ArangoDB key;
* at most :data:`MAX_SAMPLES_PER_BUCKET` sample row keys per bucket.

Everything else — an unknown key (``user_key``, ``display_name``…), a free-text value, a tombstone —
is dropped and counted in ``redacted_entries``. Dropping rather than raising: a report is
evidence, and a migration that already wrote its data must not fail the boot over a field its
report should not have carried. The test that pins the allowed key set is
``tests/unit/migrations/framework/test_report_store.py`` (TA-701a).

What the filter cannot tell apart: an account key placed where the shape expects a tenant key or a
row key — both are opaque ArangoDB keys. The shape keeps account keys out by having no place for
them; a migration that put one under ``tenants_done`` would get it through. That is why the shape
is closed (a key the filter does not know is dropped) rather than open with a deny list.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final

import structlog
from arango.database import StandardDatabase

from app.data_access.arango.collections import MIGRATION_REPORTS
from app.domain.models.privacy import ANONYMIZED_MARKER, is_tombstone
from app.migrations.framework.report import MigrationReport

if TYPE_CHECKING:
    from app.migrations.framework.base import Migration

logger = structlog.get_logger()

#: The ``details.status`` values a privacy migration reports (spec/privacy PRIV-718).
REPORT_STATUSES: Final = frozenset({"dry_run", "applied", "partial", "verify_failed", "precondition_unmet"})

#: The phases a privacy migration reports (spec/privacy PRIV-718).
REPORT_PHASES: Final = ("precheck", "dry_run", "apply", "verify", "monitor")

#: PRIV-701: at most this many sample row keys per bucket.
MAX_SAMPLES_PER_BUCKET: Final = 25

#: An identifier the report may carry: a collection or field name (``garden_plan_audit.user_key``),
#: a bucket name, a tenant key, a row key. ArangoDB keys are at most 254 bytes; a space, ``@`` or
#: any other character a display name or an e-mail address needs is outside the set.
_IDENTIFIER: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.:\-]{0,253}$")

# ── the closed shape ────────────────────────────────────────────────
# Each token says what a value at that place may be; a dict says which keys may appear.

_COUNT: Final = "count"  # non-negative int, never a bool
_FLAG: Final = "flag"  # bool
_STATUS: Final = "status"  # one of REPORT_STATUSES
_IDENT: Final = "identifier"  # one identifier
_IDENT_LIST: Final = "identifier_list"  # list of identifiers
_COUNT_MAP: Final = "count_map"  # {identifier: count | {identifier: count}}
_SAMPLE_MAP: Final = "sample_map"  # {identifier: [identifier, ...] ≤ MAX_SAMPLES_PER_BUCKET}

_PHASE_SHAPE: Final[dict[str, Any]] = {
    "precheck": {"ok": _FLAG, "unmet": _IDENT_LIST, "candidates": _COUNT_MAP},
    "dry_run": {"would_change": _COUNT_MAP},
    "apply": {"tenants_done": _IDENT_LIST, "tenants_failed": _IDENT_LIST, "changed": _COUNT_MAP},
    "verify": {"residual": _COUNT_MAP},
    "monitor": {"handed_to": _IDENT},
}

#: The allowed key set of ``details`` (TA-701a).
DETAILS_SHAPE: Final[dict[str, Any]] = {
    "status": _STATUS,
    "phases": _PHASE_SHAPE,
    "buckets": _COUNT_MAP,
    "samples": _SAMPLE_MAP,
}


def _is_identifier(value: object) -> bool:
    return (
        isinstance(value, str)
        and _IDENTIFIER.fullmatch(value) is not None
        and not is_tombstone(value)
        and value != ANONYMIZED_MARKER
    )


def _as_mapping(value: object) -> Mapping[str, Any] | None:
    """*value* as a mapping, or ``None`` when it is not one."""
    return value if isinstance(value, Mapping) else None


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


class _Redactor:
    """Walks a ``details`` payload against :data:`DETAILS_SHAPE`, keeping what fits and counting what does not."""

    def __init__(self) -> None:
        self.dropped = 0

    def walk(self, value: object, shape: object) -> tuple[bool, Any]:
        """``(kept, value)`` — the redacted value, or ``kept=False`` when nothing of it may stay."""
        if isinstance(shape, dict):
            return self._mapping(value, shape)
        if shape == _COUNT:
            return self._leaf(_is_count(value), value)
        if shape == _FLAG:
            return self._leaf(isinstance(value, bool), value)
        if shape == _STATUS:
            return self._leaf(isinstance(value, str) and value in REPORT_STATUSES, value)
        if shape == _IDENT:
            return self._leaf(_is_identifier(value), value)
        if shape == _IDENT_LIST:
            return self._identifier_list(value, cap=None)
        if shape == _COUNT_MAP:
            return self._count_map(value)
        if shape == _SAMPLE_MAP:
            return self._sample_map(value)
        self.dropped += 1  # pragma: no cover - the shape above names every token
        return False, None

    def _leaf(self, ok: bool, value: object) -> tuple[bool, Any]:
        if not ok:
            self.dropped += 1
        return ok, value if ok else None

    def _mapping(self, value: object, shape: Mapping[str, Any]) -> tuple[bool, Any]:
        mapping = _as_mapping(value)
        if mapping is None:
            self.dropped += 1
            return False, None
        out: dict[str, Any] = {}
        for key, item in mapping.items():
            if key not in shape:
                self.dropped += 1
                continue
            kept, redacted = self.walk(item, shape[key])
            if kept:
                out[key] = redacted
        return True, out

    def _identifier_list(self, value: object, *, cap: int | None) -> tuple[bool, Any]:
        if not isinstance(value, list | tuple):
            self.dropped += 1
            return False, None
        kept = [item for item in value if _is_identifier(item)]
        self.dropped += len(value) - len(kept)
        if cap is not None and len(kept) > cap:
            self.dropped += len(kept) - cap
            kept = kept[:cap]
        return True, kept

    def _count_map(self, value: object) -> tuple[bool, Any]:
        mapping = _as_mapping(value)
        if mapping is None:
            self.dropped += 1
            return False, None
        out: dict[str, Any] = {}
        for key, item in mapping.items():
            if not _is_identifier(key):
                self.dropped += 1
                continue
            if _is_count(item):
                out[key] = item
            elif _as_mapping(item) is not None:
                nested: Mapping[str, Any] = item  # a Mapping, checked on the line above
                inner = {k: v for k, v in nested.items() if _is_identifier(k) and _is_count(v)}
                self.dropped += len(nested) - len(inner)
                out[key] = inner
            else:
                self.dropped += 1
        return True, out

    def _sample_map(self, value: object) -> tuple[bool, Any]:
        mapping = _as_mapping(value)
        if mapping is None:
            self.dropped += 1
            return False, None
        out: dict[str, Any] = {}
        for key, item in mapping.items():
            if not _is_identifier(key):
                self.dropped += 1
                continue
            kept, samples = self._identifier_list(item, cap=MAX_SAMPLES_PER_BUCKET)
            if kept:
                out[key] = samples
        return True, out


def redact_details(details: Mapping[str, Any]) -> tuple[dict[str, Any], int]:
    """``(redacted, dropped)`` — *details* reduced to :data:`DETAILS_SHAPE`, and how many entries went."""
    redactor = _Redactor()
    _kept, redacted = redactor.walk(details, DETAILS_SHAPE)
    return (redacted if isinstance(redacted, dict) else {}), redactor.dropped


def report_document(
    migration: Migration, report: MigrationReport, *, recorded_at: datetime | None = None
) -> dict[str, Any]:
    """The redacted, JSON-ready form of *report* — what ``migration_reports`` stores and ``--report-out`` writes."""
    redacted: tuple[dict[str, Any], int] = redact_details(report.details)
    details: dict[str, Any] = redacted[0]
    dropped: int = redacted[1]
    return {
        "version": report.version,
        "name": report.name,
        "kind": migration.kind,
        "dry_run": report.dry_run,
        "scanned": report.scanned,
        "changed": report.changed,
        "duration_ms": report.duration_ms,
        "precondition_unmet": report.precondition_unmet,
        "incomplete": report.incomplete,
        "status": details.get("status"),
        "details": details,
        "redacted_entries": dropped,
        "recorded_at": (recorded_at or datetime.now(UTC)).isoformat(),
    }


def persist_report(db: StandardDatabase, migration: Migration, report: MigrationReport) -> dict[str, Any]:
    """Store the redacted *report* in ``migration_reports``; return the stored document.

    A new document per run (``<version>-<uuid>``): a dry run and the real run of the same version
    are two pieces of evidence, and a retried partial run is a third.
    """
    document = report_document(migration, report)
    document["_key"] = f"{report.version}-{uuid.uuid4().hex}"
    db.collection(MIGRATION_REPORTS).insert(document)
    if document["redacted_entries"]:
        logger.warning(
            "migration_report_redacted",
            version=report.version,
            name=report.name,
            redacted_entries=document["redacted_entries"],
        )
    return document
