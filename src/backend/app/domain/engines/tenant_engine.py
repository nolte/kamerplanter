import re
import unicodedata

from app.domain.engines.erasure_engine import ANONYMIZED_KEY_PREFIX


class TenantEngine:
    """Pure logic for tenant operations."""

    #: The namespace erasure renames a personal tenant into (#1700). A slug
    #: generated here never starts with it — nor equals its bare word, which the
    #: uniqueness suffix (``-2``) would turn into ``anonymized-2``. Otherwise a
    #: registration could occupy the value an erasure is about to write, and
    #: the unique ``tenants.slug`` index would abort that erasure for good.
    RESERVED_SLUG_PREFIX = ANONYMIZED_KEY_PREFIX

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate a URL-safe slug from a tenant name.

        Handles German umlauts and special characters. A result inside the
        reserved erasure namespace (:attr:`RESERVED_SLUG_PREFIX`) is moved out
        of it with a ``tenant-`` prefix.
        """
        replacements = {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "ß": "ss",
            "Ä": "Ae",
            "Ö": "Oe",
            "Ü": "Ue",
        }
        result = name
        for src, dst in replacements.items():
            result = result.replace(src, dst)

        result = unicodedata.normalize("NFKD", result)
        result = result.encode("ascii", "ignore").decode("ascii")
        result = result.lower()
        result = re.sub(r"[^a-z0-9]+", "-", result)
        result = result.strip("-") or "tenant"
        reserved_word = TenantEngine.RESERVED_SLUG_PREFIX.rstrip("-")
        if result == reserved_word or result.startswith(TenantEngine.RESERVED_SLUG_PREFIX):
            result = f"tenant-{result}"
        return result

    @staticmethod
    def validate_tenant_name(name: str) -> list[str]:
        """Validate tenant name. Returns list of error messages."""
        errors: list[str] = []
        if len(name.strip()) < 2:
            errors.append("Tenant name must be at least 2 characters")
        if len(name) > 200:
            errors.append("Tenant name must not exceed 200 characters")
        return errors

    @staticmethod
    def can_create_organization(existing_org_count: int, max_orgs: int = 10) -> bool:
        """Check if user can create another organization tenant."""
        return existing_org_count < max_orgs
