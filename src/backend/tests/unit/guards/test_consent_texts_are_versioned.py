"""A consent text does not change without a new text version (REQ-025 v1.42, UI-NFR-013 v1.4 CP-013).

A grant is a person's agreement to *one wording*: ``ConsentRecord.consent_version``
names it, and for the purposes the browser reads (``browser_error_reports``) a
grant only counts while that version is the purpose's current one. A text edited
without raising ``ConsentPurpose.version`` would let every earlier grant stand for
words nobody agreed to — silently, because nothing compares texts.

**The rule.** Every purpose's label and description (DE/EN) are pinned below as a
SHA-256 next to the version they belong to; for ``browser_error_reports`` the
texts the browser shows (``consent.banner`` in ``pages.json`` DE/EN) are pinned
next to the same version. A changed text turns this red. The fix is to raise the
version (``consent_engine.py`` and, for the browser purpose,
``BROWSER_ERROR_REPORTS_VERSION`` in ``observability/consent.ts``) and then
re-pin — or, for a change that is not one of meaning (a typo), to re-pin at the
same version and say so in the commit. Either way the change is a decision, not
an accident.

**Limits, stated.** The pin cannot judge whether an edit changes the meaning; it
only makes every edit visible to review. The frontend side covers the keys that
form the consent text, not button labels or error notices.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.domain.engines.consent_engine import BROWSER_ERROR_REPORTS, ConsentEngine
from tests.support.repo_scripts import find_repo_root

#: ``{purpose: (version, sha256 of label_de, label_en, description_de, description_en)}``.
PINNED: dict[str, tuple[str, str]] = {
    "core_functionality": ("1.0", "acdf2cba390a6a49d4e08fab1e0b33a7db1e625bc1c5ce86c38243e0144e798a"),
    "error_tracking": ("1.0", "e9ef5f78d0fec983e5df5ebf5bd569c94765de89f07930cdc47ebacfddd02457"),
    "browser_error_reports": ("1.0", "fde3e8a46bd57f36ed807bdc023aa05e0d0df909b29c081e9213237b6124c309"),
    "plant_identification": ("1.0", "b56bf10882abfd9dff17b47029b38ee553da3810f97c5c8984b61ae671fd0011"),
    "pest_detection_cloud": ("1.0", "02eb9b8935cc13f35e027ee5519813aadd3b2af4f3885f4accadaad4ce3ff34a"),
    "ai_tenant_data_access": ("1.0", "51e3778d820777fcf7524565e5961de78fed585a063a89415df74b5f91f76ead"),
    "ai_knowledge_question": ("1.0", "5d54e5d54225ce88ac99672d40a016989a2fe3bd4f9e40cc315b73332138bfe0"),
    "diary_ai_analysis": ("1.0", "79d8a1c9cc9c542cea1fd5e77cbbb42885e1845ef7ac8267db28efc473af9bb2"),
    "ai_cloud_processing": ("1.0", "7da5dd9d59c05223105501337ed45c62c9279d2ba3badbc3b5643332abc601ff"),
    "plant_diagnosis": ("1.0", "71c966a6ac8075879424b7647d3909f48176cc7c9da20d9b0510d0c5c332884a"),
    "reference_contribution": ("1.0", "7c87505c92d6db60115e92cb2a23d9b7bd88c6973be6dcc4c501ecd99787101b"),
    "pest_reference_contribution": ("1.0", "370715d851b4ba355d850a8dd0d40848a2c71cdc50d71e01e3f9bedf6b04ac22"),
}

#: The browser's text of ``browser_error_reports``: ``(version, sha256)``.
FRONTEND_PINNED: tuple[str, str] = ("1.0", "fb09081222bcfa4bf3192b2b9b115cb4b881d0420f8daac381f18adaa7ce8d13")

#: The keys under ``consent.banner`` that form the consent text the browser shows.
FRONTEND_TEXT_KEYS = (
    "title",
    "intro",
    "summary",
    "scope_device",
    "scope_account",
    "category.browser_error_reports.label",
    "category.browser_error_reports.description",
)

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
LOCALES = _REPO_ROOT / "src" / "frontend" / "src" / "i18n" / "locales" if _REPO_ROOT else None


def text_digest(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def frontend_texts(pages_by_locale: dict[str, dict]) -> list[str]:
    """The pinned keys of ``consent.banner`` for DE and EN, in a fixed order."""
    texts: list[str] = []
    for locale in ("de", "en"):
        banner = pages_by_locale[locale]["consent"]["banner"]
        for dotted in FRONTEND_TEXT_KEYS:
            node = banner
            for part in dotted.split("."):
                node = node[part]
            texts.append(node)
    return texts


def test_every_purpose_text_is_pinned_to_its_version() -> None:
    current = {
        p.key: (p.version, text_digest(p.label_de, p.label_en, p.description_de, p.description_en))
        for p in ConsentEngine().get_all_purposes()
    }
    assert set(current) == set(PINNED), "a purpose was added or removed: pin it with its version"
    changed = {key: value for key, value in current.items() if PINNED[key] != value}
    assert changed == {}, (
        "consent text changed without a pinned version: raise ConsentPurpose.version (and, for "
        f"browser_error_reports, BROWSER_ERROR_REPORTS_VERSION), then re-pin — {changed}"
    )


@pytest.mark.skipif(LOCALES is None or not LOCALES.is_dir(), reason="frontend sources not in this checkout")
def test_the_browser_text_is_pinned_to_the_same_version() -> None:
    assert LOCALES is not None
    pages = {
        locale: json.loads((LOCALES / locale / "pages.json").read_text(encoding="utf-8")) for locale in ("de", "en")
    }
    version = ConsentEngine().current_version(BROWSER_ERROR_REPORTS)

    assert (version, text_digest(*frontend_texts(pages))) == FRONTEND_PINNED


def test_the_digest_sees_every_part() -> None:
    base = text_digest("a", "b", "c", "d")
    assert text_digest("a", "b", "c", "d ") != base
    assert text_digest("ab", "", "c", "d") != base  # the separator keeps the parts apart
    pages = {
        locale: {
            "consent": {
                "banner": {
                    "title": "t",
                    "intro": "i",
                    "summary": "s",
                    "scope_device": "d",
                    "scope_account": "a",
                    "category": {"browser_error_reports": {"label": "l", "description": "x"}},
                }
            }
        }
        for locale in ("de", "en")
    }
    assert frontend_texts(pages) == ["t", "i", "s", "d", "a", "l", "x"] * 2
