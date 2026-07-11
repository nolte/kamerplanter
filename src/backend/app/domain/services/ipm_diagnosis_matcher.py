"""REQ-038 §4 — concrete DiagnosisMatcher backed by the IPM repository.

Resolves CV disease/deficiency/pest classes against REQ-010 ``diseases`` /
``pests`` stammdaten (by scientific name) and bridges deficiencies via their
REQ-036 symptom slug. Thin adapter around :class:`IIpmRepository`; the gating and
mapping logic lives in :class:`CvDiagnosisEngine`.
"""

from app.domain.engines.cv_diagnosis_engine import DiagnosisMatcher
from app.domain.interfaces.ipm_repository import IIpmRepository


class IpmDiagnosisMatcher(DiagnosisMatcher):
    """Maps CV classes onto IPM stammdaten keys (open-set: unknown → ``None``)."""

    def __init__(self, ipm_repo: IIpmRepository) -> None:
        self._ipm_repo = ipm_repo

    def match_disease_key(self, scientific_name: str | None) -> str | None:
        if not scientific_name:
            return None
        disease = self._ipm_repo.get_disease_by_scientific_name(scientific_name)
        return disease.key if disease else None

    def match_pest_key(self, scientific_name: str | None) -> str | None:
        if not scientific_name:
            return None
        pest = self._ipm_repo.get_pest_by_scientific_name(scientific_name)
        return pest.key if pest else None

    def match_symptom_slug(self, label: str) -> str | None:
        """Bridge a deficiency to its REQ-036 symptom slug.

        There is no ``deficiencies`` stammdaten collection in v1, so the
        classifier label *is* the symptom slug used by the REQ-036 assistant
        (deterministic passthrough). An empty label yields ``None``.
        """
        return label or None
