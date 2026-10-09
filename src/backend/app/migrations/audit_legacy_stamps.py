"""List rows whose author is not a member of their tenant — the v0004 stamp audit (MT-052, #2144). Read-only.

Migration ``v0004`` stamped every row without a ``tenant_key`` with one default
tenant. On a volume that held more than one person's data at the time, some rows
now belong — by their key — to a tenant their author never joined. This command
measures that: for every row with a ``tenant_key`` and an author field
(``created_by`` or ``*_by_key``) it asks whether the author holds a membership in
that tenant, and prints per collection and field how many rows are

* ``member``  — the author is an active member (expected),
* ``former``  — the author's membership exists but is inactive,
* ``never``   — the author holds no membership row in that tenant: the v0004
  suspect (or a member whose row a removal deleted).

It changes nothing; ``--dry-run`` is accepted for symmetry with the other operator
commands and is what every run is. What to do with ``never`` rows is a legal and
business decision (re-assign, keep, delete) — see ``app/migrations/README.md``
("Historisches Risiko: v0004-Stempel"). Only document keys are printed, never an
account key or address.

Usage (inside the backend container / with the backend settings in the environment)::

    python -m app.migrations.audit_legacy_stamps [--dry-run] [--sample N]

Exit codes: 0 measured and no ``never`` row, 3 measured and ``never`` rows exist
(something for the operator to decide), 1 the database could not be read, 2 usage.
"""

from __future__ import annotations

import argparse

import structlog
from arango.database import StandardDatabase

from app.data_access.arango.legacy_stamp_audit import ArangoLegacyStampAudit, StampAuditReport

logger = structlog.get_logger(__name__)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_FINDINGS = 3


def _connect() -> StandardDatabase:
    """The configured database — refused when it was never initialised (an empty one measures nothing)."""
    from arango.client import ArangoClient

    from app.config.settings import settings
    from app.data_access.arango import collections as col

    client = ArangoClient(hosts=f"http://{settings.arangodb_host}:{settings.arangodb_port}")
    db = client.db(settings.arangodb_database, username=settings.arangodb_username, password=settings.arangodb_password)
    if not db.has_collection(col.MEMBERSHIPS) or not db.has_collection(col.TENANTS):
        msg = (
            f"database {settings.arangodb_database!r} has no memberships/tenants collection: it was never "
            "initialised. Check ARANGODB_DATABASE; nothing was measured."
        )
        raise RuntimeError(msg)
    return db


def render(report: StampAuditReport) -> list[str]:
    lines = [f"Collections scanned: {report.collections_scanned}"]
    if not report.findings:
        lines.append("No row with a tenant_key carries an author field. Nothing to classify.")
        return lines
    lines.append(f"  {'collection':<32} {'field':<28} {'status':<7} {'rows':>8}  sample document keys")
    for f in sorted(report.findings, key=lambda f: (f.status != "never", f.collection, f.field, f.status)):
        lines.append(f"  {f.collection:<32} {f.field:<28} {f.status:<7} {f.count:>8}  {', '.join(f.sample)}")
    lines.append(
        f"Totals: member={report.count('member')} former={report.count('former')} never={report.count('never')}"
    )
    if report.count("never"):
        lines.append(
            "Rows marked 'never' name an author without a membership in the row's tenant — the v0004 "
            "default-tenant stamp is one cause. Nothing was changed; deciding about them is a legal/business "
            "decision (app/migrations/README.md)."
        )
    else:
        lines.append("No 'never' row: no sign of a v0004 stamp on a foreign author's data.")
    return lines


def main(argv: list[str] | None = None, *, audit: ArangoLegacyStampAudit | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="accepted for symmetry: every run only reads")
    parser.add_argument("--sample", type=int, default=5, metavar="N", help="document keys printed per line (0-50)")
    args = parser.parse_args(argv)
    if not 0 <= args.sample <= 50:
        parser.error("--sample takes 0..50")

    try:
        report = (audit or ArangoLegacyStampAudit(_connect(), sample=args.sample)).measure()
    except Exception as exc:  # noqa: BLE001 — an operator tool reports and exits non-zero
        from app.common.log_privacy import loggable_error

        logger.error("legacy_stamp_audit_failed", error=loggable_error(exc))
        print(f"Failed: {type(exc).__name__}: nothing was measured, nothing was changed.")
        return EXIT_ERROR
    for line in render(report):
        print(line)
    return EXIT_FINDINGS if report.count("never") else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
