#!/usr/bin/env python3
"""Upload one real photo with GPS EXIF per attachment category for the seeded subject (#1745).

Runs **inside the backend container** of the reach stack (``stack.py seed-files``
ships it there together with ``observe_storage_residue.py`` and
``_reach_common.py``) and prints one JSON record to stdout: which file of which
category the subject now owns in object storage, so the storage observation on
the host knows where to look. It is an environment step, not an observation: it
asserts nothing about reach.

Every file goes through the production upload pipeline —
``AttachmentService.upload`` built from the DI providers ``get_object_storage()``
and ``get_attachment_repo()``, the objects the API and the worker use — with the
subject as ``created_by`` and the subject's personal tenant as ``tenant_key``.
The one deviation is a settings copy with ``storage_strip_exif=False``: it
stands in for a deployment that runs with ``STORAGE_STRIP_EXIF=false`` (the
setting NFR-013 §4.2 provides), the only deployment in which a stored photo
still carries the GPS block the Art. 17 erasure (Phase 0) has to remove. With
the default, the upload strips EXIF at ingest and the erasure's strip would have
nothing to prove itself on.

Each category gets a distinct JPEG (a different colour, so the upload's SHA-256
dedup cannot fold two categories into one object) with an EXIF block holding a
GPS IFD, and a neutral file name that does not name the subject. A category
whose MIME whitelist refuses ``image/jpeg`` (import, export, tenant export) is
recorded under ``refused``: that is the product's rule, not a seed failure.

After the uploads the seed reads every stored object back through the storage
adapter and fails when it carries no GPS EXIF — read both with Pillow and with
the observer's own marker walk. A seeded file without EXIF would make any later
``stripped/<category>`` certify nothing.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import observe_storage_residue as observer  # noqa: E402 — shipped beside this file

MIME_TYPE = "image/jpeg"
_GPS_IFD = 0x8825
_MAKE = 0x010F


class SeedError(RuntimeError):
    """The files cannot be seeded as required; the environment fails."""


def seed_jpeg(position: int) -> bytes:
    """A small JPEG, distinct per *position*, carrying EXIF with a GPS IFD (pure; unit-tested)."""
    colour = ((position * 67) % 256, (position * 131 + 40) % 256, (position * 29 + 90) % 256)
    image = Image.new("RGB", (32, 32), colour)
    exif = Image.Exif()
    exif[_MAKE] = "reach-seed-camera"
    gps = exif.get_ifd(_GPS_IFD)
    gps[1] = "N"
    gps[2] = (52.0, 31.0, float(position))
    gps[3] = "E"
    gps[4] = (13.0, 24.0, float(position))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", exif=exif, quality=90)
    return buffer.getvalue()


def _pillow_sees_gps(data: bytes) -> bool:
    with Image.open(io.BytesIO(data)) as image:
        return bool(image.getexif().get_ifd(_GPS_IFD))


async def _read_back(storage: Any, storage_key: str) -> bytes:
    chunks = [chunk async for chunk in await storage.get_object(storage_key)]
    return b"".join(chunks)


async def seed(subject: str, tenant_key: str) -> dict[str, Any]:
    from app.common.dependencies import get_attachment_repo, get_object_storage
    from app.common.enums import AttachmentCategory
    from app.common.exceptions import InvalidFileTypeError
    from app.config.settings import settings
    from app.domain.services.attachment_service import AttachmentService

    storage = get_object_storage()
    service = AttachmentService(
        storage=storage,
        attachment_repo=get_attachment_repo(),
        settings=settings.model_copy(update={"storage_strip_exif": False}),
    )
    files: list[dict[str, str]] = []
    refused: list[str] = []
    for position, category in enumerate(AttachmentCategory):
        try:
            attachment = await service.upload(
                tenant_key=tenant_key,
                user_key=subject,
                data=seed_jpeg(position),
                mime_type=MIME_TYPE,
                original_filename=f"reach-photo-{category.value}.jpg",
                category=category,
            )
        except InvalidFileTypeError:
            refused.append(category.value)
            continue
        if attachment.key is None:
            raise SeedError(f"the {category.value} upload returned no attachment key")
        files.append(
            {"category": category.value, "attachment_key": attachment.key, "storage_key": attachment.storage_key}
        )

    for entry in files:
        stored = await _read_back(storage, entry["storage_key"])
        if not (_pillow_sees_gps(stored) and observer.jpeg_has_gps(stored)):
            raise SeedError(
                f"the stored {entry['category']} file carries no GPS EXIF; the upload stripped it, "
                "so an erasure observation on it would certify nothing"
            )
    if not files:
        raise SeedError("no category accepted an image/jpeg upload")
    return {"subject": subject, "tenant_key": tenant_key, "files": files, "refused": refused}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", required=True)
    parser.add_argument("--tenant-key", required=True)
    args = parser.parse_args(argv)
    try:
        record = asyncio.run(seed(args.subject, args.tenant_key))
    except SeedError as exc:
        print(f"seed files: {exc}", file=sys.stderr)
        return 1
    json.dump(record, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
