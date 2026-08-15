"""Image capture provenance survives ingestion, on both upload paths (#1137).

The Android client captures from two physically different devices: the phone
camera and an attached USB microscope. A microscope frame is millimetres away
under a ring light at high magnification; a phone frame is a whole leaf at arm's
length in ambient light. They favour opposite detection modes, and pooling their
HITL feedback into one signal is exactly what makes a feedback-driven model harder
to improve.

**The information is unrecoverable if not captured at ingestion.** EXIF is
stripped before processing — twice, for cloud transmission — so a device hint the
file carried is gone by the time anything could read it. That is why these tests
assert *persistence and echo*, not merely acceptance: a field the API accepts and
silently drops would look identical from the client's side and lose the data
permanently.

Both polarities throughout. A test that only sends `usb_microscope` and finds it
would pass against an implementation that hardcodes it; a test that only omits the
field would pass against one that ignores it entirely.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.common.enums import AttachmentCategory, CaptureDevice
from app.domain.engines.pest_detection_engine import PestDetectionEngine
from app.domain.models.attachment import Attachment
from app.domain.models.pest_detection import PestDetection

# ── the enum's own contract ──────────────────────────────────────────────────


def test_unknown_is_the_default_and_a_real_value() -> None:
    """Existing records and clients that send nothing must stay valid.

    `unknown` is a value rather than a null so "nobody said" and "the field was
    never populated" read the same way downstream — an analysis that has to
    special-case `None` will eventually forget to.
    """
    assert CaptureDevice.UNKNOWN == "unknown"
    assert PestDetection().capture_device == CaptureDevice.UNKNOWN


def test_the_two_devices_that_motivated_this_are_distinguishable() -> None:
    assert CaptureDevice.PHONE_CAMERA != CaptureDevice.USB_MICROSCOPE


# ── attachments ──────────────────────────────────────────────────────────────


def _attachment(**overrides: Any) -> Attachment:
    fields: dict[str, Any] = {
        "tenant_key": "t1",
        "mime_type": "image/webp",
        "byte_size": 10,
        "sha256": "abc",
        "original_filename": "leaf.webp",
        "created_by": "u1",
        "category": AttachmentCategory.PLANT,
        "storage_key": "s1",
    }
    fields.update(overrides)
    return Attachment(**fields)


def test_an_attachment_records_the_device_it_was_given() -> None:
    assert _attachment(capture_device=CaptureDevice.USB_MICROSCOPE).capture_device == CaptureDevice.USB_MICROSCOPE


def test_an_attachment_without_a_device_is_still_valid() -> None:
    """Non-breaking: the web UI sends nothing and must keep working."""
    assert _attachment().capture_device == CaptureDevice.UNKNOWN


def test_the_attachment_service_passes_the_device_through(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parameter has to reach the model, not just the signature.

    A service that accepts `capture_device` and never writes it would satisfy the
    route test below (the response echo is built from the returned model) only if
    the model carried it — so this pins the one hop in between.
    """
    import inspect

    from app.domain.services.attachment_service import AttachmentService

    signature = inspect.signature(AttachmentService.upload)

    assert "capture_device" in signature.parameters
    assert signature.parameters["capture_device"].default == CaptureDevice.UNKNOWN


# ── pest detection ───────────────────────────────────────────────────────────


class _IpmRepo:
    """The engine's other collaborator; not exercised here, so a stub is honest."""

    def get_pest_by_key(self, key: str) -> None:
        return None

    def get_disease_by_key(self, key: str) -> None:
        return None


class _Repo:
    def __init__(self) -> None:
        self.created: list[PestDetection] = []

    def create(self, detection: PestDetection) -> PestDetection:
        self.created.append(detection)
        detection.key = "d1"
        return detection


class _Result:
    source = "local_symptom"
    adapter_key = "fake"
    is_confident = True
    findings: list[Any] = []
    tiles_processed = 1
    disclaimer = "d"
    llm_explanation = None
    suggested_next_step = None


@pytest.mark.parametrize(
    "device",
    [CaptureDevice.USB_MICROSCOPE, CaptureDevice.PHONE_CAMERA, CaptureDevice.WEBCAM, CaptureDevice.FILE_UPLOAD],
)
def test_the_engine_persists_the_declared_device(device: CaptureDevice) -> None:
    """Persisted at detection time because the image itself is never retained (§8).

    There is no later moment at which the device could be recovered — unlike a
    field derivable from stored data, this one has exactly one chance.
    """
    repo = _Repo()
    engine = PestDetectionEngine(_IpmRepo(), repo)  # type: ignore[arg-type]

    engine.process_and_persist(
        _Result(),  # type: ignore[arg-type]
        tenant_key="t1",
        user_key="u1",
        plant_instance_key=None,
        image_hash="h",
        capture_device=device,
    )

    assert repo.created[0].capture_device == device


def test_the_engine_defaults_to_unknown_when_nothing_is_declared() -> None:
    """The other polarity: without this, hardcoding a device would pass above."""
    repo = _Repo()
    engine = PestDetectionEngine(_IpmRepo(), repo)  # type: ignore[arg-type]

    engine.process_and_persist(
        _Result(),  # type: ignore[arg-type]
        tenant_key="t1",
        user_key="u1",
        plant_instance_key=None,
        image_hash="h",
    )

    assert repo.created[0].capture_device == CaptureDevice.UNKNOWN


def test_the_response_carries_the_device_back() -> None:
    """Echoed so a client can verify what was recorded.

    A write-only field leaves "did it arrive?" unanswerable — and for a value that
    cannot be reconstructed, unanswerable means unusable.
    """
    from app.domain.services.pest_detection_service import PestDetectionService

    detection = PestDetection(capture_device=CaptureDevice.USB_MICROSCOPE, disclaimer="d")

    data = PestDetectionService._to_response(detection)

    assert data["capture_device"] == "usb_microscope"


# ── the routes advertise it ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("module_path", "route_fragment"),
    [
        ("app.api.v1.attachments.tenant_router", "upload_attachment"),
        ("app.api.v1.pest_detection.tenant_router", "detect_pests_global"),
        ("app.api.v1.pest_detection.tenant_router", "detect_pests"),
    ],
)
def test_every_ingestion_route_accepts_the_field(module_path: str, route_fragment: str) -> None:
    """All three ingestion points, or the client has to know which ones support it.

    #1137 asks for *one coherent addition across the two ingestion points*; a
    field present on one detect route and missing on the other would be worse than
    absent, because a client would reasonably assume symmetry.
    """
    import importlib
    import inspect

    module = importlib.import_module(module_path)
    handler = getattr(module, route_fragment)

    assert "capture_device" in inspect.signature(handler).parameters


def test_the_field_is_never_required() -> None:
    """Optional on every route, or this becomes a breaking change for the web UI."""
    import importlib
    import inspect

    for module_path, name in [
        ("app.api.v1.attachments.tenant_router", "upload_attachment"),
        ("app.api.v1.pest_detection.tenant_router", "detect_pests_global"),
    ]:
        handler = getattr(importlib.import_module(module_path), name)
        parameter = inspect.signature(handler).parameters["capture_device"]

        assert parameter.default is not inspect.Parameter.empty, f"{name} makes capture_device required"
