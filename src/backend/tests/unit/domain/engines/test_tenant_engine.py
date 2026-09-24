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


class TestAnonymizedSlugPrefixIsReserved:
    """#1700 — ``anonymized-`` is the namespace erasure renames a personal tenant into.

    A slug a registration could produce inside it can collide with the one the
    erasure writes, and ``tenants.slug`` carries a unique index: the erasure
    transaction would then abort on every retry (Art. 17 blocked for good).
    """

    def test_a_display_name_spelling_the_prefix_does_not_land_in_it(self):
        slug = TenantEngine.generate_slug("Anonymized 101")
        assert not slug.startswith("anonymized-")
        assert "anonymized-101" in slug  # still derived from the name, just moved out of the namespace

    def test_the_bare_prefix_word_is_moved_too(self):
        """``anonymized`` + the uniqueness suffix ``-2`` would otherwise reach ``anonymized-2``."""
        assert TenantEngine.generate_slug("Anonymized") != "anonymized"
        assert not TenantEngine.generate_slug("Anonymized").startswith("anonymized")

    def test_unicode_and_case_variants_are_moved(self):
        for name in ("ANONYMIZED 7", "  anonymized---x", "Anonymized-ä"):
            assert not TenantEngine.generate_slug(name).startswith("anonymized"), name

    def test_a_name_merely_containing_the_word_is_untouched(self):
        assert TenantEngine.generate_slug("Not Anonymized Garden") == "not-anonymized-garden"

    def test_the_reserved_prefix_is_the_one_erasure_writes(self):
        from app.domain.engines.erasure_engine import ANONYMIZED_KEY_PREFIX

        assert TenantEngine.RESERVED_SLUG_PREFIX == ANONYMIZED_KEY_PREFIX
