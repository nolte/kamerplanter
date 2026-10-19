"""Print engine for rendering HTML templates to PDF via WeasyPrint."""

import base64
import logging
import math
import re
from io import BytesIO
from pathlib import Path
from typing import Any, NoReturn
from urllib.parse import urlsplit
from urllib.request import url2pathname

import qrcode
import qrcode.constants
import structlog
from jinja2 import Environment, FileSystemLoader
from PIL import Image
from weasyprint import HTML
from weasyprint.urls import URLFetcher, URLFetcherResponse  # type: ignore[import-untyped]

logger = structlog.get_logger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "print"

# RFC 3986 scheme: the fetcher classifies the URL itself instead of trusting the
# caller's parse, so an odd spelling (upper case, leading whitespace) cannot slip
# past the allowlist below.
_SCHEME_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.-]*):")

# The only two resource kinds a print template legitimately references:
# inline ``data:`` URIs (QR codes, server-embedded images) and files that ship
# with the templates themselves (``base_url`` points at the template tree).
# ``http``/``https``/``ftp`` are never needed, and ``file`` is confined below.
_ALLOWED_SCHEMES: frozenset[str] = frozenset({"data", "file"})

#: A log argument that is an absolute URL (``scheme:/…``) or a ``data:`` URI. An
#: exception rendered with ``%s`` (``ValueError: …``) has a space after its colon
#: and is left readable.
_URL_ARG_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:/|data:)")
_REDACTED_URL = "<url redacted>"
_WEASYPRINT_LOGGER = "weasyprint"


