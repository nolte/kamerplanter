"""Request/response schemas of the bed templates (REQ-053 §20.12, §21.7; WP 7.8, #2474).

``tenant_key`` and ``created_by`` are absent from every body and every response (``check_tenant_body_field``,
GP-NFR-055): the owner of a template is the caller's tenant, and the author is never shown. ``is_system`` says
whether a template is a global (system) one - those cannot be changed by a tenant.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domain.models.bed_template import (
    BedTemplate,
    BedTemplateInput,
    BedTemplatePatch,
    DefaultLayout,
    SoilProfileDefaults,
)
from app.domain.models.bed_template_exchange import BedTemplateExchange, BedTemplateImportReport
from app.domain.models.geometry import BedFrameGeometry

_RECT_GEOMETRY: dict[str, Any] = {"kind": "rect", "origin": [0, 0], "width_m": 2.0, "length_m": 1.0, "rotation_deg": 0}
#: The file of GP-API-070 / the body of GP-API-071 as the OpenAPI document shows it.
_EXCHANGE_EXAMPLE: dict[str, Any] = {
    "format": "kamerplanter.bed_template",
    "schema_version": "1",
    "name": "Herb bed 1.5 x 0.8",
    "location_type_key": "raised_bed",
    "default_geometry": {"kind": "rect", "origin": [0, 0], "width_m": 1.5, "length_m": 0.8, "rotation_deg": 0},
    "height_m": 0.4,
    "default_layout": {"row_spacing_cm": 25, "spacing_cm": 20},
    "soil_profile_defaults": None,
}


class BedTemplateCreate(BedTemplateInput):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "name": "Herb bed 1.5 x 0.8",
                    "location_type_key": "raised_bed",
                    "default_geometry": {
                        "kind": "rect",
                        "origin": [0, 0],
                        "width_m": 1.5,
                        "length_m": 0.8,
                        "rotation_deg": 0,
                    },
                    "height_m": 0.4,
                    "default_layout": {"row_spacing_cm": 25, "spacing_cm": 20},
                    "soil_profile_defaults": {"growing_medium_kind": "raised_bed_mix", "drainage": "good"},
                    "recurring_task_templates": [],
                }
            ]
        },
    )


class BedTemplateUpdate(BedTemplatePatch):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"name": "Herb bed", "height_m": None}]},
    )


class BedTemplateResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "key": "sys_bed_2x1",
                    "name": "Bed 2 x 1 m",
                    "location_type_key": "bed",
                    "default_geometry": _RECT_GEOMETRY,
                    "height_m": None,
                    "default_layout": {"row_spacing_cm": None, "spacing_cm": None},
                    "soil_profile_defaults": None,
                    "recurring_task_templates": [],
                    "is_system": True,
                    "created_at": "2026-10-20T08:00:00Z",
                    "updated_at": "2026-10-20T08:00:00Z",
                }
            ]
        }
    )

    key: str
    name: str
    location_type_key: str
    #: In the bed frame (§9.2): the anchor of the shape sits at the origin.
    default_geometry: BedFrameGeometry
    height_m: float | None = None
    default_layout: DefaultLayout
    soil_profile_defaults: SoilProfileDefaults | None = None
    #: ``task_templates`` keys, stored only - placing a template copies none of them.
    recurring_task_templates: list[str]
    #: ``True`` for a global template (read by every tenant, changed by a platform admin only).
    is_system: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


def bed_template_to_response(template: BedTemplate) -> BedTemplateResponse:
    return BedTemplateResponse(
        key=template.key or "",
        name=template.name,
        location_type_key=template.location_type_key,
        default_geometry=template.default_geometry,
        height_m=template.height_m,
        default_layout=template.default_layout,
        soil_profile_defaults=template.soil_profile_defaults,
        recurring_task_templates=list(template.recurring_task_templates),
        is_system=template.is_system,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


class BedTemplateExchangeFile(BedTemplateExchange):
    """The file ``GET /bed-templates/{key}/export`` delivers and ``POST /bed-templates/import`` reads (GP-FR-173).

    No ``key``, ``tenant_key``, ``created_by``, timestamps, task templates or notes. On import, top-level fields
    the schema does not name are ignored; the nested objects are strict.
    """

    model_config = ConfigDict(extra="ignore", json_schema_extra={"examples": [_EXCHANGE_EXAMPLE]})


class BedTemplateImportResponse(BaseModel):
    """The check report of ``POST /bed-templates/import`` - the same for ``dry_run=true`` and the applied import."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "dry_run": True,
                    "schema_version": "1",
                    "migrated": False,
                    "template": _EXCHANGE_EXAMPLE,
                    "created_key": None,
                    "dropped_fields": ["created_by", "tenant_key"],
                    "unknown_fields_ignored": 0,
                }
            ]
        }
    )

    dry_run: bool
    #: The version the file was written in; ``migrated`` = lifted to the current one.
    schema_version: str
    migrated: bool
    #: The template as it is (or would be) stored, with the name it gets.
    template: BedTemplateExchangeFile
    #: The new template's key; ``null`` on a dry run.
    created_key: str | None = None
    #: Known fields of the file that were dropped on purpose (document keys, owner, author, task templates).
    dropped_fields: list[str]
    #: How many further unknown top-level fields were ignored (their names are not echoed).
    unknown_fields_ignored: int


def import_report_to_response(report: BedTemplateImportReport) -> BedTemplateImportResponse:
    return BedTemplateImportResponse(
        dry_run=report.dry_run,
        schema_version=report.schema_version,
        migrated=report.migrated,
        template=BedTemplateExchangeFile(
            format=report.template.format,
            schema_version=report.template.schema_version,
            name=report.template.name,
            location_type_key=report.template.location_type_key,
            default_geometry=report.template.default_geometry,
            height_m=report.template.height_m,
            default_layout=report.template.default_layout,
            soil_profile_defaults=report.template.soil_profile_defaults,
        ),
        created_key=report.created_key,
        dropped_fields=list(report.dropped_fields),
        unknown_fields_ignored=report.unknown_fields_ignored,
    )
