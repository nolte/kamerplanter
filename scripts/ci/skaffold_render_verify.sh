#!/usr/bin/env bash
#
# Render the Skaffold pipeline offline and assert the result is a complete,
# fully-imaged set of manifests.
#
#   scripts/ci/skaffold_render_verify.sh [output-file]
#
# Shared by `.github/workflows/skaffold-verify.yml` and the `verify:skaffold`
# task so the two cannot drift: the task documents itself as "the CI job's
# exact invocation", and that only stays true if both call this script. The
# verdict itself lives in assert_rendered_manifests.sh, which is falsifiable
# without skaffold (see that file, and the guard test that drives it).
#
# WHY THE `--images` FLAGS EXIST (PR #1579).
#
# `skaffold render` resolves `setValueTemplates` such as
# `{{.IMAGE_TAG_kamerplanter_backend}}` from the *build* result. This job
# builds nothing, so without help every one of those templates renders to Go's
# literal `<no value>` and skaffold passes it on as
# `--set controllers.backend.containers.main.image.tag=<no value>`.
#
# That was never harmless — it was merely silent. Measured on `develop`, across
# all three modules (kp + ki + recognition; no module filter is applied):
#
#   bjw-s common 5.2.0 → `image: null` for 11 of 15 containers; 40 resources;
#                        job GREEN
#   bjw-s common 5.2.1 → `image: :`, invalid YAML, helm aborts; job RED
#
# 5.2.1 replaced the `tpl`-per-field calls with
# `bjw-s.common.lib.common.renderString` plus a `TemplateRendering.valuesRendered`
# flag, so an already-evaluated value is no longer re-rendered.
#
# The bump did not break the chart: `helm lint` and `helm template` are green on
# 5.2.1, because the chart's own defaults carry real references throughout — the
# malformed value can only enter through skaffold's overrides. 5.2.1 removed the
# masking that let this job render eleven containers with no image at all and
# still report "Rendered 40 resources". Feeding real references fixes the render
# and makes the assertion mean something, which is why this is not solved by
# pinning common back to 5.2.0.
#
# The tag below is a placeholder on purpose: `--digest-source=none` takes tags
# straight from the manifests and this job never contacts a registry. The point
# is that the chart and skaffold's overrides wire together, not that any
# particular tag exists. (Threading the real `skaffold build` output in here
# instead would verify more; see PR #1579 for why that is a separate decision.)
set -euo pipefail

OUTPUT="${1:-rendered-manifests.yaml}"

# Deliberately NOT configurable from the environment: a gate whose verdict the
# caller can relax is a gate the caller can switch off.
PLACEHOLDER_TAG="ci-render-verify"

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

# The artifact list comes from skaffold itself rather than a second hard-coded
# copy, so adding a build artifact cannot silently reintroduce a `<no value>`
# image. `diagnose` is the same resolved configuration the render below uses.
#
# Run it into a file first: `mapfile < <(cmd)` discards the command's exit
# status, which would report a crashed `skaffold diagnose` as "no artifacts" —
# fail-closed, but naming a cause that was never measured.
diagnosis="$(mktemp)"
trap 'rm -f "${diagnosis}"' EXIT
if ! skaffold diagnose --yaml-only >"${diagnosis}"; then
  echo "::error::skaffold diagnose failed — cannot determine the build artifacts to render with." >&2
  exit 1
fi

artifacts=()
while IFS= read -r artifact; do
  artifacts+=("${artifact}")
done < <(sed -n 's/^[[:space:]]*-[[:space:]]*image:[[:space:]]*//p' "${diagnosis}" | sort -u)

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

# Every build artifact must appear at least once, which is the lower bound the
# previous count-only assertion could not express.
"${script_dir}/assert_rendered_manifests.sh" "${OUTPUT}" "${#artifacts[@]}"
