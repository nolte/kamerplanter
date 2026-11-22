"""File readers and arrangements for the REQ-053 wave 9 export E2E (WP 9.16, issue #2756) and the offline photo case.

FILE READERS (pure, no browser)
------------------------------
* :func:`png_size` - width and height from a PNG's ``IHDR``; raises for anything that is no PNG.
* :func:`pdf_outline_titles` - the bookmark titles of a PDF. WeasyPrint turns every ``<h1>``-``<h6>`` of the print
  template into an outline entry (its user-agent stylesheet sets ``bookmark-level``), so the garden plan PDF lists
  "Gartenplan: <Standort>" and, with the parcel page, "Parzellenliste: <Standort>" (``templates/print/
  garden_plan.html``). The E2E image has no PDF library (``tests/e2e/pyproject.toml``); the titles are read from the
  raw objects and from every Flate stream (object streams hold the outline dictionaries in a compressed PDF). The
  reader cannot read body text: the page content is glyph ids of a subset font. What it cannot read, it does not
  claim - a caller pairs every "title absent" with a "title present" on the same file.
* :func:`expected_png_size` - the Python reference of ``fitViewport`` (``routes/fitViewport.ts``) and
  ``resolvePngSize`` (``io/pngExport.ts``): the plan's content box fitted into 1 200 px, times the factor, capped
  at the canvas limits. Mirrored, not imported - the test states the rule it checks.

ARRANGEMENTS (the application's own routes, `test-pyramid-foundation` §"Arrangement-Treue")
-------------------------------------------------------------------------------------
* :func:`add_water_source` - ``POST /sites/{key}/plan/batch`` with one ``create_garden_object`` of class
  ``water_source`` (a point, ``water_source_kind`` given) - the editor's own save.
* :func:`create_bed_template` / :func:`bed_templates` - ``POST`` / ``GET /bed-templates`` (GP-FR-044).
* :func:`complete_task_via_api` - ``POST /tasks/{key}/complete`` with an empty body: "someone closed the task
  meanwhile" (WP 9.3's ``409 task.already_closed`` precondition).
* :func:`bed_list_rows` - ``GET /locations?site_key=&supports_layout=true``: what the bed list reads since WP 10.8
  (beds, plus tents and shelves - the same rows on a garden of beds), with ``nearest_water_source_m``.
"""

from __future__ import annotations

import math
import re
import struct
import uuid
import zlib
from pathlib import Path

from ._garden_plan_helpers import _api, _require, _tenant_post, tenant_get, tenant_request
from ._journey_helpers import _api_request

# ── PNG ─────────────────────────────────────────────────────────────────────

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_size(data: bytes) -> tuple[int, int]:
    """``(width, height)`` of a PNG from its ``IHDR`` chunk; raises when *data* is no PNG."""
    if data[:8] != PNG_SIGNATURE:
        raise AssertionError(f"the file is no PNG: it starts with {data[:8]!r}")
    if data[12:16] != b"IHDR":
        raise AssertionError(f"the PNG has no IHDR as its first chunk: {data[12:16]!r}")
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def write_solid_png(path: Path, size: int = 96) -> Path:
    """A solid-colour PNG of *size* x *size* px in a colour unique to this call (UUID-derived bytes).

    Unique on purpose: the attachment store deduplicates an uploader's identical bytes (SHA-256).
    """
    colour = uuid.uuid4().bytes[:3]
    raw = b"".join(b"\x00" + colour * size for _ in range(size))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    path.write_bytes(
        PNG_SIGNATURE
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )
    return path


#: ``io/pngExport.ts``: the 1x image fits the plan into this box; the canvas limits cap larger factors.
PNG_BASE_EDGE_PX = 1200
MAX_CANVAS_EDGE_PX = 16_384
MAX_CANVAS_AREA_PX = 16_777_216
#: ``routes/fitViewport.ts``.
_MARGIN_RATIO = 0.05
_MAX_PX_PER_M = 200.0
_MIN_PX_PER_M = 0.5


def _js_round(value: float) -> int:
    """``Math.round``: halves go up (Python's ``round`` goes to even)."""
    return int(math.floor(value + 0.5))


