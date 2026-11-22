"""Print hardening (REQ-053 GP-NFR-052 (a)/(d), GP-ACC-045 parts a/d, REQ-032 v1.2 §8).

Two layers, both measured through the production path:

* ``RestrictedURLFetcher`` refuses every URL that is not a ``data:`` URI or a file
  below the template directory — before any socket or file is opened — and logs
  the refusal without the URL.
* ``PrintEngine`` hands exactly that fetcher to WeasyPrint and autoescapes every
  template, so a hostile bed/plant name becomes text, never an element, and never
  a fetch.

The opener spy below replaces ``urllib.request.OpenerDirector.open`` — the one
method every real fetch in WeasyPrint 70 funnels through — so "no fetch happened"
is asserted on the thing that would have opened the socket, not on a counter the
code under test maintains itself.
"""

import base64
import logging
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import OpenerDirector, Request, url2pathname

import pytest
from structlog.testing import capture_logs
from weasyprint.urls import URLFetcher

from app.domain.engines.print_engine import (
    TEMPLATES_DIR,
    PrintEngine,
    PrintResourceDeniedError,
    RestrictedURLFetcher,
)

HOSTILE_IMAGE_NAME = '"><image href="http://169.254.169.254/"/>'
HOSTILE_FILE_NAME = "file:///etc/passwd"
HOSTILE_NAMES = (HOSTILE_IMAGE_NAME, HOSTILE_FILE_NAME)
# What each name must look like once Jinja has escaped it into text.
ESCAPED_TEXT = {
    HOSTILE_IMAGE_NAME: "&#34;&gt;&lt;image href=&#34;http://169.254.169.254/&#34;/&gt;",
    HOSTILE_FILE_NAME: HOSTILE_FILE_NAME,
}

METADATA_HOST = "169.254.169.254"
QR_DATA_URI = PrintEngine.generate_qr_code_base64("https://kamerplanter.example/t/g/plants/p1", size_mm=20)


@pytest.fixture
def opener_calls(monkeypatch, tmp_path: Path) -> list[str]:
    """Record every URL that reaches ``OpenerDirector.open``; serve only what a test may own.

    ``data:`` URIs and files below this test's ``tmp_path`` or the shipped template
    directory are served for real (the QR code in ``plant_label.html`` and the
    in-tree fixtures need them); anything else is answered with an ``OSError`` so
    a regression can never turn this test into a live request against the
    metadata host or a read of ``/etc/passwd``.
    """
    calls: list[str] = []
    original = OpenerDirector.open
    served_roots = (tmp_path.resolve(), TEMPLATES_DIR)

    def harness_may_serve(full_url: str) -> bool:
        if full_url.startswith("data:"):
            return True
        if full_url.startswith("file:"):
            path = Path(url2pathname(urlsplit(full_url).path)).resolve()
            return any(path.is_relative_to(root) for root in served_roots)
        return False

    def spy(self, url, data=None, timeout=None):
        full_url = url.full_url if isinstance(url, Request) else url
        calls.append(full_url)
        if not harness_may_serve(full_url):
            raise OSError("access blocked by test harness")
        return original(self, url, data, timeout)

    monkeypatch.setattr(OpenerDirector, "open", spy)
    return calls


@pytest.fixture
def fetcher(tmp_path: Path) -> RestrictedURLFetcher:
    (tmp_path / "base.html").write_text("<html><body>in-tree</body></html>")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "logo.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    return RestrictedURLFetcher(tmp_path)


