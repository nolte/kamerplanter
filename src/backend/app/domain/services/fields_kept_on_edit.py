"""Carry the fields an edit body does not hold over from the stored record.

Several ``PUT`` routes rebuild the domain model from the request body
(``Model(**body.model_dump())``). Every model field the body schema does not
declare therefore reaches the service at its **default**, and the repository
writes it: ``False``, ``[]`` and ``""`` overwrite the stored value, so an edit
silently turns a system location type into a deletable one, a substrate mix into
a plain substrate, or clears a species' traits.

The owning service names those fields once, as a tuple next to its update method,
and passes the stored record it already reads for the existence / ownership check
to :func:`keep_stored_fields`. The tuple is also what
``tests/unit/guards/test_put_rebuild_keeps_fields_the_body_lacks.py`` checks every
rebuilding route against, so a new model field the body does not carry is a
decision, not a silent reset.
"""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel


def keep_stored_fields[M: BaseModel](update: M, stored: M, fields: Iterable[str]) -> M:
    """Set each of ``fields`` on ``update`` to the value ``stored`` holds, and return ``update``.

    ``stored`` is the record just read for the update, so its values are handed
    over as they are. A name the model does not declare raises ``AttributeError``
    — a misspelt entry must not turn into a field that is quietly never kept.
    """
    declared = type(update).model_fields
    for name in fields:
        if name not in declared:
            raise AttributeError(f"{type(update).__name__} has no field {name!r} to keep on edit")
        setattr(update, name, getattr(stored, name))
    return update
