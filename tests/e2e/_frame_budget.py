"""The one rule a frame time is judged by (REQ-053 GP-NFR-033/034, D-01) - shared by the probe and the report.

A ``requestAnimationFrame`` gap is a whole number of display refreshes: an idle 60 Hz page already reads 16.7 ms.
A budget is therefore met when the gap stays within the budget plus a tenth of the page's own idle refresh
interval - 16.7 ms is "one refresh, no frame dropped" and within 16 ms, 33.3 ms is one dropped frame and over it.

Standard library only: ``_renderer_report.py`` runs on a bare CI runner without Selenium.
"""

from __future__ import annotations

#: The share of the idle refresh interval a frame gap may exceed its budget by.
VSYNC_TOLERANCE = 0.1
#: GP-NFR-033/034: one frame at 60 fps on a mid-range laptop, two on a mid-range phone; D-01's drag threshold.
LAPTOP_FRAME_BUDGET_MS = 16.0
PHONE_FRAME_BUDGET_MS = 33.0
D01_DRAG_FRAME_MS = 16.0


def frame_bound(budget_ms: float, vsync_ms: float | None) -> float:
    """The value a frame p95 is held against: *budget_ms* plus the refresh tolerance (none without a cadence)."""
    return float(budget_ms) + (VSYNC_TOLERANCE * float(vsync_ms) if vsync_ms else 0.0)


__all__ = [
    "D01_DRAG_FRAME_MS",
    "LAPTOP_FRAME_BUDGET_MS",
    "PHONE_FRAME_BUDGET_MS",
    "VSYNC_TOLERANCE",
    "frame_bound",
]
