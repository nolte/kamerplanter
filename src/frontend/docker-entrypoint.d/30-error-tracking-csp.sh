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

# Validate before the value reaches a CSP directive. Whoever sets SENTRY_DSN
# already controls the deployment, so this is not a privilege boundary — but the
# value flows into a security header through a `sed` replacement, and a DSN
# without a path (`https://host; script-src *`) would otherwise carry every
# character after the host straight into the policy. A malformed DSN must
# degrade to "tracking does not reach the server", never to "the page's CSP
# quietly grew a directive".
case "$SCHEME" in
    http | https) ;;
    *)
        echo "WARN  SENTRY_DSN scheme '${SCHEME}' is not http(s); CSP left unchanged." >&2
        echo "      Error events will be blocked by connect-src 'self'." >&2
        exit 0
        ;;
esac

# Host, optionally with a port. Deliberately no `;`, no space, no quote — the
# characters a CSP directive is delimited by.
case "$HOST" in
    "" | *[!A-Za-z0-9.:-]*)
        echo "WARN  SENTRY_DSN host '${HOST}' is not a bare host[:port]; CSP left unchanged." >&2
        echo "      Error events will be blocked by connect-src 'self'." >&2
        exit 0
        ;;
esac

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
