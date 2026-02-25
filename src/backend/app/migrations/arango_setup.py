"""ArangoDB setup: create collections, edges, indexes, and graph."""

import structlog

from app.common.dependencies import get_db
from app.data_access.arango.collections import ensure_collections

logger = structlog.get_logger()


def run_setup() -> None:
    """Initialize ArangoDB with all required collections and graph."""
    db = get_db()
    logger.info("arango_setup_start")
    ensure_collections(db)
    logger.info("arango_setup_complete")


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    run_setup()
