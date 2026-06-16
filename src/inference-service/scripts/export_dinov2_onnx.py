#!/usr/bin/env python3
"""Export the DINOv2 ViT-S/14 backbone to ONNX (REQ-029-A 2.3 / 3.3).

This script is NOT run in CI and is NOT executed during the container build of
the service itself -- it produces the build artifact (`model.onnx` +
`modelinfo.json`) that the multi-stage Dockerfile copies into the runtime image.

IMPORTANT LICENCE NOTE (REQ-029-A 2.3 / 5 / risk table):
    The DINOv2 *base backbone* from Meta (facebookresearch/dinov2) is published
    under Apache-2.0. Meta re-licensed from CC-BY-NC to Apache-2.0; VERIFY the
    `LICENSE` file in the official repo BEFORE every production build. NEVER
    export the PlantCLEF-2024 fine-tuned weights -- those are CC-BY-NC and must
    not be shipped.

Usage:
    pip install torch torchvision onnx
    python scripts/export_dinov2_onnx.py --output ./models/dinov2

    # Optional: larger backbone / higher resolution
    python scripts/export_dinov2_onnx.py --arch dinov2_vits14 --input-size 224

Output:
    <output>/model.onnx        -- the exported graph
    <output>/modelinfo.json    -- { model, dim, input_size, license, checksum }
"""

import argparse
import hashlib
import json
from pathlib import Path

# Embedding dimensionality per DINOv2 architecture (REQ-029-A 2.3).
ARCH_DIM = {
    "dinov2_vits14": 384,
    "dinov2_vitb14": 768,
    "dinov2_vitl14": 1024,
}


def _sha256(path: Path) -> str:
    """Compute the sha256 checksum of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export(arch: str, input_size: int, output_dir: Path, opset: int) -> None:
    """Load the DINOv2 backbone from torch.hub and export it to ONNX."""
    import torch

    if arch not in ARCH_DIM:
        raise SystemExit(f"Unknown arch {arch!r}; choose from {sorted(ARCH_DIM)}")
    if input_size % 14 != 0:
        raise SystemExit(f"input-size must be a multiple of 14 (patch size); got {input_size}")

    output_dir.mkdir(parents=True, exist_ok=True)
    onnx_path = output_dir / "model.onnx"

    print(f"Loading {arch} from facebookresearch/dinov2 (Apache-2.0 backbone) ...")
    # Verify LICENSE in the repo before relying on this in production.
    model = torch.hub.load("facebookresearch/dinov2", arch)
    model.eval()

    dummy = torch.randn(1, 3, input_size, input_size, dtype=torch.float32)

    print(f"Exporting to ONNX (opset {opset}) -> {onnx_path}")
    torch.onnx.export(
        model,
        dummy,
        str(onnx_path),
        input_names=["pixel_values"],
        output_names=["embedding"],
        dynamic_axes={
            "pixel_values": {0: "batch"},
            "embedding": {0: "batch"},
        },
        opset_version=opset,
        do_constant_folding=True,
        # Use the legacy TorchScript exporter: torch>=2.9 defaults to the
        # dynamo exporter, which rejects the dict-style dynamic_axes used here.
        dynamo=False,
    )

    checksum = _sha256(onnx_path)
    info = {
        "model": arch,
        "dim": ARCH_DIM[arch],
        "input_size": input_size,
        "license": "Apache-2.0",
        "license_note": (
            "DINOv2 base backbone (facebookresearch/dinov2) is Apache-2.0. "
            "RE-VERIFY the LICENSE before production. Do NOT use PlantCLEF "
            "fine-tuned weights (CC-BY-NC)."
        ),
        "checksum": checksum,
        "opset": opset,
    }
    info_path = output_dir / "modelinfo.json"
    info_path.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {info_path}")
    print(f"  model     = {arch}")
    print(f"  dim       = {ARCH_DIM[arch]}")
    print(f"  input     = {input_size}x{input_size}")
    print(f"  sha256    = {checksum}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export DINOv2 backbone to ONNX.")
    parser.add_argument("--arch", default="dinov2_vits14", choices=sorted(ARCH_DIM))
    parser.add_argument("--input-size", type=int, default=224)
    parser.add_argument("--output", type=Path, default=Path("./models/dinov2"))
    parser.add_argument("--opset", type=int, default=17)
    args = parser.parse_args()
    export(args.arch, args.input_size, args.output, args.opset)


if __name__ == "__main__":
    main()
