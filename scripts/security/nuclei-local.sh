#!/usr/bin/env bash
# Run Nuclei locally against a Kamerplanter target with the same template
# set, severity filter and suppression list that CI uses. Lets developers
# reproduce a CI finding without pushing.
#
# Spec: spec/nfr/NFR-014_Nuclei-Security-Scanning.md §4.4
#
# Usage:
#   ./scripts/security/nuclei-local.sh --profile pr [TARGET]
#   ./scripts/security/nuclei-local.sh --profile full TARGET
#
# TARGET defaults to http://localhost:8000 (backend) plus http://localhost:5173
# (frontend dev server) when --profile pr is selected. The full profile
# requires an explicit TARGET because it is meant to run against staging.
#
# Profiles:
#   pr   — exposure, misconfig, default-login, token-spray, kamerplanter
#          severity medium,high,critical, rate-limit 50, timeout 10
#   full — exposure, misconfig, default-login, cve, vulnerability,
#          kamerplanter severity low,medium,high,critical, rate-limit 100,
#          timeout 15
#
# Required:
#   - nuclei in PATH (https://github.com/projectdiscovery/nuclei)
#   - Nuclei templates checked out to NUCLEI_TEMPLATES_DIR (default:
#     ~/.local/share/nuclei-templates) — pinned in CI via the SHA stored
#     in .github/renovate-pins.yaml.

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." &>/dev/null && pwd)"
PROJECT_TEMPLATES="$REPO_ROOT/tests/security/nuclei-templates"
SUPPRESSIONS="$REPO_ROOT/tests/security/nuclei-suppressions.yaml"
COMMUNITY_TEMPLATES="${NUCLEI_TEMPLATES_DIR:-$HOME/.local/share/nuclei-templates}"

profile=""
target_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      profile="$2"
      shift 2
      ;;
    --profile=*)
      profile="${1#--profile=}"
      shift
      ;;
    --help|-h)
      grep -E '^#( |$)' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    --*)
      echo "::error::Unknown flag $1" >&2
      exit 1
      ;;
    *)
      target_args+=(-u "$1")
      shift
      ;;
  esac
done

if [[ -z "$profile" ]]; then
  echo "::error::--profile {pr|full} is required." >&2
  exit 1
fi

if ! command -v nuclei >/dev/null 2>&1; then
  echo "::error::nuclei not found in PATH. Install via 'go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest' or grab a release binary." >&2
  exit 1
fi

if [[ ! -d "$COMMUNITY_TEMPLATES" ]]; then
  echo "::warning::Community templates not found at $COMMUNITY_TEMPLATES. Phase 2B's CI workflow clones them; locally run 'nuclei -update-templates -update-template-dir $COMMUNITY_TEMPLATES' once." >&2
fi

# Default targets when none supplied (PR profile only).
if [[ ${#target_args[@]} -eq 0 ]]; then
  if [[ "$profile" == "pr" ]]; then
    target_args=(-u "http://localhost:8000" -u "http://localhost:5173")
  else
    echo "::error::--profile full requires an explicit target URL." >&2
    exit 1
  fi
fi

case "$profile" in
  pr)
    tags="exposure,misconfig,default-login,token-spray,kamerplanter"
    severity="medium,high,critical"
    rate=50
    timeout=10
    ;;
  full)
    tags="exposure,misconfig,default-login,cve,vulnerability,kamerplanter"
    severity="low,medium,high,critical"
    rate=100
    timeout=15
    ;;
  *)
    echo "::error::Unknown profile $profile (expected pr or full)." >&2
    exit 1
    ;;
esac

# Build suppression flags from the versioned suppressions file.
suppression_flags=()
if [[ -f "$SUPPRESSIONS" ]]; then
  while IFS= read -r flag; do
    [[ -n "$flag" ]] && suppression_flags+=("$flag")
  done < <("$REPO_ROOT/scripts/security/build-nuclei-flags.sh")
fi

# Combine project + community templates if both exist.
template_args=(-t "$PROJECT_TEMPLATES")
if [[ -d "$COMMUNITY_TEMPLATES" ]]; then
  template_args+=(-t "$COMMUNITY_TEMPLATES")
fi

mkdir -p "$REPO_ROOT/test-reports/security"
out_jsonl="$REPO_ROOT/test-reports/security/nuclei-${profile}-$(date -u +%Y%m%dT%H%M%SZ).jsonl"
out_sarif="${out_jsonl%.jsonl}.sarif"

set -x
nuclei \
  "${template_args[@]}" \
  "${target_args[@]}" \
  -tags "$tags" \
  -severity "$severity" \
  -rate-limit "$rate" \
  -timeout "$timeout" \
  -j -o "$out_jsonl" \
  -sarif-export "$out_sarif" \
  "${suppression_flags[@]}" \
  "$@"
set +x

echo "::notice::Results: $out_jsonl"
echo "::notice::SARIF:   $out_sarif"
