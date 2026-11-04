"""WP 8.4 (#2647) — the one CSV writer: formula hardening (SR-016), BOM, RFC 4180 quoting, the delimiters."""

from __future__ import annotations

import csv
import io

import pytest

from app.common.csv_export import BOM, FORMULA_PREFIXES, csv_number, csv_text, encode_csv


class TestFormulaHardening:
    @pytest.mark.parametrize("prefix", FORMULA_PREFIXES)
    def test_every_dangerous_prefix_is_neutralised(self, prefix: str) -> None:
        assert csv_text(f"{prefix}cmd|' /C calc'!A0") == f"'{prefix}cmd|' /C calc'!A0"

    def test_the_six_prefixes_are_the_ones_of_the_spec(self) -> None:
        assert set(FORMULA_PREFIXES) == {"=", "+", "-", "@", "\t", "\r"}

    @pytest.mark.parametrize("value", ["Watered", "a=b", "x+y", "5 l", " =lead space", "'quoted", "Ä"])
    def test_a_harmless_text_is_left_alone(self, value: str) -> None:
        # counter-case of the rule: only the FIRST character decides
        assert csv_text(value) == value

    def test_nothing_is_an_empty_cell(self) -> None:
        assert csv_text(None) == "" and csv_text("") == "" and csv_number(None) == ""

    def test_a_number_is_never_prefixed_whatever_its_sign(self) -> None:
        assert csv_number(-3.25) == "-3.25" and csv_number(21.5) == "21.5" and csv_number(-4) == "-4"
        assert csv_number(0) == "0"

    def test_the_decimal_mark_is_the_callers_choice_for_the_excel_variant(self) -> None:
        assert csv_number(2.5, decimal=",") == "2,5" and csv_number(-0.75, decimal=",") == "-0,75"
        assert csv_number(4, decimal=",") == "4" and csv_number(2.5) == "2.5"


class TestEncoding:
    def test_the_file_starts_with_a_bom_and_is_utf_8(self) -> None:
        data = encode_csv(["a"], [["Ä ö ü ß"]])

        assert data.startswith(BOM.encode("utf-8")) and data.startswith(b"\xef\xbb\xbf")
        assert data.decode("utf-8-sig").splitlines()[1] == "Ä ö ü ß"

    def test_rfc_4180_quoting_round_trips(self) -> None:
        cells = ['say "hi"', "a,b", "line\nbreak", "plain", "x;y"]

        data = encode_csv(["c1", "c2", "c3", "c4", "c5"], [cells])
        parsed = list(csv.reader(io.StringIO(data.decode("utf-8-sig"), newline="")))

        assert parsed == [["c1", "c2", "c3", "c4", "c5"], cells]
        assert b'"say ""hi"""' in data  # a quote is doubled
        assert b'"a,b"' in data and b'"line\nbreak"' in data

    def test_line_ends_are_crlf(self) -> None:
        assert encode_csv(["a"], [["1"], ["2"]]).decode("utf-8-sig") == "a\r\n1\r\n2\r\n"

    def test_the_semicolon_variant_quotes_the_semicolon_not_the_comma(self) -> None:
        data = encode_csv(["a", "b"], [["x;y", "1,5"]], delimiter=";").decode("utf-8-sig")

        assert data == 'a;b\r\n"x;y";1,5\r\n'

    def test_any_other_delimiter_is_refused(self) -> None:
        with pytest.raises(ValueError, match="delimiter"):
            encode_csv(["a"], [["1"]], delimiter="|")

    def test_a_neutralised_cell_is_what_the_file_holds(self) -> None:
        data = encode_csv(["a"], [[csv_text("=1+1")]]).decode("utf-8-sig")

        assert data == "a\r\n'=1+1\r\n"
