"""Tests for the boundary-validation check (``scripts/check_boundary_validation.py``).

**What is under test.** The detection logic, driven against *constructed*
application trees written into ``tmp_path`` — never against the real
``src/backend/app``. A test asserting "the tree has 54 widened fields" would go
red on the next legitimate schema and teach nobody anything; what is worth
locking down is what the check does with a given input.

**The one exception** is :class:`TestTheRecordedCeilingIsHonest`, which runs the
check over the real tree exactly as the pre-commit hook does. It does not pin a
number — it pins that the *committed* ceiling is not below reality, which is the
only way the constant can quietly stop being a ceiling.

**The deliberately-broken endpoint.** :class:`TestItCanFail` writes a router that
splats a ``str``-typed request field into a domain model whose field is an enum —
the exact shape of #966 and #971 — and asserts the check goes red and names it. A
gate nobody has watched fail is a gate nobody knows works.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script itself lives outside the backend package, so it is loaded **by path** —
the same mechanism ``test_schema_example_ratchet.py`` uses.

Traces to issue #970 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

# ── Loading the script under test by path ────────────────────────────────────


def _find_repo_root(start: Path) -> Path | None:
    """Walk up from *start* to the checkout root, identified by its markers.

    A marker walk rather than ``parents[N]``: a hard-coded index silently breaks
    the moment the test file moves, which has bitten this repository before.

    Args:
        start: Any path inside the checkout.

    Returns:
        The directory holding both ``Taskfile.yaml`` and ``scripts/``, or None.
    """
    for candidate in (start, *start.parents):
        if (candidate / "Taskfile.yaml").is_file() and (candidate / "scripts").is_dir():
            return candidate
    return None


def _load_module_by_path(module_name: str, path: Path) -> ModuleType:
    """Execute the module at *path* under *module_name* and return it.

    Registration in ``sys.modules`` happens **before** ``exec_module`` because the
    script defines ``@dataclass`` types, and ``dataclass`` resolves its own module
    through ``sys.modules`` while the module body is still running.

    Args:
        module_name: Private name to register under.
        path: The ``.py`` file to execute.

    Returns:
        The executed module.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        pytest.skip(f"{path} cannot be loaded as a Python module", allow_module_level=True)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip(
        "checkout root not found (no ancestor holds both Taskfile.yaml and scripts/); "
        "scripts/check_boundary_validation.py is unreachable from here",
        allow_module_level=True,
    )

_SCRIPT = _REPO_ROOT / "scripts" / "check_boundary_validation.py"
if not _SCRIPT.is_file():  # pragma: no cover — only on a partial checkout
    pytest.skip(f"{_SCRIPT} does not exist", allow_module_level=True)

checker = _load_module_by_path("_boundary_validation_check_under_test", _SCRIPT)


# ── A miniature application tree ─────────────────────────────────────────────

#: The enum module every constructed tree gets, mirroring ``app/common/enums.py``
#: (BACKEND.md §11 keeps every enum in one file).
_ENUMS = """
from enum import StrEnum


class ApplicationMethod(StrEnum):
    DRENCH = "drench"
    FOLIAR = "foliar"


class WaterSource(StrEnum):
    TAP = "tap"
    RAIN = "rainwater"
"""

#: The domain model every constructed tree gets unless a test overrides it.
_DOMAIN = """
from pydantic import BaseModel, Field

from app.common.enums import ApplicationMethod, WaterSource


class WateringLog(BaseModel):
    application_method: ApplicationMethod = ApplicationMethod.DRENCH
    water_source: WaterSource | None = None
    volume_liters: float = Field(gt=0)
    note: str = ""
"""


