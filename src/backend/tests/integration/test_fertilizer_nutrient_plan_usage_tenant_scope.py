"""#2099 (MT-001) — the nutrient-plan usage lookup of a fertilizer names only plans the caller may see.

``GET /t/{slug}/fertilizers/{key}/nutrient-plans`` scanned ``nutrient_plan_phase_entries``
for the fertilizer and joined ``DOCUMENT(nutrient_plans/…)`` without a tenant predicate.
For a **global** fertilizer that returned plan key, plan name, phase entries and dosages
of every tenant that uses it. Run through the real route against a real ArangoDB.
"""

from __future__ import annotations

import pytest

from tests.support.arango_integration import run_database_name
from tests.support.boundary_harness import open_env, put

pytestmark = pytest.mark.usefixtures("arango_db")

GLOBAL_FERT = "fert-global"
BASE = "/api/v1/t/alice/fertilizers"


@pytest.fixture(scope="module")
def env():
    from app.data_access.arango import collections as col
    from app.domain.models.fertilizer import Fertilizer
    from app.domain.models.nutrient_plan import DeliveryChannel, NutrientPlan, NutrientPlanPhaseEntry

    e = open_env(
        run_database_name("fert_plan_usage_scope"), ("app.api.v1.tenant_scoped.router", "tenant_scoped_router")
    )
    put(
        e.db,
        col.FERTILIZERS,
        Fertilizer(_key=GLOBAL_FERT, tenant_key="", product_name="Global Grow", fertilizer_type="base"),
    )
    for key, tenant, name in (
        ("plan-global", "", "Seed plan"),
        ("plan-a", "tenant-alice", "Alice plan"),
        ("plan-b", "tenant-bob", "Bob secret plan"),
    ):
        put(e.db, col.NUTRIENT_PLANS, NutrientPlan(_key=key, tenant_key=tenant, name=name))
        put(
            e.db,
            col.NUTRIENT_PLAN_PHASE_ENTRIES,
            NutrientPlanPhaseEntry(
                _key=f"entry-{key}",
                plan_key=key,
                phase_name="vegetative",
                sequence_order=1,
                week_start=1,
                week_end=4,
                delivery_channels=[
                    DeliveryChannel(
                        channel_id="c1",
                        application_method="drench",
                        fertilizer_dosages=[{"fertilizer_key": GLOBAL_FERT, "ml_per_liter": 1.5}],
                    )
                ],
            ),
        )
    yield e
    e.close()


def _usage(env) -> list[str]:
    response = env.client.get(f"{BASE}/{GLOBAL_FERT}/nutrient-plans")
    assert response.status_code == 200, response.text
    return sorted(row["key"] for row in response.json())


def test_a_global_fertilizers_usage_hides_the_plans_of_other_tenants(env) -> None:
    env.caller.as_a()
    keys = _usage(env)
    assert "plan-b" not in keys
    assert "Bob secret plan" not in env.client.get(f"{BASE}/{GLOBAL_FERT}/nutrient-plans").text


def test_own_and_global_plans_are_still_listed(env) -> None:
    env.caller.as_a()
    assert _usage(env) == ["plan-a", "plan-global"]


def test_the_other_tenant_sees_its_own_and_the_global_plans(env) -> None:
    env.caller.as_b()
    assert _usage(env) == ["plan-b", "plan-global"]


def test_an_empty_tenant_key_yields_global_plans_only(env) -> None:
    from app.data_access.arango.fertilizer_repository import ArangoFertilizerRepository

    rows = ArangoFertilizerRepository(env.db).get_nutrient_plan_usage(GLOBAL_FERT, tenant_key="")
    assert sorted(r["key"] for r in rows) == ["plan-global"]
