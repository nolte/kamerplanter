# SPEC-07 — Spezifikation Offline-Datenschutz

```
Paket: spec/privacy · Version 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97)
Anforderungs-IDs: PRIV-500 … PRIV-539
Hängt ab von: UI-NFR-012 v2.4 (R-055 … R-060), REQ-025 §10 (TTDSG-Zeilen), NFR-011 R-41/R-42,
REQ-053 §32.6 Pkt. 13–16, 03 §7 (Löschung offline), 13 (L-11), 15 (DA-07)
Änderung v1.1: Aktivierungsmodell mit Opt-in und Übergang (§2.1, DEC-29), Szenarienmatrix (§8a),
TDDDG und DSGVO getrennt geprüft.
```

Die Offline-Schicht von REQ-053 Welle 9 ist implementiert und geprüft (P-7-Bericht GDPR-001…006).
Dieses Dokument bündelt, was auf Geräten gespeichert wird, legt die Lebenszyklusregeln fest, die
noch Platzhalter sind, schließt die verifizierte Abweichung zwischen UI-NFR-012 R-056 und dem Code
und beantwortet die fünf Geräte-Fragen aus #2517 (2026-11-09) als Vorschläge für die rechtliche Prüfung.

---

## 1. Auf Geräten gespeicherte Daten (verifiziert, `origin/develop` 24d1c2988)

| Speicher | Name | Inhalt | Personenbezogene Daten | Namensraum | Lebensdauer |
|-------|------|---------|---------------|-----------|----------|
| IndexedDB (Dexie) | `kp-plan-cache` — Stores `plans`, `bedLists`, `siteLists`, `bedSummaries`, `bedSheets` | `{key, userKey, tenantKey, cachedAt, data}`; `storedProjection` setzt `plan_updated_by_name`, `notes`, `description`, Aufgaben-Zuständige, Erledigungsnotizen, Fotos, Bewertungen auf null | `user_key`, `tenant_key`, Beet-/Pflanzennamen, Aufgabennamen | Schlüssel `{user}:{tenant}:{site|location}` | 15 min TTL (`PLAN_CACHE_TTL_MS`); bereinigt beim App-Start, bei jedem Lesen, bei jedem Schreiben; **keine Byte-Obergrenze** |
| IndexedDB (Dexie) | `kp-write-queue` — Store `entries`, `notices` | `QueueEntry {seq, id (client_event_id UUIDv4), userKey, tenantKey, capturedAt, status pending/syncing/failed/conflict, attempts, nextAttemptAt, lastErrorCode, conflictCode, kept, expiresAt, bedKey, bedName, write}`; `write`-Arten `complete`, `note` (Pflegeereignis-Text), `bedPhoto`, `plantPhoto` (`StoredPhoto {bytes ArrayBuffer ≤ 1920 px JPEG 0.8, type, name="photo.jpg"}`) | Notiztext, Fotos, Schlüssel | Index `[userKey+tenantKey]`, `owned()`-Filter bei jedem Lesen | 365 d ab effektivem `performed_at` (pending); 90 d ab Erfassung (`failed`/`conflict`); 500 Einträge/Nutzer, 5 000/Gerät; **keine Byte-Obergrenze für Fotos** |
| Cache Storage | `kp:{user_key}:{tenant_key}` | SW-API-Cache für die 3-Pfad-Allowlist (`/sites`, `/sites/{k}/plan`, `/locations/{k}/summary`) — heute **immer leer**: das Backend sendet `Cache-Control: no-store` bei jeder `/api/v1`-Antwort (MT-044). Entschieden 2026-11-14 (REQ-053 §32.6 Pkt. 13, UI-NFR-012 v2.5): diese drei Pfade antworten `private, no-cache`, der Cache hält Plandaten (umgesetzt mit REQ-053 v1.47). Der HTTP-Cache des Browsers hält sie nicht: Worker und API-Client holen sie mit Request-Cache-Modus `no-store`, Logout sendet `Clear-Site-Data: "cache"` (SEC-001) | wären Plandaten | pro Nutzer+Mandant, Schlüssel validiert `^[A-Za-z0-9_-]{1,128}$` | 15 min, 50 MB, Generationszähler |
| Cache Storage | `kp-sw-state` | Registry Client-ID → Namensraum, Byte-Summen | Schlüssel | — | Sitzung |
| Cache Storage | Precache, `kp-static-assets`, `kp-runtime-config` | App-Shell | keine | — | Build-Revision |
| localStorage | `kp_local_data_owner` | **ein `user_key`** | ja | — | nie gelöscht |
| localStorage | `kp-garden-field-mode` | `{userKey, tenantSlug, siteKey, tab, viewports}` | ja | — | nie gelöscht (ignoriert, wenn `userKey` abweicht) |
| localStorage | `kp_active_tenant_slug` | Slug | gering | — | beim Logout gelöscht |
| localStorage | `kp.gardenPlanner.planting.lastUsed.{tenantSlug}` | Art → Abstand | Slug im Schlüssel | — | nie gelöscht |
| sessionStorage | `kp.emailChange.address` | **ausstehende E-Mail-Adresse** | ja | — | nur durch den eigenen Ablauf entfernt |
| sessionStorage | `kp.stepUp.token/resume/error` | einmaliges Step-up-Token (5 min TTL) | Auth-Artefakt | — | vom Ablauf verbraucht |
| sessionStorage | `kamerplanter.pendingInvitation` | Einladungs-Token | Auth-Artefakt | — | beim Logout gelöscht |
| Arbeitsspeicher | Access-Token (Redux `auth`) | JWT | ja | — | Tab-Lebensdauer |
| Cookie | Refresh (HttpOnly laut Spec), CSRF | — | ja | — | 30 d |

