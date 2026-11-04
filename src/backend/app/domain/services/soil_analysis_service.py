"""The soil analyses of a bed as series (REQ-053 §15.1, GP-FR-122; WP 8.7, #2650).

``GET /locations/{key}/soil-analyses``: the ``measurements`` of the bed's ``soil_analysis`` care events, per
parameter and **per method**, with every change of method marked - and never converted (U-002/U-003). The rules are
the pure :mod:`app.domain.engines.soil_analysis_engine`; this service reads.

Read-only. The method takes ``*, tenant_key: str`` without a default; the bed is resolved through
:mod:`~app.domain.services.location_ownership` (a bed has no ``tenant_key`` of its own, #2107), so a foreign and an
absent bed answer the same 404. The read is bounded: at most ``limit`` analyses (newest first), and the answer says
whether older ones were left out. The *write* of an analysis into the profile is not here: it happens in the
transaction of the care event itself (``write_care_event``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.engines.soil_analysis_engine import AnalysisEvent, MethodChange, Series, build_series
from app.domain.interfaces.care_event_repository import CareEventFilter, ICareEventRepository
from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.services.location_ownership import resolve_owned_location

#: Most analyses one answer carries.
MAX_ANALYSES = 500
DEFAULT_ANALYSES = 200


@dataclass(frozen=True)
class SoilAnalysisSeries:
    """The answer: series per ``(parameter, method)``, the marked changes, and whether the read was cut."""

    series: list[Series] = field(default_factory=list)
    method_changes: list[MethodChange] = field(default_factory=list)
    analyses: int = 0
    truncated: bool = False


class SoilAnalysisService:
    def __init__(self, site_repo: ISiteRepository, care_event_repo: ICareEventRepository) -> None:
        self._sites = site_repo
        self._events = care_event_repo

    def series(
        self,
        location_key: str,
        *,
        tenant_key: str,
        parameter: str | None = None,
        performed_from: datetime | None = None,
        performed_to: datetime | None = None,
        limit: int = DEFAULT_ANALYSES,
    ) -> SoilAnalysisSeries:
        """The analyses of the bed in the range, newest ``limit`` of them, as series per method."""
        resolve_owned_location(self._sites, location_key, tenant_key)
        bounded = max(1, min(limit, MAX_ANALYSES))
        rows = self._events.list_events(
            CareEventFilter(
                location_key=location_key,
                category="soil_analysis",
                performed_from=performed_from,
                performed_to=performed_to,
                exclude_voided=True,
            ),
            tenant_key=tenant_key,
            offset=0,
            limit=bounded + 1,
        )
        truncated = len(rows) > bounded
        events = [
            AnalysisEvent(
                key=row.event.key or "", performed_at=row.event.performed_at, measurements=row.event.measurements
            )
            for row in rows[:bounded]
            if row.event.measurements
        ]
        series, changes = build_series(events, parameter)
        return SoilAnalysisSeries(series=series, method_changes=changes, analyses=len(events), truncated=truncated)
