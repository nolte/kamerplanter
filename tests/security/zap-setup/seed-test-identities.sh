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
#   KP_API_BASE                       e.g. http://127.0.0.1:8000
#   KP_ZAP_PWD_TENANT_A_ADMIN         password for zap-tenant-a-admin
#   KP_ZAP_PWD_TENANT_A_VIEWER        password for zap-tenant-a-viewer
#   KP_ZAP_PWD_TENANT_B_ADMIN         password for zap-tenant-b-admin
#
# Where the passwords come from (NFR-015 §3.1, revised 2026-08-01): they are
# GENERATED PER RUN by the calling workflow, not stored as repository secrets.
# The identities live only as long as the ephemeral stack does, so a long-lived
# secret for a throw-away account would be attack surface without benefit. This
# script's interface is unchanged — it still reads the same three variables;
# only their provenance differs. A scan against a PERSISTENT environment would
# need reproducible passwords again, because there the accounts outlive the run.
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

# Returns the response body on 2xx and FAILS on anything else.
#
# The previous version used `curl -sS` with no status check at all, so an error
# response came back as an ordinary string and every call site had to notice on
# its own. Several did not: `ensure_membership` fed a 404 error OBJECT into
# `.[] | select(.email == …)`, which is where
# `jq: Cannot index string with string ("email")` came from — jq iterated the
# error object's values and tried to index a string. The confusing jq message
# was a symptom; the missing status check was the defect.
#
# `api_allow` lets a caller name status codes that are a legitimate answer
# rather than a failure (registration returning 4xx for an existing account).
api() {
  local method="$1"
  local path="$2"
  local token="${3:-}"
  local body="${4:-}"
  local auth_header=()
  if [[ -n "$token" ]]; then
    auth_header=(-H "Authorization: Bearer $token")
  fi

  local raw
  if [[ -n "$body" ]]; then
    raw=$(curl -sS -w $'\n%{http_code}' -X "$method" \
      -H "Content-Type: application/json" \
      "${auth_header[@]}" \
      -d "$body" \
      "$KP_API_BASE$path")
  else
    raw=$(curl -sS -w $'\n%{http_code}' -X "$method" "${auth_header[@]}" "$KP_API_BASE$path")
  fi

  local status="${raw##*$'\n'}"
  local payload="${raw%$'\n'*}"

  if [[ "$status" =~ ^2 ]] || [[ " ${api_allow:-} " == *" $status "* ]]; then
    printf '%s' "$payload"
    return 0
  fi

  echo "::error::$method $path -> HTTP $status" >&2
  echo "         $payload" >&2
  return 1
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

  # 400/409 mean the account already exists, which is the idempotent case this
  # script promises. Named explicitly so any OTHER status still fails.
  local resp
  resp=$(api_allow="400 409" api POST "/api/v1/auth/register" "" "$body")
  if echo "$resp" | jq -e 'has("detail") or has("error_code")' >/dev/null 2>&1; then
    echo "  exists already: $email"
  else
    echo "  registered: $email"
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

# Creates (or finds) the organization tenant for an owner and reports the slug
# the SERVER assigned, which is not the one this file asks for.
#
# `POST /api/v1/tenants` accepts only `name`, `description` and `max_members`
# (see TenantCreateRequest); the slug is derived server-side by
# TenantEngine.generate_slug and then de-duplicated. The old version sent a
# `slug` field, which was ignored, and then addressed the tenant by the slug it
# had ASKED for. "ZAP Tenant Alpha" becomes `zap-tenant-alpha`, not
# `zap-tenant-a`, so every later call hit a tenant that did not exist — while
# creation itself reported success (issue #895).
#
# Results come back through globals rather than stdout. The call site used to be
# `token=$(ensure_tenant … | tail -n1)`, and an `exit 1` inside a command
# substitution exits only the SUBSHELL: a failed creation could not abort the
# script, `tail` exited 0, and the token silently became the error text.
ensure_tenant() {
  local owner_email="$1"
  local wanted_slug="$2"
  local name="$3"

  ENSURE_TENANT_TOKEN=""
  ENSURE_TENANT_SLUG=""

  local owner_token
  owner_token="$(login "$owner_email")"

  # Match on the NAME, the only field this script controls. Matching on the slug
  # would never find a tenant created by an earlier run under a derived slug,
  # and the script would try to create a second one every time.
  local existing actual
  existing=$(api GET "/api/v1/tenants" "$owner_token")
  actual=$(echo "$existing" | jq -r --arg n "$name" \
    'map(select(.name == $n and .tenant_type == "organization")) | .[0].slug // empty')

  if [[ -n "$actual" ]]; then
    echo "  tenant exists: $name -> $actual"
  else
    local body resp
    body=$(jq -n --arg n "$name" '{name:$n}')
    resp=$(api POST "/api/v1/tenants" "$owner_token" "$body")
    actual=$(echo "$resp" | jq -r '.slug // empty')
    if [[ -z "$actual" ]]; then
      echo "::error::Tenant creation for '$name' returned no slug — response: $resp" >&2
      return 1
    fi
    echo "  tenant created: $name -> $actual"
  fi

  if [[ "$actual" != "$wanted_slug" ]]; then
    # Not fatal — the derived slug is authoritative and everything downstream
    # uses it. Surfaced so the divergence is visible rather than mysterious the
    # next time someone greps the logs for the name in test-identities.yaml.
    echo "  note: server-derived slug '$actual' differs from the '$wanted_slug' in test-identities.yaml"
  fi

  ENSURE_TENANT_TOKEN="$owner_token"
  ENSURE_TENANT_SLUG="$actual"
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
  # `logical slug from the data file` -> `slug the server actually assigned`.
  # Everything downstream addresses the API with the resolved value; the data
  # file's slug survives only as the key that joins tenants to memberships.
  declare -A owner_tokens
  declare -A resolved_slugs
  while IFS=$'\t' read -r slug name owner_email; do
    ensure_tenant "$owner_email" "$slug" "$name"
    owner_tokens[$slug]="$ENSURE_TENANT_TOKEN"
    resolved_slugs[$slug]="$ENSURE_TENANT_SLUG"
  done < <(yq e -o=tsv \
    '.tenants[] | [.slug, .name, .owner_email]' "$DATA_FILE")

  if [[ ${#resolved_slugs[@]} -eq 0 ]]; then
    echo "::error::No tenants resolved from $DATA_FILE — refusing to continue." >&2
    exit 1
  fi

  # ── Pass 3: invite remaining members ───────────────────────────
  echo "ensuring memberships…"
  while IFS=$'\t' read -r email tenant_slug role; do
    if [[ "$email" == "$(yq e ".tenants[] | select(.slug == \"$tenant_slug\") | .owner_email" "$DATA_FILE")" ]]; then
      continue   # owner already has admin role from tenant creation
    fi
    ensure_membership "${owner_tokens[$tenant_slug]}" "${resolved_slugs[$tenant_slug]}" "$email" "$role"
  done < <(yq e -o=tsv \
    '.users[] as $u | $u.memberships[] | [$u.email, .tenant_slug, .role]' \
    "$DATA_FILE")

  # The resolved slugs are the one thing a caller cannot derive on its own, so
  # they are published rather than re-guessed downstream.
  echo "resolved tenant slugs:"
  for logical in "${!resolved_slugs[@]}"; do
    echo "  $logical -> ${resolved_slugs[$logical]}"
    if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
      echo "slug_${logical//-/_}=${resolved_slugs[$logical]}" >> "$GITHUB_OUTPUT"
    fi
  done

  echo "done."
}

main "$@"
