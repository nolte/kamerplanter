"""Shared, optional error-tracking wiring for the Kamerplanter Python services."""

from kp_errortracking.error_tracking import (
    ENVIRONMENTS,
    init_error_tracking,
    install_uncaught_exception_redaction,
    resolve_release,
    scrub_breadcrumb,
    scrub_event,
    shape_text_redactor,
)

__all__ = [
    "ENVIRONMENTS",
    "init_error_tracking",
    "install_uncaught_exception_redaction",
    "resolve_release",
    "scrub_breadcrumb",
    "scrub_event",
    "shape_text_redactor",
]
