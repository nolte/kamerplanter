"""In-memory double of the bed-template repository (REQ-053 WP 7.8, #2474).

Keeps the two kinds of row the way ``ArangoBedTemplateRepository`` does - a tenant's own and the system ones
(``tenant_key is None``) - and applies the same rules: a read admits exactly those two arms, a write names the
row's owner and matches on it. Shared by the unit tier and the API tier.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.common.exceptions import NotFoundError
from app.domain.interfaces.bed_template_repository import IBedTemplateRepository
from app.domain.models.bed_template import BedTemplate


class FakeTemplates(IBedTemplateRepository):
    def __init__(self) -> None:
        self.templates: dict[str, BedTemplate] = {}
        self.bed_types: dict[str, bool] = {"bed": True, "raised_bed": True, "planter": True, "greenhouse": False}
        #: task template key -> tenant ("" = global).
        self.task_templates: dict[str, str] = {}
        self.writes: list[str] = []
        self._next = 0

    def add(self, template: BedTemplate) -> BedTemplate:
        self.templates[template.key or ""] = template
        return template

    def _visible(self, template: BedTemplate | None, tenant_key: str) -> BedTemplate | None:
        if template is None or not tenant_key:
            return None
        return template if template.tenant_key in (None, tenant_key) else None

    def list_visible(self, *, tenant_key, offset, limit):
        found = sorted(
            (t for t in self.templates.values() if self._visible(t, tenant_key)),
            key=lambda t: (t.name, t.key or ""),
        )
        return found[offset : offset + limit]

    def get_visible_by_key(self, key, *, tenant_key):
        return self._visible(self.templates.get(key), tenant_key)

    def visible_keys(self, keys, *, tenant_key):
        return {key for key in keys if self._visible(self.templates.get(key), tenant_key)}

    def count_owned(self, *, tenant_key):
        return sum(1 for t in self.templates.values() if t.tenant_key == tenant_key)

    def create_template(self, template: BedTemplate) -> BedTemplate:
        self._next += 1
        stored = template.model_copy(update={"key": f"bt_{self._next}", "created_at": datetime.now(UTC)})
        self.writes.append(f"create:{stored.key}")
        return self.add(stored)

    def update_template(self, key, fields: dict[str, Any], *, owner_tenant_key):
        stored = self.templates.get(key)
        if stored is None or stored.tenant_key != owner_tenant_key:
            raise NotFoundError("BedTemplate", key)
        data = {**stored.model_dump(by_alias=True), **fields}
        data = {name: value for name, value in data.items() if value is not None or name == "_key"}
        updated = BedTemplate(**data)
        self.writes.append(f"update:{key}")
        return self.add(updated)

    def delete_template(self, key, *, owner_tenant_key):
        stored = self.templates.get(key)
        if stored is None or stored.tenant_key != owner_tenant_key:
            return False
        del self.templates[key]
        self.writes.append(f"delete:{key}")
        return True

    def bed_type_flags(self, location_type_keys):
        return {key: self.bed_types[key] for key in location_type_keys if key in self.bed_types}

    def visible_task_template_keys(self, keys, *, tenant_key):
        return {key for key in keys if self.task_templates.get(key) in ("", tenant_key)}
