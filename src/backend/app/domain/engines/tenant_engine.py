import re
import unicodedata


class TenantEngine:
    """Pure logic for tenant operations."""

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate a URL-safe slug from a tenant name.

        Handles German umlauts and special characters.
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
        result = result.strip("-")
        return result or "tenant"

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
