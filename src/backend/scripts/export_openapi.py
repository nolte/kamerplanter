"""Export the OpenAPI document without a running stack.

Imports the FastAPI app, renders ``app.openapi()`` deterministically (sorted
keys, two-space indent, trailing newline) and writes it to ``--out`` or stdout.
This is the reproducible export command required by
spec/project/api-documentation/ for a code-first repository; CI re-exports the
document and diffs it against the checked-in snapshot (src/backend/openapi.json).

Usage:
    python -m scripts.export_openapi [--out openapi.json] [--check]

``--check`` exits non-zero when ``--out`` exists and differs from the fresh
export (drift gate for CI).

The export also fails when a router uses a tag that is not declared in
``app.api.v1.openapi_tags.OPENAPI_TAGS`` — keeping the top-level tag list
complete is a MUST of the API-documentation contract.
"""

import argparse
import json
import os
import sys
from pathlib import Path

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def build_document() -> dict:
    # The mounted surface depends on runtime flags (light mode drops the auth
    # routers, the knowledge router is optional). Pin the flags to the full
    # surface BEFORE the app import so the snapshot is deterministic and
    # complete regardless of the local environment.
    os.environ["KAMERPLANTER_MODE"] = "full"
    os.environ["KNOWLEDGE_SERVICE_ENABLED"] = "true"

    # Route import-time structlog output to stderr so stdout stays a clean
    # JSON document (structlog's default PrintLogger writes to stdout).
    import structlog

    structlog.configure(logger_factory=structlog.PrintLoggerFactory(sys.stderr))

    from app.main import app

    return app.openapi()


def validate_tags(document: dict) -> list[str]:
    """Return tags used by operations but missing from the top-level declaration."""
    declared = {tag["name"] for tag in document.get("tags", [])}
    used: set[str] = set()
    for path_item in document.get("paths", {}).values():
        for method, operation in path_item.items():
            if method in HTTP_METHODS:
                used.update(operation.get("tags", []))
    return sorted(used - declared)


def render(document: dict) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None, help="Write the document to this path instead of stdout.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write; exit 1 when --out differs from the fresh export (CI drift gate).",
    )
    args = parser.parse_args()

    document = build_document()

    undeclared = validate_tags(document)
    if undeclared:
        print(
            f"ERROR: {len(undeclared)} tag(s) used by operations but not declared in "
            f"app/api/v1/openapi_tags.py: {', '.join(undeclared)}",
            file=sys.stderr,
        )
        return 2

    rendered = render(document)

    if args.check:
        if args.out is None:
            print("ERROR: --check requires --out.", file=sys.stderr)
            return 2
        if not args.out.exists():
            print(f"ERROR: snapshot {args.out} missing.", file=sys.stderr)
            return 1
        if args.out.read_text() != rendered:
            print(
                f"ERROR: {args.out} is stale. Regenerate with: python -m scripts.export_openapi --out {args.out}",
                file=sys.stderr,
            )
            return 1
        print(f"OK: {args.out} matches the generated document.")
        return 0

    if args.out is not None:
        args.out.write_text(rendered)
        print(f"Wrote {args.out} ({len(document.get('paths', {}))} paths).")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