@pytest.fixture
def build_tree(tmp_path: Path) -> Callable[..., Path]:
    """Return a helper that writes a miniature ``app/`` package into ``tmp_path``.

    The shape mirrors the real tree — ``app/common/enums.py``,
    ``app/domain/models/…``, ``app/api/v1/<area>/{schemas,tenant_router}.py`` —
    because the check derives dotted module names by walking up while
    ``__init__.py`` exists and resolves imports against those names.
    """

    def _write(path: Path, source: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        for parent in path.parents:
            if parent == tmp_path:
                break
            (parent / "__init__.py").touch()
        path.write_text(textwrap.dedent(source).lstrip(), encoding="utf-8")

    def _build(
        *,
        schemas: str,
        router: str,
        domain: str = _DOMAIN,
        enums: str = _ENUMS,
        area: str = "watering_logs",
    ) -> Path:
        app = tmp_path / "app"
        _write(app / "common" / "enums.py", enums)
        _write(app / "domain" / "models" / "watering_log.py", domain)
        _write(app / "api" / "v1" / area / "schemas.py", schemas)
        _write(app / "api" / "v1" / area / "tenant_router.py", router)
        return app

    return _build


#: A router that constructs the domain model straight from the request body —
#: this codebase's standard create handler, and the site the check reads.
_CREATE_ROUTER = """
from fastapi import APIRouter

from app.api.v1.watering_logs.schemas import WateringLogCreate
from app.domain.models.watering_log import WateringLog

router = APIRouter()


@router.post("/watering-logs")
def create_log(body: WateringLogCreate):
    log = WateringLog(**body.model_dump())
    return log
"""


def _findings(app_root: Path) -> list:
    """Return the check's findings for a constructed tree."""
    _tree, _pairings, findings = checker.collect(app_root)
    return findings


def _kinds(app_root: Path) -> list[tuple[str, str]]:
    """Return ``(kind, field)`` for every *counted* finding, sorted."""
    return sorted((finding.kind, finding.field_name) for finding in _findings(app_root) if not finding.justified)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestItCanFail:
    """The deliberately-broken endpoint, and the check going red on it (#970)."""

    def test_a_new_endpoint_that_widens_an_enum_to_str_is_caught(self, build_tree: Callable[..., Path]) -> None:
        """The #966/#971 shape: ``str`` at the boundary, an enum in the domain.

        The request schema accepts ``"anything"``; the domain model raises a
        plain ``pydantic.ValidationError``, which is not FastAPI's
        ``RequestValidationError`` and therefore answers 500.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel, Field


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"
                volume_liters: float = Field(gt=0)
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == [("enum_widened_to_str", "application_method")]

    def test_the_broken_endpoint_makes_the_process_exit_non_zero(
        self, build_tree: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Detection is worth nothing if the gate still reports success."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        exit_code = checker.main(["--app-root", str(app), "--baseline", "0"])
        assert exit_code == checker.EXIT_DEFECTS
        assert "FAILED" in capsys.readouterr().out

    def test_the_failure_message_names_the_models_the_field_and_the_fix(
        self, build_tree: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Whoever hits this has just written an endpoint and does not know the domain raises.

        The message is most of the value: it must name both models, the field,
        both annotations, and what to do — not merely that a counter moved.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        checker.main(["--app-root", str(app), "--baseline", "0"])
        out = capsys.readouterr().out
        assert "WateringLogCreate.application_method: str" in out
        assert "WateringLog.application_method: ApplicationMethod" in out
        assert "from app.common.enums import" in out
        assert "422" in out
        assert checker.JUSTIFICATION_MARKER in out

    def test_the_same_endpoint_typed_against_the_enum_is_green(self, build_tree: Callable[..., Path]) -> None:
        """The fix the message asks for actually clears the check."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel, Field

            from app.common.enums import ApplicationMethod


            class WateringLogCreate(BaseModel):
                application_method: ApplicationMethod = ApplicationMethod.DRENCH
                volume_liters: float = Field(gt=0)
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == []
        assert checker.main(["--app-root", str(app), "--baseline", "0"]) == checker.EXIT_OK


class TestEnumWidening:
    """Which request annotations count as widening a domain enum."""

    def test_a_nullable_str_over_a_nullable_enum_still_counts(self, build_tree: Callable[..., Path]) -> None:
        """``str | None`` accepts every non-null string; ``WaterSource | None`` does not.

        Nullability agrees here — the widening is in the non-null half, which is
        why the two shapes are judged independently.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                water_source: str | None = None
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == [("enum_widened_to_str", "water_source")]

    def test_a_literal_is_not_a_widening(self, build_tree: Callable[..., Path]) -> None:
        """``Literal["drench", "foliar"]`` bounds the value at the boundary already.

        It is not the enum, but it cannot let through a member the domain rejects,
        and this check reports only what is certainly a 500.
        """
        app = build_tree(
            schemas="""
            from typing import Literal

            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                application_method: Literal["drench", "foliar"] = "drench"
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == []

    def test_a_str_over_a_str_domain_field_is_not_a_widening(self, build_tree: Callable[..., Path]) -> None:
        """The two agree; a free-text field is free text on both sides."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                note: str = ""
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == []

    def test_a_field_the_domain_model_does_not_have_is_ignored(self, build_tree: Callable[..., Path]) -> None:
        """A request-only field never reaches the domain model, so it cannot raise there."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                confirm_token: str = ""
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == []

    def test_an_annotated_str_is_unwrapped(self, build_tree: Callable[..., Path]) -> None:
        """``Annotated[str, Field(...)]`` is a ``str``; the constraints are not enum membership."""
        app = build_tree(
            schemas="""
            from typing import Annotated

            from pydantic import BaseModel, Field


            class WateringLogCreate(BaseModel):
                application_method: Annotated[str, Field(max_length=20)] = "drench"
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == [("enum_widened_to_str", "application_method")]

    def test_an_inherited_request_field_is_compared_too(self, build_tree: Callable[..., Path]) -> None:
        """Pydantic inherits fields, so a base class is not a hiding place."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogBase(BaseModel):
                application_method: str = "drench"


            class WateringLogCreate(WateringLogBase):
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == [("enum_widened_to_str", "application_method")]


class TestNullableWidening:
    """The #966 shape: a forwarded ``None`` over a non-nullable domain field."""

    def test_a_nullable_request_field_over_a_non_nullable_domain_field_is_reported(
        self, build_tree: Callable[..., Path]
    ) -> None:
        """``model_dump()`` emits every key, so an omitted field arrives as ``None``.

        That ``None`` *disables* the domain default rather than falling back to
        it — the default applies to a missing key only.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                note: str | None = None
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == [("nullable_over_non_nullable", "note")]

    def test_it_fails_without_any_baseline(
        self, build_tree: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """This shape has no debt left, so it is a plain defect, not a ratchet.

        The ceiling argument is passed high on purpose: it must not shelter this
        shape, only the enum one.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                note: str | None = None
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert checker.main(["--app-root", str(app), "--baseline", "999"]) == checker.EXIT_DEFECTS
        assert "forward a null the domain model rejects" in capsys.readouterr().out

    def test_exclude_unset_drops_the_key_and_clears_the_finding(self, build_tree: Callable[..., Path]) -> None:
        """The fix #967 applied: the domain model's own default then decides."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                note: str | None = None
                volume_liters: float = 1.0
            """,
            router="""
            from fastapi import APIRouter

            from app.api.v1.watering_logs.schemas import WateringLogCreate
            from app.domain.models.watering_log import WateringLog

            router = APIRouter()


            @router.post("/watering-logs")
            def create_log(body: WateringLogCreate):
                return WateringLog(**body.model_dump(exclude_unset=True))
            """,
        )
        assert _kinds(app) == []

    def test_a_nullable_domain_field_is_no_finding(self, build_tree: Callable[..., Path]) -> None:
        """Both sides accept ``None``; nothing can raise."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                water_source: str | None = None
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
            domain="""
            from pydantic import BaseModel


            class WateringLog(BaseModel):
                water_source: str | None = None
                volume_liters: float = 1.0
            """,
        )
        assert _kinds(app) == []

    def test_a_before_validator_on_the_domain_model_makes_it_undecidable(self, build_tree: Callable[..., Path]) -> None:
        """A ``mode="before"`` validator may substitute a default for the ``None``.

        The check cannot read what it substitutes, so it stays quiet rather than
        guessing — precision over reach.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                note: str | None = None
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
            domain="""
            from pydantic import BaseModel, model_validator


            class WateringLog(BaseModel):
                note: str = ""
                volume_liters: float = 1.0

                @model_validator(mode="before")
                @classmethod
                def drop_nulls(cls, data):
                    return {key: value for key, value in data.items() if value is not None}
            """,
        )
        assert _kinds(app) == []


