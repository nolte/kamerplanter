"""#2113 — SystemSettingsService encrypts the HA token and the Pl@ntNet key, decrypts for internal use only.

An in-memory repository double that keeps exactly what was upserted; the real
``EncryptionEngine`` with a key made at run time. The stored-document view
against a real ArangoDB is ``tests/integration/test_integration_secrets_at_rest.py``.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from app.domain.engines.encryption_engine import EncryptionEngine, is_fernet_token
from app.domain.models.system_settings import HomeAssistantSettings, PlantIdentificationSettings, SystemSettings
from app.domain.services.system_settings_service import SystemSettingsService

HA_TOKEN = "eyJ" + "hbGciOiJIUzI1NiJ9" + "-unit-2113"
PLANTNET_KEY = "2b10" + "UnitPlantnet2113"


class _Repo:
    def __init__(self, stored: SystemSettings | None = None) -> None:
        self.stored = stored
        self.replaced: list[tuple[str, str]] = []

    def get(self) -> SystemSettings | None:
        return self.stored.model_copy(deep=True) if self.stored is not None else None

    def upsert(self, settings: SystemSettings) -> SystemSettings:
        self.stored = settings.model_copy(deep=True)
        return settings

    def replace_plaintext_secret(
        self, *, block: str, field: str, legacy_field: str, plaintext: str, ciphertext: str
    ) -> bool:
        assert self.stored is not None
        section = getattr(self.stored, block)
        if getattr(section, field) != plaintext:
            return False
        setattr(section, field, ciphertext)
        self.replaced.append((block, legacy_field))
        return True


@pytest.fixture
def engine() -> EncryptionEngine:
    return EncryptionEngine(Fernet.generate_key().decode())


@pytest.fixture(autouse=True)
def _no_env_secrets():
    with patch("app.domain.services.system_settings_service.env_settings") as env:
        env.ha_url = ""
        env.ha_access_token = "env-token"
        env.ha_timeout = 10
        env.plantnet_api_key = "env-key"
        yield env


def test_a_written_ha_token_is_ciphertext_and_the_effective_reader_decrypts_it(engine: EncryptionEngine) -> None:
    repo = _Repo()
    service = SystemSettingsService(repo, engine)  # type: ignore[arg-type]

    service.update_ha_settings(ha_url="http://ha:8123", ha_access_token=HA_TOKEN, ha_timeout=None)

    assert repo.stored is not None
    assert is_fernet_token(repo.stored.home_assistant.ha_access_token_encrypted)
    assert HA_TOKEN not in repo.stored.model_dump_json()
    assert service.get_effective_ha_settings()["ha_access_token"] == HA_TOKEN
    info = service.get_ha_settings_with_source()
    assert (info["ha_access_token"], info["source_ha_access_token"]) == (HA_TOKEN, "db")


def test_an_empty_token_removes_the_stored_one_and_none_keeps_it(engine: EncryptionEngine) -> None:
    repo = _Repo()
    service = SystemSettingsService(repo, engine)  # type: ignore[arg-type]
    service.update_ha_settings(ha_url=None, ha_access_token=HA_TOKEN, ha_timeout=None)

    service.update_ha_settings(ha_url="http://ha:8123", ha_access_token=None, ha_timeout=None)
    assert service.get_effective_ha_settings()["ha_access_token"] == HA_TOKEN

    service.update_ha_settings(ha_url=None, ha_access_token="", ha_timeout=None)
    assert repo.stored is not None
    assert repo.stored.home_assistant.ha_access_token_encrypted is None
    assert service.get_effective_ha_settings()["ha_access_token"] == "env-token"


def test_a_written_plantnet_key_is_ciphertext_and_the_reader_decrypts_it(engine: EncryptionEngine) -> None:
    repo = _Repo()
    service = SystemSettingsService(repo, engine)  # type: ignore[arg-type]

    service.update_plant_identification_settings(PLANTNET_KEY)

    assert repo.stored is not None
    assert is_fernet_token(repo.stored.plant_identification.plantnet_api_key_encrypted)
    assert service.get_effective_plantnet_api_key() == PLANTNET_KEY
    assert service.get_plantnet_settings_with_source() == {
        "plantnet_api_key": PLANTNET_KEY,
        "source_plantnet_api_key": "db",
    }
    service.update_plant_identification_settings("")
    assert repo.stored.plant_identification.plantnet_api_key_encrypted is None


def test_legacy_plaintext_is_re_encrypted_once_on_read(engine: EncryptionEngine) -> None:
    repo = _Repo(
        SystemSettings(
            home_assistant=HomeAssistantSettings(**{"ha_access_token": HA_TOKEN}),
            plant_identification=PlantIdentificationSettings(**{"plantnet_api_key": PLANTNET_KEY}),
        )
    )
    service = SystemSettingsService(repo, engine)  # type: ignore[arg-type]

    assert service.get_effective_ha_settings()["ha_access_token"] == HA_TOKEN
    assert service.get_effective_plantnet_api_key() == PLANTNET_KEY
    service.get_ha_settings_with_source()

    assert repo.replaced == [("home_assistant", "ha_access_token"), ("plant_identification", "plantnet_api_key")]
    assert repo.stored is not None
    assert HA_TOKEN not in repo.stored.model_dump_json()
    assert PLANTNET_KEY not in repo.stored.model_dump_json()


def test_a_lost_race_keeps_the_concurrent_value(engine: EncryptionEngine) -> None:
    """The conditional swap did not match (a save in between): nothing is overwritten."""
    repo = _Repo(SystemSettings(home_assistant=HomeAssistantSettings(ha_access_token_encrypted=HA_TOKEN)))
    repo.replace_plaintext_secret = lambda **_kwargs: False  # type: ignore[method-assign]
    service = SystemSettingsService(repo, engine)  # type: ignore[arg-type]

    assert service.get_effective_ha_settings()["ha_access_token"] == HA_TOKEN


def test_without_a_key_nothing_is_rewritten_and_nothing_crashes() -> None:
    repo = _Repo(SystemSettings(home_assistant=HomeAssistantSettings(ha_access_token_encrypted=HA_TOKEN)))
    service = SystemSettingsService(repo, EncryptionEngine(""))  # type: ignore[arg-type]

    assert service.get_effective_ha_settings()["ha_access_token"] == HA_TOKEN
    service.update_plant_identification_settings(PLANTNET_KEY)

    assert repo.replaced == []
    assert repo.stored is not None
    assert repo.stored.plant_identification.plantnet_api_key_encrypted == PLANTNET_KEY


def test_a_token_of_another_key_reads_as_absent_and_the_env_value_applies(engine: EncryptionEngine) -> None:
    foreign = EncryptionEngine(Fernet.generate_key().decode()).encrypt(HA_TOKEN)
    repo = _Repo(
        SystemSettings(
            home_assistant=HomeAssistantSettings(ha_access_token_encrypted=foreign),
            plant_identification=PlantIdentificationSettings(plantnet_api_key_encrypted=foreign),
        )
    )
    service = SystemSettingsService(repo, engine)  # type: ignore[arg-type]

    assert service.get_effective_ha_settings()["ha_access_token"] == "env-token"
    assert service.get_effective_plantnet_api_key() == "env-key"
    assert repo.replaced == []
