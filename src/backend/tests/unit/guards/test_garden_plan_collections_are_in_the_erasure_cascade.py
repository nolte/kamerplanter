"""REQ-053 GP-NFR-055 / SR-007 (WP 4.1, #2400) — every account reference of the garden-plan collections is erased.

The five collections REQ-053 added hold an account key in several places: the five of ``care_events``,
``garden_objects.created_by``, ``sites.plan.plan_updated_by``, ``garden_plan_audit.user_key`` and
``bed_templates.created_by``. ``scripts/check_privacy_inventory.py`` (R6) finds a stored model field of that shape
that the erasure inventory misses — for any model. What it cannot see is the **list this requirement names**: a
model that is renamed away from the shape, a field moved into a nested object, or a collection that has a writer
and no model. So this guard pins the named list itself, from the models, against the rules the cascade executes.

* each named ``(collection, field)`` that a model carries is in ``ErasureEngine``'s anonymisation or
  pseudonymisation rules (or is excluded with a reason);
* each rule names a field the model really has (a rule on a field that does not exist erases nothing, #1663);
* ``bed_templates`` has a model since WP 7.8 (#2474); it is read off the model like the others, and the
  second guard below keeps demanding the ``created_by`` rule for any module that names the collection.

Spelling it does not see: an account reference stored under a name outside the R6 pattern.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from app.data_access.arango import collections as col
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.bed_template import BedTemplate
from app.domain.models.care_event import CareEvent
from app.domain.models.garden_object import GardenObject
from app.domain.models.garden_plan import PlanAuditRecord
from app.domain.models.site import SitePlan

APP = Path(__file__).resolve().parents[3] / "app"

#: The R6 shape of ``scripts/check_privacy_inventory.py``.
ACCOUNT_FIELD = re.compile(r"^(user_key|[a-z0-9_]+_user_key|[a-z0-9_]+_by_key|[a-z0-9_]+_account_key|[a-z0-9_]+_by)$")

#: ``(collection, dotted field prefix, model)`` — what GP-NFR-055 names, read off the models.
NAMED = (
    (col.CARE_EVENTS, "", CareEvent),
    (col.GARDEN_OBJECTS, "", GardenObject),
    (col.SITES, "plan.", SitePlan),
    (col.GARDEN_PLAN_AUDIT, "", PlanAuditRecord),
    (col.BED_TEMPLATES, "", BedTemplate),
)


def account_fields(model: type) -> set[str]:
    return {name for name in model.model_fields if ACCOUNT_FIELD.match(name)}


def reached() -> set[tuple[str, str]]:
    rules = [*ErasureEngine.ANONYMIZE_COLLECTIONS, *ErasureEngine.PSEUDONYMIZE_AUDIT_COLLECTIONS]
    return {(rule.collection, rule.user_field) for rule in rules} | {
        (rule.collection, field) for rule in rules for field in rule.clear_fields
    }


def excluded() -> set[tuple[str, str]]:
    return {(entry.collection, entry.user_field) for entry in ErasureEngine.EXCLUDED_USER_REFERENCES}


def test_the_named_fields_are_what_the_requirement_lists() -> None:
    """Anti-vacuity: the models still carry the fields GP-NFR-055 names, so an empty match cannot pass."""
    assert account_fields(CareEvent) >= {
        "performed_by_user_key",
        "performed_for_user_key",
        "created_by",
        "voided_by",
        "redacted_by",
    }
    assert account_fields(GardenObject) == {"created_by"}
    assert account_fields(SitePlan) == {"plan_updated_by"}
    assert account_fields(PlanAuditRecord) == {"user_key"}
    assert account_fields(BedTemplate) == {"created_by"}


def test_every_account_reference_of_the_named_collections_is_in_the_cascade() -> None:
    covered = reached() | excluded()
    missing = sorted(
        f"{collection}.{prefix}{field}"
        for collection, prefix, model in NAMED
        for field in account_fields(model)
        if (collection, f"{prefix}{field}") not in covered
    )
    assert missing == [], f"These account references survive an account erasure (SR-007): {missing}"


def test_every_rule_on_these_collections_names_a_field_the_model_has() -> None:
    fields = {(collection, f"{prefix}{field}") for collection, prefix, model in NAMED for field in model.model_fields}
    named_collections = {collection for collection, _, _ in NAMED}
    stale = sorted(
        f"{collection}.{field}"
        for collection, field in reached()
        if collection in named_collections and (collection, field) not in fields
    )
    assert stale == [], f"Erasure rules on fields these models do not have: {stale}"


def test_an_account_reference_is_anonymised_not_left_to_the_exclusion_list_by_accident() -> None:
    """``superseded_by_key`` matches the shape but is a document key: the one exclusion, with its reason."""
    assert ("care_events", "superseded_by_key") in excluded()
    assert {field for collection, field in excluded() if collection == "care_events"} == {"superseded_by_key"}


def _mentions_bed_templates(path: Path) -> bool:
    """Whether the module names the collection: ``col.BED_TEMPLATES`` or the string ``"bed_templates"`` (AST)."""
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Attribute) and node.attr == "BED_TEMPLATES":
            return True
        if isinstance(node, ast.Constant) and node.value == "bed_templates":
            return True
    return False


def test_every_module_that_writes_or_models_bed_templates_has_the_rule_in_the_cascade() -> None:
    """§20.12 (``bed_templates``, WP 7.8): a writer or a model of the collection needs the ``created_by`` rule."""
    sources = [
        path
        for path in (APP / "data_access").rglob("*.py")
        if path.name != "collections.py" and "migrations" not in path.parts
    ] + list((APP / "domain" / "models").glob("*.py"))
    mentions = [path.relative_to(APP).as_posix() for path in sources if _mentions_bed_templates(path)]
    assert mentions, "the scan found no module that names bed_templates: it has gone blind"
    if mentions:
        assert ("bed_templates", "created_by") in reached(), (
            f"{mentions} write or model bed_templates, but ErasureEngine has no rule for bed_templates.created_by "
            "(GP-NFR-055, SR-007). Add the AnonymisationRule and its Art. 15 manifest source in the same change."
        )
