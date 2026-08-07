"""One generated plan, two tenants, and what happens when one of them edits it (#1003).

``ActivityPlanService`` persists every plan it generates **globally** —
``tenant_key == ""``, ``is_system == False`` — and the lookup that finds it again
carried no tenant predicate at all. Two tenants growing the same species
therefore shared one plan object, and #992's guard let both of them write it: it
refuses a *foreign tenant's* workflow and a *system* workflow, and a global
non-system workflow is neither. So tenant A switching an activity off switched it
off for tenant B.

The answer implemented here is copy-on-write. The generated plan stays a shared
template; a tenant's first write materialises a private copy owned by them, and
they work on the copy from then on.

Observed red first, against the same code with the fork removed from
``TaskService._resolve_task_template_for_tenant_write`` and the tenant predicate
removed from ``get_auto_generated_workflow_for_species`` — the route move and the
threading of ``tenant_key`` are the scaffolding the fix stands on, not the fix:

* ``test_tenant_b_still_sees_the_activity_tenant_a_switched_off``
  ``assert False is True`` — B's plan showed A's edit.
* ``test_tenant_a_edits_their_own_copy_not_the_shared_template``
  ``assert 'wf-shared' != 'wf-shared'`` — A wrote the shared object itself.
* ``test_the_shared_templates_document_is_never_written``
  ``assert ['tt-water'] == []`` — the shared row was updated in place.
* ``test_tenant_b_still_sees_the_activity_tenant_a_deleted``
  ``assert 1 == 2`` — the delete removed it from B's plan too.
* ``test_a_regenerate_does_not_replace_the_shared_template``
  ``assert 'wf-shared' not in {…}`` failed: the shared workflow was deleted.

The #324 direction is asserted just as hard, in
:class:`TestATenantWhoHasNeverEditedTheSharedPlan`. Every generated plan in an
existing installation is global, so a strict ``tenant_key == caller`` predicate
would satisfy every isolation assertion above by matching nothing, and take the
feature with it.

The database double stores documents and replays the predicates the queries
actually spell out, so "the shared row was not written" is asserted on the
collection rather than on a stub's call log, and a strict predicate on the
generated-plan lookup turns the second class red rather than passing unnoticed.
"""

from __future__ import annotations

import itertools
from typing import Any
from unittest.mock import MagicMock

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.api.v1.activity_plans.tenant_router import router as activity_plans_tenant_router
from app.common.auth import get_current_tenant
from app.common.dependencies import get_activity_plan_service, get_task_repo, get_task_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.models.task import WorkflowTemplate
from app.domain.models.tenant_context import TenantContext
from app.domain.services.activity_plan_service import ActivityPlanService
from app.domain.services.task_service import TaskService
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase, apply_predicates

SPECIES = "solanum_lycopersicum"

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"
SLUG = {TENANT_A: "anna", TENANT_B: "bert"}

SHARED_PLAN = "wf-shared"
WATERING = "tt-water"
PRUNING = "tt-prune"

#: The union the fixed lookup spells out. The handler below relaxes only for
#: this exact shape; anything else — no predicate, or a strict equality — is
#: replayed literally, which is what keeps both failure directions observable.
_TENANT_UNION = 'doc.tenant_key == @tenant_key OR doc.tenant_key == ""'


def _shared_workflow() -> dict[str, Any]:
    """What ``ActivityPlanService.generate_plan`` persists: global, not system."""
    return {
        "_key": SHARED_PLAN,
        "_id": f"{col.WORKFLOW_TEMPLATES}/{SHARED_PLAN}",
        "tenant_key": "",
        "name": "Tomate",
        "auto_generated": True,
        "is_system": False,
        "species_key": SPECIES,
        "total_duration_days": 120,
        "created_at": "2026-01-01T00:00:00+00:00",
    }


def _shared_task_templates() -> dict[str, dict[str, Any]]:
    return {
        key: {
            "_key": key,
            "_id": f"{col.TASK_TEMPLATES}/{key}",
            "name": name,
            "enabled": True,
            "days_offset": offset,
            "sequence_order": order,
            "trigger_phase": "vegetative",
            "workflow_template_key": SHARED_PLAN,
        }
        for order, (key, name, offset) in enumerate(
            [(WATERING, "Giessen", 3), (PRUNING, "Ausgeizen", 7)],
        )
    }


