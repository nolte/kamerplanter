"""#2107 (MT-010) — a repository read nothing calls must not stay around unscoped.

A dead read is not harmless when it takes no tenant: it is the first thing the
next handler finds when it needs "get X by Y", and it reads every tenant's rows.
The audit named six (``plant_instance_repository.get_by_slot``,
``tank_repository.get_tanks_for_location``, ``weather_forecast_repository.get``,
``watering_log_repository.get_latest_by_plant`` / ``get_recent_runoff_logs``,
``aquaponik.link_tank`` / ``link_growbed``); #2107 removed them.

**The rule.** Every public read the derived inventory of
``test_tenant_scoped_reads_are_derived.py`` sees, whose verdict is *not*
``strict`` or ``catalogue-union`` (i.e. it can be called without a tenant) and
whose name is referenced nowhere under ``app/`` — no attribute access, no bare
name, no string constant (a ``getattr`` dispatch) — is a finding. The ones that
existed when the rule was written are pinned in :data:`_KNOWN_DEAD` so the list
can only shrink: a new dead unscoped read fails, a removed one must leave the list.

**What it does not see**, named rather than discovered later: a method whose
*name* is shared with a live method elsewhere (``get``, ``get_by_slot`` — the
measured reason the audit's own six had to be found by hand), and writers (the
inventory holds reads only).
"""

from __future__ import annotations

import ast
from collections import Counter
from functools import cache
from pathlib import Path

from tests.support.execution_guards import find_project_root
from tests.unit.guards.test_tenant_scoped_reads_are_derived import _verdicts, build_inventory

_APP = find_project_root(Path(__file__)) / "app"

#: Verdicts that make a tenant impossible to omit.
_SCOPED = frozenset({"strict", "catalogue-union"})

#: Measured 2026-10-05 after the audit's six were removed. Each is a dead read that
#: can be called without a tenant; remove the method (and its interface entry) and
#: then the line here. Never add to this set — scope or delete the new method.
_KNOWN_DEAD: frozenset[tuple[str, str]] = frozenset(
    {
        ("ArangoActuatorRepository", "get_rule"),
        ("ArangoActuatorRepository", "get_schedule"),
        ("ArangoAttachmentRepository", "count_by_tenant"),
        ("ArangoInvenTreeRepository", "get_reference"),
        ("ArangoIrrigationDemandRepository", "get_latest_for_site"),
        ("ArangoLocationAssignmentRepository", "list_by_membership"),
        ("ArangoMcpAuditRepository", "list_for_user_accounts"),
        ("ArangoNutrientPlanRepository", "get_phase_entry_by_key"),
        ("ArangoOverwinteringProfileTemplateRepository", "count_subjects"),
        ("ArangoPostHarvestRepository", "list_burping_events"),
        ("ArangoSpeciesRepository", "get_by_normalized_scientific_name"),
        ("ArangoSuccessionPlanRepository", "get_run_keys_for_plan"),
        ("ArangoTankRepository", "get_schedule_by_key"),
        ("ArangoTaskRepository", "batch_get_tasks"),
    }
)


def _referenced_names(root: Path) -> Counter[str]:
    names: Counter[str] = Counter()
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Attribute):
                names[node.attr] += 1
            elif isinstance(node, ast.Name):
                names[node.id] += 1
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.isidentifier():
                names[node.value] += 1
    return names


def _dead_unscoped(root: Path) -> set[tuple[str, str]]:
    names = _referenced_names(root)
    return {
        (v.method.owner, v.method.name)
        for v in _verdicts(build_inventory(root))
        if v.category not in _SCOPED and names[v.method.name] == 0
    }


@cache
def _measured() -> frozenset[tuple[str, str]]:
    return frozenset(_dead_unscoped(_APP))


def test_no_new_dead_read_can_be_called_without_a_tenant() -> None:
    new = sorted(_measured() - _KNOWN_DEAD)
    assert new == [], (
        "These repository reads are referenced nowhere under app/ and can be called without a tenant. "
        f"Delete them, or give them `*, tenant_key: str` (#2107): {new}"
    )


def test_the_known_dead_list_only_shrinks() -> None:
    gone = sorted(_KNOWN_DEAD - _measured())
    assert gone == [], f"Removed or scoped since the list was pinned — drop them from _KNOWN_DEAD: {gone}"


def test_the_rule_finds_a_planted_dead_read_and_ignores_a_called_one(tmp_path: Path) -> None:
    """Self-test on the same expression, against a copy of the tree with one read planted."""
    import shutil

    root = tmp_path / "app"
    shutil.copytree(_APP, root, ignore=shutil.ignore_patterns("__pycache__"))
    target = root / "data_access" / "arango" / "tank_repository.py"
    planted = (
        "\n    def tanks_by_colour(self, colour: str) -> list:\n"
        '        return list(self._db.aql.execute(f"FOR t IN {col.TANKS} FILTER t.colour == @c RETURN t", '
        'bind_vars={"c": colour}))\n'
    )
    target.write_text(target.read_text(encoding="utf-8") + planted, encoding="utf-8")
    assert ("ArangoTankRepository", "tanks_by_colour") in _dead_unscoped(root)

    caller = root / "domain" / "services" / "tank_service.py"
    caller.write_text(caller.read_text(encoding="utf-8") + "\n_USES = 'tanks_by_colour'\n", encoding="utf-8")
    assert ("ArangoTankRepository", "tanks_by_colour") not in _dead_unscoped(root)
