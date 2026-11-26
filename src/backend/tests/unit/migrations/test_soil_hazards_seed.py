"""``soil_hazards.yaml`` against its schema and the seed catalogue (REQ-054 §5.2a, #2888 F-18).

F-18 acceptance-2: the table holds per hazard the cultivation pause, the maximum
survival and the hosts at family, genus or species level, each value with an
evidence status. The directory-wide ``seed-schema-conformance`` hook validates the
file because its header declares the schema; this module pins that the schema
actually refuses the shapes acceptance-2 rules out (a value without status, a 3/3
claim with two sources, a host without level), so a green hook means something.

It also checks that every host taxon names something the seed catalogue knows: a
misspelt family or genus would never match a planted species and the hazard would
be inert without any error.
"""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

SEED_DIR = Path(__file__).resolve().parents[3] / "app" / "migrations" / "seed_data"
SEED = SEED_DIR / "soil_hazards.yaml"
SCHEMA = SEED_DIR / "schemas" / "soil_hazards.schema.yaml"

_FAMILY = re.compile(r"\b[A-Z][a-z]+aceae\b")


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _errors(document: Any) -> list[str]:
    validator = Draft202012Validator(_load(SCHEMA))
    return [error.message for error in validator.iter_errors(document)]


def _catalogue_texts() -> list[str]:
    return [path.read_text(encoding="utf-8") for path in sorted(SEED_DIR.glob("*.yaml")) if path != SEED]


def _all_entries(document: dict[str, Any]) -> list[dict[str, Any]]:
    return [entry for row in document["hazards"] for entry in (row["hosts"] + row.get("non_hosts", []))]


class TestSchema:
    def test_header_declares_the_schema(self) -> None:
        first_line = SEED.read_text(encoding="utf-8").splitlines()[0]

        assert first_line == "# yaml-language-server: $schema=./schemas/soil_hazards.schema.yaml"

    def test_shipped_table_validates(self) -> None:
        assert _errors(_load(SEED)) == []

    def test_every_value_carries_an_evidence_status(self) -> None:
        document = _load(SEED)
        for row in document["hazards"]:
            for field in ("soil_persistence_years", "max_survival_years"):
                assert row[field]["evidence"]["status"], (row["hazard"], field)
        assert all(entry["evidence"]["status"] for entry in _all_entries(document))

    def test_a_value_without_evidence_is_refused(self) -> None:
        document = copy.deepcopy(_load(SEED))
        del document["hazards"][0]["soil_persistence_years"]["evidence"]

        assert any("'evidence' is a required property" in message for message in _errors(document))

    def test_an_evidenced_claim_with_two_sources_is_refused(self) -> None:
        document = copy.deepcopy(_load(SEED))
        document["hazards"][0]["soil_persistence_years"]["evidence"]["sources"] = 2

        assert _errors(document) != []

    def test_a_host_without_level_is_refused(self) -> None:
        document = copy.deepcopy(_load(SEED))
        del document["hazards"][0]["hosts"][0]["level"]

        assert any("'level' is a required property" in message for message in _errors(document))

    def test_an_unknown_hazard_key_is_refused(self) -> None:
        document = copy.deepcopy(_load(SEED))
        document["hazards"][0]["hazard"] = "fusarium_wilt"

        assert _errors(document) != []

    def test_the_old_single_family_field_is_refused(self) -> None:
        """REQ-054 v1.4 dropped ``affected_families[]``; hosts carry their level."""
        document = copy.deepcopy(_load(SEED))
        document["hazards"][0]["affected_families"] = ["Brassicaceae"]

        assert _errors(document) != []


class TestHostsMatchTheCatalogue:
    def test_all_three_host_levels_are_used(self) -> None:
        levels = {entry["level"] for entry in _all_entries(_load(SEED))}

        assert levels == {"family", "genus", "species"}

    @pytest.mark.parametrize("level", ["family", "genus", "species"])
    def test_every_host_taxon_is_known_to_the_seed_catalogue(self, level: str) -> None:
        texts = _catalogue_texts()
        families = {name for text in texts for name in _FAMILY.findall(text)}
        genera = {value for text in texts for value in re.findall(r"^\s*genus:\s*\"?([A-Z][a-z]+)\"?\s*$", text, re.M)}
        scientific = {
            value.strip()
            for text in texts
            for value in re.findall(r"scientific_name:\s*\"?([A-Z][a-z]+ [a-z][^\"\n#]*)\"?", text)
        }

        def known(name: str) -> bool:
            if level == "family":
                return name in families
            if level == "genus":
                return name in genera
            # A species name also matches its infraspecific taxa (REQ-054 §5.2a).
            return any(sn == name or sn.startswith(f"{name} ") for sn in scientific)

        unknown = sorted(
            {
                entry["name"]
                for entry in _all_entries(_load(SEED))
                if entry["level"] == level and not known(entry["name"])
            }
        )

        assert unknown == [], f"{level} names the seed catalogue does not know: {unknown}"
