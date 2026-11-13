"""Every seeded disease and beneficial says which of its names is German and which English (#2936).

Diseases carried one English ``common_name`` and beneficials one German ``common_name``, so
the German UI showed "Powdery Mildew" and the English UI "Raubmilben". Both now carry
``common_names_i18n`` (REQ-010 v1.8). A translation is only seeded with a source (E-10);
a language without one stays absent and the UI shows the stored name instead.

Pinned here, over the committed seed data:

(a) every seeded disease names its stored ``common_name`` as its English name;
(b) every seeded disease has a German name, or is in the explicit gap list below — and
    every gap-list entry is a real disease that still has none;
(c) every seeded German disease name carries its source on the same line;
(d) every beneficial taxon has its German name, and an English one or a gap-list entry;
    every English name sits under a ``# Source:`` comment in ``pest_taxonomy.py``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import Disease
from app.domain.models.pest_taxonomy import beneficial_taxa

_APP = Path(__file__).resolve().parents[3] / "app"
_IPM_SEED = _APP / "migrations" / "seed_data" / "ipm.yaml"
_TAXONOMY = _APP / "domain" / "models" / "pest_taxonomy.py"

#: Seeded diseases for which no German name was found in a source (checked 2026-11-13).
#: Each shows its stored English ``common_name`` in the German UI until a sourced name is added.
DISEASES_WITHOUT_A_SOURCED_GERMAN_NAME: frozenset[str] = frozenset(
    {
        "Xanthomonas campestris",
        "Puccinia spp.",
        "Septoria lycopersici",
        "Pseudoperonospora cubensis",
        "Rhizoctonia solani",
        "Fusarium solani",
        "Erwinia carotovora",
        "Fluoride Toxicity (Abiotic)",
        "Ramularia nymphaearum",
        "Erwinia spp. / Pythium spp.",
    }
)

#: Beneficial taxa (slug) without a sourced English name: the English UI shows the German one.
BENEFICIALS_WITHOUT_A_SOURCED_ENGLISH_NAME: frozenset[str] = frozenset({"parasitoid_wasp"})

_SOURCE_COMMENT = re.compile(r"#\s*Source:\s*https://\S+")


def _seeded_diseases() -> list[dict[str, Any]]:
    data = yaml.safe_load(_IPM_SEED.read_text(encoding="utf-8"))
    return list(data["diseases"])


def _ids(rows: list[dict[str, Any]]) -> list[str]:
    return [row["scientific_name"] for row in rows]


@pytest.mark.parametrize("row", _seeded_diseases(), ids=_ids(_seeded_diseases()))
def test_a_seeded_disease_names_its_stored_name_as_english(row: dict[str, Any]) -> None:
    disease = Disease.model_validate(row)

    assert disease.common_names_i18n.get("en") == [disease.common_name]


@pytest.mark.parametrize("row", _seeded_diseases(), ids=_ids(_seeded_diseases()))
def test_a_seeded_disease_has_a_german_name_or_is_a_listed_gap(row: dict[str, Any]) -> None:
    disease = Disease.model_validate(row)
    has_german = bool(disease.common_names_i18n.get("de"))

    if disease.scientific_name in DISEASES_WITHOUT_A_SOURCED_GERMAN_NAME:
        assert not has_german, f"{disease.scientific_name} has a German name now: drop it from the gap list"
    else:
        assert has_german, f"{disease.scientific_name} has no German name and is not in the gap list"


def test_the_gap_list_names_only_seeded_diseases() -> None:
    assert set(_ids(_seeded_diseases())) >= DISEASES_WITHOUT_A_SOURCED_GERMAN_NAME


def test_every_seeded_german_disease_name_carries_its_source() -> None:
    lines = _IPM_SEED.read_text(encoding="utf-8").splitlines()
    start, end = lines.index("diseases:"), lines.index("treatments:")
    german_lines = [line for line in lines[start:end] if line.strip().startswith("de: [")]

    assert len(german_lines) == len(_seeded_diseases()) - len(DISEASES_WITHOUT_A_SOURCED_GERMAN_NAME)
    assert [line for line in german_lines if not _SOURCE_COMMENT.search(line)] == []


@pytest.mark.parametrize("taxon", beneficial_taxa(), ids=[t.slug for t in beneficial_taxa()])
def test_a_beneficial_carries_its_german_name_and_a_sourced_english_one_or_a_listed_gap(taxon: Any) -> None:
    names = Beneficial(
        slug=taxon.slug,
        common_name=taxon.common_name_de,
        common_names_i18n=taxon.names_i18n(),
        scientific_name=taxon.scientific_name,
    ).common_names_i18n

    assert names["de"] == [taxon.common_name_de]
    if taxon.slug in BENEFICIALS_WITHOUT_A_SOURCED_ENGLISH_NAME:
        assert "en" not in names, f"{taxon.slug} has an English name now: drop it from the gap list"
    else:
        assert names.get("en"), f"{taxon.slug} has no English name and is not in the gap list"


def test_every_english_beneficial_name_sits_under_its_source() -> None:
    lines = _TAXONOMY.read_text(encoding="utf-8").splitlines()
    english = [i for i, line in enumerate(lines) if line.strip().startswith("common_name_en=")]

    assert len(english) == len(beneficial_taxa()) - len(BENEFICIALS_WITHOUT_A_SOURCED_ENGLISH_NAME)
    assert [lines[i] for i in english if not _SOURCE_COMMENT.search(lines[i - 1])] == []
