"""Every local ``$ref`` in the exported OpenAPI document resolves inside the document.

The defect: #2749 (PR #2799) embedded ``BedTemplateExchangeFile.model_json_schema()`` as a hand-written
``openapi_extra`` request body. Its nested models point at ``#/$defs/<Name>`` — root-relative, so they resolve
nowhere once the schema sits under ``paths`` — and the Spectral lint (``invalid-ref``) of the advisory
``OpenAPI export + lint`` lane turned ``develop`` red. The plan import route had the same shape and only a
per-model check (``test_garden_plan_import_api``), which the sibling route never got.

This guard checks the whole document instead of one model, in ``tests/unit/guards`` (run by the required
``Write-route and tree guards`` context). The document is the one the lane lints: ``scripts.export_openapi``
in a subprocess, which pins the full router surface itself.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from collections.abc import Iterator
from typing import Any

import pytest
from pydantic import BaseModel

from app.common.openapi_responses import request_body_schema

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _local_refs(node: Any, where: str = "#") -> Iterator[tuple[str, str]]:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#"):
            yield where, ref
        for key, value in node.items():
            yield from _local_refs(value, f"{where}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _local_refs(value, f"{where}/{index}")


def _resolves(document: dict[str, Any], ref: str) -> bool:
    node: Any = document
    for raw in ref.removeprefix("#/").split("/"):
        part = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True


def test_every_local_ref_in_the_exported_document_resolves(tmp_path: pathlib.Path) -> None:
    out = tmp_path / "openapi.json"
    python_path = os.pathsep.join(p for p in (str(BACKEND_ROOT), os.environ.get("PYTHONPATH", "")) if p)
    export = subprocess.run(
        [sys.executable, "-W", "ignore", "-m", "scripts.export_openapi", "--out", str(out)],
        cwd=BACKEND_ROOT,
        env={**os.environ, "PYTHONPATH": python_path},
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    assert export.returncode == 0, export.stdout + export.stderr
    document = json.loads(out.read_text(encoding="utf-8"))

    refs = list(_local_refs(document))
    dangling = [f"{where} -> {ref}" for where, ref in refs if not _resolves(document, ref)]

    assert refs, "the walk found no $ref at all - it is not looking at the document"
    assert dangling == []


class _Leaf(BaseModel):
    value: int


class _Branch(BaseModel):
    leaf: _Leaf
    leaves: list[_Leaf]


class _Recursive(BaseModel):
    child: _Recursive | None = None


def test_request_body_schema_inlines_the_nested_models() -> None:
    schema = request_body_schema(_Branch)

    assert "$ref" not in json.dumps(schema)
    assert "$defs" not in schema
    assert schema["properties"]["leaf"]["properties"]["value"]["type"] == "integer"
    assert schema["properties"]["leaves"]["items"]["properties"]["value"]["type"] == "integer"


def test_request_body_schema_refuses_a_recursive_model() -> None:
    with pytest.raises(ValueError, match="recursive"):
        request_body_schema(_Recursive)