class _Collection:
    """In-memory document collection double recording every write."""

    def __init__(self, name: str, docs: dict[str, dict[str, Any]] | None = None) -> None:
        self._name = name
        self._keys = (f"{name}-{n}" for n in itertools.count(1))
        self.docs: dict[str, dict[str, Any]] = {k: dict(v) for k, v in (docs or {}).items()}
        self.inserted: list[dict[str, Any]] = []
        self.updated: list[dict[str, Any]] = []
        self.deleted: list[str] = []

    def get(self, key: str) -> dict[str, Any] | None:
        doc = self.docs.get(key)
        return dict(doc) if doc else None

    def insert(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        key = data.get("_key") or next(self._keys)
        doc = {**data, "_key": key, "_id": f"{self._name}/{key}"}
        self.docs[key] = doc
        self.inserted.append(dict(doc))
        return {"new": dict(doc)}

    def update(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        key = data["_key"]
        doc = {**self.docs.get(key, {}), **data, "_id": f"{self._name}/{key}"}
        self.docs[key] = doc
        self.updated.append(dict(doc))
        return {"new": dict(doc)}

    def delete(self, key: str) -> bool:
        self.docs.pop(key, None)
        self.deleted.append(key)
        return True


class _Fixture:
    """Router + service + repository over a document store both tenants share."""

    def __init__(self) -> None:
        self.workflows = _Collection(col.WORKFLOW_TEMPLATES, {SHARED_PLAN: _shared_workflow()})
        self.templates = _Collection(col.TASK_TEMPLATES, _shared_task_templates())
        self.phases = _Collection(col.WORKFLOW_PHASES)
        collections = {
            col.WORKFLOW_TEMPLATES: self.workflows,
            col.TASK_TEMPLATES: self.templates,
            col.WORKFLOW_PHASES: self.phases,
            col.WF_CONTAINS: _Collection(col.WF_CONTAINS),
            col.WF_HAS_PHASE: _Collection(col.WF_HAS_PHASE),
        }
        self.aql = (
            ReplayingAql()
            # Edge detach/attach queries return nothing; registered first because
            # their collection names are the more specific markers.
            .route(col.WF_CONTAINS, lambda query, bind_vars: [])
            .route(col.WF_HAS_PHASE, lambda query, bind_vars: [])
            .route(col.INSTANCE_OF, lambda query, bind_vars: [])
            .route(col.WORKFLOW_TEMPLATES, self._generated_plan_lookup)
            .route(col.WORKFLOW_PHASES, self._phases_of_workflow)
            .route(col.TASK_TEMPLATES, self._task_templates_of_workflow)
        )
        self.repo = ArangoTaskRepository(ReplayingDatabase(self.aql, collections))
        self.task_service = TaskService(self.repo, MagicMock(), MagicMock())
        self.plan_service = ActivityPlanService(
            engine=MagicMock(),
            activity_repo=MagicMock(),
            phase_repo=MagicMock(),
            task_repo=self.repo,
            planting_run_repo=MagicMock(),
        )

    # ── AQL handlers ──

    def _generated_plan_lookup(self, query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        """Replay ``get_auto_generated_workflow_for_species``.

        The literal predicates (``auto_generated``, ``species_key``) are applied
        by hand because they are the query's own; the *tenant* half is taken from
        the query text, which is the half under test:

        * no tenant predicate — the pre-#1003 query — every row matches and the
          shared template wins on ``created_at``, so a tenant never finds its
          copy;
        * a strict ``doc.tenant_key == @tenant_key`` is replayed literally by
          :func:`apply_predicates`, so a tenant without a copy finds nothing —
          the #324 regression, red on this fixture;
        * the union is honoured with the caller's row preferred.
        """
        rows = [
            doc
            for doc in self.workflows.docs.values()
            if doc.get("auto_generated") and doc.get("species_key") == bind_vars.get("species_key")
        ]
        if _TENANT_UNION in query:
            tenant_key = bind_vars["tenant_key"]
            rows = [doc for doc in rows if doc.get("tenant_key", "") in (tenant_key, "")]
            rows.sort(key=lambda doc: (0 if doc.get("tenant_key", "") == tenant_key else 1, doc["_key"]))
        else:
            rows = apply_predicates(rows, query, bind_vars)
        return rows[:1]

    def _phases_of_workflow(self, query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        return apply_predicates(list(self.phases.docs.values()), query, bind_vars)

    def _task_templates_of_workflow(self, query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        rows = apply_predicates(list(self.templates.docs.values()), query, bind_vars)
        return sorted(rows, key=lambda doc: doc.get("sequence_order", 0))

    # ── HTTP ──

    def client(self, tenant_key: str) -> TestClient:
        app = FastAPI()
        app.include_router(activity_plans_tenant_router, prefix="/api/v1/t/{tenant_slug}")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
            tenant_key=tenant_key,
            tenant_slug=SLUG[tenant_key],
            user_key=f"user-{tenant_key}",
            role=TenantRole.GROWER,
        )
        app.dependency_overrides[get_task_service] = lambda: self.task_service
        app.dependency_overrides[get_activity_plan_service] = lambda: self.plan_service
        app.dependency_overrides[get_task_repo] = lambda: self.repo
        return TestClient(app)

    # ── Actions, in the SPA's own terms ──

    def plan_of(self, tenant_key: str) -> dict[str, Any]:
        """What the activity-plan tab shows this tenant."""
        resp = self.client(tenant_key).post(
            self._url(tenant_key, "/generate"),
            json={"species_key": SPECIES},
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    def patch_template(self, tenant_key: str, template_key: str, body: dict[str, Any]) -> Any:
        return self.client(tenant_key).patch(self._url(tenant_key, f"/templates/{template_key}"), json=body)

    def delete_template(self, tenant_key: str, template_key: str) -> Any:
        return self.client(tenant_key).delete(self._url(tenant_key, f"/templates/{template_key}"))

    @staticmethod
    def _url(tenant_key: str, path: str) -> str:
        return f"/api/v1/t/{SLUG[tenant_key]}/activity-plans{path}"


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


def _activity(plan: dict[str, Any], name: str) -> dict[str, Any]:
    """Find an activity by *name*, which survives the fork — the key does not."""
    matches = [tt for tt in plan["templates"] if tt["name"] == name]
    assert len(matches) == 1, f"expected exactly one {name!r} in {[tt['name'] for tt in plan['templates']]}"
    return matches[0]


class TestOneEditByOneTenant:
    """The load-bearing scenario: two tenants, one species, one generated plan."""

    def test_tenant_b_still_sees_the_activity_tenant_a_switched_off(self):
        fx = _Fixture()

        assert fx.patch_template(TENANT_A, WATERING, {"enabled": False}).status_code == 200

        assert _activity(fx.plan_of(TENANT_B), "Giessen")["enabled"] is True

    def test_tenant_a_sees_their_own_edit(self):
        """The other half: forking must not lose the edit that caused it."""
        fx = _Fixture()

        assert fx.patch_template(TENANT_A, WATERING, {"enabled": False}).status_code == 200

        assert _activity(fx.plan_of(TENANT_A), "Giessen")["enabled"] is False

    def test_tenant_a_edits_their_own_copy_not_the_shared_template(self):
        fx = _Fixture()

        fx.patch_template(TENANT_A, WATERING, {"days_offset": 9})

        assert fx.plan_of(TENANT_A)["workflow_template_key"] != SHARED_PLAN
        assert fx.plan_of(TENANT_B)["workflow_template_key"] == SHARED_PLAN

    def test_the_shared_templates_document_is_never_written(self):
        """Asserted on the collection, not on a call log: nothing touched the source."""
        fx = _Fixture()

        fx.patch_template(TENANT_A, WATERING, {"enabled": False, "days_offset": 9})

        assert [doc["_key"] for doc in fx.templates.updated] != [WATERING]
        assert fx.templates.docs[WATERING]["enabled"] is True
        assert fx.templates.docs[WATERING]["days_offset"] == 3
        assert fx.workflows.docs[SHARED_PLAN] == _shared_workflow()

    def test_the_copy_is_owned_by_the_editing_tenant_and_still_a_generated_plan(self):
        """Both flags matter: ownership makes it private, ``auto_generated`` makes it findable."""
        fx = _Fixture()

        fx.patch_template(TENANT_A, WATERING, {"enabled": False})

        copy_key = fx.plan_of(TENANT_A)["workflow_template_key"]
        copy = fx.workflows.docs[copy_key]
        assert copy["tenant_key"] == TENANT_A
        assert copy["auto_generated"] is True
        assert copy["is_system"] is False
        assert copy["source_workflow_key"] == SHARED_PLAN
        assert copy["species_key"] == SPECIES

    def test_the_copy_carries_the_whole_plan_not_just_the_edited_activity(self):
        fx = _Fixture()

        fx.patch_template(TENANT_A, WATERING, {"enabled": False})

        plan = fx.plan_of(TENANT_A)
        assert sorted(tt["name"] for tt in plan["templates"]) == ["Ausgeizen", "Giessen"]
        assert plan["total_activities"] == 2

    def test_the_plan_says_whether_it_is_still_shared(self):
        """#1003 §3: nothing else distinguishes the two, so the SPA cannot say so either."""
        fx = _Fixture()

        assert fx.plan_of(TENANT_A)["is_shared_template"] is True

        fx.patch_template(TENANT_A, WATERING, {"enabled": False})

        assert fx.plan_of(TENANT_A)["is_shared_template"] is False
        assert fx.plan_of(TENANT_B)["is_shared_template"] is True


class TestTheForkHappensExactlyOnce:
    """A second write must reach the same copy, however the client addresses it."""

    def test_a_second_edit_does_not_produce_a_second_copy(self):
        fx = _Fixture()

        fx.patch_template(TENANT_A, WATERING, {"enabled": False})
        first_copy = fx.plan_of(TENANT_A)["workflow_template_key"]
        fx.patch_template(TENANT_A, _activity(fx.plan_of(TENANT_A), "Ausgeizen")["key"], {"days_offset": 4})

        assert fx.plan_of(TENANT_A)["workflow_template_key"] == first_copy
        assert len([doc for doc in fx.workflows.docs.values() if doc.get("tenant_key") == TENANT_A]) == 1

    def test_a_stale_client_still_holding_the_shared_key_reaches_the_copy(self):
        """The SPA keeps the pre-fork keys until it reloads; they must not write the source."""
        fx = _Fixture()

        fx.patch_template(TENANT_A, WATERING, {"enabled": False})
        second = fx.patch_template(TENANT_A, WATERING, {"days_offset": 11})

        assert second.status_code == 200, second.text
        assert second.json()["key"] != WATERING
        assert _activity(fx.plan_of(TENANT_A), "Giessen")["days_offset"] == 11
        assert fx.templates.docs[WATERING]["days_offset"] == 3
        assert len([doc for doc in fx.workflows.docs.values() if doc.get("tenant_key") == TENANT_A]) == 1


class TestDeletingAnActivityFromASharedPlan:
    """A delete forks like any other write, and removes the activity from the copy only."""

    def test_the_deleting_tenant_loses_the_activity(self):
        fx = _Fixture()

        resp = fx.delete_template(TENANT_A, PRUNING)

        assert resp.status_code == 204, resp.text
        assert [tt["name"] for tt in fx.plan_of(TENANT_A)["templates"]] == ["Giessen"]

    def test_tenant_b_still_sees_the_activity_tenant_a_deleted(self):
        fx = _Fixture()

        fx.delete_template(TENANT_A, PRUNING)

        assert len(fx.plan_of(TENANT_B)["templates"]) == 2
        assert fx.templates.docs[PRUNING]["workflow_template_key"] == SHARED_PLAN

    def test_deleting_the_same_activity_twice_is_not_found_the_second_time(self):
        """Once it is gone from the caller's own copy it is gone *for them*."""
        fx = _Fixture()

        fx.delete_template(TENANT_A, PRUNING)
        second = fx.delete_template(TENANT_A, PRUNING)

        assert second.status_code == 404, second.text
        assert second.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert fx.templates.docs[PRUNING]["workflow_template_key"] == SHARED_PLAN


class TestRegeneratingASharedPlan:
    """``force_regenerate`` is the loudest write of all and forks the same way."""

    @staticmethod
    def _fixture_with_a_stub_generator() -> _Fixture:
        """Generation itself (engine, phases, activities) is not what is under test here.

        ``generate_plan`` is stubbed down to the one property that is: it persists
        a workflow owned by whatever ``tenant_key`` it was handed. Everything
        around it — which existing plan is looked up, which one is deleted — is
        the real service.
        """
        fx = _Fixture()

        def _persist(species_key: str, tenant_key: str = "", **kwargs: Any) -> WorkflowTemplate:
            return fx.repo.create_workflow_template(
                WorkflowTemplate(
                    name="Tomate",
                    tenant_key=tenant_key,
                    auto_generated=True,
                    species_key=species_key,
                )
            )

        fx.plan_service.generate_plan = _persist  # type: ignore[method-assign]
        return fx

    def test_a_regenerate_does_not_replace_the_shared_template(self):
        fx = self._fixture_with_a_stub_generator()

        resp = fx.client(TENANT_A).post(
            f"/api/v1/t/{SLUG[TENANT_A]}/activity-plans/generate",
            json={"species_key": SPECIES, "force_regenerate": True},
        )

        assert resp.status_code == 200, resp.text
        assert SHARED_PLAN in fx.workflows.docs
        assert fx.workflows.docs[SHARED_PLAN] == _shared_workflow()
        assert fx.plan_of(TENANT_B)["workflow_template_key"] == SHARED_PLAN

    def test_a_regenerate_produces_a_plan_owned_by_the_caller(self):
        fx = self._fixture_with_a_stub_generator()

        resp = fx.client(TENANT_A).post(
            f"/api/v1/t/{SLUG[TENANT_A]}/activity-plans/generate",
            json={"species_key": SPECIES, "force_regenerate": True},
        )

        assert fx.workflows.docs[resp.json()["workflow_template_key"]]["tenant_key"] == TENANT_A
        assert resp.json()["is_shared_template"] is False

    def test_a_second_regenerate_replaces_the_callers_own_plan(self):
        fx = self._fixture_with_a_stub_generator()

        url = f"/api/v1/t/{SLUG[TENANT_A]}/activity-plans/generate"
        body = {"species_key": SPECIES, "force_regenerate": True}
        first = fx.client(TENANT_A).post(url, json=body).json()["workflow_template_key"]
        second = fx.client(TENANT_A).post(url, json=body).json()["workflow_template_key"]

        assert second != first
        assert first not in fx.workflows.docs
        assert SHARED_PLAN in fx.workflows.docs


class TestATenantWhoHasNeverEditedTheSharedPlan:
    """The #324 direction, which a strict tenant predicate would silently kill.

    Every generated plan in an existing installation is global, so ``tenant_key
    == caller`` matches nothing and refuses everybody — while passing every
    isolation assertion above. Both halves are asserted for the same reason PR
    #999 kept its four positives.
    """

    def test_the_shared_plan_is_readable(self):
        fx = _Fixture()

        plan = fx.plan_of(TENANT_B)

        assert plan["workflow_template_key"] == SHARED_PLAN
        assert len(plan["templates"]) == 2

    def test_the_shared_plan_is_still_readable_after_another_tenant_forked_it(self):
        fx = _Fixture()

        fx.patch_template(TENANT_A, WATERING, {"enabled": False})

        plan = fx.plan_of(TENANT_B)
        assert plan["workflow_template_key"] == SHARED_PLAN
        assert len(plan["templates"]) == 2

    def test_the_shared_plan_is_editable(self):
        fx = _Fixture()

        resp = fx.patch_template(TENANT_B, WATERING, {"days_offset": 5})

        assert resp.status_code == 200, resp.text
        assert resp.json()["days_offset"] == 5

    def test_the_shared_plan_is_deletable(self):
        fx = _Fixture()

        assert fx.delete_template(TENANT_B, WATERING).status_code == 204

    def test_two_tenants_forking_the_same_plan_get_one_copy_each(self):
        fx = _Fixture()

        fx.patch_template(TENANT_A, WATERING, {"days_offset": 9})
        fx.patch_template(TENANT_B, WATERING, {"days_offset": 21})

        assert _activity(fx.plan_of(TENANT_A), "Giessen")["days_offset"] == 9
        assert _activity(fx.plan_of(TENANT_B), "Giessen")["days_offset"] == 21
        assert fx.templates.docs[WATERING]["days_offset"] == 3
