"""Redaction for the E2E seed-data log (SEC-006).

The seed fixture dumps its whole result dict to ``test-reports/e2e_seed_data.log``
for post-mortem debugging. In full mode that dict carries ``access_token`` — a
live JWT for the demo account. The file is gitignored and the CI artifact upload
does not currently include it, so nothing leaks today; but the report path is
exactly the kind of thing that gets generalised ("upload test-reports/"), and
then a valid token sits in a 14-day-retention artifact.

Tokens are therefore masked before the dict is written. Deliberately
dependency-free (no selenium import) so the rule is unit-testable.
"""

from __future__ import annotations

from typing import Any

#: Placeholder written instead of a secret value.
REDACTED = "<redacted>"

#: Substrings that mark a key as secret-bearing. Matched case-insensitively on
#: the key name, so a future ``refresh_token``/``api_key``/``password`` entry is
#: covered without touching this module again.
_SECRET_KEY_MARKERS: tuple[str, ...] = ("token", "secret", "password", "api_key", "apikey", "credential")


def _is_secret_key(key: Any) -> bool:
    return isinstance(key, str) and any(marker in key.lower() for marker in _SECRET_KEY_MARKERS)


def redact_secrets(value: Any) -> Any:
    """Return *value* with every secret-bearing entry replaced by :data:`REDACTED`.

    Recurses through dicts and lists, so a token nested in a seeded sub-object is
    masked too. Non-container values are returned unchanged. A falsy secret (an
    absent token in light mode) is left as-is, so the log still shows that the
    field was empty rather than implying a redacted value.
    """
    if isinstance(value, dict):
        return {
            key: (REDACTED if _is_secret_key(key) and item else redact_secrets(item)) for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    return value


def format_seed_log(api: str, mode: str, result: dict) -> str:
    """Render the seed log body with every secret masked."""
    return f"api={api}\nmode={mode}\nresult={redact_secrets(result)}\n"
