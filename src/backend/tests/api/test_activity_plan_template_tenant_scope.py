"""The activity-plan task-template write routes, end to end (#992).

``PATCH``/``DELETE /activity-plans/templates/{key}`` used to be mounted globally
behind nothing but ``Depends(get_current_user)`` and edited the repository from
the API layer. The document key was the entire authorisation. Observed against
that code, every negative below was red, and in the way that matters — with a
``200``/``204`` and a written document, not an error of a different shape:

* foreign tenant, ``PATCH`` → ``200`` with the full edited body
  (``{"key":"tt-foreign", … "enabled":false …}``)
* foreign tenant, ``DELETE`` → ``204``, empty body
* system workflow, ``PATCH`` → ``200`` with ``{"key":"tt-sys", … "enabled":false …}``
* system workflow, ``DELETE`` → ``204``, empty body
* parentless template, ``PATCH`` → ``200`` with ``{"key":"tt-orphan", … "enabled":false …}``
* parentless template, ``DELETE`` → ``204``, empty body

The four positives in :class:`TestTheEditorItselfStillWorks` were green *then*
and are green *now*: that is the half #324 exists for. A tenant filter written
against the wrong anchor would pass all six negatives by refusing everybody, and
an activity plan is precisely the case that would expose it — every plan
``ActivityPlanService`` generates is global (``tenant_key == ""``), so a strict
``tenant_key == caller`` predicate matches nothing at all.

**Two of those positives changed for #1003, knowingly.** They were written to
pin what #992 preserved — that a global non-system workflow is writable by
anyone who can reach it — so that whoever changed that behaviour had to change
them on purpose. #1003 did: the write now forks into a private copy instead of
landing on the shared row. Both still assert what they were there to assert (the
caller can act on a generated plan, so the fix did not pass by refusing
everybody) and each additionally asserts where the write went. The semantics
themselves live in ``tests/api/test_activity_plan_copy_on_write.py``.

Exercised through the real router, the real service and the real repository
against the replaying database double, so "wrote nothing" is asserted on the
collection rather than on a stub's call log.
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
from app.common.dependencies import get_task_service
from app.common.enums import TenantRole
from app.common.exceptions import KamerplanterError
from app.data_access.arango import collections as col
from app.data_access.arango.task_repository import ArangoTaskRepository
from app.domain.models.tenant_context import TenantContext
from app.domain.services.task_service import TaskService
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase, apply_predicates

TENANT_SLUG = "anna"
TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_WORKFLOW = "wf-a1"
FOREIGN_WORKFLOW = "wf-b1"
SYSTEM_WORKFLOW = "wf-sys"
GLOBAL_PLAN_WORKFLOW = "wf-plan"

WORKFLOWS: dict[str, dict[str, Any]] = {
    OWN_WORKFLOW: {
        "_key": OWN_WORKFLOW,
        "_id": f"{col.WORKFLOW_TEMPLATES}/{OWN_WORKFLOW}",
        "tenant_key": TENANT_KEY,
        "name": "Eigener Workflow",
    },
    FOREIGN_WORKFLOW: {
        "_key": FOREIGN_WORKFLOW,
        "_id": f"{col.WORKFLOW_TEMPLATES}/{FOREIGN_WORKFLOW}",
        "tenant_key": FOREIGN_TENANT_KEY,
        "name": "Fremder Workflow",
    },
    SYSTEM_WORKFLOW: {
        "_key": SYSTEM_WORKFLOW,
        "_id": f"{col.WORKFLOW_TEMPLATES}/{SYSTEM_WORKFLOW}",
        "tenant_key": "",
        "name": "Tomato Standard",
        "is_system": True,
    },
    # What ``ActivityPlanService.generate_plan`` actually persists: global
    # (``tenant_key == ""``) and *not* a system template. This row is the #324
    # counter-example in the fixture — the route must keep serving it. Since
    # #1003 a write on it forks rather than landing here; ``species_key`` is what
    # makes it a *generated plan* rather than an ownerless shared workflow, and
    # ``generate_plan`` stamps it on every plan it persists.
    GLOBAL_PLAN_WORKFLOW: {
        "_key": GLOBAL_PLAN_WORKFLOW,
        "_id": f"{col.WORKFLOW_TEMPLATES}/{GLOBAL_PLAN_WORKFLOW}",
        "tenant_key": "",
        "name": "Tomate",
        "auto_generated": True,
        "species_key": "solanum_lycopersicum",
    },
}

OWN_TEMPLATE = "tt-own"
FOREIGN_TEMPLATE = "tt-foreign"
SYSTEM_TEMPLATE = "tt-sys"
PLAN_TEMPLATE = "tt-plan"
ORPHAN_TEMPLATE = "tt-orphan"

TASK_TEMPLATES: dict[str, dict[str, Any]] = {
    key: {
        "_key": key,
        "_id": f"{col.TASK_TEMPLATES}/{key}",
        "name": "Giessen",
        "enabled": True,
        "days_offset": 3,
        **({"workflow_template_key": parent} if parent else {}),
    }
    for key, parent in (
        (OWN_TEMPLATE, OWN_WORKFLOW),
        (FOREIGN_TEMPLATE, FOREIGN_WORKFLOW),
        (SYSTEM_TEMPLATE, SYSTEM_WORKFLOW),
        (PLAN_TEMPLATE, GLOBAL_PLAN_WORKFLOW),
        (ORPHAN_TEMPLATE, None),
    )
}


def _error_handler(request: Request, exc: KamerplanterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message},
    )


class _RecordingCollection:
    """Write-recording collection double, so "wrote nothing" is assertable."""

    def __init__(self, name: str, docs: dict[str, dict[str, Any]] | None = None) -> None:
        self._name = name
        self._keys = (f"{name}-{n}" for n in itertools.count(1))
        self.docs = docs or {}
        self.inserted: list[dict[str, Any]] = []
        self.updated: list[dict[str, Any]] = []
        self.deleted: list[str] = []

    def get(self, key: str) -> dict[str, Any] | None:
        return self.docs.get(key)

    def insert(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        key = data.get("_key") or next(self._keys)
        stored = {**data, "_key": key, "_id": f"{self._name}/{key}"}
        self.docs[key] = stored
        self.inserted.append(stored)
        return {"new": stored}

    def update(self, data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        key = data["_key"]
        stored = {**self.docs.get(key, {}), **data}
        self.docs[key] = stored
        self.updated.append(stored)
        return {"new": stored}

    def delete(self, key: str) -> bool:
        self.docs.pop(key, None)
        self.deleted.append(key)
        return True


class _Fixture:
    def __init__(self, role: TenantRole = TenantRole.GROWER) -> None:
        # Deleting a task template is lead-only (REQ-049 §2.3); tests exercising
        # a delete pass ``role=TenantRole.LEAD`` so the request reaches the
        # tenant/system anchoring guard under test rather than the role gate.
        self._role = role
        self.templates = _RecordingCollection(
            col.TASK_TEMPLATES,
            {k: dict(v) for k, v in TASK_TEMPLATES.items()},
        )
        self.workflows = _RecordingCollection(col.WORKFLOW_TEMPLATES, {k: dict(v) for k, v in WORKFLOWS.items()})
        self.phases = _RecordingCollection(col.WORKFLOW_PHASES)

    @property
    def client(self) -> TestClient:
        aql = (
            # ``delete_task_template`` detaches its two edge kinds before
            # removing the document; neither query returns rows.
            ReplayingAql()
            .route(col.WF_CONTAINS, lambda query, bind_vars: [])
            .route(col.WF_HAS_PHASE, lambda query, bind_vars: [])
            .route(col.INSTANCE_OF, lambda query, bind_vars: [])
            # The generated-plan lookup behind copy-on-write (#1003). Filtered on
            # the predicates the query spells out, with the caller's own row
            # preferred over the shared one — see
            # ``tests/api/test_activity_plan_copy_on_write.py`` for the module
            # that exercises the union itself in both directions.
            .route(col.WORKFLOW_TEMPLATES, self._generated_plan_lookup)
            .route(col.WORKFLOW_PHASES, self._rows_of(lambda: self.phases))
            .route(col.TASK_TEMPLATES, self._rows_of(lambda: self.templates))
        )
        collections = {
            col.WORKFLOW_TEMPLATES: self.workflows,
            col.TASK_TEMPLATES: self.templates,
            col.WORKFLOW_PHASES: self.phases,
            col.WF_CONTAINS: _RecordingCollection(col.WF_CONTAINS),
            col.WF_HAS_PHASE: _RecordingCollection(col.WF_HAS_PHASE),
        }
        repo = ArangoTaskRepository(ReplayingDatabase(aql, collections))
        service = TaskService(repo, MagicMock(), MagicMock())

        app = FastAPI()
        app.include_router(activity_plans_tenant_router, prefix="/api/v1/t/{tenant_slug}")
        app.add_exception_handler(KamerplanterError, _error_handler)
        app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
            tenant_key=TENANT_KEY,
            tenant_slug=TENANT_SLUG,
            user_key="user-1",
            role=self._role,
        )
        app.dependency_overrides[get_task_service] = lambda: service
        return TestClient(app)

    def _generated_plan_lookup(self, query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
        rows = [
            doc
            for doc in self.workflows.docs.values()
            if doc.get("auto_generated") and doc.get("species_key") == bind_vars.get("species_key")
        ]
        tenant_key = bind_vars.get("tenant_key", "")
        rows = [doc for doc in rows if doc.get("tenant_key", "") in (tenant_key, "")]
        rows.sort(key=lambda doc: (0 if doc.get("tenant_key", "") == tenant_key else 1, doc["_key"]))
        return rows[:1]

    @staticmethod
    def _rows_of(collection: Any) -> Any:
        return lambda query, bind_vars: apply_predicates(list(collection().docs.values()), query, bind_vars)


def _url(path: str) -> str:
    return f"/api/v1/t/{TENANT_SLUG}/activity-plans{path}"


class TestAForeignTenantsTaskTemplate:
    """Direction 1: tenant B may not touch tenant A's template."""

    def test_patching_a_foreign_tenants_template_is_not_found(self):
        fx = _Fixture()

        resp = fx.client.patch(_url(f"/templates/{FOREIGN_TEMPLATE}"), json={"enabled": False})

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert fx.templates.updated == []

    def test_deleting_a_foreign_tenants_template_is_not_found(self):
        fx = _Fixture(role=TenantRole.LEAD)

        resp = fx.client.delete(_url(f"/templates/{FOREIGN_TEMPLATE}"))

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert fx.templates.deleted == []

    def test_the_refusal_is_the_same_answer_an_unknown_key_gets(self):
        """No cross-tenant existence oracle: "foreign" and "absent" are one answer."""
        fx = _Fixture()

        foreign = fx.client.patch(_url(f"/templates/{FOREIGN_TEMPLATE}"), json={"enabled": False})
        unknown = fx.client.patch(_url("/templates/tt-does-not-exist"), json={"enabled": False})

        assert foreign.status_code == unknown.status_code == 404
        assert foreign.json()["error_code"] == unknown.json()["error_code"] == "ENTITY_NOT_FOUND"


