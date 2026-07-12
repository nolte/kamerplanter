"""CI gates for the manual 3-way plant-property enum sync (Plan WP-9-rest).

The plant-property enums (``SeedType``, ``GrowthHabit``, ``FloweringStrategy``,
``RootType``, ``CycleType``, …) are duplicated across three artefacts with **no
code-gen** between them:

1. the canonical Python ``StrEnum`` in ``app.common.enums``,
2. the JSON-Schema enum def in
   ``src/backend/app/migrations/seed_data/schemas/_defs.schema.yaml`` (validates
   the seed data), and
3. the TypeScript union in ``src/frontend/src/api/types.ts`` (the frontend
   contract).

A drift between any two of these silently breaks either the seed load (backend)
or the frontend rendering. These tests make that drift a hard failure before
merge. A fourth artefact — the ``enums.*`` i18n keys (de + en) — is covered by
the i18n-completeness gate below so a new enum value can never render as a raw
token in the UI.

Both gates are generalizable over ``_ENUM_SYNC`` / ``_I18N_ENUMS``; adding a new
plant-property enum to those registries wires it into the gate automatically.
"""

from __future__ import annotations

import json
import re
from enum import StrEnum
from pathlib import Path

import pytest
import yaml

from app.common.enums import (
    ClimactericClass,
    CycleType,
    DtmReference,
    FloweringStrategy,
    GrowthHabit,
    HarvestedPart,
    HarvestPattern,
    RootType,
    SeedType,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFS_SCHEMA = _REPO_ROOT / "src" / "backend" / "app" / "migrations" / "seed_data" / "schemas" / "_defs.schema.yaml"
_TYPES_TS = _REPO_ROOT / "src" / "frontend" / "src" / "api" / "types.ts"
_LOCALES = _REPO_ROOT / "src" / "frontend" / "src" / "i18n" / "locales"

# (python enum, _defs.schema.yaml def key, types.ts type name) — every entry is
# validated to be identical across all three artefacts.
_ENUM_SYNC: list[tuple[type[StrEnum], str, str]] = [
    (SeedType, "seed_type", "SeedType"),
    (GrowthHabit, "growth_habit", "GrowthHabit"),
    (FloweringStrategy, "flowering_strategy", "FloweringStrategy"),
    (RootType, "root_type", "RootType"),
    (CycleType, "cycle_type", "CycleType"),
]

# (python enum, enums.* i18n key) — every value must resolve in de AND en.
_I18N_ENUMS: list[tuple[type[StrEnum], str]] = [
    (SeedType, "seedType"),
    (GrowthHabit, "growthHabit"),
    (FloweringStrategy, "floweringStrategy"),
    (RootType, "rootType"),
    (CycleType, "cycleType"),
    (HarvestPattern, "harvestPattern"),
    (HarvestedPart, "harvestedPart"),
    (ClimactericClass, "climacteric"),
    (DtmReference, "dtmReference"),
]


def _enum_values(enum: type[StrEnum]) -> set[str]:
    return {member.value for member in enum}


def _schema_enum_values(defs_key: str) -> set[str]:
    defs = yaml.safe_load(_DEFS_SCHEMA.read_text(encoding="utf-8"))["$defs"]
    assert defs_key in defs, f"_defs.schema.yaml has no '$defs.{defs_key}'"
    return set(defs[defs_key]["enum"])


def _ts_union_values(type_name: str) -> set[str]:
    """Parse ``export type <type_name> = 'a' | 'b' | …;`` from types.ts.

    The declaration may span multiple lines and is terminated by ``;``.
    """
    text = _TYPES_TS.read_text(encoding="utf-8")
    match = re.search(rf"export type {re.escape(type_name)}\s*=\s*(.*?);", text, re.DOTALL)
    assert match is not None, f"types.ts has no 'export type {type_name}'"
    return set(re.findall(r"'([^']+)'", match.group(1)))


def _locale_enum_block(locale: str, i18n_key: str) -> dict[str, str]:
    data = json.loads((_LOCALES / locale / "translation.json").read_text(encoding="utf-8"))
    return data.get("enums", {}).get(i18n_key, {})


class TestPlantPropertyEnumSync:
    @pytest.mark.parametrize("enum,defs_key,ts_type", _ENUM_SYNC, ids=lambda v: getattr(v, "__name__", v))
    def test_enum_matches_schema_and_types(self, enum: type[StrEnum], defs_key: str, ts_type: str) -> None:
        py = _enum_values(enum)
        schema = _schema_enum_values(defs_key)
        ts = _ts_union_values(ts_type)
        assert py == schema, (
            f"{enum.__name__} drift enums.py vs _defs.schema.yaml['{defs_key}']: "
            f"only-in-python={sorted(py - schema)} only-in-schema={sorted(schema - py)}"
        )
        assert py == ts, (
            f"{enum.__name__} drift enums.py vs types.ts['{ts_type}']: "
            f"only-in-python={sorted(py - ts)} only-in-types={sorted(ts - py)}"
        )

    def test_new_seed_type_is_covered(self) -> None:
        # Regression guard: the enum this lane introduced must stay in the registry.
        assert any(enum is SeedType for enum, _, _ in _ENUM_SYNC)

    def test_gate_detects_injected_schema_drift(self) -> None:
        # Proof the gate bites: run the exact equality check the gate uses against a
        # deliberately drifted schema view (a value dropped) and confirm it fails.
        py = _enum_values(SeedType)
        drifted_schema = py - {"clone"}
        with pytest.raises(AssertionError):
            assert py == drifted_schema, "injected schema drift must fail the gate"

    def test_gate_detects_injected_types_drift(self) -> None:
        # Proof the gate bites on the TypeScript side too (an extra frontend value).
        py = _enum_values(SeedType)
        drifted_ts = py | {"ghost_value"}
        with pytest.raises(AssertionError):
            assert py == drifted_ts, "injected types.ts drift must fail the gate"


class TestPlantPropertyEnumI18n:
    @pytest.mark.parametrize("enum,i18n_key", _I18N_ENUMS, ids=lambda v: getattr(v, "__name__", v))
    def test_every_value_has_de_and_en_label(self, enum: type[StrEnum], i18n_key: str) -> None:
        de = _locale_enum_block("de", i18n_key)
        en = _locale_enum_block("en", i18n_key)
        for member in enum:
            assert member.value in de, f"enums.{i18n_key}.{member.value} missing in de/translation.json"
            assert member.value in en, f"enums.{i18n_key}.{member.value} missing in en/translation.json"

    def test_gate_detects_injected_i18n_gap(self) -> None:
        # Proof the gate bites: dropping a key from a copy of the de block makes the
        # membership assertion (the exact check the gate runs) fail, while the live
        # block stays complete.
        de = dict(_locale_enum_block("de", "seedType"))
        de.pop("clone", None)
        with pytest.raises(AssertionError):
            assert "clone" in de, "injected i18n gap must fail the gate"
        assert "clone" in _locale_enum_block("de", "seedType"), "live de block must still be complete"