class _WeasyPrintUrlRedactionFilter(logging.Filter):
    """Strips URL arguments from WeasyPrint's own resource-failure records.

    WeasyPrint logs ``Failed to load image at %r: %s`` (and the stylesheet and
    font siblings) on its ``weasyprint`` logger with the URL as an argument. That
    logger carries only a ``NullHandler`` and propagates, so without this filter
    a refused URL would reach the root sink even though
    :meth:`RestrictedURLFetcher._deny` keeps it out of the structlog event.
    Installed once per process by :class:`PrintEngine`; a logger-level filter
    sees exactly the records logged on ``weasyprint`` itself, which is where
    every ``LOGGER.error`` in WeasyPrint lands.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple):
            record.args = tuple(self._redact(arg) for arg in args)
        elif isinstance(args, dict):
            record.args = {key: self._redact(value) for key, value in args.items()}
        return True

    @staticmethod
    def _redact(value: object) -> object:
        if isinstance(value, str) and _URL_ARG_RE.match(value):
            return _REDACTED_URL
        return value


_WEASYPRINT_URL_FILTER = _WeasyPrintUrlRedactionFilter()


class PrintResourceDeniedError(ValueError):
    """A print template referenced a resource outside the fetch allowlist.

    Raised from :meth:`RestrictedURLFetcher.fetch`; WeasyPrint catches it, drops
    the resource and keeps rendering (GP-NFR-052 (a)). It deliberately does not
    inherit from ``KamerplanterError`` — it never crosses the engine boundary,
    and its message must stay free of the offending URL because WeasyPrint
    copies ``str(exc)`` into its own warning.
    """


class RestrictedURLFetcher(URLFetcher):  # type: ignore[misc]
    """WeasyPrint URL fetcher that resolves only ``data:`` URIs and template-tree files.

    Two gates, both inside this class so a template cannot route around them:

    1. ``allowed_protocols`` on the base class refuses every scheme other than
       ``data`` and ``file`` by name.
    2. :meth:`fetch` resolves a ``file:`` URL to a real path and refuses it unless
       it lies below the template directory (symlinks and ``..`` are resolved
       first), and refuses any ``file:`` URL with a host part.

    A refusal raises :class:`PrintResourceDeniedError` and logs
    ``print_engine.url_fetch_denied`` with the scheme and the reason only — the
    URL itself is user-controlled content and stays out of this event and out
    of the exception text (GP-NFR-052 (a), REQ-032 v1.2 §8). WeasyPrint then
    logs its own ``Failed to load … at %r`` record; :class:`PrintEngine` installs
    :class:`_WeasyPrintUrlRedactionFilter` so that record carries no URL either.

    A ``@font-face`` ``src: local(...)`` resolves to a fontconfig system path and
    is refused as ``path_outside_templates`` — bundle fonts below the template
    directory instead.
    """

    def __init__(self, templates_dir: Path) -> None:
        super().__init__(allowed_protocols=tuple(sorted(_ALLOWED_SCHEMES)), allow_redirects=False)
        self._templates_dir = templates_dir.resolve()

    @property
    def templates_dir(self) -> Path:
        """The resolved directory below which ``file:`` fetches are allowed."""
        return self._templates_dir

    def fetch(self, url: str, headers: dict[str, str] | None = None) -> URLFetcherResponse:
        """Fetch ``url`` if it is a ``data:`` URI or a file below the template directory.

        Raises:
            PrintResourceDeniedError: for every other URL, before any socket or
                file is opened.
        """
        match = _SCHEME_RE.match(url)
        scheme = match[1].lower() if match else None
        if scheme not in _ALLOWED_SCHEMES:
            self._deny(scheme, "scheme_not_allowed")

        if scheme == "file":
            try:
                parts = urlsplit(url)
                has_host = bool(parts.netloc)
                # ``url2pathname`` percent-decodes exactly once, as the opener's
                # ``FileHandler`` does, so the path checked is the path opened.
                path = Path(url2pathname(parts.path)).resolve()
            except ValueError, OSError:
                # Malformed IPv6 host, a UNC authority inside the path, an
                # embedded NUL byte: refuse through the same audited path.
                self._deny(scheme, "path_unresolvable")
            if has_host:
                self._deny(scheme, "file_host_not_allowed")
            if not path.is_relative_to(self._templates_dir):
                self._deny(scheme, "path_outside_templates")

        return super().fetch(url, headers)

    @staticmethod
    def _deny(scheme: str | None, reason: str) -> NoReturn:
        logger.warning(
            "print_engine.url_fetch_denied",
            scheme=scheme or "none",
            reason=reason,
        )
        raise PrintResourceDeniedError(f"print resource denied: {reason} (scheme={scheme or 'none'})")


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
        "garden_plan_title": "Gartenplan",
        "garden_plan_scale": "Maßstab",
        "garden_plan_paper": "Format",
        "garden_plan_revision": "Stand (Revision)",
        "garden_plan_a3_hint": "Mit A3 wäre ein feinerer Maßstab möglich.",
        "garden_plan_bed_list": "Beetliste",
        "garden_plan_bed_name": "Name",
        "garden_plan_bed_area": "Fläche (m²)",
        "garden_plan_bed_status": "Status",
        "garden_plan_bed_sun": "Sonne",
        "bed_status_planned": "geplant",
        "bed_status_active": "aktiv",
        "bed_status_retired": "stillgelegt",
        "sun_exposure_full_sun": "Vollsonne",
        "sun_exposure_partial_shade": "Halbschatten",
        "sun_exposure_shade": "Schatten",
        "sun_exposure_deep_shade": "Tiefschatten",
        "sun_exposure_unknown": "unbekannt",
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
        "garden_plan_title": "Garden plan",
        "garden_plan_scale": "Scale",
        "garden_plan_paper": "Paper",
        "garden_plan_revision": "Revision",
        "garden_plan_a3_hint": "A3 would allow a finer scale.",
        "garden_plan_bed_list": "Bed list",
        "garden_plan_bed_name": "Name",
        "garden_plan_bed_area": "Area (m²)",
        "garden_plan_bed_status": "Status",
        "garden_plan_bed_sun": "Sun",
        "bed_status_planned": "planned",
        "bed_status_active": "active",
        "bed_status_retired": "retired",
        "sun_exposure_full_sun": "full sun",
        "sun_exposure_partial_shade": "partial shade",
        "sun_exposure_shade": "shade",
        "sun_exposure_deep_shade": "deep shade",
        "sun_exposure_unknown": "unknown",
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
        # REQ-022 v2.5 outdoor + overwintering reminder types
        "deadheading": "Verbl\u00fchtes entfernen",
        "tuber_dig": "Knollen ausgraben",
        "storage_check": "Lagerkontrolle",
        "spring_uncover": "Winterschutz abnehmen",
        "winter_protection": "Winterschutz anbringen",
        # REQ-047 season & overwintering automation
        "dormancy_health_check": "Winterruhe-Kontrolle",
        "quarter_climate_check": "Winterquartier-Klima prüfen",
    },
    "en": {
        "watering": "Watering",
        "fertilizing": "Fertilizing",
        "repotting": "Repotting",
        "pest_check": "Pest check",
        "location_check": "Location check",
        "humidity_check": "Humidity check",
        "deadheading": "Deadheading",
        "tuber_dig": "Lift tubers",
        "storage_check": "Storage check",
        "spring_uncover": "Remove winter protection",
        "winter_protection": "Apply winter protection",
        # REQ-047 season & overwintering automation
        "dormancy_health_check": "Dormancy check",
        "quarter_climate_check": "Winter-quarter climate check",
    },
}


class PrintEngine:
    """Renders HTML templates to PDF bytes using Jinja2 and WeasyPrint."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._templates_dir = (templates_dir or TEMPLATES_DIR).resolve()
        # Autoescape for every template the engine renders, whatever its suffix
        # and including string templates (GP-NFR-052 (d)) — not
        # ``select_autoescape``, whose per-extension opt-in is the permissive
        # default this engine must not have.
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=True,
        )
        # Built here, not injected: a caller-supplied fetcher would be a way to
        # re-open the http/file hole this class exists to close.
        self._url_fetcher = RestrictedURLFetcher(self._templates_dir)
        # ``addFilter`` is a no-op for an instance already present, so every
        # engine may install it and the process ends up with exactly one.
        logging.getLogger(_WEASYPRINT_LOGGER).addFilter(_WEASYPRINT_URL_FILTER)

    @property
    def url_fetcher(self) -> RestrictedURLFetcher:
        """The fetcher every ``render_pdf`` call hands to WeasyPrint (read-only)."""
        return self._url_fetcher

    def render_html(self, template_name: str, context: dict[str, Any], locale: str = "de") -> str:
        """Render a print template to its HTML markup (the input to the PDF step).

        Args:
            template_name: Name of the Jinja2 template file (e.g. 'nutrient_plan.html').
            context: Template context variables.
            locale: Locale for labels ('de' or 'en'). Defaults to 'de'.

        Returns:
            Rendered HTML with every context value autoescaped.
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
        return template.render(**full_context)

    def render_pdf(self, template_name: str, context: dict[str, Any], locale: str = "de") -> bytes:
        """Render an HTML template to PDF bytes.

        Args:
            template_name: Name of the Jinja2 template file (e.g. 'nutrient_plan.html').
            context: Template context variables.
            locale: Locale for labels ('de' or 'en'). Defaults to 'de'.

        Returns:
            PDF file content as bytes.
        """
        html_content = self.render_html(template_name, context, locale)

        logger.info(
            "print_engine.render_pdf",
            template=template_name,
            locale=locale,
        )

        html = HTML(
            string=html_content,
            base_url=str(self._templates_dir),
            url_fetcher=self._url_fetcher,
        )
        pdf: bytes = html.write_pdf()
        return pdf

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

        qr_image = qr.make_image(fill_color="black", back_color="white")
        # Resize to target pixel dimensions. The resized value is a plain Pillow
        # image; the annotation keeps `img.save(...)` below from reading as an
        # untyped receiver of the repository write vocabulary (#1443 detector).
        img: Image.Image = qr_image.resize((target_pixels, target_pixels))

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
