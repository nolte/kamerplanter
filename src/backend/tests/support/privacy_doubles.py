"""Test doubles for the REQ-025 privacy repositories.

One shared double rather than three hand-rolled MagicMocks, because the thing
these tests have to get right is the *write semantics*, and a double that gets
them wrong certifies nothing. ``ArangoDataExportRepository`` is in **merge**
mode (:attr:`BaseArangoRepository._update_is_full_replace` is ``False``), so
``update`` drops a field the caller set to ``None`` while ``update_fields``
writes it (``keep_none=True``). A `MagicMock` has neither behaviour: it accepts
any call and hands back a `MagicMock`, so a write that could never land in
production reads as a success here.
"""

from __future__ import annotations

from typing import Any

from app.domain.models.privacy import DataExportRequest, ErasureRequest


class FakeDataExportRepo:
    """In-memory stand-in for :class:`IDataExportRepository`.

    Mirrors the two write modes:

    * :meth:`update` takes a full model and **drops** ``None`` values, like a
      merge-mode ``_update_doc``.
    * :meth:`update_fields` merges exactly the named fields and **keeps**
      ``None``.

    It refuses a field the model does not declare. The real method would happily
    persist one — and it would then never be read back, which is a silent
    no-op. Failing loudly here is the point of having a double at all.
    """

    def __init__(self, export: DataExportRequest | None = None) -> None:
        self.stored: dict[str, DataExportRequest] = {}
        #: How often the full-model `update` was used — the write that cannot
        #: clear a field and can resurrect a record (#1662 SCR-005).
        self.full_model_updates = 0
        if export is not None and export.key:
            self.stored[export.key] = export

    # ── reads ──────────────────────────────────────────────────────
    def get_by_key(self, key: str) -> DataExportRequest | None:
        return self.stored.get(key)

    def get_or_raise(self, key: str) -> DataExportRequest:
        from app.common.exceptions import NotFoundError

        export = self.stored.get(key)
        if export is None:
            raise NotFoundError("DataExportRequest", key)
        return export

    def list_by_user(self, user_key: str) -> list[DataExportRequest]:
        return [e for e in self.stored.values() if e.user_key == user_key]

    def list_active_by_user(self, user_key: str) -> list[DataExportRequest]:
        return [e for e in self.list_by_user(user_key) if e.status in ("pending", "processing")]

    def list_stale_pending(self, cutoff_iso: str) -> list[DataExportRequest]:
        return [e for e in self.stored.values() if e.status == "pending"]

    # ── writes ─────────────────────────────────────────────────────
    def create(self, export: DataExportRequest) -> DataExportRequest:
        key = export.key or f"exp-{len(self.stored) + 1}"
        export.key = key
        self.stored[key] = export
        return export

    def update(self, key: str, export: DataExportRequest) -> DataExportRequest:
        """Merge-mode full-model write: every ``None`` is dropped."""
        self.full_model_updates += 1
        current = self.stored.setdefault(key, export)
        for field in type(export).model_fields:
            value = getattr(export, field)
            if value is None:
                continue
            setattr(current, field, value)
        return current

    def update_fields(self, key: str, fields: dict[str, Any]) -> DataExportRequest:
        """Named-field write: ``None`` lands (``keep_none=True``)."""
        current = self.stored[key]
        for field in fields:
            if field not in type(current).model_fields:
                msg = (
                    f"'{field}' is not a field of DataExportRequest. The real repository would "
                    "persist it and never read it back, which is a silent no-op."
                )
                raise AttributeError(msg)
        # Re-validated, not `setattr`-ed: the real method writes the dict to
        # ArangoDB and returns the *re-parsed* document, so an ISO string handed
        # in comes back as a `datetime`. A double that stored the string would
        # let a serialisation mistake pass here and fail in production.
        merged = DataExportRequest.model_validate({**current.model_dump(), **fields})
        for field in type(current).model_fields:
            setattr(current, field, getattr(merged, field))
        return current

    def increment_download_count(self, key: str) -> DataExportRequest:
        current = self.stored[key]
        current.download_count += 1
        return current

    def delete(self, key: str) -> bool:
        return self.stored.pop(key, None) is not None

    def start_processing(
        self, key: str, *, from_statuses: list[str], fields: dict[str, Any]
    ) -> DataExportRequest | None:
        """The real conditional write: only from one of *from_statuses*."""
        current = self.stored.get(key)
        if current is None or current.status not in from_statuses:
            return None
        return self.update_fields(key, {**fields, "status": "processing"})

    def complete_if_processing(self, key: str, fields: dict[str, Any]) -> DataExportRequest | None:
        """The real conditional write: only while ``processing``."""
        current = self.stored.get(key)
        if current is None or current.status != "processing":
            return None
        return self.update_fields(key, fields)

    def fail_open_for_user(self, user_key: str, reason: str) -> int:
        open_exports = [e for e in self.list_by_user(user_key) if e.status in ("pending", "processing")]
        for export in open_exports:
            export.status = "failed"
            export.error_message = reason
        return len(open_exports)

    def list_expiry_due(self, now_iso: str) -> list[DataExportRequest]:
        """The real AQL filter: ``completed`` past expiry, or ``expired`` still pointing at a bundle."""
        from datetime import datetime

        now = datetime.fromisoformat(now_iso)
        return [
            e
            for e in self.stored.values()
            if (e.status == "completed" and e.expires_at is not None and e.expires_at < now)
            or (e.status == "expired" and e.file_path is not None)
        ]


