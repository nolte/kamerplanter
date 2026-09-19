"""PR #1579 — the permanent falsifier for "the skaffold render was fully imaged".

**The claim.** ``skaffold-verify`` renders the Helm chart together with
skaffold's ``setValueTemplates`` overrides and proves the two wire together.

**Why the claim needed a falsifier.** For the life of that workflow it did not
hold. ``skaffold render`` resolves ``{{.IMAGE_TAG_kamerplanter_backend}}`` from
the *build* result, the job builds nothing, and so every override reached helm
as the literal ``<no value>``. Under ``bjw-s/common`` 5.2.0 that rendered as
``image: null`` for eleven of fifteen containers while the job reported
``Rendered 40 resources`` and went green. Only the 5.2.1 bump (#1547), which
turns the same input into the unparseable ``image: :``, made it visible.

**And the first repair was itself satisfiable over the empty set.** It counted
*blank* image lines and required zero, so a render that emitted no ``image:``
field at all — the very shape a future library version can produce — would have
scored zero and printed "every container carries an image reference". It also
matched only one (``image: null``) of the four malformed shapes actually
observed. That is the third instance of the vacuous-guard family that
``skaffold-verify.yml``'s own header records removing twice before, which is
why the verdict now lives in a script this file can drive directly.

**What this file does.** Runs ``scripts/ci/assert_rendered_manifests.sh`` over
crafted manifest streams — no skaffold, no helm, no network — and requires a
RED for each defect shape, with a positive control on the well-formed stream so
"the fixture reaches the assertion" is measured rather than assumed.
Traces to #1547/#1579 (no TC-ID: a CI gate is not a user-facing case).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ASSERT_SCRIPT = Path(__file__).resolve().parents[5] / "scripts" / "ci" / "assert_rendered_manifests.sh"

# Enough `kind:` lines to clear the resource-count floor on its own, so every
# failure this file asserts is attributable to the IMAGE assertion and not to
# the count. That separation is the point: the count is exactly what passed
# while eleven containers had no image.
_PADDING = "\n".join(f"kind: ConfigMap\nmetadata:\n  name: pad-{n}" for n in range(12))


def _manifest(*image_values: str) -> str:
    containers = "\n".join(
        f"kind: Deployment\nspec:\n  containers:\n    - name: c{n}\n      image: {value}"
        for n, value in enumerate(image_values)
    )
    return f"{_PADDING}\n{containers}\n"


def _run(manifest: str, tmp_path: Path, min_images: int = 2) -> subprocess.CompletedProcess[str]:
    rendered = tmp_path / "rendered.yaml"
    rendered.write_text(manifest, encoding="utf-8")
    return subprocess.run(  # noqa: S603 - fixed argv, repository-local script
        [str(ASSERT_SCRIPT), str(rendered), str(min_images)],
        capture_output=True,
        text=True,
        check=False,
    )


pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash is required to execute the assertion script")


class TestThePositiveControlPasses:
    """Without this, every RED below could come from a broken fixture."""

    def test_well_formed_images_are_accepted(self, tmp_path: Path) -> None:
        result = _run(_manifest("ghcr.io/nolte/kamerplanter-backend:latest", "arangodb:3.12.11"), tmp_path)
        assert result.returncode == 0, result.stderr
        assert "2 image references, all well-formed" in result.stdout


class TestMalformedImagesAreRejected:
    """Each shape below was produced by a real render of this repository's chart."""

    @pytest.mark.parametrize(
        ("value", "shape"),
        [
            ("null", "common 5.2.0 with blanked repository and tag"),
            (":", "common 5.2.1 with blanked repository and tag"),
            ("ghcr.io/nolte/kamerplanter-backend:", "common 5.2.1 with only the tag blanked"),
            ("<no value>", "the literal skaffold passes when a tag is unresolved"),
            ('""', "an explicitly empty reference"),
            (":latest", "a blanked repository"),
        ],
    )
    def test_malformed_reference_fails(self, value: str, shape: str, tmp_path: Path) -> None:
        result = _run(_manifest("arangodb:3.12.11", value), tmp_path)
        assert result.returncode != 0, f"{shape} was accepted: {result.stdout}"
        assert "malformed image reference" in result.stderr


class TestTheAssertionIsNotSatisfiableOverTheEmptySet:
    """The hole in the first repair: no images at all scored zero defects.

    A stream with plenty of resources and no container is the shape a library
    version can produce, and it must be RED — not "every container carries an
    image reference".
    """

    def test_a_render_without_any_image_field_fails(self, tmp_path: Path) -> None:
        result = _run(_PADDING + "\n", tmp_path)
        assert result.returncode != 0, "a render with no image field at all was accepted"
        assert "expected at least" in result.stderr

    def test_fewer_images_than_build_artifacts_fails(self, tmp_path: Path) -> None:
        result = _run(_manifest("arangodb:3.12.11"), tmp_path, min_images=2)
        assert result.returncode != 0, "a render missing an artifact's image was accepted"
        assert "expected at least" in result.stderr


class TestTheResourceFloorStillApplies:
    def test_a_near_empty_render_fails(self, tmp_path: Path) -> None:
        rendered = tmp_path / "rendered.yaml"
        rendered.write_text("kind: ConfigMap\n", encoding="utf-8")
        result = subprocess.run(  # noqa: S603 - fixed argv, repository-local script
            [str(ASSERT_SCRIPT), str(rendered), "1"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "expected the full chart" in result.stderr

    def test_a_missing_render_fails(self, tmp_path: Path) -> None:
        result = subprocess.run(  # noqa: S603 - fixed argv, repository-local script
            [str(ASSERT_SCRIPT), str(tmp_path / "absent.yaml"), "1"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "missing or empty" in result.stderr
