"""Tests for the tenant-body gate (``scripts/check_tenant_body_field.py``).

**What is under test.** The detection logic, driven against *constructed* API
trees written into ``tmp_path`` — never against the real ``src/backend/app/api``.
A test asserting "the tree has 296 request schemas" would go red on the next
legitimate schema and teach nobody anything; what is worth locking down is what
the check does with a given input.

**The deliberately-broken schema.** :class:`TestItCanFail` writes a request
schema carrying ``tenant_key`` and a router that binds it as a body — the shape
of #1000 — and asserts the check goes red and names it. A gate nobody has
watched fail is a gate nobody knows works.

**The other half is what it refuses to report.** :class:`TestResponsesAreNotBodies`
pins that a response schema keeps its ``tenant_key`` unremarked. Fourteen of them
ship today; a check that flagged those would be switched off within a week, and
then it would guard nothing at all.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package, so it is loaded by path.

Traces to the 2026-08-08 issue-pattern audit, measure P1.2, and to issue #1000
(no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import json
import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_tenant_body_field")


# ── A miniature API tree ─────────────────────────────────────────────────────

#: A router binding one request schema as a body — this codebase's create handler.
_CREATE_ROUTER = """
from fastapi import APIRouter

from app.api.v1.watering_logs.schemas import WateringLogCreate

router = APIRouter()


@router.post("/watering-logs")
def create_log(body: WateringLogCreate):
    return body
"""


@pytest.fixture
def build_tree(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper that writes a miniature ``app/api`` package into ``tmp_path``.

    The shape mirrors the real tree — ``app/api/v1/<area>/{schemas,router}.py``
    — because the check derives dotted module names by walking up while
    ``__init__.py`` exists and resolves imports against those names. The scan
    root it returns is ``app/api``, which is what the check is pointed at.
    """

    def _write(path: Path, source: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        for parent in path.parents:
            if parent == tmp_path:
                break
            (parent / "__init__.py").touch()
        path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")

    def _build(*, schemas: str, router: str = _CREATE_ROUTER, area: str = "watering_logs") -> Path:
        app = tmp_path / "app"
        _write(app / "api" / "v1" / area / "schemas.py", schemas)
        _write(app / "api" / "v1" / area / "router.py", router)
        return app / "api"

    return _build


def _fields(scan_root: Path) -> list[tuple[str, str]]:
    """``(class, field)`` for every *counted* finding, sorted."""
    _tree, _requests, findings = checker.collect(scan_root)
    return sorted((finding.class_name, finding.field_name) for finding in findings if not finding.justified)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestItCanFail:
    """The deliberately-broken schema, and the check going red on it (#1000)."""

    def test_a_request_schema_carrying_tenant_key_is_caught(self, build_tree: Callable[..., Path]) -> None:
        """The #1000 shape: the caller names the tenant its write lands in."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                tenant_key: str = ""
                volume_liters: float = 1.0
            """
        )
        assert _fields(scan_root) == [("WateringLogCreate", "tenant_key")]

    def test_the_broken_schema_makes_the_process_exit_non_zero(
        self, build_tree: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Detection is worth nothing if the gate still reports success."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                tenant_key: str = ""
            """
        )
        assert checker.main(["--scan-root", str(scan_root)]) == checker.EXIT_DEFECTS
        assert "WateringLogCreate.tenant_key" in capsys.readouterr().out

    def test_the_failure_message_names_the_fix_and_the_hatch(
        self, build_tree: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Whoever hits this has just written a schema and does not know the rule.

        The message is most of the value: it has to say where the tenant comes
        from instead, and how to record a deliberate exception.
        """
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                tenant_key: str = ""
            """
        )
        checker.main(["--scan-root", str(scan_root)])
        out = capsys.readouterr().out
        assert "get_current_tenant" in out
        assert "REQ-024" in out
        assert checker.JUSTIFICATION_MARKER in out

    def test_tenant_slug_is_caught_too(self, build_tree: Callable[..., Path]) -> None:
        """The path segment's name is no safer in a body than the key is."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                tenant_slug: str = ""
            """
        )
        assert _fields(scan_root) == [("WateringLogCreate", "tenant_slug")]

    def test_the_same_schema_without_the_field_is_green(self, build_tree: Callable[..., Path]) -> None:
        """The fix the message asks for actually clears the check."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                volume_liters: float = 1.0
            """
        )
        assert _fields(scan_root) == []
        assert checker.main(["--scan-root", str(scan_root)]) == checker.EXIT_OK


class TestResponsesAreNotBodies:
    """What the check refuses to report, so it does not get switched off."""

    def test_a_response_schema_keeps_its_tenant_key(self, build_tree: Callable[..., Path]) -> None:
        """Telling a client which tenant a record belongs to is not the defect.

        Fourteen response schemas ship such a field today (``ActivityResponse``,
        ``ActuatorResponse``, ``NotificationResponse``, …). Flagging them would
        make the check noise.
        """
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                volume_liters: float = 1.0


            class WateringLogResponse(BaseModel):
                tenant_key: str
                volume_liters: float
            """
        )
        assert _fields(scan_root) == []

    def test_a_dependency_annotated_parameter_is_not_a_body(self, build_tree: Callable[..., Path]) -> None:
        """``Annotated[TenantContext, Depends(...)]`` is resolved server-side.

        Its ``tenant_key`` is the authenticated one — the very value the rule
        says to use — so reading the context model as request input would flag
        the correct implementation.
        """
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class TenantContext(BaseModel):
                tenant_key: str


            class WateringLogCreate(BaseModel):
                volume_liters: float = 1.0
            """,
            router="""
            from typing import Annotated

            from fastapi import APIRouter, Depends

            from app.api.v1.watering_logs.schemas import TenantContext, WateringLogCreate

            router = APIRouter()


            def get_current_tenant() -> TenantContext:
                return TenantContext(tenant_key="t1")


            @router.post("/watering-logs")
            def create_log(
                body: WateringLogCreate,
                ctx: Annotated[TenantContext, Depends(get_current_tenant)],
            ):
                return body, ctx
            """,
        )
        assert _fields(scan_root) == []

    def test_a_similarly_named_field_is_not_matched(self, build_tree: Callable[..., Path]) -> None:
        """``default_tenant_key`` on the OIDC provider config is a real setting.

        Widening the match to "any field mentioning a tenant" would flag it on
        the first run, which is why the match is exact.
        """
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                default_tenant_key: str | None = None
            """
        )
        assert _fields(scan_root) == []


