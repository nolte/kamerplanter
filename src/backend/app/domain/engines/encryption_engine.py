"""Fernet-based encryption engine for OIDC client secrets (SK-06)."""

import structlog
from cryptography.fernet import Fernet, InvalidToken

logger = structlog.get_logger()

#: Version byte of every Fernet token (spec: ``0x80``), base64url-encoded: every
#: token starts with ``gAAAAA`` and is at least 57 bytes before encoding.
_FERNET_TOKEN_PREFIX = "gAAAAA"
_MIN_FERNET_TOKEN_LENGTH = 100


class SecretKeyMismatchError(RuntimeError):
    """A stored Fernet token cannot be opened with the configured ``FERNET_KEY`` (#1859).

    Raised instead of handing the ciphertext back as if it were the secret. The
    message carries neither the token nor anything decrypted.
    """


def is_usable_fernet_key(key: str) -> bool:
    """Whether ``key`` is a key ``Fernet`` accepts — the one check both start gates use (#1859)."""
    if not key:
        return False
    try:
        Fernet(key.encode())
    except ValueError:  # malformed base64 or not 32 bytes
        return False
    return True


def _looks_like_a_fernet_token(value: str) -> bool:
    return value.startswith(_FERNET_TOKEN_PREFIX) and len(value) >= _MIN_FERNET_TOKEN_LENGTH


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
            # Decision (#1859): two very different things raise InvalidToken.
            # * A value that is not a Fernet token at all is plaintext stored
            #   before encryption was enabled. No migration has encrypted every
            #   such row, so it keeps passing through — refusing it would lock
            #   out working configurations on upgrade.
            # * A value that IS a Fernet token was encrypted with another key
            #   (a worker or backend with a drifted FERNET_KEY, a rotation that
            #   reached one process only). Returning it handed the ciphertext to
            #   an OIDC provider or InvenTree as the credential, silently. That
            #   is refused loudly.
            # Once a migration has encrypted every legacy row, the passthrough
            # can go too and every InvalidToken becomes a refusal.
            if _looks_like_a_fernet_token(ciphertext):
                logger.error("decryption_key_mismatch")
                raise SecretKeyMismatchError(
                    "A stored secret cannot be decrypted with the configured FERNET_KEY; "
                    "the backend and the worker must use the key it was encrypted with."
                ) from None
            logger.warning("decryption_legacy_plaintext", hint="Value predates encryption; re-save to encrypt it.")
            return ciphertext
