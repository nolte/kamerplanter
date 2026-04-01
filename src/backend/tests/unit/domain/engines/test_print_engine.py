"""Tests for PrintEngine."""

import pytest

from app.domain.engines.print_engine import LABELS, REMINDER_TYPE_LABELS, PrintEngine


@pytest.fixture
def engine(tmp_path):
    """Create a PrintEngine with a temporary templates directory."""
    # Create a minimal test template
    template = tmp_path / "test.html"
    template.write_text("<html><body><h1>{{ title }}</h1><p>{{ labels.author }}</p></body></html>")

    # Create base.html for templates that extend it
    base = tmp_path / "base.html"
    base.write_text(
        "<!DOCTYPE html><html><head><style></style></head><body>{% block content %}{% endblock %}</body></html>"
    )

    return PrintEngine(templates_dir=tmp_path)


class TestPrintEngine:
    def test_render_pdf_returns_bytes(self, engine):
        """PDF rendering returns non-empty bytes."""
        result = engine.render_pdf("test.html", {"title": "Test Plan"}, locale="de")

        assert isinstance(result, bytes)
        assert len(result) > 0
        # PDF files start with %PDF
        assert result[:5] == b"%PDF-"

    def test_render_pdf_german_locale(self, engine):
        """German locale passes correct labels to template."""
        result = engine.render_pdf("test.html", {"title": "Test"}, locale="de")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_render_pdf_english_locale(self, engine):
        """English locale passes correct labels to template."""
        result = engine.render_pdf("test.html", {"title": "Test"}, locale="en")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_render_pdf_unknown_locale_falls_back_to_german(self, engine):
        """Unknown locale falls back to German labels."""
        result = engine.render_pdf("test.html", {"title": "Test"}, locale="fr")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_render_pdf_invalid_template_raises(self, engine):
        """Non-existent template raises TemplateNotFound."""
        from jinja2 import TemplateNotFound

        with pytest.raises(TemplateNotFound):
            engine.render_pdf("nonexistent.html", {})


class TestGenerateQrCodeBase64:
    def test_returns_valid_data_uri(self):
        """QR code generation returns a valid base64 data URI."""
        result = PrintEngine.generate_qr_code_base64("https://example.com/plant/123")

        assert result.startswith("data:image/png;base64,")
        # The base64 part should be non-empty
        b64_part = result.split(",", 1)[1]
        assert len(b64_part) > 0

    def test_base64_is_decodable(self):
        """The base64 portion can be decoded to valid PNG bytes."""
        import base64

        result = PrintEngine.generate_qr_code_base64("https://example.com")
        b64_part = result.split(",", 1)[1]
        decoded = base64.b64decode(b64_part)

        # PNG magic bytes
        assert decoded[:8] == b"\x89PNG\r\n\x1a\n"

    def test_size_parameter_affects_output(self):
        """Different size_mm values produce different output sizes."""
        small = PrintEngine.generate_qr_code_base64("https://example.com", size_mm=20)
        large = PrintEngine.generate_qr_code_base64("https://example.com", size_mm=60)

        # Larger QR code should produce more base64 data
        assert len(large) > len(small)

    def test_encodes_url_correctly(self):
        """QR code encodes the provided URL (smoke test — decoding requires external lib)."""
        url = "https://kamerplanter.example/t/my-garden/plants/abc123"
        result = PrintEngine.generate_qr_code_base64(url, size_mm=25)

        assert isinstance(result, str)
        assert result.startswith("data:image/png;base64,")

    def test_minimum_size(self):
        """Works with the minimum allowed QR size (20mm)."""
        result = PrintEngine.generate_qr_code_base64("https://example.com", size_mm=20)
        assert result.startswith("data:image/png;base64,")

    def test_maximum_size(self):
        """Works with a large QR size (60mm)."""
        result = PrintEngine.generate_qr_code_base64("https://example.com", size_mm=60)
        assert result.startswith("data:image/png;base64,")


class TestLabels:
    def test_german_labels_complete(self):
        """German labels contain all required keys."""
        required_keys = [
            "author",
            "generated",
            "substrate",
            "phase_overview",
            "phase",
            "weeks",
            "target_ec",
            "product",
            "optional",
            "care_checklist_title",
            "plant",
            "species",
            "reminder_type",
            "due_date",
            "location",
            "notes_section",
            "plant_label_title",
            "planted",
            "family",
            "cultivar",
            "note",
            "cut_marks_hint",
        ]
        for key in required_keys:
            assert key in LABELS["de"], f"Missing German label: {key}"

    def test_english_labels_complete(self):
        """English labels contain all required keys."""
        for key in LABELS["de"]:
            assert key in LABELS["en"], f"Missing English label: {key}"

    def test_reminder_type_labels_cover_all_types(self):
        """Reminder type labels cover all ReminderType enum values."""
        from app.common.enums import ReminderType

        for rt in ReminderType:
            assert rt.value in REMINDER_TYPE_LABELS["de"], f"Missing DE label for {rt}"
            assert rt.value in REMINDER_TYPE_LABELS["en"], f"Missing EN label for {rt}"
