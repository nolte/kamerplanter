"""Print engine for rendering HTML templates to PDF via WeasyPrint."""

import base64
import math
from io import BytesIO
from pathlib import Path

import qrcode
import qrcode.constants
import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

logger = structlog.get_logger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "print"

# ── Locale-specific labels ──────────────────────────────────────────

LABELS: dict[str, dict[str, str]] = {
    "de": {
        "author": "Autor",
        "generated": "Erstellt am",
        "substrate": "Substrat",
        "water_config": "Wasser-Konfiguration",
        "ro_percent": "RO-Anteil",
        "phase_overview": "Phasen\u00fcbersicht",
        "phase": "Phase",
        "weeks": "Wochen",
        "target_ec": "Ziel-EC",
        "product": "Produkt",
        "optional": "Optional",
        "yes": "Ja",
        "no": "Nein",
        "additional_notes": "Weitere Hinweise",
        "flushing": "Flushing",
        "care_checklist_title": "Pflege-Checkliste",
        "date": "Datum",
        "no_entries": "Keine Pflegeaufgaben f\u00e4llig.",
        "plant": "Pflanze",
        "species": "Art",
        "reminder_type": "Typ",
        "due_date": "F\u00e4llig am",
        "location": "Standort",
        "notes_section": "Notizen",
        "handwritten_notes_hint": "Platz f\u00fcr handschriftliche Notizen",
        "overdue": "\u00dcberf\u00e4llig",
        "due_today": "Heute f\u00e4llig",
        "upcoming": "Demnächst",
        "plant_label_title": "Pflanzen-Infokarten",
        "planted": "Gepflanzt",
        "family": "Familie",
        "cultivar": "Sorte",
        "note": "Hinweis",
        "cut_marks_hint": "Entlang der Linien ausschneiden",
    },
    "en": {
        "author": "Author",
        "generated": "Generated",
        "substrate": "Substrate",
        "water_config": "Water configuration",
        "ro_percent": "RO percentage",
        "phase_overview": "Phase overview",
        "phase": "Phase",
        "weeks": "Weeks",
        "target_ec": "Target EC",
        "product": "Product",
        "optional": "Optional",
        "yes": "Yes",
        "no": "No",
        "additional_notes": "Additional notes",
        "flushing": "Flushing",
        "care_checklist_title": "Care checklist",
        "date": "Date",
        "no_entries": "No care tasks due.",
        "plant": "Plant",
        "species": "Species",
        "reminder_type": "Type",
        "due_date": "Due date",
        "location": "Location",
        "notes_section": "Notes",
        "handwritten_notes_hint": "Space for handwritten notes",
        "overdue": "Overdue",
        "due_today": "Due today",
        "upcoming": "Upcoming",
        "plant_label_title": "Plant info cards",
        "planted": "Planted",
        "family": "Family",
        "cultivar": "Cultivar",
        "note": "Note",
        "cut_marks_hint": "Cut along the lines",
    },
}

REMINDER_TYPE_LABELS: dict[str, dict[str, str]] = {
    "de": {
        "watering": "Gie\u00dfen",
        "fertilizing": "D\u00fcngen",
        "repotting": "Umtopfen",
        "pest_check": "Sch\u00e4dlingskontrolle",
        "location_check": "Standortkontrolle",
        "humidity_check": "Feuchtigkeitskontrolle",
    },
    "en": {
        "watering": "Watering",
        "fertilizing": "Fertilizing",
        "repotting": "Repotting",
        "pest_check": "Pest check",
        "location_check": "Location check",
        "humidity_check": "Humidity check",
    },
}


class PrintEngine:
    """Renders HTML templates to PDF bytes using Jinja2 and WeasyPrint."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._templates_dir = templates_dir or TEMPLATES_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=select_autoescape(["html"]),
        )

    def render_pdf(self, template_name: str, context: dict, locale: str = "de") -> bytes:
        """Render an HTML template to PDF bytes.

        Args:
            template_name: Name of the Jinja2 template file (e.g. 'nutrient_plan.html').
            context: Template context variables.
            locale: Locale for labels ('de' or 'en'). Defaults to 'de'.

        Returns:
            PDF file content as bytes.
        """
        labels = LABELS.get(locale, LABELS["de"])
        reminder_labels = REMINDER_TYPE_LABELS.get(locale, REMINDER_TYPE_LABELS["de"])

        full_context = {
            "labels": labels,
            "reminder_type_labels": reminder_labels,
            "locale": locale,
            **context,
        }

        template = self._env.get_template(template_name)
        html_content = template.render(**full_context)

        logger.info(
            "print_engine.render_pdf",
            template=template_name,
            locale=locale,
        )

        html = HTML(string=html_content, base_url=str(self._templates_dir))
        return html.write_pdf()

    @staticmethod
    def generate_qr_code_base64(url: str, size_mm: int = 25) -> str:
        """Generate a QR code as a base64-encoded PNG data URI.

        Args:
            url: The URL to encode in the QR code.
            size_mm: Desired QR code size in millimeters (at 300 DPI).

        Returns:
            Data URI string: ``data:image/png;base64,<b64>``.
        """
        # Calculate pixel size from mm at 300 DPI
        target_pixels = int(math.ceil(size_mm * 300 / 25.4))

        qr = qrcode.QRCode(
            version=None,  # auto-detect smallest version
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        # Resize to target pixel dimensions
        img = img.resize((target_pixels, target_pixels))

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("ascii")

        logger.debug(
            "print_engine.generate_qr_code",
            url=url,
            size_mm=size_mm,
            target_pixels=target_pixels,
        )

        return f"data:image/png;base64,{b64}"
