"""REQ-053 WP 9.9 (#2749) - the bed-template exchange routes through the deployed app.

Rows: GP-API-070 (export one template as a file), GP-API-071 (import a file, dry run first), GP-FR-173.
Criteria: GP-ACC-062 (the file and the roundtrip), GP-ACC-063 (413 / 422 / 409, keys of the file ignored, a dry run
writes nothing).

``app.main`` with the real ``BedTemplateService``, the real tenant gate, the real body limit and the in-memory
double of ``tests/support``. The integration tier (``tests/integration/test_garden_plan_tenant_isolation.py``) runs
the roundtrip against ArangoDB; this tier shows the wire: status codes, the published codes, the role gate.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user, get_is_platform_admin
from app.common.dependencies import get_bed_template_service, get_tenant_service
from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.config.settings import settings
from app.domain.models.bed_template import MAX_TEMPLATES_PER_TENANT, BedTemplate, DefaultLayout, SoilProfileDefaults
from app.domain.models.bed_template_exchange import MAX_FILE_BYTES
from app.domain.models.user import User
from app.domain.services.bed_template_service import BedTemplateService
from tests.support.bed_template_fakes import FakeTemplates
from tests.support.garden_plan_fakes import OTHER_TENANT, TENANT

_BASE = "/api/v1/t/own"
_IMPORT = f"{_BASE}/bed-templates/import"
_POLYGON = {"kind": "polygon", "points": [[0, 0], [1.5, 0], [1.5, 0.8], [0.4, 1.2]], "rotation_deg": 15}
#: The strings the owner's template carries that no file may contain (GP-ACC-062 negative search).
_FORBIDDEN_IN_FILE = ("tenant_key", "created_by", "note", TENANT, "u_author", "task_water", '"_key"', '"key"')


class _Tenants:
    role = TenantRole.GROWER

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        keys = {"own": TENANT, "other": OTHER_TENANT}
        if slug not in keys:
            raise NotFoundError("Tenant", slug)
        return SimpleNamespace(key=keys[slug], slug=slug, is_active=True)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace:
        return SimpleNamespace(role=type(self).role, admin_scopes=[], is_active=True)

    def get_personal_tenant(self, user_key: str) -> None:
        return None


@pytest.fixture
def templates() -> FakeTemplates:
    fake = FakeTemplates()
    fake.task_templates["task_water"] = TENANT
    fake.add(
        BedTemplate(
            _key="own",
            tenant_key=TENANT,
            created_by="u_author",
            name="Herb spiral",
            location_type_key="raised_bed",
            default_geometry=_POLYGON,
            height_m=0.6,
            default_layout=DefaultLayout(row_spacing_cm=25, spacing_cm=20),
            soil_profile_defaults=SoilProfileDefaults(growing_medium_kind="raised_bed_mix", drainage="good"),
            recurring_task_templates=["task_water"],
        )
    )
    fake.add(
        BedTemplate(
            _key="sys_bed",
            tenant_key=None,
            name="System bed",
            location_type_key="bed",
            default_geometry={"kind": "rect", "origin": [0, 0], "width_m": 2, "length_m": 1, "rotation_deg": 0},
        )
    )
    fake.add(
        BedTemplate(
            _key="theirs",
            tenant_key=OTHER_TENANT,
            name="Their bed",
            location_type_key="bed",
            default_geometry={"kind": "circle", "origin": [0, 0], "radius_m": 0.4},
        )
    )
    return fake


@pytest.fixture
def client(templates: FakeTemplates) -> Iterator[Callable[..., TestClient]]:
    from app.main import app

    service = BedTemplateService(templates)

    def build(role: TenantRole = TenantRole.GROWER) -> TestClient:
        _Tenants.role = role
        return TestClient(app)

    app.dependency_overrides[get_current_user] = lambda: User(
        _key="u_sabine", email="s@example.org", display_name="Sabine"
    )
    app.dependency_overrides[get_tenant_service] = _Tenants
    app.dependency_overrides[get_is_platform_admin] = lambda: False
    app.dependency_overrides[get_bed_template_service] = lambda: service
    try:
        yield build
    finally:
        _Tenants.role = TenantRole.GROWER
        app.dependency_overrides.clear()


def _export(client: TestClient, key: str = "own") -> dict[str, Any]:
    response = client.get(f"{_BASE}/bed-templates/{key}/export")
    assert response.status_code == 200, response.text
    return response.json()


def _import(client: TestClient, document: Any, **params: Any) -> Any:
    content = document if isinstance(document, bytes) else json.dumps(document).encode()
    return client.post(_IMPORT, content=content, params=params, headers={"content-type": "application/json"})


def _own_writes(templates: FakeTemplates) -> list[str]:
    return [write for write in templates.writes if write.startswith("create:")]


class TestTheExport:
    def test_the_file_carries_the_shape_and_nothing_of_the_owner(self, client) -> None:
        """GP-ACC-062: ``schema_version``, geometry, standard size, planting grid - and none of the owner's data."""
        response = client(TenantRole.VIEWER).get(f"{_BASE}/bed-templates/own/export")

        assert response.status_code == 200, response.text
        assert response.headers["content-disposition"] == 'attachment; filename="bed-template-own.json"'
        document = response.json()
        assert document == {
            "format": "kamerplanter.bed_template",
            "schema_version": "1",
            "name": "Herb spiral",
            "location_type_key": "raised_bed",
            "default_geometry": _POLYGON,
            "height_m": 0.6,
            "default_layout": {"row_spacing_cm": 25.0, "spacing_cm": 20.0},
            "soil_profile_defaults": {
                "growing_medium_kind": "raised_bed_mix",
                "soil_texture": "unknown",
                "drainage": "good",
                "site_water_regime": "unknown",
                "conditions": [],
            },
        }
        # Negative search over the raw bytes, not over a parsed subset of them.
        assert [needle for needle in _FORBIDDEN_IN_FILE if needle in response.text] == []

    def test_a_system_template_can_be_exported(self, client) -> None:
        assert _export(client(TenantRole.VIEWER), "sys_bed")["name"] == "System bed"

    @pytest.mark.parametrize("key", ["theirs", "absent"])
    def test_a_foreign_or_absent_template_is_a_404(self, client, key: str) -> None:
        response = client(TenantRole.LEAD).get(f"{_BASE}/bed-templates/{key}/export")

        assert response.status_code == 404, response.text
        assert "Their bed" not in response.text and OTHER_TENANT not in response.text


