"""Tests for the seed harvest/month check (``scripts/check_seed_harvest_integrity.py``).

**What is under test.** The detection logic, driven against *constructed* seed
trees written into ``tmp_path`` — never against the real ``seed_data``. A test
asserting "the tree holds 42 ornamentals" would go red on the next legitimate
species and teach nobody anything; what is worth locking down is what the check
does with a given input.

Three things are pinned against reality instead:

* :class:`TestTheRealSeedTreeIsClean` runs the check over the real seed data
  exactly as the pre-commit hook does. It pins no number — it pins that both
  invariants hold, which is the whole claim the hook makes.
* :class:`TestTheDefaultMatchesTheModel` pins ``ALLOWS_HARVEST_DEFAULT`` against
  ``Species.allows_harvest``'s declared default. The script cannot import the
  model (it runs in an isolated pre-commit venv carrying only PyYAML), so the
  constant is duplicated; this is what stops the duplicate from drifting. If the
  model's default ever flips to ``False``, invariant A would silently stop
  finding the 43 records that carry no ``allows_harvest`` key — the exact shape
  #1002 reported — and only this test would notice.
* :class:`TestItCanFail` reconstructs both reported defects in miniature — the
  ornamental *Dracaena* shape of #1002 and the *Allium porrum* split-across-two-
  files shape of #1008 — and asserts the check goes red and names them. A gate
  nobody has watched fail is a gate nobody knows works.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package, so it is loaded **by path** — the same
mechanism ``test_boundary_validation_check.py`` and
``test_schema_example_ratchet.py`` use.

Traces to issues #1002 and #1008 (no TC-ID: a source-tree gate is not a
user-facing case).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

from app.domain.models.species import Species

# ── Loading the script under test by path ────────────────────────────────────


def _find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* to the checkout root, identified by its markers.

    A marker walk rather than ``parents[N]``: a hard-coded index silently breaks
    the moment the test file moves, which has bitten this repository before.

    Args:
        start: Any path inside the checkout.

    Returns:
        The directory holding both ``Taskfile.yaml`` and ``scripts/``, or None.
    """
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "scripts").is_dir():
            return candidate
    return None


