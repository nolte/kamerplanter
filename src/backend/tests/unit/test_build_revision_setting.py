"""`Settings.build_revision` and its resolution to a reportable value (#1210).

The unit here is the settings object alone — no app, no TestClient, no network.
Two things are pinned:

1. **The environment-variable name.** `Settings` runs with
   `model_config = {"env_prefix": ""}`, so the field name *is* the variable name:
   `build_revision` reads `BUILD_REVISION`. That is not a detail — it is the
   contract the Dockerfile's `ENV BUILD_REVISION` relies on. Rename the field
   without renaming the `ENV` and the endpoint silently reports `"unknown"`
   forever: nothing errors, the build keeps passing, and the diagnostic is dead
   exactly when it is needed. `test_the_environment_variable_is_build_revision`
   is what makes that rename go red.

2. **Absent and blank are the same case.** An unset variable and the
   `ENV BUILD_REVISION=""` an unbaked image carries must both resolve to
   `"unknown"`.

Delimitation: what an HTTP client receives is asserted in
`tests/api/test_health_build_revision.py`; that the value is actually baked into
the image is asserted in `test_build_revision_wiring.py`.
"""

from __future__ import annotations

import pytest

from app.config.settings import UNKNOWN_BUILD_REVISION, Settings

_SHA = "37cbc06fcf0c7d69c07f7abbd3d485cb241070da"


class TestTheDefaultIsHonest:
    """Nothing baked in => say so, rather than guess."""

    def test_the_field_defaults_to_empty(self) -> None:
        """The raw field is empty, not pre-filled with a plausible-looking value."""
        assert Settings().build_revision == ""

    def test_an_unset_variable_resolves_to_unknown(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BUILD_REVISION", raising=False)

        assert Settings().resolve_build_revision() == UNKNOWN_BUILD_REVISION

    def test_an_empty_variable_resolves_to_unknown(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`ENV BUILD_REVISION=${BUILD_REVISION}` with an empty ARG sets it blank.

        This is the exact shape an image built without the build-arg ships with,
        so it is the case that decides whether the fallback works in practice.
        Present-but-empty is not unset, and pydantic reports it as `""`.
        """
        monkeypatch.setenv("BUILD_REVISION", "")

        assert Settings().resolve_build_revision() == UNKNOWN_BUILD_REVISION

    def test_a_whitespace_only_variable_resolves_to_unknown(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A Helm value rendered from an unset key arrives as whitespace."""
        monkeypatch.setenv("BUILD_REVISION", "   ")

        assert Settings().resolve_build_revision() == UNKNOWN_BUILD_REVISION

    def test_unknown_is_never_derived_from_the_app_version(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The substitution that would recreate #1210 in a new disguise.

        `app_version` is always populated and always looks like an answer. Falling
        back to it would leave the operator exactly where they started — holding a
        confident value that says nothing about which commit is running.
        """
        monkeypatch.delenv("BUILD_REVISION", raising=False)
        settings = Settings()

        assert settings.resolve_build_revision() != settings.app_version


class TestTheEnvironmentContract:
    """The variable name is part of the wiring, so it is pinned like one."""

    def test_the_environment_variable_is_build_revision(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`BUILD_REVISION` is what the Dockerfile sets; the field must read it.

        A rename on either side breaks the chain *silently* — the endpoint would
        report `"unknown"` on a properly built image and nothing would be red.
        """
        monkeypatch.setenv("BUILD_REVISION", _SHA)

        assert Settings().build_revision == _SHA

    def test_the_value_is_reported_verbatim(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Full length, unnormalised: it is compared byte-for-byte against the
        image's `org.opencontainers.image.revision` annotation, so any truncation
        or case-folding here turns a match into a mismatch."""
        monkeypatch.setenv("BUILD_REVISION", _SHA)

        resolved = Settings().resolve_build_revision()

        assert resolved == _SHA
        assert len(resolved) == 40

    def test_surrounding_whitespace_is_stripped_but_the_sha_survives(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A YAML-folded or shell-quoted value must still compare equal."""
        monkeypatch.setenv("BUILD_REVISION", f"  {_SHA}\n")

        assert Settings().resolve_build_revision() == _SHA

    def test_build_revision_does_not_disturb_the_app_version(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The two fields are independent — setting one must not move the other.

        `app_version` feeds OpenAPI `info.version`, the mDNS advertisement and the
        Sentry release; a build variable that reached any of those would be an
        unannounced contract change.
        """
        monkeypatch.setenv("BUILD_REVISION", _SHA)

        settings = Settings()

        assert settings.app_version == "1.0.0"
        assert settings.build_revision == _SHA
