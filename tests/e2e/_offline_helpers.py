"""Offline probes for the REQ-053 wave 9 E2E (WP 9.15, issue #2755; UI-NFR-012 §5.1.5, §5.3.4).

What the offline cases need besides page objects: switching the page's network off and on through the Chrome
DevTools Protocol, and reading what the browser stores - IndexedDB databases and records, Cache Storage, the
service worker registration, the web app manifest. Every helper here reads or switches **browser state**, never a
page element (those live in ``pages/offline_page.py``).

LOUD BY CONSTRUCTION (`test-falsifiability` T1, T3, T4)
------------------------------------------------------
* :func:`cdp` raises when the browser refuses a command - an offline test whose "offline" switch silently did
  nothing would pass by never leaving the network.
* :func:`set_network_offline` reads its effect back (``navigator.onLine`` flips) and raises when it does not.
* The readers distinguish "not there" from "there and empty": :func:`indexeddb_record_keys` answers ``None`` for a
  database that does not exist (it never opens one - ``indexedDB.open`` would create it) and a list otherwise;
  :func:`cache_names` raises in an insecure context instead of answering ``[]``.

WHY CDP, AND ITS LIMIT
----------------------
``Network.emulateNetworkConditions`` with ``offline: true`` takes the **page target** offline: its requests fail
with ``ERR_INTERNET_DISCONNECTED`` and ``navigator.onLine`` reads ``false`` (the `online`/`offline` events fire).
It does not reach the service worker's own target, so a request the worker forwards to the network can still get
through. The cases therefore never prove "offline" by a request that failed alone: the plan read asserts the
cached-data banner (shown only for an answer read from IndexedDB, ``cachedAt``), the app shell asserts that the
navigation was answered by the worker (``workerStart > 0``) while the page reported ``navigator.onLine === false``.

Selenium's ``Remote`` driver has no ``execute_cdp_cmd``; chromedriver (behind the Grid too) serves the command at
``/session/<id>/goog/cdp/execute``, registered here as ``_inp_probe.py`` does.
"""

from __future__ import annotations

import json

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

#: How long a switch of the network state may take to reach ``navigator.onLine`` (an event, not a request).
NETWORK_SWITCH_S = 10
#: How long the service worker may take to install and activate (it precaches the app shell first).
WORKER_ACTIVE_S = 60

PLAN_CACHE_DB = "kp-plan-cache"
WRITE_QUEUE_DB = "kp-write-queue"
#: Cache Storage names the app keeps on logout by design (``pwa/cachePolicy.ts`` ``isPublicCacheName``): the
#: precached app shell, the static assets and the runtime config hold no account data.
PUBLIC_CACHE_PREFIXES = ("workbox-precache", "kp-static-assets", "kp-runtime-config")
#: The per-user API cache of the worker: ``kp:{user_key}:{tenant_key}`` (``cachePolicy.ts`` ``API_CACHE_PREFIX``).
USER_CACHE_PREFIX = "kp:"
#: Where the worker persists which tab uses which namespace (``sw.ts`` ``STATE_CACHE`` / ``STATE_URL``).
WORKER_STATE_CACHE = "kp-sw-state"
WORKER_STATE_URL = "/__kp-sw-state/namespaces"


class OfflineProbeError(AssertionError):
    """The browser would not do or tell what an offline probe asked for."""


def _register_cdp(driver: WebDriver) -> None:
    commands = getattr(driver.command_executor, "_commands", None)
    if commands is not None and "executeCdpCommand" not in commands:
        commands["executeCdpCommand"] = ("POST", "/session/$sessionId/goog/cdp/execute")


def cdp(driver: WebDriver, command: str, params: dict | None = None) -> dict:
    """Run one CDP *command* on the page target; its result. Raises when the browser takes no CDP."""
    params = params or {}
    native = getattr(driver, "execute_cdp_cmd", None)
    if callable(native):
        return native(command, params) or {}
    _register_cdp(driver)
    try:
        answer = driver.execute("executeCdpCommand", {"cmd": command, "params": params})
    except Exception as exc:  # the one named gap: re-raised with what was asked
        raise OfflineProbeError(
            f"the browser refused the CDP command {command!r}: {exc}. The offline cases need Chrome "
            "(local or behind the Grid); Firefox has no CDP network emulation."
        ) from exc
    return (answer or {}).get("value") or {}


