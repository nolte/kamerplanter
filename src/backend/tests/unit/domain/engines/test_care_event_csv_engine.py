"""WP 8.4 (#2647) — the care log as CSV rows: flat GP-FR-100 fields, display names, hardened text cells."""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.engines.care_event_csv_engine import CARE_EVENT_CSV_COLUMNS, care_event_csv_rows
from app.domain.models.care_event import CareEvent, CareEventView

AT = datetime(2026, 6, 1, 8, 30, tzinfo=UTC)


def _view(**fields) -> CareEventView:  # type: ignore[no-untyped-def]
    stored = {
        "_key": "ce1",
        "tenant_key": "t1",
        "site_key": "S1",
        "location_key": "L1",
        "category": "watering",
        "summary": "Watered",
        "performed_at": AT,
        "performed_by_user_key": "u_secret_key",
    } | {k: v for k, v in fields.items() if k not in ("performed_by", "plant_names")}
    event = CareEvent(**stored)
    return CareEventView(
        event=event, performed_by=fields.get("performed_by", "Sabine"), plant_names=fields.get("plant_names", [])
    )


def _row(view: CareEventView) -> dict[str, str]:
    return dict(zip(CARE_EVENT_CSV_COLUMNS, care_event_csv_rows([view])[0], strict=True))


def test_the_row_has_one_cell_per_column() -> None:
    assert len(care_event_csv_rows([_view()])[0]) == len(CARE_EVENT_CSV_COLUMNS)


def test_the_flat_fields_and_the_display_name_are_exported() -> None:
    row = _row(_view(quantity=2.5, unit="l", plant_names=["Basil", "Mint"]))

    assert (row["performed_at"], row["category"], row["performed_by"]) == (AT.isoformat(), "watering", "Sabine")
    assert (row["quantity"], row["unit"], row["plant_names"]) == ("2.5", "l", "Basil | Mint")
    assert row["key"] == "ce1"


def test_no_account_key_leaves_the_server() -> None:
    cells = " ".join(care_event_csv_rows([_view()])[0])

    assert "u_secret_key" not in cells


def test_a_formula_in_a_free_text_is_neutralised_and_a_negative_number_is_not() -> None:
    row = _row(_view(summary="=HYPERLINK(1)", reason="+cmd", observed_outcome="@x", quantity=-1.5, unit="l"))

    assert (row["summary"], row["reason"], row["observed_outcome"]) == ("'=HYPERLINK(1)", "'+cmd", "'@x")
    assert row["quantity"] == "-1.5"


def test_a_formula_in_the_display_name_is_neutralised() -> None:
    assert _row(_view(performed_by="=evil()"))["performed_by"] == "'=evil()"


def test_superseded_voided_and_redacted_entries_say_so() -> None:
    row = _row(_view(superseded_by_key="ce2", voided_at=AT, void_reason="undo", redacted_at=AT))

    assert (row["superseded"], row["voided_at"], row["void_reason"], row["redacted_at"]) == (
        "yes",
        AT.isoformat(),
        "undo",
        AT.isoformat(),
    )


def test_the_photos_are_counted_not_listed() -> None:
    assert _row(_view(photo_refs=["a1", "a2"]))["photo_count"] == "2"


def test_the_excel_variant_writes_a_decimal_comma_and_the_default_a_point() -> None:
    view = _view(quantity=2.5, unit="l", quantity_total=10.25, quantity_total_unit="l")

    default = dict(zip(CARE_EVENT_CSV_COLUMNS, care_event_csv_rows([view])[0], strict=True))
    excel = dict(zip(CARE_EVENT_CSV_COLUMNS, care_event_csv_rows([view], decimal_comma=True)[0], strict=True))

    assert (default["quantity"], default["quantity_total"]) == ("2.5", "10.25")
    assert (excel["quantity"], excel["quantity_total"]) == ("2,5", "10,25")
