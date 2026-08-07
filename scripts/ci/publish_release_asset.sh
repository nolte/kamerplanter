#!/usr/bin/env bash
#
# Attach files to a GitHub release, refusing to change an asset that is already
# PUBLISHED. A published version reference must resolve to the same bytes
# forever (spec/project/continuous-delivery §B); a consumer who downloaded an
# asset yesterday has no way to notice that today's file under the same tag is
# a different one.
#
# This replaces `gh release upload --clobber`. That flag was not gratuitous:
# without it a re-run of a publish job dies on the asset its first run
# uploaded, so simply deleting it would trade a mutable release for a broken
# retry. Idempotence is therefore re-established by decision, per asset:
#
#   absent                                 -> upload
#   present, release still a DRAFT         -> replace (nothing is published
#                                             yet, so no immutability promise
#                                             exists; this is the path a
#                                             re-dispatch normally takes,
#                                             because this project pushes the
#                                             tag BEFORE publishing the draft)
#   present, release PUBLISHED, identical  -> skip, exit 0 (re-run stays green)
#   present, release PUBLISHED, different  -> FAIL (the valuable half: a
#                                             differing byte under a published
#                                             tag means something is wrong and
#                                             must be seen, not overwritten)
#
# Recovery from the last case is forward-only: publish a new version. Replacing
# a published asset stays possible, but only as a deliberate out-of-band act
# (`gh release delete-asset`), never as a side effect of a re-run.
#
# Compare modes:
#   bytes        exact byte comparison, for deterministically generated files
#                (the OpenAPI export renders with sort_keys=True; the compose
#                file and .env.example are sed/cp from the tagged tree).
#   tar-content  unpack both .tgz and diff the trees. `helm package` stamps tar
#                headers with time.Now(), so two packagings of an IDENTICAL
#                chart never compare equal byte-wise. Comparing the unpacked
#                content is what makes "identical" mean identical chart rather
#                than identical archive — without it, the rule above would fail
#                every legitimate chart re-run.
#
# The correct long-term home for this is nolte/gh-plumbing: its
# reusable-release-publish.yml attaches the HACS asset with --clobber and
# carries the same defect for every consumer. Kept local as an interim measure
# until that upstream work package lands (github-actions-best-practices §E).
#
# Requires: gh (GH_TOKEN in the environment), jq, tar, diff.

set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <tag> <bytes|tar-content> <file>..." >&2
  exit 2
fi

TAG=$1
MODE=$2
shift 2

case "$MODE" in
  bytes | tar-content) ;;
  *)
    echo "::error::Unknown compare mode '$MODE' (expected 'bytes' or 'tar-content')." >&2
    exit 2
    ;;
esac

WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

# One read for the whole run. `gh release view` resolves a draft by tag name as
# well as a published release, which is the same resolution the upload itself
# relies on; a missing release fails here, loudly, before anything is written.
META=$(gh release view "$TAG" --json isDraft,assets)
IS_DRAFT=$(printf '%s' "$META" | jq -r '.isDraft')

n=0
for file in "$@"; do
  n=$((n + 1))
  if [[ ! -f "$file" ]]; then
    echo "::error::'$file' does not exist — refusing to report a successful upload for a file this run never produced." >&2
    exit 1
  fi
  name=$(basename "$file")

  if ! printf '%s' "$META" | jq -e --arg n "$name" '[.assets[].name] | index($n) != null' >/dev/null; then
    gh release upload "$TAG" "$file"
    echo "::notice::Attached new asset '$name' to $TAG."
    continue
  fi

  if [[ "$IS_DRAFT" == "true" ]]; then
    # Not yet published: replacing breaks no promise, and this keeps a
    # re-dispatch of a failed release run working.
    gh release upload "$TAG" "$file" --clobber
    echo "::notice::Replaced '$name' on the still-DRAFT release $TAG (nothing published yet)."
    continue
  fi

  dir="$WORKDIR/$n"
  mkdir -p "$dir/published"
  gh release download "$TAG" --pattern "$name" --dir "$dir/published"
  published="$dir/published/$name"
  if [[ ! -f "$published" ]]; then
    echo "::error::Could not download the published asset '$name' from $TAG — refusing to guess whether it matches." >&2
    exit 1
  fi

  equal=false
  case "$MODE" in
    bytes)
      if cmp -s "$file" "$published"; then equal=true; fi
      ;;
    tar-content)
      mkdir -p "$dir/local-tree" "$dir/published-tree"
      tar -xzf "$file" -C "$dir/local-tree"
      tar -xzf "$published" -C "$dir/published-tree"
      if diff -r "$dir/local-tree" "$dir/published-tree" >"$dir/diff.txt" 2>&1; then
        equal=true
      fi
      ;;
  esac

  if [[ "$equal" == "true" ]]; then
    echo "::notice::'$name' is already published on $TAG with identical content — skipping the upload."
    continue
  fi

  {
    echo "::error::'$name' is already published on $TAG and this run produced DIFFERENT content."
    echo "A published version reference must resolve to the same bytes forever"
    echo "(spec/project/continuous-delivery §B), so this run refuses to overwrite it."
    echo "Recovery is forward-only: publish a new version. If the published asset is"
    echo "known to be wrong and must go, remove it deliberately and re-run:"
    echo "  gh release delete-asset $TAG $name"
  } >&2
  if [[ -s "${dir}/diff.txt" ]]; then
    echo "--- difference (first 50 lines) ---" >&2
    head -n 50 "$dir/diff.txt" >&2
  fi
  exit 1
done
