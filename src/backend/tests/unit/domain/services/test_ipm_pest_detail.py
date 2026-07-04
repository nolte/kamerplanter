"""REQ-010 — Schädlings-Detailseite: aggregierter Detail-Service + Router.

Deckt die IPM-Hierarchie-Sortierung der Gegenmaßnahmen, den Nützlings-Lookup
über ``detection_slug``, den Schadbild-Hinweis aus der Erkennungs-Taxonomie
(REQ-044) sowie die Abwärtskompatibilität des erweiterten ``Pest``-Modells ab.
"""

from unittest.mock import MagicMock

import pytest

from app.api.v1.ipm import router as ipm_router
from app.common.enums import PathogenType, PestSeverity, PlantPart, TreatmentType
from app.common.exceptions import NotFoundError
from app.domain.models.beneficial import Beneficial
from app.domain.models.ipm import Disease, Pest, Treatment
from app.domain.services.ipm_service import IpmService


def _treatment(name: str, ttype: TreatmentType) -> Treatment:
    # Chemische Mittel erzwingen eine Karenz > 0 (Modell-Validator).
    safety = 7 if ttype == TreatmentType.CHEMICAL else 0
    return Treatment(_key=name, name=name, treatment_type=ttype, safety_interval_days=safety)


class _FakeRepo:
    def __init__(self, *, pest=None, treatments=None, beneficials=None, treatment=None, pests=None, diseases=None):
        self._pest = pest
        self._treatments = treatments or []
        self._beneficials = beneficials or []
        self._treatment = treatment
        self._pests = pests or []
        self._diseases = diseases or []
        self.beneficial_slug_queried: str | None = None

    def get_pest_by_key(self, key):
        return self._pest if self._pest and self._pest.key == key else None

    def get_pest_or_raise(self, key):
        pest = self.get_pest_by_key(key)
        if pest is None:
            raise NotFoundError("Pest", key)
        return pest

    def get_treatments_for_pest(self, key):
        return list(self._treatments)

    def get_beneficials_for_pest_slug(self, slug):
        self.beneficial_slug_queried = slug
        return [b for b in self._beneficials if slug in b.preys_on]

    def get_treatment_by_key(self, key):
        return self._treatment if self._treatment and self._treatment.key == key else None

    def get_treatment_or_raise(self, key):
        treatment = self.get_treatment_by_key(key)
        if treatment is None:
            raise NotFoundError("Treatment", key)
        return treatment

    def get_pests_for_treatment(self, key):
        return list(self._pests)

    def get_diseases_for_treatment(self, key):
        return list(self._diseases)


def _service(repo) -> IpmService:
    # get_pest_detail nutzt nur das Repository; die Engines werden gemockt.
    return IpmService(repo, MagicMock(), MagicMock(), MagicMock())


class TestGetPestDetail:
    def test_treatments_sorted_by_ipm_hierarchy(self):
        pest = Pest(_key="p1", scientific_name="Tetranychus urticae", common_name="Spider Mites")
        treatments = [
            _treatment("Pyrethrin", TreatmentType.CHEMICAL),
            _treatment("Sticky Traps", TreatmentType.MECHANICAL),
            _treatment("Environmental Control", TreatmentType.CULTURAL),
            _treatment("Neem Oil", TreatmentType.BIOLOGICAL),
        ]
        service = _service(_FakeRepo(pest=pest, treatments=treatments))

        detail = service.get_pest_detail("p1")

        order = [t.treatment_type for t in detail["treatments"]]
        assert order == [
            TreatmentType.CULTURAL,
            TreatmentType.BIOLOGICAL,
            TreatmentType.MECHANICAL,
            TreatmentType.CHEMICAL,
        ]

    def test_duplicate_treatments_are_deduplicated(self):
        # Mehrfache identische targets_pest-Edges → das Repo liefert dasselbe
        # Treatment mehrfach; der Service liefert es genau einmal zurück.
        pest = Pest(_key="p1", scientific_name="X", common_name="Y")
        neem = _treatment("Neem Oil", TreatmentType.BIOLOGICAL)
        service = _service(_FakeRepo(pest=pest, treatments=[neem, neem, neem]))

        detail = service.get_pest_detail("p1")

        assert [t.name for t in detail["treatments"]] == ["Neem Oil"]

    def test_beneficials_and_symptom_hint_from_detection_slug(self):
        pest = Pest(
            _key="p1",
            scientific_name="Tetranychus urticae",
            common_name="Spider Mites",
            detection_slug="spider_mite",
        )
        ladybird = Beneficial(
            _key="b1",
            slug="ladybird",
            common_name="Marienkäfer",
            scientific_name="Coccinellidae",
            preys_on=["spider_mite", "aphid"],
        )
        repo = _FakeRepo(pest=pest, beneficials=[ladybird])
        service = _service(repo)

        detail = service.get_pest_detail("p1")

        assert repo.beneficial_slug_queried == "spider_mite"
        assert [b.slug for b in detail["beneficials"]] == ["ladybird"]
        # Schadbild-Hinweis stammt aus der REQ-044-Taxonomie (PestTaxon.symptom_hint_de).
        assert detail["detection_symptom_hint"]
        assert "Gespinste" in detail["detection_symptom_hint"]

    def test_without_detection_slug_no_beneficials(self):
        pest = Pest(_key="p1", scientific_name="X", common_name="Y")
        repo = _FakeRepo(pest=pest, beneficials=[])
        service = _service(repo)

        detail = service.get_pest_detail("p1")

        assert detail["beneficials"] == []
        assert detail["detection_symptom_hint"] is None
        assert repo.beneficial_slug_queried is None

    def test_unknown_key_raises_not_found(self):
        service = _service(_FakeRepo(pest=None))
        with pytest.raises(NotFoundError):
            service.get_pest_detail("missing")


