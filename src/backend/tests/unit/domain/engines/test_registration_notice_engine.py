"""What the REQ-023 §3.2 notice says — and, more importantly, what it must not.

The mail goes to a third party at the request of an unauthenticated caller who
chose both the recipient and the moment. Everything the caller submitted is
therefore attacker-controlled content aimed at somebody else's inbox, and none
of it may appear. The tests below pin that, plus DE/EN parity: a mirror that
silently loses a paragraph would ship a different message to English users.
"""

import pytest

from app.domain.engines.registration_notice_engine import BODIES, SUBJECTS, RegistrationNoticeEngine

FRONTEND_URL = "https://garden.example.com"


@pytest.fixture
def engine() -> RegistrationNoticeEngine:
    return RegistrationNoticeEngine()


class TestLocaleSelection:
    def test_german_is_the_canonical_variant(self, engine: RegistrationNoticeEngine) -> None:
        subject, body = engine.render("de", FRONTEND_URL)

        assert subject == SUBJECTS["de"]
        assert "kein zweites Konto angelegt" in body

    def test_english_is_the_mirror(self, engine: RegistrationNoticeEngine) -> None:
        subject, body = engine.render("en", FRONTEND_URL)

        assert subject == SUBJECTS["en"]
        assert "no second account was created" in body

    @pytest.mark.parametrize("locale", [None, "", "fr", "de-DE"])
    def test_unknown_locale_falls_back_to_german(
        self,
        engine: RegistrationNoticeEngine,
        locale: str | None,
    ) -> None:
        subject, _ = engine.render(locale, FRONTEND_URL)

        assert subject == SUBJECTS["de"]

    def test_both_variants_exist_for_every_subject(self) -> None:
        assert SUBJECTS.keys() == BODIES.keys() == {"de", "en"}


class TestLinks:
    def test_links_point_at_the_configured_frontend(self, engine: RegistrationNoticeEngine) -> None:
        _, body = engine.render("de", FRONTEND_URL)

        assert f'href="{FRONTEND_URL}/login"' in body
        assert f'href="{FRONTEND_URL}/password-reset"' in body

    def test_trailing_slash_does_not_double_up(self, engine: RegistrationNoticeEngine) -> None:
        _, body = engine.render("en", "https://garden.example.com/")

        assert "//login" not in body.replace("https://", "")

    def test_body_carries_no_token_and_no_one_click_action(
        self,
        engine: RegistrationNoticeEngine,
    ) -> None:
        """Nothing happened that needs undoing, so nothing here may be actionable."""
        for locale in ("de", "en"):
            _, body = engine.render(locale, FRONTEND_URL)
            links = [part for part in body.split('href="')[1:]]
            for link in links:
                url = link.split('"')[0]
                assert url in (f"{FRONTEND_URL}/login", f"{FRONTEND_URL}/password-reset")


class TestWhatTheMailDoesNotContain:
    """The template takes no request input at all — asserted, not assumed."""

    def test_render_accepts_nothing_the_caller_submitted(self) -> None:
        import inspect

        parameters = set(inspect.signature(RegistrationNoticeEngine.render).parameters)

        # No display_name, no email, no password, no ip: the signature is the
        # guarantee. A future parameter would have to break this test first.
        assert parameters == {"self", "locale", "frontend_url"}

    @pytest.mark.parametrize("locale", ["de", "en"])
    def test_states_that_nothing_changed(self, engine: RegistrationNoticeEngine, locale: str) -> None:
        _, body = engine.render(locale, FRONTEND_URL)

        expected = "nichts geändert" if locale == "de" else "Nothing about your\naccount changed".replace("\n", " ")
        assert expected in body

    @pytest.mark.parametrize("locale", ["de", "en"])
    def test_announces_the_suppression_window(
        self,
        engine: RegistrationNoticeEngine,
        locale: str,
    ) -> None:
        """The recipient is told they will not get one of these per attempt."""
        _, body = engine.render(locale, FRONTEND_URL)

        expected = "einmal pro Tag" if locale == "de" else "once a day"
        assert expected in body
