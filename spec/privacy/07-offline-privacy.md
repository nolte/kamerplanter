# SPEC-07 — Spezifikation Offline-Datenschutz

```
Paket: spec/privacy · Version 1.2 · 2026-11-22 · Gemessen gegen: develop 007a4ea90 (Audit 2026-11-22)
(v1.1: develop 24d1c2988; Nachtrag #2839 develop 343afbb97)
Anforderungs-IDs: PRIV-500 … PRIV-539
Hängt ab von: UI-NFR-012 v2.4 (R-055 … R-060), REQ-025 §10 (TTDSG-Zeilen), NFR-011 R-41/R-42,
REQ-053 §32.6 Pkt. 13–16, 03 §7 (Löschung offline), 13 (L-11), 15 (DA-07)
Änderung v1.1: Aktivierungsmodell mit Opt-in und Übergang (§2.1, DEC-29), Szenarienmatrix (§8a),
TDDDG und DSGVO getrennt geprüft.
Änderungen 1.2: §1 durch das gemessene Inventar mit 21 Speicherorten ersetzt (SW-Cache unprojiziert LEG-27, ohne
physische Frist LEG-36, `notices` LEG-56, Cookie nur mit „Angemeldet bleiben“ 30 d LEG-37); Ereignis-Matrix (§1.1) und
serverseitiges Verhalten (§1.2); Ist-Stand je Anforderung (Opt-in und Fristen nicht gebaut, Kill-Switch nur Betreiber,
Logout-Wipe nicht abgewartet, keine Quarantäne/Fehlercodes); DSGVO und § 25 TDDDG getrennt (§2.2); Grundsicherung
nach Art. 25/32 vs. Shared-Device-Modus als Produktempfehlung (§8.0); PRIV-534…539 neu; PRIV-524/§8a korrigiert.
```

Die Offline-Schicht von REQ-053 Welle 9 ist implementiert (P-7-Bericht GDPR-001…006). Das Audit 2026-11-22 hat den
Stand neu gemessen: Isolation und Minimierung im IndexedDB-Lesecache sind solide, aber **keine** der Lebenszyklus- und
Aktivierungsanforderungen dieses Dokuments (PRIV-505, 509–514, 516, 519–521, 524–526, 530–533) ist umgesetzt; der
SW-API-Cache hält seit `private, no-cache` unprojizierte Rohantworten. Dieses Dokument bündelt, was auf Geräten
gespeichert wird (Ist), legt die Lebenszyklusregeln fest (Soll), schließt die verifizierte Abweichung zwischen
UI-NFR-012 R-056 und dem Code und beantwortet die fünf Geräte-Fragen aus #2517 (2026-11-09) als Vorschläge für die
rechtliche Prüfung. Umsetzung: PRA-0.07, PRA-0.08, PRA-2.15, PRA-2.16, PRA-2.17 (`12`).

---

## 1. Auf Geräten gespeicherte Daten (gemessen, develop `007a4ea90`, Audit 2026-11-22)

Ersetzt die Tabelle der Fassung 1.1 (gemessen an `24d1c2988`). Pfade ohne Präfix unter `src/frontend/src/`
(`offline/…`, `planCache.ts`, `queue*.ts`, `retention.ts` = `features/gardenPlanner/offline/`), Backend unter
`src/backend/app/`. Legende TDDDG (Vorschlag, § 25 Abs. 2 Nr. 2, L-11): **E** = für den gewünschten Dienst „App“
unbedingt erforderlich (unstreitig); **E\*** = erforderlich nur für eine *ausdrücklich gewünschte* Offline-/
Komfortfunktion → ausdrückliche Handlung nötig (DEC-29, LEG-09); **U** = vom Nutzer selbst gesetzte Einstellung
(Handlung = Wunsch); **K** = Einwilligung (§ 25 Abs. 1).

| # | Speicherort / Name | Inhalt | Personenbezug | Bindung Nutzer+Mandant | Frist (Ist) | Löschauslöser (Ist) | TDDDG | Code-Beleg |
|---|---|---|---|---|---|---|---|---|
| S1 | IndexedDB `kp-plan-cache` (`plans`, `bedLists`, `siteLists`, `bedSummaries`, `bedSheets`) | projizierte Plan-/Beet-/Aufgabendaten (`storedProjection` nullt Mitgliedernamen, Notizen, Beschreibungen, Zuweisungen, Erledigungsnotizen, Fotos, Bewertungen) | ja (Schlüssel, Beet-/Pflanzen-/Aufgabennamen) | Primärschlüssel `{user}:{tenant}:…`, Felder `userKey`/`tenantKey` | 15 min nutzbar (`PLAN_CACHE_TTL_MS`); physisch bis App-Start/Lesen/Schreiben; **keine Byte-Obergrenze** | Logout, toter Refresh, Mandantenwechsel, Kontolöschung hier, Kill-Switch, Light-Mode-Übernahme | E\* | `offline/db.ts:555–585`; `planCache.ts:180–198, 345–367`; `storageWipe.ts:13` |
| S2 | IndexedDB `kp-write-queue` / `entries` | `complete`, Pflegenotiz-Text, Beet-/Pflanzenfotos (≤ 1920 px, JPEG 0.8, EXIF entfernt), `bedName`, `client_event_id`, Zeiten, Zustand | **ja, hoch** (Freitext, Fotos) | Index `[userKey+tenantKey]`, `owned()` | pending **365 d** ab effektivem `performed_at`; failed/conflict/kept **90 d** ab Erfassung (hart kodiert); 500/Nutzer, 5 000/Gerät; **keine Foto-Byte-Obergrenze** | Senden; Verwerfen; bestätigter Logout (nur eigener Nutzer, alle Mandanten); Kontolöschung hier; Fristablauf (nur bei App-Start/Sync); Kill-Switch | E\* (Erfassung = Handlung; Bestand ohne Schalter) | `queueDb.ts:636–660`; `retention.ts:13–32`; `queue.ts:42–47, 234–236, 253–290, 339–369`; `pwa/writeQueueWipe.ts:19–76` |
| S3 | IndexedDB `kp-write-queue` / `notices` | `{userKey, count}` entfernter Einträge | ja (Schlüssel) | `userKey` | **unbefristet** bis Login des Eigentümers (LEG-56) | Quittierung (`acknowledgePurged`), bestätigter Logout, Kontolöschung hier, Kill-Switch | E\* | `queueDb.ts:647–651`; `queue.ts:356–400`; `pwa/writeQueueWipe.ts:57` |
| S4 | Cache Storage `kp:{user_key}:{tenant_key}` (SW-API-Cache) | **Roh**-Antworten `/sites`, `/sites/{k}/plan`, `/locations/{k}/summary` **inkl.** `plan_updated_by_name`, Beet-`notes`/`description` (bis 4 000 Zeichen), `cover_photo_ref` (LEG-27) | **ja, auch Dritte** | Cache-Name, je Client | 15 min **auslieferbar** (`isFresh`); physisch bis Prune/Session-Ende/Überlauf 50 MB (LEG-36) | Logout/toter Refresh/Mandantenwechsel (`KP_CLEAR_DATA` + Fenster löscht alle nicht-öffentlichen Caches), Namespace-Wechsel ohne Nutzer, Kill-Switch | E\* | `sw.ts:104–135, 193–243`; `pwa/apiCache.ts:613–656`; `pwa/cachePolicy.ts:14–17, 87–107, 165–171` |
| S5 | Cache Storage `kp-sw-state` | Client-ID → `kp:{user}:{tenant}`, Byte-Summen | ja (Schlüssel) | — | **unbefristet** (persistiert bei jeder Änderung; LEG-36) | Fenster-Löschung bei Logout u. a. (Race PRIV-516), Kill-Switch | E\* | `sw.ts:57–102, 129–135` |
| S6 | Cache Storage `workbox-precache-*`, `kp-static-assets`, `kp-runtime-config` | App-Shell, Chunks, Laufzeit-Konfiguration | nein | — | bis Build-Revision / 450 Einträge | nur Kill-Switch | E | `pwa/cachePolicy.ts:29–47, 200–202`; `sw.ts:213–280` |
| S7 | Service-Worker-Registrierung `/sw.js` + Background-Sync-Tag `kp-write-queue` | Worker, Sync-Anmeldung | nein | — | bis Deregistrierung | Kill-Switch | E (Shell) / E\* (Sync) | `main.tsx:43` (bedingungslos); `sw.ts:331–339`; `pwa/cachePolicy.ts:64` |
| S8 | PushManager-Abo (Browser) | Push-Endpunkt | ja (serverseitig ans Konto gebunden) | Nutzer (Server) | bis Abmeldung | Logout (`notifyServer:true`), erzwungenes Abmelden (nur Browser) | U (Nutzer aktiviert Push) | `store/sessionListener.ts:51`; `authSlice.ts:95` |
| S9 | localStorage `kp_local_data_owner` | ein `user_key` | ja | — | **nie gelöscht** | — | U/E (Sitzungskontinuität); Hygiene PRIV-512 | `lib/localDataOwner.ts:16, 25–37` |
| S10 | localStorage `kp-garden-field-mode` | `{userKey, tenantSlug, siteKey, tab, viewports}` | ja | `userKey` im Wert (Lesen filtert) | nie gelöscht | — | U | `field/fieldPrefs.ts:27, 45–60` |
| S11 | localStorage `kp.gardenPlanner.planting.lastUsed.{slug}` | Art → Abstände | gering (Slug) | Slug im Schlüssel | nie gelöscht | — | U | `planting/plantingSubmit.ts:164–205` |
| S12 | localStorage `kp_active_tenant_slug` | Slug | gering | — | bis Logout | Logout, erzwungenes Abmelden | E | `tenantSlice.ts:15–20`; `store/sessionListener.ts:44–49` |
| S13 | localStorage UX: `kamerplanter-lang`, Theme, `kp-kiosk-preference`, `kp-dashboard-layout`, `kp-module-visibility`, `kp-plant-grid-format`, `kp_garden_plan_*`, `kp.ai.dailyTip.dismissed.*`, `kp-light-mode-warning-dismissed`, Tabellengrößen | Einstellungen | nein (gerätebezogen) | — | nie | — | U | `i18n/i18n.ts:48–50`; `lib/*Storage.ts`; `editor/use*.ts` |
| S14 | localStorage `kamerplanter:consent:v1`; `plant_identification_consent` (Light-Mode) | Einwilligungsentscheidung | gering | gerätebezogen | nie | — | E (Merken der Entscheidung) | `observability/consent.ts:18, 70, 132`; `identification/PlantIdentificationDialog.tsx:51–63` |
| S15 | sessionStorage `kp.emailChange.address` | ausstehende E-Mail-Adresse | **ja** | — | Tab-Lebensdauer | eigener Ablauf; **nicht** Logout | E | `pages/auth/EmailChangeCard.tsx:28–51` |
| S16 | sessionStorage `kp.stepUp.token/resume/error` | Step-up-Token (5 min) | Auth-Artefakt | — | Tab / Verbrauch | eigener Ablauf; nicht Logout | E | `utils/stepUpReauth.ts:22–26, 147–166` |
| S17 | sessionStorage `kamerplanter.pendingInvitation`, `kamerplanter.loginReturnTo` | Einladungs-Token, Rücksprungpfad | Auth-Artefakt / gering | — | Tab | expliziter Logout | E | `utils/pendingInvitation.ts:18, 41`; `utils/loginReturn.ts:18, 82`; `authSlice.ts:89–94` |
| S18 | Arbeitsspeicher (Redux `auth.accessToken`, alle Slices) | JWT 15 min, Daten | ja | Session-Epoche | Tab | Reducer-Reset bei Session-Ende; Epoch-Middleware verwirft späte Antworten | — (flüchtig; Auslegung: kein Endgerätespeicher i. S. v. § 25) | `authSlice.ts:13, 157–163`; `sessionEpochMiddleware.ts:50–74` |
| S19 | Cookie `kp_refresh` (HttpOnly, `secure=settings.cookie_secure`, `SameSite=Lax`, Pfad `/api/v1/auth`) | Refresh-Token | ja | Konto | **Session-Cookie; 30 d nur mit „Angemeldet bleiben“** (`max_age` nur bei `remember_me`; LEG-37) | Logout (`delete_cookie`), Rotation | E | `api/v1/auth/router.py:251–273, 533–535`; `pages/auth/LoginPage.tsx:39, 85, 198–205`; `auth_service.py:661, 785` |
| S20 | Cookie `csrf_token` (nicht HttpOnly) | CSRF-Double-Submit | nein/gering | — | Session-Cookie | — | E | `api/v1/auth/csrf.py:20–31` |
| S21 | Browser-HTTP-Cache | Offline-Lesepfade nicht (Request-Modus `no-store`); Anhänge `private, no-cache` | ggf. | — | Browser | Logout `Clear-Site-Data: "cache"` | E | `pwa/cachePolicy.ts:128–134`; `common/cache_control.py:57–65`; `attachments/response_headers.py:29` |

