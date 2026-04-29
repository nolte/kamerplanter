#!/usr/bin/env bash
# Translate tests/security/nuclei-suppressions.yaml into Nuclei CLI flags.
# Emits one flag per line on stdout so callers can collect them with a
# while-read loop. Honors `expires` per NFR-014 §6.1: expired entries
# print a warning to stderr and after 30 days of grace make the script
# exit non-zero (so CI fails closed).
#
# Usage:
#   readarray -t flags < <(./scripts/security/build-nuclei-flags.sh)
#   nuclei "${flags[@]}" ...
#
# Or in a workflow:
#   FLAGS="$(./scripts/security/build-nuclei-flags.sh | tr '\n' ' ')"

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." &>/dev/null && pwd)"
SUPPRESSIONS="${KP_NUCLEI_SUPPRESSIONS:-$REPO_ROOT/tests/security/nuclei-suppressions.yaml}"

if [[ ! -f "$SUPPRESSIONS" ]]; then
  exit 0   # nothing to suppress
fi

if ! command -v yq >/dev/null 2>&1; then
  echo "::error::yq (mikefarah/yq) is required." >&2
  exit 1
fi

count=$(yq e '.suppressions | length' "$SUPPRESSIONS")
if [[ "$count" == "0" || -z "$count" ]]; then
  exit 0
fi

today_epoch=$(date -u +%s)
grace_seconds=$((30 * 24 * 60 * 60))
expired_within_grace=0
expired_past_grace=0

for i in $(seq 0 $((count - 1))); do
  template_id=$(yq e ".suppressions[$i].template_id" "$SUPPRESSIONS")
  matched_url=$(yq e ".suppressions[$i].matched_url // \"\"" "$SUPPRESSIONS")
  expires=$(yq e ".suppressions[$i].expires" "$SUPPRESSIONS")
  reason=$(yq e ".suppressions[$i].reason" "$SUPPRESSIONS")

  expires_epoch=$(date -u -d "$expires" +%s 2>/dev/null || echo 0)
  if [[ "$expires_epoch" -eq 0 ]]; then
    echo "::warning::nuclei-suppressions[$i] template_id=$template_id has unparseable expires=$expires; emitting flag anyway." >&2
  elif [[ "$expires_epoch" -lt "$today_epoch" ]]; then
    age=$((today_epoch - expires_epoch))
    if [[ "$age" -gt "$grace_seconds" ]]; then
      expired_past_grace=$((expired_past_grace + 1))
      echo "::error::nuclei-suppressions[$i] template_id=$template_id expired on $expires (>30 days grace exceeded). Renew or remove. Reason was: $reason" >&2
      continue
    else
      expired_within_grace=$((expired_within_grace + 1))
      echo "::warning::nuclei-suppressions[$i] template_id=$template_id expired on $expires (within 30-day grace). Renew before $(date -u -d "@$((expires_epoch + grace_seconds))" +%Y-%m-%d)." >&2
    fi
  fi

  if [[ -n "$matched_url" ]]; then
    # Nuclei does not natively support per-URL exclusion, so we drop the
    # whole template ID for that suppression and rely on the matched_url
    # being documented in the YAML for triage purposes.
    echo "-exclude-id"
    echo "$template_id"
  else
    echo "-exclude-id"
    echo "$template_id"
  fi
done

if [[ "$expired_past_grace" -gt 0 ]]; then
  echo "::error::$expired_past_grace nuclei-suppressions are expired beyond the 30-day grace window. Failing closed." >&2
  exit 1
fi