def navigator_online(driver: WebDriver) -> bool:
    return bool(driver.execute_script("return navigator.onLine;"))


def set_network_offline(driver: WebDriver, offline: bool) -> None:
    """Take the page offline (or back online); return once ``navigator.onLine`` reads the new state."""
    cdp(driver, "Network.enable")
    cdp(
        driver,
        "Network.emulateNetworkConditions",
        {"offline": offline, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1},
    )
    try:
        WebDriverWait(driver, NETWORK_SWITCH_S, poll_frequency=0.2).until(
            lambda d: navigator_online(d) is (not offline)
        )
    except TimeoutException as exc:
        raise OfflineProbeError(
            f"after the CDP switch to {'offline' if offline else 'online'} the page still reports "
            f"navigator.onLine={navigator_online(driver)}"
        ) from exc


def browser_now_ms(driver: WebDriver) -> int:
    """``Date.now()`` of the page - the clock the capture time of a buffered entry is taken from."""
    return int(driver.execute_script("return Date.now();"))


# ── IndexedDB ───────────────────────────────────────────────────────────────

_DATABASE_NAMES = """
var done = arguments[arguments.length - 1];
if (typeof indexedDB === 'undefined' || typeof indexedDB.databases !== 'function') {
  done({error: 'indexedDB.databases() is not available'});
  return;
}
indexedDB.databases().then(function (list) {
  done({names: list.map(function (d) { return d.name; })});
}, function (e) { done({error: String(e)}); });
"""

#: The app databases whose requests :func:`install_indexeddb_trace` records (``pwa/storageWipe.ts``).
TRACED_DATABASES = (PLAN_CACHE_DB, WRITE_QUEUE_DB)
#: How many trace entries a page keeps (the oldest go first) and how many a failure message quotes.
TRACE_LIMIT = 200
TRACE_QUOTED = 80

