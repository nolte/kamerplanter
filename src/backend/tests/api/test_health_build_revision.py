"""`GET /api/health` names the build it is running (#1210).

The failure this closes, measured: a running production instance could not say
which build it was. `/api/health` reported `version: "1.0.0"` — a hardcoded
constant matching no release ever published — so an operator holding a fix that
had merged two days earlier answered "did my fix arrive?" by re-triggering the
500 it was supposed to have removed. There was no cheaper question to ask.

`build_revision` is therefore a **new, separate** field, and the tests below are
mostly about that separation. `version` could not simply be re-pointed at the
build: the same `settings.app_version` feeds OpenAPI `info.version` (and with it
the published `openapi.json` release asset and the API docs) and the mDNS service
advertisement. Repointing it would have rewritten an API contract version to say
`37cbc06f…` — a silent, wide-reaching breakage in exchange for a diagnostic.
`test_openapi_info_version_is_the_contract_version_not_the_build` is the test
holding that line; the mDNS half is held structurally in
`tests/unit/test_build_revision_wiring.py`, because the announcer only runs
inside the lifespan.

Delimitation: whether the *value* reaches the image at all is build plumbing
(Dockerfile `ARG`/`ENV`, workflow `build-args`) and is asserted in
`tests/unit/test_build_revision_wiring.py`. The `""` → `"unknown"` mapping itself
belongs to `Settings` and is asserted in `tests/unit/test_build_revision_setting.py`.
This module asserts only what an HTTP client actually receives.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config.settings import UNKNOWN_BUILD_REVISION, settings
from app.main import app

# A full 40-character SHA, because that is the contract: it must compare against
# the image's `org.opencontainers.image.revision` annotation with no truncation.
_BAKED_SHA = "37cbc06fcf0c7d69c07f7abbd3d485cb241070da"


def _health() -> dict:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200, response.text
    return response.json()


def test_health_reports_unknown_when_no_build_stamped_a_revision() -> None:
    """The unbaked case, asserted by setting no environment variable at all.

    This is the state of a local checkout, of the `dev` image target and of any
    image built without the build-arg. The honest answer there is `"unknown"`.

    What must NOT happen is a fabricated one — least of all `app_version`, which
    is always present and always plausible. That substitution would reproduce the
    original defect exactly: an operator reading a confident-looking value that
    tells them nothing about which commit is running.
    """
    assert _health()["build_revision"] == UNKNOWN_BUILD_REVISION


def test_health_reports_the_baked_revision_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    """A baked image reports its SHA unchanged — full length, not shortened.

    Patched on the settings singleton rather than through the environment on
    purpose: the singleton is built at import time, so an env var set inside a
    test would arrive too late and this test would pass against a broken endpoint
    that never read the setting at all.
    """
    monkeypatch.setattr(settings, "build_revision", _BAKED_SHA)

    assert _health()["build_revision"] == _BAKED_SHA


def test_a_whitespace_only_revision_is_not_a_build_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """`ENV BUILD_REVISION=""` and a Helm value of `"  "` are the unbaked case.

    An empty variable arrives as a present-but-blank string, not as unset. Told
    apart, it would surface as `build_revision: ""` — which an operator's tooling
    would compare against an annotation and silently mismatch.
    """
    monkeypatch.setattr(settings, "build_revision", "   ")

    assert _health()["build_revision"] == UNKNOWN_BUILD_REVISION


def test_the_pre_existing_fields_are_untouched(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_version_and_build_revision_are_two_different_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    """The load-bearing property: neither field is derived from the other.

    Without this, an implementation that set `build_revision = app_version` would
    satisfy every "the key is present" assertion above while answering the
    operator's question with the same useless constant that prompted #1210.
    """
    monkeypatch.setattr(settings, "build_revision", _BAKED_SHA)

    body = _health()

    assert body["build_revision"] == _BAKED_SHA
    assert body["version"] == "1.0.0"
    assert body["build_revision"] != body["version"]


def test_openapi_info_version_is_the_contract_version_not_the_build(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_the_endpoint_stays_reachable_without_authentication(monkeypatch: pytest.MonkeyPatch) -> None:
    """An operator diagnoses a broken instance without first obtaining a token.

    The same property major negotiation depends on (#1124), restated here because
    the new field is worthless if the one call an operator makes during an
    incident needs credentials.
    """
    monkeypatch.setattr(settings, "build_revision", _BAKED_SHA)

    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert "build_revision" in response.json()