class TestPrecisionGuards:
    """What the check refuses to report, so it does not get switched off."""

    def test_a_field_validator_on_the_request_field_silences_that_field(self, build_tree: Callable[..., Path]) -> None:
        """A request schema validating the field itself may narrow it invisibly."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel, field_validator

            from app.common.enums import ApplicationMethod


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"
                note: str = ""
                volume_liters: float = 1.0

                @field_validator("application_method")
                @classmethod
                def known_method(cls, value: str) -> str:
                    return ApplicationMethod(value).value
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == []

    def test_a_field_validator_only_silences_the_fields_it_names(self, build_tree: Callable[..., Path]) -> None:
        """The guard is per field, not per model — a named field is not a blanket."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel, field_validator


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"
                water_source: str | None = None
                volume_liters: float = 1.0

                @field_validator("water_source")
                @classmethod
                def known_source(cls, value):
                    return value
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == [("enum_widened_to_str", "application_method")]

    def test_a_model_validator_silences_the_fields_its_body_mentions(self, build_tree: Callable[..., Path]) -> None:
        """It sees every field, and the check cannot tell which values it narrows."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel, model_validator


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"
                volume_liters: float = 1.0

                @model_validator(mode="after")
                def check_domain_rules(self):
                    if self.application_method == "fertigation":
                        raise ValueError("not supported")
                    return self
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == []

    def test_a_model_validator_about_other_fields_is_not_blanket_cover(self, build_tree: Callable[..., Path]) -> None:
        """Presence of *a* validator must not blind the check to the whole schema.

        This is the boundary-validation pattern #967 and #971 introduced: the
        request schema restates the domain's cross-field rules. Reading that as
        "this schema validates itself" would make every fixed endpoint a blind
        spot — ``WateringLogCreate`` is precisely such a schema, and its validator
        is about targets, not about the application method.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel, model_validator


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"
                volume_liters: float = 1.0
                plant_keys: list[str] = []
                slot_keys: list[str] = []

                @model_validator(mode="after")
                def check_domain_rules(self):
                    if not self.plant_keys and not self.slot_keys:
                        raise ValueError("at least one target is required")
                    return self
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == [("enum_widened_to_str", "application_method")]

    def test_a_response_construction_is_not_a_boundary(self, build_tree: Callable[..., Path]) -> None:
        """``Response(**domain.model_dump())`` runs outbound; no caller input is involved.

        The dumped name is a local, not an annotated endpoint parameter, which is
        exactly how the two directions are told apart.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogResponse(BaseModel):
                application_method: str
                volume_liters: float
            """,
            router="""
            from fastapi import APIRouter

            from app.api.v1.watering_logs.schemas import WateringLogResponse
            from app.domain.models.watering_log import WateringLog

            router = APIRouter()


            @router.get("/watering-logs/{key}")
            def get_log(key: str):
                log = WateringLog(volume_liters=1.0)
                return WateringLogResponse(**log.model_dump())
            """,
        )
        _tree, pairings, findings = checker.collect(app)
        assert pairings == []
        assert findings == []

    def test_an_unresolvable_domain_model_is_skipped_not_guessed(self, build_tree: Callable[..., Path]) -> None:
        """A callee that is not a class in the scanned tree yields no pairing."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"
            """,
            router="""
            from fastapi import APIRouter

            from app.api.v1.watering_logs.schemas import WateringLogCreate
            from some_third_party import ExternalLog

            router = APIRouter()


            @router.post("/watering-logs")
            def create_log(body: WateringLogCreate):
                return ExternalLog(**body.model_dump())
            """,
        )
        _tree, pairings, _findings = checker.collect(app)
        assert pairings == []


