#!/usr/bin/env python3
"""Alert when the running instance is not serving the bytes the chart pins.

Issue #1210 — the LAST hop of the delivery chain, and the only one nothing
measured. A merge reaches the cluster in four hops::

    merge -> docker-publish (GHCR) -> Renovate digest PR (chart pin) -> ArgoCD sync

``scripts/ci/check_digest_freshness.py`` measures hop 3: is the digest in
``helm/kamerplanter/values.yaml`` still the one GHCR serves for the channel? It
was **green throughout the 2026-08-17 incident, and correctly so** — the chart
pinned a perfectly good build. What nobody measured is hop 4: does the *pod*
actually run those bytes? It did not, for days, and the way that surfaced was an
operator re-triggering the bug a merged fix had already removed.

This script asks the instance itself. It compares two values that are the same
40-character git SHA by construction:

  (a) ``org.opencontainers.image.revision`` on the pinned image, written by
      docker/metadata-action from ``github.sha``; and
  (b) ``build_revision`` from ``GET <instance>/api/health``, baked into the image
      by ``src/backend/Dockerfile`` (``ARG``/``ENV BUILD_REVISION``) from
      ``docker-publish.yml`` (``build-args: BUILD_REVISION=${{ github.sha }}``).

Both come from the same expression in the same build, so they are compared in
full. There is no truncation rule anywhere, deliberately: a truncation rule is a
thing to get wrong.

THE INSTANCE HAS THREE ANSWERS, NOT TWO
---------------------------------------
``build_revision`` is disclosed only when the instance sets
``HEALTH_EXPOSE_BUILD_REVISION`` (default **off**). The three well-formed replies
mean three different things and must never be collapsed:

``no build_revision key at all``
    The instance was configured not to disclose its build. **Nothing is wrong
    with the deployment** — but this check cannot run against it. Raises
    :class:`BuildRevisionNotDisclosedError`: RED, no issue, and a message naming
    the setting rather than anything resembling drift. See the reasoning below.
``"unknown"``
    The instance is willing to disclose, but no build stamped a revision into
    the image (a dev image, or a build without the ``BUILD_REVISION`` build-arg).
    The measurement is undetermined: RED, no issue.
``a 40-character hex SHA``
    The real answer. This is the only reply that reaches :func:`decide`.

WHY "NOT DISCLOSED" IS RED AND NOT A GREEN WARNING
--------------------------------------------------
It is tempting to make this state green-with-a-warning, on the grounds that the
deployment is healthy and only the *view* of it is missing — and that a job which
is red for a known reason trains people to ignore it. That reasoning was weighed
and rejected, for three reasons:

1. Scheduling this job **is** the statement "I want this answered". If the far
   end declines to answer, the check is not running — and NFR-018 §2's whole
   thesis is that a check which cannot report a failure is indistinguishable from
   one that is not running. A green run saying "not disclosed" is exactly that
   shape: the eighteen issues of cluster G are checks that reported green on
   nothing.
2. **No other job covers this gap.** Hop 3 (``chart-image-digest-freshness.yml``)
   cannot see whether the instance answers. There is no second guard to lean on,
   which is what would otherwise justify a soft state.
3. It is resolvable by exactly one known action, named in the error. A red that
   names its single fix is a to-do, not an ignore-trainer — and if the operator
   decides *not* to disclose, the correct response is to stop scheduling this job
   (or point it at an instance that does disclose), not to leave a job running
   that structurally cannot answer. The red forces that decision instead of
   letting the repository drift into believing hop 4 is covered when it is not.

THE DISCLOSURE TRADE, STATED PLAINLY
------------------------------------
Enabling ``HEALTH_EXPOSE_BUILD_REVISION`` on an internet-facing instance is a
deliberate decision to disclose. The SHA itself is public, but the mapping
*host -> commit* is not, and it yields the exact patch distance: anyone can run
``git log <revision>..develop`` and read off which fixes the instance has not
got — amplified by this repository publishing its own open security findings.
For the reference deployment that trade was made knowingly. It is not a default
and must not be presented as one.

THE THREE VERDICTS
------------------
``match``
    The instance serves the pinned build. Exit 0; the workflow closes an open
    alert issue.
``within_grace``
    They differ, but the pinned image is younger than ``DRIFT_THRESHOLD_HOURS``
    (default 24, measured from its ``org.opencontainers.image.created``). A pin
    written minutes ago has not had time to roll out; alerting on it would fire
    after every Renovate merge.
``drift``
    They differ and the pinned image has been pinned-and-unserved beyond the
    grace window. This is the incident. Exit 0 — the alert lives in a single
    deduped issue, not in the run status, exactly as the hop-3 job does it.

KNOWN LIMITATION OF THE GRACE CLOCK
-----------------------------------
The window is anchored on the pinned image's creation time, which means **a fresh
re-pin resets it**. A cluster that is stuck while Renovate keeps re-pinning is
therefore invisible for the first ``DRIFT_THRESHOLD_HOURS`` after each re-pin.
Measured against this repository's actual history the exposure is small — image
re-pins run 3-5 days apart, with the occasional same-day pair (two on
2026-08-16, 1.9h apart) — so a multi-day stall is still caught on most days, just
not necessarily on the first. Removing the reset needs a clock this job does not
have: when the *current pin* was written, or how long the instance's own build
has been superseded. Recorded here rather than silently accepted.

FAIL LOUD (NFR-018 section 2)
-----------------------------
An unset ``DEPLOYED_INSTANCE_URL``, an unreachable instance, a reply that is not
a Kamerplanter health payload, an undisclosed or ``"unknown"`` revision, a
revision that is not a full SHA, a missing revision annotation, a missing
``created``, an unparseable manifest, or an image whose own two self-descriptions
disagree is NOT "no drift". It raises, :func:`run` prints ``::error::`` and exits
non-zero WITHOUT writing the report — the run goes red and opens NO issue, so a
transient blip cannot spam the tracker. An undetermined check must never read as
a clean one.

The registry plumbing below deliberately duplicates
``check_digest_freshness.py`` rather than importing it. The two answer different
questions of the same registry on different schedules, and keeping them
independent means a change to the pin-freshness job cannot silently alter the
delivery job. Lifting the shared plumbing into one helper is a worthwhile
follow-up; it is not this change.

Standard library only: this runs on a bare runner with none of the project's
dependencies installed, exactly like the hop-3 job.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

REGISTRY_HOST = "ghcr.io"

#: The image whose build identity answers "what is this instance running?". The
#: backend is the one that serves /api/health; the frontend has no equivalent
#: endpoint, so it is out of scope here by construction, not by oversight.
BACKEND_REPOSITORY = "ghcr.io/nolte/kamerplanter-backend"

REPORT_PATH = "deployed-build-report.json"

HEALTH_PATH = "/api/health"
HTTP_TIMEOUT_SECONDS = 30
DEFAULT_THRESHOLD_HOURS = 24.0

REVISION_ANNOTATION = "org.opencontainers.image.revision"
CREATED_ANNOTATION = "org.opencontainers.image.created"

#: The environment variable src/backend/Dockerfile bakes the build SHA into.
BUILD_REVISION_ENV = "BUILD_REVISION"

#: The instance-side setting that decides whether ``build_revision`` appears in
#: the health payload at all. Default off; enabling it on an internet-facing
#: instance is a deliberate disclosure decision (see the module docstring).
DISCLOSURE_SETTING = "HEALTH_EXPOSE_BUILD_REVISION"

#: What /api/health reports when the instance is willing to disclose but nothing
#: baked a revision in. Mirrors ``app.config.settings.UNKNOWN_BUILD_REVISION`` as
#: a literal: this script runs outside the backend package on a runner where
#: ``app`` is not importable, so it cannot share the constant.
UNKNOWN_BUILD_REVISION = "unknown"

#: ``<channel>@sha256:<64 hex>`` — the shape check_chart_image_digests.py enforces.
PINNED_TAG_RE = re.compile(
    r"^(?P<channel>[\w][\w.\-]*)@(?P<digest>sha256:[0-9a-f]{64})$"
)

FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

#: The shape the endpoint itself accepts before falling back to "unknown". A
#: value matching this but shorter than 40 characters is well-formed yet
#: uncomparable here — see :func:`read_instance_revision`.
ENDPOINT_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")

MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)

VERDICT_MATCH = "match"
VERDICT_WITHIN_GRACE = "within_grace"
VERDICT_DRIFT = "drift"

EXIT_OK = 0
EXIT_UNDETERMINED = 1
EXIT_USAGE = 2

#: An injectable ``urllib.request.urlopen``. Every network read in this module
#: goes through one of these, so a test can drive the whole script — URL
#: construction included — without touching the network.
Opener = Callable[..., Any]


class DeployedBuildError(RuntimeError):
    """A condition under which the check could not be determined — fail loud."""


class BuildRevisionNotDisclosedError(DeployedBuildError):
    """The instance answered, but was configured not to reveal its build.

    A distinct type, not a flavour of the generic error, because it is the one
    undetermined outcome that says nothing whatsoever about the deployment: the
    pod may be perfectly current. Its message must therefore never read as drift.
    """


class BuildRevisionUnknownError(DeployedBuildError):
    """The instance would disclose its build, but no build stamped one in."""


@dataclass(frozen=True)
class PinnedImage:
    """What the chart pins, as the registry describes it."""

    repository: str
    channel: str
    digest: str
    revision: str
    created: datetime
    #: The value of ``BUILD_REVISION`` in the image config's ``Env``, or None when
    #: the image was built before/without the stamp. Not a bool, because a
    #: disagreement with :attr:`revision` is itself a finding.
    stamped_revision: str | None

    @property
    def stamped(self) -> bool:
        """Whether these bytes can identify themselves at runtime at all."""
        return self.stamped_revision is not None


@dataclass(frozen=True)
class Verdict:
    """The outcome of one comparison, and whether it warrants an alert."""

    name: str
    alerting: bool
    headline: str
    explanation: str
    age_hours: float


class RegistryReader:
    """Read manifests and config blobs for one GHCR repository path."""

    def __init__(self, path: str, *, open_url: Opener = urllib.request.urlopen) -> None:
        """Bind the reader to a repository path.

        Args:
            path: Repository path without the registry host, e.g.
                ``nolte/kamerplanter-backend``.
            open_url: Injection seam for ``urllib.request.urlopen``.
        """
        self.path = path
        self._open_url = open_url
        self._token: str | None = None

    def token(self) -> str:
        """Exchange for a pull token, once per reader.

        Basic-auths the CI token when one is present so this keeps working if the
        package is ever made private; anonymous suffices for the public ones —
        the same exchange scripts/ci/pin_chart_image_digests.sh performs.
        """
        if self._token is not None:
            return self._token
        url = f"https://{REGISTRY_HOST}/token?scope=repository:{self.path}:pull&service={REGISTRY_HOST}"
        request = urllib.request.Request(url)
        gh_token = os.environ.get("GHCR_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if gh_token:
            basic = base64.b64encode(f"x-access-token:{gh_token}".encode()).decode()
            request.add_header("Authorization", f"Basic {basic}")
        try:
            with self._open_url(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                token = json.load(response).get("token", "")
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            raise DeployedBuildError(
                f"pull-token exchange failed for {self.path}: {exc}"
            ) from exc
        if not token:
            raise DeployedBuildError(f"registry returned no pull token for {self.path}")
        self._token = str(token)
        return self._token

    def manifest(self, reference: str) -> dict:
        """Fetch a manifest or index by digest or tag."""
        url = f"https://{REGISTRY_HOST}/v2/{self.path}/manifests/{reference}"
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {self.token()}")
        request.add_header("Accept", MANIFEST_ACCEPT)
        try:
            with self._open_url(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                body = json.load(response)
        except urllib.error.HTTPError as exc:
            raise DeployedBuildError(
                f"{self.path}@{reference} manifest request failed: HTTP {exc.code}"
            ) from exc
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            raise DeployedBuildError(
                f"{self.path}@{reference} manifest request failed: {exc}"
            ) from exc
        if not isinstance(body, dict):
            raise DeployedBuildError(
                f"{self.path}@{reference} manifest is not a JSON object"
            )
        return body

    def blob(self, digest: str) -> dict:
        """Fetch a JSON blob (an image config) by digest."""
        url = f"https://{REGISTRY_HOST}/v2/{self.path}/blobs/{digest}"
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {self.token()}")
        try:
            with self._open_url(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                body = json.load(response)
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            raise DeployedBuildError(
                f"{self.path} config blob {digest} unreadable: {exc}"
            ) from exc
        if not isinstance(body, dict):
            raise DeployedBuildError(
                f"{self.path} config blob {digest} is not a JSON object"
            )
        return body


def parse_timestamp(value: str) -> datetime:
    """Parse an OCI timestamp into an aware datetime.

    Args:
        value: An RFC 3339 timestamp, possibly with more than six fractional
            digits — the pinned image config carries nine, which
            ``fromisoformat`` rejects.

    Returns:
        The timestamp, UTC when it carried no offset.

    Raises:
        DeployedBuildError: When the value cannot be parsed.
    """
    normalised = re.sub(r"(\.\d{6})\d+", r"\1", value.replace("Z", "+00:00"))
    try:
        parsed = datetime.fromisoformat(normalised)
    except ValueError as exc:
        raise DeployedBuildError(f"unparseable timestamp {value!r}: {exc}") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _platform_manifest(index: dict) -> dict:
    """Pick the runnable platform manifest entry out of an image index.

    Attestation manifests carry ``platform.os``/``architecture`` of ``unknown``
    and must be skipped; linux/amd64 is preferred, being what the cluster runs.
    """
    entries = [
        entry
        for entry in index.get("manifests") or []
        if isinstance(entry, dict)
        and entry.get("platform", {}).get("os") not in (None, "unknown")
        and entry.get("platform", {}).get("architecture") not in (None, "unknown")
    ]
    if not entries:
        raise DeployedBuildError("image index carries no runnable platform manifest")
    for entry in entries:
        platform = entry.get("platform", {})
        if platform.get("os") == "linux" and platform.get("architecture") == "amd64":
            return entry
    return entries[0]


def _first_annotation(sources: list[dict], key: str) -> str | None:
    """The first non-empty string value for *key* across *sources*."""
    for source in sources:
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _stamped_revision(config: dict) -> str | None:
    """Read ``BUILD_REVISION`` out of an image config's ``Env``.

    Returns:
        The stamped SHA, or None when the variable is absent or empty — the two
        shapes an image built before, or without, the #1210 build-arg has.
    """
    for entry in config.get("config", {}).get("Env") or []:
        if not isinstance(entry, str):
            continue
        name, separator, value = entry.partition("=")
        if name == BUILD_REVISION_ENV and separator:
            return value.strip() or None
    return None


def read_pinned_image(
    reader: RegistryReader, repository: str, channel: str, digest: str
) -> PinnedImage:
    """Resolve the pinned digest into the build identity of those bytes.

    Reads the revision and creation time from the first source that carries them:
    index annotations, then the platform manifest's annotations, then the config
    blob's labels. All three are written by the same docker/metadata-action run,
    so they agree; the chain exists so a single-platform or differently-published
    image does not make the check undeterminable.

    Args:
        reader: Registry access for this repository.
        repository: Fully qualified image name, for messages.
        channel: The tag the digest is pinned under, for messages.
        digest: The pinned ``sha256:...`` digest.

    Returns:
        The pinned image's build identity.

    Raises:
        DeployedBuildError: When the revision, the timestamp, or the manifest
            itself cannot be determined, or when the image's annotation and its
            baked-in stamp disagree.
    """
    index = reader.manifest(digest)
    annotations: list[dict] = [index.get("annotations") or {}]

    manifest = index
    if index.get("manifests"):
        manifest = reader.manifest(_platform_manifest(index)["digest"])
        annotations.append(manifest.get("annotations") or {})

    config_digest = manifest.get("config", {}).get("digest")
    if not config_digest:
        raise DeployedBuildError(
            f"{repository}@{digest}: image manifest has no config digest"
        )
    config = reader.blob(config_digest)
    annotations.append(config.get("config", {}).get("Labels") or {})

    revision = _first_annotation(annotations, REVISION_ANNOTATION)
    if not revision:
        raise DeployedBuildError(
            f"{repository}@{digest}: no {REVISION_ANNOTATION} on the index, the platform "
            "manifest or the config labels — cannot say which commit these bytes are"
        )
    if not FULL_SHA_RE.match(revision):
        raise DeployedBuildError(
            f"{repository}@{digest}: {REVISION_ANNOTATION} is {revision!r}, not a full "
            "40-character git SHA — the endpoint reports a full SHA, so a comparison would "
            "need a truncation rule this check deliberately does not have"
        )

    created = _first_annotation(annotations, CREATED_ANNOTATION) or config.get(
        "created"
    )
    if not created:
        raise DeployedBuildError(
            f"{repository}@{digest}: no {CREATED_ANNOTATION} and no config `created` — the "
            "grace window has no clock to run on"
        )

    stamped_revision = _stamped_revision(config)
    if stamped_revision is not None and stamped_revision != revision:
        raise DeployedBuildError(
            f"{repository}@{digest}: the image describes itself twice and disagrees — annotation "
            f"{revision}, baked-in {BUILD_REVISION_ENV} {stamped_revision}. Comparing the endpoint "
            "against either would be arbitrary; fix the build chain."
        )

    return PinnedImage(
        repository=repository,
        channel=channel,
        digest=digest,
        revision=revision,
        created=parse_timestamp(str(created)),
        stamped_revision=stamped_revision,
    )


def health_url(instance_url: str) -> str:
    """Build the health URL for an instance base URL.

    Args:
        instance_url: Base URL of the deployed instance, with or without a
            trailing slash.

    Returns:
        The absolute ``/api/health`` URL.

    Raises:
        DeployedBuildError: When the value is blank or is not an http(s) URL. A
            mis-set repository variable must go red here rather than produce a
            soft verdict from whatever else urllib would open.
    """
    candidate = (instance_url or "").strip()
    if not candidate:
        raise DeployedBuildError(
            "DEPLOYED_INSTANCE_URL is unset or blank — there is no instance to ask, and an "
            "unasked question is not a clean answer (NFR-018 §2)"
        )
    parsed = urllib.parse.urlparse(candidate)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise DeployedBuildError(
            f"DEPLOYED_INSTANCE_URL {candidate!r} is not an http(s) URL"
        )
    return f"{candidate.rstrip('/')}{HEALTH_PATH}"


def read_instance_revision(
    instance_url: str, *, open_url: Opener = urllib.request.urlopen
) -> str:
    """Ask the running instance which build it serves.

    Args:
        instance_url: Base URL of the deployed instance.
        open_url: Injection seam for ``urllib.request.urlopen``.

    Returns:
        The full 40-character git SHA the instance reports.

    Raises:
        BuildRevisionNotDisclosedError: When the payload carries no ``build_revision``
            key, i.e. the instance runs with the disclosure setting off. This
            says nothing about whether the deployment is current.
        BuildRevisionUnknownError: When the instance discloses ``"unknown"``.
        DeployedBuildError: When the instance is unreachable, does not answer
            with a Kamerplanter health payload, or reports a revision that
            cannot be compared in full.
    """
    url = health_url(instance_url)
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/json")
    try:
        with open_url(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise DeployedBuildError(f"{url} answered HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise DeployedBuildError(f"{url} is unreachable: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DeployedBuildError(f"{url} did not answer with JSON: {exc}") from exc

    if not isinstance(payload, dict) or "status" not in payload:
        raise DeployedBuildError(
            f"{url} did not answer with a Kamerplanter health payload (no `status` field) — "
            "the configured URL probably does not point at this application"
        )

    if "build_revision" not in payload:
        raise BuildRevisionNotDisclosedError(
            f"{url} answered, but discloses no build_revision — the instance runs with "
            f"{DISCLOSURE_SETTING} off (its default). This is NOT drift: the deployment may be "
            "perfectly current, and nothing here says otherwise. This check simply cannot run "
            f"against that instance. Set {DISCLOSURE_SETTING}=true on the watched instance — a "
            "deliberate decision to disclose which commit it runs, since that reveals the exact "
            "patch distance to develop — or stop scheduling this job against it."
        )

    raw = payload.get("build_revision")
    if not isinstance(raw, str):
        raise DeployedBuildError(f"{url} reported a non-string build_revision: {raw!r}")
    revision = raw.strip()

    if revision == UNKNOWN_BUILD_REVISION:
        raise BuildRevisionUnknownError(
            f'{url} discloses build_revision "{UNKNOWN_BUILD_REVISION}" — the instance is willing '
            "to say which build it runs, but no build stamped one in (a dev image, or an image "
            f"built without the {BUILD_REVISION_ENV} build-arg). The measurement is undetermined."
        )
    if not FULL_SHA_RE.match(revision):
        detail = (
            "an abbreviated revision, which cannot be compared against the image annotation "
            "without a truncation rule this check deliberately does not have"
            if ENDPOINT_SHA_RE.match(revision)
            else "neither a git SHA nor the documented fallback"
        )
        raise DeployedBuildError(
            f"{url} reported build_revision {revision!r}: {detail}."
        )
    return revision


def decide(
    pinned: PinnedImage,
    instance_revision: str,
    *,
    now: datetime,
    threshold_hours: float,
) -> Verdict:
    """Compare the pinned build against the running one.

    Args:
        pinned: The build identity of the bytes the chart pins.
        instance_revision: The full SHA the instance reported.
        now: The moment of measurement.
        threshold_hours: Grace window, measured from the pinned image's creation.

    Returns:
        One of the three verdicts documented in the module docstring.
    """
    age_hours = (now - pinned.created).total_seconds() / 3600.0

    if instance_revision == pinned.revision:
        return Verdict(
            name=VERDICT_MATCH,
            alerting=False,
            headline=(
                f"The instance serves the pinned build {pinned.revision[:12]} — the delivery chain is closed."
            ),
            explanation="",
            age_hours=age_hours,
        )

    difference = f"instance {instance_revision[:12]}, pinned {pinned.revision[:12]}"

    if age_hours < threshold_hours:
        return Verdict(
            name=VERDICT_WITHIN_GRACE,
            alerting=False,
            headline=f"Not yet rolled out ({difference}).",
            explanation=(
                f"The pinned image is {age_hours:.1f}h old, inside the {threshold_hours:g}h grace "
                "window. A pin written minutes ago has not had time to reach the cluster."
            ),
            age_hours=age_hours,
        )

    return Verdict(
        name=VERDICT_DRIFT,
        alerting=True,
        headline=f"The running instance is NOT serving the pinned build ({difference}).",
        explanation=(
            f"The chart has pinned this image for {age_hours:.1f}h, beyond the "
            f"{threshold_hours:g}h grace window, and the cluster has not picked it up. The chart "
            "pin itself is fine — chart-image-digest-freshness.yml measures that hop and will be "
            "green, as it was throughout the incident this check was built for — so the stall is "
            "between the pin and the pod: ArgoCD sync, image pull, or a rollout that never "
            "restarted."
        ),
        age_hours=age_hours,
    )


def select_backend_pin(pins: list) -> tuple[str, str]:
    """Find the backend image pin among the chart's image pins.

    Args:
        pins: The list of ``{"repository": ..., "tag": ...}`` mappings the
            workflow extracts from the chart.

    Returns:
        ``(channel, digest)`` for the backend image.

    Raises:
        DeployedBuildError: When the backend pin is absent, malformed, or the
            chart pins the backend at two different digests.
    """
    found: dict[tuple[str, str], None] = {}
    for pin in pins if isinstance(pins, list) else []:
        if (
            not isinstance(pin, dict)
            or str(pin.get("repository", "")) != BACKEND_REPOSITORY
        ):
            continue
        match = PINNED_TAG_RE.match(str(pin.get("tag", "")))
        if not match:
            raise DeployedBuildError(
                f"{BACKEND_REPOSITORY} tag {pin.get('tag')!r} is not `<channel>@sha256:<digest>` "
                "— check_chart_image_digests.py should have caught this pre-merge."
            )
        found[(match.group("channel"), match.group("digest"))] = None

    if not found:
        raise DeployedBuildError(
            f"no {BACKEND_REPOSITORY} pin in the extracted chart images — refusing to report a "
            "clean delivery check against nothing"
        )
    if len(found) > 1:
        rendered = ", ".join(f"{channel}@{digest}" for channel, digest in sorted(found))
        raise DeployedBuildError(
            f"the chart pins {BACKEND_REPOSITORY} at more than one build ({rendered}) — there is "
            "no single 'pinned build' to compare the instance against"
        )
    return next(iter(found))


def build_report(
    pinned: PinnedImage,
    instance_revision: str,
    verdict: Verdict,
    *,
    instance_url: str,
    threshold_hours: float,
) -> dict:
    """Assemble the JSON the workflow's issue step consumes."""
    return {
        "verdict": verdict.name,
        "alerting": verdict.alerting,
        "headline": verdict.headline,
        "explanation": verdict.explanation,
        "threshold_hours": threshold_hours,
        "age_hours": round(verdict.age_hours, 1),
        "instance_url": instance_url,
        "pinned": {
            "repository": pinned.repository,
            "channel": pinned.channel,
            "digest": pinned.digest,
            "revision": pinned.revision,
            "created": pinned.created.isoformat(),
            "stamped": pinned.stamped,
        },
        "instance": {"revision": instance_revision},
    }


