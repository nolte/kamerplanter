"""Tests for the preprocessing contract (REQ-029-A 3.2, Szenario A6)."""

import numpy as np
import pytest

from app.preprocessing import (
    _MEAN,
    _STD,
    INPUT_SIZE,
    load_image,
    preprocess,
)
from tests.conftest import make_image_bytes


def test_output_shape_and_dtype():
    """Preprocessing yields a (1, 3, 224, 224) float32 NCHW tensor."""
    arr = preprocess(make_image_bytes())
    assert arr.shape == (1, 3, INPUT_SIZE, INPUT_SIZE)
    assert arr.dtype == np.float32


def test_determinism_same_bytes_same_array():
    """Szenario A6: identical bytes must produce a bitwise-identical array."""
    data = make_image_bytes()
    a = preprocess(data)
    b = preprocess(data)
    np.testing.assert_array_equal(a, b)


def test_consistency_reencoded_identical_image():
    """Two PNG encodings of the same pixels produce the same preprocessing output."""
    img1 = make_image_bytes(color=(10, 120, 60), size=(300, 200), fmt="PNG")
    img2 = make_image_bytes(color=(10, 120, 60), size=(300, 200), fmt="PNG")
    np.testing.assert_array_equal(preprocess(img1), preprocess(img2))


def test_different_images_differ():
    """Different images must not collapse to the same embedding input."""
    a = preprocess(make_image_bytes(color=(0, 0, 0)))
    b = preprocess(make_image_bytes(color=(255, 255, 255)))
    assert not np.array_equal(a, b)


def test_imagenet_normalisation_range():
    """A white image maps to (1 - MEAN)/STD per channel after normalisation."""
    white = make_image_bytes(color=(255, 255, 255), size=(224, 224))
    arr = preprocess(white)
    # All-white center crop -> each channel ~ (1 - mean) / std
    expected = ((1.0 - _MEAN.reshape(3)) / _STD.reshape(3)).astype(np.float32)
    # The left half is red in make_image_bytes; sample the right half (still 255s
    # except where overwritten). Use the top-right pixel which stays white.
    actual = arr[0, :, 0, -1]
    np.testing.assert_allclose(actual, expected, rtol=1e-4, atol=1e-4)


def test_square_input_unchanged_size():
    """A square image at INPUT_SIZE needs no crop and keeps the size."""
    arr = preprocess(make_image_bytes(size=(INPUT_SIZE, INPUT_SIZE)))
    assert arr.shape[2:] == (INPUT_SIZE, INPUT_SIZE)


def test_load_image_returns_rgb():
    """load_image always returns an RGB image (EXIF applied, metadata stripped)."""
    img = load_image(make_image_bytes())
    assert img.mode == "RGB"


def test_custom_input_size_is_multiple_of_patch():
    """A non-default input size is honoured."""
    arr = preprocess(make_image_bytes(size=(400, 400)), input_size=98)
    assert arr.shape == (1, 3, 98, 98)


def test_landscape_and_portrait_both_crop_to_square():
    """Both orientations reduce to INPUT_SIZE x INPUT_SIZE."""
    landscape = preprocess(make_image_bytes(size=(640, 320)))
    portrait = preprocess(make_image_bytes(size=(320, 640)))
    assert landscape.shape == portrait.shape == (1, 3, INPUT_SIZE, INPUT_SIZE)


@pytest.mark.parametrize("fmt", ["PNG", "JPEG"])
def test_decodes_common_formats(fmt):
    """PNG and JPEG both decode and preprocess without error."""
    arr = preprocess(make_image_bytes(fmt=fmt))
    assert arr.shape == (1, 3, INPUT_SIZE, INPUT_SIZE)
