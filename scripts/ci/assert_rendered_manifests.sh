#!/usr/bin/env bash
#
# Assert that a rendered manifest stream is complete AND fully imaged.
#
#   scripts/ci/assert_rendered_manifests.sh <rendered.yaml> <min-images>
#
# Split out of skaffold_render_verify.sh so the verdict can be falsified without
# running skaffold: src/backend/tests/unit/guards/test_skaffold_render_assertion.py
# drives this script over crafted manifests and requires a RED for each defect
# shape below. An assertion that has only ever seen its passing input is not
# known to be able to fail (NFR-018 §2).
#
# THE ASSERTION IS POSITIVE, AND THAT IS THE POINT.
#
# The first draft of this check counted *blank* image lines and required zero.
# It was satisfiable over the empty set: a render that stopped emitting `image:`
# altogether — the shape a future library version can produce, and exactly the
# class this gate exists to catch — yields zero blank lines and would have
# printed "every container carries an image reference". The `kind:` count does
# not cover that either, because forty Services and ConfigMaps with no container
# at all clear it.
#
# So this asserts two positive facts instead:
#
#   1. at least <min-images> image references exist, and
#   2. every one of them parses as `repo:tag`.
#
# (2) subsumes the enumerated defect forms rather than listing them, which is
# what the negative version got wrong: it matched `image:`, `image: null` and
# `image: ""`, but NOT `image: :`, `image: <no value>`, `image: repo:` or
# `image: :tag`. Only one of the four shapes actually observed on develop was
# covered; helm rejecting the invalid YAML was doing the real work.
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 <rendered.yaml> <min-images>" >&2
  exit 2
fi

OUTPUT="$1"
MIN_IMAGES="$2"
MIN_KINDS=10

if [[ ! -s "${OUTPUT}" ]]; then
  echo "::error::Rendered manifest '${OUTPUT}' is missing or empty." >&2
  exit 1
fi

# gate-integrity-ok: `grep -c` exits 1 when it counts zero, and under `set -e`
# that would abort before the threshold below is compared — the swallowed status
# is what lets the assertion FAIL LOUDLY on an empty render instead of never
# running. NOTE: check_workflow_gate_integrity.py scans .github/workflows only
# (DEFAULT_SCAN_ROOT), so this marker is PROSE here, not an enforced contract —
# moving the render out of the workflow moved these two `|| true` out of that
# guard's reach. Flagged for follow-up in PR #1579.
kinds=$(grep -c '^kind:' "${OUTPUT}" || true)
if [[ "${kinds}" -lt "${MIN_KINDS}" ]]; then
  echo "::error::Render produced only ${kinds} resources — expected the full chart (>= ${MIN_KINDS})." >&2
  exit 1
fi

images=()
while IFS= read -r image; do
  # Values may be quoted by the renderer; compare the reference itself.
  image="${image%\"}"
  image="${image#\"}"
  images+=("${image}")
done < <(sed -n 's/^[[:space:]]*image:[[:space:]]*//p' "${OUTPUT}")

# The lower bound is the fact the count-only check could not express: a render
# that emits no `image:` field at all must be RED, not silently green.
if [[ "${#images[@]}" -lt "${MIN_IMAGES}" ]]; then
  echo "::error::Render produced ${#images[@]} image reference(s), expected at least ${MIN_IMAGES} — the manifests verify nothing about image wiring." >&2
  exit 1
fi

invalid=()
for image in "${images[@]}"; do
  # `repo:tag`, both halves non-empty and free of whitespace. Rejects the
  # observed breakages: '', 'null', ':', '<no value>', 'repo:', ':tag'.
  if [[ ! "${image}" =~ ^[^[:space:]:]+:[^[:space:]:]+$ ]]; then
    invalid+=("${image}")
  fi
done

if [[ "${#invalid[@]}" -gt 0 ]]; then
  echo "::error::Render produced ${#invalid[@]} malformed image reference(s) — expected 'repo:tag':" >&2
  printf '  %s\n' "${invalid[@]}" >&2
  exit 1
fi

echo "Rendered ${kinds} resources; ${#images[@]} image references, all well-formed."
