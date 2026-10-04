"""Seed database with system activity definitions.

All data is loaded from seed_data/activities.yaml.

A seed entry is matched to a stored row by ``name`` among the **global** rows only
(:func:`global_activity_map`, #2027). The loader used to look the name up across
every row: a tenant's own activity named like a seed was found, rewritten from the
seed model (``is_system: true``, ``tenant_key: ""``) and so turned into a global
system row. Since v0076 the unique index is ``(tenant_key, name)``, so the global
seed row and a tenant's activity of the same name coexist.
"""

import structlog

from app.common.dependencies import get_activity_repo
from app.data_access.arango.activity_repository import ArangoActivityRepository
from app.domain.models.activity import Activity
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def global_activity_map(repo: ArangoActivityRepository) -> dict[str, Activity]:
    """``name → global activity`` — the seed-match universe (#2027).

    Global rows only (``tenant_key`` empty or absent), the whole catalogue, through
    :meth:`ArangoActivityRepository.get_global_activities`. The first row per name
    wins; the rows come ordered by ``_key``.
    """
    rows: dict[str, Activity] = {}
    for activity in repo.get_global_activities():
        rows.setdefault(activity.name, activity)
    return rows


def run_seed_activities() -> None:
    """Upsert system activities from YAML seed data."""
    repo = get_activity_repo()
    data = load_yaml("activities.yaml")

    activities = data.get("activities", [])
    existing_map = global_activity_map(repo)
    created = 0
    updated = 0

    for entry in activities:
        entry["is_system"] = True
        existing = existing_map.get(entry["name"])

        if existing:
            activity = Activity.model_validate({**entry, "_key": existing.key})
            repo.update(existing.key, activity)
            updated += 1
        else:
            activity = Activity.model_validate(entry)
            # Recorded so a name the YAML lists twice updates the row just created.
            existing_map[activity.name] = repo.create(activity)
            created += 1

    logger.info("seed_activities_complete", created=created, updated=updated)
