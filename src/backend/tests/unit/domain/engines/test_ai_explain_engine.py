"""Regression tests for :mod:`app.domain.engines.ai_explain_engine`.

The load-bearing case is that importing the module and resolving the templates
directory must never raise, regardless of how deep the source file sits. A prior
version hard-coded ``Path(__file__).resolve().parents[5]``, which held in the
repo layout but overshot the filesystem root in the container image
(``/app/app/domain/engines``) and crashed the whole backend at import with
``IndexError``.
"""

from pathlib import Path

from app.domain.engines.ai_explain_engine import (
    ExplainEngine,
    ExplainTemplate,
    _load_templates,
    _resolve_templates_dir,
)


class TestResolveTemplatesDir:
    def test_repo_layout_finds_existing_dir(self):
        """The real repo layout resolves to the actual templates directory."""
        resolved = _resolve_templates_dir()
        assert resolved.name == "explain-templates"
        assert resolved.is_dir()

    def test_container_layout_does_not_raise(self):
        """The flat container path must not raise (the old parents[5] bug)."""
        container_file = Path("/app/app/domain/engines/ai_explain_engine.py")
        # Sanity: the old fixed index really would have crashed here.
        try:
            container_file.parents[5]
            raised = False
        except IndexError:
            raised = True
        assert raised, "expected the flat layout to overshoot parents[5]"

        # The resolver walks up safely and returns a best-effort path instead.
        resolved = _resolve_templates_dir(start=container_file)
        assert resolved.name == "explain-templates"
        assert not resolved.is_dir()  # no spec/ tree at that synthetic root

    def test_missing_dir_degrades_to_empty(self, monkeypatch):
        """A missing templates directory yields an empty template set."""
        monkeypatch.setattr(
            "app.domain.engines.ai_explain_engine._TEMPLATES_DIR",
            Path("/nonexistent/spec/knowledge/explain-templates"),
        )
        _load_templates.cache_clear()
        try:
            assert _load_templates() == {}
        finally:
            _load_templates.cache_clear()


class TestExplainEngineDegradation:
    def test_build_question_returns_none_without_templates(self, monkeypatch):
        """With no templates loaded, an unknown template id yields ``None``."""
        monkeypatch.setattr(
            "app.domain.engines.ai_explain_engine._TEMPLATES_DIR",
            Path("/nonexistent/spec/knowledge/explain-templates"),
        )
        _load_templates.cache_clear()
        try:
            engine = ExplainEngine()
            assert engine.get_template("anything") is None
            assert engine.build_question("anything", "en", {}) is None
        finally:
            _load_templates.cache_clear()


class TestExplainTemplateRendering:
    """REQ-031 §4.5 — the actual "why?" question rendering (slot filling)."""

    def test_render_fills_slots_and_selects_language(self):
        """DE/EN variants are chosen by language and slots are substituted."""
        template = ExplainTemplate(
            {
                "id": "care_reminder_watering",
                "question_de": "Warum sollte ich {{plant_display}} jetzt giessen? Phase {{phase}}.",
                "question_en": "Why should I water {{plant_display}} now? Phase {{phase}}.",
            }
        )
        slots = {"plant_display": "Tomate", "phase": "vegetative"}

        assert template.render("de", slots) == "Warum sollte ich Tomate jetzt giessen? Phase vegetative."
        assert template.render("en", slots) == "Why should I water Tomate now? Phase vegetative."

    def test_render_leaves_unknown_slots_blank_and_collapses_whitespace(self):
        """Missing slots become empty and the extra whitespace is collapsed."""
        template = ExplainTemplate(
            {
                "id": "care_reminder_watering",
                "question_de": "Pflanze {{species}} in Phase {{phase}}, Substrat {{substrate}}.",
            }
        )

        rendered = template.render("de", {"species": "Cannabis sativa", "phase": "flowering"})

        assert rendered == "Pflanze Cannabis sativa in Phase flowering, Substrat ."
        assert "{{" not in rendered


class TestExplainEngineWithTemplates:
    """Rendering against the curated templates that ship in the repo layout."""

    def test_load_templates_indexes_curated_care_templates(self):
        """The shipped care templates are discoverable and keyed by id."""
        _load_templates.cache_clear()
        try:
            templates = _load_templates()
            assert "care_reminder_watering" in templates
            assert templates["care_reminder_watering"].applies_to == "care.watering"
        finally:
            _load_templates.cache_clear()

    def test_build_question_renders_known_template(self):
        """A known template id renders a slot-filled, marker-free question."""
        _load_templates.cache_clear()
        try:
            engine = ExplainEngine()
            question = engine.build_question(
                "care_reminder_watering",
                "en",
                {
                    "plant_display": "Basil",
                    "species": "Ocimum basilicum",
                    "phase": "vegetative",
                    "substrate": "coco",
                },
            )
            assert question is not None
            assert "Basil" in question
            assert "{{" not in question
        finally:
            _load_templates.cache_clear()
