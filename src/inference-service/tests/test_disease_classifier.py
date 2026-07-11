"""REQ-038 unit tests for DiseaseClassifier / PhenotypeEngine internals."""

import numpy as np
import pytest

from app.disease_classifier import (
    DiseaseClassifier,
    DiseaseModelNotReadyError,
    _softmax,
)
from app.phenotype_engine import PhenotypeEngine, PhenotypeUnavailableError
from tests.conftest import make_image_bytes


class _FakeSession:
    """Minimal ONNX session stand-in emitting fixed logits."""

    def __init__(self, logits: list[float]) -> None:
        self._logits = np.asarray([logits], dtype=np.float32)

    def get_inputs(self):
        class _Inp:
            name = "pixel_values"

        return [_Inp()]

    def run(self, _outputs, _feed):
        return [self._logits]


def _ready_classifier(logits: list[float], labels: list) -> DiseaseClassifier:
    from app.disease_classifier import DiseaseLabel

    clf = DiseaseClassifier(model_path="/nonexistent", input_size=224)
    clf._session = _FakeSession(logits)
    clf._input_name = "pixel_values"
    clf._labels = [DiseaseLabel(**lbl) for lbl in labels]
    clf._ready = True
    return clf


class TestSoftmax:
    def test_softmax_sums_to_one(self):
        out = _softmax(np.asarray([2.0, 1.0, 0.1], dtype=np.float32))
        assert abs(float(np.sum(out)) - 1.0) < 1e-6
        assert out[0] > out[1] > out[2]

    def test_softmax_all_equal(self):
        out = _softmax(np.zeros(4, dtype=np.float32))
        assert np.allclose(out, 0.25)


class TestClassify:
    def test_topk_ordered_by_probability(self):
        clf = _ready_classifier(
            [0.2, 5.0, 1.0],
            [
                {"label": "a", "category": "disease"},
                {"label": "b", "category": "deficiency"},
                {"label": "c", "category": "healthy"},
            ],
        )
        results = clf.classify(make_image_bytes(), k=2)
        assert [r.label for r in results] == ["b", "c"]
        assert results[0].category == "deficiency"
        assert results[0].probability > results[1].probability

    def test_unknown_category_defaults_to_disease(self):
        clf = _ready_classifier([1.0], [{"label": "x", "category": "bogus"}])
        assert clf.classify(make_image_bytes())[0].category == "disease"

    def test_classify_raises_when_not_ready(self):
        clf = DiseaseClassifier(model_path="/nonexistent", input_size=224)
        with pytest.raises(DiseaseModelNotReadyError):
            clf.classify(make_image_bytes())

    def test_classify_raises_on_logit_label_mismatch(self):
        clf = _ready_classifier([1.0, 2.0], [{"label": "only_one", "category": "disease"}])
        with pytest.raises(DiseaseModelNotReadyError):
            clf.classify(make_image_bytes())


class TestParseLabels:
    def test_parses_dict_and_list_forms(self):
        clf = DiseaseClassifier(model_path="/x", input_size=224)
        labels = clf._parse_labels('{"classes": [{"label": "a", "category": "disease"}]}')
        assert labels[0].label == "a"
        plain = clf._parse_labels('["a", "b"]')
        assert [entry.label for entry in plain] == ["a", "b"]

    def test_rejects_empty(self):
        clf = DiseaseClassifier(model_path="/x", input_size=224)
        with pytest.raises(ValueError, match="non-empty"):
            clf._parse_labels("[]")


class TestPhenotypeEngineDegradation:
    def test_disabled_engine_is_unavailable(self):
        engine = PhenotypeEngine(enabled=False)
        assert engine.is_available() is False
        with pytest.raises(PhenotypeUnavailableError):
            engine.measure(make_image_bytes())

    def test_missing_plantcv_degrades_gracefully(self, monkeypatch):
        engine = PhenotypeEngine(enabled=True)
        # Force the lazy import to fail.
        import builtins

        real_import = builtins.__import__

        def _fail(name, *args, **kwargs):
            if name == "plantcv":
                raise ImportError("no plantcv")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _fail)
        assert engine.is_available() is False
