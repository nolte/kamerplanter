"""Load the ONNX model a built image ships and run one inference through it.

    python verify_onnx_model.py <model-dir> <expected-dim> <input-size>

Run INSIDE the image under test (``docker run --entrypoint python``), mounted in
by ``scripts/ci/smoke_model_image.sh``'s ``model`` mode. It needs only
``onnxruntime`` and ``numpy``, which every image in this class already installs.

#1609 — why this exists beside the HTTP readiness probe. Two of the three
model-shipping images become ready on their own, so starting them and requiring
``/ready`` is the better proof: it exercises the real serving path. The
inference service does not: its lifespan connects to pgvector and runs
migrations BEFORE it starts loading the model, so a lone container can never
answer at all. Requiring ``/ready`` there would assert the absence of a
database, not the presence of a model. This asserts the model directly instead —
a truncated export, a missing ``model.onnx_data``, or a graph whose output
dimension drifted from what the service expects all fail here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort


#: ONNX tensor element types, as onnxruntime spells them in `NodeArg.type`.
_DTYPES = {
    "tensor(float)": np.float32,
    "tensor(double)": np.float64,
    "tensor(float16)": np.float16,
    "tensor(int64)": np.int64,
    "tensor(int32)": np.int32,
    "tensor(bool)": np.bool_,
}


def _dtype_of(spec) -> object:  # noqa: ANN001 — onnxruntime NodeArg has no public type
    return _DTYPES.get(spec.type, np.float32)


def _shape_of(spec, input_size: int) -> list[int]:  # noqa: ANN001
    """A concrete shape for *spec*, resolving dynamic axes.

    A dynamic axis comes back as a string (``"batch"``, ``"height"``) or as
    ``None``. Batch is 1; every other free axis takes the input size the export
    was made for.
    """
    return [dim if isinstance(dim, int) else (1 if index == 0 else input_size) for index, dim in enumerate(spec.shape)]


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(f"usage: {argv[0]} <model-dir> <expected-dim> <input-size>", file=sys.stderr)
        return 2

    model_dir = Path(argv[1])
    expected_dim = int(argv[2])
    input_size = int(argv[3])

    onnx = model_dir / "model.onnx"
    if not onnx.is_file():
        print(f"FAIL: {onnx} is not a file; the image ships no graph", file=sys.stderr)
        print(f"       {model_dir} contains: {sorted(p.name for p in model_dir.glob('*'))}", file=sys.stderr)
        return 1

    # Session creation is already a real assertion: it resolves the external
    # weights file (`model.onnx_data`) and rejects a truncated or malformed graph.
    session = ort.InferenceSession(str(onnx), providers=["CPUExecutionProvider"])

    # EVERY declared input is fed, not just the first one — measured, not
    # assumed. The DINOv2 export carries a second input, `masks`, an artifact of
    # the traced forward signature; feeding only `pixel_values` raises
    # "Required inputs (['masks']) are missing". `app/embedder.py` builds the
    # same neutral values for non-primary inputs, so this mirrors the real feed.
    feed = {spec.name: np.zeros(_shape_of(spec, input_size), dtype=_dtype_of(spec)) for spec in session.get_inputs()}

    output = session.run(None, feed)[0]
    dim = int(output.shape[-1])
    if dim != expected_dim:
        print(f"FAIL: {onnx} produces dimension {dim}, the service expects {expected_dim}", file=sys.stderr)
        return 1

    print(f"model ok: {onnx} -> {tuple(output.shape)} (dimension {dim})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