class TestSiblingUpdateSchemas:
    """The update path — where the value is persisted first and raises afterwards."""

    def test_an_update_schema_is_paired_through_its_create_sibling(self, build_tree: Callable[..., Path]) -> None:
        """No splat exists on the update route, so the pairing comes from the create one.

        ``PUT /watering-logs/{key}`` was the worse of #971's two findings: the
        service assigns the body onto the loaded model with ``setattr``, which
        Pydantic does not validate, so an unknown enum value is **written** and
        every later read of that document then raises.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel

            from app.common.enums import ApplicationMethod


            class WateringLogCreate(BaseModel):
                application_method: ApplicationMethod = ApplicationMethod.DRENCH
                volume_liters: float = 1.0


            class WateringLogUpdate(BaseModel):
                application_method: str | None = None
            """,
            router="""
            from fastapi import APIRouter

            from app.api.v1.watering_logs.schemas import WateringLogCreate, WateringLogUpdate
            from app.domain.models.watering_log import WateringLog

            router = APIRouter()


            @router.post("/watering-logs")
            def create_log(body: WateringLogCreate):
                return WateringLog(**body.model_dump())


            @router.put("/watering-logs/{key}")
            def update_log(key: str, body: WateringLogUpdate):
                return key, body.model_dump(exclude_unset=True)
            """,
        )
        assert _kinds(app) == [("enum_widened_to_str", "application_method")]

    def test_an_update_schema_nobody_binds_as_a_request_body_is_not_paired(
        self, build_tree: Callable[..., Path]
    ) -> None:
        """A dead schema cannot 500 anything, and counting it would inflate the ceiling."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel

            from app.common.enums import ApplicationMethod


            class WateringLogCreate(BaseModel):
                application_method: ApplicationMethod = ApplicationMethod.DRENCH
                volume_liters: float = 1.0


            class WateringLogUpdate(BaseModel):
                application_method: str | None = None
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == []

    def test_a_different_resources_update_schema_is_not_pulled_in_by_prefix(
        self, build_tree: Callable[..., Path]
    ) -> None:
        """``WateringLogTemplateUpdate`` is another resource, not this one's sibling.

        The stem must match exactly; a prefix match would attach one resource's
        schema to another resource's domain model and report a coincidence.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel

            from app.common.enums import ApplicationMethod


            class WateringLogCreate(BaseModel):
                application_method: ApplicationMethod = ApplicationMethod.DRENCH
                volume_liters: float = 1.0


            class WateringLogTemplateUpdate(BaseModel):
                application_method: str | None = None
            """,
            router="""
            from fastapi import APIRouter

            from app.api.v1.watering_logs.schemas import (
                WateringLogCreate,
                WateringLogTemplateUpdate,
            )
            from app.domain.models.watering_log import WateringLog

            router = APIRouter()


            @router.post("/watering-logs")
            def create_log(body: WateringLogCreate):
                return WateringLog(**body.model_dump())


            @router.put("/watering-log-templates/{key}")
            def update_template(key: str, body: WateringLogTemplateUpdate):
                return key, body.model_dump()
            """,
        )
        assert _kinds(app) == []

    def test_the_nullable_shape_is_not_reported_for_a_sibling(self, build_tree: Callable[..., Path]) -> None:
        """There is no splat to read the dump flags from, so it is not decidable.

        Reporting it anyway would flag every optional field of every update
        schema, which is the whole design of a patch body.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel

            from app.common.enums import ApplicationMethod


            class WateringLogCreate(BaseModel):
                application_method: ApplicationMethod = ApplicationMethod.DRENCH
                volume_liters: float = 1.0


            class WateringLogUpdate(BaseModel):
                note: str | None = None
            """,
            router="""
            from fastapi import APIRouter

            from app.api.v1.watering_logs.schemas import WateringLogCreate, WateringLogUpdate
            from app.domain.models.watering_log import WateringLog

            router = APIRouter()


            @router.post("/watering-logs")
            def create_log(body: WateringLogCreate):
                return WateringLog(**body.model_dump())


            @router.put("/watering-logs/{key}")
            def update_log(key: str, body: WateringLogUpdate):
                return key, body.model_dump(exclude_unset=True)
            """,
        )
        assert _kinds(app) == []


class TestJustification:
    """The per-site escape hatch, and why a bare marker is not one."""

    _SCHEMA_WITH_REASON = """
    from pydantic import BaseModel


    class WateringLogCreate(BaseModel):
        # boundary-widening: legacy import accepts historical spellings, mapped in the service
        application_method: str = "drench"
        volume_liters: float = 1.0
    """

    def test_a_reason_above_the_field_exempts_it(self, build_tree: Callable[..., Path]) -> None:
        """A site that genuinely wants the wider type says so, in place, with a reason."""
        app = build_tree(schemas=self._SCHEMA_WITH_REASON, router=_CREATE_ROUTER)
        findings = _findings(app)
        assert [finding.justified for finding in findings] == [True]
        assert _kinds(app) == []

    def test_a_reason_on_the_field_line_exempts_it(self, build_tree: Callable[..., Path]) -> None:
        """Trailing placement is accepted too — same rule as the UTC check's hatch."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"  # boundary-widening: mapped in the service layer
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == []

    def test_a_bare_marker_is_not_an_exemption(self, build_tree: Callable[..., Path]) -> None:
        """The point of the hatch is the reason, not the token.

        Without this, the hatch is a silencer and the gate measures diligence at
        typing rather than at thinking.
        """
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"  # boundary-widening:
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == [("enum_widened_to_str", "application_method")]

    def test_a_too_short_reason_is_not_an_exemption(self, build_tree: Callable[..., Path]) -> None:
        """``# boundary-widening: ok`` explains nothing a reviewer can argue with."""
        app = build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"  # boundary-widening: ok
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )
        assert _kinds(app) == [("enum_widened_to_str", "application_method")]

    def test_the_report_names_every_justified_site(
        self, build_tree: Callable[..., Path], capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An exemption stays visible; a silent one is indistinguishable from a fix."""
        app = build_tree(schemas=self._SCHEMA_WITH_REASON, router=_CREATE_ROUTER)
        assert checker.main(["--app-root", str(app), "--baseline", "0"]) == checker.EXIT_OK
        out = capsys.readouterr().out
        assert "justified" in out
        assert "legacy import accepts historical spellings" in out


class TestRatchetDirections:
    """Growth fails, equality passes, a drop passes and names the new number (#973)."""

    @pytest.fixture
    def two_widened_fields(self, build_tree: Callable[..., Path]) -> Path:
        """A tree carrying exactly two enum-widened fields."""
        return build_tree(
            schemas="""
            from pydantic import BaseModel


            class WateringLogCreate(BaseModel):
                application_method: str = "drench"
                water_source: str | None = None
                volume_liters: float = 1.0
            """,
            router=_CREATE_ROUTER,
        )

    def test_equal_to_the_ceiling_is_green(self, two_widened_fields: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert checker.main(["--app-root", str(two_widened_fields), "--baseline", "2"]) == checker.EXIT_OK
        assert "deferred, not settled" in capsys.readouterr().out

    def test_growth_fails_and_lists_every_counted_field(
        self, two_widened_fields: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The check has no memory of which one is new, so it prints them all."""
        assert checker.main(["--app-root", str(two_widened_fields), "--baseline", "1"]) == checker.EXIT_DEFECTS
        out = capsys.readouterr().out
        assert "1 above the ceiling of 1" in out
        assert "application_method" in out
        assert "water_source" in out

    def test_a_drop_passes_and_names_the_new_number(
        self, two_widened_fields: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Per #973: failing on a drop makes every concurrent PR conflict on one integer.

        Worse, resolving that conflict by taking either side leaves a ceiling
        above reality, which loosens the gate without anybody seeing it.
        """
        assert checker.main(["--app-root", str(two_widened_fields), "--baseline", "5"]) == checker.EXIT_OK
        out = capsys.readouterr().out
        assert "below the recorded ceiling of 5" in out
        assert "can be lowered to 2" in out

    def test_json_reports_the_counts_and_every_finding(
        self, two_widened_fields: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import json

        checker.main(["--app-root", str(two_widened_fields), "--baseline", "2", "--json"])
        payload = json.loads(capsys.readouterr().out)
        assert payload["enum_widened_to_str"] == 2
        assert payload["nullable_over_non_nullable"] == 0
        assert {finding["field"] for finding in payload["findings"]} == {"application_method", "water_source"}

    def test_a_missing_root_is_a_usage_error_not_a_pass(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A check that cannot run must not report success — the #814 failure mode."""
        assert checker.main(["--app-root", str(tmp_path / "nowhere")]) == checker.EXIT_USAGE
        assert "does not exist" in capsys.readouterr().err


class TestTheRecordedCeilingIsHonest:
    """The committed ceiling, measured against the real tree."""

    def test_the_real_tree_is_at_or_below_the_recorded_ceiling(self) -> None:
        """What the pre-commit hook asserts, asserted here too.

        Running it from pytest as well means a backend-only change that widens an
        enum goes red in the backend suite, not only in the ``static`` lane.
        """
        assert checker.main([]) == checker.EXIT_OK

    def test_the_ceiling_is_not_stale_by_more_than_a_working_margin(self) -> None:
        """A ceiling far above reality is a gate that has quietly stopped gating.

        Not an equality assertion: a drop is deliberately allowed to pass
        unrecorded (#973), so the constant may legitimately lag. It may not lag
        *far* — five is a batch of fixes, not a forgotten sweep.
        """
        app_root = _REPO_ROOT / checker.DEFAULT_APP_ROOT
        _tree, _pairings, findings = checker.collect(app_root)
        widened = [finding for finding in findings if finding.kind == "enum_widened_to_str" and not finding.justified]
        assert checker.MAX_ENUM_WIDENED_FIELDS - len(widened) <= 5, (
            f"MAX_ENUM_WIDENED_FIELDS is {checker.MAX_ENUM_WIDENED_FIELDS} but the tree carries "
            f"{len(widened)}; lower the constant in scripts/check_boundary_validation.py"
        )

    def test_no_nullable_widening_survives_in_the_real_tree(self) -> None:
        """This shape has no debt and no baseline — zero is the whole rule."""
        app_root = _REPO_ROOT / checker.DEFAULT_APP_ROOT
        _tree, _pairings, findings = checker.collect(app_root)
        nullable = [
            finding for finding in findings if finding.kind == "nullable_over_non_nullable" and not finding.justified
        ]
        assert nullable == []
