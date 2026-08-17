"""`GET /api/health` names the build it is running — when told to (#1210).

The failure this closes, measured: a running production instance could not say
which build it was. `/api/health` reported `version: "1.0.0"` — a hardcoded
constant matching no release ever published — so an operator holding a fix that
had merged two days earlier answered "did my fix arrive?" by re-triggering the
500 it was supposed to have removed. There was no cheaper question to ask.

`build_revision` is therefore a **new, separate** field, and part of these tests
are about that separation. `version` could not simply be re-pointed at the build:
the same `settings.app_version` feeds OpenAPI `info.version` (and with it the
published `openapi.json` release asset and the API docs) and the mDNS service
advertisement. Repointing it would have rewritten an API contract version to say
`37cbc06f…` — a silent, wide-reaching breakage in exchange for a diagnostic.
`test_openapi_info_version_is_the_contract_version_not_the_build` is the test
holding that line; the mDNS half is held structurally in
`tests/unit/test_build_revision_wiring.py`, because the announcer only runs
inside the lifespan.

The other part is the **disclosure gate** added by the security remediation. The
endpoint is unauthenticated, and the SHA is not what is sensitive there — the
repository is public — the mapping *this host → that commit* is: it yields the
exact hash-pinned dependency set and, via `git log <revision>..develop`, the
exact list of merged security fixes this instance has not received. So the field
is opt-in (`HEALTH_EXPOSE_BUILD_REVISION`, default off).

**Three states, three observable answers**, and `TestTheDisclosureGate` exists to
keep them apart:

| configuration                | payload                  | meaning                          |
|------------------------------|--------------------------|----------------------------------|
| gate off                     | no `build_revision` key  | configured not to disclose       |
| gate on, nothing baked in    | `"unknown"`              | willing, but no build stamped one |
| gate on, revision baked in   | the SHA                  | the real answer                   |

Collapsing the first two into `"unknown"` would leave the drift-detection
consumer unable to tell a healthy silent instance from a broken build pipeline.

Delimitation: whether the *value* reaches the image at all is build plumbing
(Dockerfile `ARG`/`ENV`, workflow `build-args`) and is asserted in
`tests/unit/test_build_revision_wiring.py`. The `""` → `"unknown"` mapping and
the shape check themselves belong to `Settings` and are asserted in
`tests/unit/test_build_revision_setting.py`. This module asserts only what an
HTTP client actually receives.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config.settings import UNKNOWN_BUILD_REVISION, Settings, settings
from app.main import app

# A full 40-character SHA, because that is the contract: it must compare against
# the image's `org.opencontainers.image.revision` annotation with no truncation.
_BAKED_SHA = "37cbc06fcf0c7d69c07f7abbd3d485cb241070da"


@pytest.fixture
def disclosing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Turn the disclosure gate on for tests about the *value* of the field.

    Patched on the settings singleton rather than through the environment on
    purpose: the singleton is built at import time, so an env var set inside a
    test would arrive too late and the test would pass against an endpoint that
    never read the setting at all.
    """
    monkeypatch.setattr(settings, "health_expose_build_revision", True)


def _health() -> dict:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200, response.text
    return response.json()


