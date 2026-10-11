"""Seed the plan catalogue (REQ-056 §7.1, §13.2, #2142).

``plans.yaml`` holds the default plan ``standard`` with every limit ``null`` (= the
instance settings). Create-if-absent: a plan the platform admin renamed or changed
is never overwritten, so a re-run - every boot - changes nothing once it exists.

Run by the seed registry on every boot, right after the migrations (v0091 stamps
``plan_key = "standard"`` on every tenant): fatal, because the plan a tenant points at
must exist. Should it be missing anyway, the entitlement check falls back to the
default plan, then to the instance settings, and logs ``entitlement.plan_missing``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.domain.models.plan import Plan, PlanLimits
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

#: ArangoDB "unique constraint violated": the key was inserted by someone else.
_ERR_UNIQUE_CONSTRAINT = 1210


def seeded_plans() -> list[Plan]:
    """The plans ``plans.yaml`` declares, validated against the domain model."""
    data = load_yaml("plans.yaml")
    return [
        Plan(
            key=entry["key"],
            name=entry["name"],
            description=entry["description"],
            is_default=entry["is_default"],
            limits=PlanLimits(**entry["limits"]),
        )
        for entry in data["plans"]
    ]


def _has_default(db: StandardDatabase) -> bool:
    cursor = db.aql.execute(
        "FOR p IN @@plans FILTER p.is_default == true LIMIT 1 RETURN 1", bind_vars={"@plans": col.PLANS}
    )
    return any(True for _ in cursor)  # type: ignore[union-attr]


def seed_plans(db: StandardDatabase) -> int:
    """Insert each seeded plan that is not stored yet; return how many were inserted. Idempotent."""
    if not db.has_collection(col.PLANS):
        db.create_collection(col.PLANS)
    plans_col = db.collection(col.PLANS)
    now = datetime.now(UTC).isoformat()
    created = 0
    for plan in seeded_plans():
        if plans_col.has(plan.key):
            continue
        doc: dict[str, Any] = {
            **plan.model_dump(by_alias=True, mode="json", exclude={"created_at", "updated_at"}),
            "created_at": now,
            "updated_at": now,
        }
        if doc["is_default"] and _has_default(db):
            # A platform admin already chose another default: re-creating this plan must not make two.
            doc["is_default"] = False
        try:
            plans_col.insert(doc)
        except DocumentInsertError as exc:
            if exc.error_code != _ERR_UNIQUE_CONSTRAINT:
                raise
            continue
        created += 1
    if created:
        logger.info("plans_seeded", count=created)
    return created


def run_seed_plans(db: StandardDatabase) -> None:
    """The seed-registry job: :func:`seed_plans`, its count only logged."""
    seed_plans(db)
