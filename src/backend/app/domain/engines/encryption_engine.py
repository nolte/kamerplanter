"""Fernet-based encryption engine for OIDC client secrets (SK-06)."""

import structlog
from cryptography.fernet import Fernet, InvalidToken

logger = structlog.get_logger()


class EncryptionEngine:
    """Encrypt/decrypt sensitive values using Fernet symmetric encryption.

    When fernet_key is empty, operates in plaintext passthrough mode (dev only).
    """

    def __init__(self, fernet_key: str) -> None:
        if fernet_key:
            self._fernet = Fernet(fernet_key.encode())
            self._enabled = True
        else:
            self._fernet = None
            self._enabled = False
            logger.warning("encryption_disabled", reason="No FERNET_KEY configured. Secrets stored in plaintext.")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def encrypt(self, plaintext: str) -> str:
        if not self._enabled or not self._fernet:
            return plaintext
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        if not self._enabled or not self._fernet:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.error("decryption_failed", hint="Ciphertext may be plaintext from before encryption was enabled.")
            return ciphertext