Korrekturen gegenüber Fassung 1.1 (Audit 2026-11-22): Der SW-API-Cache ist **nicht** „immer leer“ — die drei Offline-
Lesepfade antworten `private, no-cache` (`allow_offline_read_cache` in `api/v1/sites/tenant_router.py:107`,
`garden_plan/tenant_router.py:339`, `locations/tenant_router.py:361`; `common/cache_control.py:36`), und der Worker
speichert die Antwort **ohne** `storedProjection` (`grep storedProjection src/frontend/src/sw.ts src/frontend/src/pwa/*.ts`
→ 0; LEG-27). Die Lebensdauer „15 min“ (S4) und „Sitzung“ (S5) gilt nur für das Ausliefern; physisch bleiben beide bis
Prune/Session-Ende (LEG-36). Der Refresh-Cookie ist ein Session-Cookie; 30 d gelten nur mit „Angemeldet bleiben“
(LEG-37). Der Store `notices` war nicht inventarisiert (LEG-56).

Nicht vorhanden [VERIFIED_CODE]: `device_id` / Token-Persistenz im Web Storage (R-048…R-051 zurückgestellt; das
Access-Token liegt nur im Redux-Speicher), API-Daten in localStorage, `redux-persist`, RTK Query, Schalter
`kp-offline-mode` (0 Treffer), `OFFLINE_*`-Einstellungen, Zustand `quarantined` (`queueTypes.ts:61`).

### 1.1 Ereignis-Matrix (Ereignis × Speicherort → Verhalten, Ist-Stand)

Abkürzungen: **L** gelöscht · **B** bleibt · **B\*** bleibt, aber für andere Nutzer/Mandanten unsichtbar und nicht sendbar ·
**F** Frist läuft weiter.

| Ereignis | S1 Plan-Cache | S2 Puffer (eigene) | S2 Puffer (andere Nutzer) | S3 `notices` | S4 `kp:*` | S5 `kp-sw-state` | S9–S11 Nutzer-localStorage | S15/S16 sessionStorage | S19 Refresh-Cookie | Server |
|---|---|---|---|---|---|---|---|---|---|---|
| **Expliziter Logout, bestätigt** (`layouts/MainLayout.tsx:105`) | L (nicht abgewartet, PRIV-514) | L (alle Mandanten) | B\* | L (eigener) | L (SW `endSession` + Fenster) | L, aber Race → ggf. neu geschrieben (PRIV-516) | **B** | B (Tab) | L | Refresh widerrufen |
| **Logout ohne Bestätigung / Zählung fehlgeschlagen** | L | **B** | B\* | B | L | L/Race | B | B | L | wie oben |
| **Erzwungenes Abmelden `clearAuth`** | L | B | B\* | B | L | L/Race | B | B | — | — |
| **Browser/Tab geschlossen ohne Logout** | B (bis nächster Start; TTL) | B, F | B\*, F | B | B (unbefristet, LEG-36) | B | B | L (Tab-Ende) | Session-Cookie L; mit „Angemeldet bleiben“ B 30 d | Sitzung lebt |
| **Toter Refresh 401/403 beim Start** (`store/sessionListener.ts:72–77`) | L | **B**, F (keine Quarantäne) | B\* | B | L | L/Race | B | — | — | — |
| **Mandantenwechsel** (`TenantSwitcher.tsx:65`) | L (abgewartet + Reload) | B\* (für alten Mandanten) | B\* | B | L | L | B | B | B | — |
| **Kontolöschung auf diesem Gerät** (`AccountSettingsPage.tsx:726–735`) | L (abgewartet) | L | B\* | L | L | L/Race | **B** | B | serverseitig widerrufen | `is_active=False`, Tokens widerrufen, Löschung nach Karenz |
| **Kontolöschung auf anderem Gerät, dieses Gerät offline → online** | beim Start: Refresh 401 → L | **B bis 365 d / 90 d** (keine Quarantäne, kein `account.closed`) | B\* | B | L | L/Race | B | — | ungültig | jeder Request 401 (`full_auth_provider.py:70–73`) → nichts angenommen |
| **Entzug der Mitgliedschaft (Nutzer aktiv)** | B bis TTL; bei Neuauflösung Namespace-Wechsel → S4 L | Einträge des Mandanten **nie gesendet**, `pending` bis 365 d; falls doch gesendet (Tab offen) → 403 → `failed` 90 d | B\* | B | bei Namespace-Wechsel L | aktualisiert | B | B | B | 403 `_ACTIVE_TENANT_DENIED` (`common/auth.py:247–248`) → nichts angenommen |
| **Mandantenlöschung** (`status` pending_deletion/deleted) | wie Mitgliedschaftsentzug | wie Mitgliedschaftsentzug (bis 365 d) | B\* | B | wie oben | — | B | B | B | `tenant.is_active=False` → 403 (`common/auth.py:240–241`, `tenant.py:96–103`); Tombstones mit dem Mandanten gelöscht (`tenant_erasure_engine.py:236`) |
| **Geteiltes Gerät: B meldet sich an (A ohne Logout)** | A-Zeilen B\* bis TTL-Purge | A: **B\*, F** — per DevTools lesbar | — | A: B | A-Caches bei Prune/Namespace-Wechsel L; mit lebendem A-Tab B\* | aktualisiert | A-Werte **B** (`kp_local_data_owner` sperrt Übernahme durch B — positiv) | gleicher Tab: A-Werte B | A-Cookie durch B-Login überschrieben | — |
| **Sync fehlgeschlagen: Netz/5xx/408/429** | — | `pending`, Backoff 1→60 s, max. 5 Versuche → `failed` (90 d) | — | — | — | — | — | — | — | Idempotenz über `client_event_id` (`client_event_writes.py:36–63`) |
| **Sync: 4xx (422/403/404)** | — | `failed` 90 d ab Erfassung; „Erneut“ → `pending` | — | — | — | — | — | — | — | — |
| **Sync: 409 `payload_mismatch` / `task.already_closed`, 404 `task.missing`/`client_event.deleted`** | — | `conflict` → Dialog; „Behalten“ = auf Gerät, nie gesendet, 90 d | — | — | — | — | — | — | — | Tombstone verhindert Wiedererstellung |
| **Sync: 401** | — | Stopp ohne Versuchszählung; bleibt `pending` | — | — | — | — | — | — | — | — |
| **Wiederverbindung gelöschter Nutzer** | L (toter Refresh) | B bis Frist; Server weist ab (401); Login unmöglich (Zeile weg bzw. `is_active=False`, `password_hash=None`) | B\* | B unbefristet (LEG-56) | L | L/Race | B | — | — | kein Eintrag angenommen |
| **Kill-Switch `PWA_CACHING_ENABLED=false`** | L | L | L | L | L | L | B | B | B | — |
| **App-Start** | Purge > TTL | Purge > Frist | Purge | ergänzt | — | geladen | — | — | Refresh | — |

