#!/usr/bin/env python3
"""Look at the subject's stored files after its erasure: gone, stripped, or still EXIF (#1745).

Observation step of the ``requirement-req025-art17-storage-cleanup-reaches-files``
reach probe. It opens the bytes on disk, never the erasure request's report, the
``attachments`` metadata or a log line: those are what the erasure says about
itself, and a strip that rewrote the metadata but not the file (or the other way
round) would pass for done.

For every file ``seed_stored_files.py`` uploaded
(``.reach/subjects/<subject>.files.json``) it reads
``<storage_root>/<storage_key>`` — the host side of the backend's object storage,
``storage_root`` from ``.reach/stack.json`` — and walks the JPEG's header
segments up to the start of scan: an ``APP1`` segment opening with ``Exif\\0\\0``
is EXIF, and a GPS IFD pointer (tag ``0x8825``) in its IFD0 is the location the
erasure has to remove. Bytes after the start of scan are pixels and are never
read as metadata.

Output, one member per line (the runner compares; this script states no verdict):

* ``deleted/<category>`` — the seeded file no longer exists;
* ``stripped/<category>`` — the file exists without an EXIF segment;
* ``exif/<category>`` — the file still carries EXIF (with or without GPS);
* ``seeded/<n>`` — how many files the seed uploaded, so the output is never empty.

``--counts`` prints ``<category> present=… exif=… gps=…`` instead, followed by
the same ``seeded/<n>`` line.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _reach_common import DEFAULT_SUBJECT, ReachError, reach_dir, read_stack  # noqa: E402

_SOI = b"\xff\xd8"
_APP1 = 0xE1
#: Start of scan and end of image: the header segments end at either.
_HEADER_END = (0xDA, 0xD9)
#: Markers without a length field (TEM, RST0..RST7).
_STANDALONE = {0x01, *range(0xD0, 0xD8)}
_EXIF_HEADER = b"Exif\x00\x00"
_GPS_IFD_POINTER = 0x8825


@dataclass
class Finding:
    category: str
    present: bool
    exif: bool
    gps: bool


def _exif_tiff(data: bytes) -> bytes | None:
    """The TIFF block of the first ``Exif`` APP1 segment before the scan data, or None."""
    if not data.startswith(_SOI):
        return None
    position = 2
    while position + 1 < len(data):
        if data[position] != 0xFF:
            return None
        marker = data[position + 1]
        if marker == 0xFF:  # fill byte before a marker
            position += 1
            continue
        if marker in _HEADER_END:
            return None
        if marker in _STANDALONE:
            position += 2
            continue
        if position + 4 > len(data):
            return None
        length = int.from_bytes(data[position + 2 : position + 4], "big")
        end = position + 2 + length
        if length < 2 or end > len(data):
            return None
        payload = data[position + 4 : end]
        if marker == _APP1 and payload.startswith(_EXIF_HEADER):
            return payload[len(_EXIF_HEADER) :]
        position = end
    return None


def jpeg_has_exif(data: bytes) -> bool:
    """Whether *data* is a JPEG whose header segments hold an EXIF block (pure; unit-tested)."""
    return _exif_tiff(data) is not None


def jpeg_has_gps(data: bytes) -> bool:
    """Whether the EXIF block's IFD0 points at a GPS IFD (tag ``0x8825``)."""
    tiff = _exif_tiff(data)
    if tiff is None or len(tiff) < 8:
        return False
    order = {b"II": "little", b"MM": "big"}.get(tiff[:2])
    if order is None or int.from_bytes(tiff[2:4], order) != 42:
        return False
    ifd = int.from_bytes(tiff[4:8], order)
    if ifd + 2 > len(tiff):
        return False
    entries = int.from_bytes(tiff[ifd : ifd + 2], order)
    for index in range(entries):
        entry = ifd + 2 + 12 * index
        if entry + 12 > len(tiff):
            return False
        if int.from_bytes(tiff[entry : entry + 2], order) == _GPS_IFD_POINTER:
            return True
    return False


def inspect(storage_root: Path, files: list[dict[str, Any]]) -> list[Finding]:
    """Read every seeded file under *storage_root*; a missing one is recorded, not an error."""
    root = storage_root.resolve()
    findings: list[Finding] = []
    for entry in files:
        path = (root / entry["storage_key"]).resolve()
        if root not in path.parents:
            raise ReachError(f"storage key {entry['storage_key']!r} resolves outside {root}")
        if not path.is_file():
            findings.append(Finding(entry["category"], present=False, exif=False, gps=False))
            continue
        data = path.read_bytes()
        findings.append(Finding(entry["category"], present=True, exif=jpeg_has_exif(data), gps=jpeg_has_gps(data)))
    return findings


def members(findings: list[Finding], seeded_total: int) -> list[str]:
    """Member lines for the inspected *findings* (pure; unit-tested)."""
    lines: list[str] = []
    for item in sorted(findings, key=lambda finding: finding.category):
        if not item.present:
            lines.append(f"deleted/{item.category}")
        elif item.exif:
            lines.append(f"exif/{item.category}")
        else:
            lines.append(f"stripped/{item.category}")
    lines.append(f"seeded/{seeded_total}")
    return lines


def count_lines(findings: list[Finding]) -> list[str]:
    """The raw ``--counts`` lines, one per category."""
    lines: list[str] = []
    for category in sorted({item.category for item in findings}):
        own = [item for item in findings if item.category == category]
        present = sum(item.present for item in own)
        exif = sum(item.exif for item in own)
        gps = sum(item.gps for item in own)
        lines.append(f"{category} present={present} exif={exif} gps={gps}")
    return lines


def files_record(subject: str) -> dict[str, Any]:
    path = reach_dir() / "subjects" / f"{subject}.files.json"
    if not path.is_file():
        raise ReachError(f"{path} is missing; run `task reach:seed:stored-files` first")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", default=DEFAULT_SUBJECT)
    parser.add_argument("--counts", action="store_true", help="print raw counts per category instead")
    args = parser.parse_args(argv)
    try:
        record = files_record(args.subject)
        findings = inspect(Path(read_stack()["storage_root"]), record["files"])
    except ReachError as exc:
        print(f"observe storage: {exc}", file=sys.stderr)
        return 1
    seeded = len(record["files"])
    lines = [*count_lines(findings), f"seeded/{seeded}"] if args.counts else members(findings, seeded)
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