class TestRestrictedURLFetcher:
    @pytest.mark.parametrize(
        "url",
        [
            f"http://{METADATA_HOST}/",
            f"HTTP://{METADATA_HOST}/latest/meta-data/",
            f"https://{METADATA_HOST}/",
            "ftp://example.invalid/x",
            "gopher://example.invalid/",
            "javascript:alert(1)",
            "not-a-url",
        ],
    )
    def test_non_data_non_file_scheme_is_refused_without_opening(self, fetcher, opener_calls, url):
        with pytest.raises(PrintResourceDeniedError):
            fetcher.fetch(url)

        assert opener_calls == []

    @pytest.mark.parametrize(
        "path_url",
        [
            HOSTILE_FILE_NAME,
            "FILE:///etc/passwd",
            "file:///etc/hostname",
            "file://localhost/etc/passwd",
            "file:////evil.invalid/share/x",
        ],
    )
    def test_file_outside_template_tree_is_refused_without_opening(self, fetcher, opener_calls, path_url):
        with pytest.raises(PrintResourceDeniedError):
            fetcher.fetch(path_url)

        assert opener_calls == []

    @pytest.mark.parametrize(
        "traversal",
        [
            "/sub/../../../../../../etc/passwd",
            # Percent-encoded dots: the opener's FileHandler decodes them once,
            # so the check must decode them too (``url2pathname``).
            "/sub/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd",
            "/sub/%2E%2E/%2E%2E/%2E%2E/%2E%2E/%2E%2E/etc/passwd",
        ],
    )
    def test_traversal_below_template_tree_is_refused(self, fetcher, opener_calls, tmp_path, traversal):
        with pytest.raises(PrintResourceDeniedError):
            fetcher.fetch(tmp_path.as_uri() + traversal)

        assert opener_calls == []

    def test_unresolvable_path_is_refused_through_the_audited_path(self, fetcher, opener_calls, tmp_path):
        with capture_logs() as logs, pytest.raises(PrintResourceDeniedError):
            fetcher.fetch(tmp_path.as_uri() + "/base%00.html")

        assert opener_calls == []
        assert [entry["reason"] for entry in logs if entry["event"] == "print_engine.url_fetch_denied"] == [
            "path_unresolvable"
        ]

    def test_symlink_escaping_the_template_tree_is_refused(self, fetcher, opener_calls, tmp_path):
        outside = tmp_path.parent / "outside-secret.txt"
        outside.write_text("secret")
        (tmp_path / "link.txt").symlink_to(outside)

        with pytest.raises(PrintResourceDeniedError):
            fetcher.fetch((tmp_path / "link.txt").as_uri())

        assert opener_calls == []

    def test_file_with_host_part_is_refused_even_inside_the_tree(self, fetcher, opener_calls, tmp_path):
        with_host = "file://localhost" + str(tmp_path / "base.html")

        with pytest.raises(PrintResourceDeniedError):
            fetcher.fetch(with_host)

        assert opener_calls == []

    def test_data_uri_is_served(self, fetcher):
        response = fetcher.fetch("data:text/plain;base64,aGk=")

        assert response.read() == b"hi"

    @pytest.mark.parametrize("relative", ["base.html", "sub/logo.svg"])
    def test_file_below_template_tree_is_served(self, fetcher, tmp_path, relative):
        response = fetcher.fetch((tmp_path / relative).as_uri())

        assert len(response.read()) > 0

    def test_query_and_fragment_do_not_defeat_the_path_check(self, fetcher, tmp_path):
        # WeasyPrint strips ``?``/``#`` from file URLs before opening; the path
        # check must see the same path the opener would.
        response = fetcher.fetch((tmp_path / "base.html").as_uri() + "?x=1#top")

        assert b"in-tree" in response.read()

    @pytest.mark.parametrize(
        ("url", "scheme", "reason"),
        [
            (f"http://{METADATA_HOST}/", "http", "scheme_not_allowed"),
            (HOSTILE_FILE_NAME, "file", "path_outside_templates"),
            ("file://localhost/etc/passwd", "file", "file_host_not_allowed"),
            ("not-a-url", "none", "scheme_not_allowed"),
        ],
    )
    def test_refusal_is_logged_and_raised_without_the_url(self, fetcher, url, scheme, reason):
        with capture_logs() as logs, pytest.raises(PrintResourceDeniedError) as excinfo:
            fetcher.fetch(url)

        denied = [entry for entry in logs if entry["event"] == "print_engine.url_fetch_denied"]
        assert len(denied) == 1
        flattened = " ".join(str(value) for value in denied[0].values())
        for leak in (METADATA_HOST, "/etc/passwd", url):
            assert leak not in flattened
            assert leak not in str(excinfo.value)
        assert denied[0]["scheme"] == scheme
        assert denied[0]["reason"] == reason

    def test_base_class_gate_also_refuses_http(self, fetcher, opener_calls):
        """The ``allowed_protocols`` gate holds even if the subclass ``fetch`` is bypassed."""
        with pytest.raises(ValueError, match="disallowed protocol"):
            URLFetcher.fetch(fetcher, f"http://{METADATA_HOST}/")

        assert opener_calls == []


