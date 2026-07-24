"""Preprocessing contract (REQ-029-A 3.2) -- index- and query-identical.

CRITICAL: Embeddings are only comparable when reference and query images are
preprocessed EXACTLY the same way. Any deviation makes the matching unusable.
This module is the single source of truth for that transform; both the
reference-indexing pipeline and the live /match path MUST go through it.

Pipeline:
    1. EXIF orientation applied + RGB conversion
    2. Resize shorter edge to INPUT_SIZE, center-crop INPUT_SIZE x INPUT_SIZE
    3. /255.0, ImageNet normalisation (x - MEAN) / STD
    4. HWC -> CHW, batch dimension, float32

The transform is fully deterministic: the same bytes always yield the same array.
"""

import io

import numpy as np
from PIL import Image, ImageOps

# ImageNet statistics (DINOv2 was trained on ImageNet-normalised inputs).
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Default input size: a multiple of 14 (DINOv2 patch size). 518 yields higher
# accuracy at the cost of latency; 224 is the MVP baseline (REQ-029-A 2.3).
INPUT_SIZE = 224

_MEAN = np.array(IMAGENET_MEAN, dtype=np.float32).reshape(1, 1, 3)
_STD = np.array(IMAGENET_STD, dtype=np.float32).reshape(1, 1, 3)


def _resize_shorter_edge(image: Image.Image, target: int) -> Image.Image:
    """Resize so the shorter edge equals ``target``, preserving aspect ratio."""
    width, height = image.size
    if width <= height:
        new_width = target
        new_height = max(target, round(height * target / width))
    else:
        new_height = target
        new_width = max(target, round(width * target / height))
    return image.resize((new_width, new_height), Image.Resampling.BICUBIC)


def _center_crop(image: Image.Image, size: int) -> Image.Image:
    """Crop a ``size`` x ``size`` square from the centre of the image."""
    width, height = image.size
    left = (width - size) // 2
    top = (height - size) // 2
    return image.crop((left, top, left + size, top + size))


def load_image(image_bytes: bytes) -> Image.Image:
    """Decode bytes into an EXIF-corrected RGB PIL image.

    Applies the EXIF orientation tag (cameras/phones rotate via metadata) and
    then drops all metadata by converting to a plain RGB image -- this doubles
    as EXIF stripping for any downstream consumer.
    """
    image: Image.Image = Image.open(io.BytesIO(image_bytes))
    # Apply EXIF orientation, then convert to RGB (strips remaining metadata).
    image = ImageOps.exif_transpose(image)
    return image.convert("RGB")


def preprocess(image_bytes: bytes, input_size: int = INPUT_SIZE) -> np.ndarray:
    """Run the full preprocessing contract on raw image bytes.

    Args:
        image_bytes: Raw encoded image (JPEG/PNG/etc.).
        input_size: Target square size; must match the model's expected input.

    Returns:
        A ``(1, 3, input_size, input_size)`` float32 array (NCHW), ready for ONNX.
    """
    image = load_image(image_bytes)
    image = _resize_shorter_edge(image, input_size)
    image = _center_crop(image, input_size)

    array = np.asarray(image, dtype=np.float32) / 255.0  # HWC, [0, 1]
    array = (array - _MEAN) / _STD  # ImageNet normalisation
    array = np.transpose(array, (2, 0, 1))  # HWC -> CHW
    return np.expand_dims(array, axis=0).astype(np.float32)  # add batch dim
