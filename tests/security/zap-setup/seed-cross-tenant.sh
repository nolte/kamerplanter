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
#   KP_ZAP_TENANT_A_SLUG         slug the server assigned to tenant A
#   KP_ZAP_TENANT_B_SLUG         slug the server assigned to tenant B
#
# The two slug variables are NOT optional and NOT guessable: the API derives the
# slug from the tenant name and this script must address the tenant the server
# actually created, not the one test-identities.yaml asks for (issue #895).
# seed-test-identities.sh publishes both.
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
: "${KP_ZAP_TENANT_A_SLUG:?KP_ZAP_TENANT_A_SLUG is required — see seed-test-identities.sh}"

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

# A site is the smallest tenant-scoped resource that still has a detail route:
# `name` is its only required field, and `/t/{slug}/sites/{key}` is what the
# cross-tenant probe needs to aim at. A location was the first choice and is
# wrong — it requires `site_key` and `area_m2`, so it cannot be created without
# building the very thing this creates.
RESOURCE_A_KEY="$(curl -fsS -X POST \
  "$KP_API_BASE/api/v1/t/$KP_ZAP_TENANT_A_SLUG/sites" \
  -H "Authorization: Bearer $TENANT_A_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"ZAP-A-CrossTenant-Probe"}' \
  | jq -r '.key // ._key // empty')"

if [[ -z "$RESOURCE_A_KEY" ]]; then
  echo "::error::Could not create the tenant-A probe resource. Without it the" >&2
  echo "         cross-tenant check has no target and would report clean while" >&2
  echo "         testing nothing." >&2
  exit 1
fi

echo "Seeded probe resource in $KP_ZAP_TENANT_A_SLUG: $RESOURCE_A_KEY"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "tenant_a_token=$TENANT_A_TOKEN"
    echo "tenant_b_token=$TENANT_B_TOKEN"
    echo "resource_a_key=$RESOURCE_A_KEY"
  } >> "$GITHUB_OUTPUT"
fi