@pytest.fixture
def engine() -> PrintEngine:
    return PrintEngine()


@pytest.fixture
def fetch_calls(engine, monkeypatch) -> list[str]:
    """Record every URL WeasyPrint asks the engine's own fetcher for."""
    calls: list[str] = []
    original = engine.url_fetcher.fetch

    def spy(url, headers=None):
        calls.append(url)
        return original(url, headers)

    monkeypatch.setattr(engine.url_fetcher, "fetch", spy)
    return calls


def _care_checklist_context(plant_name: str) -> dict:
    entry = {
        "plant_key": "p1",
        "plant_name": plant_name,
        "species_name": "Ocimum basilicum",
        "reminder_type": "watering",
        "urgency": "overdue",
        "due_date": "2026-10-15",
        "location": None,
    }
    return {
        "generated_date": "2026-10-16 05:00",
        "target_date": None,
        "entries": [entry],
        "urgency_groups": [{"urgency": "overdue", "label": "Überfällig", "entries": [entry]}],
    }


def _plant_label_context(name: str) -> dict:
    return {
        "cards": [
            {
                "name": name,
                "scientific_name": "Ocimum basilicum",
                "family": "",
                "cultivar": "Genovese",
                "planted_date": "01.05.2026",
                "current_phase": "vegetative",
                "location": name,
                "note": name,
                "qr_data_uri": QR_DATA_URI,
            }
        ],
        "fields": ["scientific_name", "cultivar", "planted_date", "phase", "location", "note"],
        "layout": "grid",
        "qr_size_mm": 20,
        "generated_date": "2026-10-16 05:00",
    }


def _nutrient_plan_context(plan_name: str) -> dict:
    return {
        "plan_name": plan_name,
        "description": plan_name,
        "author": plan_name,
        "substrate_type": "coco",
        "generated_date": "2026-10-16 05:00",
        "phases": [
            {
                "phase_name": "vegetative",
                "week_start": 1,
                "week_end": 4,
                "target_ec_ms": 1.2,
                "npk_ratio": [3, 1, 2],
                "calcium_ppm": 120,
                "magnesium_ppm": 40,
                "sulfur_ppm": 50,
                "notes": plan_name,
                "channels": [
                    {
                        "channel_id": "root",
                        "label": "Root",
                        "application_method": "root",
                        "target_ec_ms": 1.2,
                        "target_ph": 5.8,
                        "dosages": [
                            {"product_name": plan_name, "ml_per_liter": 2.0, "optional": False, "mixing_order": 1},
                        ],
                    }
                ],
            }
        ],
        "water_config": {"ro_percent": 50, "base_ec_note": plan_name},
        "flushing_notes": plan_name,
        "calmag_notes": plan_name,
    }


TEMPLATE_CONTEXTS = {
    "care_checklist.html": _care_checklist_context,
    "plant_label.html": _plant_label_context,
    "nutrient_plan.html": _nutrient_plan_context,
}