class TestTheDisclosureGate:
    """Whether the field appears at all — the security half of the change."""

    def test_the_default_is_not_to_disclose(self) -> None:
        """Off unless an operator opts in, asserted on a freshly built `Settings`.

        A default of `True` would hand every deployment — including the ones whose
        operators never read this file — a public host→commit mapping. Asserting
        it on `Settings()` rather than on the patched singleton is deliberate: this
        is about what a *new* instance does, not about what this test session
        configured.
        """
        assert Settings().health_expose_build_revision is False

    def test_the_key_is_absent_when_the_gate_is_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Absent, not `"unknown"` — the distinction the consumer depends on.

        A revision is deliberately present while the gate is closed, so an
        implementation that reads the setting but forgets to act on it goes red
        here instead of passing on an empty environment.
        """
        monkeypatch.setattr(settings, "health_expose_build_revision", False)
        monkeypatch.setattr(settings, "build_revision", _BAKED_SHA)

        payload = _health()

        assert "build_revision" not in payload

    def test_a_closed_gate_and_an_unbaked_build_are_different_answers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The load-bearing property, asserted as a comparison rather than twice.

        "Configured not to tell you" and "nothing stamped a revision in" are
        different facts about a deployment: the first is healthy, the second means
        the build pipeline lost the value. A consumer that has to act on that
        difference can only do so if the two payloads differ — which an
        implementation reporting `"unknown"` for a closed gate would break while
        satisfying every single-state assertion above.
        """
        monkeypatch.setattr(settings, "build_revision", "")
        monkeypatch.setattr(settings, "health_expose_build_revision", True)
        willing_but_unbaked = _health()

        monkeypatch.setattr(settings, "health_expose_build_revision", False)
        not_disclosing = _health()

        assert willing_but_unbaked["build_revision"] == UNKNOWN_BUILD_REVISION
        assert "build_revision" not in not_disclosing

    def test_closing_the_gate_disturbs_nothing_else(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The gate removes one key and changes no other answer.

        `supported_majors` in particular is the Android client's major-negotiation
        input (#1124) and is unauthenticated for that reason; a disclosure gate on
        a *different* field must not quietly take it with it.
        """
        monkeypatch.setattr(settings, "health_expose_build_revision", False)

        payload = _health()

        assert payload["status"] == "healthy"
        assert payload["version"] == settings.app_version
        assert payload["mode"] == settings.kamerplanter_mode
        assert payload["supported_majors"] == [1]
        assert "build_revision" not in payload


class TestTheReportedValue:
    """What an opted-in instance actually answers."""

    def test_health_reports_unknown_when_no_build_stamped_a_revision(
        self, disclosing: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The unbaked case: a local checkout, the `dev` image target, or any
        image built without the build-arg. The honest answer there is `"unknown"`.

        What must NOT happen is a fabricated one — least of all `app_version`,
        which is always present and always plausible. That substitution would
        reproduce the original defect exactly: an operator reading a
        confident-looking value that tells them nothing about which commit is
        running.
        """
        monkeypatch.setattr(settings, "build_revision", "")

        assert _health()["build_revision"] == UNKNOWN_BUILD_REVISION

    def test_health_reports_the_baked_revision_verbatim(
        self, disclosing: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A baked image reports its SHA unchanged — full length, not shortened."""
        monkeypatch.setattr(settings, "build_revision", _BAKED_SHA)

        assert _health()["build_revision"] == _BAKED_SHA

    def test_a_whitespace_only_revision_is_not_a_build_identity(
        self, disclosing: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`ENV BUILD_REVISION=""` and a Helm value of `"  "` are the unbaked case.

        An empty variable arrives as a present-but-blank string, not as unset. Told
        apart, it would surface as `build_revision: ""` — which an operator's
        tooling would compare against an annotation and silently mismatch.
        """
        monkeypatch.setattr(settings, "build_revision", "   ")

        assert _health()["build_revision"] == UNKNOWN_BUILD_REVISION

    @pytest.mark.parametrize(
        ("malformation", "value"),
        [
            ("too short to abbreviate a commit", "37cbc0"),
            ("longer than a SHA", _BAKED_SHA + "0"),
            ("not hexadecimal", "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"),
            ("upper case, which no annotation ever carries", _BAKED_SHA.upper()),
            ("padded around something that is not a SHA", "  not a revision  "),
            ("markup", "<script>alert(1)</script>"),
            ("a branch name someone wired in by mistake", "refs/heads/develop"),
        ],
    )
    def test_a_malformed_revision_is_reported_as_unknown(
        self, disclosing: None, monkeypatch: pytest.MonkeyPatch, malformation: str, value: str
    ) -> None:
        """Only `[0-9a-f]{7,40}` leaves the endpoint (SEC-002).

        Not an injection defence — there is no injection path here: the value is
        serialised by `JSONResponse` with no interpolation, and its only supplier
        is `github.sha`. The reason is downstream integrity. This payload is read
        by operator tooling and by a CI drift job; a misconfigured value of
        arbitrary length, or one carrying markup, would propagate uncontrolled into
        dashboards and shell pipelines. `"unknown"` is the answer the field already
        has for "I cannot tell you what commit this is", and a value that is not a
        revision is exactly that case.
        """
        monkeypatch.setattr(settings, "build_revision", value)

        assert _health()["build_revision"] == UNKNOWN_BUILD_REVISION, malformation

    def test_a_padded_but_recoverable_sha_still_answers_the_question(
        self, disclosing: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Surrounding whitespace is transport, not malformation — the SHA survives.

        A Helm-rendered or YAML-folded value arrives padded (`"  <sha>\\n"`), and
        the commit inside it is recoverable *exactly*. Rejecting it would report
        "unknown" for a correctly stamped build, which destroys information rather
        than protecting anything: what reaches the client is a clean 40-character
        SHA either way. The integrity rule the shape check enforces is about what
        **leaves** this endpoint, and stripping satisfies it.
        """
        monkeypatch.setattr(settings, "build_revision", f"  {_BAKED_SHA}\n")

        assert _health()["build_revision"] == _BAKED_SHA

    def test_the_pre_existing_fields_are_untouched(self, disclosing: None, monkeypatch: pytest.MonkeyPatch) -> None:
        """Adding a field must not disturb the three that clients already read.

        `supported_majors` in particular is the Android client's major-negotiation
        input (#1124); it is asserted here as well as in `test_api_major_discovery.py`
        because this change edits the very dict literal that produces it.
        """
        monkeypatch.setattr(settings, "build_revision", _BAKED_SHA)

        body = _health()

        assert body["status"] == "healthy"
        assert body["version"] == settings.app_version
        assert body["mode"] == settings.kamerplanter_mode
        assert body["supported_majors"] == [1]

    def test_version_and_build_revision_are_two_different_answers(
        self, disclosing: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The load-bearing property: neither field is derived from the other.

        Without this, an implementation that set `build_revision = app_version`
        would satisfy every "the key is present" assertion above while answering
        the operator's question with the same useless constant that prompted #1210.
        """
        monkeypatch.setattr(settings, "build_revision", _BAKED_SHA)

        body = _health()

        assert body["build_revision"] == _BAKED_SHA
        assert body["version"] == "1.0.0"
        assert body["build_revision"] != body["version"]


def test_openapi_info_version_is_the_contract_version_not_the_build(
    disclosing: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The OpenAPI document keeps describing the API contract, not the image.

    `info.version` is consumed well outside this process — the `openapi.json`
    release asset, the generated API docs, client generators. A build SHA there
    would be a contract change dressed up as a diagnostic, so the separation is
    asserted while a revision is deliberately present and *could* have leaked.
    """
    monkeypatch.setattr(settings, "build_revision", _BAKED_SHA)

    info = app.openapi()["info"]

    assert info["version"] == settings.app_version == "1.0.0"
    assert info["version"] != _BAKED_SHA


def test_the_endpoint_stays_reachable_without_authentication(disclosing: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """An operator diagnoses a broken instance without first obtaining a token.

    The same property major negotiation depends on (#1124), restated here because
    the new field is worthless if the one call an operator makes during an
    incident needs credentials — and because the field is now behind a rate limit,
    which must bound the endpoint without closing it.
    """
    monkeypatch.setattr(settings, "build_revision", _BAKED_SHA)

    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert "build_revision" in response.json()