#: Diagnostic for #3082 (an open of ``kp-plan-cache`` stays queued behind a request another connection blocks):
#: records every ``indexedDB.open`` / ``indexedDB.deleteDatabase`` of the traced databases with the version asked
#: for, the time, the first stack frames and what happened to it - ``upgradeneeded``, ``blocked``, ``success``,
#: ``error`` on the request, ``versionchange``, ``close()`` and a forced ``close`` on the connection it opened.
#: PASS-THROUGH: the original methods run with the original arguments, the app's own handlers still run (listeners
#: only record and never throw), and the trace opens no connection of its own. The probe below uses the saved
#: original ``open``, so its own polling never floods the window.
#: The trace spans the tab's documents (``sessionStorage``): each entry names its document (``d<n>``), each document
#: starts with its path, and ``pagehide``/``pageshow`` say whether it entered or left the back/forward cache,
#: where it would keep its connections open (#3082: the failing document's own opens never completed).
_IDB_TRACE = r"""
(function () {
  if (window.__kpIdbTrace || typeof IDBFactory === 'undefined') return;
  var NAMES = %(names)s, LIMIT = %(limit)d, KEY = '__kpIdbTrace', entries = [], seq = 0, doc = 1;
  // The tab's earlier documents (#3082: the request ahead of a pending open was issued before the failing
  // document existed). sessionStorage outlives a navigation within the tab; a refused storage only loses history.
  try {
    var kept = JSON.parse(window.sessionStorage.getItem(KEY) || 'null');
    if (kept && Array.isArray(kept.entries)) { entries = kept.entries; seq = kept.seq || 0; doc = (kept.doc || 0) + 1; }
  } catch (ignored) { /* no history */ }
  var proto = IDBFactory.prototype, originalOpen = proto.open, originalDelete = proto.deleteDatabase;
  window.__kpIdbTrace = {entries: entries, open: originalOpen, deleteDatabase: originalDelete};
  function now() { return Math.round(performance.now()); }
  function save() {
    try { window.sessionStorage.setItem(KEY, JSON.stringify({entries: entries, seq: seq, doc: doc})); }
    catch (ignored) { /* the in-memory trace still answers */ }
  }
  function add(entry) {
    entry.doc = doc;
    entries.push(entry);
    if (entries.length > LIMIT) entries.shift();
    save();
  }
  function event(id, name, what) { add({id: id, db: name, ev: what, t: now()}); }
  add({id: 0, db: '-', ev: 'document ' + String(location.pathname).slice(0, 80), t: now()});
  // Whether a document went into the back/forward cache (and kept its connections) or came back from it.
  ['pagehide', 'pageshow'].forEach(function (type) {
    window.addEventListener(type, function (e) { event(0, '-', type + (e.persisted ? ' persisted' : '')); });
  });
  ['freeze', 'resume'].forEach(function (type) {
    document.addEventListener(type, function () { event(0, '-', type); });
  });
  function frames() {
    var lines = String(new Error().stack || '').split('\n').slice(4, 9);
    return lines.map(function (line) { return line.trim().replace(/^at /, ''); }).join(' < ');
  }
  function traceConnection(id, name, db) {
    if (!db || db.__kpIdbTraced) return;
    db.__kpIdbTraced = true;
    db.addEventListener('versionchange', function (e) {
      event(id, name, 'versionchange ' + e.oldVersion + '->' + e.newVersion);
    });
    db.addEventListener('close', function () { event(id, name, 'forced close'); });
    var close = db.close;
    db.close = function () { event(id, name, 'close()'); return close.apply(this, arguments); };
  }
  function watch(id, name, request, opens) {
    ['upgradeneeded', 'blocked', 'success', 'error'].forEach(function (type) {
      request.addEventListener(type, function (e) {
        try {
          var detail = type === 'upgradeneeded' || type === 'blocked' ? ' ' + e.oldVersion + '->' + e.newVersion : '';
          if (type === 'error') detail = ' ' + (request.error && request.error.name);
          event(id, name, type + detail);
          if (opens && (type === 'upgradeneeded' || type === 'success')) traceConnection(id, name, request.result);
        } catch (ignored) { /* a trace never breaks the app */ }
      });
    });
  }
  function begin(op, name, version) {
    var id = ++seq;
    add({id: id, db: name, op: op, version: version, t: now(), wall: Date.now(), stack: frames()});
    return id;
  }
  proto.open = function (name) {
    var request = originalOpen.apply(this, arguments);
    if (NAMES.indexOf(name) >= 0) {
      try { watch(begin('open', name, arguments.length > 1 ? arguments[1] : null), name, request, true); }
      catch (ignored) { /* pass-through */ }
    }
    return request;
  };
  proto.deleteDatabase = function (name) {
    var request = originalDelete.apply(this, arguments);
    if (NAMES.indexOf(name) >= 0) {
      try { watch(begin('delete', name, null), name, request, false); } catch (ignored) { /* pass-through */ }
    }
    return request;
  };
})();
""" % {"names": json.dumps(list(TRACED_DATABASES)), "limit": TRACE_LIMIT}

_TRACE_ENTRIES = """
var done = arguments[arguments.length - 1];
done(window.__kpIdbTrace ? {entries: window.__kpIdbTrace.entries.slice()} : {entries: null});
"""


def install_indexeddb_trace(driver: WebDriver) -> None:
    """Record the app's IndexedDB requests in every document this session loads from now on (#3082 diagnostic).

    Registered with CDP ``Page.addScriptToEvaluateOnNewDocument``, so it runs before the app's own code in each
    later navigation; a document already open is not traced. The ``trace_indexeddb`` marker registers it before the
    session's first navigation (``conftest.start_browser_session``). Raises when the browser takes no CDP.
    """
    cdp(driver, "Page.addScriptToEvaluateOnNewDocument", {"source": _IDB_TRACE})


def format_indexeddb_trace(entries: list[dict] | None, limit: int = TRACE_QUOTED) -> str:
    """The last *limit* trace entries, one per line; says so when the document was not traced."""
    if entries is None:
        return "IndexedDB trace: none in this document (install_indexeddb_trace was not registered before it loaded)"
    if not entries:
        return "IndexedDB trace: no open or deletion of the traced databases in this tab"
    shown = entries[-limit:]
    lines = [
        f"IndexedDB trace (last {len(shown)} of {len(entries)} entries across the tab's documents; "
        "d = document number, t = ms since that document started):"
    ]
    for entry in shown:
        head = f"  d{entry.get('doc', 1)} #{entry.get('id')} {entry.get('db')} t={entry.get('t')}"
        if "op" in entry:
            version = entry.get("version")
            asked = "no version" if version is None else f"version {version}"
            lines.append(
                f"{head} {entry['op']} ({asked}) from {str(entry.get('stack') or '?')[:240]}"
            )
        else:
            lines.append(f"{head} -> {entry.get('ev')}")
    return "\n".join(lines)


