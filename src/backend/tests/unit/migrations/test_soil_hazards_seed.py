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

#: A scientific species name: genus plus epithet (infraspecific ranks may follow).
_SPECIES_NAME = re.compile(r"^[A-Z][a-z]+ [a-z][a-z-]+( .+)?$")


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _errors(document: Any) -> list[str]:
    validator = Draft202012Validator(_load(SCHEMA))
    return [error.message for error in validator.iter_errors(document)]


def _catalogue() -> tuple[set[str], set[str], set[str]]:
    """Families, genera and scientific names from the structured seed fields only.

    Comments and free text do not count: a name that appears only in a comment
    would never match a planted species.
    """
    families: set[str] = set()
    genera: set[str] = set()
    scientific: set[str] = set()
    for path in sorted(SEED_DIR.glob("*.yaml")):
        if path == SEED:
            continue
        document = _load(path)
        if not isinstance(document, dict):
            continue
        for family in document.get("families") or []:
            if isinstance(family, dict) and isinstance(family.get("name"), str):
                families.add(family["name"])
        for key in ("species", "new_species"):
            for entry in document.get(key) or []:
                if not isinstance(entry, dict):
                    continue
                for field, target in (("family", families), ("genus", genera), ("scientific_name", scientific)):
                    if isinstance(entry.get(field), str):
                        target.add(entry[field].strip())
        for name, family in (document.get("new_species_family_map") or {}).items():
            scientific.add(str(name).strip())
            families.add(str(family).strip())
    return families, genera, scientific


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

    def test_an_evidenced_duration_without_kind_is_refused(self) -> None:
        document = copy.deepcopy(_load(SEED))
        del document["hazards"][0]["soil_persistence_years"]["evidence"]["kind"]

        assert any("'kind' is a required property" in message for message in _errors(document))

    def test_an_evidenced_duration_without_years_is_refused(self) -> None:
        document = copy.deepcopy(_load(SEED))
        document["hazards"][0]["soil_persistence_years"]["years"] = None

        assert _errors(document) != []

    def test_a_not_found_duration_with_years_is_refused(self) -> None:
        document = copy.deepcopy(_load(SEED))
        juglone = next(row for row in document["hazards"] if row["hazard"] == "juglone")
        juglone["max_survival_years"]["years"] = 5

        assert _errors(document) != []

    def test_insufficient_with_three_sources_is_refused(self) -> None:
        document = copy.deepcopy(_load(SEED))
        white_rot = next(row for row in document["hazards"] if row["hazard"] == "white_rot")
        white_rot["soil_persistence_years"]["evidence"]["sources"] = 3

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
        families, genera, scientific = _catalogue()

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

    def test_a_species_entry_names_genus_and_epithet(self) -> None:
        """A bare genus entered at species level would match no planted species."""
        bare = sorted(
            entry["name"]
            for entry in _all_entries(_load(SEED))
            if entry["level"] == "species" and not _SPECIES_NAME.match(entry["name"])
        )

        assert bare == []

    def test_a_genus_entry_is_one_word(self) -> None:
        multi = sorted(
            entry["name"] for entry in _all_entries(_load(SEED)) if entry["level"] == "genus" and " " in entry["name"]
        )

        assert multi == []