def expected_png_size(bounds: tuple[float, float, float, float], factor: int) -> tuple[int, int]:
    """The PNG size the export must produce for a plan whose content box is *bounds* (metres) at *factor*.

    ``fitViewport(bounds, 1200, 1200)``: a margin of 5 % of the longer side on every side, the larger of the two
    fits (clamped to 0.5 ... 200 px/m), the box rounded to whole pixels. ``resolvePngSize``: times *factor*,
    floored, unless the factor exceeds the canvas limits (then the largest fitting factor, two decimals).
    """
    min_x, min_y, max_x, max_y = bounds
    size_x = max(max_x - min_x, 0.1)
    size_y = max(max_y - min_y, 0.1)
    margin = max(size_x, size_y) * _MARGIN_RATIO
    content_w = size_x + 2 * margin
    content_h = size_y + 2 * margin
    fit = min(PNG_BASE_EDGE_PX / content_w, PNG_BASE_EDGE_PX / content_h)
    px_per_m = min(_MAX_PX_PER_M, max(_MIN_PX_PER_M, fit))
    base_w = max(1, _js_round(content_w * px_per_m))
    base_h = max(1, _js_round(content_h * px_per_m))
    fitting = min(
        MAX_CANVAS_EDGE_PX / base_w,
        MAX_CANVAS_EDGE_PX / base_h,
        math.sqrt(MAX_CANVAS_AREA_PX / (base_w * base_h)),
    )
    applied = math.floor(fitting * 100) / 100 if factor > fitting else factor
    return max(1, math.floor(base_w * applied)), max(1, math.floor(base_h * applied))


# ── PDF bookmarks ───────────────────────────────────────────────────────────

_STREAM = re.compile(rb"stream\r?\n")
_TITLE = re.compile(rb"/Title\s*")


def _streams(data: bytes) -> list[bytes]:
    """Every ``stream`` body that inflates with zlib (Flate); other filters (images, fonts in other codecs) are not
    text and are left out on purpose - the count of what inflated is returned with the titles' source."""
    inflated: list[bytes] = []
    for match in _STREAM.finditer(data):
        start = match.end()
        end = data.find(b"endstream", start)
        if end < 0:
            break
        # No rstrip of the end-of-line before ``endstream``: compressed bytes may themselves end in CR or LF, and
        # cutting them made a stream (and the outline in it) vanish now and then. The decompressor stops at the
        # end of the zlib stream by itself and leaves the trailing end-of-line as unused data.
        inflater = zlib.decompressobj()
        try:
            body = inflater.decompress(data[start:end])
        except zlib.error:
            continue  # not Flate (a DCT image, an uncompressed stream): holds no outline dictionary
        if inflater.eof:
            inflated.append(body)
    return inflated


def _literal(buffer: bytes, start: int) -> tuple[bytes, int]:
    """A PDF literal string starting after its ``(``: the raw bytes (escapes resolved) and the end position."""
    out = bytearray()
    depth = 1
    i = start
    while i < len(buffer):
        char = buffer[i]
        if char == 0x5C:  # backslash
            nxt = buffer[i + 1 : i + 2]
            mapping = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f"}
            if nxt in mapping:
                out += mapping[nxt]
                i += 2
            elif nxt.isdigit():
                digits = re.match(rb"[0-7]{1,3}", buffer[i + 1 : i + 4])
                out.append(int(digits.group(0), 8) & 0xFF)  # type: ignore[union-attr]
                i += 1 + len(digits.group(0))  # type: ignore[union-attr]
            elif nxt in (b"\r", b"\n"):
                i += 2
            else:
                out += nxt
                i += 2
            continue
        if char == 0x28:
            depth += 1
        elif char == 0x29:
            depth -= 1
            if depth == 0:
                return bytes(out), i + 1
        out.append(char)
        i += 1
    raise AssertionError("an unterminated PDF string in an outline title")


def _decode(raw: bytes) -> str:
    if raw.startswith(b"\xfe\xff"):
        return raw[2:].decode("utf-16-be")
    return raw.decode("latin-1")


def _titles_in(buffer: bytes) -> list[str]:
    titles: list[str] = []
    for match in _TITLE.finditer(buffer):
        position = match.end()
        opener = buffer[position : position + 1]
        if opener == b"(":
            raw, _end = _literal(buffer, position + 1)
            titles.append(_decode(raw))
        elif opener == b"<":
            close = buffer.find(b">", position)
            hexdigits = re.sub(rb"\s+", b"", buffer[position + 1 : close])
            titles.append(_decode(bytes.fromhex(hexdigits.decode("ascii"))))
    return titles


