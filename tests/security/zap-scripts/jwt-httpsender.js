// HttpSender script — attaches the Bearer token to every outgoing request and
// re-logs-in when the backend answers 401.
//
// Spec: spec/nfr/NFR-015_OWASP-ZAP-Security-Scanning.md §3.2
//
// Why HttpSender and not a classic Authentication script: an Authentication
// script sets the header on the login reply only. ZAP's spider, AjaxSpider and
// active scanner build their own requests afterwards, and those would go out
// without an Authorization header — the authenticated scan would then quietly
// scan the anonymous surface and report it as authenticated coverage.
//
// The token is read from ZAP's global variables, seeded by the workflow before
// the scan starts (KP_ZAP_TOKEN). Re-login uses KP_ZAP_LOGIN_* so an expiring
// 15-minute access token (REQ-023) does not end the scan half-way.

var ScriptVars = Java.type('org.zaproxy.zap.extension.script.ScriptVars');
var HttpRequestHeader = Java.type('org.parosproxy.paros.network.HttpRequestHeader');
var HttpHeader = Java.type('org.parosproxy.paros.network.HttpHeader');
var URI = Java.type('org.apache.commons.httpclient.URI');

function tokenVar() {
  return ScriptVars.getGlobalVar('KP_ZAP_TOKEN');
}

function sendingRequest(msg, initiator, helper) {
  var token = tokenVar();
  if (token === null || token === '') {
    return;
  }
  msg.getRequestHeader().setHeader('Authorization', 'Bearer ' + token);
}

function responseReceived(msg, initiator, helper) {
  if (msg.getResponseHeader().getStatusCode() !== 401) {
    return;
  }
  // A 401 on a request that carried a token means the token expired. Re-login
  // once and store the new one; the next request picks it up. Deliberately no
  // retry of the current message: ZAP treats the 401 as the response for this
  // request, which is correct — the point is that the SCAN continues
  // authenticated, not that this one request is repaired.
  var base = ScriptVars.getGlobalVar('KP_ZAP_LOGIN_URL');
  var body = ScriptVars.getGlobalVar('KP_ZAP_LOGIN_BODY');
  if (base === null || body === null) {
    return;
  }

  var req = helper.prepareMessage();
  req.setRequestHeader(
    new HttpRequestHeader(HttpRequestHeader.POST, new URI(base, false), HttpHeader.HTTP11)
  );
  req.getRequestHeader().setHeader(HttpHeader.CONTENT_TYPE, 'application/json');
  req.setRequestBody(body);
  req.getRequestHeader().setContentLength(req.getRequestBody().length());

  helper.sendAndReceive(req, false);

  var refreshed = req.getResponseBody().toString();
  var match = /"access_token"\s*:\s*"([^"]+)"/.exec(refreshed);
  if (match !== null) {
    ScriptVars.setGlobalVar('KP_ZAP_TOKEN', match[1]);
    print('[jwt-httpsender] re-authenticated after 401');
  } else {
    // Losing the token silently would turn the rest of an authenticated scan
    // into an anonymous one that still reports as authenticated.
    print('[jwt-httpsender] RE-LOGIN FAILED — remaining requests are anonymous');
  }
}
