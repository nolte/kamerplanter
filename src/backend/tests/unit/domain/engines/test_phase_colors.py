"""The phase colour reference runs against the shared vectors (REQ-053 §19.6, GP-FR-067, GP-UX-005, #2489).

``spec/e2e-testcases/fixtures/garden-plan-vectors.json`` (operation ``phase_color``) is read by this module and by
``features/gardenPlanner/planting/phaseColors.vectors.test.ts``, so the PDF legend and the plan on screen paint a phase
in the same colour. The hash is also pinned against its written definition, so the reference is not only compared
with itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.domain.engines.phase_colors import (
    FALLBACK_PALETTE,
    PHASE_COLORS,
    name_hash,
    normalised_phase_name,
    phase_color,
)
from app.domain.engines.plan_svg_engine import _PAINT
from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:
    raise RuntimeError("checkout root not found; the shared phase colour vectors are unreachable from here")

VECTORS: dict[str, Any] = json.loads(
    (_REPO_ROOT / "spec" / "e2e-testcases" / "fixtures" / "garden-plan-vectors.json").read_text(encoding="utf-8")
)
CASES: list[dict[str, Any]] = [case for case in VECTORS["cases"] if case["operation"] == "phase_color"]


class TestPhaseColorVectors:
    @pytest.mark.parametrize("case", [pytest.param(case, id=case["id"]) for case in CASES])
    def test_vector(self, case: dict[str, Any]) -> None:
        assert phase_color(case["input"]["name"]) == case["expected"]

    def test_the_vectors_cover_every_named_phase_the_fallback_and_the_normalisation(self) -> None:
        assert "phase_color" in VECTORS["operations"]
        named = {case["input"]["name"] for case in CASES}
        assert set(PHASE_COLORS) <= named, "every named phase needs its own vector"
        expected = {case["expected"] for case in CASES}
        assert expected & set(FALLBACK_PALETTE) - set(PHASE_COLORS.values()), "the hash fallback needs a vector"
        ids = {case["id"] for case in CASES}
        assert {"phase-color-upper-case", "phase-color-whitespace", "phase-color-unknown-case-sensitive"} <= ids


class TestAlgorithm:
    def test_the_hash_is_the_written_int32_recurrence(self) -> None:
        def reference(name: str) -> int:
            encoded = name.encode("utf-16-le")
            units = [encoded[i] | encoded[i + 1] << 8 for i in range(0, len(encoded), 2)]
            hashed = 0
            for unit in units:
                hashed = ((hashed * 31 + unit + 2**31) % 2**32) - 2**31
            return hashed

        for name in ("dormancy", "juvenile", "Überwinterung", "x" * 200):
            assert name_hash(name) == reference(name)

    def test_the_normalisation_keeps_letters_a_to_z_only(self) -> None:
        assert normalised_phase_name("  Pre-Bloom\t") == "prebloom"

    @pytest.mark.parametrize("name", ["flowering", "dormancy", "", "\U0001f331", "<script>"])
    def test_every_colour_is_a_paint_the_svg_writer_accepts(self, name: str) -> None:
        assert _PAINT.match(phase_color(name))
