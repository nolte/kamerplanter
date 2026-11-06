"""REQ-053 WP 8.26 (#2669) - the reading half of the CSV rules (GP-FR-174, SR-016).

Encoding, delimiter and record bound of :func:`read_table`, the formula prefixes discarded on read, and the numbers
German Excel writes. The writer's own tests (``test_csv_export.py``) pin the other half; the round trip below pins
that what the writer neutralises, the reader neutralises again.
"""

from __future__ import annotations

import pytest

from app.common.csv_export import BOM, csv_text, encode_csv
from app.common.csv_import import (
    ERROR_EMPTY,
    ERROR_INVALID_DELIMITER,
    ERROR_INVALID_ENCODING,
    ERROR_MALFORMED,
    CsvReadError,
    decode_csv,
    had_formula_prefix,
    header_key,
    neutralised_text,
    parse_decimal,
    read_table,
)


class TestEncoding:
    def test_a_bom_is_dropped_and_the_umlauts_survive(self) -> None:
        text = decode_csv((BOM + "Name;Länge_m\r\nGrüner Daumen;2\r\n").encode("utf-8"))

        assert text.startswith("Name;Länge_m") and "Grüner Daumen" in text

    def test_a_file_without_bom_reads_the_same(self) -> None:
        assert decode_csv(b"Name;Typ\n") == "Name;Typ\n"

    def test_latin_1_bytes_are_refused_not_guessed(self) -> None:
        with pytest.raises(CsvReadError) as caught:
            decode_csv("Name;Länge_m\n".encode("latin-1"))

        assert caught.value.code == ERROR_INVALID_ENCODING


class TestTheTable:
    def test_header_records_and_their_line_numbers(self) -> None:
        table = read_table("Name;Typ\r\nA;Beet\r\n;\r\nB;Beet\r\n")

        assert table.header == ("Name", "Typ")
        assert [(r.line, r.cells) for r in table.records] == [(2, ("A", "Beet")), (4, ("B", "Beet"))]

    def test_a_quoted_cell_may_hold_the_delimiter_and_a_line_break(self) -> None:
        table = read_table('Name;Typ\r\n"Beet; Nord\r\nzwei";Beet\r\nC;Beet\r\n')

        assert table.records[0].cells == ("Beet; Nord\r\nzwei", "Beet")
        assert [record.line for record in table.records] == [3, 4]  # the line a record ends on

    def test_a_comma_separated_header_is_refused_with_a_hint(self) -> None:
        with pytest.raises(CsvReadError) as caught:
            read_table("Name,Typ,Breite_m,Länge_m\nA,Beet,1,1\n")

        assert caught.value.code == ERROR_INVALID_DELIMITER

    @pytest.mark.parametrize("text", ["", "\r\n\r\n", ";;\r\n"])
    def test_an_empty_file_is_refused(self, text: str) -> None:
        with pytest.raises(CsvReadError) as caught:
            read_table(text)

        assert caught.value.code == ERROR_EMPTY

    def test_an_unclosed_quote_is_malformed(self) -> None:
        with pytest.raises(CsvReadError) as caught:
            read_table('Name;Typ\r\n"A;Beet\r\n')

        assert caught.value.code == ERROR_MALFORMED

    def test_the_read_stops_one_record_past_the_bound(self) -> None:
        text = "Name;Typ\n" + "".join(f"B{n};Beet\n" for n in range(50))

        assert len(read_table(text, max_records=10).records) == 11
        assert len(read_table(text).records) == 50  # the positive control: unbounded reads them all


class TestFormulaPrefixesAreDiscarded:
    @pytest.mark.parametrize(
        ("cell", "stored"),
        [
            ("=SUM(A1)", "SUM(A1)"),
            ("+Beet", "Beet"),
            ("-Beet", "Beet"),
            ("@Beet", "Beet"),
            ("\tBeet", "Beet"),
            ("\rBeet", "Beet"),
            ("=+-@Beet", "Beet"),
            ("'=SUM(A1)", "SUM(A1)"),  # what csv_text writes for a formula-looking name
            ("  = HYPERLINK(x)", "HYPERLINK(x)"),
            ("'s Gartl", "'s Gartl"),  # a ' before no formula character is part of the name
            ("Beet 1", "Beet 1"),
            ("Beet-Nord", "Beet-Nord"),  # only a *leading* character is a prefix
        ],
    )
    def test_the_cell_as_it_is_stored(self, cell: str, stored: str) -> None:
        assert neutralised_text(cell) == stored

    def test_the_warning_flag_is_raised_for_a_prefix_only(self) -> None:
        assert had_formula_prefix("=1+1") is True
        assert had_formula_prefix("  Beet  ") is False
        assert had_formula_prefix("") is False

    def test_what_the_writer_neutralises_the_reader_neutralises_again(self) -> None:
        file = encode_csv(["Name", "Typ"], [[csv_text("=cmd|' /C calc'!A0"), "Beet"]], delimiter=";")

        record = read_table(decode_csv(file)).records[0]

        assert neutralised_text(record.cells[0]) == "cmd|' /C calc'!A0"
        assert not neutralised_text(record.cells[0]).startswith(("=", "+", "-", "@", "'"))


class TestNumbers:
    @pytest.mark.parametrize(("cell", "value"), [("2,5", 2.5), ("2.5", 2.5), ("2", 2.0), (" 0,75 ", 0.75)])
    def test_a_decimal_comma_and_a_decimal_point_are_both_read(self, cell: str, value: float) -> None:
        assert parse_decimal(cell) == value

    @pytest.mark.parametrize("cell", ["-2", "+2", "1e3", "1.250,5", "1,250.5", "2,5 m", "=2", "", ",5", "2,", "∞"])
    def test_anything_but_a_plain_unsigned_decimal_is_refused(self, cell: str) -> None:
        with pytest.raises(ValueError):
            parse_decimal(cell)


class TestHeaderKeys:
    @pytest.mark.parametrize("cell", ["Länge_m", "Laenge_m", "LÄNGE M", "länge-m", " Länge (m) ", "'=Länge_m"])
    def test_every_spelling_reads_the_same_key(self, cell: str) -> None:
        assert header_key(cell) == "laenge_m"
