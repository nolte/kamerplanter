"""The care log as CSV rows (REQ-053 GP-FR-104, GP-API-034 ``format=csv``; WP 8.4, #2647).

Pure: a list of :class:`CareEventView` in, header and rows out; the file itself (BOM, quoting, formula hardening of
text cells) is :mod:`app.common.csv_export`. The columns are the flat fields of GP-FR-100.

**No account key ever leaves.** ``performed_by`` and ``performed_for`` are the display names the view resolved (or
``anonymisiert``, or a third party's label), never the user keys. Free texts are what the log holds - a redacted
entry already reads ``[redacted]``. The photo references are not exported (only their count): they are storage
handles, not content of a spreadsheet.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.common.csv_export import csv_number, csv_text
from app.domain.models.care_event import CareEventView

#: Separator of the plants of one event inside a cell.
PLANT_SEPARATOR = " | "

CARE_EVENT_CSV_COLUMNS: tuple[str, ...] = (
    "performed_at",
    "category",
    "summary",
    "location_key",
    "plant_names",
    "performed_by",
    "performed_for",
    "trigger",
    "reason",
    "product_label",
    "quantity",
    "unit",
    "quantity_total",
    "quantity_total_unit",
    "material",
    "observed_outcome",
    "outcome_rating",
    "photo_count",
    "superseded",
    "voided_at",
    "void_reason",
    "redacted_at",
    "key",
)


def care_event_csv_rows(views: Iterable[CareEventView], *, decimal_comma: bool = False) -> list[list[str]]:
    """The cells of the download, one row per event, in :data:`CARE_EVENT_CSV_COLUMNS` order.

    ``decimal_comma`` writes the numbers with a comma (the semicolon variant for Excel in a decimal-comma locale).
    """
    decimal = "," if decimal_comma else "."
    rows: list[list[str]] = []
    for view in views:
        event = view.event
        rows.append(
            [
                event.performed_at.isoformat(),
                csv_text(event.category),
                csv_text(event.summary),
                csv_text(event.location_key),
                csv_text(PLANT_SEPARATOR.join(view.plant_names)),
                csv_text(view.performed_by),
                csv_text(view.performed_for),
                csv_text(event.trigger),
                csv_text(event.reason),
                csv_text(event.product_label),
                csv_number(event.quantity, decimal=decimal),
                csv_text(event.unit),
                csv_number(event.quantity_total, decimal=decimal),
                csv_text(event.quantity_total_unit),
                csv_text(event.material),
                csv_text(event.observed_outcome),
                csv_text(event.outcome_rating),
                csv_number(len(event.photo_refs)),
                "yes" if event.superseded_by_key else "",
                event.voided_at.isoformat() if event.voided_at else "",
                csv_text(event.void_reason),
                event.redacted_at.isoformat() if event.redacted_at else "",
                csv_text(event.key),
            ]
        )
    return rows
