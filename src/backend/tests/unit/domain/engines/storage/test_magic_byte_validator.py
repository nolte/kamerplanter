"""NFR-013 §5.1 step 3 — MagicByteValidator unit tests."""

from app.domain.engines.storage.magic_byte_validator import _SNIFF_LEN, MagicByteValidator

JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01"
PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 "
GIF = b"GIF89a\x01\x00\x01\x00"
PDF = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3"
ZIP = b"PK\x03\x04\x14\x00\x00\x00"
HEIC = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00"


class TestMagicByteValidator:
    def setup_method(self) -> None:
        self.validator = MagicByteValidator()

    def test_accepts_matching_jpeg(self) -> None:
        assert self.validator.is_valid(JPEG, "image/jpeg") is True

    def test_accepts_matching_png(self) -> None:
        assert self.validator.is_valid(PNG, "image/png") is True

    def test_accepts_matching_webp(self) -> None:
        assert self.validator.is_valid(WEBP, "image/webp") is True

    def test_accepts_matching_gif(self) -> None:
        assert self.validator.is_valid(GIF, "image/gif") is True

    def test_accepts_matching_pdf(self) -> None:
        assert self.validator.is_valid(PDF, "application/pdf") is True

    def test_accepts_matching_zip(self) -> None:
        assert self.validator.is_valid(ZIP, "application/zip") is True

    def test_accepts_matching_heic(self) -> None:
        assert self.validator.is_valid(HEIC, "image/heic") is True

    def test_blocks_png_declared_as_jpeg(self) -> None:
        # A real PNG masquerading as a JPEG must be blocked.
        assert self.validator.is_valid(PNG, "image/jpeg") is False

    def test_blocks_executable_disguised_as_jpeg(self) -> None:
        # ELF / PE-ish bytes claiming to be a JPEG.
        disguised = b"MZ\x90\x00\x03\x00\x00\x00"
        assert self.validator.is_valid(disguised, "image/jpeg") is False

    def test_blocks_html_disguised_as_png(self) -> None:
        html = b"<!DOCTYPE html><html><body>x</body></html>"
        assert self.validator.is_valid(html, "image/png") is False

    def test_unknown_mime_is_denied(self) -> None:
        assert self.validator.is_valid(JPEG, "application/x-msdownload") is False

    def test_csv_accepts_utf8_text(self) -> None:
        csv = b"name,scientific_name\nTomato,Solanum lycopersicum\n"
        assert self.validator.is_valid(csv, "text/csv") is True

    def test_csv_blocks_binary_with_nul(self) -> None:
        binary = b"name,sci\x00\x01\x02"
        assert self.validator.is_valid(binary, "text/csv") is False

    def test_only_inspects_sniff_prefix_for_csv(self) -> None:
        # SEC-008 — a NUL byte beyond the sniff window must NOT cause a false
        # negative; only the first _SNIFF_LEN bytes are decoded/inspected.
        data = (b"a," * 300)[:_SNIFF_LEN] + b"\x00" * 10_000
        assert self.validator.is_valid(data, "text/csv") is True

    def test_signature_check_ignores_bytes_past_prefix(self) -> None:
        # Valid JPEG header followed by garbage well past the prefix still valid.
        data = JPEG + b"\xff" * (_SNIFF_LEN * 4)
        assert self.validator.is_valid(data, "image/jpeg") is True
