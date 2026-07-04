#!/usr/bin/env python3
"""Extract species-level overwintering templates from the plant Steckbriefe.

Reads the §4.3 "Überwinterung" table of every ``spec/knowledge/plants/*.md`` and
emits a schema-conformant seed file
(``src/backend/app/migrations/seed_data/overwintering_profiles.yaml``) of
``OverwinteringProfileTemplate`` entries (REQ-022 §OverwinteringProfile).

Design goals:

* **Deterministic & re-runnable** — same inputs always produce the same output;
  entries are sorted by slug so diffs are stable.
* **No fabrication** — only values that can be confidently normalised from the
  curated tables are emitted. Anything ambiguous is omitted and counted in the
  review log printed to stderr.
* **Prefix-tolerant** — the ``KA-Feld`` column has drifted across docs
  (``overwintering_profiles.`` / ``overwintering_profile.`` / ``overwintering.``);
  matching keys on the field segment after the last dot absorbs that drift.

Usage::

    python3 scripts/extract_overwintering_templates.py            # write the seed file
    python3 scripts/extract_overwintering_templates.py --check    # dry-run, report only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLANTS_DIR = REPO_ROOT / "spec" / "knowledge" / "plants"
OUT_FILE = (
    REPO_ROOT
    / "src"
    / "backend"
    / "app"
    / "migrations"
    / "seed_data"
    / "overwintering_profiles.yaml"
)

# ── Enum vocabularies (mirrored from app.common.enums; kept local so the
#    extractor stays runnable without importing the backend package). ──────────
HARDINESS = ("dig_and_store", "needs_protection", "frost_free", "hardy")
WINTER_ACTION = (
    "move_indoors",
    "dig_store",
    "earth_up",
    "fleece",
    "mulch",
    "wrap",
    "none",
)
SPRING_ACTION = ("move_outdoors", "harden_off", "uncover", "replant", "prune")
LIGHT = ("semi_bright", "bright", "dark")
WATERING = ("minimal", "reduced", "normal", "none")
TUBER = ("pre_sprouting", "dig_pending", "planted", "growing", "drying", "stored")

_NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


def _first_enum(text: str, vocab: tuple[str, ...]) -> str | None:
    """Return the enum token that appears earliest in ``text`` (word-boundary)."""
    best: tuple[int, str] | None = None
    lowered = text.lower()
    for token in vocab:
        match = re.search(rf"\b{re.escape(token)}\b", lowered)
        if match and (best is None or match.start() < best[0]):
            best = (match.start(), token)
    return best[1] if best else None


def _first_int(text: str, lo: int, hi: int) -> int | None:
    for raw in _NUM.findall(text):
        value = int(float(raw.replace(",", ".")))
        if lo <= value <= hi:
            return value
    return None


def _numbers(text: str) -> list[float]:
    # Normalise the Unicode minus (U+2212) so "−20 °C" is read as a number.
    text = text.replace("−", "-")
    return [float(raw.replace(",", ".")) for raw in _NUM.findall(text)]


def _quarter_numbers(text: str) -> list[float]:
    """Non-negative temperatures from a winter-quarter cell.

    A winter quarter is by definition frost-free (≥ 0 °C), so every dash here is a
    range separator — including the ASCII double-hyphen "10--15" and en-dash "10–15"
    used across the Steckbriefe — never a minus sign. Neutralising them prevents the
    trailing range endpoint from being misread as a negative number.
    """
    cleaned = re.sub(r"[−–—]|--", " ", text)
    cleaned = re.sub(
        r"(?<=\d)\s*-\s*(?=\d)", " ", cleaned
    )  # single hyphen between digits
    return [
        float(raw.replace(",", ".")) for raw in re.findall(r"\d+(?:[.,]\d+)?", cleaned)
    ]


def _is_na_strict(value: str) -> bool:
    """True when a cell is truly not-applicable for *any* field (dash / 'entfällt').

    Deliberately does NOT treat "Freiland" as N/A: in a hardiness or action cell
    ("hardy, überwintert im Freiland") it is meaningful context, not absence.
    """
    stripped = value.strip()
    if stripped[:1] in {"—", "–", "-"} and not re.match(r"-?\d", stripped):
        return True
    lowered = stripped.lower()
    markers = ("nicht zutreffend", "entfällt", "entfaellt", "nicht relevant")
    return any(m in lowered for m in markers)


def _is_na_quarter(value: str) -> bool:
    """True when a *winter-quarter* cell means "no quarter" (field-overwintered)."""
    if _is_na_strict(value):
        return True
    lowered = value.strip().lower()
    markers = (
        "kein quartier",
        "freiland",
        "nicht nötig",
        "nicht noetig",
        "kein geschütztes",
        "kein geschuetztes",
    )
    return any(m in lowered for m in markers)


def _map_light(text: str) -> str | None:
    token = _first_enum(text, LIGHT)
    if token:
        return token
    lowered = text.lower()
    # Drop negated dark phrases ("kein Dunkellager", "nicht dunkel") first.
    lowered = re.sub(r"kein\w*\s+dunkel\w*", "", lowered)
    lowered = re.sub(r"nicht\s+dunkel\w*", "", lowered)
    candidates: list[tuple[int, str]] = []
    for keyword, mapped in (
        ("dunkel", "dark"),
        ("dark", "dark"),
        ("halb", "semi_bright"),
        ("semi", "semi_bright"),
        ("indirekt", "semi_bright"),
        ("hell", "bright"),
        ("sonn", "bright"),
        ("bright", "bright"),
    ):
        idx = lowered.find(keyword)
        if idx >= 0:
            candidates.append((idx, mapped))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1]


def _map_watering(text: str) -> str | None:
    token = _first_enum(text, WATERING)
    if token:
        return token
    lowered = text.lower()
    if "keine" in lowered or "kein " in lowered or "trocken" in lowered:
        return "none"
    if "minimal" in lowered:
        return "minimal"
    if (
        "sparsam" in lowered
        or "reduziert" in lowered
        or "reduc" in lowered
        or "wenig" in lowered
    ):
        return "reduced"
    if "normal" in lowered:
        return "normal"
    return None


def _map_winter_action(text: str) -> str | None:
    token = _first_enum(text, WINTER_ACTION)
    if token:
        return token
    lowered = text.lower()
    if (
        "einräum" in lowered
        or "einraeum" in lowered
        or "ins haus" in lowered
        or "drinnen" in lowered
    ):
        return "move_indoors"
    if "ausgrab" in lowered or "einlager" in lowered or "einschlag" in lowered:
        return "dig_store"
    if "vlies" in lowered:
        return "fleece"
    if (
        "anhäuf" in lowered
        or "anhaeuf" in lowered
        or "häufeln" in lowered
        or "haeufeln" in lowered
    ):
        return "earth_up"
    if "umwickel" in lowered or "einpack" in lowered or "einwickel" in lowered:
        return "wrap"
    if "mulch" in lowered or "laub" in lowered or "stroh" in lowered:
        return "mulch"
    return None


def _map_spring_action(text: str) -> str | None:
    token = _first_enum(text, SPRING_ACTION)
    if token:
        return token
    lowered = text.lower()
    if "abhärt" in lowered or "abhaert" in lowered:
        return "harden_off"
    if (
        "nach drau" in lowered
        or "ins freie" in lowered
        or "ausräum" in lowered
        or "ausraeum" in lowered
    ):
        return "move_outdoors"
    if "abräum" in lowered or "abraeum" in lowered or "abdeckung entfern" in lowered:
        return "uncover"
    if "umpflanz" in lowered or "neu einpflanz" in lowered or "umtopf" in lowered:
        return "replant"
    if (
        "rückschnitt" in lowered
        or "schneiden" in lowered
        or "zurückschneiden" in lowered
    ):
        return "prune"
    return None


#: Infraspecific connectors that are part of the name, not an author citation.
_INFRA_MARKERS = {"var.", "subsp.", "ssp.", "f.", "cv.", "subvar.", "convar.", "×", "x"}


def _normalize_sci_name(raw: str) -> str:
    """Reduce a curated name to the binomial the species collection stores.

    Drops synonym parentheticals ("(syn. …)"), cultivar quotes ("'Great Silence'")
    and trailing author citations ("Cav."), while keeping infraspecific markers
    (``var.`` / ``subsp.`` / ``×`` …). Without this, cultivar-level Steckbriefe like
    ``Dahlia pinnata Cav.`` never resolve to species ``Dahlia pinnata`` and their
    templates seed with an empty ``species_key``.
    """
    name = re.split(r"\s*\(", raw.strip())[0]  # drop "(syn. …)"
    name = re.split(r"[‘’']", name)[0]  # drop 'Cultivar' quotes onwards
    parts = name.split()
    if len(parts) <= 2:
        return " ".join(parts)
    kept = parts[:2]  # genus + epithet (or genus + hybrid marker)
    i = 2
    while i < len(parts):
        word = parts[i]
        if word.lower() in _INFRA_MARKERS:
            kept.append(word)
            if i + 1 < len(parts):
                kept.append(parts[i + 1])
                i += 2
                continue
            i += 1
            continue
        if word[:1].islower():  # an unmarked lowercase epithet part — keep
            kept.append(word)
            i += 1
            continue
        break  # a capitalised token is an author citation — stop here
    # The species collection spells hybrids with an ASCII "x", not the Unicode "×".
    return " ".join(kept).replace("×", "x")


def _scientific_name(text: str) -> str | None:
    """Pull the scientific name from the ``species.scientific_name`` KA-Feld row."""
    for row in _table_rows(text):
        if len(row) >= 3 and "species.scientific_name" in row[-1] and row[1]:
            return _normalize_sci_name(row[1])
    # Fallback: H1 "Common — Genus species".
    heading = re.search(r"^#\s+.*?—\s*(.+)$", text, re.M)
    return _normalize_sci_name(heading.group(1)) if heading else None


def _table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    text = re.sub(
        r"<!--.*?-->", "", text, flags=re.S
    )  # drop inline provenance comments
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in stripped.strip("|").split("|")]
        # Skip markdown separator rows (---|---).
        if all(set(c) <= {"-", ":", ""} for c in cells):
            continue
        rows.append(cells)
    return rows


def _overwintering_section(text: str) -> str | None:
    """Slice the §4.3 Überwinterung section out of a Steckbrief."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^#{2,4}\s", line) and "berwinterung" in line.lower():
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^##\s", lines[j]):  # next level-2 section
            end = j
            break
    return "\n".join(lines[start:end])


