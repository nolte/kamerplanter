"""Object-key shape of a GDPR export bundle, and its loggable form (#1773).

The export bundle is the one object whose storage key embeds a data subject's
account key: ``privacy/exports/<user_key>/<export_key>.json``. Every other key
in object storage lives in the ``t/<tenant_key>/…`` namespace and names no
person. The storage adapters log the keys they touch, and a log stream has no
retention rule of its own (NFR-011), so a logged bundle key would outlive the
account, its erasure and the erasure record (R-06).

The shape and its redaction live in this one module on purpose: the adapters
do not know which caller builds which key, and a redaction that re-derived the
shape elsewhere could drift from the builder without either side noticing.
"""

from __future__ import annotations

#: Namespace of the export bundles; the segment after it is the account key.
EXPORT_BUNDLE_NAMESPACE = "privacy/exports/"

#: What replaces the account-key segment in a logged key.
REDACTED_SUBJECT_SEGMENT = "<subject>"


def export_bundle_key(user_key: str, export_key: str) -> str:
    """Storage key of one export bundle.

    Outside the ``t/{tenant}/...`` attachment namespace on purpose: the bundle
    spans every tenant the user belongs to and belongs to the user, not to any
    one of them.
    """
    return f"{EXPORT_BUNDLE_NAMESPACE}{user_key}/{export_key}.json"


def loggable_storage_key(key: str) -> str:
    """*key* as it may appear in a log line: the account-key segment masked.

    A bundle key keeps its namespace and the export key, which is what a log
    reader correlates on; the segment that names the account is replaced. A
    prefix (``privacy/exports/<user_key>/``) and a bare account segment are
    masked the same way. Every other key is returned unchanged — it carries no
    account key.
    """
    stripped = key.lstrip("/")
    if not stripped.startswith(EXPORT_BUNDLE_NAMESPACE):
        return key
    remainder = stripped[len(EXPORT_BUNDLE_NAMESPACE) :]
    if not remainder:
        return key
    _subject, separator, rest = remainder.partition("/")
    return f"{EXPORT_BUNDLE_NAMESPACE}{REDACTED_SUBJECT_SEGMENT}{separator}{rest}"
