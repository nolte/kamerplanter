
from app.domain.engines.tenant_engine import TenantEngine


class TestGenerateSlug:
    def test_basic_name(self):
        assert TenantEngine.generate_slug("My Garden") == "my-garden"

    def test_german_umlauts(self):
        assert TenantEngine.generate_slug("Schöner Gärten") == "schoener-gaerten"

    def test_eszett(self):
        assert TenantEngine.generate_slug("Große Straße") == "grosse-strasse"

    def test_special_characters(self):
        assert TenantEngine.generate_slug("Hello! @World#") == "hello-world"

    def test_leading_trailing_hyphens_stripped(self):
        assert TenantEngine.generate_slug("---test---") == "test"

    def test_consecutive_hyphens_collapsed(self):
        assert TenantEngine.generate_slug("a   b   c") == "a-b-c"

    def test_empty_after_normalization(self):
        assert TenantEngine.generate_slug("!!!") == "tenant"

    def test_unicode_normalization(self):
        result = TenantEngine.generate_slug("café résumé")
        assert result == "cafe-resume"

    def test_mixed_case(self):
        assert TenantEngine.generate_slug("GemeinschaftsGarten") == "gemeinschaftsgarten"

    def test_numbers_preserved(self):
        assert TenantEngine.generate_slug("Garden 42") == "garden-42"


class TestValidateTenantName:
    def test_valid_name(self):
        errors = TenantEngine.validate_tenant_name("My Garden")
        assert errors == []

    def test_too_short(self):
        errors = TenantEngine.validate_tenant_name("A")
        assert len(errors) == 1
        assert "at least 2" in errors[0]

    def test_whitespace_only_too_short(self):
        errors = TenantEngine.validate_tenant_name("  ")
        assert len(errors) == 1

    def test_too_long(self):
        errors = TenantEngine.validate_tenant_name("x" * 201)
        assert len(errors) == 1
        assert "200" in errors[0]


class TestCanCreateOrganization:
    def test_under_limit(self):
        assert TenantEngine.can_create_organization(5, max_orgs=10) is True

    def test_at_limit(self):
        assert TenantEngine.can_create_organization(10, max_orgs=10) is False

    def test_over_limit(self):
        assert TenantEngine.can_create_organization(11, max_orgs=10) is False

    def test_zero_existing(self):
        assert TenantEngine.can_create_organization(0) is True
