"""#2113 — the pure Apprise-URL secret helpers: mask, resolve, seal, open, export."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.common.exceptions import ValidationError
from app.domain.engines.apprise_url_secrets import (
    URLS,
    URLS_CONFIGURED,
    URLS_ENCRYPTED,
    export_config,
    mask_url,
    masked_channels,
    masked_urls,
    open_config,
    resolve_masked_urls,
    seal_config,
)
from app.domain.engines.encryption_engine import EncryptionEngine, is_fernet_token
from app.domain.models.notification import ChannelPreference

TGRAM = "tgram://" + "123456789:" + "AAbot2113" + "Secret/4711"
GOTIFY = "gotifys://" + "gotify.example.org/" + "Atoken2113"


@pytest.fixture
def engine() -> EncryptionEngine:
    return EncryptionEngine(Fernet.generate_key().decode())


class TestMask:
    def test_a_url_masks_to_its_scheme_and_position(self) -> None:
        assert mask_url(TGRAM, 1) == "tgram://****#1"

    @pytest.mark.parametrize("value", ["not a url", "", None, "://x", "bad scheme!://x"])
    def test_a_value_without_a_usable_scheme_masks_to_the_position_only(self, value: object) -> None:
        assert mask_url(value, 3) == "****#3"

    def test_a_list_masks_by_position_and_a_non_list_to_nothing(self) -> None:
        assert masked_urls([TGRAM, GOTIFY]) == ["tgram://****#1", "gotifys://****#2"]
        assert masked_urls("tgram://x") == []

    def test_masked_channels_copies_and_masks_only_apprise(self) -> None:
        channels = {
            "apprise": ChannelPreference(enabled=True, config={URLS: [TGRAM], URLS_ENCRYPTED: ["x"]}),
            "email": ChannelPreference(enabled=True, config={"digest": True}),
        }

        masked = masked_channels(channels)

        assert masked["apprise"].config == {URLS: ["tgram://****#1"]}
        assert masked["email"].config == {"digest": True}
        assert channels["apprise"].config[URLS] == [TGRAM]


class TestResolve:
    def test_placeholders_resolve_to_the_stored_url_and_new_lines_pass(self) -> None:
        assert resolve_masked_urls(["gotifys://****#2", "ntfy://x/y"], [TGRAM, GOTIFY]) == [GOTIFY, "ntfy://x/y"]

    def test_a_non_list_is_returned_for_the_validation_to_refuse(self) -> None:
        assert resolve_masked_urls("tgram://****#1", [TGRAM]) == "tgram://****#1"

    @pytest.mark.parametrize("placeholder", ["tgram://****#2", "tgram://****#0", "gotifys://****#1", "****#1"])
    def test_a_placeholder_without_its_stored_url_is_refused_value_free(self, placeholder: str) -> None:
        with pytest.raises(ValidationError) as caught:
            resolve_masked_urls(["ntfy://ok/x", placeholder], [TGRAM])

        assert caught.value.details[0]["field"] == "channels.apprise.config.urls[1]"
        assert TGRAM not in str(caught.value.details)


class TestSealAndOpen:
    def test_seal_stores_ciphertext_only_and_open_restores_the_list(self, engine: EncryptionEngine) -> None:
        sealed = seal_config({URLS: [TGRAM, GOTIFY], "other": 1}, engine)

        assert set(sealed) == {URLS_ENCRYPTED, "other"}
        assert all(is_fernet_token(token) for token in sealed[URLS_ENCRYPTED])
        assert open_config(sealed, engine) == {URLS: [TGRAM, GOTIFY], "other": 1}

    def test_a_caller_supplied_ciphertext_key_is_dropped(self, engine: EncryptionEngine) -> None:
        assert seal_config({URLS_ENCRYPTED: ["json://internal/x"]}, engine) == {}

    def test_a_legacy_plaintext_row_opens_as_stored(self, engine: EncryptionEngine) -> None:
        assert open_config({URLS: [TGRAM]}, engine) == {URLS: [TGRAM]}

    def test_a_token_of_another_key_is_left_out_not_shown(self, engine: EncryptionEngine) -> None:
        foreign = EncryptionEngine(Fernet.generate_key().decode()).encrypt(TGRAM)
        own = engine.encrypt(GOTIFY)

        assert open_config({URLS_ENCRYPTED: [foreign, own, 7]}, engine) == {URLS: [GOTIFY]}

    def test_without_a_key_the_values_stay_plaintext_and_still_open(self) -> None:
        plain = EncryptionEngine("")

        sealed = seal_config({URLS: [TGRAM]}, plain)

        assert sealed == {URLS_ENCRYPTED: [TGRAM]}
        assert open_config(sealed, plain) == {URLS: [TGRAM]}


class TestExport:
    def test_ciphertext_and_plaintext_become_a_count(self, engine: EncryptionEngine) -> None:
        assert export_config({URLS_ENCRYPTED: [engine.encrypt(TGRAM)], "x": 1}) == {URLS_CONFIGURED: 1, "x": 1}
        assert export_config({URLS: [TGRAM, GOTIFY]}) == {URLS_CONFIGURED: 2}
        assert export_config({URLS: "garbage"}) == {URLS_CONFIGURED: 0}

    def test_a_config_without_urls_is_unchanged(self) -> None:
        assert export_config({"x": 1}) == {"x": 1}
