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

3. **Only a revision-shaped value leaves the method** (SEC-002). Not against
   injection — there is none: the value comes from `github.sha` and is serialised
   by `JSONResponse` with no interpolation. Against *downstream* damage: the
   payload feeds operator tooling and a CI drift job, so an arbitrary-length or
   markup-bearing misconfiguration would propagate into dashboards and shell
   pipelines. `TestOnlyARevisionShapeIsReported` draws that line, and
   `test_surrounding_whitespace_is_stripped_but_the_sha_survives` marks where it
   deliberately does *not* fall.

Delimitation: whether the field is disclosed **at all** is a separate decision
(`health_expose_build_revision`, asserted in
`tests/api/test_health_build_revision.py`) — this method answers "what is the
revision", never "may you know it". What an HTTP client receives is asserted in
that same module; that the value is actually baked into the image is asserted in
`test_build_revision_wiring.py`.
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


class TestTheDisclosureDefaultIsClosed:
    """Knowing the revision and *publishing* it are two different decisions.

    `/api/health` is unauthenticated. The SHA itself is not the sensitive part —
    the repository is public — the mapping *this host → that commit* is: it yields
    the exact hash-pinned dependency set and, through `git log <revision>..develop`,
    the exact list of merged security fixes this instance has not received. This
    repository publishes its own open findings too, so the reader need not even
    guess which of them apply. An operator may accept that trade for their own
    instance; nobody inherits it by upgrading.

    The endpoint-level behaviour is asserted in
    `tests/api/test_health_build_revision.py`; what is pinned here is the default
    and the variable name, both of which fail silently when they drift.
    """

    def test_the_gate_defaults_to_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HEALTH_EXPOSE_BUILD_REVISION", raising=False)

        assert Settings().health_expose_build_revision is False

    def test_the_gate_is_opened_by_its_environment_variable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`HEALTH_EXPOSE_BUILD_REVISION`, derived from the field name via
        `env_prefix: ""` — the same convention `BUILD_REVISION` relies on. A rename
        on either side leaves an operator with a chart value that does nothing and
        an endpoint that stays silent for reasons nobody can find."""
        monkeypatch.setenv("HEALTH_EXPOSE_BUILD_REVISION", "true")

        assert Settings().health_expose_build_revision is True


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
        """A YAML-folded or shell-quoted value must still compare equal.

        This is the one place the shape check (SEC-002) deliberately does not
        reject: padding is an artefact of the *transport* — Helm rendering, a
        shell quote, a folded YAML scalar — and the commit inside it is recoverable
        exactly. Answering "unknown" for a correctly stamped build because the
        chart appended a newline would destroy information rather than protect
        anything; what leaves the method is a clean 40-character SHA either way,
        which is precisely the integrity property the check exists for.
        """
        monkeypatch.setenv("BUILD_REVISION", f"  {_SHA}\n")

        assert Settings().resolve_build_revision() == _SHA

    def test_a_short_but_valid_abbreviation_is_accepted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Seven characters is git's own shortest unambiguous abbreviation.

        The image never stamps one — `github.sha` is full length — but an operator
        pinning `BUILD_REVISION` by hand while reproducing an incident does, and
        an abbreviation still answers "which commit is this?". The lower bound
        exists to reject noise, not to reject git.
        """
        monkeypatch.setenv("BUILD_REVISION", _SHA[:7])

        assert Settings().resolve_build_revision() == _SHA[:7]

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


class TestOnlyARevisionShapeIsReported:
    """SEC-002: the method returns a SHA or `"unknown"`, and nothing else.

    The threat modelled here is **not** injection. There is no injection path: the
    value's only supplier in production is `github.sha`, and it reaches the client
    through `JSONResponse` with no string interpolation anywhere on the way. The
    threat is a misconfiguration propagating: this payload is consumed by operator
    tooling and by a CI drift-detection job, so an arbitrary-length or
    markup-bearing value would flow uncontrolled into dashboards and shell
    pipelines. The shape check restores what the docstring already claimed the
    field was — a SHA, or an honest admission of not knowing.
    """

    @pytest.mark.parametrize(
        ("malformation", "value"),
        [
            ("too short to abbreviate a commit", "37cbc0"),
            ("longer than a SHA", _SHA + "0"),
            ("not hexadecimal", "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"),
            ("upper case, which no OCI annotation ever carries", _SHA.upper()),
            ("internal whitespace that no strip can rescue", f"{_SHA[:20]} {_SHA[20:]}"),
            ("markup", "<script>alert(1)</script>"),
            ("a branch name wired in by mistake", "refs/heads/develop"),
            ("a shell substitution that never expanded", "${GITHUB_SHA}"),
            ("a full-length value with one non-hex character", f"{_SHA[:-1]}g"),
        ],
    )
    def test_a_malformed_value_resolves_to_unknown(
        self, monkeypatch: pytest.MonkeyPatch, malformation: str, value: str
    ) -> None:
        monkeypatch.setenv("BUILD_REVISION", value)

        assert Settings().resolve_build_revision() == UNKNOWN_BUILD_REVISION, malformation

    def test_the_malformed_value_is_not_echoed_in_any_form(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Rejected means replaced, not sanitised — no fragment survives.

        A "clean it up and report the remainder" implementation would satisfy the
        parametrised cases above for several inputs (`refs/heads/develop` contains
        no hex run of seven, but `<b>deadbeef</b>` does) while still handing a
        consumer a value the build never produced. Replacement is the only
        behaviour that keeps "what /api/health reports" equal to "what the build
        stamped, or nothing".
        """
        monkeypatch.setenv("BUILD_REVISION", "<b>deadbeefdeadbeef</b>")

        resolved = Settings().resolve_build_revision()

        assert resolved == UNKNOWN_BUILD_REVISION
        assert "deadbeef" not in resolved

    def test_the_raw_field_still_carries_what_the_environment_said(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The check lives in the resolution, not in the field.

        `build_revision` keeps the raw value so an operator debugging a mangled
        deployment can still read what was actually configured; only the *reported*
        value is constrained. Pinning this stops a later "just validate it in the
        field" refactor from silently making the misconfiguration invisible.
        """
        monkeypatch.setenv("BUILD_REVISION", "not-a-sha")

        settings = Settings()

        assert settings.build_revision == "not-a-sha"
        assert settings.resolve_build_revision() == UNKNOWN_BUILD_REVISION
