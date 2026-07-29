#!/usr/bin/env bash
# Seed ZAP DAST cross-tenant test identities against a running staging
# or CI Kamerplanter backend. Idempotent — safe to re-run.
#
# Spec: spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md §3.1 / §3.3
#
# This script is *external* tooling. It speaks to the backend exclusively
# through the public REST API (/auth/register, /tenants/, /tenants/{slug}/
# invitations/email, /tenants/invitations/accept). It does not import any
# backend Python module and does not need access to the database. Therefore
# it must NOT be deployed inside the production backend image.
#
# Required environment variables:
#   KP_API_BASE                       e.g. https://staging.kamerplanter.example
#   KP_ZAP_PWD_TENANT_A_ADMIN         password for zap-tenant-a-admin
#   KP_ZAP_PWD_TENANT_A_VIEWER        password for zap-tenant-a-viewer
#   KP_ZAP_PWD_TENANT_B_ADMIN         password for zap-tenant-b-admin
#
# Optional:
#   KP_ZAP_DATA   path to test-identities.yaml (default: alongside this script)
#
# Usage:
#   ./seed-test-identities.sh
#
# Exit codes:
#   0  — every identity in test-identities.yaml is present and consistent
#   1  — required env var missing, network failure, or backend rejected a request
#   2  — placeholder password detected; refusing to register

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
DATA_FILE="${KP_ZAP_DATA:-$SCRIPT_DIR/test-identities.yaml}"
PLACEHOLDER="from-env-required"

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "::error::Required environment variable $name is not set." >&2
    exit 1
  fi
  if [[ "${!name}" == "$PLACEHOLDER" ]]; then
    echo "::error::Environment variable $name still contains the placeholder $PLACEHOLDER." >&2
    exit 2
  fi
}

require_env KP_API_BASE
require_env KP_ZAP_PWD_TENANT_A_ADMIN
require_env KP_ZAP_PWD_TENANT_A_VIEWER
require_env KP_ZAP_PWD_TENANT_B_ADMIN

if ! command -v jq >/dev/null 2>&1; then
  echo "::error::jq is required (apt-get install jq)." >&2
  exit 1
fi
if ! command -v yq >/dev/null 2>&1; then
  echo "::error::yq (mikefarah/yq) is required." >&2
  exit 1
fi

if [[ ! -f "$DATA_FILE" ]]; then
  echo "::error::Data file $DATA_FILE not found." >&2
  exit 1
fi

api() {
  local method="$1"
  local path="$2"
  local token="${3:-}"
  local body="${4:-}"
  local auth_header=()
  if [[ -n "$token" ]]; then
    auth_header=(-H "Authorization: Bearer $token")
  fi
  if [[ -n "$body" ]]; then
    curl -sS -X "$method" \
      -H "Content-Type: application/json" \
      "${auth_header[@]}" \
      -d "$body" \
      "$KP_API_BASE$path"
  else
    curl -sS -X "$method" "${auth_header[@]}" "$KP_API_BASE$path"
  fi
}

password_for() {
  local email="$1"
  case "$email" in
    zap-tenant-a-admin@zap.kamerplanter.example)  echo "$KP_ZAP_PWD_TENANT_A_ADMIN" ;;
    zap-tenant-a-viewer@zap.kamerplanter.example) echo "$KP_ZAP_PWD_TENANT_A_VIEWER" ;;
    zap-tenant-b-admin@zap.kamerplanter.example)  echo "$KP_ZAP_PWD_TENANT_B_ADMIN" ;;
    *)
      echo "::error::No password mapping for $email." >&2
      exit 1
      ;;
  esac
}

register_user() {
  local email="$1"
  local display_name="$2"
  local password
  password="$(password_for "$email")"

  local body
  body=$(jq -n --arg e "$email" --arg p "$password" --arg d "$display_name" \
    '{email:$e, password:$p, display_name:$d}')

  local resp
  resp=$(api POST "/api/v1/auth/register" "" "$body" || true)
  local status
  status=$(echo "$resp" | jq -r 'if has("detail") then .detail else "ok" end')
  if [[ "$status" == "ok" ]]; then
    echo "  registered: $email"
  else
    # Common idempotency: backend reports email already in use.
    echo "  exists or rejected: $email — $status"
  fi
}