class FakeErasureRepo:
    """In-memory :class:`IErasureRepository` with the real filters and write semantics (#1767).

    ``find_active_for_user``, ``list_due_for_hard_delete`` and
    ``claim_for_run`` mirror the AQL of ``ArangoErasureRepository`` — the
    claim refuses a ``completed`` request and one a *fresh* ``in_progress`` run
    holds. ``update_fields`` refuses a field the model does not declare and
    re-parses the merged document, as the driver round-trip does.
    """

    def __init__(self, *requests: ErasureRequest) -> None:
        self.stored: dict[str, ErasureRequest] = {}
        for request in requests:
            self.create(request)

    def create(self, erasure: ErasureRequest) -> ErasureRequest:
        erasure.key = erasure.key or f"er-{len(self.stored) + 1}"
        self.stored[erasure.key] = erasure
        return erasure

    def create_with_key(self, erasure: ErasureRequest, key: str) -> ErasureRequest:
        from app.common.exceptions import DuplicateError

        if key in self.stored:
            raise DuplicateError("erasure_requests", "_key", key)
        erasure.key = key
        self.stored[key] = erasure
        return erasure

    def get_by_key(self, key: str) -> ErasureRequest | None:
        return self.stored.get(key)

    def list_by_user(self, user_key: str) -> list[ErasureRequest]:
        return [e for e in self.stored.values() if e.user_key == user_key]

    def find_active_for_user(self, user_key: str) -> ErasureRequest | None:
        open_states = ("scheduled", "in_progress", "partially_completed")
        return next((e for e in self.list_by_user(user_key) if e.status in open_states), None)

    def list_due_for_hard_delete(self, now_iso: str, stale_before_iso: str) -> list[ErasureRequest]:
        from datetime import datetime

        now = datetime.fromisoformat(now_iso)
        stale_before = datetime.fromisoformat(stale_before_iso)
        due = []
        for e in self.stored.values():
            if e.hard_delete_scheduled_at is None or e.hard_delete_scheduled_at > now:
                continue
            if e.status in ("scheduled", "partially_completed") or (
                e.status == "in_progress" and (e.updated_at is None or e.updated_at <= stale_before)
            ):
                due.append(e)
        return due

    def claim_for_run(self, key: str, *, now_iso: str, stale_before_iso: str) -> ErasureRequest | None:
        from datetime import datetime

        e = self.stored.get(key)
        if e is None or e.status == "completed":
            return None
        stale_before = datetime.fromisoformat(stale_before_iso)
        if e.status == "in_progress" and e.updated_at is not None and e.updated_at > stale_before:
            return None
        return self.update_fields(key, {"status": "in_progress", "last_attempt_at": now_iso, "updated_at": now_iso})

    def update_fields(self, key: str, fields: dict[str, Any]) -> ErasureRequest:
        current = self.stored[key]
        for field in fields:
            if field not in ErasureRequest.model_fields:
                msg = f"'{field}' is not a field of ErasureRequest; the real write would be a silent no-op."
                raise AttributeError(msg)
        merged = ErasureRequest.model_validate({**current.model_dump(by_alias=True), **fields})
        for field in ErasureRequest.model_fields:
            setattr(current, field, getattr(merged, field))
        return current


class RecordingErasureExecutor:
    """In-memory stand-in for :class:`IErasureExecutor` (#1645).

    Returns the report shape ``ArangoErasureExecutor`` produces for a run over
    the whole plan: one outcome per ArangoDB step (``affected`` may be ``0``),
    and the non-ArangoDB phases listed as ``delegated``. The delegated set is
    the real executor's own constant, not a copy, so this double cannot claim a
    step the real executor would hand off — or the reverse.

    ``fail_with`` makes the run raise instead, as an aborted transaction does —
    for every subject, or only for those in ``fail_for``. ``drop`` removes
    named steps from the report, to model a run that did not account for a
    declared step.
    """

    def __init__(
        self,
        *,
        fail_with: BaseException | None = None,
        fail_for: frozenset[str] | None = None,
        drop: tuple[str, ...] = (),
    ) -> None:
        self.runs: list[tuple[str, str | None]] = []
        self._fail_with = fail_with
        self._fail_for = fail_for
        self._drop = drop

    def run_erasure_plan(self, plan, *, tombstone, executors=None):  # type: ignore[no-untyped-def]
        from app.data_access.arango.erasure_executor import _DELEGATED_PHASE_EXECUTORS
        from app.domain.models.privacy import ErasureExecutionReport, ErasureStepOutcome

        self.runs.append((plan.user_key, tombstone))
        if self._fail_with is not None and (self._fail_for is None or plan.user_key in self._fail_for):
            raise self._fail_with
        report = ErasureExecutionReport()
        for step in plan.steps:
            if executors is not None and step.executor not in executors:
                continue
            if step.collection in self._drop:
                continue
            if step.kind == "phase" and step.executor in _DELEGATED_PHASE_EXECUTORS:
                report.delegated.append(step.collection)
            else:
                report.steps.append(
                    ErasureStepOutcome(collection=step.collection, kind=step.kind, executor=step.executor)
                )
        return report
