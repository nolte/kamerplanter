#!/usr/bin/env bash
#
# Render the Skaffold pipeline offline and assert the result is a complete,
# fully-imaged set of manifests.
#
#   scripts/ci/skaffold_render_verify.sh [output-file]
#
# Shared by `.github/workflows/skaffold-verify.yml` and the `verify:skaffold`
# task so the two cannot drift: the task documents itself as "the CI job's
# exact invocation", and that only stays true if both call this script.
#
# WHY THE `--images` FLAGS EXIST (issue: common 5.2.1 render break).
#
# `skaffold render` resolves `setValueTemplates` such as
# `{{.IMAGE_TAG_kamerplanter_backend}}` from the *build* result. This job
# builds nothing, so without help every one of those templates renders to Go's
# literal `<no value>` and skaffold passes it on as
# `--set controllers.backend.containers.main.image.tag=<no value>`.
#
# That was never harmless — it was merely silent. Measured on `develop`:
#
#   bjw-s common 5.2.0 → `image: null`   (parses; asserts nothing; GREEN)
#   bjw-s common 5.2.1 → `image: :`      (invalid YAML; helm aborts; RED)
#
# 5.2.1 replaced the `tpl`-per-field calls with
# `bjw-s.common.lib.common.renderString` plus a `TemplateRendering.valuesRendered`
# flag, so an already-evaluated value is no longer re-rendered. For the blanked
# image fields the evaluated tag measures length 0 under 5.2.0 and length 10
# under 5.2.1 — 10 being `<no value>` — which flips
# `{{- if $imageTag -}}` from false to true and appends the bare colon.
#
# So the bump did not break the chart: `helm lint` and `helm template` are green
# on 5.2.1. It removed the masking that let this job render five first-party
# containers with NO IMAGE AT ALL and still report "Rendered 40 resources".
# Feeding real references fixes the render and makes the assertion mean
# something, which is why this is not solved by pinning common back to 5.2.0.
#
# The tag below is a placeholder on purpose: `--digest-source=none` takes tags
# straight from the manifests and this job never contacts a registry. The point
# is that the chart and skaffold's overrides wire together, not that any
# particular tag exists.
set -euo pipefail

OUTPUT="${1:-rendered-manifests.yaml}"
PLACEHOLDER_TAG="${SKAFFOLD_RENDER_PLACEHOLDER_TAG:-ci-render-verify}"
MIN_KINDS="${SKAFFOLD_RENDER_MIN_KINDS:-10}"

# The artifact list comes from skaffold itself rather than a second hard-coded
# copy, so adding a build artifact cannot silently reintroduce a `<no value>`
# image. `diagnose` is the same resolved configuration the render below uses.
mapfile -t artifacts < <(
  skaffold diagnose --yaml-only \
    | sed -n 's/^[[:space:]]*-[[:space:]]*image:[[:space:]]*//p' \
    | sort -u
)

if [[ "${#artifacts[@]}" -eq 0 ]]; then
  echo "::error::skaffold diagnose reported no build artifacts — refusing to render, because every image override would silently become '<no value>'." >&2
  exit 1
fi

image_flags=()
for artifact in "${artifacts[@]}"; do
  image_flags+=(--images "${artifact}:${PLACEHOLDER_TAG}")
done

echo "Rendering with ${#artifacts[@]} resolved image reference(s): ${artifacts[*]}"

skaffold render \
  --offline=true \
  --digest-source=none \
  "${image_flags[@]}" \
  --output "${OUTPUT}"

# ── Assertions ────────────────────────────────────────────────────────────
# An `--output` file that is empty or near-empty would otherwise pass silently,
# which is the vacuous-success shape this job exists to remove.

# gate-integrity-ok: the guard IS this count, and `grep -c` exits 1 when it
# counts zero. Under `set -e` that would abort before the threshold is
# compared — the swallowed status is what lets the assertion below fail loudly
# on an empty render instead of never running.
kinds=$(grep -c '^kind:' "${OUTPUT}" || true)
if [[ "${kinds}" -lt "${MIN_KINDS}" ]]; then
  echo "::error::Render produced only ${kinds} resources — expected the full chart (>= ${MIN_KINDS})." >&2
  exit 1
fi

# The count above is satisfied by a chart whose containers carry no image, which
# is exactly what this job reported as green for the life of the workflow. Every
# rendered `image:` must therefore be a non-empty reference.
# gate-integrity-ok: same reason as above — `grep -c` exits 1 on zero matches,
# and zero blank images is the PASSING state.
blank_images=$(grep -cE '^[[:space:]]*image:[[:space:]]*(null|"")?[[:space:]]*$' "${OUTPUT}" || true)
if [[ "${blank_images}" -gt 0 ]]; then
  echo "::error::Render produced ${blank_images} container(s) without an image reference — the manifests verify nothing about image wiring." >&2
  grep -nE '^[[:space:]]*image:[[:space:]]*(null|"")?[[:space:]]*$' "${OUTPUT}" >&2
  exit 1
fi

echo "Rendered ${kinds} resources; every container carries an image reference."
