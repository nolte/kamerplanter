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
        rows, delim = parser.parse(csv_bytes, EntityType.SPECIES)
        assert delim == ","
        assert len(rows) == 1
        assert rows[0]["scientific_name"] == "Rosa canina"

    def test_semicolon_delimited(self, parser):
        csv_bytes = b"scientific_name;common_name\nRosa canina;Dog rose\n"
        rows, delim = parser.parse(csv_bytes, EntityType.SPECIES)
        assert delim == ";"
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
        rows, _ = parser.parse(csv_bytes, EntityType.SPECIES)
        assert rows == []


class TestGetTemplate:
    def test_species_template(self, parser):
        template = parser.get_template(EntityType.SPECIES)
        assert "scientific_name" in template
        assert "common_name" in template

    def test_family_template(self, parser):
        template = parser.get_template(EntityType.BOTANICAL_FAMILY)
        assert "name" in template
