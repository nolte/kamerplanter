import pytest

from app.common.enums import EntityType
from app.domain.engines.csv_parser import CsvParser


@pytest.fixture
def parser():
    return CsvParser()


class TestDetectEncoding:
    def test_utf8(self, parser):
        assert parser.detect_encoding(b"hello") == "utf-8"

    def test_latin1_fallback(self, parser):
        # Byte 0xe4 is 'ä' in latin-1, invalid standalone in utf-8
        assert parser.detect_encoding(b"\xe4\xf6\xfc") == "latin-1"


class TestDetectDelimiter:
    def test_semicolon(self, parser):
        assert parser.detect_delimiter("a;b;c") == ";"

    def test_tab(self, parser):
        assert parser.detect_delimiter("a\tb\tc") == "\t"

    def test_comma(self, parser):
        assert parser.detect_delimiter("a,b,c") == ","

    def test_default_comma(self, parser):
        assert parser.detect_delimiter("abc") == ","


class TestParse:
    def test_species_basic(self, parser):
        csv_bytes = b"scientific_name,common_name,description\nRosa canina,Dog rose,A wild rose\n"
        rows, warnings = parser.parse(csv_bytes, EntityType.SPECIES)
        assert len(warnings) == 0
        assert len(rows) == 1
        assert rows[0]["scientific_name"] == "Rosa canina"

    def test_semicolon_delimited(self, parser):
        csv_bytes = b"scientific_name;common_name\nRosa canina;Dog rose\n"
        rows, warnings = parser.parse(csv_bytes, EntityType.SPECIES)
        assert len(warnings) == 0
        assert rows[0]["scientific_name"] == "Rosa canina"

    def test_missing_required_column(self, parser):
        csv_bytes = b"common_name,description\nDog rose,A rose\n"
        with pytest.raises(ValueError, match="Missing required columns.*scientific_name"):
            parser.parse(csv_bytes, EntityType.SPECIES)

    def test_family_parse(self, parser):
        csv_bytes = b"name,common_name,order_name\nRosaceae,Rose family,Rosales\n"
        rows, _ = parser.parse(csv_bytes, EntityType.BOTANICAL_FAMILY)
        assert len(rows) == 1
        assert rows[0]["name"] == "Rosaceae"

    def test_empty_file(self, parser):
        csv_bytes = b""
        rows, warnings = parser.parse(csv_bytes, EntityType.SPECIES)
        assert rows == []
        assert warnings == []


class TestRowCountLimit:
    """SEC-M-008: Reject files exceeding MAX_DATA_ROWS."""

    def test_rejects_over_10000_rows(self, parser):
        header = "scientific_name\n"
        rows = "".join(f"Genus species{i}\n" for i in range(10_001))
        csv_bytes = (header + rows).encode()
        with pytest.raises(ValueError, match="exceeds maximum of 10000 data rows"):
            parser.parse(csv_bytes, EntityType.SPECIES)

    def test_accepts_exactly_10000_rows(self, parser):
        header = "scientific_name\n"
        rows = "".join(f"Genus species{i}\n" for i in range(10_000))
        csv_bytes = (header + rows).encode()
        result_rows, _ = parser.parse(csv_bytes, EntityType.SPECIES)
        assert len(result_rows) == 10_000


class TestCsvInjectionSanitization:
    """SEC-M-008: Strip dangerous leading characters from cell values."""

    @pytest.mark.parametrize("prefix", ["=", "+", "-", "@"])
    def test_strips_injection_prefix(self, parser, prefix):
        csv_bytes = f"scientific_name,common_name\nRosa canina,{prefix}HYPERLINK()\n".encode()
        rows, warnings = parser.parse(csv_bytes, EntityType.SPECIES)
        assert rows[0]["common_name"] == "HYPERLINK()"
        assert len(warnings) == 1
        assert "SUSPICIOUS_CONTENT" in warnings[0]

    def test_strips_tab_prefix_in_quoted_cell(self, parser):
        """Tab inside a quoted CSV cell is detected and stripped."""
        csv_bytes = b'scientific_name,common_name\nRosa canina,"\tHYPERLINK()"\n'
        rows, warnings = parser.parse(csv_bytes, EntityType.SPECIES)
        assert rows[0]["common_name"] == "HYPERLINK()"
        assert len(warnings) == 1
        assert "SUSPICIOUS_CONTENT" in warnings[0]

    def test_cr_prefix_neutralized_by_line_normalization(self, parser):
        """CR is neutralized by line-ending normalization + strip before CSV parsing."""
        # \r is converted to \n during preprocessing, then stripped from cell value
        csv_bytes = b'scientific_name,common_name\nRosa canina,"\rHYPERLINK()"\n'
        rows, _warnings = parser.parse(csv_bytes, EntityType.SPECIES)
        # The \r→\n is handled by line normalization + strip, content is clean
        assert rows[0]["common_name"] == "HYPERLINK()"

    def test_no_warning_for_clean_data(self, parser):
        csv_bytes = b"scientific_name,common_name\nRosa canina,Dog rose\n"
        rows, warnings = parser.parse(csv_bytes, EntityType.SPECIES)
        assert len(warnings) == 0
        assert rows[0]["common_name"] == "Dog rose"

    def test_strips_equals_formula(self, parser):
        csv_bytes = b"scientific_name,common_name\nRosa canina,=SUM(A1:A10)\n"
        rows, warnings = parser.parse(csv_bytes, EntityType.SPECIES)
        assert rows[0]["common_name"] == "SUM(A1:A10)"
        assert "SUSPICIOUS_CONTENT" in warnings[0]
        assert "common_name" in warnings[0]

    def test_negative_number_stripped(self, parser):
        """Negative numbers starting with '-' are stripped as a security measure."""
        csv_bytes = b"scientific_name,common_name\nRosa canina,-1\n"
        rows, warnings = parser.parse(csv_bytes, EntityType.SPECIES)
        assert rows[0]["common_name"] == "1"
        assert len(warnings) == 1


class TestGetTemplate:
    def test_species_template(self, parser):
        template = parser.get_template(EntityType.SPECIES)
        assert "scientific_name" in template
        assert "common_name" in template

    def test_family_template(self, parser):
        template = parser.get_template(EntityType.BOTANICAL_FAMILY)
        assert "name" in template
