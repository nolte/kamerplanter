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
import secrets

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


def email_digest(email: str) -> str:
    """Return a stable, non-plaintext digest of an email for log correlation.

    Follows the pseudonymisation convention already used for audit records
    (``ai_audit_logger.hash_question``, ``ErasureEngine.compute_tombstone_hash``):
    truncated sha256 over the normalised address. Repeated probes of the same
    address stay correlatable without writing the address itself into a log
    stream that has no retention rule of its own (NFR-011) — the address in a
    suppressed-duplicate event belongs to a third party who never consented to
    the request that mentioned it.
    """
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:16]
