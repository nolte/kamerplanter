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

from app.domain.models.privacy import DataExportRequest


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
        self.expire_old_result: list[DataExportRequest] = []
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

    def expire_old(self, now_iso: str) -> list[DataExportRequest]:
        return self.expire_old_result
