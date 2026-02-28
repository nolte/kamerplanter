from cryptography.fernet import Fernet

from app.domain.engines.encryption_engine import EncryptionEngine


class TestEncryptionEngineEnabled:
    key = Fernet.generate_key().decode()

    def test_roundtrip(self):
        engine = EncryptionEngine(self.key)
        plaintext = "my-secret-client-secret"
        ciphertext = engine.encrypt(plaintext)
        assert ciphertext != plaintext
        assert engine.decrypt(ciphertext) == plaintext

    def test_enabled_flag(self):
        engine = EncryptionEngine(self.key)
        assert engine.enabled is True

    def test_different_ciphertext_each_time(self):
        engine = EncryptionEngine(self.key)
        ct1 = engine.encrypt("same-value")
        ct2 = engine.encrypt("same-value")
        # Fernet includes a timestamp, so ciphertexts differ
        assert ct1 != ct2

    def test_empty_string(self):
        engine = EncryptionEngine(self.key)
        ciphertext = engine.encrypt("")
        assert engine.decrypt(ciphertext) == ""

    def test_unicode_roundtrip(self):
        engine = EncryptionEngine(self.key)
        plaintext = "Geheimer Schlüssel mit Ümläuten: äöüß"
        assert engine.decrypt(engine.encrypt(plaintext)) == plaintext


class TestEncryptionEngineDisabled:
    def test_plaintext_passthrough(self):
        engine = EncryptionEngine("")
        secret = "my-plain-secret"
        assert engine.encrypt(secret) == secret
        assert engine.decrypt(secret) == secret

    def test_enabled_flag_false(self):
        engine = EncryptionEngine("")
        assert engine.enabled is False


class TestDecryptionFallback:
    def test_invalid_ciphertext_returns_input(self):
        key = Fernet.generate_key().decode()
        engine = EncryptionEngine(key)
        # If someone stored plaintext before encryption was enabled,
        # decrypt should return it as-is (fallback)
        assert engine.decrypt("not-a-valid-fernet-token") == "not-a-valid-fernet-token"

    def test_wrong_key_returns_input(self):
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()
        engine1 = EncryptionEngine(key1)
        engine2 = EncryptionEngine(key2)
        ciphertext = engine1.encrypt("secret")
        # Wrong key → InvalidToken → falls back to ciphertext
        assert engine2.decrypt(ciphertext) == ciphertext