def indexeddb_trace(driver: WebDriver) -> str:
    """The formatted trace of the current document; a diagnostic, so a failure to read it is named, not raised."""
    try:
        answer = driver.execute_async_script(_TRACE_ENTRIES)
    except Exception as exc:  # diagnostic text for a failure message that is already being raised
        return f"IndexedDB trace: could not be read ({exc.__class__.__name__}: {exc})"
    entries = answer.get("entries") if isinstance(answer, dict) else None
    return format_indexeddb_trace(entries)


#: How long the probe's ``indexedDB.open`` may stay pending before it reports that instead of answering. Below the
#: driver's 30 s script timeout on purpose: an open request queued behind a version change or deletion that another
#: connection blocks never completes, and Selenium would only say "script timeout" (TC-053-086/087/088 nightlies).
STORE_OPEN_PENDING_MS = 10_000

#: Opens an existing database read-only and lists the primary keys of one store. Never keeps a database it created:
#: the caller checks the name first, and ``onupgradeneeded`` (which only fires for a new database) aborts the
#: creation. That abort still matters while pending: an open queued behind the app's own ``deleteDatabase`` would
#: create a fresh v1 once the deletion completes, and the abort discards it again. A version-less open is never
#: ``blocked`` itself; it only waits in the queue, which is what the watchdog reports.
#: Every path calls ``done`` exactly once: a request still pending after ``STORE_OPEN_PENDING_MS`` answers
#: ``{pending: ...}`` with the origin's databases and versions, a request that succeeds after that closes its
#: connection at once (left open it would itself block the app's next upgrade or deletion), and an exception in a
#: callback answers ``{error: ...}`` instead of leaving the script to time out.
#: The open goes through the original ``IDBFactory.open`` saved by :data:`_IDB_TRACE` (so the probe is not traced),
#: and a pending answer carries the page's trace, which :func:`indexeddb_record_keys` appends to its error.
_STORE_KEYS = """
var name = arguments[0], store = arguments[1], pendingMs = arguments[2], done = arguments[arguments.length - 1];
var answered = false;
function finish(value) { if (!answered) { answered = true; clearTimeout(watchdog); done(value); } }
var trace = window.__kpIdbTrace;
var request = (trace ? trace.open : IDBFactory.prototype.open).call(indexedDB, name);
var watchdog = setTimeout(function () {
  var state = {pending: true, readyState: request.readyState, waitedMs: pendingMs,
               trace: trace ? trace.entries.slice() : null};
  // databases() can stall like the open itself; answer without the list rather than run into the script timeout.
  setTimeout(function () { finish(state); }, 2000);
  indexedDB.databases().then(function (list) {
    state.databases = list.map(function (d) { return d.name + '@' + d.version; });
    finish(state);
  }, function () { finish(state); });
}, pendingMs);
request.onupgradeneeded = function () { request.transaction.abort(); finish({missing: true}); };
request.onerror = function () { finish({error: String(request.error)}); };
request.onsuccess = function () {
  var db = request.result;
  if (answered) { db.close(); return; }
  try {
    if (!db.objectStoreNames.contains(store)) {
      db.close();
      finish({keys: null, stores: Array.from(db.objectStoreNames)});
      return;
    }
    var keys = db.transaction(store, 'readonly').objectStore(store).getAllKeys();
    keys.onsuccess = function () { db.close(); finish({keys: keys.result.map(String)}); };
    keys.onerror = function () { db.close(); finish({error: String(keys.error)}); };
  } catch (e) {
    db.close();
    finish({error: String(e)});
  }
};
"""


def indexeddb_database_names(driver: WebDriver) -> list[str]:
    """The IndexedDB databases of the page's origin; raises when the browser cannot list them."""
    answer = driver.execute_async_script(_DATABASE_NAMES)
    if not isinstance(answer, dict) or "names" not in answer:
        raise OfflineProbeError(f"the IndexedDB databases could not be listed: {answer!r}")
    return [str(name) for name in answer["names"]]


