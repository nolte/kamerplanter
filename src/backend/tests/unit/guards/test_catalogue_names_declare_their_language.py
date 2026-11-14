"""#2936 — a domain model that stores a common name stores it per language.

Diseases carried one English ``common_name`` and beneficials one German ``common_name``;
neither followed the UI language (UI-NFR-007 R-009a). The predecessor #2902 fixed the same
defect for species. The class is "a domain model with a vernacular name field that cannot
say which language the name is in", so this guard enumerates the class, not the two sites.

**The rule.** Every Pydantic model in ``app/domain/models/`` and ``app/domain/interfaces/``
with a field named ``common_name`` or ``common_name_<lang>`` also carries, outside
:data:`_ALLOWED`, either

* a ``common_names_i18n`` map (Species, Disease, Beneficial), or
* name fields for at least two languages: ``common_name_de`` plus ``common_name`` (the
  English base, as on Pest) or ``common_name_en`` (as on BotanicalFamily).

**Blind spots**, named rather than discovered later:

* models outside the two packages (API schemas, engine dataclasses) — they carry what a
  domain model holds or a name already resolved server-side;
* a name field spelled differently (``name``, ``label``, ``display_name``);
* a model that HAS both fields but whose seed fills only one language (the seed tests pin
  that per entity: ``tests/unit/migrations/test_seed_ipm_names_i18n.py``,
  ``test_seed_common_names_i18n.py``).
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from pydantic import BaseModel

import app.domain.interfaces as interfaces_pkg
import app.domain.models as models_pkg

#: ``module.Class`` -> why a single-language name is accepted there. Keep it short.
_ALLOWED: dict[str, str] = {
    "app.domain.interfaces.pest_detection_adapter.PestFinding": (
        "a detection finding carries the taxon's German name (PestTaxon.common_name_de); the "
        "detection taxonomy has sourced English names only for four beneficials so far (#2936)"
    ),
}


def _models() -> dict[str, type[BaseModel]]:
    found: dict[str, type[BaseModel]] = {}
    for package in (models_pkg, interfaces_pkg):
        for info in pkgutil.iter_modules(package.__path__, f"{package.__name__}."):
            module = importlib.import_module(info.name)
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseModel) and obj.__module__ == module.__name__:
                    found[f"{obj.__module__}.{obj.__qualname__}"] = obj
    return found


def _name_fields(model: type[BaseModel]) -> set[str]:
    return {f for f in model.model_fields if f == "common_name" or f.startswith("common_name_")}


def _declares_its_languages(model: type[BaseModel]) -> bool:
    fields = set(model.model_fields)
    if "common_names_i18n" in fields:
        return True
    return "common_name_de" in fields and bool({"common_name", "common_name_en"} & fields)


def test_the_scan_sees_the_known_name_carriers() -> None:
    names = {path for path, model in _models().items() if _name_fields(model)}

    assert {
        "app.domain.models.ipm.Pest",
        "app.domain.models.ipm.Disease",
        "app.domain.models.beneficial.Beneficial",
        "app.domain.models.botanical_family.BotanicalFamily",
        "app.domain.models.pest_taxonomy.PestTaxon",
    } <= names


def test_every_model_with_a_common_name_declares_its_languages() -> None:
    offenders = [
        path
        for path, model in _models().items()
        if _name_fields(model) and path not in _ALLOWED and not _declares_its_languages(model)
    ]

    assert offenders == []


def test_every_allowlisted_model_is_real_and_still_single_language() -> None:
    models = _models()
    for path in _ALLOWED:
        assert path in models, path
        assert not _declares_its_languages(models[path]), f"{path} declares its languages now: drop it from _ALLOWED"
