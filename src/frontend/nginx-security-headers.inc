# Security headers shared across all location blocks.
# Spec: spec/nfr/NFR-014_Nuclei-Security-Scanning.md §3.2
#
# nginx scopes `add_header` per location: a location that defines its own
# add_header (e.g. for Cache-Control) drops every server-level header.
# Including this snippet from each location restores the full set.

add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self' data:; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
