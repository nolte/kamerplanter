"""Command-line entrypoint for the migration framework (NFR-016 O-2).

``python -m app.migrations {upgrade|downgrade|current|history|create}``

``create`` scaffolds the next ``vNNNN_<slug>.py`` from a template so authors get
idempotent up/down stubs, a :class:`MigrationReport` return and a docstring for
free.  Everything else operates against the live database resolved via the
dependency layer.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import structlog

from app.migrations.framework.report import MigrationReport
from app.migrations.framework.runner import MigrationRunner

logger = structlog.get_logger()

_VERSIONS_DIR = Path(__file__).resolve().parent.parent / "versions"
_SLUG_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_MODULE_RE = re.compile(r"^v(?P<number>\d{4})_[a-z0-9_]+\.py$")

_TEMPLATE = '''"""{title}

TODO: describe the one-time transformation this migration performs.

Idempotency (M-3): re-running MUST be a no-op — only touch documents that still
need changing.  Dry-run (M-5): honour ``dry_run`` by computing the report without
writing.  Reversibility (M-6): keep ``reversible = False`` and let ``down`` raise
unless you can honestly invert the change.
"""

from __future__ import annotations

from arango.database import StandardDatabase

from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport


class {class_name}(Migration):
    version = "{version}"
    name = "{slug}"
    description = "TODO: one-line description"
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        scanned = 0
        changed = 0
        # TODO: implement the idempotent, dry-run-aware transformation.
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=dry_run,
        )


migration = {class_name}()
'''


def _next_version() -> str:
    """Return the next zero-padded version based on the existing modules."""
    highest = 0
    for path in _VERSIONS_DIR.glob("v*.py"):
        match = _MODULE_RE.match(path.name)
        if match:
            highest = max(highest, int(match.group("number")))
    return str(highest + 1).zfill(4)


def _class_name(slug: str) -> str:
    return "".join(part.capitalize() for part in slug.split("_")) + "Migration"


def scaffold_migration(slug: str) -> Path:
    """Create the next ``vNNNN_<slug>.py`` from the template; return its path."""
    if not _SLUG_RE.match(slug):
        raise ValueError(f"Invalid slug {slug!r}: use lower_snake_case starting with a letter")
    version = _next_version()
    path = _VERSIONS_DIR / f"v{version}_{slug}.py"
    if path.exists():
        raise FileExistsError(f"{path} already exists")
    title = f"v{version}_{slug} — {slug.replace('_', ' ')}"
    path.write_text(
        _TEMPLATE.format(title=title, class_name=_class_name(slug), version=version, slug=slug),
        encoding="utf-8",
    )
    return path


def _format_report(report: MigrationReport) -> str:
    return (
        f"  {report.version} {report.name}: scanned={report.scanned} "
        f"changed={report.changed} dry_run={report.dry_run} duration_ms={report.duration_ms}"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.migrations", description="Kamerplanter migration framework")
    sub = parser.add_subparsers(dest="command", required=True)

    upgrade = sub.add_parser("upgrade", help="apply pending migrations")
    upgrade.add_argument("--to", dest="target", default=None, help="apply up to this version (inclusive)")
    upgrade.add_argument("--dry-run", action="store_true", help="compute reports without writing")

    downgrade = sub.add_parser("downgrade", help="roll back migrations above --to")
    downgrade.add_argument("--to", dest="target", required=True, help="target version to roll back to (inclusive)")
    downgrade.add_argument("--dry-run", action="store_true", help="compute reports without writing")

    sub.add_parser("current", help="print the highest applied version")
    sub.add_parser("history", help="print the applied-migration history")

    create = sub.add_parser("create", help="scaffold the next migration module")
    create.add_argument("slug", help="lower_snake_case slug for the new migration")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint. Returns a process exit code."""
    from app.config.logging import setup_logging

    setup_logging()
    args = _build_parser().parse_args(argv)

    if args.command == "create":
        path = scaffold_migration(args.slug)
        print(f"Created {path}")  # noqa: T201 — intentional CLI output
        return 0

    from app.common.dependencies import get_db

    db = get_db()
    runner = MigrationRunner()

    if args.command == "upgrade":
        reports = runner.upgrade(db, target=args.target, dry_run=args.dry_run)
        if not reports:
            print("No pending migrations.")  # noqa: T201
        else:
            print(f"{'Planned' if args.dry_run else 'Applied'} {len(reports)} migration(s):")  # noqa: T201
            for report in reports:
                print(_format_report(report))  # noqa: T201
        return 0

    if args.command == "downgrade":
        reports = runner.downgrade(db, target=args.target, dry_run=args.dry_run)
        print(f"{'Planned rollback of' if args.dry_run else 'Reverted'} {len(reports)} migration(s):")  # noqa: T201
        for report in reports:
            print(_format_report(report))  # noqa: T201
        return 0

    if args.command == "current":
        print(runner.current(db) or "(none)")  # noqa: T201
        return 0

    if args.command == "history":
        rows = runner.history(db)
        if not rows:
            print("(no migrations applied)")  # noqa: T201
        for row in rows:
            print(  # noqa: T201
                f"  {row.get('version')} {row.get('name')} "
                f"applied_at={row.get('applied_at')} status={row.get('status')}"
            )
        return 0

    return 1  # pragma: no cover - argparse enforces a valid subcommand