class TestReach:
    """The three ways a field reaches the wire without being declared locally."""

    def test_an_inherited_field_is_compared_too(self, build_tree: Callable[..., Path]) -> None:
        """Pydantic inherits fields, so a base class is not a hiding place."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogBase(BaseModel):
                tenant_key: str = ""


            class WateringLogCreate(WateringLogBase):
                volume_liters: float = 1.0
            """
        )
        assert _fields(scan_root) == [("WateringLogBase", "tenant_key")]

    def test_a_nested_model_is_request_input_too(self, build_tree: Callable[..., Path]) -> None:
        """``list[EntryIn]`` inside a body arrives from the same caller."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class EntryIn(BaseModel):
                tenant_key: str = ""


            class WateringLogCreate(BaseModel):
                entries: list[EntryIn] = []
            """
        )
        assert _fields(scan_root) == [("EntryIn", "tenant_key")]

    def test_a_schema_no_router_binds_yet_is_still_covered(self, build_tree: Callable[..., Path]) -> None:
        """A ``…Request`` written before its endpoint must not be invisible.

        Binding alone would make the check pass on the commit that introduces
        the schema and fail on the one that wires it — the second author would
        be handed a finding they did not create.
        """
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                volume_liters: float = 1.0


            class ArchiveRunRequest(BaseModel):
                tenant_key: str = ""
            """
        )
        assert _fields(scan_root) == [("ArchiveRunRequest", "tenant_key")]


class TestJustification:
    """The per-site escape hatch, and why a bare marker is not one."""

    def test_a_reason_above_the_field_exempts_it(self, build_tree: Callable[..., Path]) -> None:
        """A site that genuinely needs the field says so, in place, with a reason."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                # tenant-body-ok: platform-admin endpoint, the tenant is the object of the call
                tenant_key: str = ""
            """
        )
        _tree, _requests, findings = checker.collect(scan_root)
        assert [finding.justified for finding in findings] == [True]
        assert _fields(scan_root) == []

    def test_a_reason_on_the_field_line_exempts_it(self, build_tree: Callable[..., Path]) -> None:
        """Trailing placement is accepted too — same rule as the UTC check's hatch."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                tenant_key: str = ""  # tenant-body-ok: verified against ctx before any write
            """
        )
        assert _fields(scan_root) == []

    def test_a_bare_marker_is_not_an_exemption(self, build_tree: Callable[..., Path]) -> None:
        """The point of the hatch is the reason, not the token.

        Without this the hatch is a silencer, and the gate measures diligence at
        typing rather than at thinking.
        """
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                tenant_key: str = ""  # tenant-body-ok:
            """
        )
        assert _fields(scan_root) == [("WateringLogCreate", "tenant_key")]

    def test_a_too_short_reason_is_not_an_exemption(self, build_tree: Callable[..., Path]) -> None:
        """``# tenant-body-ok: ok`` explains nothing a reviewer can argue with."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                tenant_key: str = ""  # tenant-body-ok: ok
            """
        )
        assert _fields(scan_root) == [("WateringLogCreate", "tenant_key")]

    def test_the_report_names_every_justified_site(
        self, build_tree: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An exemption stays visible; a silent one is indistinguishable from a fix."""
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                # tenant-body-ok: platform-admin endpoint, the tenant is the object of the call
                tenant_key: str = ""
            """
        )
        assert checker.main(["--scan-root", str(scan_root)]) == checker.EXIT_OK
        out = capsys.readouterr().out
        assert "justified" in out
        assert "the tenant is the object of the call" in out


class TestProcessContract:
    """Exit codes and the machine-readable output."""

    def test_json_reports_both_buckets(
        self, build_tree: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        scan_root = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                tenant_key: str = ""


            class ArchiveRunRequest(BaseModel):
                tenant_slug: str = ""  # tenant-body-ok: inert, the service never reads it
            """
        )
        assert checker.main(["--scan-root", str(scan_root), "--json"]) == checker.EXIT_DEFECTS
        payload = json.loads(capsys.readouterr().out)
        assert [entry["field"] for entry in payload["unjustified"]] == ["tenant_key"]
        assert [entry["field"] for entry in payload["justified"]] == ["tenant_slug"]

    def test_a_missing_root_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A check that cannot run must not report success — the #814 failure mode."""
        assert checker.main(["--scan-root", str(tmp_path / "nowhere")]) == checker.EXIT_USAGE
        assert "does not exist" in capsys.readouterr().err


class TestTheRealTree:
    """What the pre-commit hook asserts, asserted here too."""

    def test_no_unjustified_tenant_field_survives_in_the_api_layer(self) -> None:
        """Running it from pytest as well means a backend-only change goes red here.

        Zero unjustified, not zero findings: the two that exist carry a marker,
        and the point of a per-site hatch is that it stays visible.
        """
        assert checker.main([]) == checker.EXIT_OK