class TestASystemWorkflowsTaskTemplate:
    """Direction 3: shared seed data refuses the write but stays visible."""

    def test_patching_a_system_workflows_template_is_refused(self):
        fx = _Fixture()

        resp = fx.client.patch(_url(f"/templates/{SYSTEM_TEMPLATE}"), json={"enabled": False})

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert fx.templates.updated == []

    def test_deleting_a_system_workflows_template_is_refused(self):
        """A delete here would remove the template for every tenant."""
        fx = _Fixture(role=TenantRole.LEAD)

        resp = fx.client.delete(_url(f"/templates/{SYSTEM_TEMPLATE}"))

        assert resp.status_code == 422, resp.text
        assert resp.json()["error_code"] == "VALIDATION_ERROR"
        assert fx.templates.deleted == []

    def test_the_two_refusals_stay_distinct(self):
        """422 "read yes, write no" for system data, 404 "not yours" for a foreign tenant."""
        fx = _Fixture()

        system = fx.client.patch(_url(f"/templates/{SYSTEM_TEMPLATE}"), json={"enabled": False})
        foreign = fx.client.patch(_url(f"/templates/{FOREIGN_TEMPLATE}"), json={"enabled": False})

        assert system.status_code == 422
        assert foreign.status_code == 404


class TestATemplateWithNoParentWorkflowIsRefused:
    """The decision taken for the parentless case, stated in the class name.

    ``ActivityPlanService.generate_plan`` assigns ``workflow_template_key`` to
    every template it persists, so a parentless one cannot arise from the
    legitimate flow. It also has no owner — and on a write route that is the one
    case where "no anchor, so no refusal" means "editable and deletable by
    anyone". So it is refused, with the same 404 a foreign parent gets, because
    "who owns this" genuinely has no answer and the alternative would confirm
    that the key exists.
    """

    def test_patching_a_parentless_template_is_not_found(self):
        fx = _Fixture()

        resp = fx.client.patch(_url(f"/templates/{ORPHAN_TEMPLATE}"), json={"enabled": False})

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert fx.templates.updated == []

    def test_deleting_a_parentless_template_is_not_found(self):
        fx = _Fixture(role=TenantRole.LEAD)

        resp = fx.client.delete(_url(f"/templates/{ORPHAN_TEMPLATE}"))

        assert resp.status_code == 404, resp.text
        assert resp.json()["error_code"] == "ENTITY_NOT_FOUND"
        assert fx.templates.deleted == []


