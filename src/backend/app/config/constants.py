"""Domain constants for system parameters.

Phase-specific data (VPD ranges, NPK defaults, EC targets, photoperiod)
has been moved to seed_data/species.yaml (default_phases section).

Substrate-specific data (EC limits) has been moved to
seed_data/substrate_defaults.yaml.
"""

# Default rotation window in years
DEFAULT_ROTATION_WINDOW_YEARS: int = 3

# NFR-011 §4: the erasure tombstone salt (ERASURE_TOMBSTONE_SALT) must be a
# high-entropy secret; a value shorter than this is treated as unset/insecure.
# Read by the API start-up gate (app.main) and the worker start-up gate (app.tasks).
MIN_TOMBSTONE_SALT_LENGTH: int = 32

# NFR-011 §3.4 L-1/L-2 (#1812): the log pseudonym salt (LOG_PSEUDONYM_SALT) keys
# the ``sub_…`` subject references and the ``email_sha256`` digests on log lines.
# Same floor as the tombstone salt; read by both start-up gates, by
# ``ErasureEngine.log_subject`` and by ``app.common.decoys.email_digest``.
MIN_LOG_PSEUDONYM_SALT_LENGTH: int = 32
