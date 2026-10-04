"""Finding A — the IPM rows of the plant-info seed files are read under the files' own keys.

``seed_plant_info`` and ``seed_adventskalender`` read ``pests`` / ``diseases`` /
``treatments`` / ``pest_treatments`` / ``disease_treatments``; the files say
``new_pests`` / ``new_diseases`` / ``new_treatments`` / ``treatment_pest_edges`` /
``treatment_disease_edges``. Every read returned the empty default. The real-server
counterpart is ``tests/integration/test_seed_ipm_rows_reach.py``.

**The class** (:class:`TestEverySeedFileWithIpmRowsIsRead`): every file under
``seed_data/`` that carries one of :data:`~app.migrations.seed_ipm_rows.IPM_KEYS` is
handed to ``seed_ipm_rows`` by a loader (``source="<file>"``), or is in :data:`UNREAD`
with the reason. **Spellings this does not see:** ``pest_species_edges`` /
``disease_species_edges`` (carried by four files, read by no loader, not an IPM key
here); a key read through a variable or an f-string; a ``source=`` that is not a string
literal; and ``ipm.yaml``, whose own schema spells the keys ``pests`` / ``pest_treatments``.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from app.domain.models.ipm import Disease, Pest, Treatment
from app.migrations import seed_ipm_rows as module
from app.migrations.seed_ipm_rows import (
    IPM_KEYS,
    build_diseases,
    build_pests,
    build_target_edges,
    build_treatments,
    seed_ipm_rows,
)
from app.migrations.yaml_loader import load_yaml

_MIGRATIONS = Path(module.__file__).parent
_SEED_DATA = _MIGRATIONS / "seed_data"

#: Seed files carrying IPM keys that no loader reads, with the reason. May only shrink.
UNREAD: dict[str, str] = {
    "plant_info_indoor_4.yaml": (
        "seed_plant_info_extended seeds no IPM rows; its 3 new_diseases carry no scientific_name "
        "(the Disease model requires one) — a data decision, finding A report"
    ),
    "plant_info_outdoor_1.yaml": (
        "seed_plant_info_extended seeds no IPM rows; its 5 new_pests carry no common_name "
        "(the Pest model requires one) — a data decision, finding A report"
    ),
    "plant_info_outdoor_3.yaml": (
        "seed_plant_info_extended seeds no IPM rows; 2 of its new_diseases carry no scientific_name "
        "— a data decision, finding A report"
    ),
}


class TestTheRealFiles:
    """Built from the shipped YAML: the old key spelling yields zero of each."""

    def test_plant_info(self) -> None:
        data = load_yaml("plant_info.yaml")
        pests = build_pests(data, source="plant_info.yaml")
        diseases = build_diseases(data, source="plant_info.yaml")
        treatments = build_treatments(data, source="plant_info.yaml")
        pest_edges, disease_edges = build_target_edges(data, source="plant_info.yaml")

        assert len(pests) == 8 and "Bemisia tabaci" in {p.scientific_name for p in pests}
        assert len(diseases) == 6 and "Septoria apiicola" in {d.scientific_name for d in diseases}
        # 6 rows; "Alcohol Spray" is chemical without a safety interval and refused by the model
        assert sorted(t.name for t in treatments) == sorted(
            [
                "Nematodes (Heterorhabditis)",
                "Amblyseius cucumeris",
                "Yellow Sticky Traps",
                "Straw Mulch",
                "Copper Spray",
            ]
        )
        assert (len(pest_edges), len(disease_edges)) == (12, 7)
        assert ("Ferramol", "Spanish Slug") in pest_edges

    def test_adventskalender(self) -> None:
        data = load_yaml("adventskalender.yaml")
        diseases = build_diseases(data, source="adventskalender.yaml")
        pest_edges, disease_edges = build_target_edges(data, source="adventskalender.yaml")

        assert len(build_pests(data, source="adventskalender.yaml")) == 6
        assert {d.common_name for d in diseases} == {
            "Leek Rust",
            "Alternaria Leaf Blight",
            "White Rot",
            "Cercospora Leaf Spot",
        }
        assert all(d.affected_plant_parts for d in diseases)
        assert "Ferramol" in {t.name for t in build_treatments(data, source="adventskalender.yaml")}
        # 7 entries; the stray "- Lamiaceae" of a half commented-out block is not a pair
        assert (len(pest_edges), len(disease_edges)) == (12, 6)


class TestRowShapes:
    def test_a_disease_named_by_name_and_affected_parts_is_read(self) -> None:
        data = {
            "new_diseases": [
                {"scientific_name": "X y", "name": "X Rot", "pathogen_type": "fungal", "affected_parts": ["leaf"]}
            ]
        }

        [disease] = build_diseases(data, source="t")

        assert disease.common_name == "X Rot"
        assert [part.value for part in disease.affected_plant_parts] == ["leaf"]

    def test_a_row_the_model_refuses_is_skipped_and_the_others_kept(self) -> None:
        data = {
            "new_treatments": [
                {"name": "Spray", "treatment_type": "chemical", "safety_interval_days": 0},
                {"name": "Net", "treatment_type": "mechanical"},
            ]
        }

        assert [t.name for t in build_treatments(data, source="t")] == ["Net"]

    def test_a_malformed_edge_is_skipped(self) -> None:
        pest_edges, disease_edges = build_target_edges(
            {"treatment_pest_edges": [["A", "B"]], "treatment_disease_edges": ["Lamiaceae", ["C", "D", "E"]]},
            source="t",
        )

        assert (pest_edges, disease_edges) == ([("A", "B")], [])


class _FakeIpmRepo:
    """Stores what it is given; ``get_all_*`` page like the real repository."""

    def __init__(self) -> None:
        self.pests: list[Pest] = []
        self.diseases: list[Disease] = []
        self.treatments: list[Treatment] = []
        self.pest_edges: set[tuple[str, str]] = set()
        self.disease_edges: set[tuple[str, str]] = set()

    @staticmethod
    def _page(rows: list[Any], offset: int, limit: int) -> tuple[list[Any], int]:
        return rows[offset : offset + limit], len(rows)

    def _stored(self, rows: list[Any], row: Any, prefix: str) -> Any:
        stored = row.model_copy(update={"key": f"{prefix}{len(rows)}"})
        rows.append(stored)
        return stored

    def get_all_pests(self, offset: int = 0, limit: int = 50) -> tuple[list[Pest], int]:
        return self._page(self.pests, offset, limit)

    def get_all_diseases(self, offset: int = 0, limit: int = 50) -> tuple[list[Disease], int]:
        return self._page(self.diseases, offset, limit)

    def get_all_treatments(self, offset: int = 0, limit: int = 50) -> tuple[list[Treatment], int]:
        return self._page(self.treatments, offset, limit)

    def create_pest(self, pest: Pest) -> Pest:
        return self._stored(self.pests, pest, "p")

    def create_disease(self, disease: Disease) -> Disease:
        return self._stored(self.diseases, disease, "d")

    def create_treatment(self, treatment: Treatment) -> Treatment:
        return self._stored(self.treatments, treatment, "t")

    def create_targets_pest_edge(self, treatment_key: str, pest_key: str) -> None:
        self.pest_edges.add((treatment_key, pest_key))

    def create_targets_disease_edge(self, treatment_key: str, disease_key: str) -> None:
        self.disease_edges.add((treatment_key, disease_key))


_FILE = {
    "new_pests": [{"scientific_name": "Pieris brassicae", "common_name": "Cabbage White Butterfly"}],
    "new_treatments": [{"name": "Net", "treatment_type": "mechanical"}],
    "treatment_pest_edges": [["Net", "Cabbage White Butterfly"], ["Net", "Unknown Bug"]],
}


class TestSeeding:
    def test_an_existing_pest_is_not_created_again_and_its_file_name_still_links(self) -> None:
        repo = _FakeIpmRepo()
        repo.create_pest(Pest(scientific_name="Pieris brassicae", common_name="Large Cabbage White"))

        counts = seed_ipm_rows(repo, _FILE, source="t")  # type: ignore[arg-type]

        assert (counts.pests_created, counts.treatments_created) == (0, 1)
        assert repo.pest_edges == {("t0", "p0")}
        assert (counts.edges_linked, counts.edges_unresolved) == (1, 1)

    def test_a_second_run_creates_nothing(self) -> None:
        repo = _FakeIpmRepo()
        seed_ipm_rows(repo, _FILE, source="t")  # type: ignore[arg-type]

        again = seed_ipm_rows(repo, _FILE, source="t")  # type: ignore[arg-type]

        assert (again.pests_created, again.diseases_created, again.treatments_created) == (0, 0, 0)
        assert (len(repo.pests), len(repo.treatments)) == (1, 1)


def _sources_handed_to_seed_ipm_rows() -> set[str]:
    """``source="<file>"`` of every ``seed_ipm_rows(...)`` call in ``app/migrations/*.py``."""
    found: set[str] = set()
    for path in sorted(_MIGRATIONS.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "seed_ipm_rows"):
                continue
            for kw in node.keywords:
                if kw.arg == "source" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    found.add(kw.value.value)
    return found


def _files_with_ipm_keys() -> set[str]:
    return {path.name for path in sorted(_SEED_DATA.glob("*.yaml")) if set(load_yaml(path.name) or {}) & set(IPM_KEYS)}


class TestEverySeedFileWithIpmRowsIsRead:
    def test_every_file_is_read_or_declared_unread(self) -> None:
        missing = sorted(_files_with_ipm_keys() - _sources_handed_to_seed_ipm_rows() - set(UNREAD))
        assert missing == [], f"seed files with IPM rows no loader reads: {missing}"

    def test_no_entry_outlives_its_file(self) -> None:
        stale = sorted(set(UNREAD) - (_files_with_ipm_keys() - _sources_handed_to_seed_ipm_rows()))
        assert stale == [], f"UNREAD entries that are read now, or carry no IPM key: {stale}"

    def test_the_measured_population(self) -> None:
        """Five files on 2026-10-04 — a scan that finds none is broken, not clean."""
        assert {"plant_info.yaml", "adventskalender.yaml"} <= _sources_handed_to_seed_ipm_rows()
        assert len(_files_with_ipm_keys()) >= 5

    @pytest.mark.parametrize("key", ["pests", "diseases", "treatments", "pest_treatments", "disease_treatments"])
    def test_the_old_spelling_is_not_an_ipm_key(self, key: str) -> None:
        assert key not in IPM_KEYS
