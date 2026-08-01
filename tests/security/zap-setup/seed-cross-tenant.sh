#!/usr/bin/env bash
# Create a resource inside tenant A so the cross-tenant passive rule has
# something concrete to probe for from tenant B's session.
#
# Spec: spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md §3.3
#
# Runs after seed-test-identities.sh. Like that script it speaks only to the
# public REST API and must never be deployed inside the production image.
#
# Required environment:
#   KP_API_BASE                  base URL of the running backend
#   KP_ZAP_PWD_TENANT_A_ADMIN    per-run password for the tenant-A admin
#   KP_ZAP_PWD_TENANT_B_ADMIN    per-run password for the tenant-B admin
#
# Writes to $GITHUB_OUTPUT when present:
#   tenant_a_token, tenant_b_token, resource_a_key
#
# Why the tokens are outputs: the nightly scan needs tenant B's token to drive
# an authenticated session, and tenant A's resource key to know which URL a
# leak would expose. Both are per-run values that die with the runner.

set -euo pipefail

: "${KP_API_BASE:?KP_API_BASE is required}"
: "${KP_ZAP_PWD_TENANT_A_ADMIN:?KP_ZAP_PWD_TENANT_A_ADMIN is required}"
: "${KP_ZAP_PWD_TENANT_B_ADMIN:?KP_ZAP_PWD_TENANT_B_ADMIN is required}"

login() {
  local email="$1" password="$2" token
  token="$(curl -fsS -X POST "$KP_API_BASE/api/v1/auth/login" \
    -H 'Content-Type: application/json' \
    -d "$(jq -nc --arg e "$email" --arg p "$password" '{email:$e,password:$p}')" \
    | jq -r '.access_token // empty')"
  if [[ -z "$token" ]]; then
    echo "::error::Login failed for $email — the scan cannot run authenticated." >&2
    exit 1
  fi
  printf '%s' "$token"
}

TENANT_A_TOKEN="$(login zap-tenant-a-admin@zap.kamerplanter.example "$KP_ZAP_PWD_TENANT_A_ADMIN")"
TENANT_B_TOKEN="$(login zap-tenant-b-admin@zap.kamerplanter.example "$KP_ZAP_PWD_TENANT_B_ADMIN")"

# A location is the smallest tenant-scoped resource with a stable create route.
RESOURCE_A_KEY="$(curl -fsS -X POST \
  "$KP_API_BASE/api/v1/t/zap-tenant-a/locations" \
  -H "Authorization: Bearer $TENANT_A_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"ZAP-A-CrossTenant-Probe","location_type":"indoor"}' \
  | jq -r '._key // .key // empty')"

if [[ -z "$RESOURCE_A_KEY" ]]; then
  echo "::error::Could not create the tenant-A probe resource. Without it the" >&2
  echo "         cross-tenant check has no target and would report clean while" >&2
  echo "         testing nothing." >&2
  exit 1
fi

echo "Seeded tenant-A probe resource: $RESOURCE_A_KEY"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "tenant_a_token=$TENANT_A_TOKEN"
    echo "tenant_b_token=$TENANT_B_TOKEN"
    echo "resource_a_key=$RESOURCE_A_KEY"
  } >> "$GITHUB_OUTPUT"
fi
