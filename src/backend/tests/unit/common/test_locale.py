"""NFR-017 R-112/R-114 — the one server-side locale resolution (#2902)."""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.common.locale import (
    DEFAULT_LOCALE,
    MAX_ACCEPT_LANGUAGE_LENGTH,
    SUPPORTED_LOCALES,
    get_request_locale,
    negotiate_accept_language,
    normalize_locale,
    resolve_locale,
)


class TestNormalizeLocale:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("de", "de"),
            ("en", "en"),
            ("en-GB", "en"),
            ("EN_us", "en"),
            (" de-AT ", "de"),
            ("fr", None),
            ("", None),
            (None, None),
            ("english", None),
        ],
    )
    def test_maps_a_tag_onto_a_supported_locale(self, value: str | None, expected: str | None) -> None:
        assert normalize_locale(value) == expected

    def test_supported_and_default(self) -> None:
        assert SUPPORTED_LOCALES == ("de", "en")
        assert DEFAULT_LOCALE == "de"


class TestNegotiateAcceptLanguage:
    @pytest.mark.parametrize(
        ("header", "expected"),
        [
            ("en", "en"),
            ("de", "de"),
            ("en-GB,en;q=0.9,de;q=0.8", "en"),
            ("de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7", "de"),
            # the weight decides, not the position
            ("de;q=0.5,en;q=0.9", "en"),
            ("en;q=0.1, de", "de"),
            # an unsupported first choice falls through to the next supported one
            ("fr-CH,fr;q=0.9,en;q=0.8,de;q=0.7", "en"),
            # equal weights keep the header order
            ("en;q=0.8,de;q=0.8", "en"),
            # q=0 means "not acceptable"
            ("en;q=0,de;q=0.1", "de"),
            ("en;q=0", None),
            # whitespace and case
            ("  EN-gb ; Q = 0.9 ", "en"),
            # the wildcard accepts any language: the default one
            ("fr,*;q=0.5", "de"),
            ("*", "de"),
        ],
    )
    def test_picks_the_most_preferred_supported_locale(self, header: str, expected: str | None) -> None:
        assert negotiate_accept_language(header) == expected

    @pytest.mark.parametrize(
        "header",
        [
            "",
            "fr",
            "fr, it;q=0.9",
            ";;;,,,",
            "en;q=abc",
            "en;q=1.5",
            "en;q=-1",
            "en;foo=bar",
            "e n",
            "en-",
            "x" * (MAX_ACCEPT_LANGUAGE_LENGTH + 1),
        ],
    )
    def test_malformed_or_unsupported_input_names_no_locale(self, header: str) -> None:
        assert negotiate_accept_language(header) is None

    def test_a_malformed_range_does_not_spoil_the_rest(self) -> None:
        assert negotiate_accept_language("en;q=abc, de;q=0.5") == "de"
        assert negotiate_accept_language("garbage!!, en") == "en"

    def test_none_is_no_header(self) -> None:
        assert negotiate_accept_language(None) is None


class TestResolveLocale:
    def test_explicit_parameter_wins_over_the_header(self) -> None:
        assert resolve_locale(explicit="en", accept_language="de") == "en"

    def test_an_unsupported_explicit_parameter_falls_through_to_the_header(self) -> None:
        assert resolve_locale(explicit="fr", accept_language="en") == "en"

    def test_nothing_is_the_default(self) -> None:
        assert resolve_locale(explicit=None, accept_language=None) == "de"
        assert resolve_locale(explicit="", accept_language="fr") == "de"


class TestDependency:
    @pytest.fixture
    def client(self) -> TestClient:
        app = FastAPI()

        @app.get("/probe")
        def probe(language: str = Depends(get_request_locale)) -> dict[str, str]:
            return {"language": language}

        return TestClient(app)

    @pytest.mark.parametrize(
        ("headers", "query", "expected"),
        [
            ({"Accept-Language": "en-GB,en;q=0.9,de;q=0.8"}, "", "en"),
            ({"Accept-Language": "de"}, "", "de"),
            ({}, "", "de"),
            ({"Accept-Language": "fr"}, "", "de"),
            ({"Accept-Language": "de"}, "?locale=en", "en"),
            ({"Accept-Language": "de"}, "?language=en", "en"),
        ],
    )
    def test_the_request_resolves_to_one_supported_locale(
        self, client: TestClient, headers: dict[str, str], query: str, expected: str
    ) -> None:
        assert client.get(f"/probe{query}", headers=headers).json() == {"language": expected}