def _parse_entry(slug: str, text: str) -> tuple[dict | None, list[str]]:
    """Return (entry, warnings). ``entry`` is None when no §4.3 table is present."""
    warnings: list[str] = []
    section = _overwintering_section(text)
    if section is None:
        return None, [f"{slug}: no §4.3 Überwinterung section"]

    fields: dict[str, object] = {}
    for row in _table_rows(section):
        if len(row) < 3:
            continue
        ka_cell = next((c for c in row if "overwintering" in c.lower()), None)
        if ka_cell is None:
            continue
        field = ka_cell.lower().split(".")[-1].strip()
        value = row[1]
        if not value or _is_na_strict(value):
            continue
        if field.startswith("winter_quarter") and _is_na_quarter(value):
            continue

        if field == "hardiness_rating":
            fields["hardiness_rating"] = _first_enum(value, HARDINESS)
        elif field == "winter_action":
            fields["winter_action"] = _map_winter_action(value)
            month = _first_int(value, 1, 12)
            if month is not None:
                fields.setdefault("winter_action_month", month)
        elif field == "winter_action_month":
            fields["winter_action_month"] = _first_int(value, 1, 12)
        elif field == "spring_action":
            fields["spring_action"] = _map_spring_action(value)
            month = _first_int(value, 1, 12)
            if month is not None:
                fields.setdefault("spring_action_month", month)
        elif field == "spring_action_month":
            fields["spring_action_month"] = _first_int(value, 1, 12)
        elif field == "winter_quarter_temp_min":
            nums = _quarter_numbers(value)
            if nums:
                fields["winter_quarter_temp_min"] = nums[0]
        elif field == "winter_quarter_temp_max":
            nums = _quarter_numbers(value)
            if nums:
                fields["winter_quarter_temp_max"] = nums[0]
        elif field == "winter_quarter_temp_c":  # legacy combined "a–b (Minimum c)" cell
            nums = _quarter_numbers(value)
            if nums:
                # The range is the FIRST two numbers; trailing "(Minimum x)" is ignored.
                pair = nums[:2]
                fields.setdefault("winter_quarter_temp_min", min(pair))
                fields.setdefault("winter_quarter_temp_max", max(pair))
        elif field == "winter_quarter_light":
            fields["winter_quarter_light"] = _map_light(value)
        elif field in {"winter_watering", "winter_quarter_watering"}:
            fields["winter_watering"] = _map_watering(value)
        elif field == "storage_medium":
            fields["storage_medium"] = value
        elif field == "storage_check_interval_days":
            fields["storage_check_interval_days"] = _first_int(value, 1, 365)
        elif field == "tuber_status":
            fields["tuber_status"] = _first_enum(value, TUBER)

    # Drop keys that normalised to None.
    fields = {k: v for k, v in fields.items() if v is not None}

    required = ("hardiness_rating", "winter_action")
    missing = [r for r in required if r not in fields]
    if missing:
        return None, [
            f"{slug}: §4.3 present but missing required field(s): {', '.join(missing)}"
        ]

    # tuber_status is only valid for dig_and_store (mirror the model invariant).
    if fields.get("tuber_status") and fields.get("hardiness_rating") != "dig_and_store":
        warnings.append(
            f"{slug}: dropped tuber_status (hardiness_rating != dig_and_store)"
        )
        fields.pop("tuber_status")

    sci = _scientific_name(text)
    if not sci:
        return None, [f"{slug}: could not resolve scientific_name"]

    entry: dict[str, object] = {"_key": slug, "species_scientific_name": sci}
    entry.update(fields)
    return entry, warnings


