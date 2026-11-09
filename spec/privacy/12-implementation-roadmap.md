# SPEC-12 — Umsetzungs-Roadmap

```
Paket: spec/privacy · Version 1.0 · 2026-11-09 · gemessen gegen develop 24d1c2988
Nur Issue-Vorschläge — nichts davon wurde auf GitHub angelegt. Titel sind englisch und
direkt einfügbar; jede Einheit ist unabhängig umsetzbar und benennt ihre Abhängigkeiten.
```

---

## 0. Einordnung in die laufende REQ-053-Arbeit

- Die REQ-053-Partition vom 2026-11-09 plant **#2770** (Backfill-Tombstone-Kopien,
  Reminder-`created_by`, v0104-Mandanten-Gate, Einfrieren von `SOURCE_COLLECTIONS`) als
  nächste Lane nach dem Wave-10-Plan (#2758). **PRIV-E01 unten ist #2770**, mit durch
  `04` §2–3 geschärfter Akzeptanz; es sollte in dieser Warteschlange bleiben und auf dieses
  Paket verweisen, statt dupliziert zu werden.
- **#2517** bleibt das Rechts-Issue; dieses Paket liefert dafür die LEG-Liste und das
  DSFA-Vorscreening (`11`) als Eingabe, die der DSB braucht. Es blockiert P0/P1-Engineering
  nicht: Jedes Element wird mit dem dokumentierten Default ausgeliefert und benennt die LEG,
  die ihn ändern kann.
- Wave 10 von REQ-053 (Indoor-Grundriss) hat keine Datenschutz-Punkte; die Epics unten bilden
  eigene Lanes (`feat/priv-<slug>` von `origin/develop`, eigener Worktree, serieller
  Merge-Zug).

Prioritätsstufen: **P0** kritische Datenschutz-/Datenintegritäts-Defekte (in der nächsten
Lane beheben) · **P1** Kern-Lebenszyklus und Zugriffskontrolle · **P2** Aufbewahrung,
Administration, Offline-Schutzmaßnahmen · **P3** Governance, Monitoring, kontinuierliche
Compliance.

---

## P0 — Kritische Defekte

### PRIV-E01 · fix(care-events): never copy a tombstone into the care log; one actor rule for confirmations; v0104 gates and source list (= #2770)

- **Problem**: `account_of` kopiert `anon_<hash>`-Pseudonyme aus den gesetzlich
  aufbewahrten Zeilen gelöschter Konten nach `care_events.performed_by_user_key` (v0104 und
  der tägliche Konsistenz-Job); die Löschregel für Pflegeereignisse erreicht sie nie; die
  Bestätigungspfade von Task-Queue und MCP speichern `null`, während REST/Benachrichtigung
  den Aufrufer speichern; Reminder-Zeilen haben kein `created_by`; v0104 schreibt in
  nicht aktive Mandanten und iteriert eine veränderliche Quellliste.
- **Scope**: `carry_account_reference` in `domain/models/privacy.py` (PRIV-205), genutzt von
  `care_event_backfill_mapper.account_of` und `task_completion_engine`; Principal wird auf
  den Bestätigungspfaden von Task-Queue und MCP übergeben (PRIV-003/119); `created_by =
  principal` bei Live-Reminder-Ereignissen, `null` beim Backfill (PRIV-214); Korrekturrecht
  für Systemzeilen (PRIV-215); `display_performer`/Filter behandeln Tombstone-förmige Werte
  wie den Marker (PRIV-207); v0104: `ActiveTenants`-Gate für die Backfill-Art, eingefrorenes
  Quell-Tupel, `_DOWN_SCAN` unterscheidet Zeilen migrationsbürtiger Herkunft; einmalige
  Korrektur bereits kopierter Tombstones → **PRIV-E04** (Migration), falls v0104 irgendwo
  gelaufen ist (P-6 sagt, es lief am 2026-11-07 in Produktion? — den P-6-Bericht prüfen; die
  lokale Analyse fand den Backfill gemergt).
- **Abhängigkeiten**: keine (Konstanten dürfen hier eingeführt und in E03 konsolidiert
  werden).
- **Akzeptanz**: TA-002, TA-003/120, TA-121, TA-123, TA-203, TA-801; der Dry-Run-Bericht
  listet `tombstone_sources_marked`.
- **Tests**: `test_care_event_backfill_mapper.py` (Tombstone-Fall), der Bestätigungstest über
  vier Pfade mit Assertion auf den Durchführenden (heute nur Trigger/Kategorie),
  Unit-Test für das v0104-Mandanten-Gate.
- **Spec-Verweise**: `01` §4, `03` §4, `04` §2.2/§3.3.
- **Offene Rechtsfrage**: LEG-07 (blockiert den technischen Fix nicht).

### PRIV-E02 · fix(privacy): suppress a closed account's display name during the erasure grace

- **Problem**: Nach `request_erasure` wird der Name der betroffenen Person bis zu 90 Tage
  lang aufgelöst (`is_active` wird von den Anzeige-Joins ignoriert).
- **Scope**: Anzeige-Joins lesen `is_active`; geschlossen → Zustand `erased` (PRIV-104);
  die Plattform-Löschvorschau bleibt unberührt.
- **Abhängigkeiten**: keine (kann dem Resolver vorausgehen; E05 verschiebt es in den
  Resolver).
- **Akzeptanz**: TA-100, TA-101.
- **Spec-Verweise**: `03` §2.2.

### PRIV-E03 · refactor(privacy): one definition of marker, tombstone regex and `[redacted]`; residue scan for account erasure

- **Problem**: vier Marker-Kopien, drei Regex-Literale; die Mandantenlöschung hat eine
  Residuenprüfung, die Kontolöschung keine.
- **Scope**: Konstanten in `domain/models/privacy.py` (PRIV-201); Guard, der den Drei-Kopien-Pin
  ersetzt; Residuen-Scan im `erasure_executor`, der `partially_completed` mit `residue`
  markiert (PRIV-234).
- **Abhängigkeiten**: keine.
- **Akzeptanz**: TA-200, TA-102/208.
- **Spec-Verweise**: `04` §1, §8.

### PRIV-E04 · chore(migrations): v0107 — convert copied tombstones to the marker, plan-audit actor to the marker, clear anonymised attachments' file names

- **Problem**: Legacy-Kopien (E01) existieren in Produktionsdaten; der Tombstone in
  `garden_plan_audit.user_key` hat keine Grundlage (DEC-16); `original_filename` überlebt die
  Löschung.
- **Scope**: `09` §3 (v0107), Inventaränderung für `garden_plan_audit` und `attachments`
  (`clear_fields`), persistierter Dry-Run-Bericht (`09` §2 Minimum: `--report-out`).
- **Abhängigkeiten**: E01 (Konstanten), E03.
- **Akzeptanz**: TA-700, TA-701, TA-207, TA-209.
- **Spec-Verweise**: `04` §4.1/§7, `09` §2–3.
- **Offene Rechtsfrage**: LEG-15 (Marker vs. Tombstone für das Plan-Audit) — Default Marker.

---

## P1 — Kern-Datenschutz-Lebenszyklus und Zugriffskontrolle

### PRIV-E05 · feat(identity): attribution registry and the single person resolver (`PersonRef`)

- **Problem**: keine deklarierte Zuordnungsrolle pro Feld; die Anzeige wird ad hoc aufgelöst;
  das Backend gibt das deutsche Literal „anonymisiert" aus; das Plan-Audit liefert
  `null`-Akteure.
- **Scope**: `AttributionRole`, `RetentionClass`, `review_fields` an den Inventarmodellen
  (`08` §2.1); Guard R7; `IdentityReferenceService.resolve_display` (`08` §2.3); `*_kind`-Felder
  in den Antworten von Pflegeereignissen und Plan-Audit; Frontend-i18n `enums.personRef.*`;
  Deprecation des Literals.
- **Abhängigkeiten**: E02, E03.
- **Akzeptanz**: TA-001, TA-004…TA-007, TA-030 (Doku-Prüfskript); PRIV-218 (Plan-Audit-Akteur
  als `PersonRef`) wird durch TA-005 abgedeckt.
- **Spec-Verweise**: `01` §4, `08` §2–3.

### PRIV-E06 · feat(tenants): former-member name suppression and leave/removal transparency

- **Problem**: Ein ausgetretenes Mitglied bleibt für immer namentlich genannt; beim Austritt
  gibt es keine Information.
- **Scope**: `RETENTION_FORMER_MEMBER_NAME_DAYS` (Default 90), abgeleiteter Zustand aus der
  Austrittszeile des Security-Audits (PRIV-112/114), Filter-/CSV-Verhalten, Texte für
  Austrittsdialog und Entfernungshinweis DE/EN (PRIV-115), Beitritts-Semantik bei erneutem
  Beitritt (PRIV-118), Service-Accounts (PRIV-134).
- **Abhängigkeiten**: E05.
- **Akzeptanz**: TA-110…TA-114.
- **Spec-Verweise**: `03` §3.
- **Offene Rechtsfrage**: LEG-06 (Frist, Umfang von Art. 15).

### PRIV-E07 · feat(privacy): free-text review queue and generic redaction for tenant leads

- **Problem**: Die Löschung lässt inhaltlichen Freitext zurück, der die Person nennt; es gibt
  keine Liste der betroffenen Zeilen; Schwärzung nur für Pflegeereignisse, nur für Leads,
  keine UI-Aktion.
- **Scope**: Collection `privacy_review_items` + Indizes + Mandanteninventar (`08` §3.7);
  Item-Erzeugung als Post-Commit-Phase der Kontolöschung mit Namens-Token-Markierung,
  Grenzen, Idempotenz (PRIV-221…223, PRIV-108); `REDACTABLE_FIELDS`; generischer
  Schwärzungsdienst und Routen (`08` §4.1); Lineage-Vorschläge für Templates/Audit
  (PRIV-230); `management` darf schwärzen (PRIV-231, Spec-Änderungsvorschlag); `material`
  und Mess-Strings kommen in die Schwärzungsmenge (PRIV-213, Spec-Änderungsvorschlag);
  Frontend `PrivacyReviewPage` (Lazy-Chunk), Zusammenfassung, i18n; Datenschutz-Aktionen in
  `security_audit_log` (`08` §3.8 Teilmenge: `REDACTION_APPLIED`, `REVIEW_DECIDED`);
  R-43-Beat; Metriken `privacy_review_items_*`.
- **Abhängigkeiten**: E05 (Registry `review_fields`), E03.
- **Akzeptanz**: TA-103, TA-205, TA-206, TA-210, TA-211, TA-226 (Überfälligkeits-Metrik),
  TA-305, TA-307, TA-809.
- **Spec-Verweise**: `04` §5–6, `08` §3.7/§4.1/§5–6.
- **Offene Rechtsfrage**: LEG-08 (Modell und SLA) — Default wird ausgeliefert.

### PRIV-E08 · feat(tenants): `attribution_visibility` setting, purpose permissions, member e-mail restriction, audited name exports

- **Problem**: Jedes Mitglied sieht jeden Durchführenden und die E-Mail jedes Mitglieds; CSV
  mit Namen für alle; kein Audit von Namensexporten; die beschreibende Berechtigungsmatrix
  weicht von den Gates ab.
- **Scope**: `TenantSettings.attribution_visibility` (Default `all_members`),
  Resolver-Integration (PRIV-300…303); Berechtigungen `attribution.filter|export`,
  `privacy.review` (PRIV-304); `MemberInfoResponse.email` nur für `management` (PRIV-305,
  **Breaking Change**, Frontend angepasst); CSV-`R`-Rendering für Nicht-Leads +
  `ATTRIBUTION_EXPORTED`-Audit (PRIV-307/308); die Zuweisungsspalte im Beetlisten-CSV folgt
  der Einstellung (PRIV-309); MCP-Tools liefern `PersonRef` (PRIV-310, REQ-033
  Versionssprung); `inspector = "mcp:<key>"` → `inspected_by_key`; Mandanten-Einstellungs-UI
  mit der Erklärung zu §26 BDSG/BetrVG; kein Per-Person-Aggregations-Guard (PRIV-403);
  Kommentare der `_RBAC`-Tabelle an die Gates angepasst (Folgearbeit in `05` §1 vermerkt).
- **Abhängigkeiten**: E05.
- **Akzeptanz**: TA-300…TA-309.
- **Spec-Verweise**: `05`, `06` §5.
- **Offene Rechtsfrage**: LEG-02, LEG-05 (Default für Organisations-Mandanten), LEG-14.

### PRIV-E09 · feat(tenants): `record_keeping` profile — statutory retention only where a duty exists

- **Problem**: Die Aufbewahrung nach PflSchG/KCanG und Tombstones gelten für jeden Mandanten.
- **Scope**: `TenantSettings.record_keeping` (Default `legacy`), v0108, Verzweigung von
  Löschung/Mandanteninventar nach der Klasse (PRIV-122, PRIV-401), Reklassifizierungs-Job
  (PRIV-402, `09` §4), Anlage-Ablauf fragt Organisations-Mandanten, Audit-Aktion, Doku
  (Querverweis auf `compliance-anbauvereinigung.md`).
- **Abhängigkeiten**: E05.
- **Akzeptanz**: TA-122, TA-403/703, TA-404.
- **Spec-Verweise**: `03` §5, `06` §3, `09` §4.
- **Offene Rechtsfrage**: LEG-03, LEG-04, LEG-17 — der Default `legacy` behält das heutige
  Verhalten bei, bis entschieden ist; der Schalter existiert, damit die Entscheidung ohne
  Release angewendet werden kann.

### PRIV-E10 · feat(offline): dead-session quarantine, stable revocation codes, awaited logout wipe, storage-key hygiene

- **Problem**: Ein anderswo gelöschtes Konto lässt die Queue bis zu 365 d bestehen; der
  Logout-Wipe wird nicht abgewartet; `kp-sw-state`-Race; `localStorage` behält
  `user_key`/E-Mail; nur ein generisches 403.
- **Scope**: Zustand `quarantined` und Dexie v3 (PRIV-510/519, `09` §8); `401 account.closed`
  bei Refresh/Schreibzugriffen für geschlossene Konten, `403 membership.ended` für gültige
  Tokens mit erfasstem Austritt (PRIV-520/131); Client-Reaktionen (PRIV-521); abgewarteter
  Wipe + `replace` (PRIV-514); `KP_CLEAR_DONE`-Handshake (PRIV-516); PRIV-512-Schlüsselliste;
  Sweep bei `visibilitychange` (PRIV-513); Kill-Switch-Poll (PRIV-523);
  Guard-Erweiterungen.
- **Abhängigkeiten**: keine auf E05 (Client- und Auth-Pfade).
- **Akzeptanz**: TA-131, TA-502, TA-512, TA-514, TA-516, TA-519…TA-521, TA-523, TA-528,
  TA-803; E2E TC-053-091/092.
- **Spec-Verweise**: `03` §7, `07` §7.
- **Offene Rechtsfrage**: LEG-10 (Karenzzeit) — Default 14 d.

---

## P2 — Aufbewahrung, Administration und Offline-Schutzmaßnahmen

### PRIV-E11 · feat(offline): configurable device retention, shared-device mode, byte ceilings, device page

- **Scope**: Runtime-Config-Einstellungen und Defaults 90/30 (PRIV-511), 60-Tage-Hinweis,
  `PLAN_CACHE_MAX_BYTES`, `QUEUE_PHOTO_MAX_BYTES` (PRIV-505/509), Shared-Device-Modus
  installations- und mandantenweit mit Idle-Logout, sitzungsgebundene Queue, 5-Min-TTL,
  Login-Banner, Kiosk-Implikation (PRIV-524…526), Offline-Opt-in-Schalter
  (LEG-09-Empfehlung), Geräteseite (PRIV-530), Doku DE/EN, Korrektur der REQ-025-§10-Tabelle
  inkl. TDDDG-Umbenennung (Spec-Änderung).
- **Abhängigkeiten**: E10.
- **Akzeptanz**: TA-500, TA-505, TA-509, TA-511, TA-524, TA-530; E2E TC-053-093.
- **Spec-Verweise**: `07` §2, §4–6, §8, §10.
- **Offene Rechtsfrage**: LEG-09, LEG-10.

### PRIV-E12 · feat(privacy): attribution removal on leaving a tenant (Art. 21 / 17(1)(c))

- **Scope**: `POST /t/{slug}/privacy/attribution-removal` (Step-up), mandantenbezogener
  Marker-Lauf, der `ANONYMIZE_COLLECTIONS` nach `tenant_key` gefiltert wiederverwendet,
  Review-Items, Audit-Aktion `ATTRIBUTION_REMOVED`, gesetzliche Ausnahme je
  `record_keeping`, Text bei erneutem Beitritt (PRIV-116/118).
- **Abhängigkeiten**: E06, E07, E09.
- **Akzeptanz**: TA-112, TA-805.
- **Spec-Verweise**: `03` §3.2.
- **Offene Rechtsfrage**: LEG-06.

### PRIV-E13 · feat(retention): new rows R-46 (watering/feeding/tank logs), R-47 (closed tasks/comments), R-48 (notifications); keyed performer fields

- **Scope**: Migration v0109 für Schlüssel-Durchführende (`09` §5), Request-Schemas mit
  `performed_by_label`, UI-Dialoge „Ich war's / jemand anderes", Nährstoffplan-`author_*`,
  `workflow_templates.created_by_user_key`; Aufbewahrungs-Beats mit Obergrenzen;
  NFR-011-Zeilen (Spec-Änderungsvorschlag); Art.-15-Manifest-Quellen für die neuen
  Schlüsselfelder (R2).
- **Abhängigkeiten**: E05.
- **Akzeptanz**: TA-702, TA-400…TA-403, TA-603.
- **Spec-Verweise**: `06` §2.3, `08` §3.4, `09` §5.
- **Offene Rechtsfrage**: Fristen gemäß NFR-011 v1.29 („Vorschlag, DSB-Prüfung offen").

### PRIV-E14 · feat(backup): erasure replay ledger, bucket mirror, restore replay command, dump retention — before enabling backups

- **Scope**: `erasure_replay_ledger` + R-45-Beat, Mirror-Objekt, CLI
  `privacy_restore_replay`, Erweiterung von `backup-restore.md`, Helm
  `backup.retentionDays` Obergrenze 35, Restore-Drill-Test (nightly), Collection
  `migration_reports` und `--report-out` (`09` §2), falls nicht in E04 erledigt.
- **Abhängigkeiten**: E03 (Plan-Fingerprint), E07 (Review-Item-Replay).
- **Akzeptanz**: TA-709…TA-711, TA-804.
- **Spec-Verweise**: `09` §6, `08` §3.7.
- **Offene Rechtsfrage**: LEG-11.

---

## P3 — Governance, Monitoring, kontinuierliche Compliance

### PRIV-E15 · feat(observability): privacy-operations endpoint, metrics, consistency beat, stale alerts, unified escalation, resume job

- **Scope**: `GET /admin/platform/privacy/operations|consistency`, Beat
  `privacy.consistency` (PRIV-206), Metriken (`08` §5), gemeinsames
  `PRIVACY_OPERATION_ESCALATE_AFTER_ATTEMPTS` (PRIV-109), Stale-Alert (PRIV-110), verwaiste
  Mandanten im Monitoring (PRIV-127), Job `privacy.resume_partial_erasures` (PRIV-717),
  R-06-Docstring-Korrektur, Grafana-Panel (Doku).
- **Abhängigkeiten**: E03, E07.
- **Akzeptanz**: TA-104, TA-105, TA-202, TA-305, TA-717.
- **Spec-Verweise**: `03` §2.4, `04` §2.2, `08` §4.2/§5–6.

### PRIV-E16 · docs(privacy): spec change set — REQ-025 / NFR-011 / REQ-053 / REQ-024 / REQ-049 / REQ-022 / REQ-023 / user docs

- **Scope**: die Vorschläge aus `06` §9 als versionierte Änderungen mit Changelog-Zeilen:
  Zuordnungsrollen und Review-Phase in REQ-025 §3.1.3; §10-Tabelle (Schlüssel, TDDDG);
  NFR-011 R-43…R-48, R-26-Marker, R-25-Formulierung und `material`; REQ-053
  GP-FR-109-vs-E-16-Widerspruch, GP-NFR-055 Plan-Audit-Marker; REQ-024/REQ-049
  Einstellungen und E-Mail-Regel, `management` darf schwärzen; REQ-022 Bestätigungen haben
  keinen Akteur; REQ-023 §5b.1 Zeile zum Backup-Lesezugriff; Docs `privacy.md`
  DSFA-Satz; Abschnitt „Für Betriebe und Vereine" mit der Betriebsrats-Vorlage (PRIV-406);
  Versions-/Footer-Drift (REQ-025-Footer 1.5, NFR-011-Footer 1.7, REQ-051-Footer 1.0).
- **Abhängigkeiten**: Betreiber-Freigabe der DEC-Punkte; keine technischen.
- **Akzeptanz**: `mkdocs build --strict`; Spec-Readiness-Review; jede Changelog-Zeile zitiert
  `spec/privacy`.
- **Offene Rechtsfrage**: der Wortlaut der Art.-13/14-Texte (LEG-12).

### PRIV-E17 · docs(privacy): DPIA hand-over package and RoPA input

- **Scope**: `11` mit der LEG-Liste an den DSB übergeben; die RoPA-Eingabetabelle aus `02`
  erzeugen (Export-Skript, das aus der Registry ein CSV der Verarbeitungstätigkeiten
  erzeugt — optionale Automatisierung, P3); Entscheidungen zurück in `decision-log.md`
  eintragen.
- **Abhängigkeiten**: E05 (Registry als Quelle).
- **Akzeptanz**: Decision-Log-Zeilen LEG-01…17 haben einen anderen Status als `open`.

---

## Abhängigkeitsgraph

```mermaid
flowchart LR
    E01["P0 E01 (Issue 2770)"] --> E04["P0 E04 v0107"]
    E03["P0 E03 constants+residue"] --> E04
    E02["P0 E02 closed-name"] --> E05
    E03 --> E05["P1 E05 registry+PersonRef"]
    E05 --> E06["P1 E06 former member"]
    E05 --> E07["P1 E07 review queue"]
    E05 --> E08["P1 E08 visibility"]
    E05 --> E09["P1 E09 record_keeping"]
    E10["P1 E10 offline revocation"] --> E11["P2 E11 device retention"]
    E06 --> E12["P2 E12 attribution removal"]
    E07 --> E12
    E09 --> E12
    E05 --> E13["P2 E13 retention rows"]
    E03 --> E14["P2 E14 backups"]
    E07 --> E14
    E03 --> E15["P3 E15 observability"]
    E07 --> E15
    E05 --> E17["P3 E17 DPIA/RoPA"]
    E16["P3 E16 spec changes"]
```

Vorgeschlagene Lane-Reihenfolge im seriellen Merge-Zug: E01 → E03 → E02 → E04 → E05 → E10 →
E07 → E08 → E06 → E09 → E11 → E13 → E15 → E12 → E14 → E16/E17 (Doku kann parallel laufen,
da sie nur `spec/` und `docs/` berührt).

---

## Issue-Template (für jedes Epic bei der Anlage)

```
**Spec:** spec/privacy/<doc> §<n>, PRIV-<ids>. Priorität <P0..P3>. Abhängig von: <E..>.
## Problem
## Scope (in / out)
## Akzeptanz (TA-ids)
## Tests
## Offene Rechtsentscheidungen (LEG-ids; der Default, mit dem dieses Issue ausgeliefert wird)
## Leitplanken: BACKEND.md/FRONTEND.md; `*, tenant_key: str`; Route-Walk + Route-Consumer-Pin + begrenzte Listen für neue Routen;
Enums additiv mit DE/EN-i18n; Bundle-Budget; kein Prod-Deploy; Branch feat/priv-<slug> von origin/develop in eigenem Worktree.
```