class TestPestModelBackwardCompatibility:
    def test_minimal_pest_has_safe_defaults(self):
        # Ein Seed/DB-Dokument im alten Format (nur Basisfelder) bleibt gültig.
        pest = Pest(scientific_name="Aphis gossypii", common_name="Aphids")
        assert pest.affected_plant_parts == []
        assert pest.host_plants == []
        assert pest.reference_image_refs == []
        assert pest.damage_symptoms is None
        assert pest.severity is None
        assert pest.detection_slug is None

    def test_detail_fields_round_trip(self):
        pest = Pest(
            scientific_name="Tetranychus urticae",
            common_name="Spider Mites",
            severity=PestSeverity.HIGH,
            affected_plant_parts=[PlantPart.LEAF, PlantPart.STEM],
            detection_slug="spider_mite",
            reference_image_refs=["/api/v1/attachments/1"],
        )
        assert pest.severity == PestSeverity.HIGH
        assert PlantPart.LEAF in pest.affected_plant_parts


class TestRouterMapping:
    def test_router_maps_detail_to_response(self):
        pest = Pest(
            _key="p1",
            scientific_name="Tetranychus urticae",
            common_name="Spider Mites",
            detection_slug="spider_mite",
            severity=PestSeverity.HIGH,
        )
        ladybird = Beneficial(
            _key="b1",
            slug="ladybird",
            common_name="Marienkäfer",
            scientific_name="Coccinellidae",
            preys_on=["spider_mite"],
        )
        treatments = [_treatment("Neem Oil", TreatmentType.BIOLOGICAL)]
        service = _service(_FakeRepo(pest=pest, treatments=treatments, beneficials=[ladybird]))

        resp = ipm_router.get_pest_detail("p1", service=service)

        assert resp.pest.key == "p1"
        assert resp.pest.severity == PestSeverity.HIGH
        assert [t.name for t in resp.treatments] == ["Neem Oil"]
        assert [b.slug for b in resp.beneficials] == ["ladybird"]
        assert resp.detection_symptom_hint

    def test_router_propagates_not_found(self):
        service = _service(_FakeRepo(pest=None))
        with pytest.raises(NotFoundError):
            ipm_router.get_pest_detail("missing", service=service)


class TestGetTreatmentDetail:
    def test_returns_treatment_with_targets(self):
        treatment = Treatment(_key="t1", name="Neem Oil", name_de="Niemöl", treatment_type=TreatmentType.BIOLOGICAL)
        pest = Pest(_key="p1", scientific_name="Tetranychus urticae", common_name="Spider Mites")
        disease = Disease(
            _key="d1",
            scientific_name="Botrytis cinerea",
            common_name="Grey Mold",
            pathogen_type=PathogenType.FUNGAL,
        )
        service = _service(_FakeRepo(treatment=treatment, pests=[pest], diseases=[disease]))

        detail = service.get_treatment_detail("t1")

        assert detail["treatment"].name_de == "Niemöl"
        assert [p.key for p in detail["targeted_pests"]] == ["p1"]
        assert [d.key for d in detail["targeted_diseases"]] == ["d1"]

    def test_deduplicates_targeted_pests(self):
        treatment = Treatment(_key="t1", name="Neem Oil", treatment_type=TreatmentType.BIOLOGICAL)
        pest = Pest(_key="p1", scientific_name="X", common_name="Y")
        service = _service(_FakeRepo(treatment=treatment, pests=[pest, pest, pest]))

        detail = service.get_treatment_detail("t1")

        assert len(detail["targeted_pests"]) == 1

    def test_unknown_key_raises_not_found(self):
        service = _service(_FakeRepo(treatment=None))
        with pytest.raises(NotFoundError):
            service.get_treatment_detail("missing")

    def test_router_maps_treatment_detail(self):
        treatment = Treatment(_key="t1", name="Neem Oil", name_de="Niemöl", treatment_type=TreatmentType.BIOLOGICAL)
        pest = Pest(_key="p1", scientific_name="Tetranychus urticae", common_name="Spider Mites")
        service = _service(_FakeRepo(treatment=treatment, pests=[pest]))

        resp = ipm_router.get_treatment_detail("t1", service=service)

        assert resp.treatment.name_de == "Niemöl"
        assert [p.key for p in resp.targeted_pests] == ["p1"]
        assert resp.targeted_pests[0].common_name == "Spider Mites"


class TestTreatmentModelMultilingual:
    def test_minimal_treatment_has_safe_defaults(self):
        t = Treatment(name="Neem Oil", treatment_type=TreatmentType.BIOLOGICAL)
        assert t.name_de is None
        assert t.description_de is None
        assert t.how_to_apply is None
        assert t.mode_of_action_de is None
        assert t.precautions is None
