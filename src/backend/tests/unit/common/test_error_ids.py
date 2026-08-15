"""A support reference id must not read as a payment card (#1158).

The post-merge ZAP scan of `57ee6a2c` raised a **High**-risk "PII Disclosure —
Credit Card Type detected: Maestro" on `POST /api/v1/privacy/erasure`, evidence
`576481450749`. That string is a UUID's final twelve-character group, all decimal
digits, Luhn-valid. No PII was disclosed; the identifier merely looked like a card.

Measured: 0.035 % of `err_<uuid4>` values carry such a run — one in 2 800. An API
scan makes thousands of requests, so it recurs, and each recurrence is a
*blocking* finding. A blocking finding that fires at random is worse than none: it
trains everyone to read that lane's red as noise (the #1178 pattern).
"""

from __future__ import annotations

import re

from app.common.error_ids import looks_like_a_card_number, new_error_id


class TestTheDetector:
    def test_it_recognises_the_string_zap_actually_flagged(self) -> None:
        """The concrete evidence from the #1158 report, not an invented example."""
        assert looks_like_a_card_number("err_9b342802-5467-5935-a1b2-576481450749")

    def test_a_run_that_fails_the_checksum_is_not_flagged(self) -> None:
        """Every card-number heuristic applies Luhn first. Flagging on length
        alone would reject most UUIDs and turn the generator into a loop that
        rarely terminates for no gain."""
        assert not looks_like_a_card_number("err_0000-000000000001")

    def test_a_short_digit_run_is_not_flagged(self) -> None:
        """Eleven digits is below the shortest card length (Maestro, 12)."""
        assert not looks_like_a_card_number("err_abc-57648145074-def")

    def test_a_luhn_valid_window_inside_a_longer_run_is_flagged(self) -> None:
        """A 16-digit sequence whose *first twelve* digits are Luhn-valid trips the
        same heuristic. A check testing only the whole run would miss it — and a
        generator built on that check would keep emitting exactly those ids."""
        assert looks_like_a_card_number("5764814507491234")


class TestTheGenerator:
    def test_the_shape_is_unchanged(self) -> None:
        """`err_` plus a UUID4, so logs, docs and the support instruction ("quote
        the reference ID") keep working. The fix is a re-draw, not a new format."""
        assert re.fullmatch(r"err_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", new_error_id())

    def test_ids_are_unique(self) -> None:
        """The re-draw must not have collapsed the entropy — an id that repeats
        cannot join a caller's report to one log line."""
        ids = [new_error_id() for _ in range(2000)]

        assert len(set(ids)) == len(ids)

    def test_no_generated_id_looks_like_a_card(self) -> None:
        """The property itself, over enough draws to have caught the old
        behaviour: at 0.035 % the pre-#1158 generator would have produced ~18
        card-like ids in this sample."""
        assert not any(looks_like_a_card_number(new_error_id()) for _ in range(50_000))


class TestEveryMintSiteUsesIt:
    """Four places minted this string independently before #1158.

    A shared helper that three of four callers use is not a shared helper — it is
    a fourth copy with better documentation. This scans the source rather than
    calling the sites, because the property is *where the id comes from*, and a
    call-based test would pass against a site that kept its own `uuid4()`.
    """

    def test_no_module_mints_an_error_id_by_hand(self) -> None:
        import pathlib

        import app

        root = pathlib.Path(app.__file__).resolve().parent
        offenders = [
            path.relative_to(root).as_posix()
            for path in root.rglob("*.py")
            if "__pycache__" not in path.parts
            and 'f"err_{' in path.read_text(encoding="utf-8")
            and path.name != "error_ids.py"
        ]

        assert offenders == [], (
            f"these modules mint an error id by hand instead of calling new_error_id(): {offenders}. "
            "Each one can emit a card-like identifier and trip a PII scanner (#1158)."
        )


class TestWhyTheOtherNumericIdentifierIsNotAffected:
    """A response carries two numeric identifiers. Only one of them was the source.

    Checked rather than assumed, because a fix that closes 0.035 % of a class
    while a larger source sits beside it is the shape that reads as closed and is
    not (#1158).

    **ArangoDB document keys.** Observed on the reference instance during the
    #1098 session: `13949`, `18132826`, `18132838`, `27773485`, `11598950`,
    `122282`, `122484` — five to eight digits. Every card heuristic starts at
    **twelve** (Maestro, the brand ZAP named), so a document key is structurally
    too short to match, whatever its checksum.

    A false trail worth recording, because it looked convincing: the scan's
    request URIs *do* contain 328 numeric segments of 17–19 digits, 57.6 % of
    which carry a Luhn-valid 12-digit window — and ZAP raised **zero** findings on
    them. Those are ZAP's own filler values for OpenAPI path parameters, sitting
    in *requests*; rule 10062 is a passive scanner over *response* bodies.
    Measuring them was measuring the wrong side of the exchange.
    """

    OBSERVED_DOCUMENT_KEYS = ("13949", "18132826", "18132838", "27773485", "11598950", "122282", "122484")
    SHORTEST_CARD_LENGTH = 12

    def test_a_document_key_is_too_short_to_be_mistaken_for_a_card(self) -> None:
        for key in self.OBSERVED_DOCUMENT_KEYS:
            assert len(key) < self.SHORTEST_CARD_LENGTH, (
                f"document key {key!r} reached card length — the exposure this file assumes away "
                "no longer holds, and the fix here covers only error ids"
            )
            assert not looks_like_a_card_number(key)

    def test_the_detector_is_not_error_id_specific(self) -> None:
        """So if keys ever grow past twelve digits, the same helper applies at that
        boundary. The exclusion above is a measured fact about today's data, not a
        property of the code."""
        assert looks_like_a_card_number("576481450749")