def _dump_yaml(entries: list[dict]) -> str:
    """Emit deterministic YAML (no PyYAML dependency; controlled field order)."""
    order = [
        "_key",
        "species_scientific_name",
        "hardiness_rating",
        "winter_action",
        "winter_action_month",
        "spring_action",
        "spring_action_month",
        "winter_quarter_temp_min",
        "winter_quarter_temp_max",
        "winter_quarter_light",
        "winter_watering",
        "storage_medium",
        "storage_check_interval_days",
        "tuber_status",
        "notes",
    ]

    def fmt(value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float):
            return str(int(value)) if value.is_integer() else str(value)
        if isinstance(value, int):
            return str(value)
        text = str(value)
        if text == "" or re.search(r"[:#\"'\n]", text) or text != text.strip():
            return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return text

    lines = [
        "# yaml-language-server: $schema=./schemas/overwintering_profiles.schema.yaml",
        "# GENERATED by scripts/extract_overwintering_templates.py — DO NOT EDIT BY HAND.",
        "# Source: spec/knowledge/plants/*.md §4.3 Überwinterung (REQ-022 §OverwinteringProfile).",
        "# Re-generate: python3 scripts/extract_overwintering_templates.py",
        "overwintering_profiles:",
    ]
    for entry in entries:
        first = True
        for key in order:
            if key not in entry:
                continue
            prefix = "  - " if first else "    "
            lines.append(f"{prefix}{key}: {fmt(entry[key])}")
            first = False
    return "\n".join(lines) + "\n"


