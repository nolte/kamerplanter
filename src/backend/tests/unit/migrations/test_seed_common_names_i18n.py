"""Every seeded species says which of its names are German and which English (#2902).

``common_names`` is a flat, language-mixed list and its order differs between the
seed files (species.yaml lists English first, the plant_info files German first), so
"first entry" showed English names in the German UI. ``common_names_i18n`` carries the
language. Its source is the Steckbrief row ``| Volksnamen (DE/EN) | <DE>; <EN> |``.

Pinned here, over the committed seed data:

(a) every seed entry with names carries a language map, and every name in it is one
    of the entry's ``common_names`` (the map never introduces a name);
(b) where a Steckbrief describes the same taxon, the preferred German name
    (``de[0]``) is the Steckbrief's first German name, and every name of a
    two-part Steckbrief row sits in the language list its side of the ``;`` names;
(c) named core species resolve to the German name a German gardener expects;
(d) a species seeded in two files carries the same names in both — the loaders
    sync names onto existing rows, two different lists would flip-flop per boot.

Comparator for (b): names are folded (casefold, ä/ö/ü/ß → ae/oe/ue/ss, hyphens,
spaces and apostrophes dropped, a trailing ``(…)`` qualifier removed), because some
Steckbriefe spell names transliterated ("Moehre") or hyphenated differently
("Lippenstift-Pflanze") while the seed keeps the real spelling ("Möhre").
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from app.domain.models.species import Species, validate_common_names_i18n
from app.migrations.seed_steckbrief_consistency import (
    _HTML_COMMENT,
    _normalize_name,
    _row_cells,
    parse_steckbrief,
    repo_root,
)

_ROOT = repo_root()
_SEED_DIR = _ROOT / "src" / "backend" / "app" / "migrations" / "seed_data"
_PLANTS_DIR = _ROOT / "spec" / "knowledge" / "plants"
_NAMES_ANCHOR = "`species.common_names`"

#: Seed files that carry species with vernacular names, and the list key holding them.
_SPECIES_FILES: dict[str, str] = {
    "species.yaml": "species",
    "plant_info.yaml": "new_species",
    "plant_info_indoor_1.yaml": "new_species",
    "plant_info_indoor_2.yaml": "new_species",
    "plant_info_indoor_3.yaml": "new_species",
    "plant_info_indoor_4.yaml": "new_species",
    "plant_info_outdoor_1.yaml": "new_species",
    "plant_info_outdoor_2.yaml": "new_species",
    "plant_info_outdoor_3.yaml": "new_species",
    "plant_info_supplement_1.yaml": "new_species",
    "adventskalender.yaml": "new_species",
}

#: Seed entries whose name-matched Steckbrief does NOT describe the seeded taxon, so
#: its first German name is not the species' preferred one. Each needs a reason.
_STECKBRIEF_DE_FIRST_EXCEPTIONS: dict[str, str] = {
    "Dahlia pinnata": "dahlia_x_hybrida_armateras.md is a cultivar sheet ('Dahlie Armateras'); "
    "the species row is dahlia_embassy.md 'Dahlie; Dahlia' (filed as 'Dahlia pinnata Cav.')",
}

#: Steckbrief tokens deliberately not taken into the seed: not a verifiable
#: vernacular name (E-10 — no value without a source the reviewer could confirm).
_UNTAKEN_STECKBRIEF_NAMES: frozenset[str] = frozenset({"Koemelkolben"})

_UMLAUTS = (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"))


def _fold(name: str) -> str:
    folded = re.sub(r"\s*\([^)]*\)\s*$", "", name).casefold()
    for umlaut, ascii_form in _UMLAUTS:
        folded = folded.replace(umlaut, ascii_form)
    return re.sub(r"[\s\-'’]", "", folded)


def _seed_entries() -> list[tuple[str, dict[str, Any]]]:
    entries: list[tuple[str, dict[str, Any]]] = []
    for filename, list_key in _SPECIES_FILES.items():
        doc = yaml.safe_load((_SEED_DIR / filename).read_text(encoding="utf-8")) or {}
        entries.extend((filename, entry) for entry in doc.get(list_key) or [] if entry.get("common_names"))
    return entries


def _steckbrief_rows() -> dict[str, str]:
    """``{normalized scientific name: raw 'Volksnamen (DE/EN)' cell}`` (first sheet wins)."""
    rows: dict[str, str] = {}
    for path in sorted(_PLANTS_DIR.glob("*.md")):
        sci = parse_steckbrief(path).get("scientific_name")
        if not sci or sci in rows:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if _NAMES_ANCHOR in line:
                cells = _row_cells(line)
                if cells and len(cells) >= 2:
                    rows[sci] = _HTML_COMMENT.sub("", cells[1]).strip()
                break
    return rows


_ENTRIES = _seed_entries()
_STECKBRIEFE = _steckbrief_rows()


def _id(item: tuple[str, dict[str, Any]]) -> str:
    return f"{item[0]}:{item[1]['scientific_name']}"


def test_the_corpus_is_what_the_issue_measured() -> None:
    # 213 named entries across ten files when #2902 was filed; a shrinking count
    # would mean a file silently dropped out of _SPECIES_FILES' reach.
    assert len(_ENTRIES) >= 213


@pytest.mark.parametrize("item", _ENTRIES, ids=_id)
def test_every_entry_has_a_language_map_within_its_names(item: tuple[str, dict[str, Any]]) -> None:
    _filename, entry = item
    names_i18n = entry.get("common_names_i18n")

    assert names_i18n, "no common_names_i18n — the UI would fall back to 'first entry', the #2902 defect"
    assert set(names_i18n) <= {"de", "en"}
    # Raises on a name outside common_names, an empty name or a bad key.
    assert validate_common_names_i18n(entry["common_names"], names_i18n) == names_i18n
    # And the model the loaders build accepts the pair.
    Species(scientific_name=entry["scientific_name"], common_names=entry["common_names"], common_names_i18n=names_i18n)


@pytest.mark.parametrize("item", _ENTRIES, ids=_id)
def test_the_preferred_german_name_is_the_steckbriefs(item: tuple[str, dict[str, Any]]) -> None:
    _filename, entry = item
    sci = entry["scientific_name"]
    raw = _STECKBRIEFE.get(_normalize_name(sci))
    if raw is None or sci in _STECKBRIEF_DE_FIRST_EXCEPTIONS:
        pytest.skip("no Steckbrief describes exactly this taxon")
    first_german = re.split(r"[;,]", raw, maxsplit=1)[0].strip()

    assert _fold(entry["common_names_i18n"]["de"][0]) == _fold(first_german)


@pytest.mark.parametrize("item", _ENTRIES, ids=_id)
def test_every_name_of_a_two_part_steckbrief_row_sits_in_its_language(item: tuple[str, dict[str, Any]]) -> None:
    _filename, entry = item
    sci = entry["scientific_name"]
    raw = _STECKBRIEFE.get(_normalize_name(sci))
    if raw is None or sci in _STECKBRIEF_DE_FIRST_EXCEPTIONS or raw.count(";") != 1:
        pytest.skip("no two-part 'DE; EN' Steckbrief row for exactly this taxon")
    names_i18n = entry["common_names_i18n"]
    for language, part in zip(("de", "en"), raw.split(";"), strict=True):
        listed = {_fold(name) for name in names_i18n.get(language, [])}
        for token in (t.strip() for t in part.split(",")):
            if not token or token in _UNTAKEN_STECKBRIEF_NAMES or _fold(token) == _fold(sci):
                continue
            assert _fold(token) in listed, f"Steckbrief {language} name {token!r} missing from common_names_i18n"


@pytest.mark.parametrize(
    ("scientific_name", "german", "english"),
    [
        ("Daucus carota", "Möhre", "Carrot"),
        ("Pisum sativum", "Erbse", "Garden Pea"),
        ("Solanum lycopersicum", "Tomate", "Tomato"),
        ("Cucurbita pepo", "Zucchini", "Zucchini"),
        ("Allium schoenoprasum", "Schnittlauch", "Chives"),
    ],
)
def test_core_species_resolve_to_the_expected_names(scientific_name: str, german: str, english: str) -> None:
    hits = [entry for _f, entry in _ENTRIES if entry["scientific_name"] == scientific_name]

    assert hits, f"{scientific_name} is not seeded"
    for entry in hits:
        assert entry["common_names_i18n"]["de"][0] == german
        assert entry["common_names_i18n"]["en"][0] == english


def test_a_species_seeded_twice_carries_the_same_names_in_both_files() -> None:
    seen: dict[str, tuple[str, dict[str, Any]]] = {}
    for filename, entry in _ENTRIES:
        key = _normalize_name(entry["scientific_name"])
        if key in seen:
            first_file, first = seen[key]
            assert (first["common_names"], first["common_names_i18n"]) == (
                entry["common_names"],
                entry["common_names_i18n"],
            ), f"{entry['scientific_name']}: {first_file} and {filename} disagree on the names"
        else:
            seen[key] = (filename, entry)


def test_the_comparator_folds_what_the_steckbriefe_transliterate() -> None:
    assert _fold("Möhre") == _fold("Moehre")
    assert _fold("Lippenstiftpflanze") == _fold("Lippenstift-Pflanze")
    assert _fold("Ahlbeere") == _fold("Ahlbeere (Norddeutschland)")
    assert _fold("Erbse") != _fold("Pea")


def test_the_seed_dir_resolves() -> None:
    assert isinstance(_SEED_DIR, Path) and (_SEED_DIR / "species.yaml").is_file()
