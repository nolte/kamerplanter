"""REQ-044 WP-3 — operator CLI to build the few-shot pest prototype index.

Run once the inference service is deployed and reachable. Pulls CC0/CC-BY
images per pest/symptom/beneficial class from GBIF (public occurrence search,
no credentials), indexes the frozen-DINOv2 prototypes service-side, and writes
an attribution manifest (CC-BY compliance) — no images are persisted.

Usage:
    python -m app.migrations.acquire_pest_dataset [--manifest PATH] [--class SLUG]
"""

import argparse
import json
import sys

import structlog

from app.common.dependencies import get_pest_dataset_acquisition_service
from app.domain.models.pest_taxonomy import get_taxon

logger = structlog.get_logger()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the REQ-044 few-shot pest prototype index.")
    parser.add_argument(
        "--manifest",
        default="pest_reference_manifest.json",
        help="Where to write the attribution manifest.",
    )
    parser.add_argument(
        "--class",
        dest="class_slug",
        default=None,
        help="Acquire a single class (slug) instead of all.",
    )
    args = parser.parse_args(argv)

    service = get_pest_dataset_acquisition_service()

    if args.class_slug:
        taxon = get_taxon(args.class_slug)
        if taxon is None:
            print(f"Unknown class slug: {args.class_slug}", file=sys.stderr)
            return 2
        summary = service.acquire_for_class(taxon)
        manifest = summary.pop("manifest")
        results = {"classes": 1, "total_accepted": summary["accepted"], "results": [summary], "manifest": manifest}
    else:
        results = service.acquire_all()

    with open(args.manifest, "w", encoding="utf-8") as fh:
        json.dump(results["manifest"], fh, ensure_ascii=False, indent=2)

    print(
        f"Acquired {results['total_accepted']} prototypes across {results['classes']} classes. "
        f"Manifest: {args.manifest}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