### 1.2 Serverseitiges Verhalten (VERIFIED_CODE)

- **Abweisung toter Konten und Mitgliedschaften:** Die Kontolöschung setzt sofort `is_active=False` und widerruft die
  Refresh-Tokens (`domain/services/privacy_service.py:983–984`, `:1520–1521`); gelöschte oder geschlossene Konten erhalten
  401 (`domain/engines/full_auth_provider.py:70–73`, `domain/services/auth_service.py:887–889`). Verlust der Mitgliedschaft
  oder ein Mandant mit `status ≠ active` ergibt das generische 403 `_ACTIVE_TENANT_DENIED` (`common/auth.py:169, 237–248`;
  `tenant.py:96–103`). **Serverseitig wird kein gepufferter Eintrag eines gelöschten oder geschlossenen Kontos und kein
  Eintrag nach Mitgliedschaftsende angenommen.** Die Codes `account.closed`/`membership.ended` (PRIV-520) gibt es nicht.
- **Idempotenz:** `client_event_id` mit Digest `{"user": user_key, "body": …}`, HMAC mit `erasure_tombstone_salt`
  (`client_event.py:13–17, 52–55`; `client_event_writes.py:36–63`); Tombstones `client_event_tombstones` 395 d
  (`client_event.py:46`, `06` R-61), bei Mandantenlöschung entfernt (`tenant_erasure_engine.py:236`).
- **Puffer nicht wählbarer Mandanten:** Sync sendet nur im aktiven Scope (`sync.ts`, `owned()`); ein entfernter oder
  gelöschter Mandant erscheint nicht mehr im Umschalter (`TenantSwitcher.tsx`, `_membership_for_slug` `common/auth.py:240–248`).
  Seine Einträge werden **nie gesendet**, bleiben `pending` und damit bis **365 d** (nicht 90 d, wie §7.3 der Fassung 1.1
  nahelegte). Die Nutzerdoku (`docs/de/user-guide/privacy.md:442`, „90 Tage bzw. ein Jahr“) ist zutreffend, das Jahr ist
  aber der Regelfall → PRIV-538.
- **Fern-Widerruf von Sitzungen:** `DELETE /users/me/sessions/{key}` (`AccountSettingsPage.tsx:656` `revokeSession`); das
  Access-Token wird über die Generation sofort ungültig (`full_auth_provider.py:27–36, 73`). Wirksam gegen den
  „vergessenen Logout“ (nur Sitzung; lokale Puffer bleiben bis zum nächsten Start des Zielgeräts, dort 401 → nur
  Lesecaches gelöscht) — bisher weder in §8a noch in der Nutzerdoku (PRIV-539).

---

## 2. TDDDG-§25-Einordnung (LEG-09)

Die deutsche Umsetzung von ePrivacy Art. 5(3) ist das **TDDDG** (am 14. Mai 2024 vom TTDSG
umbenannt); die Specs sagen noch „TTDSG" — redaktionelle Korrektur vorgeschlagen. § 25 Abs. 1 verlangt eine Einwilligung
für das Speichern oder Auslesen von Informationen auf dem Endgerät, sofern nicht § 25 Abs. 2 Nr. 2 greift: die
Speicherung ist **unbedingt erforderlich**, um einen vom Nutzer **ausdrücklich gewünschten** Telemediendienst bereitzustellen.