class TestTheEditorItselfStillWorks:
    """Direction 2 (#324): the fix must not pass its negatives by refusing everyone."""

    def test_the_callers_own_template_is_still_editable(self):
        fx = _Fixture()

        resp = fx.client.patch(_url(f"/templates/{OWN_TEMPLATE}"), json={"enabled": False})

        assert resp.status_code == 200, resp.text
        assert resp.json()["enabled"] is False
        assert [doc["_key"] for doc in fx.templates.updated] == [OWN_TEMPLATE]

    def test_the_callers_own_template_is_still_deletable(self):
        fx = _Fixture(role=TenantRole.LEAD)

        resp = fx.client.delete(_url(f"/templates/{OWN_TEMPLATE}"))

        assert resp.status_code == 204, resp.text
        assert fx.templates.deleted == [OWN_TEMPLATE]

    def test_a_globally_generated_activity_plans_template_is_still_editable(self):
        """Every plan ``ActivityPlanService`` generates is global — the whole feature rides on this.

        **Changed for #1003, on purpose.** This test and its ``…_deletable``
        sibling were written to pin the behaviour #992 preserved: a global,
        non-system workflow is writable by anyone who can reach it. #1003 decided
        that is wrong — it is one object shared by every tenant growing that
        species — and replaced it with copy-on-write.

        What the two of them covered is unchanged and still asserted here: a
        tenant can act on a generated plan, the route does not refuse them, and
        the #324 direction stays honest. What is *added* is where the write
        landed. It no longer lands on the shared row: the shared document is
        asserted untouched, which is precisely the assertion that could not be
        made before. ``tests/api/test_activity_plan_copy_on_write.py`` carries
        the rest of the semantics; this module keeps only the part that belongs
        to the route's own contract.
        """
        fx = _Fixture()

        resp = fx.client.patch(_url(f"/templates/{PLAN_TEMPLATE}"), json={"days_offset": 9})

        assert resp.status_code == 200, resp.text
        assert resp.json()["days_offset"] == 9
        # The edit is real, and it is *not* on the shared template.
        assert resp.json()["key"] != PLAN_TEMPLATE
        assert PLAN_TEMPLATE not in [doc["_key"] for doc in fx.templates.updated]
        assert fx.templates.docs[PLAN_TEMPLATE]["days_offset"] == 3

    def test_a_globally_generated_activity_plans_template_is_still_deletable(self):
        """Copy-on-write for the delete verb too (#1003): the caller's copy loses it, nobody else does.

        Same knowing replacement as the sibling above. The original asserted
        ``fx.templates.deleted == [PLAN_TEMPLATE]`` — the shared row was removed
        for every tenant. That is now the failure, not the contract: the delete
        still succeeds (204, unchanged), but it removes the activity from the
        private copy the write materialised.
        """
        fx = _Fixture(role=TenantRole.LEAD)

        resp = fx.client.delete(_url(f"/templates/{PLAN_TEMPLATE}"))

        assert resp.status_code == 204, resp.text
        assert fx.templates.deleted != []
        assert PLAN_TEMPLATE not in fx.templates.deleted
        assert PLAN_TEMPLATE in fx.templates.docs

    def test_the_three_editable_fields_all_still_arrive(self):
        """The service filters through its own allow-list; none of the editor's fields may be dropped."""
        fx = _Fixture()

        resp = fx.client.patch(
            _url(f"/templates/{OWN_TEMPLATE}"),
            json={"enabled": False, "days_offset": 12, "trigger_phase": "flowering"},
        )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert (body["enabled"], body["days_offset"], body["trigger_phase"]) == (False, 12, "flowering")


