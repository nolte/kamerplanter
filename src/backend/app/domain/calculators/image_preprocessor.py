"""REQ-029 §5.4 — EXIF stripping and image normalization.

Pure-logic helpers (no I/O beyond in-memory image decoding). Every user image
is normalized and stripped of metadata *before* it leaves the instance to a
third party (REQ-029-A §10.1, REQ-029 §5.4). All EXIF metadata — GPS,
device info, capture timestamp — is dropped by re-encoding pixel data only.
"""

import io

from PIL import Image

# Maximum edge length sent to the identification service. Pl@ntNet accepts
# large images but downsizing keeps payloads small and stays well within limits.
MAX_IMAGE_DIMENSION = 1024


def strip_exif_and_normalize(
    image_data: bytes,
    *,
    max_dimension: int = MAX_IMAGE_DIMENSION,
) -> bytes:
    """Remove all metadata and normalize resolution/format.

    The image is decoded, optionally downscaled so its longest edge does not
    exceed ``max_dimension``, converted to RGB and re-encoded as JPEG. Because a
    fresh image is built from the raw pixel data, no EXIF block survives.

    Args:
        image_data: Raw JPEG/PNG bytes.
        max_dimension: Maximum length of the longest edge after normalization.

    Returns:
        Clean JPEG bytes without any EXIF metadata.

    Raises:
        ValueError: when the bytes cannot be decoded as an image.
    """
    try:
        with Image.open(io.BytesIO(image_data)) as img:
            img = img.convert("RGB")

            longest_edge = max(img.size)
            if longest_edge > max_dimension:
                scale = max_dimension / longest_edge
                new_size = (round(img.width * scale), round(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Re-encode from pixel data only — this drops every EXIF tag.
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=90)
            return buffer.getvalue()
    except (OSError, ValueError) as exc:
        raise ValueError("Image could not be decoded.") from exc