def indexeddb_record_keys(driver: WebDriver, database: str, store: str) -> list[str] | None:
    """Primary keys of *store* in *database*; ``None`` when the database does not exist (it is not created)."""
    if database not in indexeddb_database_names(driver):
        return None
    answer = driver.execute_async_script(_STORE_KEYS, database, store, STORE_OPEN_PENDING_MS)
    if isinstance(answer, dict) and answer.get("pending"):
        raise OfflineProbeError(
            f"opening {database!r} did not complete within {answer.get('waitedMs')} ms "
            f"(request readyState {answer.get('readyState')!r}; databases {answer.get('databases')}): "
            "the open is queued behind a version change or deletion that another connection blocks\n"
            + format_indexeddb_trace(answer.get("trace"))
        )
    if not isinstance(answer, dict) or "error" in answer:
        raise OfflineProbeError(f"reading {database}/{store} failed: {answer!r}")
    if answer.get("missing"):
        return None
    if answer.get("keys") is None:
        raise OfflineProbeError(
            f"the database {database!r} has no store {store!r}; it has {answer.get('stores')}"
        )
    return list(answer["keys"])


def wait_for_cached_record(
    driver: WebDriver, database: str, store: str, fragment: str, what: str, timeout: int = 15
) -> str:
    """Wait until *store* holds a record whose key contains *fragment*; that key.

    The read-through cache writes in the background after a successful online read; the offline half of a case
    may only start once the record is there - a durable signal, not a pause.
    """
    found: list[str] = []

    def _written(_d) -> bool:
        keys = indexeddb_record_keys(driver, database, store) or []
        found[:] = [key for key in keys if fragment in key]
        return bool(found)

    try:
        WebDriverWait(driver, timeout, poll_frequency=0.5).until(_written)
    except TimeoutException as exc:
        raise AssertionError(
            f"{what}: {database}/{store} holds no record for {fragment!r}; keys: "
            f"{indexeddb_record_keys(driver, database, store)}\n{indexeddb_trace(driver)}"
        ) from exc
    return found[0]


# ── Cache Storage and the service worker ────────────────────────────────────

_CACHE_NAMES = """
var done = arguments[arguments.length - 1];
if (typeof caches === 'undefined') { done({error: 'no Cache Storage (insecure context?)'}); return; }
caches.keys().then(function (names) { done({names: names}); }, function (e) { done({error: String(e)}); });
"""

_WORKER_STATE = """
var done = arguments[arguments.length - 1];
if (!('serviceWorker' in navigator) || !navigator.serviceWorker) {
  done({supported: false, secure: window.isSecureContext});
  return;
}
navigator.serviceWorker.getRegistration('/').then(function (registration) {
  var active = registration && registration.active;
  var controller = navigator.serviceWorker.controller;
  done({
    supported: true,
    secure: window.isSecureContext,
    registered: !!registration,
    scope: registration ? registration.scope : null,
    activeUrl: active ? active.scriptURL : null,
    activeState: active ? active.state : null,
    controllerUrl: controller ? controller.scriptURL : null
  });
}, function (e) { done({error: String(e)}); });
"""

#: What answered the top-level navigation: ``workerStart`` is set only when a service worker took the request.
_NAVIGATION = """
var entry = performance.getEntriesByType('navigation')[0];
return entry ? {name: entry.name, workerStart: entry.workerStart, transferSize: entry.transferSize,
                type: entry.type} : null;
"""

_HEADERS_OF = """
var url = arguments[0], done = arguments[arguments.length - 1];
fetch(url, {cache: 'no-store', credentials: 'same-origin'}).then(function (response) {
  done({status: response.status, cacheControl: response.headers.get('cache-control'),
        contentType: response.headers.get('content-type')});
}, function (e) { done({error: String(e)}); });
"""


def cache_names(driver: WebDriver) -> list[str]:
    """The Cache Storage names of the origin; raises in an insecure context (no ``caches`` at all)."""
    answer = driver.execute_async_script(_CACHE_NAMES)
    if not isinstance(answer, dict) or "names" not in answer:
        raise OfflineProbeError(f"Cache Storage could not be read: {answer!r}")
    return [str(name) for name in answer["names"]]


def user_cache_names(driver: WebDriver) -> list[str]:
    """The worker's per-account API caches (``kp:{user}:{tenant}``) - what a logout must remove."""
    return [name for name in cache_names(driver) if name.startswith(USER_CACHE_PREFIX)]