class TestTheImport:
    def test_the_roundtrip_gives_the_same_template_under_a_free_name(self, client, templates: FakeTemplates) -> None:
        """GP-ACC-062: export -> import is the same template (the name had to change: the original is still there)."""
        exported = _export(client())

        checked = _import(client(), exported, name="Herb spiral copy")
        assert checked.status_code == 200, checked.text
        assert checked.json()["dry_run"] is True and checked.json()["created_key"] is None
        assert _own_writes(templates) == []

        applied = _import(client(), exported, name="Herb spiral copy", dry_run="false")
        assert applied.status_code == 200, applied.text
        key = applied.json()["created_key"]
        stored = templates.templates[key]
        assert (stored.tenant_key, stored.created_by, stored.recurring_task_templates) == (TENANT, "u_sabine", [])
        assert _export(client(), key) == {**exported, "name": "Herb spiral copy"}

    def test_a_name_in_use_is_409_with_a_free_name_proposed(self, client, templates: FakeTemplates) -> None:
        """GP-ACC-063: the original still exists; any case of its name collides; the proposal is free."""
        document = {**_export(client()), "name": "HERB SPIRAL"}

        for dry_run in ("true", "false"):
            response = _import(client(), document, dry_run=dry_run)
            assert response.status_code == 409, response.text
            detail = response.json()["details"][0]
            assert (detail["code"], detail["suggested_name"]) == ("bed_template.name_taken", "HERB SPIRAL (2)")
        assert _own_writes(templates) == []

    def test_the_proposal_skips_numbers_in_use_and_does_not_stack_them(self, client, templates) -> None:
        templates.add(BedTemplate(_key="n2", tenant_key=TENANT, name="Herb spiral (2)", **_shape()))

        response = _import(client(), {**_export(client()), "name": "Herb spiral (2)"})

        assert response.status_code == 409, response.text
        assert response.json()["details"][0]["suggested_name"] == "Herb spiral (3)"

    def test_a_system_templates_name_collides_too(self, client) -> None:
        response = _import(client(), _export(client(), "sys_bed"))

        assert response.status_code == 409 and response.json()["details"][0]["suggested_name"] == "System bed (2)"

    def test_another_tenants_name_does_not_collide(self, client, templates: FakeTemplates) -> None:
        response = _import(client(), {**_export(client()), "name": "Their bed"}, dry_run="false")

        assert response.status_code == 200, response.text
        assert templates.templates[response.json()["created_key"]].tenant_key == TENANT

    def test_keys_of_the_file_are_ignored_and_reported(self, client, templates: FakeTemplates) -> None:
        """GP-ACC-063: a file that names an owner, an author, a key and task templates stores none of them."""
        document = {
            **_export(client()),
            "name": "Imported",
            "_key": "own",
            "key": "theirs",
            "tenant_key": OTHER_TENANT,
            "created_by": "u_intruder",
            "recurring_task_templates": ["task_water"],
            "notes": "Ask Bob",
            "x-anything": "<script>",
        }

        response = _import(client(), document, dry_run="false")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["dropped_fields"] == [
            "_key",
            "created_by",
            "key",
            "notes",
            "recurring_task_templates",
            "tenant_key",
        ]
        assert body["unknown_fields_ignored"] == 1 and "<script>" not in response.text
        stored = templates.templates[body["created_key"]]
        assert body["created_key"] not in ("own", "theirs")
        assert (stored.tenant_key, stored.created_by, stored.recurring_task_templates) == (TENANT, "u_sabine", [])
        assert templates.templates["theirs"].name == "Their bed" and templates.templates["own"].name == "Herb spiral"

    def test_a_file_above_256_kb_is_413(self, client, templates: FakeTemplates) -> None:
        padding = "x" * (MAX_FILE_BYTES + 1)
        response = _import(client(), {**_export(client()), "name": "Big", "padding": padding})

        assert response.status_code == 413, response.text
        assert response.json()["error_code"] == "REQUEST_BODY_TOO_LARGE" and "256 KB" in response.json()["message"]
        assert _own_writes(templates) == []

    def test_a_file_of_exactly_256_kb_is_read(self, client) -> None:
        document = {**_export(client()), "name": "Edge", "padding": ""}
        size = len(json.dumps(document).encode())
        document["padding"] = "x" * (MAX_FILE_BYTES - size)
        assert len(json.dumps(document).encode()) == MAX_FILE_BYTES

        assert _import(client(), document).status_code == 200

    @pytest.mark.parametrize(
        ("change", "code"),
        [
            ({"schema_version": "0"}, "bed_template.schema_version_unsupported"),
            ({"schema_version": "2"}, "bed_template.schema_version_unsupported"),
            ({"schema_version": 1}, "bed_template.schema_version_unsupported"),
            ({"schema_version": None}, "bed_template.schema_version_unsupported"),
            ({"format": "kamerplanter.garden_plan"}, "bed_template.import_invalid"),
            ({"format": None}, "bed_template.import_invalid"),
            ({"height_m": 3}, "bed_template.import_invalid"),
            ({"default_layout": {"spacing_cm": 20, "rows": 3}}, "bed_template.import_invalid"),
            ({"default_geometry": {"kind": "point", "origin": [0, 0]}}, "bed_template.import_invalid"),
            ({"soil_profile_defaults": {"substrate_key": "sub_1"}}, "bed_template.import_invalid"),
            ({"name": "   "}, "bed_template.import_invalid"),
        ],
        ids=[
            "older version",
            "newer version",
            "version as number",
            "no version",
            "plan backup",
            "no format",
            "height",
            "unknown grid field",
            "point",
            "soil reference",
            "blank name",
        ],
    )
    def test_the_file_is_validated(self, client, templates: FakeTemplates, change: dict, code: str) -> None:
        """GP-ACC-063: a schema error or a version older than the predecessor is a 422."""
        document = {key: value for key, value in {**_export(client()), "name": "New", **change}.items()}
        if change.get("format", "") is None:
            document.pop("format")
        if "schema_version" in change and change["schema_version"] is None:
            document.pop("schema_version")

        response = _import(client(), document, dry_run="false")

        assert response.status_code == 422, response.text
        assert response.json()["details"][0]["code"] == code
        assert _own_writes(templates) == []

    @pytest.mark.parametrize(
        "content",
        [b"not json", b"[1, 2]", b'"text"', b"\xff\xfe", ("[" * 11 + "]" * 11).encode(), b"[" * 100_000],
        ids=["not json", "array", "string", "not utf-8", "11 levels", "100k levels"],
    )
    def test_a_file_that_is_no_template_object_is_422(self, client, content: bytes) -> None:
        response = _import(client(), content)

        assert response.status_code == 422, response.text
        assert response.json()["details"][0]["code"] in {"bed_template.import_invalid", "bed_template.import_too_deep"}

    def test_a_nesting_past_ten_levels_inside_an_ignored_field_is_422(self, client) -> None:
        deep: Any = 1
        for _ in range(10):
            deep = [deep]
        response = _import(client(), {**_export(client()), "name": "Deep", "extra": deep})

        assert response.status_code == 422, response.text
        assert response.json()["details"][0]["code"] == "bed_template.import_too_deep"

    def test_a_bed_type_this_installation_lacks_is_reference_not_found(self, client) -> None:
        response = _import(client(), {**_export(client()), "name": "New", "location_type_key": "moon_bed"})

        assert response.status_code == 422, response.text
        assert response.json()["details"][0]["code"] == "reference.not_found"

    def test_the_quota_holds_on_the_dry_run_too(self, client, templates: FakeTemplates) -> None:
        for index in range(MAX_TEMPLATES_PER_TENANT - 1):
            templates.add(BedTemplate(_key=f"q{index}", tenant_key=TENANT, name=f"Q{index}", **_shape()))

        response = _import(client(), {**_export(client()), "name": "One too many"})

        assert response.status_code == 422, response.text
        assert response.json()["details"][0]["code"] == "bed_template.quota_exceeded"

    def test_a_viewer_imports_nothing(self, client, templates: FakeTemplates) -> None:
        document = {**_export(client()), "name": "New"}  # built first: ``client(role)`` sets the role it serves

        response = _import(client(TenantRole.VIEWER), document, dry_run="false")

        assert response.status_code == 403, response.text
        assert _own_writes(templates) == []


