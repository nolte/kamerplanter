#!/usr/bin/env bash
#
# Resolve the Helm chart version for the ref being built, and REFUSE a release
# tag that claims the develop channel (#1222).
#
#   env:
#     REF: ${{ github.ref }}
#     REF_NAME: ${{ github.ref_name }}
#   run: scripts/ci/determine_chart_version.sh
#
# Writes `version=<resolved>` to $GITHUB_OUTPUT when that variable is set, and
# echoes the resolved version on stdout either way.
#
# THE RESOLUTION ITSELF IS UNCHANGED. It is the logic `docker-publish.yml`'s
# `Determine chart version` step has always carried, moved out of the workflow
# verbatim: `${REF_NAME#v}` on a `refs/tags/v*` ref, the empty string on
# anything else. The empty string is load-bearing — it is what keeps the two
# release-only steps that follow (`Update chart version for release` and `Pin
# image digests in chart values for release`) from running on a branch push.
#
# WHAT IS NEW, AND WHY.
#
# `helm/*/Chart.yaml` on develop carries a `-dev` pre-release version, and
# `scripts/check_chart_develop_version.py` keeps it that way in the required
# `static` lane. That guard enforces a WEAKER rule than the one that matters.
# The rule that matters is "the version a non-tag ref publishes must never equal
# a published release version", and it is not statically decidable: the set of
# published versions is not in the checkout. A draft release has no git tag at
# all, and the `static` lane checks out shallow with no tags — so a tag-derived
# rule would be green on a developer's machine and inert in CI.
#
# The weak rule is sufficient only under one premise:
#
#     No release tag ever carries a `dev` pre-release.
#
# This script turns that premise from an assumption into an enforced rule, at
# the one moment it is decidable: on the tag ref itself. Tag any `v<x>-dev`, and
# the release path resolves the chart version to `<x>-dev`, rewrites Chart.yaml
# to it and pushes `charts/kamerplanter:<x>-dev`. Should that string ever equal
# the develop tree's own version — it reads `0.2.1-dev` today, and moves with
# every release — the published release would be silently overwritten by the
# next develop merge: exactly the defect #1222 is
# about (measured: `charts/kamerplanter:0.2.0`, published with release v0.2.0 on
# 2026-08-13, rebuilt from develop on 2026-08-18), reintroduced through the back
# door. Without this rejection the static guard claims more than it enforces.
#
# THE RESERVATION IS NARROW ON PURPOSE. Only the first dot-separated pre-release
# identifier `dev` is refused (`v0.3.0-dev`, `v0.3.0-dev.4`). `v0.3.0-rc1` and
# `v0.3.0-beta.1` stay legal — they cannot collide with the develop channel.
# Build metadata is not a pre-release, so `v0.3.0+dev` is legal too. Case is
# significant: SemVer pre-release identifiers are case-sensitive and the
# committed develop value is lowercase `dev`, so `v0.3.0-DEV` resolves to a
# different OCI tag and cannot collide with it.
#
# WHERE THIS RUNS, AND WHAT IT DOES NOT COVER. As the first substantive step of
# `publish-helm-charts`, before `helm package` and `helm push` — a rejection
# after the push would be theatre. It does NOT stop the eight image jobs, which
# `publish-helm-charts` depends on and which have therefore already pushed
# `<image>:0.3.0-dev` by the time this fires. That is deliberate scope: an image
# tag derived from a release tag collides with nothing develop publishes
# (develop publishes `:latest`), whereas the chart tag does, because `helm push`
# derives the OCI tag verbatim from the chart version and offers no override.
#
# WHAT A REJECTION COSTS. Read this before tagging, because the blast radius is
# wider than this job. The workflow is TRIGGERED by the tag, so by the time this
# runs the GitHub release for that tag already exists and is published — this
# check cannot prevent the release, only the chart. And the fallout does not stop
# at the chart either: `update-release-assets` is chained to this job by
# `needs: [… publish-helm-charts]` with
# `if: … !contains(needs.*.result, 'failure')` (docker-publish.yml), so a failure
# here SKIPS it. A `v0.3.0-dev` tag therefore leaves a published release with no
# chart `.tgz`, no `docker-compose-<version>.yml`, no `.env.example-<version>`
# and no Packages block in its notes — the exact damage #1218 catalogued, this
# time caused by this check rather than by a missing credential. The eight images
# are already in the registry by then, so the release is half-built either way.
#
# That is disclosed, not defended. It is accepted here for two reasons: the
# alternative — publishing a chart under a version reference the next develop
# merge overwrites — is the worse outcome and is not reversible, whereas a
# half-built release is (`gh release delete v0.3.0-dev`, retag as `v0.3.0`,
# re-run). And the cheap place to catch a `-dev` release tag is BEFORE the
# release is created, which is not this file: this script only ever sees a ref
# that has already fired. Moving the rejection there — or decoupling the
# non-chart assets from this job's result — is a delivery decision, deliberately
# not taken as a side effect of #1222.
#
# NO SEMVER VALIDATION BEYOND THE RESERVATION. `Determine chart version` has
# never validated the tag shape, and adding that here would newly reject tags
# for a reason unrelated to #1222.

set -euo pipefail

REF="${REF:?REF must be set to the ref being built (github.ref)}"
REF_NAME="${REF_NAME-}"

# Publish the resolved version to the step output and to stdout. One function so
# the two sinks cannot drift apart.
emit_version() {
  local version="$1"
  if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
    echo "version=${version}" >>"$GITHUB_OUTPUT"
  fi
  printf '%s\n' "$version"
}

if [[ "$REF" != refs/tags/v* ]]; then
  emit_version ""
  exit 0
fi

if [[ -z "$REF_NAME" ]]; then
  echo "::error::REF is ${REF} but REF_NAME is empty — cannot resolve the release version." >&2
  exit 1
fi

VERSION="${REF_NAME#v}"

# The pre-release is everything after the FIRST hyphen, once build metadata
# (`+…`) is dropped. A SemVer core is digits and dots only, so the first hyphen
# is where the pre-release starts.
WITHOUT_BUILD="${VERSION%%+*}"
FIRST_PRERELEASE_ID=""
if [[ "$WITHOUT_BUILD" == *-* ]]; then
  PRERELEASE="${WITHOUT_BUILD#*-}"
  FIRST_PRERELEASE_ID="${PRERELEASE%%.*}"
fi

if [[ "$FIRST_PRERELEASE_ID" == "dev" ]]; then
  echo "::error::Release tag ${REF_NAME} carries the reserved 'dev' pre-release identifier (chart version would be ${VERSION})." >&2
  echo "::error::'dev' names the develop channel: helm/*/Chart.yaml carries a -dev version, and every helm/** merge to develop republishes that OCI tag." >&2
  echo "::error::Releasing under it would give a published release a version reference that the next develop merge overwrites (#1222)." >&2
  echo "::error::Retag without it: 'v${WITHOUT_BUILD%%-*}' for a release, or an -rc/-beta pre-release — both stay legal." >&2
  exit 1
fi

emit_version "$VERSION"
