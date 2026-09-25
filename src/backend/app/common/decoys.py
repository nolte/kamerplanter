"""Shared helpers for the account-enumeration guards.

Several surfaces have to answer "this address is already taken" without saying
so: registration (SEC-H-009), login (SEC-H-010) and the Art. 16 email change.
Each of them synthesises a response that is indistinguishable from the genuine
one, and each of them logs the event without writing the probed address down in
the clear. These two helpers are what that has in common; they lived privately
in ``auth_service`` until the third call site made the duplication worse than
the import.
"""

import hashlib
import hmac
import secrets

from app.config.constants import MIN_TOMBSTONE_SALT_LENGTH
from app.config.settings import settings

#: Digit count of a synthesised, never-stored ArangoDB ``_key``.
#:
#: ArangoDB's default (traditional) key generator produces a plain decimal
#: counter value, so a decoy of the same character class and width is the
#: closest a synthesised key can get to a genuinely generated one.
_DECOY_DOCUMENT_KEY_DIGITS = 7


def decoy_document_key() -> str:
    """Return a random, never-stored key shaped like an ArangoDB-generated one.

    The value identifies no document: it is never written, and every
    key-addressed endpoint requires authentication, so the (negligible) chance
    of colliding with a real key grants the caller nothing.

    Fresh on every call, deliberately. A *stable* decoy key would itself
    fingerprint the address it was handed out for.
    """
    lower = 10 ** (_DECOY_DOCUMENT_KEY_DIGITS - 1)
    return str(lower + secrets.randbelow(9 * lower))


#: What :func:`email_digest` returns without a usable salt — never the unkeyed hash.
UNAVAILABLE_EMAIL_DIGEST = "unavailable"


def email_digest(email: str) -> str:
    """Return a keyed, non-plaintext pseudonym of an email for log correlation.

    Repeated probes of the same address stay correlatable without writing the
    address itself into a log stream that has no retention rule of its own
    (NFR-011) — the address in a suppressed-duplicate event belongs to a third
    party who never consented to the request that mentioned it.

    **Keyed, not a plain hash** (#1781). An unkeyed sha256 over an e-mail
    address is dictionary-reversible: addresses are a small, enumerable space,
    so anyone holding the log stream could confirm a guessed address by hashing
    it. The digest is 16 hex chars of an HMAC-SHA256 over the normalised
    address, keyed with the tombstone salt under the purpose label
    ``log-email`` — separated from the tombstone hash and from
    ``ErasureEngine.log_subject`` (``log-subject``). An operator holding the
    salt can still compute the digest of a given address.

    Read by log calls only: no stored value or lookup depends on it, so a salt
    rotation breaks nothing but cross-deploy log correlation.

    A missing or short salt must not turn a log line into an error, and must not
    fall back to the unkeyed hash either: it yields the constant
    :data:`UNAVAILABLE_EMAIL_DIGEST` (cf. ``anon_unavailable`` of
    ``ErasureEngine.log_subject``). The salt is read at call time.
    """
    salt = settings.erasure_tombstone_salt
    if not salt or len(salt) < MIN_TOMBSTONE_SALT_LENGTH:
        return UNAVAILABLE_EMAIL_DIGEST
    normalised = email.strip().lower()
    return hmac.new(salt.encode("utf-8"), f"log-email:{normalised}".encode(), hashlib.sha256).hexdigest()[:16]