class TestTheHardening:
    def test_a_key_of_the_file_is_never_echoed_in_a_422(self, client) -> None:
        """SEC-002: the path of a finding names schema fields and indices only, never a key the file chose."""
        document = {
            **_export(client()),
            "name": "New",
            "default_layout": {"spacing_cm": 20, "exfil_k3y_one": 1},
            "soil_profile_defaults": {"exfil_k3y_two": True},
        }

        response = _import(client(), document)

        assert response.status_code == 422, response.text
        assert "exfil_k3y" not in response.text
        fields = sorted(detail["field"] for detail in response.json()["details"])
        assert fields == ["default_layout.<unknown>", "soil_profile_defaults.<unknown>"]

    def test_an_index_and_a_schema_field_pass(self, client) -> None:
        document = {**_export(client()), "name": "New", "default_geometry": {**_POLYGON, "points": [[0, 0], [1, "x"]]}}

        response = _import(client(), document)

        assert response.status_code == 422, response.text
        assert any(detail["field"].startswith("default_geometry.") for detail in response.json()["details"])

    @pytest.mark.parametrize(
        "name", ["Beet\u202e1", "Beet\u200b", "Beet\x07", "Beet\u2066x"], ids=["bidi", "zwsp", "bell", "isolate"]
    )
    def test_a_name_with_a_control_or_format_character_is_refused(self, client, templates, name: str) -> None:
        """SEC-003: Cc and Cf characters are refused in the name of an imported file - also as the ``name`` override."""
        in_file = _import(client(), {**_export(client()), "name": name}, dry_run="false")
        as_override = _import(client(), _export(client()), name=name, dry_run="false")

        assert (in_file.status_code, as_override.status_code) == (422, 422), in_file.text
        assert _own_writes(templates) == []

    def test_the_name_is_stored_in_nfc(self, client, templates: FakeTemplates) -> None:
        decomposed = "Kra\u0308uterbeet"

        response = _import(client(), {**_export(client()), "name": decomposed}, dry_run="false")

        assert response.status_code == 200, response.text
        assert templates.templates[response.json()["created_key"]].name == "Kr\u00e4uterbeet"

    def test_the_import_is_budgeted_per_tenant(self, client) -> None:
        """SEC-001: the template import has its own per-tenant budget (``rate_limit_bed_template_import``)."""
        budget = int(settings.rate_limit_bed_template_import.split("/")[0])
        document = {**_export(client()), "name": "New"}

        statuses = [_import(client(), document).status_code for _ in range(budget + 1)]

        assert statuses == [200] * budget + [429]


def _shape() -> dict[str, Any]:
    return {
        "location_type_key": "bed",
        "default_geometry": {"kind": "rect", "origin": [0, 0], "width_m": 1, "length_m": 1, "rotation_deg": 0},
    }
