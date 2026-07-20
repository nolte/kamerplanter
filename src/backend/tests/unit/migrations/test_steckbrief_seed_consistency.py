"""Tests for the Steckbrief<->seed consistency validator (Issue #680).

Three guarantees, per the issue:
  (a) the validator is GREEN on the real, committed data set;
  (b) an artificially injected drift is detected (would break the build);
  (c) an allowlisted discrepancy does NOT break the build.

Plus focused tests for the Markdown/CSV parsing edge cases the corpus relies on.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from app.migrations.seed_steckbrief_consistency import (
    ALLOWED_DISCREPANCIES,
    _clean_value,
    check,
    find_drifts,
    load_seed_attributes,
    main,
    parse_steckbrief,
)

# --------------------------------------------------------------------------- #
# (a) real data is green
# --------------------------------------------------------------------------- #


def test_real_data_has_no_unallowlisted_drift() -> None:
    result = check()
    assert result.ok, "unexpected Steckbrief<->seed drift:\n" + "\n".join(
        f"  [{d.attribute}] {d.scientific_name}: steckbrief={d.steckbrief_value!r} seed={d.seed_value!r}"
        for d in result.violations
    )
    assert not result.violations


def test_allowlist_has_no_obsolete_entries() -> None:
    # Every ALLOWED_DISCREPANCIES entry must still correspond to a live drift,
    # otherwise it is dead weight hiding nothing (or masking a changed value).
    result = check()
    assert not result.obsolete_allowlist, "obsolete allowlist entries: " + ", ".join(
        f"{a.scientific_name}/{a.attribute}" for a in result.obsolete_allowlist
    )


def test_stephanotis_is_allowlisted_not_a_violation() -> None:
    result = check()
    allowlisted = {(d.scientific_name, d.attribute) for d in result.allowlisted}
    violations = {(d.scientific_name, d.attribute) for d in result.violations}
    assert ("Stephanotis floribunda", "photoperiod_type") in allowlisted
    assert ("Stephanotis floribunda", "photoperiod_type") not in violations


def test_cli_main_is_green_on_real_data() -> None:
    assert main([]) == 0


def test_first_allowlist_entry_is_stephanotis() -> None:
    # The issue mandates Stephanotis/photoperiod_type as the first documented entry.
    first = ALLOWED_DISCREPANCIES[0]
    assert first.scientific_name == "Stephanotis floribunda"
    assert first.attribute == "photoperiod_type"
    assert first.steckbrief_value == "day_neutral"
    assert first.seed_value == "short_day"
    assert first.reason and first.source


# --------------------------------------------------------------------------- #
# Fixtures for synthetic corpora
# --------------------------------------------------------------------------- #


def _write_steckbrief(plants_dir: Path, name: str, scientific_name: str, growth_habit: str) -> None:
    plants_dir.mkdir(parents=True, exist_ok=True)
    (plants_dir / f"{name}.md").write_text(
        textwrap.dedent(
            f"""\
            # Test — {scientific_name}

            ## 1. Taxonomie

            | Feld | Wert | KA-Feld |
            |------|------|---------|
            | Wissenschaftlicher Name | {scientific_name} | `species.scientific_name` |
            | Wuchsform | {growth_habit} | `species.growth_habit` |
            """
        ),
        encoding="utf-8",
    )


def _write_species_seed(seed_dir: Path, scientific_name: str, growth_habit: str) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    (seed_dir / "species.yaml").write_text(
        textwrap.dedent(
            f"""\
            species:
              - scientific_name: {scientific_name}
                growth_habit: {growth_habit}
            """
        ),
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- #
# (b) injected drift is detected
# --------------------------------------------------------------------------- #


def test_injected_drift_is_detected(tmp_path: Path) -> None:
    plants = tmp_path / "plants"
    seed = tmp_path / "seed_data"
    _write_steckbrief(plants, "foo", "Foo bar", growth_habit="herb")
    _write_species_seed(seed, "Foo bar", growth_habit="succulent")

    drifts, unmatched = find_drifts(plants, load_seed_attributes(seed))

    assert not unmatched
    assert len(drifts) == 1
    drift = drifts[0]
    assert drift.scientific_name == "Foo bar"
    assert drift.attribute == "growth_habit"
    assert drift.steckbrief_value == "herb"
    assert drift.seed_value == "succulent"


def test_matching_values_produce_no_drift(tmp_path: Path) -> None:
    plants = tmp_path / "plants"
    seed = tmp_path / "seed_data"
    _write_steckbrief(plants, "foo", "Foo bar", growth_habit="succulent")
    _write_species_seed(seed, "Foo bar", growth_habit="succulent")

    drifts, unmatched = find_drifts(plants, load_seed_attributes(seed))

    assert not drifts
    assert not unmatched


def test_steckbrief_without_seed_counterpart_is_not_a_drift(tmp_path: Path) -> None:
    plants = tmp_path / "plants"
    seed = tmp_path / "seed_data"
    _write_steckbrief(plants, "foo", "Foo aggregate spp.", growth_habit="herb")
    _write_species_seed(seed, "Foo bar", growth_habit="succulent")

    drifts, unmatched = find_drifts(plants, load_seed_attributes(seed))

    assert not drifts
    assert len(unmatched) == 1


# --------------------------------------------------------------------------- #
# (c) allowlisted discrepancy does not break the build
# --------------------------------------------------------------------------- #


def test_allowlisted_drift_does_not_break(tmp_path: Path, monkeypatch) -> None:
    import app.migrations.seed_steckbrief_consistency as mod

    plants = tmp_path / "spec" / "knowledge" / "plants"
    seed = tmp_path / "src" / "backend" / "app" / "migrations" / "seed_data"
    _write_steckbrief(plants, "foo", "Foo bar", growth_habit="herb")
    _write_species_seed(seed, "Foo bar", growth_habit="succulent")

    entry = mod.AllowedDiscrepancy(
        scientific_name="Foo bar",
        attribute="growth_habit",
        steckbrief_value="herb",
        seed_value="succulent",
        reason="test",
        source="test",
    )
    monkeypatch.setattr(mod, "ALLOWED_DISCREPANCIES", (entry,))

    result = check(root=tmp_path)

    assert result.ok
    assert not result.violations
    assert len(result.allowlisted) == 1
    assert result.allowlisted[0].scientific_name == "Foo bar"


def test_allowlist_only_matches_exact_value_pair(tmp_path: Path, monkeypatch) -> None:
    # An allowlist entry pinned to a different seed value must NOT absorb a drift
    # whose seed value has since changed -- it stays a violation.
    import app.migrations.seed_steckbrief_consistency as mod

    plants = tmp_path / "spec" / "knowledge" / "plants"
    seed = tmp_path / "src" / "backend" / "app" / "migrations" / "seed_data"
    _write_steckbrief(plants, "foo", "Foo bar", growth_habit="herb")
    _write_species_seed(seed, "Foo bar", growth_habit="succulent")

    stale = mod.AllowedDiscrepancy(
        scientific_name="Foo bar",
        attribute="growth_habit",
        steckbrief_value="herb",
        seed_value="grass",  # seed actually says succulent now
        reason="test",
        source="test",
    )
    monkeypatch.setattr(mod, "ALLOWED_DISCREPANCIES", (stale,))

    result = check(root=tmp_path)

    assert not result.ok
    assert len(result.violations) == 1
    assert result.obsolete_allowlist == [stale]


# --------------------------------------------------------------------------- #
# Parsing edge cases
# --------------------------------------------------------------------------- #


def test_parse_ignores_csv_block_and_reads_table_anchor(tmp_path: Path) -> None:
    path = tmp_path / "s.md"
    path.write_text(
        textwrap.dedent(
            """\
            | Wissenschaftlicher Name | Foo bar | `species.scientific_name` |
            | Wuchsform | succulent | `species.growth_habit` |
            | Photoperiode | day_neutral <!-- Q: x --> (korr.) | `lifecycle_configs.photoperiod_type` |

            ```csv
            scientific_name,photoperiod_type,growth_habit
            Foo bar,long_day,herb
            ```
            """
        ),
        encoding="utf-8",
    )
    parsed = parse_steckbrief(path)
    assert parsed["scientific_name"] == "Foo bar"
    assert parsed["growth_habit"] == "succulent"
    # Value read from the table anchor, not the stale CSV; comment/parenthesis stripped.
    assert parsed["photoperiod_type"] == "day_neutral"


def test_clean_value_handles_missing_markers() -> None:
    assert _clean_value("—") is None
    assert _clean_value("<!-- DATEN FEHLEN -->") is None
    assert _clean_value("<!-- DATEN FEHLEN: kein Wert --> (tagneutral)") is None
    assert _clean_value("") is None
    assert _clean_value("polycarpic (mehrjährig wiederholt blühend)") == "polycarpic"
    assert _clean_value("`bulb_geophyte` (krautartig)") == "bulb_geophyte"
    assert _clean_value("short_day") == "short_day"


# --------------------------------------------------------------------------- #
# Fix 1: synonym / parenthetical name suffix is stripped before matching
# --------------------------------------------------------------------------- #


def test_parse_strips_synonym_parenthesis_from_name(tmp_path: Path) -> None:
    # "Salvia rosmarinus (Syn. Rosmarinus officinalis)" must normalize to the
    # bare seed key "Salvia rosmarinus" -- otherwise a real drift is silently
    # swallowed as "unmatched". Regression guard for Issue #680 pre-merge review.
    path = tmp_path / "rosmarinus.md"
    path.write_text(
        textwrap.dedent(
            """\
            | Wissenschaftlicher Name | Salvia rosmarinus (Syn. Rosmarinus officinalis) | `species.scientific_name` |
            | Wuchsform | shrub | `species.growth_habit` |
            """
        ),
        encoding="utf-8",
    )
    parsed = parse_steckbrief(path)
    assert parsed["scientific_name"] == "Salvia rosmarinus"


def test_synonym_parenthesis_name_matches_seed_and_surfaces_drift(tmp_path: Path) -> None:
    # End-to-end proof: a Steckbrief whose name carries a "(Syn. ...)" suffix
    # now matches the plain seed key and its drift is caught (not dropped as
    # unmatched).
    plants = tmp_path / "plants"
    seed = tmp_path / "seed_data"
    plants.mkdir(parents=True, exist_ok=True)
    (plants / "rosmarinus.md").write_text(
        textwrap.dedent(
            """\
            | Wissenschaftlicher Name | Salvia rosmarinus (Syn. Rosmarinus officinalis) | `species.scientific_name` |
            | Wuchsform | shrub | `species.growth_habit` |
            """
        ),
        encoding="utf-8",
    )
    _write_species_seed(seed, "Salvia rosmarinus", growth_habit="subshrub")

    drifts, unmatched = find_drifts(plants, load_seed_attributes(seed))

    assert not unmatched
    assert len(drifts) == 1
    assert drifts[0].scientific_name == "Salvia rosmarinus"
    assert drifts[0].attribute == "growth_habit"
    assert drifts[0].steckbrief_value == "shrub"
    assert drifts[0].seed_value == "subshrub"


# --------------------------------------------------------------------------- #
# Fix 2: growth_determinacy is wired but currently latent (no Steckbrief anchor)
# --------------------------------------------------------------------------- #


def test_growth_determinacy_is_latent_in_real_corpus() -> None:
    # Documents the current state: no committed Steckbrief carries the
    # growth_determinacy anchor, so the column is compared for 0 species today.
    # If a Steckbrief starts carrying it, this assertion flips and the wiring
    # (proven live by the test below) takes over -- update this test then.
    from pathlib import Path as _Path

    from app.migrations.seed_steckbrief_consistency import (
        ATTR_ANCHORS,
        _plants_dir,
        parse_steckbrief,
        repo_root,
    )

    anchor_attr = "growth_determinacy"
    assert anchor_attr in ATTR_ANCHORS
    carriers = [
        p.name for p in sorted(_plants_dir(repo_root()).glob("*.md")) if anchor_attr in parse_steckbrief(_Path(p))
    ]
    assert carriers == [], f"growth_determinacy no longer latent: {carriers}"


def test_growth_determinacy_drift_is_caught_when_a_steckbrief_carries_it(tmp_path: Path) -> None:
    # Proves the wiring is not dead: the moment a Steckbrief exposes the
    # growth_determinacy anchor, a mismatch against the seed lifecycle_config is
    # detected exactly like the active attributes.
    plants = tmp_path / "plants"
    seed = tmp_path / "seed_data"
    plants.mkdir(parents=True, exist_ok=True)
    (plants / "foo.md").write_text(
        textwrap.dedent(
            """\
            | Wissenschaftlicher Name | Foo bar | `species.scientific_name` |
            | Determinität | indeterminate | `lifecycle_configs.growth_determinacy` |
            """
        ),
        encoding="utf-8",
    )
    seed.mkdir(parents=True, exist_ok=True)
    (seed / "species.yaml").write_text("species: []\n", encoding="utf-8")
    (seed / "plant_info_test.yaml").write_text(
        textwrap.dedent(
            """\
            lifecycle_configs:
              Foo bar:
                growth_determinacy: determinate
            """
        ),
        encoding="utf-8",
    )

    drifts, unmatched = find_drifts(plants, load_seed_attributes(seed))

    assert not unmatched
    assert len(drifts) == 1
    assert drifts[0].attribute == "growth_determinacy"
    assert drifts[0].steckbrief_value == "indeterminate"
    assert drifts[0].seed_value == "determinate"