| Speicher | Vorgeschlagene Einordnung | Begründung | Status |
|---------|-------------------------|-----------|--------|
| `kp-plan-cache`, `kp-write-queue`, `kp:*`, `kp-sw-state` | § 25 Abs. 2 Nr. 2 — erforderlich für die **Offline-Funktion, die der Nutzer wünscht**, indem er die PWA installiert/nutzt und offline handelt | die Funktion kann ohne lokalen Speicher nicht existieren; der Schreibpuffer enthält nur, was der Nutzer eingegeben hat; Minimierung **nur** im IndexedDB-Cache — der SW-API-Cache `kp:*` hält Namen und Notizen (S4, LEG-27), was das Gewicht von LEG-09 erhöht, weil „unbedingt erforderlich“ den Umfang einschließt | REQ-025 v1.40 §10 sagt dasselbe, „Vorschlag, Rechtsprüfung offen (#2517)“. **Ist (Audit 2026-11-22):** implizit, ohne Schalter — SW-Registrierung bedingungslos (`main.tsx:43`), Plan-Cache schreibt bei jedem Online-Lesen (`planCache.ts:160–167`), Puffer ebenso (`queue.ts:143–150`), SW-Cache füllt sich, sobald der Store Nutzer und Mandant kennt (`store/sessionListener.ts:89–96` → `sw.ts:314–319`); einzige Sperre ist der Betreiber-Kill-Switch. Bis DEC-29 umgesetzt ist: `processing_allowed = provisorisch` (Prüfdatum LEG-09) |
| Precache, statische Assets, Runtime-Config | § 25 Abs. 2 Nr. 2 (App-Shell) | keine personenbezogenen Daten | unbestritten |
| `kp_local_data_owner`, `kp-garden-field-mode`, Pflanz-`lastUsed`, Mandanten-Slug | § 25 Abs. 2 Nr. 2 (Sitzungskontinuität / vom Nutzer gesetzter UX-Zustand) | erforderlich für den gewählten Arbeitsablauf; aber **Hygiene**: Schlüssel, die einen `user_key` oder eine E-Mail enthalten, dürfen die Sitzung nicht überdauern (PRIV-512) | Vorschlag |
| Einwilligungs-Flags (`kamerplanter:consent:v1`) | erforderlich (Merken einer Einwilligungsentscheidung) | — | unbestritten |
| Sentry-SDK-Speicher | nicht erforderlich → Einwilligung (`error_tracking`) | REQ-025 TT-002 | in der Spec implementiert |

**PRIV-500** Die obige Einordnung MUSS die einzige Tabelle in REQ-025 §10 sein (Spec-Änderungs-
vorschlag: die vorhandenen localStorage-/sessionStorage-Zeilen ergänzen, `redux_state`,
`i18next`, `theme` entfernen, TTDSG → TDDDG umbenennen). Solange die Tabelle
gilt, ist kein Einwilligungsbanner erforderlich (TT-003). **[LEGAL_REVIEW_REQUIRED LEG-09]**: (a) Ist
„Offline-Nutzung“ ein *ausdrücklich gewünschter* Dienst (L-11: „vom Nutzer ausdrücklich gewünschten digitalen
Dienst“, kumulativ mit „unbedingt erforderlich“), wenn die PWA ohne Opt-in cached? (b) Sind die Fristen aus §6
verhältnismäßig? TDDDG (Zugriff auf das Endgerät) und DSGVO (Verarbeitung der gespeicherten Daten: Art. 5 Abs. 1
lit. c, e; Art. 25 Abs. 2) werden **getrennt** geprüft; die Tabelle oben beantwortet die TDDDG-Frage, §4–§6 die
DSGVO-Frage. **Ist-Stand REQ-025 §10 (Audit 2026-11-22, `DOCUMENTATION_GAP`):** Z. 1723 („heute leer, weil das Backend
`no-store` sendet“) ist veraltet; `i18next`, `theme`, `redux_state` (Z. 1716–1718) existieren so nicht — der
Sprachschlüssel ist `kamerplanter-lang` (`i18n/i18n.ts:50`), `redux-persist` gibt es nicht. Maßstab für die neue
Tabelle ist §1 (S1–S21, TA-500). Umsetzung PRA-2.15 Teil (6), Doku-Korrektur PRA-0.05.

### 2.2 Zwei Rechtsschichten: § 25 TDDDG und DSGVO (Audit 2026-11-22)

**§ 25 TDDDG** regelt nur, **ob** auf dem Endgerät gespeichert oder ausgelesen werden darf (L-11). **Was** gespeichert
wird, wie lange und wie geschützt, ist **DSGVO**. Die Schichten werden getrennt bewertet.

| Ebene | § 25 TDDDG | DSGVO |
|---|---|---|
| Rechtspflicht | Einwilligung (Abs. 1), außer Abs. 2 Nr. 2 greift: **kumulativ** „unbedingt erforderlich“ **und** Dienst „vom Nutzer ausdrücklich gewünscht“ | Rechtsgrundlage der Inhalte Art. 6 Abs. 1 lit. b; zusätzlich Art. 5 Abs. 1 lit. c/e, Art. 25 Abs. 2, Art. 32; Nutzerdoku und REQ-025 §10 müssen den Cache-Inhalt zutreffend beschreiben (Art. 12/13; betroffen auch andere Mitglieder, LEG-27); Art. 17 begründet **keine absolute** Fernlöschpflicht für Kopien auf fremden, offline Geräten |
| Auslegung (INFERRED) | App-Shell (S6/S7) von Abs. 2 Nr. 2 gedeckt. Lesecache, Puffer und SW-API-Cache dienen der „Offline-Nutzung“; Aufruf oder Installation der App ist kein ausdrücklicher Wunsch danach (DA-07) — der Ist-Stand stützt Abs. 2 Nr. 2 nur schwach. Gegenargument: der Puffer entsteht erst durch eine Offline-Erfassung, also eine Nutzerhandlung. Ein persistentes Refresh-Cookie nach ausdrücklichem Anhaken von „Angemeldet bleiben“ ist vertretbar (LEG-37) | Weil die App die Daten selbst ablegt und ein einfacher Weg existiert (Erkennung beim nächsten Online-Kontakt), spricht Art. 25 dafür, ihn zu nutzen (Quarantäne). 365 d für Notiztext und Fotos (`retention.ts:13`) orientieren sich an der Server-Rückdatierungsgrenze, nicht an der Erforderlichkeit (LEG-10). `notices.user_key` (LEG-56) und der SW-Cache ohne physische Frist (LEG-36) wiegen gering |
| Schutzmaßnahme | Opt-in-Schalter (PRIV-531…533, PRA-2.15) | Projektion im SW-Cache (PRIV-534, PRA-0.07); Grundsicherung beim Logout (PRA-0.08); Fristen 90/30/14 d, Quarantäne, Fehlercodes (PRA-2.15); physische Fristen (PRIV-535/536, PRA-2.16) |
| Produktempfehlung | — | Shared-Device-Modus (§8, PRA-2.17) — keine Rechtspflicht |
| Offene Rechtsfrage (`16`) | Genügt ein Geräteschalter mit Erklärtext als „ausdrücklich gewünscht“; ist der Puffer anders zu bewerten als der Lesecache (Q-DSB-06); Übergangsrisiko für Bestandsinstallationen bis DEC-29 (Q-LAW-16) | Angemessenheit 90/30/14 d, Quarantäne als Art.-17-Umsetzung auf fremden Geräten, Hinweis ohne Modus (Q-DSB-07); Art. 14 gegenüber Dritten, deren Daten im Gerätespeicher eines Mitglieds liegen (Q-LAW-17); VVT-Eintrag „Speicherung auf dem Endgerät“ (Q-DSB-08) |

### 2.1 Aktivierungsmodell (DEC-29, ersetzt DEC-21; DA-07)

**PRIV-531** [PROPOSED] Der Offline-Lesecache und der Schreibpuffer DÜRFEN NUR angelegt werden, nachdem die
Nutzerin/der Nutzer den **Offline-Modus auf diesem Gerät ausdrücklich eingeschaltet** hat (Schalter in den
Kontoeinstellungen und im Offline-Hinweis der Feldansicht). Default **aus** für **neue und bestehende**
Installationen. Die App-Shell (Precache, `kp-static-assets`, `kp-runtime-config`) ist davon unabhängig (für den
gewünschten Dienst „App“ unbedingt erforderlich). Der Schalterzustand ist eine Geräteeinstellung
(`localStorage kp-offline-mode`, kein API-Payload) und wird im Art.-15-Bundle nicht benötigt.

**PRIV-532** [PROPOSED] **Übergang bestehender Installationen** (beim ersten Start der neuen Version, `09` §8):
(a) `kp-plan-cache` wird gelöscht; (b) vorhandene Puffer-Einträge werden in einem Übergangsdialog mit „jetzt senden /
verwerfen“ angezeigt; ohne Entscheidung werden sie nach 7 Tagen mit Hinweis gelöscht; (c) der Offline-Modus steht
auf aus, bis er eingeschaltet wird; (d) eine frühere Nutzung der PWA gilt **nicht** als Wunsch nach Offline-Lesen oder
-Puffern (keine stillschweigende Übernahme).

**PRIV-533** Der Schalter MUSS erklären, **welche** Daten gespeichert werden (Kategorien aus §1), **wie lange** (§6)
und **wie** sie gelöscht werden (§7, §10); das Ausschalten löscht Cache und Puffer dieses Geräts für den Nutzer
(nach dem Dialog aus PRIV-515).

**Ist-Stand (Audit 2026-11-22, `CONFIRMED`):** PRIV-531…533 sind **nicht gebaut** (`grep "kp-offline-mode\|offlineMode"`
→ 0; TA-531/532 offen). Die einzige Abschaltung ist der installationsweite **Betreiber**-Kill-Switch
`PWA_CACHING_ENABLED` (Default `true`, `helm/kamerplanter/values.yaml:1063`; gelesen nur beim Start,
`lib/serviceWorkerRegistration.ts:103–107`); Nutzerinnen und Nutzer haben keinen Schalter. Präzisierung zu PRIV-531:
Der Schalter MUSS **alle drei** Lesespeicher gaten — IndexedDB-Lesecache, SW-API-Cache (über `KP_SET_NAMESPACE`: ohne
Schalter `postNamespace(null, null)`) und Puffer (`cacheUsable()`/`writeQueueAvailable()` = false). Umsetzung PRA-2.15
Teil (1); Gate `processing_allowed = provisorisch` bis LEG-09 entschieden ist.

---

## 3. Speicher-Namensraum und Isolation

**PRIV-501** [v, beibehalten] Jeder IndexedDB-Datensatz und jeder API-Cache-Eintrag MUSS
`user_key` **und** `tenant_key` tragen, und jedes Lesen MUSS nach beiden filtern (`owned()`); die Schlüssel
erreichen den Worker per `postMessage` (`KP_SET_NAMESPACE`), nie aus einem Token.

**PRIV-502** [v, beibehalten] Keine API-Daten in `localStorage`/`sessionStorage` (UI-NFR-012 R-055,
Guard `test/guards/…`).

**PRIV-503** [Vorschlag] Der Namensraum MUSS außerdem eine vom Server abgeleitete **Cache-Generation** enthalten
(`X-KP-Cache-Generation`-Header oder `runtime-config.js`-Wert), damit ein serverseitiges
Datenschutzereignis (Löschung, Ende der Mitgliedschaft) alle Geräte-Caches eines Mandanten ohne
Client-Versionssprung invalidieren kann: eine geänderte Generation macht `isFresh` falsch. Geringe Kosten; ersetzt
nichts. Priorität P2.

---

## 4. Cache-Lebenszyklus (Lesecache)

**PRIV-504** [v, beibehalten] TTL 15 min; abgelaufene Einträge werden bei Start/Lesen/Schreiben physisch gelöscht
(NFR-011 R-41, P-7 GDPR-005). Audit 2026-11-22: gilt für S1; wird die App nicht mehr geöffnet, bleiben Restdatensätze
unbegrenzt (Sweep bei `visibilitychange`, PRIV-513).

**PRIV-505** [Vorschlag] `kp-plan-cache` MUSS eine Byte-Obergrenze erhalten (`PLAN_CACHE_MAX_BYTES`,
Standard 20 MB) mit Verdrängung des ältesten zuerst, wie die 50 MB des SW-Caches. Ist: nicht gebaut.

**PRIV-506** [v für den IndexedDB-Lesecache S1] Der Lesecache DARF keine Mitgliedernamen, Notizen, Beschreibungen,
Zuweisungen, Erledigungsnotizen, Fotos oder Bewertungen enthalten (`storedProjection`, `planCache.ts:338–367`); der Guard
sichert die Projektion ab. Beet-/Pflanzen-/Aufgaben-**Namen** bleiben (für das Offline-Blatt nötig) — sie sind
Inhalt, vom Prüfmodell erfasst, wenn sie eine Person benennen. **Korrektur (Audit 2026-11-22, LEG-27):** Für den
SW-API-Cache S4 gilt PRIV-506 **nicht** — er speichert die Rohantwort (`pwa/apiCache.ts:617–626` kopiert den Body
unverändert), also `plan.plan_updated_by_name` (`api/v1/garden_plan/schemas.py:502`,
`data_access/arango/garden_plan_repository.py:351`), Beet-`notes`/`description` (`api/v1/locations/schemas.py:102, 130,
145, 160`) und `cover_photo_ref`. Die Aussagen in `02` (Plan-Cache nullt `plan_updated_by_name`), REQ-025 §10 Z. 1721 und
`docs/de/user-guide/privacy.md:426` gelten nur für S1. **P1.**

**PRIV-534** [PROPOSED, PRA-0.07] Der SW-API-Cache MUSS dieselbe Minimierung wie S1 anwenden. Bevorzugt (A): eine
serverseitige Offline-Projektion der drei Allowlist-Pfade ohne `plan_updated_by_name`, `notes`, `description`,
`cover_photo_ref` (bei `X-KP-Offline-Read: 1` oder generell); alternativ (B) eine gemeinsame `storedProjection`
(aus `planCache.ts` nach `pwa/` verschoben) im SW-Plugin `cacheWillUpdate` vor `cache.put`; oder (C) SW-API-Cache
abschalten und nur IndexedDB nutzen (eine Minimierungsstelle; PO-Entscheidung, `12`). Ein Guard MUSS sichern, dass jede
Allowlist-Route eine Projektion hat. Danach REQ-025 §10, `02` und Nutzerdoku korrigieren. Schutzverstärkend, ohne
Rechtsfreigabe.

**PRIV-535** [PROPOSED, PRA-2.16, LEG-36] Der Worker MUSS bei `activate`, bei jedem `KP_SET_NAMESPACE` und gedrosselt in
`fetch` (≥ 5 min) alle `kp:*`-Einträge mit `x-kp-cached-at < now − TTL` löschen und leere Caches entfernen;
`kp-sw-state` wird beim Prune ohne lebende Clients geleert. Heute verhindert `isFresh` nur das **Ausliefern**
(`pwa/cachePolicy.ts:165–171`; `pwa/apiCache.ts:628–631, 651–653`; kein Sweep über `cachedAt` in `sw.ts`). **P2.**

---

## 5. Puffer-Lebenszyklus (Schreibpuffer)

**PRIV-507** [v, beibehalten] Allowlist von vier Schreibarten; FIFO; einzelner Sender (Web Locks);
Backoff 1 → 60 s, 5 Versuche; `client_event_id` konstant über Versuche hinweg; serverseitige Wiederholung (Replay)
antwortet 200 mit dem gespeicherten Objekt; 409 `client_event.payload_mismatch` für einen anderen Body
unter derselben ID; Konflikte → `conflict`, abgelehnte 4xx → `failed`, 401 → Stopp.

**PRIV-508** [v, beibehalten] Fotos werden auf dem Client neu kodiert (≤ 1920 px, JPEG 0.8, Canvas entfernt
EXIF), generischer Name `photo.jpg`; das serverseitige EXIF-Entfernen bleibt maßgeblich.

**PRIV-509** [Vorschlag] Der Puffer MUSS eine **Foto-Byte-Obergrenze** pro Nutzer erhalten
(`QUEUE_PHOTO_MAX_BYTES`, Standard 100 MB; die UI-NFR-012-Risikotabelle nennt 200 MB ohne
Limit [v]); bei Überschreitung wird die Aufnahme mit `QueueFullError`-Semantik abgelehnt.

**PRIV-510** [Vorschlag] Eintragszustände erhalten `quarantined` (§7); `expiresAt` wird bei
Zustandsänderung neu berechnet (Karenzzeit für tote Sitzungen).

Ist-Stand PRIV-509/510 (Audit 2026-11-22): nicht gebaut — kein `QUEUE_PHOTO_MAX_BYTES`, kein Zustand `quarantined`
(`queueTypes.ts:61`).

**PRIV-536** [PROPOSED, PRA-2.16, LEG-56] Ein Hinweis im Store `notices` MUSS mit `createdAt` gespeichert und in
`purgeExpiredEntries` nach `OFFLINE_DEAD_SESSION_GRACE_DAYS` gelöscht werden; bei Login eines anderen `user_key`
(PRIV-519) wird er mitgelöscht. Heute bleibt `{userKey, count}` bis zur Quittierung durch den Eigentümer — für ein
gelöschtes Konto oder eine Person, die das Gerät nie wieder nutzt, unbefristet (`queueDb.ts:647–651`; `queue.ts:356–364,
373–400`), eine Art.-17-Restspur nach Fristablauf. **P3.**

---

## 6. Aufbewahrung auf dem Gerät (LEG-10)

Aktuelle Platzhalter [v]: 365 d pending (am V-11-Rückdatierungslimit des Servers verankert),
90 d `failed`/`conflict`. Beide sind „Platzhalter-Standard aus #2759; für geteilte Geräte kann
der Betreiber kürzere wählen" (REQ-053 §32.6 Pkt. 14) — aber es existiert keine Einstellung [v].
**Bestätigt (Audit 2026-11-22, Hauptsession):** hart kodiert in `features/gardenPlanner/offline/retention.ts:13`
`ENTRY_MAX_AGE_DAYS = 365` und `:15` `UNSENDABLE_MAX_AGE_DAYS = 90`; keine `OFFLINE_*`-Einstellung. Keine der
Kontrollen PRIV-511, 512, 513, 514, 516, 519, 520, 521, 524, 525, 526 ist umgesetzt (LEG-10, `CONFIRMED`, **P1**:
Notiztext, Fotos und Schlüssel liegen auf geteilten Geräten bis 365 d; nicht P0, weil serverseitig nichts
wiederaufgenommen wird, §1.2). Umsetzung PRA-2.15; die Defaults 90/30/14 d brauchen die DSB-Freigabe (Q-DSB-07),
die Mechanik nicht.

**PRIV-511** Die Fristen MÜSSEN über `runtime-config.js` vom Betreiber konfigurierbar werden
(`OFFLINE_QUEUE_PENDING_MAX_DAYS`, `OFFLINE_QUEUE_UNSENDABLE_MAX_DAYS`,
`OFFLINE_DEAD_SESSION_GRACE_DAYS`, `OFFLINE_SHARED_DEVICE_MODE`) mit diesen Standardwerten und
Begründungen:

| Einstellung | Standard (Vorschlag) | Obergrenze | Begründung |
|---------|--------------------|---------|---------------|
| pending max age | **90 d** (bisher 365) | 365 (V-11) | eine offline erfasste und drei Monate ungesendete Notiz oder ein Foto ist für die Koordination veraltet; der Server würde sie weiterhin annehmen (V-11), daher wird der Nutzer an Tag 60 gefragt („senden oder verwerfen") und der Eintrag an Tag 90 gelöscht — Minimierung (Art. 5(1)(e)) vor Vollständigkeit |
| unsendable max age | **30 d** (bisher 90) | 90 | ein `failed`-/`conflict`-Eintrag hat ab der ersten Synchronisierung einen sichtbaren Dialog; 30 Tage reichen für die Entscheidung |
| dead-session grace (§7) | **14 d** | 30 | lang genug für ein gewöhnliches erneutes Einloggen nach Ablauf des 30-Tage-Refresh-Cookies wäre es **nicht** — die Wahl ist also bewusst: nach einer toten Sitzung muss der Nutzer sich innerhalb von zwei Wochen einloggen oder ungesendete Offline-Arbeit verlieren; die Alternative (365 d behalten) ist die Lücke, die #2517 Q3 als bekannt bezeichnet |
| shared-device mode | **aus** | — | §8 |

**PRIV-512** Der Logout MUSS jeden Storage-Schlüssel löschen, der einen `user_key`, eine E-Mail-Adresse
oder einen Mandanten-Slug enthält: `kp_local_data_owner`, `kp-garden-field-mode`,
`kp.gardenPlanner.planting.lastUsed.*`, `kp.emailChange.address`, `kp.stepUp.*`, zusätzlich
zu `kp_active_tenant_slug` und der ausstehenden Einladung [v: nur die letzten beiden werden gelöscht].
Reine UX-Schlüssel (Theme, Sprache, Kiosk, Layout, Einwilligungs-Flags) bleiben. Dieselbe Liste gilt bei
Kontolöschung auf dem Gerät und bei totem Refresh; eine zentrale Liste (z. B. `pwa/sessionKeys.ts`) mit Guard stellt
sicher, dass jeder neue Schlüssel mit `userKey`, E-Mail oder Slug dort steht (PRA-0.08).

**PRIV-513** Die Bereinigung (`purgeExpiredEntries`) MUSS beim App-Start, nach dem Login
und vor jeder Synchronisierung laufen und zusätzlich **bei `visibilitychange` → visible**, wenn die letzte
Bereinigung älter als eine Stunde ist (ein Kiosk-Tablet, das nie neu lädt, bereinigt sonst nie).
**Korrektur (Audit 2026-11-22):** Heute läuft sie **nur** beim App-Start (`main.tsx:49–55`) und vor dem Sync
(`queue.ts:339–369`); „nach dem Login“ und `visibilitychange` fehlen.

---

## 7. Sitzungsende, Widerruf, Konto-Löschung

### 7.1 Logout (verifizierte Abweichung, R-056 a)

[v] `clearOfflineData` läuft aus einem Redux-Listener bei `logoutUser.fulfilled/rejected` und
`clearAuth`; `MainLayout` macht `await dispatch(logoutUser()); navigate('/login')` — eine SPA-
Navigation, **kein** Reload, und die Bereinigung des Listeners wird nicht abgewartet. R-056(a) sagt, die Bereinigung
geschehe „bevor die Seite neu lädt"; für den Mandantenwechsel stimmt das
(`await clearOfflineData(); window.location.reload()`), für den Logout ist die Reihenfolge nicht
garantiert. **Bestätigt (Audit 2026-11-22):** `layouts/MainLayout.tsx:105–108`; Bereinigung im Listener
`store/sessionListener.ts:35–53`; der Guard `test/guards/offlineDataClearedOnSessionChange.test.ts:116–130` pinnt nur
den Mandantenwechsel.

**PRIV-514** Der Logout MUSS `await clearOfflineData(...)` **vor** Navigation oder Reload ausführen, und
der Guard `offlineDataClearedOnSessionChange.test.ts` MUSS das Await auf dem Logout-Pfad absichern,
wie er den Mandantenwechsel absichert. Empfehlung: Der Logout führt nach der Bereinigung `window.location.replace('/login')`
aus (ein Reload verwirft außerdem jedes Token im Arbeitsspeicher).

**PRIV-515** [v] Ein ausdrücklicher Logout mit ungesendeten Einträgen fragt „jetzt senden / verwerfen und abmelden /
abbrechen" (`useUnsyncedWritesGuard`). Das bleibt; im Modus für geteilte Geräte (§8) hat der Dialog keine
Option „behalten".

**PRIV-516** [v, Korrektur] `KP_CLEAR_DATA` → das `endSession` des Workers ruft `persistState()` auf,
was `kp-sw-state` neu schreibt, während das Fenster es löscht (mögliche Race Condition, Inhalt = Client →
Namensraum-Zuordnung). Der Worker MUSS seinen Zustand bei `KP_CLEAR_DATA` löschen statt ihn zu persistieren,
und das Fenster MUSS auf die Bestätigung des Workers (`KP_CLEAR_DONE`) warten, bevor es den Logout abschließt.
Bestätigt (Audit 2026-11-22): `sw.ts:129–135` schreibt neu, während `offlineData.ts:185–190` löscht. Umsetzung
PRIV-512/514/516 als Logout-Grundsicherung PRA-0.08 (schutzverstärkend, ohne Rechtsfreigabe).

**PRIV-517** [v] Der Logout löscht den Lesecache **aller** Nutzer auf dem Gerät und den Schreibpuffer
nur des abmeldenden Nutzers. Beibehalten: der Lesecache enthält 15-Minuten-Daten; der Puffer eines anderen
Nutzers ist dessen ungesendete Arbeit. Präzisierung (Audit 2026-11-22): Der eigene Puffer wird nur nach
**bestätigtem** Dialog gelöscht (`offlineData.ts:180–193`, `store/sessionListener.ts:41–43`); schlägt die Zählung fehl
oder läuft `clearAuth`, bleibt er (§1.1).

### 7.2 Mandantenwechsel

**PRIV-518** [v, beibehalten] `clearOfflineData()` dann `reload()`; der Schreibpuffer bleibt erhalten (Einträge
sind namensraumgebunden und werden nur für denselben Nutzer+Mandanten synchronisiert). Guard existiert.

### 7.3 Tote Sitzung (Refresh abgelehnt 401/403)

[v] Heute: Lesecache geleert (`store/sessionListener.ts:72–77`), Puffer bleibt, Einträge warten bis zu 90/365 Tage;
ein 403 bei der Wiederholung (Replay) markiert `failed`; UI-NFR-012 R-060(b) dokumentiert es als bekannte Lücke (#2517
Q3, P-7 GDPR-006). **Korrektur (Audit 2026-11-22, `PARTIALLY_CONFIRMED`):** `failed` (90 d) entsteht nur, wenn der
Eintrag überhaupt gesendet wird. Einträge eines Mandanten, den der Nutzer nicht mehr wählen kann (Mitgliedschaftsende,
Mandantenlöschung), werden **nie gesendet** und bleiben `pending` bis 365 d (§1.2). Server: 401 für gelöschte und
geschlossene Konten, generisches 403 `_ACTIVE_TENANT_DENIED` für Mitgliedschafts-/Mandantenverlust; nichts wird
angenommen.

**PRIV-519** Ein abgelehnter Refresh MUSS jeden Puffer-Eintrag des gespeicherten `user_key` in
`quarantined` versetzen mit `expiresAt = now + OFFLINE_DEAD_SESSION_GRACE_DAYS`. Einträge in Quarantäne
werden nie wiederholt; ein erfolgreicher Login desselben `user_key` auf dem Gerät stellt
sie in ihren vorherigen Zustand wieder her; jeder andere Login oder der Ablauf löscht sie mit einem Hinweis
(„N ungesendete Einträge einer früheren Sitzung wurden entfernt").

**PRIV-520** Der Server MUSS stabile `error_code`s zurückgeben, auf die der Client sofort reagiert
(Löschen statt Quarantäne): `account.closed` (Löschung angefordert; die Nutzerzeile existiert noch mit
`is_active=false`), `membership.ended` (keine aktive Mitgliedschaft im Mandanten des
Schreibvorgangs; der Nutzer existiert). Der Refresh-Endpunkt gibt für ein geschlossenes Konto `account.closed` zurück;
die mandantengebundenen Schreibpfade geben `403 membership.ended` statt des generischen 403 zurück — **[v]**
heute antwortet `_membership_for_slug` mit einem identischen 403 für unbekannten Slug / inaktiven Mandanten /
keine Mitgliedschaft (bewusst, gegen Enumeration). PRIV-520 gilt daher **nur für
authentifizierte Aufrufer mit gültigem Token** (der Nutzer existiert und ist aktiv): die
Unterscheidung verrät nichts, was sie nicht ohnehin in ihrer Mandantenliste sehen könnten. Bei einem gelöschten
Konto (Nutzerzeile weg) bleibt das generische 401 und die Quarantäne aus §7.3 gilt.

**PRIV-521** Bei `account.closed` MUSS der Client **alles** zu diesem `user_key` löschen
(Puffer, Caches, die localStorage-Schlüssel aus PRIV-512) ohne Dialog; bei `membership.ended`
nur die Einträge dieses `(user_key, tenant_key)`, mit Hinweis.

**PRIV-538** [PROPOSED, PRA-2.15 Teil (4)] Beim Laden der Mandantenliste MUSS der Client Puffer-Einträge für Mandanten,
die nicht mehr in der Liste stehen, wie `membership.ended` behandeln (Löschung mit Hinweis), statt sie bis zur
365-d-Frist `pending` zu halten.

Ist-Stand PRIV-519…521 (Audit 2026-11-22): nicht gebaut; die Codes `account.closed`/`membership.ended` existieren nicht
(§1.2). Die Unterscheidung `membership.ended` braucht eine Security-Freigabe (Enumeration, TA-520).

### 7.4 Konto-Löschung auf diesem Gerät

**PRIV-522** [v, beibehalten] `AccountSettingsPage` löscht Lesecache und den Puffer des Betroffenen vor
der Weiterleitung (`AccountSettingsPage.tsx:726–735`, `await clearOfflineData({discardWriteQueueOf})`, dann
`location.href='/login'`; bestätigt Audit 2026-11-22). Ergänzen: die PRIV-512-Schlüssel (heute bleiben sie).

### 7.5 Kill-Switch

**PRIV-523** [v, beibehalten] `PWA_CACHING_ENABLED=false` → deregistrieren, alle Caches und alle
Datenbanken löschen (Puffer eingeschlossen). **[Korrektur]** der Worker prüft das Flag höchstens einmal pro 60 s und
nur bei Navigationen/Aktivierung; ein Tab, der nie navigiert, wird spät erreicht. Die App MUSS außerdem
`runtime-config.js` bei `visibilitychange` abfragen (im Abstand von ≥ 60 s) und selbst handeln. Der Hinweis aus P-7,
dass ein **altes Frontend-Image** Daten auf Geräten hinterlässt, bleibt bestehen — der Kill-Switch erfordert
einen ausgerollten Worker, der das Flag liest; dokumentierte Betreiber-Einschränkung. Ist (Audit 2026-11-22): Worker
`sw.ts:141–149, 151–168, 284–286, 295–300`; die App liest das Flag nur beim Start (`lib/serviceWorkerRegistration.ts:103–107`);
Abfrage bei `visibilitychange` offen. Der Kill-Switch ist eine **Betreiber**-Maßnahme für die ganze Installation und
ersetzt weder den Nutzerschalter (PRIV-531) noch die Löschung auf einem einzelnen Gerät (PRIV-530).

---

## 8. Geteilte Geräte

Ein Logout-Hinweis allein ist kein ausreichender Schutz (#2517 Q5). Gemeinschaftsgärten nutzen ein geteiltes
Tablet im Schuppen; Mitarbeitende teilen sich ein Telefon.

### 8.0 Grundsicherung (Art. 25/32) und Shared-Device-Modus (Produktempfehlung) — Audit 2026-11-22

- **Rechtspflicht:** keine ausdrückliche. Weder DSGVO noch TDDDG schreiben einen bestimmten „Modus“ vor; Pflicht sind
  dem Risiko angemessene Maßnahmen (Art. 32 Abs. 1, Art. 25 Abs. 1) und datenschutzfreundliche Voreinstellungen
  (Art. 25 Abs. 2).
- **Auslegung — Grundsicherung unabhängig vom Modus:** Weil Gemeinschaftsgärten und Vereine Zielgruppe sind (RISK-09),
  ist ein geteiltes Gerät **vorhersehbar**; Art. 32 i. V. m. Art. 25 verlangt daher mindestens: abgewarteter
  Logout-Wipe (PRIV-514), Schlüsselhygiene (PRIV-512), Beseitigung der `kp-sw-state`-Race (PRIV-516),
  Quarantäne/Löschung bei totem Konto und bei Login eines anderen Nutzers (PRIV-519), Sichtbarkeit ungesendeter
  Einträge (PRIV-525) und Minimierung im SW-Cache (PRIV-534). Ein reiner Doku-Hinweis („immer abmelden“) genügt dafür
  nicht, weil er das Risiko vollständig auf den Nutzer verlagert, obwohl technisch einfache Mittel existieren. Umsetzung
  PRA-0.07, PRA-0.08, PRA-2.15 — schutzverstärkend, ohne Rechtsfreigabe (außer den Fristwerten).
- **Produktempfehlung — Shared-Device-Modus:** sitzungsgebundener Puffer, Idle-Logout, TTL 5 min, `remember_me`
  erzwungen aus, Kiosk impliziert Modus (PRIV-524/526/537) ist **Empfehlung, nicht Pflicht** — vor allem für
  Kiosk-Tablets und Vereins-PCs; Betreiber- und Mandantenschalter, Default aus, Kiosk = an (PRA-2.17). Option im Modus:
  Logout-Antwort zusätzlich mit `Clear-Site-Data: "storage"` (löscht aber auch Puffer anderer Nutzer und
  Einwilligungs-Flags — nur im Modus vertretbar; Browser-Unterstützung prüfen).
- **Offene Rechtsfrage:** genügt die 14-d-Quarantäne als Art.-17-Umsetzung für Kopien auf fremden Geräten; sind 365 d
  für Freitext/Fotos überhaupt vertretbar (Q-DSB-07 in `16`).

**PRIV-524** Der Betreiber MUSS `OFFLINE_SHARED_DEVICE_MODE=true` in
`runtime-config.js` setzen können (installationsweit), und ein Mandanten-`lead ∧ management` MUSS
`settings.shared_device_mode=true` für seinen Mandanten setzen können (gilt, wenn dieser Mandant auf
dem Gerät aktiv ist). Im Modus für geteilte Geräte gilt:
- der Schreibpuffer ist **sitzungsgebunden**: bei Sitzungsende (Logout, `beforeunload` des letzten
  Tabs ist unzuverlässig → `visibilitychange: hidden` + ein 15-Minuten-Inaktivitäts-Timer verwenden) werden ungesendete Einträge
  nach einem Sendeversuch gelöscht; die UI zeigt die Anzahl ungesendeter Einträge offline prominent an,
  damit der Nutzer vor dem Verlassen sendet;
- die TTL des Lesecaches sinkt auf 5 Minuten und wird bei `visibilitychange: hidden` bereinigt;
- der Inaktivitäts-Timer meldet den Nutzer nach `SHARED_DEVICE_IDLE_MINUTES` (Standard 15) mit der
  Bereinigung aus §7.1 ab;
- der Login-Bildschirm zeigt den Modus („Gemeinsames Gerät — Daten werden beim Abmelden
  gelöscht");
- kein „Angemeldet bleiben“: die Checkbox wird ausgeblendet und `remember_me` serverseitig auf `false` erzwungen
  (PRIV-537). **Korrektur (Audit 2026-11-22, LEG-37):** Die Fassung 1.1 nahm hier an, „Angemeldet bleiben“ sei „ohnehin
  nicht implementiert“. Tatsächlich bietet der Login eine Checkbox (`pages/auth/LoginPage.tsx:39, 85, 198–205`); bei
  Aktivierung setzt der Server das Refresh-Cookie mit `max_age = 30 d`, sonst als Session-Cookie
  (`api/v1/auth/router.py:251–269, 390–411`; `auth_service.py:661, 785`; `config/settings.py:382`). Default aus ist
  datenschutzfreundlich (Art. 25 Abs. 2); auf einem geteilten Gerät mit gesetzter Checkbox und vergessenem Logout
  übernimmt die nächste Person aber die **volle Sitzung**. Nicht implementiert ist nur die Token-Persistenz im Web Storage
  (R-048…R-051 zurückgestellt).

**PRIV-537** [PROPOSED, PRA-2.17, LEG-37] Im Shared-Device-Modus MUSS der Login die Checkbox „Angemeldet bleiben“
ausblenden und der Server `remember_me` ignorieren (Cookie ohne `max_age`); außerhalb des Modus MUSS die Checkbox den
Hinweis „nicht auf geteilten Geräten“ tragen. **P2.**

**PRIV-539** [PROPOSED, PRA-2.15 Teil (6)] Der Fern-Widerruf von Sitzungen (`DELETE /users/me/sessions/{key}`, §1.2)
MUSS in der Nutzerdoku „Daten auf deinem Gerät“ und in der Szenarienmatrix §8a als Abhilfe für den vergessenen Logout
genannt werden; die Doku sagt ehrlich, dass er die Sitzung beendet, lokale Puffer aber erst beim nächsten Start des
Zielgeräts (401 → Lesecaches gelöscht) erreicht.

**PRIV-525** Ohne Modus für geteilte Geräte MUSS der dokumentierte Hinweis („Geteiltes Gerät: immer
abmelden", `docs/de/user-guide/privacy.md`) bestehen bleiben **und** die App MUSS die Anzahl ungesendeter
Einträge am Mandanten-Umschalter und im Kontomenü anzeigen, damit ein Nutzer, der das Abmelden vergisst,
wenigstens sieht, dass Daten verbleiben.

**PRIV-526** Die Kiosk-Präferenz (`kp-kiosk-preference`, REQ-021) MUSS die Standardwerte des Modus für
geteilte Geräte implizieren, sofern der Betreiber sie nicht überschreibt (ein Kiosk ist per Definition geteilt).

### 8a. Szenarienmatrix geteilte Geräte (DA-07)

| Szenario | Risiko | Maßnahme (Anforderung) | Restrisiko |
|----------|--------|------------------------|------------|
| Geteiltes Browserprofil (Familie, WG) | Lesecache/Puffer der vorherigen Person lesbar (DevTools) | Offline-Modus Opt-in je Gerät (PRIV-531); Wipe beim Logout abgewartet (PRIV-514); Schlüsselhygiene (PRIV-512); Puffer nur für denselben `user_key` sendbar (PRIV-501) | niedrig; verbleibt bei Verzicht auf Logout → PRIV-525 Anzeige ungesendeter Einträge |
| Kiosk-Tablet im Schuppen | nie abgemeldet, nie neu geladen | Kiosk ⇒ Shared-Device-Modus (PRIV-526): Idle-Logout, sitzungsgebundener Puffer, TTL 5 min; Sweep bei `visibilitychange` (PRIV-513) | niedrig |
| Vereins-PC mit gemeinsamem Konto | Zurechnung auf eine gemeinsame Identität; Audit unbrauchbar | organisatorisch: ein Konto je Person (Doku); technisch: Shared-Device-Modus; Hinweis in der Mandanten-UI, wenn ein Konto von mehreren Geräten gleichzeitig genutzt wird (Sessions > n) — PROPOSED, P3 | mittel (organisatorisch) |
| Mehrere Nutzer nacheinander am selben Gerät | Puffer A sichtbar für B | Puffer je `user_key`; B sieht A nicht (VERIFIED_CODE `owned()`); A-Einträge werden bei Login von B **nicht** gelöscht (A’s Arbeit) außer im Shared-Device-Modus | niedrig |
| Vergessener Logout, „Angemeldet bleiben“ **nicht** gesetzt (Default) | Zugriff mit A’s Sitzung bis zum Schließen des Browsers (Session-Cookie) | Idle-Logout nur im Shared-Device-Modus; PRIV-525 sichtbar machen; Fern-Widerruf von einem anderen Gerät (PRIV-539, VERIFIED_CODE) | niedrig–mittel |
| Vergessener Logout, „Angemeldet bleiben“ gesetzt (Audit 2026-11-22, LEG-37) | volle Sitzung A’s für die nächste Person bis 30 d | im Modus Checkbox aus und `remember_me` ignoriert (PRIV-537); außerhalb Hinweis an der Checkbox; Fern-Widerruf (PRIV-539); Betreiber kann den Modus installationsweit setzen (PRIV-524) | mittel ohne Modus |
| Kontowiderruf/Entzug der Mitgliedschaft | Puffer/Cache bleiben (Ist: Einträge nicht wählbarer Mandanten bis 365 d, §1.2) | `account.closed`/`membership.ended` (PRIV-520/521), Quarantäne (PRIV-519), Mandantenliste als Auslöser (PRIV-538) | niedrig–mittel (bis 14 d) |
| Offline-Kontolöschung (Antrag auf Gerät A, Gerät B offline) | B behält Daten | B erkennt beim nächsten Online-Kontakt `account.closed` (Karenz) oder 401 (gelöscht) → Löschung/Quarantäne | niedrig–mittel; dokumentierte Lücke bis 14 d (LEG-10) |

---

## 9. Wiederholung (Replay) und Konfliktbehandlung (Datenschutzaspekte)

**PRIV-527** [v, beibehalten] Die Wiederholung (Replay) ist idempotent über `client_event_id`; der Digest enthält den
Aufrufer (`{"user": user_key, "body": …}`), sodass ein anderes Mitglied, das die ID wiederholt, eine andere
Anfrage stellt (409). Der Digest-Schlüssel verwendet `erasure_tombstone_salt` wieder (REQ-053 §32.6 Pkt. 16,
SEC-003) — vermerkt, hier nicht geändert; ein domänengetrennter Schlüssel bräuchte eine Übergangsregel.
Bestätigt (Audit 2026-11-22): `client_event.py:13–17, 52–55`; `client_event_writes.py:36–63`; die
Salt-Mehrfachverwendung ist Teil von LEG-15 (`04`).

**PRIV-528** Eine Wiederholung (Replay) DARF KEINE personenbezogenen Daten wieder einführen, die der Server inzwischen gelöscht
oder geschwärzt hat: (a) eine gepufferte `note`, deren Autor gelöscht wurde, wird abgelehnt (`account.closed` /
401 — der Autor kann sich nicht einloggen); (b) ein gepufferter Schreibvorgang, der eine inzwischen geschwärzte Zeile adressiert,
erzeugt ein **neues** Ereignis und hebt die Schwärzung nie auf (der Server liest nie Client-Text in
eine bestehende Zeile) [v: `log` fügt ein oder gibt den gespeicherten Gewinner zurück; kein Update-Pfad]; (c) eine
Wiederholung (Replay) eines `complete` für eine von jemand anderem erledigte Aufgabe antwortet 409 `task.already_closed`
[v]. Abnahme TA-528. Bestätigt (Audit 2026-11-22): (a) und (c) serverseitig wirksam (`full_auth_provider.py:70–73`;
Tombstones `client_event_tombstones.py:1–11`, 395 d) — ein gepufferter Eintrag eines gelöschten oder geschlossenen
Kontos wird nie angenommen; die Ablehnung erfolgt heute per 401, nicht per `account.closed`.

**PRIV-529** Der Konfliktdialog DARF NICHT den Namen eines anderen Mitglieds für den serverseitigen
Gewinner zeigen (er zeigt nur den Aufgabenzustand) — im Komponententest absichern.

---

## 10. Information auf der Geräteseite

**PRIV-530** Der Abschnitt der Nutzerdokumentation „Daten auf deinem Gerät" und die In-App-Kontoseite MÜSSEN
pro Gerät zeigen: ob der Offline-Modus an ist, die Anzahl ungesendeter Einträge, das Alter des
ältesten, die geltenden Aufbewahrungseinstellungen, den Zustand des Modus für geteilte Geräte und eine Schaltfläche „Daten auf
diesem Gerät löschen" (= `clearAllOfflineStorage()` für diesen Nutzer). Ist (Audit 2026-11-22): nicht gebaut;
Umsetzung PRA-2.15 Teil (5). Die Nutzerdoku MUSS zusätzlich den SW-Cache-Inhalt zutreffend beschreiben (§1 S4) und
den Fern-Widerruf nennen (PRIV-539).

---

## 11. Abnahmekriterien

| ID | Kriterium |
|----|-----------|
| TA-500 | Die Tabelle in REQ-025 §10 entspricht dem Speicherinventar aus §1 (Skript vergleicht Schlüsselnamen im Code mit der Spec-Tabelle). |
| TA-501 | Jedes IndexedDB-Lesen wird nach `[userKey+tenantKey]` gefiltert; eine eingeschleuste fremde Zeile wird nie zurückgegeben (Regressionsabsicherung bestehender Tests). |
| TA-502 | Kein `localStorage`-/`sessionStorage`-Schreibvorgang einer API-Nutzlast (Guard existiert; auf die PRIV-512-Schlüsselliste beim Logout erweitern). |
| TA-505 | Der Plan-Cache verdrängt das Älteste oberhalb von `PLAN_CACHE_MAX_BYTES`. |
| TA-509 | Der Puffer lehnt ein Foto oberhalb von `QUEUE_PHOTO_MAX_BYTES` ab. |
| TA-511 | Die Bereinigung nutzt die konfigurierten Fristen; Standardwerte 90/30/14; ein pending-Eintrag bei 60 d erzeugt die Abfrage „senden oder verwerfen" einmalig. |
| TA-512 | Nach dem Logout existiert keiner der aufgeführten Schlüssel in `localStorage`/`sessionStorage`; Theme/Sprache/Einwilligung bleiben erhalten. |
| TA-514 | Der Logout wartet die Bereinigung vor der Navigation ab; der Guard schlägt bei einem eingeschleusten nicht abgewarteten Aufruf fehl. |
| TA-516 | `KP_CLEAR_DATA` hinterlässt keinen `kp-sw-state`-Cache; das Fenster wartet auf `KP_CLEAR_DONE`. |
| TA-519 | Ein 401 beim Refresh versetzt die Einträge des Nutzers in Quarantäne; Login desselben Nutzers stellt sie wieder her; Login eines anderen Nutzers löscht sie mit Hinweis; Ablauf löscht. |
| TA-520 | Refresh eines geschlossenen Kontos → `401 account.closed`; Mandanten-Schreibvorgang nach Entfernung der Mitgliedschaft (gültiges Token) → `403 membership.ended`; unbekannter Slug weiterhin das generische 403 für einen authentifizierten Aufrufer ohne Mitgliedschaft? — **nein**: `membership.ended` wird nur zurückgegeben, wenn der Aufrufer eine Mitgliedschaft *hatte*, die endete (Security-Audit-Zeile existiert) — andernfalls das generische 403. Der Test deckt alle drei ab. |
| TA-521 | `account.closed` löscht alles des Nutzers ohne Dialog; `membership.ended` löscht die `(user, tenant)`-Einträge mit Hinweis. |
| TA-523 | Der Kill-Switch wirkt innerhalb eines `visibilitychange` bei einem Tab, der nie navigiert. |
| TA-524 | Modus für geteilte Geräte: Abmeldung bei Inaktivität löscht; ungesendete Einträge werden nach einem Sendeversuch bei Sitzungsende gelöscht; TTL 5 min. |
| TA-528 | Wiederholung (Replay) nach Schwärzung hebt keine Schwärzung auf; Wiederholung (Replay) durch einen gelöschten Autor wird abgelehnt; Wiederholung (Replay) einer fremden Erledigung → 409. |
| TA-529 | Der Konfliktdialog zeigt keinen Mitgliedernamen des Gewinners. |
| TA-530 | Die Geräteseite zeigt Anzahl ungesendeter Einträge, ältestes Alter, Einstellungen, und die Löschschaltfläche funktioniert. |
| TA-531 | Ohne eingeschalteten Offline-Modus entstehen weder `kp-plan-cache`-Zeilen noch Puffer-Einträge; die App-Shell wird dennoch vorgeladen; Einschalten erzeugt sie, Ausschalten löscht sie nach Dialog. |
| TA-532 | Übergang: bestehende Installation mit Cache und 3 Puffer-Einträgen → Cache gelöscht, Dialog mit 3 Einträgen, nach 7 Tagen ohne Entscheidung gelöscht (Uhr fixiert), Offline-Modus aus. |
| TA-533 | Unit-Test: `createApiCachePlugin().cacheWillUpdate` (bzw. die serverseitige Projektion) mit `plan.plan_updated_by_name="Sabine"` und `locations[0].notes="x"` → gespeicherter Body enthält beide als `null`; Guard: jede Allowlist-Route hat eine Projektion; E2E: nach der Planansicht enthält `caches.open('kp:…')` keinen Mitgliedernamen. |
| TA-537 | Unit-Test mit fixierter Uhr: ein 16 min alter `kp:*`-Eintrag ist nach dem Sweep nicht mehr in `cache.keys()`; ein leerer Cache wird gelöscht; `kp-sw-state` existiert nach Prune ohne lebende Clients nicht. |
| TA-538 | Unit-Test: ein `notices`-Hinweis älter als die Frist ist nach `purgeExpiredEntries` nicht mehr vorhanden; Login eines anderen `user_key` entfernt ihn. |
| TA-539 | Komponententest: bei `OFFLINE_SHARED_DEVICE_MODE=true` keine Checkbox „Angemeldet bleiben“; Backend-Test: Login mit `remember_me=true` im Modus → Cookie ohne `max_age`. |
| TA-536 | Puffer mit Einträgen für Mandant X; Mandantenliste ohne X → Einträge gelöscht, Hinweis angezeigt. |
| TA-540 | Spec-/Doku-Review: Nutzerdoku und §8a nennen den Fern-Widerruf von Sitzungen mit seiner Grenze. |
| E2E | `tests/e2e/test_req053_wave9_offline.py` erweitern: TC „Logout löscht jeden Nutzerschlüssel", TC „Quarantäne bei toter Sitzung", TC „Bereinigung bei Inaktivität im Modus für geteilte Geräte". |
