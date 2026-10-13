"""#2108 — every image decode under ``app/`` goes through the shared pixel ceiling.

The defect class: a module opens caller-supplied image bytes with Pillow and
relies on Pillow's own ``Image.MAX_IMAGE_PIXELS`` (a *warning* at ~89 MPx, an
error only at ~178 MPx) instead of the product's 40 MPx ceiling. #2108 found it
in the attachment pipeline — ``exif_stripper`` and ``thumbnail_generator`` — while
two siblings (``cv_diagnosis``, ``recognition``) carried their own copy of the
40 MPx constant. A 445 KB PNG of 12 000 x 12 000 px passed and was decoded; the
EXIF strip then materialised every pixel as a Python tuple (measured: 80 bytes
per pixel, ~11.5 GB for that file).

The class is not those two modules: it is **every call that hands bytes to a
Pillow decoder** — ``Image.open`` in any spelling (``PIL.Image.open``, an
aliased ``Image``, ``from PIL.Image import open``) and the incremental
``ImageFile.Parser`` — in every module under ``app/``. Each must sit in
:data:`_ALLOWED_MODULE`, the module that checks ``width x height`` from the
header before anything is decoded (``app.common.image_bounds.open_bounded_image``).
Every other module reaches Pillow's decoders through it.

The same scan refuses ``Image.getdata()``: materialising every pixel as a Python
object is what turned a 40 MPx photo into gigabytes, and no caller under ``app/``
needs pixel tuples.

**What this predicate cannot see** (so nobody reads green as more than it is):
a decoder reached through ``getattr``/``importlib``, a third-party library that
decodes images internally, and images decoded outside ``app/`` (the inference
and knowledge sidecars are separate services). Pillow's process-global
``Image.MAX_IMAGE_PIXELS``, which ``app.common.image_bounds`` lowers on import, is
the backstop for those inside this process.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[3] / "app"

#: The one module allowed to call a Pillow decoder.
_ALLOWED_MODULE = APP / "common" / "image_bounds.py"

#: Pinned so a scan that silently stops reaching the call sites fails instead of
#: going green: the modules that decode images through the shared helper.
_EXPECTED_HELPER_USERS = frozenset(
    {
        "app/domain/engines/storage/exif_stripper.py",
        "app/domain/engines/storage/thumbnail_generator.py",
        "app/api/v1/tenant_scoped/cv_diagnosis/tenant_router.py",
        "app/api/v1/recognition/tenant_router.py",
    }
)


def _pil_image_aliases(tree: ast.AST) -> tuple[set[str], set[str], set[str]]:
    """Names bound to ``PIL.Image``, to ``PIL``, and to ``PIL.Image.open`` / ``ImageFile.Parser``."""
    image_names: set[str] = set()
    pil_names: set[str] = set()
    decoder_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "PIL":
            for alias in node.names:
                if alias.name == "Image":
                    image_names.add(alias.asname or alias.name)
                if alias.name == "ImageFile":
                    image_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module in {"PIL.Image", "PIL.ImageFile"}:
            for alias in node.names:
                if alias.name in {"open", "Parser"}:
                    decoder_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "PIL.Image":
                    if alias.asname:
                        image_names.add(alias.asname)
                    else:
                        pil_names.add("PIL")
                elif alias.name == "PIL":
                    pil_names.add(alias.asname or "PIL")
    return image_names, pil_names, decoder_names


def _findings_in_source(source: str) -> list[str]:
    """Every Pillow decoder call and every ``.getdata()`` call in *source*, as ``line: text``."""
    tree = ast.parse(source)
    image_names, pil_names, decoder_names = _pil_image_aliases(tree)
    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in decoder_names:
            findings.append(f"{node.lineno}: {func.id}(...)")
        elif isinstance(func, ast.Attribute):
            owner = func.value
            if func.attr in {"open", "Parser"} and isinstance(owner, ast.Name) and owner.id in image_names:
                findings.append(f"{node.lineno}: {owner.id}.{func.attr}(...)")
            elif (
                func.attr in {"open", "Parser"}
                and isinstance(owner, ast.Attribute)
                and owner.attr in {"Image", "ImageFile"}
                and isinstance(owner.value, ast.Name)
                and owner.value.id in pil_names
            ):
                findings.append(f"{node.lineno}: {owner.value.id}.{owner.attr}.{func.attr}(...)")
            elif func.attr == "getdata":
                findings.append(f"{node.lineno}: .getdata()")
    return findings


def _app_modules() -> list[Path]:
    return sorted(path for path in APP.rglob("*.py") if "__pycache__" not in path.parts)


def _relative(path: Path) -> str:
    return path.relative_to(APP.parent).as_posix()


def test_no_module_but_the_ceiling_calls_a_pillow_decoder() -> None:
    offenders: list[str] = []
    for path in _app_modules():
        if path == _ALLOWED_MODULE:
            continue
        for finding in _findings_in_source(path.read_text(encoding="utf-8")):
            offenders.append(f"{_relative(path)}:{finding}")
    assert not offenders, (
        "decode images through app.common.image_bounds.open_bounded_image (40 MPx ceiling, #2108):\n"
        + "\n".join(offenders)
    )


def test_the_ceiling_module_is_where_the_decoder_is_called() -> None:
    """Non-vacuity: the allowed module exists and the scan sees its decoder call."""
    assert _ALLOWED_MODULE.is_file()
    assert any("open" in finding for finding in _findings_in_source(_ALLOWED_MODULE.read_text(encoding="utf-8")))


def _calls_the_ceiling(source: str) -> bool:
    """Whether *source* calls ``open_bounded_image`` or ``image_dimensions`` (parsed, not text-matched)."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name in {"open_bounded_image", "image_dimensions"}:
                return True
    return False


def test_the_decoding_modules_call_the_ceiling() -> None:
    """Non-vacuity: the modules that decode images reach Pillow through the helper."""
    users = {
        _relative(path)
        for path in _app_modules()
        if path != _ALLOWED_MODULE and _calls_the_ceiling(path.read_text(encoding="utf-8"))
    }
    missing = _EXPECTED_HELPER_USERS - users
    assert not missing, f"these decoding modules no longer call the ceiling: {sorted(missing)}"


@pytest.mark.parametrize(
    "source",
    [
        "from PIL import Image\nImage.open(b)\n",
        "from PIL import Image as I\nI.open(b)\n",
        "import PIL.Image\nPIL.Image.open(b)\n",
        "import PIL\nPIL.Image.open(b)\n",
        "import PIL.Image as PI\nPI.open(b)\n",
        "from PIL.Image import open as o\no(b)\n",
        "from PIL import ImageFile\nImageFile.Parser()\n",
        "from PIL.ImageFile import Parser\nParser()\n",
        "x = img.getdata()\n",
    ],
)
def test_the_scan_flags_every_decoder_spelling(source: str) -> None:
    """Self-test through the same detector the tree scan uses."""
    assert _findings_in_source(source), source


@pytest.mark.parametrize(
    "source",
    [
        "with open(path) as fh:\n    fh.read()\n",
        "from PIL import Image\nImage.new('RGB', (1, 1))\n",
        "import io\nio.open(p)\n",
    ],
)
def test_the_scan_leaves_non_decoding_calls_alone(source: str) -> None:
    assert not _findings_in_source(source), source