_WORKER_NAMESPACES = """
var name = arguments[0], url = arguments[1], done = arguments[arguments.length - 1];
if (typeof caches === 'undefined') { done({error: 'no Cache Storage (insecure context?)'}); return; }
caches.has(name).then(function (exists) {
  if (!exists) { done({namespaces: null}); return; }
  return caches.open(name).then(function (cache) { return cache.match(url); }).then(function (stored) {
    if (!stored) { done({namespaces: []}); return; }
    return stored.json().then(function (value) {
      var clients = (value && value.registry && value.registry.clients) || {};
      done({namespaces: Object.keys(clients).map(function (id) { return clients[id]; })});
    });
  });
}).catch(function (e) { done({error: String(e)}); });
"""


def worker_namespaces(driver: WebDriver) -> list[str] | None:
    """The ``kp:{user}:{tenant}`` namespaces the worker holds for its tabs (persisted state); ``None`` without state.

    A tab announces its namespace once the signed-in user and the active tenant are known (``sessionListener``);
    the worker keeps it in ``kp-sw-state`` and drops it when that user's session ends (``KP_CLEAR_DATA``).
    """
    answer = driver.execute_async_script(_WORKER_NAMESPACES, WORKER_STATE_CACHE, WORKER_STATE_URL)
    if not isinstance(answer, dict) or "error" in answer:
        raise OfflineProbeError(f"the worker's namespace state could not be read: {answer!r}")
    names = answer.get("namespaces")
    return None if names is None else [str(name) for name in names]


def worker_state(driver: WebDriver) -> dict:
    answer = driver.execute_async_script(_WORKER_STATE)
    if not isinstance(answer, dict) or "error" in answer:
        raise OfflineProbeError(f"the service worker registration could not be read: {answer!r}")
    if not answer.get("supported"):
        raise OfflineProbeError(
            f"no navigator.serviceWorker on this page (isSecureContext={answer.get('secure')}); a "
            "secure_context test must run with the insecure-origin switch (conftest.secure_context_args)"
        )
    return answer


def wait_for_active_worker(driver: WebDriver, what: str) -> dict:
    """Wait until the registration for ``/`` has an ``activated`` worker; its state."""
    last: list[dict] = [{}]

    def _active(_d) -> bool:
        last[0] = worker_state(driver)
        return last[0].get("activeState") == "activated"

    try:
        WebDriverWait(driver, WORKER_ACTIVE_S, poll_frequency=0.5).until(_active)
    except TimeoutException as exc:
        raise AssertionError(f"{what}: no activated service worker; state {last[0]!r}") from exc
    return last[0]


def navigation_entry(driver: WebDriver) -> dict:
    entry = driver.execute_script(_NAVIGATION)
    if not isinstance(entry, dict):
        raise OfflineProbeError("the page has no navigation timing entry")
    return entry


def response_headers(driver: WebDriver, path: str) -> dict:
    """Status and caching headers of a same-origin ``GET`` *path*, fetched by the page (``cache: no-store``)."""
    answer = driver.execute_async_script(_HEADERS_OF, path)
    if not isinstance(answer, dict) or "error" in answer:
        raise OfflineProbeError(f"GET {path} from the page failed: {answer!r}")
    return answer


def app_manifest(driver: WebDriver) -> dict:
    """CDP ``Page.getAppManifest``: ``url``, ``errors`` and the raw ``data`` the browser parsed."""
    return cdp(driver, "Page.getAppManifest")


__all__ = [
    "PLAN_CACHE_DB",
    "PUBLIC_CACHE_PREFIXES",
    "USER_CACHE_PREFIX",
    "WRITE_QUEUE_DB",
    "OfflineProbeError",
    "app_manifest",
    "browser_now_ms",
    "cache_names",
    "cdp",
    "indexeddb_database_names",
    "format_indexeddb_trace",
    "indexeddb_record_keys",
    "indexeddb_trace",
    "install_indexeddb_trace",
    "navigation_entry",
    "navigator_online",
    "response_headers",
    "set_network_offline",
    "user_cache_names",
    "wait_for_active_worker",
    "wait_for_cached_record",
    "worker_namespaces",
    "worker_state",
]