class TestTheUnguardedGlobalRoutesAreGone:
    """The old paths must not survive alongside the guarded ones."""

    def test_the_global_activity_plans_router_module_is_removed(self):
        """Nothing was left on it once ``/apply`` moved for #1000, so it is gone.

        Every write on this feature is tenant-scoped now: the template writes
        (#992), generation (#1003) and finally ``/apply`` (#1000).
        """
        import importlib

        try:
            importlib.import_module("app.api.v1.activity_plans.router")
        except ModuleNotFoundError:
            return
        raise AssertionError("app.api.v1.activity_plans.router should have been removed")

    def test_all_write_routes_live_on_the_tenant_scoped_router(self):
        """``/generate`` (#1003) and ``/apply`` (#1000) both need the caller's tenant.

        ``/generate`` because which plan a caller is shown depends on whether
        their tenant has forked it, and ``/apply`` because the created tasks are
        stamped with the caller's tenant — which used to come from the request
        body, #1000's defect.
        """
        from app.api.v1.activity_plans.tenant_router import router as tenant_router

        tenant_paths = {(route.path, method) for route in tenant_router.routes for method in route.methods}

        assert ("/activity-plans/generate", "POST") in tenant_paths
        assert ("/activity-plans/apply", "POST") in tenant_paths
        assert ("/activity-plans/templates/{key}", "PATCH") in tenant_paths
        assert ("/activity-plans/templates/{key}", "DELETE") in tenant_paths
