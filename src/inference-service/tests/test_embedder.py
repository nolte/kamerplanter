"""Unit tests for the ONNX feed construction in Embedder.

Regression guard for the acquisition run failing with
``Required inputs (['masks']) are missing from input feed (['pixel_values'])``:
some DINOv2 ONNX exports carry an auxiliary scalar boolean ``masks`` input, and
the session must be fed a neutral value for it alongside ``pixel_values``.
"""

import numpy as np

from app.embedder import Embedder


class _FakeNodeArg:
    def __init__(self, name: str, shape: list, type_: str) -> None:
        self.name = name
        self.shape = shape
        self.type = type_


class _FakeSession:
    """Minimal ONNX session stand-in that records the feed it was given."""

    def __init__(self, inputs: list[_FakeNodeArg]) -> None:
        self._inputs = inputs
        self.last_feed: dict | None = None

    def get_inputs(self) -> list[_FakeNodeArg]:
        return self._inputs

    def run(self, _outputs, feed):
        self.last_feed = feed
        batch = feed["pixel_values"]
        # Emit a (N, 384) embedding regardless of the masks value.
        return [np.ones((batch.shape[0], 384), dtype=np.float32)]


def test_neutral_input_bool_scalar_is_false():
    arg = _FakeNodeArg("masks", [], "tensor(bool)")
    value = Embedder._neutral_input(arg)
    assert value.dtype == np.bool_
    assert value.shape == ()
    assert bool(value) is False


def test_neutral_input_symbolic_dims_collapse_to_one():
    arg = _FakeNodeArg("aux", ["batch", 4], "tensor(float)")
    value = Embedder._neutral_input(arg)
    assert value.shape == (1, 4)
    assert value.dtype == np.float32
    assert not value.any()


def _make_loaded_embedder(inputs: list[_FakeNodeArg]) -> tuple[Embedder, _FakeSession]:
    """An Embedder with its session pre-populated as the load thread would."""
    emb = Embedder(model_path="/nonexistent", input_size=224, expected_dim=384)
    session = _FakeSession(inputs)
    emb._session = session
    emb._input_name = inputs[0].name
    emb._aux_inputs = [(inp.name, Embedder._neutral_input(inp)) for inp in inputs[1:]]
    emb._ready = True
    return emb, session


def test_embed_batch_feeds_masks_input(monkeypatch):
    """When the model declares a masks input, embed_batch must feed it."""
    monkeypatch.setattr(
        "app.embedder.preprocess",
        lambda _img, _size: np.zeros((1, 3, 224, 224), dtype=np.float32),
    )
    inputs = [
        _FakeNodeArg("pixel_values", ["batch", 3, 224, 224], "tensor(float)"),
        _FakeNodeArg("masks", [], "tensor(bool)"),
    ]
    emb, session = _make_loaded_embedder(inputs)

    result = emb.embed_batch([b"fake-image-bytes"])

    assert len(result) == 1
    assert session.last_feed is not None
    # Both the primary and the auxiliary input were fed (the missing-masks bug).
    assert set(session.last_feed.keys()) == {"pixel_values", "masks"}
    assert session.last_feed["masks"].dtype == np.bool_


def test_embed_batch_without_aux_inputs(monkeypatch):
    """A masks-free model (clean export) feeds only pixel_values."""
    monkeypatch.setattr(
        "app.embedder.preprocess",
        lambda _img, _size: np.zeros((1, 3, 224, 224), dtype=np.float32),
    )
    inputs = [_FakeNodeArg("pixel_values", ["batch", 3, 224, 224], "tensor(float)")]
    emb, session = _make_loaded_embedder(inputs)

    emb.embed_batch([b"fake-image-bytes"])

    assert set(session.last_feed.keys()) == {"pixel_values"}
