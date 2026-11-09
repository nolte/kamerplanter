# SPEC-07 — Offline Privacy Specification

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · measured against develop 24d1c2988
Requirement IDs: PRIV-500 … PRIV-539
Depends on: UI-NFR-012 v2.4 (R-055 … R-060), REQ-025 §10 (TTDSG rows), NFR-011 R-41/R-42,
REQ-053 §32.6 Pkt. 13–16, 03 §7 (deletion while offline)
```

The offline layer of REQ-053 wave 9 is implemented and reviewed (P-7 report GDPR-001…006).
This document consolidates what is stored on devices, fixes the lifecycle rules that are
still placeholders, closes the verified drift between UI-NFR-012 R-056 and the code, and
answers the five device questions of #2517 (2026-11-09) as proposals for legal review.

---

## 1. Data stored on devices (verified, `origin/develop` 24d1c2988)

| Store | Name | Content | Personal data | Namespace | Lifetime |
|-------|------|---------|---------------|-----------|----------|
| IndexedDB (Dexie) | `kp-plan-cache` — stores `plans`, `bedLists`, `siteLists`, `bedSummaries`, `bedSheets` | `{key, userKey, tenantKey, cachedAt, data}`; `storedProjection` nulls `plan_updated_by_name`, `notes`, `description`, task assignee, completion notes, photos, ratings | `user_key`, `tenant_key`, bed/plant names, task names | key `{user}:{tenant}:{site|location}` | 15 min TTL (`PLAN_CACHE_TTL_MS`); purged at app start, every read, every write; **no byte ceiling** |
| IndexedDB (Dexie) | `kp-write-queue` — store `entries`, `notices` | `QueueEntry {seq, id (client_event_id UUIDv4), userKey, tenantKey, capturedAt, status pending/syncing/failed/conflict, attempts, nextAttemptAt, lastErrorCode, conflictCode, kept, expiresAt, bedKey, bedName, write}`; `write` kinds `complete`, `note` (care event text), `bedPhoto`, `plantPhoto` (`StoredPhoto {bytes ArrayBuffer ≤ 1920 px JPEG 0.8, type, name="photo.jpg"}`) | note text, photos, keys | `[userKey+tenantKey]` index, `owned()` filter on every read | 365 d from effective `performed_at` (pending); 90 d from capture (`failed`/`conflict`); 500 entries/user, 5 000/device; **no photo byte ceiling** |
| Cache Storage | `kp:{user_key}:{tenant_key}` | SW API cache for the 3-path allowlist (`/sites`, `/sites/{k}/plan`, `/locations/{k}/summary`) — **always empty**: the backend sends `Cache-Control: no-store` on every `/api/v1` answer (MT-044) | would be plan data | per user+tenant, keys validated `^[A-Za-z0-9_-]{1,128}$` | 15 min, 50 MB, generation counter |
| Cache Storage | `kp-sw-state` | client-id → namespace registry, byte totals | keys | — | session |
| Cache Storage | precache, `kp-static-assets`, `kp-runtime-config` | app shell | none | — | build revision |
| localStorage | `kp_local_data_owner` | **a `user_key`** | yes | — | never cleared |
| localStorage | `kp-garden-field-mode` | `{userKey, tenantSlug, siteKey, tab, viewports}` | yes | — | never cleared (ignored if `userKey` differs) |
| localStorage | `kp_active_tenant_slug` | slug | low | — | cleared on logout |
| localStorage | `kp.gardenPlanner.planting.lastUsed.{tenantSlug}` | species → spacing | slug in key | — | never cleared |
| sessionStorage | `kp.emailChange.address` | **pending e-mail address** | yes | — | removed by its flow only |
| sessionStorage | `kp.stepUp.token/resume/error` | one-time step-up token (5 min TTL) | auth artefact | — | consumed by flow |
| sessionStorage | `kamerplanter.pendingInvitation` | invitation token | auth artefact | — | cleared on logout |
| memory | access token (Redux `auth`) | JWT | yes | — | tab lifetime |
| cookie | refresh (HttpOnly per spec), CSRF | — | yes | — | 30 d |

Not present [v]: `device_id` / token persistence (R-048…R-051 deferred), API data in
localStorage, `redux-persist`, RTK Query.

---

## 2. TDDDG §25 classification (LEG-09)

The German implementation of ePrivacy Art. 5(3) is **TDDDG** (renamed from TTDSG on
14 May 2024); the specs still say "TTDSG" — editorial fix proposed. §25(1) requires consent
for storing or reading information on the end device unless §25(2) Nr. 2 applies: the
storage is **strictly necessary** to provide a telemedia service **expressly requested by
the user**.

| Storage | Proposed classification | Reasoning | Status |
|---------|-------------------------|-----------|--------|
| `kp-plan-cache`, `kp-write-queue`, `kp:*`, `kp-sw-state` | §25(2) Nr. 2 — necessary for the **offline function the user requests** by installing/using the PWA and by acting while offline | the function cannot exist without local storage; data minimised (no names, notes, assignments in the cache); TTL 15 min; the write queue holds only what the user typed | REQ-025 v1.40 §10 says the same, "Vorschlag, Rechtsprüfung offen (#2517)" |
| Precache, static assets, runtime config | §25(2) Nr. 2 (app shell) | no personal data | uncontested |
| `kp_local_data_owner`, `kp-garden-field-mode`, planting `lastUsed`, tenant slug | §25(2) Nr. 2 (session continuity / UX state the user set) | necessary for the chosen workflow; but **hygiene**: keys holding a `user_key` or e-mail must not outlive the session (PRIV-512) | proposal |
| consent flags (`kamerplanter:consent:v1`) | necessary (remembering a consent decision) | — | uncontested |
| Sentry SDK storage | not necessary → consent (`error_tracking`) | REQ-025 TT-002 | implemented in spec |

**PRIV-500** The classification above MUST be the single table in REQ-025 §10 (spec change
proposal: add the localStorage/sessionStorage rows that exist, remove `redux_state`,
`i18next`, `theme`, rename TTDSG → TDDDG). No consent banner is required while the table
holds (TT-003). **[legal LEG-09]**: (a) is "offline use" an expressly requested service when
the PWA caches on first login without an explicit opt-in? Recommendation: add an explicit
**"Offline-Modus aktivieren"** toggle per device (default **off** for new installations,
default on for installations that already cache — operator decides), which also settles the
"expressly requested" criterion; (b) are the retention periods of §6 proportionate.

---

## 3. Storage namespace and isolation

**PRIV-501** [v, keep] Every IndexedDB record and every API cache entry MUST carry
`user_key` **and** `tenant_key`, and every read MUST filter on both (`owned()`); the keys
reach the worker by `postMessage` (`KP_SET_NAMESPACE`), never from a token.

**PRIV-502** [v, keep] No API data in `localStorage`/`sessionStorage` (UI-NFR-012 R-055,
guard `test/guards/…`).

**PRIV-503** [proposal] The namespace MUST also include a **cache generation** derived from
the server (`X-KP-Cache-Generation` header or `runtime-config.js` value) so that a server-side
privacy event (erasure, membership end) can invalidate all device caches of a tenant without
a client version bump: a changed generation makes `isFresh` false. Low cost; replaces
nothing. Priority P2.

---

## 4. Cache lifecycle (read cache)

**PRIV-504** [v, keep] TTL 15 min; expired entries physically deleted at start/read/write
(NFR-011 R-41, P-7 GDPR-005).

**PRIV-505** [proposal] `kp-plan-cache` MUST get a byte ceiling (`PLAN_CACHE_MAX_BYTES`,
default 20 MB) with oldest-first eviction, like the SW cache's 50 MB.

**PRIV-506** [v, keep] The read cache MUST contain no member names, notes, descriptions,
assignments, completion notes, photos or ratings (`storedProjection`); the guard pins the
projection. Bed/plant/task **names** remain (needed for the offline sheet) — they are
content, covered by the review model when they name a person.

---

## 5. Queue lifecycle (write buffer)

**PRIV-507** [v, keep] Allowlist of four write kinds; FIFO; single sender (Web Locks);
backoff 1 → 60 s, 5 attempts; `client_event_id` constant across attempts; server replay
answers 200 with the stored object; 409 `client_event.payload_mismatch` for another body
under the same id; conflicts → `conflict`, refused 4xx → `failed`, 401 → stop.

**PRIV-508** [v, keep] Photos re-encoded on the client (≤ 1920 px, JPEG 0.8, canvas drops
EXIF), generic name `photo.jpg`; server-side EXIF strip remains authoritative.

**PRIV-509** [proposal] The queue MUST get a **photo byte ceiling** per user
(`QUEUE_PHOTO_MAX_BYTES`, default 100 MB; UI-NFR-012 risk table names 200 MB without a
limit [v]); exceeding it refuses the capture with `QueueFullError` semantics.

**PRIV-510** [proposal] Entry states gain `quarantined` (§7); `expiresAt` is recomputed
when the state changes (dead-session grace).

---

## 6. Retention on the device (LEG-10)

Current placeholders [v]: 365 d pending (anchored to the server's V-11 back-dating limit),
90 d `failed`/`conflict`. Both are "Platzhalter-Standard aus #2759; für geteilte Geräte kann
der Betreiber kürzere wählen" (REQ-053 §32.6 Pkt. 14) — but no setting exists [v].

**PRIV-511** The periods MUST become operator-configurable through `runtime-config.js`
(`OFFLINE_QUEUE_PENDING_MAX_DAYS`, `OFFLINE_QUEUE_UNSENDABLE_MAX_DAYS`,
`OFFLINE_DEAD_SESSION_GRACE_DAYS`, `OFFLINE_SHARED_DEVICE_MODE`) with these defaults and
justifications:

| Setting | Default (proposal) | Ceiling | Justification |
|---------|--------------------|---------|---------------|
| pending max age | **90 d** (was 365) | 365 (V-11) | a note or photo captured offline and unsent for three months is stale for coordination; the server would still accept it (V-11), so the user is asked at day 60 ("send or discard") and the entry is purged at 90 — minimisation (Art. 5(1)(e)) over completeness |
| unsendable max age | **30 d** (was 90) | 90 | a `failed`/`conflict` entry has a visible dialog from the first sync; 30 days is enough to decide |
| dead-session grace (§7) | **14 d** | 30 | long enough for an ordinary re-login after a 30-day refresh-cookie expiry would **not** be — so the choice is deliberate: after a dead session the user must log in within two weeks or lose unsent offline work; the alternative (keep for 365 d) is what #2517 Q3 calls the known gap |
| shared-device mode | **off** | — | §8 |

**PRIV-512** Logout MUST clear every storage key that holds a `user_key`, an e-mail address
or a tenant slug: `kp_local_data_owner`, `kp-garden-field-mode`,
`kp.gardenPlanner.planting.lastUsed.*`, `kp.emailChange.address`, `kp.stepUp.*`, in addition
to `kp_active_tenant_slug` and the pending invitation [v: only the last two are cleared].
UX-only keys (theme, language, kiosk, layout, consent flags) stay.

**PRIV-513** The sweep (`purgeExpiredEntries`) MUST keep running at app start, after login
and before every sync [v], and additionally **on `visibilitychange` → visible** when the last
sweep is older than one hour (a kiosk tablet that never reloads otherwise never sweeps).

---

## 7. Session end, revocation, account deletion

### 7.1 Logout (verified drift, R-056 a)

[v] `clearOfflineData` runs from a Redux listener on `logoutUser.fulfilled/rejected` and
`clearAuth`; `MainLayout` does `await dispatch(logoutUser()); navigate('/login')` — an SPA
navigation, **not** a reload, and the listener's wipe is not awaited. R-056(a) says the wipe
happens "bevor die Seite neu lädt"; for the tenant switch that is true
(`await clearOfflineData(); window.location.reload()`), for logout the order is not
guaranteed.

**PRIV-514** Logout MUST `await clearOfflineData(...)` **before** navigation or reload, and
the guard `offlineDataClearedOnSessionChange.test.ts` MUST pin the await on the logout path
as it pins the tenant switch. Recommendation: logout performs `window.location.replace('/login')`
after the wipe (a reload also drops every in-memory token).

**PRIV-515** [v] Explicit logout with unsent entries asks "send now / discard and log out /
cancel" (`useUnsyncedWritesGuard`). This stays; in shared-device mode (§8) the dialog has no
"keep" option.

**PRIV-516** [v, fix] `KP_CLEAR_DATA` → the worker's `endSession` calls `persistState()`
which rewrites `kp-sw-state` while the window deletes it (possible race, content = client →
namespace map). The worker MUST delete its state instead of persisting it on
`KP_CLEAR_DATA`, and the window MUST wait for the worker's acknowledgement
(`KP_CLEAR_DONE`) before completing the logout.

**PRIV-517** [v] Logout wipes the read cache of **all** users on the device and the write
queue of the leaving user only. Keep: the read cache is 15-minute data; the queue of another
user is their unsent work.

### 7.2 Tenant switch

**PRIV-518** [v, keep] `clearOfflineData()` then `reload()`; the write queue is kept (entries
are namespaced and only synced for the same user+tenant). Guard exists.

### 7.3 Dead session (refresh refused 401/403)

[v] Today: read cache cleared, queue kept, entries wait until 90/365 days; a 403 on replay
marks `failed`; UI-NFR-012 R-060(b) documents it as the known gap (#2517 Q3, P-7 GDPR-006).

**PRIV-519** A refused refresh MUST put every queue entry of the stored `user_key` into
`quarantined` with `expiresAt = now + OFFLINE_DEAD_SESSION_GRACE_DAYS`. Quarantined entries
are never replayed; a successful login of the **same** `user_key` on the device restores
them to their previous state; any other login or the expiry purges them with a notice
("N unsent entries of a previous session were removed").

**PRIV-520** The server MUST return stable `error_code`s the client acts on immediately
(purge instead of quarantine): `account.closed` (erasure requested; the user row still
exists with `is_active=false`), `membership.ended` (no active membership in the tenant of the
write; the user exists). The refresh endpoint returns `account.closed` for a closed account;
the tenant write paths return `403 membership.ended` instead of the generic 403 — **[v]**
today `_membership_for_slug` answers one identical 403 for unknown slug / inactive tenant /
no membership (deliberately, against enumeration). PRIV-520 therefore applies **only to
authenticated callers whose token is valid** (the user exists and is active): the
distinction leaks nothing they could not already see in their tenant list. For an erased
account (user row gone) the generic 401 stays and §7.3's quarantine applies.

**PRIV-521** On `account.closed` the client MUST wipe **everything** of that `user_key`
(queue, caches, the localStorage keys of PRIV-512) without a dialog; on `membership.ended`
only the entries of that `(user_key, tenant_key)`, with a notice.

### 7.4 Account deletion on this device

**PRIV-522** [v, keep] `AccountSettingsPage` wipes read cache and the subject's queue before
redirecting. Add: the PRIV-512 keys.

### 7.5 Kill switch

**PRIV-523** [v, keep] `PWA_CACHING_ENABLED=false` → unregister, delete all caches and all
databases (queue included). **[fix]** the worker probes the flag at most once per 60 s and
only on navigations/activate; a tab that never navigates is reached late. The app MUST also
poll `runtime-config.js` on `visibilitychange` (≥ 60 s apart) and act itself. The P-7 note
that an **old frontend image** leaves data on devices stays true — the kill switch requires
a deployed worker that reads the flag; documented operator limitation.

---

## 8. Shared devices

A logout hint alone is not adequate protection (#2517 Q5). Community gardens use a shared
tablet in the shed; employees share a phone.

**PRIV-524** The operator MUST be able to set `OFFLINE_SHARED_DEVICE_MODE=true` in
`runtime-config.js` (installation-wide), and a tenant `lead ∧ management` MUST be able to set
`settings.shared_device_mode=true` for their tenant (applies when that tenant is active on
the device). In shared-device mode:
- the write queue is **session-bound**: at session end (logout, `beforeunload` of the last
  tab is unreliable → use `visibilitychange: hidden` + a 15-minute idle timer) unsent entries
  are purged after one attempt to send; the UI shows the unsent count prominently while
  offline so the user sends before leaving;
- the read cache TTL drops to 5 minutes and is purged on `visibilitychange: hidden`;
- the idle timer logs the user out after `SHARED_DEVICE_IDLE_MINUTES` (default 15) with the
  wipe of §7.1;
- the login screen shows the mode ("Gemeinsames Gerät — Daten werden beim Abmelden
  gelöscht");
- no "remember me" / token persistence (not implemented anyway, R-048…R-051 deferred).

**PRIV-525** Without shared-device mode the documented hint ("Geteiltes Gerät: immer
abmelden", `docs/de/user-guide/privacy.md`) MUST stay **and** the app MUST show the unsent
count on the tenant switcher and the account menu, so that a user who forgets to log out at
least sees that data remains.

**PRIV-526** The kiosk preference (`kp-kiosk-preference`, REQ-021) MUST imply shared-device
mode defaults unless the operator overrides (a kiosk is by definition shared).

---

## 9. Replay and conflict handling (privacy aspects)

**PRIV-527** [v, keep] Replay is idempotent on `client_event_id`; the digest includes the
caller (`{"user": user_key, "body": …}`), so another member replaying the id is a different
request (409). The digest key reuses `erasure_tombstone_salt` (REQ-053 §32.6 Pkt. 16,
SEC-003) — noted, not changed here; a domain-separated key would need a transition rule.

**PRIV-528** A replay MUST NOT re-introduce personal data that the server has since erased
or redacted: (a) a buffered `note` whose author was erased is refused (`account.closed` /
401 — the author cannot log in); (b) a buffered write that targets a row since redacted
creates a **new** event, never un-redacts (the server never reads client text into an
existing row) [v: `log` inserts or returns the stored winner; no update path]; (c) a
replay of a `complete` for a task completed by someone else answers 409 `task.already_closed`
[v]. Acceptance TA-528.

**PRIV-529** The conflict dialog MUST NOT show another member's name for the server-side
winner (it shows the task state only) — pin in the component test.

---

## 10. Information on the device page

**PRIV-530** The user docs section "Daten auf deinem Gerät" and the in-app account page MUST
show, per device: whether offline mode is on, the number of unsent entries, the age of the
oldest, the retention settings in force, the shared-device mode state, and a "Daten auf
diesem Gerät löschen" button (= `clearAllOfflineStorage()` for this user).

---

## 11. Acceptance criteria

| ID | Criterion |
|----|-----------|
| TA-500 | REQ-025 §10 table equals the storage inventory of §1 (script compares key names in code with the spec table). |
| TA-501 | Every IndexedDB read is filtered by `[userKey+tenantKey]`; a planted foreign row is never returned (regression pin of existing tests). |
| TA-502 | No `localStorage`/`sessionStorage` write of an API payload (guard exists; extend to the PRIV-512 key list on logout). |
| TA-505 | Plan cache evicts oldest beyond `PLAN_CACHE_MAX_BYTES`. |
| TA-509 | Queue refuses a photo beyond `QUEUE_PHOTO_MAX_BYTES`. |
| TA-511 | Sweep uses the configured periods; defaults 90/30/14; a pending entry at 60 d produces the "send or discard" prompt once. |
| TA-512 | After logout none of the listed keys exists in `localStorage`/`sessionStorage`; theme/lang/consent survive. |
| TA-514 | Logout awaits the wipe before navigation; the guard fails on a planted un-awaited call. |
| TA-516 | `KP_CLEAR_DATA` leaves no `kp-sw-state` cache; the window waits for `KP_CLEAR_DONE`. |
| TA-519 | A 401 on refresh quarantines the user's entries; same-user login restores them; another user's login purges them with a notice; expiry purges. |
| TA-520 | Refresh of a closed account → `401 account.closed`; tenant write after membership removal (valid token) → `403 membership.ended`; unknown slug still the generic 403 for an authenticated caller without membership? — **no**: `membership.ended` is returned only when the caller *had* a membership that ended (security audit row exists) — otherwise the generic 403. The test covers all three. |
| TA-521 | `account.closed` wipes everything of the user without a dialog; `membership.ended` wipes `(user, tenant)` entries with a notice. |
| TA-523 | Kill switch acts within one `visibilitychange` on a tab that never navigates. |
| TA-524 | Shared-device mode: idle logout wipes; unsent entries purged after one send attempt at session end; TTL 5 min. |
| TA-528 | Replay after redaction creates no un-redaction; replay by an erased author is refused; replay of a foreign completion → 409. |
| TA-529 | Conflict dialog renders no member name of the winner. |
| TA-530 | Device page shows unsent count, oldest age, settings, and the wipe button works. |
| E2E | extend `tests/e2e/test_req053_wave9_offline.py`: TC "logout clears every user key", TC "dead session quarantine", TC "shared-device idle wipe". |
