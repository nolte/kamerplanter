from abc import ABC, abstractmethod
from typing import Any

from app.common.types import BedTemplateKey
from app.domain.models.bed_template import BedTemplate


class IBedTemplateRepository(ABC):
    """Persistence of the bed templates (REQ-053 §20.12; WP 7.8).

    A template has two owners: a tenant (``tenant_key``) or nobody (``tenant_key is None`` - a *system* template
    every tenant reads). Every method takes the tenant keyword-only without a default and filters inside the
    query, so another tenant's template answers exactly like an absent one (``None`` / ``NotFoundError``).
    The writes name their **owner** (``owner_tenant_key``): a tenant's key for its own template, ``None`` for a
    global one - a write for the wrong owner matches nothing, so a tenant can never reach a global row and a
    platform-admin edit of a global row can never land on a tenant's.
    """

    @abstractmethod
    def list_visible(self, *, tenant_key: str, offset: int, limit: int) -> list[BedTemplate]:
        """The system templates and the tenant's own, by name; a window of ``limit`` from ``offset``."""

    @abstractmethod
    def get_visible_by_key(self, key: BedTemplateKey, *, tenant_key: str) -> BedTemplate | None:
        """The template behind ``key`` when it is a system template or the tenant's own, else ``None``."""

    @abstractmethod
    def visible_keys(self, keys: list[BedTemplateKey], *, tenant_key: str) -> set[BedTemplateKey]:
        """Which of ``keys`` are system templates or the tenant's own (the import's reference check)."""

    @abstractmethod
    def count_owned(self, *, tenant_key: str) -> int:
        """How many templates the tenant owns (system templates are not counted)."""

    @abstractmethod
    def create_template(self, template: BedTemplate) -> BedTemplate:
        """Insert the template as it is (``tenant_key`` and ``created_by`` are the service's)."""

    @abstractmethod
    def update_template(
        self, key: BedTemplateKey, fields: dict[str, Any], *, owner_tenant_key: str | None
    ) -> BedTemplate:
        """Write *only* ``fields`` (``None`` removes a value) on the template of that owner; else ``NotFoundError``."""

    @abstractmethod
    def delete_template(self, key: BedTemplateKey, *, owner_tenant_key: str | None) -> bool:
        """Delete the template of that owner and, atomically, unset ``template_key`` on the beds placed from it.

        A tenant template releases the beds of that tenant's sites only, a system template (``owner_tenant_key``
        ``None``) the beds of every tenant (#2528). ``False`` when the owner has no such template - nothing written.
        """

    @abstractmethod
    def bed_type_flags(self, location_type_keys: list[str]) -> dict[str, bool]:
        """``{location type key: is_bed}`` for the keys that exist; an absent key is not in the result."""

    @abstractmethod
    def visible_task_template_keys(self, keys: list[str], *, tenant_key: str) -> set[str]:
        """Which of ``keys`` are task templates of the tenant or global ones (empty ``tenant_key``)."""
