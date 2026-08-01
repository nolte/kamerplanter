// Passive scan rule — raises a High alert when a request authenticated for one
// tenant gets a successful answer from another tenant's URL space.
//
// Spec: spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md §3.3, escalated to
// Critical by §5.1. A cross-tenant hit is a REQ-024 break: one tenant reading
// another's data.
//
// Passive rather than active on purpose. Every request the authenticated scan
// makes passes through here, so the check rides along on the spider, the
// AjaxSpider and the active scanner without generating traffic of its own —
// and it therefore also catches a leak on a route nobody thought to probe.

var PluginPassiveScanner = Java.type('org.zaproxy.zap.extension.pscan.PluginPassiveScanner');
var Base64 = Java.type('java.util.Base64');

// Tenant-scoped routes are `/api/v1/t/{tenant_slug}/...` (REQ-024).
var URL_TENANT_RE = /\/api\/v1\/t\/([a-z0-9-]+)(\/|$)/;

function decodeTenantFromJwt(authHeader) {
  if (authHeader === null || authHeader.indexOf('Bearer ') !== 0) {
    return null;
  }
  var parts = authHeader.substring(7).split('.');
  if (parts.length < 2) {
    return null;
  }
  try {
    var payload = new java.lang.String(Base64.getUrlDecoder().decode(parts[1]), 'UTF-8');
    var match = /"tenant_slug"\s*:\s*"([^"]+)"/.exec(payload);
    return match === null ? null : match[1];
  } catch (e) {
    // A token we cannot decode is not evidence of a leak. Staying quiet here is
    // the one safe direction: the alternative would be an alert on every
    // malformed header.
    return null;
  }
}

function scan(helper, msg, src) {
  var status = msg.getResponseHeader().getStatusCode();
  if (status !== 200 && status !== 201) {
    return;
  }

  var url = msg.getRequestHeader().getURI().toString();
  var urlMatch = URL_TENANT_RE.exec(url);
  if (urlMatch === null) {
    return;
  }
  var urlTenant = urlMatch[1];

  var jwtTenant = decodeTenantFromJwt(msg.getRequestHeader().getHeader('Authorization'));
  if (jwtTenant === null || jwtTenant === urlTenant) {
    return;
  }

  helper
    .newAlert()
    .setRisk(3) // High; §5.1 escalates a cross-tenant hit to Critical.
    .setConfidence(3)
    .setName('Cross-tenant access: token for one tenant answered by another')
    .setDescription(
      'A request carrying a JWT for tenant "' +
        jwtTenant +
        '" received ' +
        status +
        ' from a URL scoped to tenant "' +
        urlTenant +
        '". Under REQ-024 the tenant is the isolation container; a successful ' +
        'response here means data crossed that boundary.'
    )
    .setEvidence(url)
    .setSolution(
      'Enforce the tenant scope server-side on this route: resolve the tenant ' +
        'from the URL, compare it against the caller membership, and answer 403 ' +
        'on mismatch. Do not rely on the client sending the right slug.'
    )
    .setCweId(639) // Authorization Bypass Through User-Controlled Key
    .setWascId(2)
    .setMessage(msg)
    .raise();
}

function appliesToHistoryType(historyType) {
  // Include ZAP's own spider/scanner traffic, not just proxied browsing — the
  // authenticated scan generates almost all of its requests that way.
  return PluginPassiveScanner.getDefaultHistoryTypes().contains(historyType);
}
