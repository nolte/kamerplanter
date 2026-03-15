"""Seed database with system activity definitions.

All data is loaded from seed_data/activities.yaml.
"""

import structlog

from app.common.dependencies import get_activity_repo
from app.domain.models.activity import Activity
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def run_seed_activities() -> None:
    """Upsert system activities from YAML seed data."""
    repo = get_activity_repo()
    data = load_yaml("activities.yaml")

    activities = data.get("activities", [])
    created = 0
    updated = 0

    for entry in activities:
        entry["is_system"] = True
        existing = repo.get_by_name(entry["name"])

        if existing:
            activity = Activity.model_validate({**entry, "_key": existing.key})
            repo.update(existing.key, activity)
            updated += 1
        else:
            activity = Activity.model_validate(entry)
            repo.create(activity)
            created += 1

    logger.info("seed_activities_complete", created=created, updated=updated)