login() {
  local email="$1"
  local password
  password="$(password_for "$email")"

  local body
  body=$(jq -n --arg e "$email" --arg p "$password" '{email:$e, password:$p}')

  local resp
  resp=$(api POST "/api/v1/auth/login" "" "$body")
  echo "$resp" | jq -er '.access_token' >/dev/null || {
    echo "::error::Login failed for $email — response: $resp" >&2
    exit 1
  }
  echo "$resp" | jq -r '.access_token'
}

ensure_tenant() {
  local owner_email="$1"
  local slug="$2"
  local name="$3"

  local owner_token
  owner_token="$(login "$owner_email")"

  # Look up existing tenants for the user.
  local existing
  existing=$(api GET "/api/v1/tenants" "$owner_token")
  if echo "$existing" | jq -e --arg s "$slug" '.[] | select(.slug == $s)' >/dev/null; then
    echo "  tenant exists: $slug"
    echo "$owner_token"
    return 0
  fi

  local body
  body=$(jq -n --arg n "$name" --arg s "$slug" \
    '{name:$n, slug:$s, tenant_type:"organization"}')

  local resp
  resp=$(api POST "/api/v1/tenants" "$owner_token" "$body")
  echo "$resp" | jq -er '.slug' >/dev/null || {
    echo "::error::Tenant creation failed for $slug — response: $resp" >&2
    exit 1
  }
  echo "  tenant created: $slug"
  echo "$owner_token"
}

ensure_membership() {
  local admin_token="$1"
  local slug="$2"
  local invitee_email="$3"
  local role="$4"

  local members
  members=$(api GET "/api/v1/tenants/$slug/members" "$admin_token")
  if echo "$members" | jq -e --arg e "$invitee_email" \
       '.[] | select(.email == $e)' >/dev/null; then
    echo "  membership exists: $invitee_email -> $slug"
    return 0
  fi

  local invite_body
  invite_body=$(jq -n --arg e "$invitee_email" --arg r "$role" \
    '{email:$e, role:$r}')
  local invite
  invite=$(api POST "/api/v1/tenants/$slug/invitations/email" \
            "$admin_token" "$invite_body")
  local token
  token=$(echo "$invite" | jq -er '.token') || {
    echo "::error::Invitation failed: $invite" >&2
    exit 1
  }

  local invitee_token
  invitee_token="$(login "$invitee_email")"

  local accept_body
  accept_body=$(jq -n --arg t "$token" '{token:$t}')
  api POST "/api/v1/tenants/invitations/accept" "$invitee_token" "$accept_body" \
    >/dev/null
  echo "  membership created: $invitee_email -> $slug ($role)"
}

main() {
  echo "ZAP test identity seed — target $KP_API_BASE"

  # ── Pass 1: register every user ────────────────────────────────
  echo "registering users…"
  while IFS=$'\t' read -r email display_name; do
    register_user "$email" "$display_name"
  done < <(yq e -o=tsv \
    '.users[] | [.email, .display_name]' "$DATA_FILE")

  # ── Pass 2: ensure tenants (each owner becomes admin) ──────────
  echo "ensuring tenants…"
  declare -A owner_tokens
  while IFS=$'\t' read -r slug name owner_email; do
    token=$(ensure_tenant "$owner_email" "$slug" "$name" | tail -n1)
    owner_tokens[$slug]="$token"
  done < <(yq e -o=tsv \
    '.tenants[] | [.slug, .name, .owner_email]' "$DATA_FILE")

  # ── Pass 3: invite remaining members ───────────────────────────
  echo "ensuring memberships…"
  while IFS=$'\t' read -r email tenant_slug role; do
    if [[ "$email" == "$(yq e ".tenants[] | select(.slug == \"$tenant_slug\") | .owner_email" "$DATA_FILE")" ]]; then
      continue   # owner already has admin role from tenant creation
    fi
    ensure_membership "${owner_tokens[$tenant_slug]}" "$tenant_slug" "$email" "$role"
  done < <(yq e -o=tsv \
    '.users[] as $u | $u.memberships[] | [$u.email, .tenant_slug, .role]' \
    "$DATA_FILE")

  echo "done."
}

main "$@"