class TestHostileNamesInExistingTemplates:
    """GP-ACC-045 (a)/(d) for the three templates that exist today."""

    @pytest.mark.parametrize("template_name", sorted(TEMPLATE_CONTEXTS))
    @pytest.mark.parametrize("hostile", HOSTILE_NAMES)
    def test_hostile_name_becomes_text_not_an_element(self, engine, template_name, hostile):
        html = engine.render_html(template_name, TEMPLATE_CONTEXTS[template_name](hostile))

        # The name survives as visible text — escaped where it carries markup
        # characters, verbatim where it does not (``file:///etc/passwd`` is plain
        # text; the fetcher test below is what keeps it from becoming a read).
        assert ESCAPED_TEXT[hostile] in html
        assert "<image" not in html
        assert re.search(r"""(src|href)\s*=\s*["']?file:""", html) is None
        assert "url(file:" not in html
        if hostile == HOSTILE_IMAGE_NAME:
            assert hostile not in html

    @pytest.mark.parametrize("template_name", sorted(TEMPLATE_CONTEXTS))
    @pytest.mark.parametrize("hostile", HOSTILE_NAMES)
    def test_hostile_name_triggers_no_fetch(self, engine, fetch_calls, opener_calls, template_name, hostile):
        pdf = engine.render_pdf(template_name, TEMPLATE_CONTEXTS[template_name](hostile))

        assert pdf[:5] == b"%PDF-"
        assert all(url.startswith("data:") for url in fetch_calls), fetch_calls
        assert all(url.startswith("data:") for url in opener_calls), opener_calls
        if template_name == "plant_label.html":
            # The one shipped template that fetches at all: proves the spy sits
            # on the fetcher WeasyPrint really uses, not on an idle sibling.
            assert QR_DATA_URI in fetch_calls
            assert QR_DATA_URI in opener_calls


class TestEngineHandsWeasyPrintTheRestrictedFetcher:
    """Defence in depth: even markup that *does* carry a hostile URL never opens it."""

    @pytest.fixture
    def leaky_engine(self, tmp_path: Path) -> PrintEngine:
        # A template author marking user input ``|safe`` is the realistic way an
        # element reaches WeasyPrint; the fetcher is the gate behind that mistake.
        (tmp_path / "leaky.html").write_text(
            '<html><body><h1>{{ title }}</h1><img src="{{ src | safe }}" alt="x"></body></html>'
        )
        # Every other way a stylesheet, a font or a nested SVG can name a URL.
        (tmp_path / "evil.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="10" height="10"><image href="{{ src | safe }}" width="10" height="10"/></svg>'
        )
        return PrintEngine(templates_dir=tmp_path)

    @pytest.fixture
    def fetcher_calls(self, leaky_engine, monkeypatch) -> list[str]:
        calls: list[str] = []
        original = leaky_engine.url_fetcher.fetch

        def spy(url, headers=None):
            calls.append(url)
            return original(url, headers)

        monkeypatch.setattr(leaky_engine.url_fetcher, "fetch", spy)
        return calls

    @pytest.mark.parametrize("src", [f"http://{METADATA_HOST}/", HOSTILE_FILE_NAME])
    def test_hostile_img_src_is_refused_before_any_open(self, leaky_engine, fetcher_calls, opener_calls, src):
        with capture_logs() as logs:
            pdf = leaky_engine.render_pdf("leaky.html", {"title": "t", "src": src})

        assert pdf[:5] == b"%PDF-"
        assert fetcher_calls == [src], "WeasyPrint must route the fetch through the engine's fetcher"
        assert opener_calls == []
        assert any(entry["event"] == "print_engine.url_fetch_denied" for entry in logs)

    @pytest.mark.parametrize(
        ("body", "src"),
        [
            pytest.param('<link rel="stylesheet" href="{{ src | safe }}">', f"http://{METADATA_HOST}/x.css", id="link"),
            pytest.param(
                "<style>@import url('{{ src | safe }}');</style>", f"http://{METADATA_HOST}/x.css", id="import"
            ),
            pytest.param(
                "<style>body{background:url('{{ src | safe }}')}</style><p>x</p>", HOSTILE_FILE_NAME, id="css-url"
            ),
            pytest.param(
                "<style>@font-face{font-family:evil;src:url('{{ src | safe }}')}</style>"
                '<p style="font-family:evil">x</p>',
                f"http://{METADATA_HOST}/f.ttf",
                id="font-face",
            ),
        ],
    )
    def test_hostile_stylesheet_font_and_css_urls_are_refused(
        self, leaky_engine, fetcher_calls, opener_calls, tmp_path, body, src
    ):
        (tmp_path / "styled.html").write_text(f"<html><head></head><body>{body}</body></html>")

        with capture_logs() as logs:
            pdf = leaky_engine.render_pdf("styled.html", {"src": src})

        assert pdf[:5] == b"%PDF-"
        assert src in fetcher_calls, fetcher_calls
        assert opener_calls == []
        assert any(entry["event"] == "print_engine.url_fetch_denied" for entry in logs)

    def test_image_inside_an_in_tree_svg_is_refused(self, leaky_engine, fetcher_calls, opener_calls, tmp_path):
        hostile = f"http://{METADATA_HOST}/"
        # The SVG itself is in the tree (served); the <image> it carries is not.
        svg = leaky_engine.render_html("evil.svg", {"src": hostile})
        (tmp_path / "rendered.svg").write_text(svg)
        (tmp_path / "nested.html").write_text('<html><body><img src="rendered.svg" alt="x"></body></html>')

        with capture_logs() as logs:
            pdf = leaky_engine.render_pdf("nested.html", {})

        svg_uri = (tmp_path.resolve() / "rendered.svg").as_uri()
        assert pdf[:5] == b"%PDF-"
        assert fetcher_calls == [svg_uri, hostile]
        assert opener_calls == [svg_uri]
        assert any(entry["event"] == "print_engine.url_fetch_denied" for entry in logs)

    @pytest.mark.parametrize("src", [f"http://{METADATA_HOST}/", HOSTILE_FILE_NAME])
    def test_weasyprints_own_failure_record_carries_no_url(self, leaky_engine, opener_calls, caplog, src):
        """WeasyPrint logs ``Failed to load image at %r`` itself; the engine's filter blanks the URL."""
        with caplog.at_level(logging.DEBUG, logger="weasyprint"):
            leaky_engine.render_pdf("leaky.html", {"title": "t", "src": src})

        failures = [
            record for record in caplog.records if record.name == "weasyprint" and "Failed to load" in record.msg
        ]
        assert failures, "the record this test guards against must exist, or it guards nothing"
        assert "Failed to load image at '<url redacted>'" in caplog.text
        for leak in (METADATA_HOST, "/etc/passwd"):
            assert leak not in caplog.text

    def test_in_tree_file_still_resolves_relative_to_the_template_directory(self, tmp_path, opener_calls):
        (tmp_path / "logo.png").write_bytes(_one_pixel_png())
        (tmp_path / "rel.html").write_text('<html><body><img src="logo.png" alt="logo"></body></html>')
        engine = PrintEngine(templates_dir=tmp_path)

        pdf = engine.render_pdf("rel.html", {})

        assert pdf[:5] == b"%PDF-"
        assert opener_calls == [(tmp_path.resolve() / "logo.png").as_uri()]


