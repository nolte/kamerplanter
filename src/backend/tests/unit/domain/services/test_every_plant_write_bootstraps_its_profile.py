"""REQ-022 / #1422 round 4 — every path that stores a plant gives it a care profile.

The bootstrap added in round 3 sat on `PlantInstanceService.create_plant` only, and
two paths write a `PlantInstance` without going through it — both of them named in
`plant_instance_service`'s own module docstring since #1349:

* `PlantingRunService.create_plants` writes each batch instance straight to the
  repository, so a run of forty plants produced forty plants that would never have
  received a care reminder;
* `_spawn_pup` does the same for the D10 pup.

That is the #948 shape one more time, and it is the third instance in this PR alone:
a predicate opted into at the call site, with a sibling path that never opted in. The
two call sites are fixed; this file is what stops the next one being added silently.

**It matches on the write, not on the caller.** A new method that calls
`create(...)` on a plant repository must either bootstrap or say why not — "I did not
think of care profiles" is the failure mode, so not thinking of them has to fail.

**What it detects is the mention, not the reachability**, and that limit is measured
rather than assumed: replacing the batch path's `if self._care_profile_bootstrap is
not None and created.key:` with `if False:` leaves this file green, because the call
still appears inside the dead branch. Deciding whether a call *runs* needs the
control-flow graph; deciding whether the author thought about it needs only this.

That is the right trade for the defect this guards. A dead-but-present bootstrap is a
deliberate act someone has to write; the three instances in #1422 were all the other
kind — a path added later by someone who never knew the bootstrap existed.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_SERVICES = Path(__file__).resolve().parents[4] / "app" / "domain" / "services"

#: Repository attributes that hold a plant repository, by the name each service uses.
_PLANT_REPO_ATTRIBUTES = {"_repo", "_plant_repo"}

#: Services whose `_repo` is *not* a plant repository — the reason the attribute name
#: alone cannot decide, and the reason this list exists rather than a guess.
_NOT_PLANT_SERVICES = {
    "planting_run_service.py": "its `_repo` is the run repository; `_plant_repo` is the plant one",
}

#: Methods that store a plant and deliberately do not bootstrap, with the reason.
#: Empty is the goal; an entry is a decision, not a placeholder.
_EXEMPT: dict[str, str] = {}


def _plant_writing_methods() -> dict[str, ast.FunctionDef]:
    """Methods that call ``<plant repo>.create(...)``, by ``file::method``."""
    found: dict[str, ast.FunctionDef] = {}
    for path in sorted(_SERVICES.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for call in ast.walk(node):
                if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)):
                    continue
                if call.func.attr != "create":
                    continue
                target = call.func.value
                if not (isinstance(target, ast.Attribute) and target.attr in _PLANT_REPO_ATTRIBUTES):
                    continue
                if path.name in _NOT_PLANT_SERVICES and target.attr == "_repo":
                    continue
                if path.name != "plant_instance_service.py" and target.attr == "_repo":
                    # Another service's own `_repo` is its own aggregate, not a plant.
                    continue
                found[f"{path.name}::{node.name}"] = node
    return found


def _bootstraps(node: ast.FunctionDef) -> bool:
    """Does this method reach the care-profile bootstrap, directly or via the helper?"""
    for inner in ast.walk(node):
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Attribute)
            and inner.func.attr in {"_bootstrap_care_profile_for", "_care_profile_bootstrap"}
        ):
            return True
        if isinstance(inner, ast.Attribute) and inner.attr == "_care_profile_bootstrap":
            return True
    return False


def test_the_scan_finds_the_known_plant_writers():
    """The control. Every assertion below is over this set, so an empty one agrees.

    Three methods store a plant today. If the scan stops seeing them it has broken,
    and the real check would pass over nothing — which is the failure mode this file
    exists to prevent, one layer up.
    """
    found = set(_plant_writing_methods())

    assert "plant_instance_service.py::create_plant" in found, found
    assert "plant_instance_service.py::_spawn_pup" in found, found
    assert "planting_run_service.py::create_plants" in found, found


@pytest.mark.parametrize("qualified", sorted(_plant_writing_methods()))
def test_every_plant_write_bootstraps_a_care_profile(qualified: str):
    """A plant that reaches the database without a profile never gets a reminder.

    The nightly generator iterates **stored profiles**, so the omission is silent:
    the plant exists, the page renders, and nothing is ever due.
    """
    if qualified in _EXEMPT:
        pytest.skip(f"exempt: {_EXEMPT[qualified]}")

    node = _plant_writing_methods()[qualified]

    assert _bootstraps(node), (
        f"{qualified} stores a plant and never reaches the care-profile bootstrap. "
        f"Call `self._bootstrap_care_profile_for(created)` (or the injected hook), or "
        f"add it to _EXEMPT with the reason it needs no profile (REQ-022, #1422)."
    )
