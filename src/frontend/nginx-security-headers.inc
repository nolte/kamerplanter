# Security headers shared across all location blocks.
# Spec: spec/nfr/NFR-014_Nuclei-Security-Scanning.md §3.2, NFR-001 §Security-Headers
#
# nginx scopes `add_header` per location: a location that defines its own
# add_header (e.g. for Cache-Control) drops every server-level header.
# Including this snippet from each location restores the full set.
#
# Every configuration that includes this snippet MUST define the variable
# $kp_csp_connect_extra (the `map` at the top of nginx.conf and of the chart's
# default.conf); nginx refuses to start on an unknown variable.

add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
# img-src includes blob: per NFR-001 §CSP — the photo gallery (REQ-034) and
# image-capture previews render client-side object URLs (URL.createObjectURL);
# without blob: every gallery image and upload preview is CSP-blocked and the
# UI misreports it as an unsupported image format.
#
# worker-src 'self' (REQ-053 WP 9.1, #2741): the service worker /sw.js is the
# only worker. Named explicitly instead of inheriting script-src, so a later
# script-src widening cannot silently admit a foreign or blob: worker.
#
# style-src keeps 'unsafe-inline' on purpose (#3025 W-20, NFR-001 §CSP). Emotion
# (MUI's styling engine) creates <style> elements at runtime for every styled
# component, and index.html carries the boot splash (#612) as an inline <style>.
# Dropping 'unsafe-inline' needs a per-response nonce that nginx stamps into
# index.html AND hands to Emotion's cache. index.html is precached by the
# service worker, though, so the nonce would be frozen into the cached copy and
# replayed on every visit, which is no nonce at all. A hash for the splash alone
# does not help either: any hash or nonce in style-src makes CSP2+ browsers
# IGNORE 'unsafe-inline', which would drop every Emotion style. script-src has
# no 'unsafe-inline' (SH-002), so injected markup still cannot run script.
#
# connect-src: the variable is empty unless an error tracker is configured;
# then it is " <scheme>://<host>[:port]" of exactly the configured SENTRY_DSN,
# written at container start by docker-entrypoint.d/30-error-tracking-csp.sh
# (#777, #3025 W-21). Never a wildcard.
#
# object-src 'none': the app embeds no <object>/<embed>; default-src 'self'
# alone would still admit same-origin plugin content.
add_header Content-Security-Policy "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; font-src 'self' data:; script-src 'self'; worker-src 'self'; connect-src 'self'${kp_csp_connect_extra}; object-src 'none'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; manifest-src 'self'" always;
# For browsers without frame-ancestors. DENY says what frame-ancestors 'none'
# says (and what NFR-001 §Security-Headers asks for); SAMEORIGIN contradicted it.
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
# X-XSS-Protection is deliberately not sent (#3025 W-22): current browsers
# removed the XSS auditor, and where it survived, `1; mode=block` opened a
# cross-site leak of its own. The CSP's script-src is the XSS defence.
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
# Browser features: camera (REQ-029-A webcam capture, useWebcamCapture) and
# geolocation (site GPS, garden-planner field position) for this origin only;
# the features the app never uses are off for the page and every frame in it.
add_header Permissions-Policy "camera=(self), geolocation=(self), microphone=(), payment=(), usb=(), serial=(), bluetooth=(), hid=(), midi=()" always;
# The app opens no cross-origin window it needs a handle to (OAuth is a full
# redirect, row links open with noopener), so it owns its browsing context
# group; and nothing it serves is meant to be embedded by another origin.
add_header Cross-Origin-Opener-Policy "same-origin" always;
add_header Cross-Origin-Resource-Policy "same-origin" always;
