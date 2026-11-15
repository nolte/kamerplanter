"""#2955 — a pest-detection finding carries the taxon's names per language.

``PestFinding.common_name`` is the taxon's German name; before #2955 it was all a finding
said, so an English UI showed "Gemeine Spinnmilbe". Every adapter that maps a label onto
the taxonomy now also hands on ``PestTaxon.names_i18n()``; a label outside the taxonomy
carries no map and the client shows its ``common_name``.
"""

from __future__ import annotations

from app.common.enums import PestFindingMode
from app.data_access.external.demo_pest_adapter import DemoPestAdapter
from app.data_access.external.kindwise_pest_adapter import KindwisePestAdapter
from app.data_access.external.local_pest_adapters import _finding_from_raw
from app.domain.models.pest_taxonomy import get_taxon


def test_a_local_finding_of_a_known_taxon_carries_its_names() -> None:
    finding = _finding_from_raw({"label": "spider_mite", "confidence": 0.8}, default_mode=PestFindingMode.DIRECT)

    assert finding.common_name == "Gemeine Spinnmilbe"
    assert finding.common_names_i18n == {"de": ["Gemeine Spinnmilbe"], "en": ["Two-spotted spider mite"]}


def test_a_local_finding_outside_the_taxonomy_carries_no_map() -> None:
    finding = _finding_from_raw(
        {"label": "mystery_bug", "common_name": "Mystery", "confidence": 0.8}, default_mode=PestFindingMode.DIRECT
    )

    assert (finding.common_name, finding.common_names_i18n) == ("Mystery", {})


def test_a_cloud_finding_carries_the_taxon_names_or_none() -> None:
    payload = {
        "result": {
            "disease": {
                "suggestions": [{"name": "aphid", "probability": 0.7}, {"name": "leaf spot", "probability": 0.4}]
            }
        }
    }

    known, unknown = KindwisePestAdapter._parse(payload)

    assert known.common_names_i18n == get_taxon("aphid").names_i18n()  # type: ignore[union-attr]
    assert (unknown.common_name, unknown.common_names_i18n) == ("leaf spot", {})


def test_every_demo_finding_carries_its_names() -> None:
    result = DemoPestAdapter().detect([], language="en")

    assert [f.common_names_i18n.get("en") for f in result.findings] == [["Two-spotted spider mite"], ["Aphids"]]
