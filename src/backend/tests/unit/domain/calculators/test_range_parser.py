"""REQ-053 GP-FR-061 — the lower value of a species distance range string."""

import pytest

from app.domain.calculators.range_parser import parse_range_bounds, parse_range_lower


class TestParseRangeLower:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            # the three shapes the issue names
            ("40", 40.0),
            ("25-30", 25.0),
            ("20--30", 20.0),
            # the shapes measured in the seed data (2026-10-16)
            ("30-40", 30.0),
            ("300--500", 300.0),
            ("90", 90.0),
            (110, 110.0),
            # what the seed schema's ``distance_cm_string`` pattern additionally admits
            ("5–10", 5.0),
            ("5—10", 5.0),
            ("15 - 25", 15.0),
            ("30–-40", 30.0),
            ("2.5-5", 2.5),
            ("40.0", 40.0),
            ("0", 0.0),
            # what the parser tolerates beyond the schema (API / CSV input is unvalidated)
            (" 15 - 25 ", 15.0),
            ("30–40 cm", 30.0),
            ("30 CM", 30.0),
            (12.5, 12.5),
        ],
    )
    def test_lower_value(self, value, expected):
        assert parse_range_lower(value) == pytest.approx(expected)

    def test_reversed_range_still_yields_the_smaller_value(self):
        assert parse_range_lower("40-30") == 30.0

    @pytest.mark.parametrize(
        "value",
        [
            None,
            "",
            "   ",
            "unknown",
            "abc-def",
            "-30",
            "30-",
            "30-40-50",
            "30 to 40",
            "30 bis 40",
            "30 x 40",
            "30cm-40cm",
            "n/a",
            True,
            False,
            [],
            -5,
            -0.5,
            float("nan"),
            float("inf"),
        ],
    )
    def test_unparsable_yields_none(self, value):
        assert parse_range_lower(value) is None

    @pytest.mark.parametrize("value", ["1,500", "1,5", "2,5-5", "1.500-2,000"])
    def test_decimal_comma_is_ambiguous_and_yields_none(self, value):
        """``"1,500"`` is a 15 m tree spacing in German notation as often as 1.5 cm — no guess."""
        assert parse_range_lower(value) is None

    def test_unicode_digits_are_not_digits(self):
        """``re.ASCII``: the schema's ECMA ``\\d`` does not match fullwidth or Arabic-Indic digits."""
        assert parse_range_lower("３０") is None
        assert parse_range_lower("٣٠-٤٠") is None

    @pytest.mark.parametrize("n", [5, 30, 45, 60, 90, 120, 300, 1500])
    def test_integer_seed_values_round_trip_as_exact_floats(self, n):
        """The result is a ``float`` carrying the integer exactly, so the type is pinned, not only the value."""
        single = parse_range_lower(str(n))
        ranged = parse_range_lower(f"{n}--{n + 10}")
        assert type(single) is float and single == float(n)
        assert type(ranged) is float and ranged == float(n)


class TestParseRangeBounds:
    def test_range(self):
        assert parse_range_bounds("50--80") == (50.0, 80.0)

    def test_single_value_is_a_degenerate_range(self):
        assert parse_range_bounds("40") == (40.0, 40.0)

    def test_reversed_range_is_normalised(self):
        assert parse_range_bounds("80-50") == (50.0, 80.0)

    def test_none(self):
        assert parse_range_bounds(None) is None
