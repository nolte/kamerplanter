"""Domain constants for system parameters.

Phase-specific data (VPD ranges, NPK defaults, EC targets, photoperiod)
has been moved to seed_data/species.yaml (default_phases section).

Substrate-specific data (EC limits) has been moved to
seed_data/substrate_defaults.yaml.
"""

# Default rotation window in years
DEFAULT_ROTATION_WINDOW_YEARS: int = 3

# REQ-053 GP-FR-131 (K-004): the fallback window and any per-family pause stop at 8 years; longer lock-out periods
# after an infestation (club root, potato cyst nematodes) belong to ``soil_hazards`` (REQ-054 H-10), not here.
MAX_ROTATION_WINDOW_YEARS: int = 8

# REQ-053 GP-API-039: the look-back of ``GET /locations/{key}/rotation`` is at least this many years by default, at
# most ``MAX_ROTATION_TIMELINE_YEARS`` (a larger ``years`` is a 422).
MIN_ROTATION_TIMELINE_YEARS: int = 5
MAX_ROTATION_TIMELINE_YEARS: int = 10

# NFR-011 §4: the erasure tombstone salt (ERASURE_TOMBSTONE_SALT) must be a
# high-entropy secret; a value shorter than this is treated as unset/insecure.
# Read by the API start-up gate (app.main) and the worker start-up gate (app.tasks).
MIN_TOMBSTONE_SALT_LENGTH: int = 32

# NFR-011 §3.4 L-1/L-2 (#1812): the log pseudonym salt (LOG_PSEUDONYM_SALT) keys
# the ``sub_…`` subject references and the ``email_sha256`` digests on log lines.
# Same floor as the tombstone salt; read by both start-up gates, by
# ``ErasureEngine.log_subject`` and by ``app.common.decoys.email_digest``.
MIN_LOG_PSEUDONYM_SALT_LENGTH: int = 32

# #2154: how long a Celery worker that reports readiness (WORKER_READY_FILE set)
# keeps trying to open ArangoDB before it refuses to start, and how long it waits
# between tries. One unreachable-server attempt itself takes ~18 s (python-arango's
# own retries, measured), so the worst case is about budget + 18 s. The chart's
# worker startupProbe must outlast it (tests/unit/guards/test_chart_worker_probes.py).
WORKER_DATABASE_START_BUDGET_SECONDS: int = 60
WORKER_DATABASE_START_RETRY_SECONDS: int = 5
