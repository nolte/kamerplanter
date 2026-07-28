#!/bin/sh
# Allow the error tracker's ingest origin in the CSP — but only when one is
# configured (#777).
#
# The shipped policy is `connect-src 'self'`, which blocks the SDK's event POST.
# Widening it unconditionally would weaken the header for every deployment that
# does not use a tracker, so the default file is left exactly as built and this
# script only appends the one origin the configured DSN actually points at.
#
# The DSN has the form https://<public-key>@<host>/<project-id>; only the scheme
# and host go into the policy. The key never reaches the header.
set -eu

DSN="${SENTRY_DSN:-}"
[ -n "$DSN" ] || exit 0

HEADERS_FILE=/etc/nginx/conf.d/nginx-security-headers.inc

# scheme://[credentials@]host[/...]  ->  scheme://host
SCHEME=$(printf '%s' "$DSN" | sed -n 's|^\([a-zA-Z][a-zA-Z0-9+.-]*\)://.*|\1|p')
HOST=$(printf '%s' "$DSN" | sed -e 's|^[a-zA-Z][a-zA-Z0-9+.-]*://||' -e 's|^[^@/]*@||' -e 's|/.*$||')

if [ -z "$SCHEME" ] || [ -z "$HOST" ]; then
    echo "WARN  SENTRY_DSN is set but not parseable as a URL; CSP left unchanged." >&2
    echo "      Error events will be blocked by connect-src 'self'." >&2
    exit 0
fi

ORIGIN="${SCHEME}://${HOST}"

# Extend connect-src in place. Anchored on the exact shipped token so a policy
# edit that renames or reorders directives makes this a visible no-op rather
# than a silent mismatch.
if ! grep -q "connect-src 'self';" "$HEADERS_FILE"; then
    echo "WARN  connect-src 'self'; not found in $HEADERS_FILE; CSP left unchanged." >&2
    echo "      Error events will be blocked. Re-check the policy after editing it." >&2
    exit 0
fi

sed -i "s|connect-src 'self';|connect-src 'self' ${ORIGIN};|" "$HEADERS_FILE"
echo "INFO  CSP connect-src extended with the error-tracking origin ${ORIGIN}." >&2