class TestAutoescapeIsPinned:
    def test_template_without_html_suffix_is_still_escaped(self, tmp_path):
        (tmp_path / "label.txt").write_text("<p>{{ name }}</p>")
        engine = PrintEngine(templates_dir=tmp_path)

        html = engine.render_html("label.txt", {"name": HOSTILE_IMAGE_NAME})

        assert "<image" not in html
        assert "&lt;image" in html

    @pytest.mark.parametrize("template_name", sorted(TEMPLATE_CONTEXTS))
    def test_shipped_templates_are_autoescaped(self, engine, template_name):
        html = engine.render_html(template_name, TEMPLATE_CONTEXTS[template_name]("<b>bold</b>"))

        assert "<b>bold</b>" not in html
        assert "&lt;b&gt;bold&lt;/b&gt;" in html


class TestExistingTemplatesStillRender:
    def test_default_engine_confines_file_fetches_to_the_shipped_template_directory(self, engine):
        assert engine.url_fetcher.templates_dir == TEMPLATES_DIR

    @pytest.mark.parametrize("locale", ["de", "en"])
    @pytest.mark.parametrize("template_name", sorted(TEMPLATE_CONTEXTS))
    def test_fixture_renders_to_pdf(self, engine, template_name, locale):
        pdf = engine.render_pdf(template_name, TEMPLATE_CONTEXTS[template_name]("Basilikum"), locale=locale)

        assert pdf[:5] == b"%PDF-"


def _one_pixel_png() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
