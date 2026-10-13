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

import re

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


#: The attachment namespace: ``t/{tenant_key}/{category}/{yyyy}/{mm}/{ulid}.{ext}``
#: (``StorageKeyBuilder.build``). The segment after it names a tenant.
TENANT_NAMESPACE = "t/"


def loggable_storage_key(key: str) -> str:
    """*key* as it may appear in a log line: every segment that names a person or a tenant masked.

    * An export-bundle key (``privacy/exports/<user_key>/<export_key>.json``)
      keeps its namespace and the export key, which is what a log reader
      correlates on; the account segment is replaced (#1773).
    * An attachment key (``t/<tenant_key>/<category>/<yyyy>/<mm>/<ulid>.<ext>``)
      keeps the category, the date partition, the ULID and the extension; the
      tenant segment becomes its salted log reference (``ten_…``,
      :func:`app.common.log_privacy.log_tenant`) — the same reference the
      service log lines carry, so a delete line still correlates with its
      tenant without naming it (#1966). The tenant key sits on the pseudonymised
      retention rows, and for a personal tenant it identifies its owner.
    * A prefix (``t/<tenant_key>/``, ``privacy/exports/<user_key>/``) and a bare
      segment are masked the same way. Every other key is returned unchanged —
      it carries neither.
    """
    stripped = key.lstrip("/")
    if stripped.startswith(TENANT_NAMESPACE):
        tenant_key, separator, rest = stripped[len(TENANT_NAMESPACE) :].partition("/")
        if not tenant_key:
            return key
        # Imported here: ``log_privacy`` imports this module for the free-text masking below.
        from app.common.log_privacy import log_tenant

        return f"{TENANT_NAMESPACE}{log_tenant(tenant_key)}{separator}{rest}"
    if not stripped.startswith(EXPORT_BUNDLE_NAMESPACE):
        return key
    remainder = stripped[len(EXPORT_BUNDLE_NAMESPACE) :]
    if not remainder:
        return key
    _subject, separator, rest = remainder.partition("/")
    return f"{EXPORT_BUNDLE_NAMESPACE}{REDACTED_SUBJECT_SEGMENT}{separator}{rest}"


#: An export-bundle key (or prefix) inside free text: the namespace and the
#: account segment up to the next separator a path or a quoted message uses.
_EMBEDDED_BUNDLE_KEY = re.compile(re.escape(EXPORT_BUNDLE_NAMESPACE) + r"[^/\s'\"]+")


def mask_export_bundle_keys(text: str) -> str:
    """*text* with the account segment of every embedded export-bundle key masked (#1773 review).

    For free text — an exception message — that reaches a log line: a storage
    error names the object it failed on (``[Errno 2] No such file or directory:
    '/data/privacy/exports/<user_key>/<export>.json'``). Masked the same way as
    :func:`loggable_storage_key`, whatever account the segment names; text
    without a bundle key is returned unchanged.
    """
    return _EMBEDDED_BUNDLE_KEY.sub(f"{EXPORT_BUNDLE_NAMESPACE}{REDACTED_SUBJECT_SEGMENT}", text)