def pdf_outline_titles(data: bytes) -> list[str]:
    """Every ``/Title`` string of a PDF (outline entries and the document info), in file order.

    Raises when *data* is no PDF. An empty list is a valid answer only for a PDF without bookmarks - which the
    garden plan PDF never is (its ``<h1>`` "Gartenplan: …"); callers assert that title first.
    """
    if not data.startswith(b"%PDF-"):
        raise AssertionError(f"the file is no PDF: it starts with {data[:8]!r}")
    titles = _titles_in(data)
    for stream in _streams(data):
        titles.extend(_titles_in(stream))
    return titles


# ── Arrangements ────────────────────────────────────────────────────────────


def add_water_source(
    base_url: str,
    seed: dict,
    *,
    site_key: str,
    revision: int,
    point: tuple[float, float],
    label: str,
) -> tuple[str, int]:
    """One tap (class ``water_source``, a point, kind ``tap``) on the plan; ``(object key, new revision)``."""
    api, token = _api(base_url, seed)
    status, body = _api_request(
        f"{api}/sites/{site_key}/plan/batch",
        "POST",
        token,
        {
            "expected_revision": revision,
            "operations": [
                {
                    "op": "create_garden_object",
                    "temp_key": "tap",
                    "data": {
                        "object_type": "water_source",
                        "label": label,
                        "geometry": {"kind": "point", "origin": [float(point[0]), float(point[1])]},
                        "props": {"water_source_kind": "tap"},
                    },
                }
            ],
        },
    )
    _require(status, body, (200,), f"POST /sites/{site_key}/plan/batch (water source)")
    key = (body.get("key_map") or {}).get("tap")
    if not key:
        raise AssertionError(
            f"Self-provisioning failed: the batch answered no key for the tap: {body!r}"
        )
    return str(key), int(body["plan_revision"])


def bed_list_rows(base_url: str, seed: dict, site_key: str) -> dict[str, dict]:
    """``GET /locations?site_key=&supports_layout=true`` by key - the rows the bed list and its water column read."""
    body = tenant_get(
        base_url, seed, f"/locations?site_key={site_key}&supports_layout=true&limit=200"
    )
    rows = body.get("items") if isinstance(body, dict) else body
    if not isinstance(rows, list):
        raise AssertionError(f"the bed list of {site_key!r} is not a list: {body!r}")
    return {str(row["key"]): row for row in rows}


def create_bed_template(base_url: str, seed: dict, *, name: str) -> dict:
    """A tenant template "<name>": raised bed 1.6 x 0.8 m, 0.4 m high, rows 25 cm, spacing 20 cm."""
    return _tenant_post(
        base_url,
        seed,
        "/bed-templates",
        {
            "name": name,
            "location_type_key": "raised_bed",
            "default_geometry": {
                "kind": "rect",
                "origin": [0.0, 0.0],
                "width_m": 1.6,
                "length_m": 0.8,
                "rotation_deg": 0.0,
            },
            "height_m": 0.4,
            "default_layout": {"row_spacing_cm": 25.0, "spacing_cm": 20.0},
            "recurring_task_templates": [],
        },
        expected=(201,),
    )


def bed_templates(base_url: str, seed: dict) -> list[dict]:
    """``GET /bed-templates``: the system templates and the tenant's own."""
    body = tenant_get(base_url, seed, "/bed-templates?limit=200")
    if not isinstance(body, list):
        raise AssertionError(f"GET /bed-templates is not a list: {body!r}")
    return body


def complete_task_via_api(base_url: str, seed: dict, task_key: str) -> dict:
    """``POST /tasks/{key}/complete`` with nothing but the completion - a second device closing the task."""
    status, body = tenant_request(base_url, seed, "POST", f"/tasks/{task_key}/complete", {})
    _require(status, body, (200,), f"POST /tasks/{task_key}/complete")
    if not isinstance(body, dict) or body.get("status") != "completed":
        raise AssertionError(f"Self-provisioning failed: the task did not close: {body!r}")
    return body


__all__ = [
    "PNG_BASE_EDGE_PX",
    "add_water_source",
    "bed_list_rows",
    "bed_templates",
    "complete_task_via_api",
    "create_bed_template",
    "expected_png_size",
    "pdf_outline_titles",
    "png_size",
    "write_solid_png",
]
