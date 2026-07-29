"""Shared, optional error-tracking wiring for the Kamerplanter Python services."""

from kp_errortracking.error_tracking import (
    ENVIRONMENTS,
    init_error_tracking,
    resolve_release,
    scrub_breadcrumb,
    scrub_event,
)

__all__ = [
    "ENVIRONMENTS",
    "init_error_tracking",
    "resolve_release",
    "scrub_breadcrumb",
    "scrub_event",
]
