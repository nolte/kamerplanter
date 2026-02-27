import bcrypt

# NIST 800-63B: min 10 chars, no complexity rules
MIN_PASSWORD_LENGTH = 10

# bcrypt has a hard 72-byte limit on password input
_BCRYPT_MAX_BYTES = 72


def _truncate_for_bcrypt(password: str) -> bytes:
    """Encode and truncate password to 72 bytes (bcrypt limit)."""
    encoded = password.encode("utf-8")
    return encoded[:_BCRYPT_MAX_BYTES]


class PasswordEngine:
    """Pure logic for password hashing and validation — no DB access."""

    def hash_password(self, password: str) -> str:
        pw_bytes = _truncate_for_bcrypt(password)
        return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        pw_bytes = _truncate_for_bcrypt(plain)
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))

    def validate_password_policy(self, password: str) -> list[str]:
        """Validate password against NIST 800-63B policy. Returns list of violation messages."""
        errors: list[str] = []
        if len(password) < MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        if len(password) > 128:
            errors.append("Password must not exceed 128 characters.")
        return errors
