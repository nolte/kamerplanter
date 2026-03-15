"""Seed data for REQ-020 Onboarding Starter Kits."""

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.starter_kit import StarterKit
from app.migrations.yaml_loader import load_yaml


def seed_starter_kits(db) -> int:
    """Seed starter kits into the database. Returns count of kits created."""
    data = load_yaml("starter_kits.yaml")
    repo = BaseArangoRepository(db, col.STARTER_KITS)
    created = 0
    for kit_data in data["starter_kits"]:
        existing = repo.find_by_field("kit_id", kit_data["kit_id"])
        if not existing:
            kit = StarterKit(**kit_data)
            repo.create(kit)
            created += 1
    return created
