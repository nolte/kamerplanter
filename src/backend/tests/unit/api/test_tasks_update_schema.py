"""``TaskUpdate`` enforces the same bounds as ``TaskCreate`` (SEC-007).

``PUT /tasks/{key}`` ``setattr``s the submitted values straight onto the domain
``Task`` model, which does not validate on assignment — so whatever the schema
accepts is persisted unchecked. The bound on ``name`` therefore has to live in
the update schema, not only in the create schema (and not in the browser, whose
incidental enforcement disappeared with ``noValidate``).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.tasks.schemas import TaskCreate, TaskUpdate


def test_name_bounds_match_the_create_schema() -> None:
    create_field = TaskCreate.model_fields["name"]
    update_field = TaskUpdate.model_fields["name"]

    def _bounds(field) -> dict[str, int]:  # noqa: ANN001 — pydantic FieldInfo
        return {
            type(meta).__name__: getattr(meta, "min_length", None) or getattr(meta, "max_length", None)
            for meta in field.metadata
        }

    assert _bounds(update_field) == _bounds(create_field)


def test_empty_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskUpdate(name="")


def test_overlong_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TaskUpdate(name="x" * 201)


def test_omitted_name_stays_optional() -> None:
    """A partial update that does not touch ``name`` is unaffected."""
    update = TaskUpdate(priority="high")

    assert update.name is None
    assert update.model_dump(exclude_none=True) == {"priority": "high"}


def test_valid_name_passes() -> None:
    assert TaskUpdate(name="x" * 200).name == "x" * 200