Nicht vorhanden [v]: `device_id` / Token-Persistenz (R-048…R-051 zurückgestellt), API-Daten in
localStorage, `redux-persist`, RTK Query.

---

## 2. TDDDG-§25-Einordnung (LEG-09)

Die deutsche Umsetzung von ePrivacy Art. 5(3) ist das **TDDDG** (am 14. Mai 2024 vom TTDSG
umbenannt); die Specs sagen noch „TTDSG" — redaktionelle Korrektur vorgeschlagen. § 25 Abs. 1 verlangt eine Einwilligung
für das Speichern oder Auslesen von Informationen auf dem Endgerät, sofern nicht § 25 Abs. 2 Nr. 2 greift: die
Speicherung ist **unbedingt erforderlich**, um einen vom Nutzer **ausdrücklich gewünschten** Telemediendienst bereitzustellen.

| Speicher | Vorgeschlagene Einordnung | Begründung | Status |
|---------|-------------------------|-----------|--------|
| `kp-plan-cache`, `kp-write-queue`, `kp:*`, `kp-sw-state` | § 25 Abs. 2 Nr. 2 — erforderlich für die **Offline-Funktion, die der Nutzer wünscht**, indem er die PWA installiert/nutzt und offline handelt | die Funktion kann ohne lokalen Speicher nicht existieren; Daten minimiert (keine Namen, Notizen, Zuweisungen im Cache); TTL 15 min; der Schreibpuffer enthält nur, was der Nutzer eingegeben hat | REQ-025 v1.40 §10 sagt dasselbe, „Vorschlag, Rechtsprüfung offen (#2517)" |
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
DSGVO-Frage.

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
(NFR-011 R-41, P-7 GDPR-005).

**PRIV-505** [Vorschlag] `kp-plan-cache` MUSS eine Byte-Obergrenze erhalten (`PLAN_CACHE_MAX_BYTES`,
Standard 20 MB) mit Verdrängung des ältesten zuerst, wie die 50 MB des SW-Caches.

**PRIV-506** [v, beibehalten] Der Lesecache DARF keine Mitgliedernamen, Notizen, Beschreibungen,
Zuweisungen, Erledigungsnotizen, Fotos oder Bewertungen enthalten (`storedProjection`); der Guard sichert die
Projektion ab. Beet-/Pflanzen-/Aufgaben-**Namen** bleiben (für das Offline-Blatt nötig) — sie sind
Inhalt, vom Prüfmodell erfasst, wenn sie eine Person benennen.

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

---

## 6. Aufbewahrung auf dem Gerät (LEG-10)

Aktuelle Platzhalter [v]: 365 d pending (am V-11-Rückdatierungslimit des Servers verankert),
90 d `failed`/`conflict`. Beide sind „Platzhalter-Standard aus #2759; für geteilte Geräte kann
der Betreiber kürzere wählen" (REQ-053 §32.6 Pkt. 14) — aber es existiert keine Einstellung [v].

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
Reine UX-Schlüssel (Theme, Sprache, Kiosk, Layout, Einwilligungs-Flags) bleiben.

**PRIV-513** Die Bereinigung (`purgeExpiredEntries`) MUSS weiterhin beim App-Start, nach dem Login
und vor jeder Synchronisierung laufen [v] und zusätzlich **bei `visibilitychange` → visible**, wenn die letzte
Bereinigung älter als eine Stunde ist (ein Kiosk-Tablet, das nie neu lädt, bereinigt sonst nie).

---

## 7. Sitzungsende, Widerruf, Konto-Löschung

### 7.1 Logout (verifizierte Abweichung, R-056 a)

[v] `clearOfflineData` läuft aus einem Redux-Listener bei `logoutUser.fulfilled/rejected` und
`clearAuth`; `MainLayout` macht `await dispatch(logoutUser()); navigate('/login')` — eine SPA-
Navigation, **kein** Reload, und die Bereinigung des Listeners wird nicht abgewartet. R-056(a) sagt, die Bereinigung
geschehe „bevor die Seite neu lädt"; für den Mandantenwechsel stimmt das
(`await clearOfflineData(); window.location.reload()`), für den Logout ist die Reihenfolge nicht
garantiert.

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

**PRIV-517** [v] Der Logout löscht den Lesecache **aller** Nutzer auf dem Gerät und den Schreibpuffer
nur des abmeldenden Nutzers. Beibehalten: der Lesecache enthält 15-Minuten-Daten; der Puffer eines anderen
Nutzers ist dessen ungesendete Arbeit.

### 7.2 Mandantenwechsel

**PRIV-518** [v, beibehalten] `clearOfflineData()` dann `reload()`; der Schreibpuffer bleibt erhalten (Einträge
sind namensraumgebunden und werden nur für denselben Nutzer+Mandanten synchronisiert). Guard existiert.

### 7.3 Tote Sitzung (Refresh abgelehnt 401/403)

[v] Heute: Lesecache geleert, Puffer bleibt, Einträge warten bis zu 90/365 Tage; ein 403 bei der Wiederholung (Replay)
markiert `failed`; UI-NFR-012 R-060(b) dokumentiert es als bekannte Lücke (#2517 Q3, P-7 GDPR-006).

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

### 7.4 Konto-Löschung auf diesem Gerät

**PRIV-522** [v, beibehalten] `AccountSettingsPage` löscht Lesecache und den Puffer des Betroffenen vor
der Weiterleitung. Ergänzen: die PRIV-512-Schlüssel.

### 7.5 Kill-Switch

**PRIV-523** [v, beibehalten] `PWA_CACHING_ENABLED=false` → deregistrieren, alle Caches und alle
Datenbanken löschen (Puffer eingeschlossen). **[Korrektur]** der Worker prüft das Flag höchstens einmal pro 60 s und
nur bei Navigationen/Aktivierung; ein Tab, der nie navigiert, wird spät erreicht. Die App MUSS außerdem
`runtime-config.js` bei `visibilitychange` abfragen (im Abstand von ≥ 60 s) und selbst handeln. Der Hinweis aus P-7,
dass ein **altes Frontend-Image** Daten auf Geräten hinterlässt, bleibt bestehen — der Kill-Switch erfordert
einen ausgerollten Worker, der das Flag liest; dokumentierte Betreiber-Einschränkung.

---

## 8. Geteilte Geräte

Ein Logout-Hinweis allein ist kein ausreichender Schutz (#2517 Q5). Gemeinschaftsgärten nutzen ein geteiltes
Tablet im Schuppen; Mitarbeitende teilen sich ein Telefon.

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
- kein „Angemeldet bleiben" / keine Token-Persistenz (ohnehin nicht implementiert, R-048…R-051 zurückgestellt).

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
| Vergessener Logout | Zugriff mit A’s Sitzung | Idle-Logout nur im Shared-Device-Modus; außerhalb: Refresh-Cookie 30 d (VERIFIED_SPEC) → PRIV-525 sichtbar machen; Betreiber kann Modus installationsweit setzen (PRIV-524) | mittel ohne Modus |
| Kontowiderruf/Entzug der Mitgliedschaft | Puffer/Cache bleiben | `account.closed`/`membership.ended` (PRIV-520/521), Quarantäne (PRIV-519) | niedrig–mittel (bis 14 d) |
| Offline-Kontolöschung (Antrag auf Gerät A, Gerät B offline) | B behält Daten | B erkennt beim nächsten Online-Kontakt `account.closed` (Karenz) oder 401 (gelöscht) → Löschung/Quarantäne | niedrig–mittel; dokumentierte Lücke bis 14 d (LEG-10) |

---

## 9. Wiederholung (Replay) und Konfliktbehandlung (Datenschutzaspekte)

**PRIV-527** [v, beibehalten] Die Wiederholung (Replay) ist idempotent über `client_event_id`; der Digest enthält den
Aufrufer (`{"user": user_key, "body": …}`), sodass ein anderes Mitglied, das die ID wiederholt, eine andere
Anfrage stellt (409). Der Digest-Schlüssel verwendet `erasure_tombstone_salt` wieder (REQ-053 §32.6 Pkt. 16,
SEC-003) — vermerkt, hier nicht geändert; ein domänengetrennter Schlüssel bräuchte eine Übergangsregel.

**PRIV-528** Eine Wiederholung (Replay) DARF KEINE personenbezogenen Daten wieder einführen, die der Server inzwischen gelöscht
oder geschwärzt hat: (a) eine gepufferte `note`, deren Autor gelöscht wurde, wird abgelehnt (`account.closed` /
401 — der Autor kann sich nicht einloggen); (b) ein gepufferter Schreibvorgang, der eine inzwischen geschwärzte Zeile adressiert,
erzeugt ein **neues** Ereignis und hebt die Schwärzung nie auf (der Server liest nie Client-Text in
eine bestehende Zeile) [v: `log` fügt ein oder gibt den gespeicherten Gewinner zurück; kein Update-Pfad]; (c) eine
Wiederholung (Replay) eines `complete` für eine von jemand anderem erledigte Aufgabe antwortet 409 `task.already_closed`
[v]. Abnahme TA-528.

**PRIV-529** Der Konfliktdialog DARF NICHT den Namen eines anderen Mitglieds für den serverseitigen
Gewinner zeigen (er zeigt nur den Aufgabenzustand) — im Komponententest absichern.

---

## 10. Information auf der Geräteseite

**PRIV-530** Der Abschnitt der Nutzerdokumentation „Daten auf deinem Gerät" und die In-App-Kontoseite MÜSSEN
pro Gerät zeigen: ob der Offline-Modus an ist, die Anzahl ungesendeter Einträge, das Alter des
ältesten, die geltenden Aufbewahrungseinstellungen, den Zustand des Modus für geteilte Geräte und eine Schaltfläche „Daten auf
diesem Gerät löschen" (= `clearAllOfflineStorage()` für diesen Nutzer).

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
| E2E | `tests/e2e/test_req053_wave9_offline.py` erweitern: TC „Logout löscht jeden Nutzerschlüssel", TC „Quarantäne bei toter Sitzung", TC „Bereinigung bei Inaktivität im Modus für geteilte Geräte". |
