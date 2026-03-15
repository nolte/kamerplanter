"""YAML seed data loader utility.

Loads seed data from YAML files in the seed_data/ directory.
Pydantic v2 models handle string→enum coercion via model_validate().
"""

from pathlib import Path
from typing import Any

import yaml

SEED_DATA_DIR = Path(__file__).parent / "seed_data"


def load_yaml(filename: str) -> Any:
    """Load and parse a YAML file from the seed_data directory."""
    path = SEED_DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