def _load_module_by_path(module_name: str, path: Path) -> ModuleType:
    """Execute the module at *path* under *module_name* and return it.

    Registration in ``sys.modules`` happens **before** ``exec_module`` because the
    script defines ``@dataclass`` types, and ``dataclass`` resolves its own module
    through ``sys.modules`` while the module body is still running.

    Args:
        module_name: Private name to register under.
        path: The ``.py`` file to execute.

    Returns:
        The executed module.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        pytest.skip(f"{path} cannot be loaded as a Python module", allow_module_level=True)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip(
        "checkout root not found (no ancestor holds both Taskfile.yaml and scripts/); "
        "scripts/check_seed_harvest_integrity.py is unreachable from here",
        allow_module_level=True,
    )

_SCRIPT = _REPO_ROOT / "scripts" / "check_seed_harvest_integrity.py"
if not _SCRIPT.is_file():  # pragma: no cover — only on a partial checkout
    pytest.skip(f"{_SCRIPT} does not exist", allow_module_level=True)

checker = _load_module_by_path("_seed_harvest_integrity_check_under_test", _SCRIPT)

_REAL_SEED_DIR = _REPO_ROOT / "src/backend/app/migrations/seed_data"


# ── Building miniature seed trees ────────────────────────────────────────────


def _write_seed(seed_dir: Path, name: str, document: dict[str, Any]) -> Path:
    """Write *document* as ``<seed_dir>/<name>`` and return the path."""
    seed_dir.mkdir(parents=True, exist_ok=True)
    path = seed_dir / name
    path.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _findings(seed_dir: Path) -> list[Any]:
    """Run both invariants over the seed tree at *seed_dir*."""
    entries = checker.load_seed_species(seed_dir)
    return checker.collect_findings(entries.values())


def _invariants(findings: list[Any]) -> set[str]:
    """Return the set of invariant names present in *findings*."""
    return {finding.invariant for finding in findings}


# ── The duplicated default ───────────────────────────────────────────────────


class TestTheDefaultMatchesTheModel:
    """``ALLOWS_HARVEST_DEFAULT`` must track ``Species.allows_harvest``."""

    def test_the_constant_equals_the_models_declared_default(self) -> None:
        """The script's copy of the default is still the model's default.

        The script runs in a pre-commit venv holding only PyYAML and cannot
        import the model, so the value is duplicated. Were the model to flip to
        ``False``, invariant A would stop firing on every record that omits the
        key — 43 of the 44 the sweep found — and the check would report a clean
        tree it had not actually checked.
        """
        assert Species.model_fields["allows_harvest"].default == checker.ALLOWS_HARVEST_DEFAULT

    def test_the_default_is_true_which_is_why_the_check_reads_it(self) -> None:
        """Pin the direction of the default, not merely that the two agree.

        Both sides being ``False`` would satisfy the test above while making
        invariant A near-inert. This states the premise the check is built on.
        """
        assert checker.ALLOWS_HARVEST_DEFAULT is True


# ── Invariant A — allows_harvest without harvest months (#1002) ──────────────


class TestHarvestDataPresence:
    """A record claiming a harvest must supply a month to check a Karenz against."""

    def test_an_omitted_flag_with_no_months_is_a_finding(self, tmp_path: Path) -> None:
        """The #1002 shape: an ornamental that never mentions ``allows_harvest``.

        This is the case a literal reading of the YAML misses entirely, and it is
        the one that accounts for nearly every real occurrence.
        """
        _write_seed(
            tmp_path,
            "plants.yaml",
            {"new_species": [{"scientific_name": "Dracaena reflexa", "plant_category": "tropical_foliage"}]},
        )

        findings = _findings(tmp_path)

        assert _invariants(findings) == {"allows-harvest-without-harvest-months"}
        assert findings[0].scientific_name == "Dracaena reflexa"
        assert "defaulted to true" in findings[0].detail

    def test_an_explicit_true_with_no_months_is_a_finding(self, tmp_path: Path) -> None:
        """A stated ``allows_harvest: true`` is held to the same standard."""
        _write_seed(
            tmp_path,
            "plants.yaml",
            {"new_species": [{"scientific_name": "Aloe vera", "allows_harvest": True}]},
        )

        findings = _findings(tmp_path)

        assert _invariants(findings) == {"allows-harvest-without-harvest-months"}
        assert "allows_harvest: true but no harvest_months" in findings[0].detail

    def test_an_explicit_false_is_clean(self, tmp_path: Path) -> None:
        """``allows_harvest: false`` needs no months — the Karenz is genuinely N/A."""
        _write_seed(
            tmp_path,
            "plants.yaml",
            {"new_species": [{"scientific_name": "Monstera adansonii", "allows_harvest": False}]},
        )

        assert _findings(tmp_path) == []

    def test_top_level_harvest_months_satisfy_the_invariant(self, tmp_path: Path) -> None:
        """A harvested species with a flat window is clean."""
        _write_seed(
            tmp_path,
            "plants.yaml",
            {"new_species": [{"scientific_name": "Daucus carota", "harvest_months": [7, 8, 9]}]},
        )

        assert _findings(tmp_path) == []

    def test_months_carried_only_by_a_growing_period_satisfy_the_invariant(self, tmp_path: Path) -> None:
        """Harvest data in the periods counts as harvest data.

        Without this, every multi-period crop would be reported for invariant A
        as well as B, and the two findings would compete for the same fix.
        """
        _write_seed(
            tmp_path,
            "plants.yaml",
            {
                "new_species": [
                    {
                        "scientific_name": "Triticum aestivum",
                        "direct_sow_months": [3, 4],
                        "harvest_months": [7, 8],
                        "growing_periods": [
                            {"label": "Sommerweizen", "direct_sow_months": [3, 4], "harvest_months": [7, 8]},
                        ],
                    }
                ]
            },
        )

        assert _findings(tmp_path) == []

    def test_an_empty_harvest_months_list_does_not_count_as_data(self, tmp_path: Path) -> None:
        """``harvest_months: []`` is the absence of a window, not a window.

        Several seed records spell the empty case out explicitly; treating the
        key's mere presence as satisfaction would let the whole class back in.
        """
        _write_seed(
            tmp_path,
            "plants.yaml",
            {"new_species": [{"scientific_name": "Ficus elastica", "harvest_months": []}]},
        )

        assert _invariants(_findings(tmp_path)) == {"allows-harvest-without-harvest-months"}


# ── Invariant B — top level equals the union of the periods (#1008) ──────────


class TestTopLevelIsThePeriodUnion:
    """Flat month fields must say what the growing periods say."""

    def test_the_reported_allium_porrum_shape_is_a_finding(self, tmp_path: Path) -> None:
        """#1008 verbatim: flat fields that are neither the union nor a subset.

        Reproduced across two files, as the real defect was: the periods came
        from ``adventskalender.yaml`` and the flat months from an enrichment in
        ``plant_info_outdoor_1.yaml``. Neither file is wrong when read alone,
        which is why the check merges before it judges.
        """
        _write_seed(
            tmp_path,
            "a_periods.yaml",
            {
                "new_species": [
                    {
                        "scientific_name": "Allium porrum",
                        "allows_harvest": True,
                        "growing_periods": [
                            {"label": "Sommerporree", "direct_sow_months": [2, 3], "harvest_months": [8, 9, 10, 11]},
                            {"label": "Winterporree", "direct_sow_months": [5, 6], "harvest_months": [12, 1, 2, 3]},
                        ],
                    }
                ]
            },
        )
        _write_seed(
            tmp_path,
            "b_enrichment.yaml",
            {
                "species_enrichment": {
                    "Allium porrum": {
                        "direct_sow_months": [3, 4],
                        "harvest_months": [9, 10, 11, 12, 1, 2],
                    }
                }
            },
        )

        findings = _findings(tmp_path)

        assert _invariants(findings) == {"top-level-months-not-period-union"}
        assert {f.detail.split()[0] for f in findings} == {"direct_sow_months", "harvest_months"}
        sowing = next(f for f in findings if f.detail.startswith("direct_sow_months"))
        # The winter crop's whole sowing window is missing, and month 4 is sourced
        # by no period at all — both halves of the reported defect.
        assert "missing from the top level: [2, 5, 6]" in sowing.detail
        assert "present only at the top level: [4]" in sowing.detail

    def test_absent_flat_fields_are_a_finding_when_the_periods_carry_months(self, tmp_path: Path) -> None:
        """The Triticum shape: the periods answer, ``get_species_info`` does not.

        An empty top level is not "no claim" — it is the claim that there is no
        sowing or harvest window, next to two periods that describe one.
        """
        _write_seed(
            tmp_path,
            "plants.yaml",
            {
                "new_species": [
                    {
                        "scientific_name": "Triticum aestivum",
                        "growing_periods": [
                            {"label": "Sommerweizen", "direct_sow_months": [3, 4], "harvest_months": [7, 8]},
                            {"label": "Winterweizen", "direct_sow_months": [9, 10], "harvest_months": [7]},
                        ],
                    }
                ]
            },
        )

        findings = _findings(tmp_path)

        assert _invariants(findings) == {"top-level-months-not-period-union"}
        assert len(findings) == 2

    def test_the_exact_union_is_clean_regardless_of_order(self, tmp_path: Path) -> None:
        """Comparison is by set: a season written 8…3 across the year is fine.

        Several records spell a winter harvest as ``[12, 1, 2]`` rather than
        sorted, and rewriting them to satisfy a list comparison would destroy
        the readable season order for nothing.
        """
        _write_seed(
            tmp_path,
            "plants.yaml",
            {
                "new_species": [
                    {
                        "scientific_name": "Allium porrum",
                        "direct_sow_months": [3, 4, 5],
                        "harvest_months": [8, 9, 10, 11, 12, 1, 2, 3],
                        "growing_periods": [
                            {"label": "Sommerporree", "direct_sow_months": [3, 4], "harvest_months": [8, 9, 10, 11]},
                            {"label": "Winterporree", "direct_sow_months": [5], "harvest_months": [12, 1, 2, 3]},
                        ],
                    }
                ]
            },
        )

        assert _findings(tmp_path) == []

    def test_a_field_no_period_carries_is_not_compared(self, tmp_path: Path) -> None:
        """``bloom_months`` at the top level with none in the periods stays quiet.

        No seed record splits bloom per period, so demanding union equality
        there would only force the value to be duplicated into every period to
        say nothing new — and a check with false positives gets suppressed.
        """
        _write_seed(
            tmp_path,
            "plants.yaml",
            {
                "new_species": [
                    {
                        "scientific_name": "Allium porrum",
                        "direct_sow_months": [3],
                        "harvest_months": [8],
                        "bloom_months": [6, 7],
                        "growing_periods": [
                            {"label": "Sommerporree", "direct_sow_months": [3], "harvest_months": [8]},
                        ],
                    }
                ]
            },
        )

        assert _findings(tmp_path) == []

    def test_a_species_without_periods_is_not_compared(self, tmp_path: Path) -> None:
        """A single-window species has nothing to disagree with."""
        _write_seed(
            tmp_path,
            "plants.yaml",
            {
                "new_species": [
                    {
                        "scientific_name": "Daucus carota",
                        "direct_sow_months": [3, 4, 5],
                        "harvest_months": [7, 8, 9],
                    }
                ]
            },
        )

        assert _findings(tmp_path) == []


# ── The merge the seeders produce ────────────────────────────────────────────


class TestTheMergedView:
    """A consumer sees the merge, not one YAML record — so the check does too."""

    def test_enrichment_fills_an_empty_field(self, tmp_path: Path) -> None:
        """Enrichment supplying the months clears invariant A.

        Mirrors the seeders, which set an enrichment field only where the stored
        value is ``None`` / ``""`` / ``[]``.
        """
        _write_seed(
            tmp_path,
            "a_base.yaml",
            {"new_species": [{"scientific_name": "Allium schoenoprasum", "harvest_months": []}]},
        )
        _write_seed(
            tmp_path,
            "b_enrichment.yaml",
            {"species_enrichment": {"Allium schoenoprasum": {"harvest_months": [4, 5, 6]}}},
        )

        assert _findings(tmp_path) == []

    def test_enrichment_never_overwrites_a_populated_field(self, tmp_path: Path) -> None:
        """A populated base value survives enrichment, as in the seeders."""
        _write_seed(
            tmp_path,
            "a_base.yaml",
            {"new_species": [{"scientific_name": "Allium schoenoprasum", "harvest_months": [4, 5]}]},
        )
        _write_seed(
            tmp_path,
            "b_enrichment.yaml",
            {"species_enrichment": {"Allium schoenoprasum": {"harvest_months": [9, 10]}}},
        )

        entries = checker.load_seed_species(tmp_path)

        assert entries["Allium schoenoprasum"].fields["harvest_months"] == [4, 5]

    def test_an_enrichment_without_a_base_record_seeds_nothing_and_is_ignored(self, tmp_path: Path) -> None:
        """An orphan enrichment block is not a species and not this check's business.

        The seeders log ``enrichment_species_not_found`` and move on; inventing a
        record here would report a defect on data that never reaches a consumer.
        """
        _write_seed(
            tmp_path,
            "orphan.yaml",
            {"species_enrichment": {"Nonexistent species": {"allows_harvest": True}}},
        )

        assert checker.load_seed_species(tmp_path) == {}
        assert _findings(tmp_path) == []

    def test_every_contributing_file_is_named_in_the_finding(self, tmp_path: Path) -> None:
        """The report points at the files, because the fix may be in either."""
        _write_seed(
            tmp_path,
            "a_base.yaml",
            {"new_species": [{"scientific_name": "Ficus elastica", "genus": "Ficus"}]},
        )
        _write_seed(
            tmp_path,
            "b_enrichment.yaml",
            {"species_enrichment": {"Ficus elastica": {"frost_sensitivity": "sensitive"}}},
        )

        findings = _findings(tmp_path)

        assert set(findings[0].sources) == {"a_base.yaml", "b_enrichment.yaml"}

    def test_non_mapping_documents_are_skipped(self, tmp_path: Path) -> None:
        """A YAML file that is a list, or empty, must not crash the loader."""
        (tmp_path / "list.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")
        (tmp_path / "empty.yaml").write_text("", encoding="utf-8")
        _write_seed(
            tmp_path,
            "plants.yaml",
            {"new_species": [{"scientific_name": "Daucus carota", "harvest_months": [7]}]},
        )

        assert list(checker.load_seed_species(tmp_path)) == ["Daucus carota"]

    def test_a_missing_seed_directory_raises_rather_than_reporting_clean(self, tmp_path: Path) -> None:
        """A wrong path must not read as "no findings" — that is a false green."""
        with pytest.raises(FileNotFoundError):
            checker.load_seed_species(tmp_path / "nope")


# ── The gate, watched failing and watched passing ────────────────────────────


class TestItCanFail:
    """The exit code moves with the data, on the real entry point."""

    def test_main_exits_non_zero_and_names_the_record(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """A defective tree fails the gate and says which record and why."""
        _write_seed(
            tmp_path,
            "plants.yaml",
            {"new_species": [{"scientific_name": "Dracaena reflexa"}]},
        )

        exit_code = checker.main(["--seed-dir", str(tmp_path)])

        assert exit_code == 1
        out = capsys.readouterr().out
        assert "FAIL: 1 finding(s)" in out
        assert "Dracaena reflexa" in out
        assert "never invent harvest months" in out

    def test_main_exits_zero_on_a_clean_tree(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """The same entry point passes once the data is right."""
        _write_seed(
            tmp_path,
            "plants.yaml",
            {"new_species": [{"scientific_name": "Dracaena reflexa", "allows_harvest": False}]},
        )

        exit_code = checker.main(["--seed-dir", str(tmp_path)])

        assert exit_code == 0
        assert "OK: 1 seed species records" in capsys.readouterr().out

    def test_json_output_carries_the_findings(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """``--json`` stays machine-readable and still exits non-zero."""
        import json

        _write_seed(
            tmp_path,
            "plants.yaml",
            {"new_species": [{"scientific_name": "Dracaena reflexa"}]},
        )

        exit_code = checker.main(["--seed-dir", str(tmp_path), "--json"])

        assert exit_code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["species_checked"] == 1
        assert payload["findings"][0]["invariant"] == "allows-harvest-without-harvest-months"


class TestTheRealSeedTreeIsClean:
    """The claim the pre-commit hook makes, asserted against the real seed data."""

    @pytest.mark.skipif(not _REAL_SEED_DIR.is_dir(), reason="seed_data not present")
    def test_both_invariants_hold_over_the_shipped_seed_data(self) -> None:
        """No seed species asserts a harvest or sowing fact nobody can act on.

        Deliberately pins no count: the number of species is free to grow, the
        invariant is not.
        """
        findings = _findings(_REAL_SEED_DIR)

        assert findings == [], "\n".join(finding.render() for finding in findings)

    @pytest.mark.skipif(not _REAL_SEED_DIR.is_dir(), reason="seed_data not present")
    def test_the_two_reported_species_are_fixed_at_the_source(self) -> None:
        """#1002 and #1008's own records, checked by name rather than in bulk.

        The bulk assertion above would also pass if these two records vanished
        from the seed; this one pins that they are present *and* consumable.
        """
        entries = checker.load_seed_species(_REAL_SEED_DIR)

        leek = entries["Allium porrum"]
        periods = leek.fields["growing_periods"]
        assert set(leek.fields["direct_sow_months"]) == {3, 4, 5}
        assert set(leek.fields["harvest_months"]) == {8, 9, 10, 11, 12, 1, 2, 3}
        assert set(leek.fields["direct_sow_months"]) == {
            month for period in periods for month in period["direct_sow_months"]
        }

        aloe = entries["Aloe vera"]
        assert aloe.fields["allows_harvest"] is True
        assert set(aloe.fields["harvest_months"]) == set(range(1, 13))