def build() -> tuple[str, list[dict], list[str]]:
    """Extract every template and return (yaml_text, entries, warnings).

    Pure and deterministic — the single source of truth shared by the CLI and the
    seed-drift test, so a manual edit to the generated file is caught.
    """
    entries: list[dict] = []
    warnings: list[str] = []
    for path in sorted(PLANTS_DIR.glob("*.md")):
        entry, warns = _parse_entry(path.stem, path.read_text(encoding="utf-8"))
        warnings.extend(warns)
        if entry is not None:
            entries.append(entry)

    entries.sort(key=lambda e: e["_key"])

    # Non-fatal data-quality pass: flag rating↔action D5-path inconsistencies in the
    # *source* Steckbriefe. Not enforced (templates are reference data; D5 is checked
    # at instance time against the real site zone), only surfaced for curator review.
    path_b_ratings = {"frost_free", "dig_and_store"}
    path_b_actions = {"move_indoors", "dig_store"}
    for entry in entries:
        exp_b = entry["hardiness_rating"] in path_b_ratings
        act_b = entry["winter_action"] in path_b_actions
        if exp_b != act_b:
            warnings.append(
                f"{entry['_key']}: D5 rating/action mismatch "
                f"(rating={entry['hardiness_rating']}, action={entry['winter_action']})"
            )
        # A relocation action needs a month, or the "move indoors before frost"
        # reminder can never fire for a plant reusing this template.
        if (
            entry["winter_action"] in path_b_actions
            and "winter_action_month" not in entry
        ):
            warnings.append(
                f"{entry['_key']}: relocation action '{entry['winter_action']}' has no "
                f"winter_action_month — winter reminder will not fire (fill §4.3 in the Steckbrief)"
            )

    return _dump_yaml(entries), entries, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="dry-run: report only, do not write"
    )
    args = parser.parse_args()

    output, entries, warnings = build()

    print(
        f"extracted {len(entries)} overwintering templates from {len(list(PLANTS_DIR.glob('*.md')))} Steckbriefe",
        file=sys.stderr,
    )
    skips = [w for w in warnings if "no §4.3" in w]
    print(
        f"  {len(skips)} without a §4.3 section (mostly true annuals — expected)",
        file=sys.stderr,
    )
    for w in warnings:
        if "no §4.3" not in w:
            print(f"  REVIEW: {w}", file=sys.stderr)

    if args.check:
        return 0
    OUT_FILE.write_text(output, encoding="utf-8")
    print(f"wrote {OUT_FILE.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
