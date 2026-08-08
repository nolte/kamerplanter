#!/usr/bin/env bash
#
# Pin every Kamerplanter-owned image in a chart values file to the IMMUTABLE
# digest published for a release version, and refuse to exit 0 if one escaped.
#
#   pin_chart_image_digests.sh helm/kamerplanter/values.yaml 1.2.3
#
# The released chart is what the GitOps repository consumes, so it is the last
# place a moving reference can hide. Before this, the release rewrote the tag to
# the version and stopped there — better than the `:latest` the develop tree
# carried, but a version tag is only immutable by CONVENTION: re-running the
# publish workflow for an existing tag republishes it against different bytes,
# and nothing downstream can tell. `1.2.3@sha256:…` cannot be republished
# against different bytes; that is the whole difference (#987).
#
# Addressed by YAML PATH, never by rewriting a literal. The sed this logic grew
# out of matched the string `tag: latest`, which made it silently conditional on
# a default nobody guarantees — ship a pinned default and the substitution stops
# matching, the step still exits 0, and the released chart quietly carries
# whatever was committed. It also rewrote commented-out example blocks, because
# a comment contains the literal too.
#
# The digest is read from the registry rather than passed in from the build
# jobs. That is deliberate: it verifies that `<repository>:<version>` actually
# RESOLVES at release time, which a value handed over from a sibling job does
# not. The caller must therefore order this after the image builds — see the
# `needs:` on publish-helm-charts.
#
# Authentication: anonymous for public packages; set GITHUB_TOKEN (or
# GHCR_TOKEN) and it is used for the registry token exchange, which is what
# makes this work for a package that is private or rate-limited.

set -euo pipefail

VALUES_FILE="${1:?usage: $0 <values-file> <version>}"
VERSION="${2:?usage: $0 <values-file> <version>}"

OWNED_GLOB='*ghcr.io/nolte/kamerplanter-*'
REGISTRY_HOST='ghcr.io'

if [[ ! -f "$VALUES_FILE" ]]; then
  echo "::error::$VALUES_FILE does not exist." >&2
  exit 1
fi

# Resolve an image reference to the digest the registry currently serves for it.
# HEAD on the manifest and read `docker-content-digest`, with every manifest
# media type in the Accept header — asking for only the v2 manifest gets a 404
# for a multi-arch image, whose top-level document is an index. The digest
# returned is the index digest, which is exactly what a kubelet resolves.
resolve_digest() {
  local repository="$1" reference="$2"
  local path token digest
  path="${repository#"$REGISTRY_HOST"/}"

  local token_args=(-s)
  if [[ -n "${GHCR_TOKEN:-${GITHUB_TOKEN:-}}" ]]; then
    token_args+=(-u "x-access-token:${GHCR_TOKEN:-${GITHUB_TOKEN}}")
  fi
  token=$(curl "${token_args[@]}" \
    "https://${REGISTRY_HOST}/token?scope=repository:${path}:pull&service=${REGISTRY_HOST}" |
    python3 -c 'import json,sys; print(json.load(sys.stdin).get("token",""))')

  if [[ -z "$token" ]]; then
    echo "::error::Could not obtain a pull token for ${repository}." >&2
    return 1
  fi

  digest=$(curl -sI \
    -H "Authorization: Bearer ${token}" \
    -H 'Accept: application/vnd.oci.image.index.v1+json' \
    -H 'Accept: application/vnd.docker.distribution.manifest.list.v2+json' \
    -H 'Accept: application/vnd.oci.image.manifest.v1+json' \
    -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' \
    "https://${REGISTRY_HOST}/v2/${path}/manifests/${reference}" |
    tr -d '\r' | awk 'tolower($1) == "docker-content-digest:" { print $2 }')

  if [[ ! "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
    echo "::error::${repository}:${reference} did not resolve to a digest." >&2
    echo "::error::Publish the image before packaging the chart." >&2
    return 1
  fi
  printf '%s' "$digest"
}

mapfile -t repositories < <(
  yq "[.. | select(has(\"repository\")) |
       select(.repository == \"$OWNED_GLOB\") | .repository] | unique | .[]" \
    "$VALUES_FILE"
)

if [[ ${#repositories[@]} -eq 0 ]]; then
  # A pin step that finds nothing to pin has stopped measuring the thing it was
  # written for — most likely the values structure moved under it.
  echo "::error::No Kamerplanter images found in $VALUES_FILE — refusing to report success." >&2
  exit 1
fi

for repository in "${repositories[@]}"; do
  digest=$(resolve_digest "$repository" "$VERSION")
  echo "  $repository -> ${VERSION}@${digest}"
  yq -i "(.. | select(has(\"repository\")) |
          select(.repository == \"$repository\") | .tag) = \"${VERSION}@${digest}\"" \
    "$VALUES_FILE"
done

# The rewrite above must not be trusted to have worked. A release that ships a
# chart still pointing at a moving reference is exactly the defect this exists
# to prevent, and the implementation before #983/#987 had no way to notice.
escaped=$(yq "
  [.. | select(has(\"repository\")) |
   select(.repository == \"$OWNED_GLOB\") |
   select(.tag | test(\"^${VERSION//./\\.}@sha256:[0-9a-f]{64}\$\") | not) |
   .repository + \":\" + .tag] | .[]
" "$VALUES_FILE")

if [[ -n "$escaped" ]]; then
  echo "::error::Chart values still carry unpinned Kamerplanter images:" >&2
  printf '%s\n' "$escaped" | sed 's/^/  /' >&2
  exit 1
fi

echo "All Kamerplanter images pinned to ${VERSION}@sha256:…"
