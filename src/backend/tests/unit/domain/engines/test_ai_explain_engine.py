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