def _threshold_hours() -> float:
    """Read DRIFT_THRESHOLD_HOURS, refusing a value that is not a duration."""
    raw = os.environ.get("DRIFT_THRESHOLD_HOURS", "").strip()
    if not raw:
        return DEFAULT_THRESHOLD_HOURS
    try:
        value = float(raw)
    except ValueError as exc:
        raise DeployedBuildError(
            f"DRIFT_THRESHOLD_HOURS is {raw!r}, not a number: {exc}"
        ) from exc
    if value < 0:
        raise DeployedBuildError(
            f"DRIFT_THRESHOLD_HOURS is {value}, which is not a duration"
        )
    return value


def main(
    argv: list[str] | None = None,
    *,
    open_url: Opener = urllib.request.urlopen,
    now: datetime | None = None,
) -> int:
    """Run the delivery check and write the report.

    Args:
        argv: Command line without the program name; expects one path to the
            extracted chart image pins.
        open_url: Injection seam for every network read.
        now: Measurement time, defaulting to the current UTC time.

    Returns:
        0 on any determined verdict — the alert, when there is one, is the issue
        the workflow opens, not this exit code.

    Raises:
        DeployedBuildError: On anything that leaves the verdict undetermined.
    """
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print("usage: check_deployed_build.py <pins.json>", file=sys.stderr)
        return EXIT_USAGE

    instance_url = os.environ.get("DEPLOYED_INSTANCE_URL", "")
    # Validated before any network call so an unset variable is reported as
    # itself, not as a confusing connection error.
    health_url(instance_url)

    threshold_hours = _threshold_hours()

    try:
        with open(arguments[0], encoding="utf-8") as handle:
            pins = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise DeployedBuildError(
            f"cannot read chart image pins from {arguments[0]}: {exc}"
        ) from exc

    channel, digest = select_backend_pin(pins)
    reader = RegistryReader(
        BACKEND_REPOSITORY[len(f"{REGISTRY_HOST}/") :], open_url=open_url
    )
    # The pinned image is resolved FIRST so an "unknown" from the instance can be
    # explained: if the pinned bytes carry no stamp either, no deployment of them
    # could have answered, which is the difference between an actionable red and
    # a baffling one.
    pinned = read_pinned_image(reader, BACKEND_REPOSITORY, channel, digest)
    try:
        instance_revision = read_instance_revision(instance_url, open_url=open_url)
    except BuildRevisionUnknownError as exc:
        if not pinned.stamped:
            raise BuildRevisionUnknownError(
                f"{exc} The pinned image {digest} carries no {BUILD_REVISION_ENV} either, so no "
                "deployment of the pinned bytes can answer this yet — a stamped image has to be "
                "published and pinned first."
            ) from exc
        raise

    verdict = decide(
        pinned,
        instance_revision,
        now=now or datetime.now(timezone.utc),
        threshold_hours=threshold_hours,
    )
    report = build_report(
        pinned,
        instance_revision,
        verdict,
        instance_url=instance_url,
        threshold_hours=threshold_hours,
    )
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(f"Pinned:   {pinned.repository}:{pinned.channel} -> {pinned.revision}")
    print(f"          ({pinned.digest}, built {pinned.created.isoformat()})")
    print(f"Instance: {instance_url}{HEALTH_PATH} -> {instance_revision}")
    print(f"Verdict:  {verdict.name} — {verdict.headline}")
    if verdict.explanation:
        print(f"          {verdict.explanation}")
    return EXIT_OK


def run(argv: list[str] | None = None, **kwargs: Any) -> int:
    """Wrap :func:`main` in the fail-loud contract.

    Returns:
        :data:`EXIT_UNDETERMINED` when the verdict could not be determined —
        loud, and with no report written, so the workflow's issue step no-ops
        and the red run is the only signal.
    """
    try:
        return main(argv, **kwargs)
    except DeployedBuildError as exc:
        print(
            f"::error::deployed build check could not be determined: {exc}",
            file=sys.stderr,
        )
        return EXIT_UNDETERMINED


if __name__ == "__main__":
    raise SystemExit(run())
