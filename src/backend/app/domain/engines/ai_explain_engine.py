"""REQ-031 §4.5 — ``ExplainEngine`` for "why?" answers.

Loads curated question templates from ``spec/knowledge/explain-templates/*.yaml``,
fills their slots from the backend context and asks the Knowledge Service. Curated
templates keep the LLM input compact and deterministic instead of free text.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import structlog
import yaml

logger = structlog.get_logger(__name__)


def _resolve_templates_dir(start: Path | None = None) -> Path:
    """Locate ``spec/knowledge/explain-templates`` without raising at import time.

    Walks up from this file looking for the templates directory. This works both
    in the repo layout (…/src/backend/app/domain/engines → repo root) and in the
    container image, where the backend is copied to ``/app`` (skaffold build
    context ``src/backend``) so the ``src/backend`` levels are absent and a fixed
    ``parents[5]`` index would overshoot the filesystem root with an IndexError.
    The container image does not ship ``spec/`` at all, so no candidate exists
    there; the returned best-effort path is then reported as missing by
    :func:`_load_templates`, which degrades gracefully to an empty template set.

    ``start`` defaults to this module's file and exists for testing the
    resolution against a synthetic layout.
    """
    here = (start or Path(__file__)).resolve()
    for parent in here.parents:
        candidate = parent / "spec" / "knowledge" / "explain-templates"
        if candidate.is_dir():
            return candidate
    # No spec/ tree on disk (e.g. the container image). Return a stable,
    # non-existent path so _load_templates() logs explain_templates_dir_missing.
    return here.parents[-1] / "spec" / "knowledge" / "explain-templates"


#: ``spec/knowledge/explain-templates``. Best-effort; missing in the container
#: image, where :func:`_load_templates` degrades to an empty template set.
_TEMPLATES_DIR = _resolve_templates_dir()

_SLOT_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class ExplainTemplate:
    """A single question template with DE/EN variants."""

    def __init__(self, raw: dict) -> None:
        self.id: str = raw["id"]
        self.applies_to: str = raw.get("applies_to", "")
        self.question_de: str = raw.get("question_de", "")
        self.question_en: str = raw.get("question_en", "")
        self.expected_length_words_max: int = raw.get("expected_length_words_max", 80)

    def render(self, language: str, slots: dict[str, object]) -> str:
        """Fill the language-appropriate template, leaving unknown slots blank."""
        template = self.question_en if language == "en" else self.question_de

        def _replace(match: re.Match[str]) -> str:
            value = slots.get(match.group(1))
            return "" if value is None else str(value)

        rendered = _SLOT_RE.sub(_replace, template)
        # Collapse whitespace introduced by empty slots for a clean prompt.
        return re.sub(r"[ \t]+", " ", rendered).strip()


@lru_cache(maxsize=1)
def _load_templates() -> dict[str, ExplainTemplate]:
    """Load and cache all explain templates keyed by ``id``."""
    templates: dict[str, ExplainTemplate] = {}
    if not _TEMPLATES_DIR.exists():
        logger.warning("explain_templates_dir_missing", path=str(_TEMPLATES_DIR))
        return templates
    for path in sorted(_TEMPLATES_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        for entry in raw:
            template = ExplainTemplate(entry)
            templates[template.id] = template
    return templates


class ExplainEngine:
    """Renders curated "why?" questions from templates."""

    def get_template(self, template_id: str) -> ExplainTemplate | None:
        """Return the template with ``template_id`` or ``None`` when unknown."""
        return _load_templates().get(template_id)

    def build_question(self, template_id: str, language: str, slots: dict[str, object]) -> str | None:
        """Render the question for ``template_id``; ``None`` when it is unknown."""
        template = self.get_template(template_id)
        if template is None:
            return None
        return template.render(language, slots)
