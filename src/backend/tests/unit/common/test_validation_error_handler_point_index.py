"""The 422 envelope carries ``point_index`` for a coordinate-range error only (REQ-053 GP-ACC-056).

``validation_error_handler`` is global, so the extension is keyed on the error type:
a ``geometry.invalid`` error with ``ctx.point_index`` gains the key, every other
error keeps exactly ``field``/``reason``/``code`` — even one whose context happens
to carry a ``point_index``.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.common.error_handlers import validation_error_handler


def _details(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    request = Request({"type": "http", "method": "PUT", "path": "/api/v1/x", "query_string": b"", "headers": []})
    response = asyncio.run(validation_error_handler(request, RequestValidationError(errors)))
    assert response.status_code == 422
    body = json.loads(bytes(response.body))
    assert body["error_code"] == "VALIDATION_ERROR"
    details: list[dict[str, Any]] = body["details"]
    return details


def test_a_geometry_range_error_carries_the_point_index() -> None:
    (detail,) = _details(
        [
            {
                "type": "geometry.invalid",
                "loc": ("body", "boundary", "polygon", "points"),
                "msg": "Coordinates must lie within 0.0..1000.0 m, got (1000.5, 0.0).",
                "ctx": {"point_index": 3},
            }
        ]
    )
    assert detail == {
        "field": "body.boundary.polygon.points",
        "reason": "Coordinates must lie within 0.0..1000.0 m, got (1000.5, 0.0).",
        "code": "geometry.invalid",
        "point_index": 3,
    }


def test_an_origin_range_error_has_no_point_index() -> None:
    (detail,) = _details([{"type": "geometry.invalid", "loc": ("body", "origin"), "msg": "out of range"}])
    assert set(detail) == {"field", "reason", "code"}


def test_any_other_error_keeps_its_shape_even_with_a_point_index_in_ctx() -> None:
    (detail,) = _details(
        [{"type": "value_error", "loc": ("body", "name"), "msg": "bad", "ctx": {"point_index": 1, "error": "x"}}]
    )
    assert detail == {"field": "body.name", "reason": "bad", "code": "value_error"}
