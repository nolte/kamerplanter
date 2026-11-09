# SPEC-03 — Lebenszyklus von Konto und Mitgliedschaft

```
Paket: spec/privacy · Version 1.0 · 2026-11-09 · gemessen gegen develop 24d1c2988
Anforderungs-IDs: PRIV-100 … PRIV-139
Abhängig von: 01 (Vokabular, Komponenten), 04 (Bedeutung von Marker/Tombstone), 06 (Fristen)
```

Dieses Dokument spezifiziert den vollständigen Lebenszyklus der Beziehung einer betroffenen Person zur
Plattform und zu jedem Mandanten: Kontolöschung, Beendigung der Mitgliedschaft, Mandantenlöschung,
Wiedereintritt, Löschanfragen während des Offline-Betriebs, Löschung von Nutzern mit gesetzlich
aufzubewahrenden Datensätzen und Wiederaufnahme der Verarbeitung nach Teilausfall. Für jeden betroffenen
Datensatz wird das erwartete Verhalten angegeben. Verifizierte Fakten sind mit **[verifiziert]**
markiert, neues Verhalten mit **[Vorschlag]**.

---

## 1. Zustände

### 1.1 Konto

| Zustand | Definition [verifiziert, sofern nicht anders markiert] | Beobachtbar |
|---------|---------------------------------------------------------|-------------|
| `active` | `users.is_active = true`, keine `erasure_requests`-Zeile in `scheduled`/`in_progress` | Login funktioniert |
| `closed` | `request_erasure` wurde ausgeführt: `is_active=false`, `password_hash=None`, alle Refresh-Tokens widerrufen, Einladungen des persönlichen Mandanten widerrufen, Organisationen abgewickelt (INV-1), Mitglieder persönlicher Mandanten benachrichtigt; `erasure_requests.status = scheduled`, `hard_delete_scheduled_at = now + R-01` | kein Login; **[Vorschlag]** Anzeigename für andere Mitglieder nicht mehr auflösbar (PRIV-104) |
| `erasing` | `claim_for_run` erfolgreich (`status = in_progress`, 6 h Stale-Fenster) | — |
| `partially_completed` | ein Versuch ist fehlgeschlagen oder hat Schritte unerreicht gelassen; `attempt_count`, `next_attempt_at` (Backoff `min(2^(n-1), 7)` Tage), Eskalationslog bei Versuch 5 | Admin sieht es unter `GET /admin/platform/erasures/{key}` |
| `erased` | `users`-Zeile entfernt; `erasure_requests.user_key` ist der Tombstone; `status = completed` | nichts wird aufgelöst; Zeilen tragen Marker/Tombstone |
| `purged` | `erasure_requests`-Zeile durch R-06 gelöscht (3 Jahre, nur wenn `user_key` ein Tombstone ist) | — |

Es gibt **keinen Abbruch** einer Kontolöschungsanfrage **[verifiziert]** (Docstring in `privacy_service.py`:
„there is no cancel route, the password hash is dropped with the request"). Dieses Paket behält diese
Entscheidung bei; ihre Folge für Offline-Geräte siehe §7.3.

### 1.2 Mitgliedschaft (pro Mandant)

| Zustand | Definition | Datensatz |
|---------|------------|-----------|
| `invited` | `invitations`-Zeile (an E-Mail gebunden oder Link) | Einladung |
| `member` | `memberships`-Zeile, `is_active = true`, `role`, `admin_scopes`, `joined_at` | Mitgliedschaft |
| `former` | **keine Zeile** — `leave_tenant` / `remove_member` / `admin_remove_membership` löschen die Mitgliedschaft samt Kanten und `location_assignments` hart **[verifiziert]** (`membership_repository.py:130-142`); nur `security_audit_log` (`MEMBERSHIP_LEFT` / `MEMBERSHIP_REMOVED`, mit `old_role`, `old_scopes`, 730 Tage) hält fest, dass die Person Mitglied war | abgeleitet: „Konto-Key in Mandantenzeilen vorhanden, keine aktive Mitgliedschaft" |
| `deactivated` | `is_active = false` — wird nur bei Mandantenlöschung/-import verwendet (`deactivate_all_for_tenant`) | Mitgliedschaft |

**[verifiziert]** Das Modell kennt weder `status`, `left_at` noch eine Mitgliedschaftshistorie
(`domain/models/membership.py`). **[Vorschlag, DEC-05]** Dieses Paket fügt **keine** hinzu:
der Zustand „ehemaliges Mitglied" wird zur Lesezeit abgeleitet (§3), und das Security-Audit bleibt der
Nachweis, wer wann Mitglied war. Begründung: eine Collection `former_members` wäre ein neuer
Speicher personenbezogener Daten mit eigener Aufbewahrung; der abgeleitete Zustand braucht keine.

### 1.3 Mandant

**[verifiziert]** `TenantStatus ∈ {active, suspended, pending_deletion, orphaned, deleted, importing}`
(`common/enums.py`); nur `active` löst einen Slug auf (`_membership_for_slug`, dasselbe 403 für
unbekannt / inaktiv / keine Mitgliedschaft). Löschung: `delete_tenant` (lead **und** `management`,
Step-up) → `pending_deletion` für `RETENTION_TENANT_ERASURE_GRACE_DAYS` (Standard 90, Obergrenze
90, 0 erlaubt) → `resume_tenant_erasures` (04:30 UTC) führt das Mandanteninventar aus → `deleted`.
`cancel_tenant_erasure` existiert. `TenantType ∈ {personal, organization}` ausschließlich — im Code gibt es
keinen Typ `community` oder `commercial`.

---

## 2. Kontolöschung

### 2.1 Anfrage (wie implementiert, unverändert)

**PRIV-100** Der Anfragepfad MUSS wie implementiert bleiben [verifiziert]: Step-up
(`StepUpVerifier`: wiederholte E-Mail, aktuelles Passwort oder per E-Mail gesendeter Code; API-Keys und Service-Accounts
abgelehnt; Sperre 429 `STEP_UP_LOCKED`), idempotenter Datensatzschlüssel
`compute_request_key` (`erq_` + HMAC), `find_active_for_user` verweigert eine zweite Anfrage,
sofortige Schließung, Abwicklung von Organisationen, Mitgliederbenachrichtigung. `DELETE /users/me` eröffnet dieselbe
Anfrage (REQ-023 §3.9).

### 2.2 Verhalten während der Karenzzeit (neu)

**PRIV-101** [Vorschlag] Solange das Konto `closed` ist, MÜSSEN die Daten der Person als
*eingeschränkt* behandelt werden (Art. 18 analog): keine Benachrichtigung wird an sie gesendet, keine Erinnerung nennt sie,
keine Aufgabe wird ihr zugewiesen. [verifizierte Lücke] Heute ändern sich nur `is_active` und `password_hash`;
`DOCUMENT(users/…)`-Joins lösen den Anzeigenamen noch bis zu 90 Tage lang auf.

**PRIV-102** [Vorschlag] Die betroffene Person MUSS den Status der Anfrage einsehen können
(`GET /privacy/erasure/{key}` existiert) **ohne sich anzumelden**? — Nein: das Konto ist geschlossen, daher ist
die Statusseite nur über das E-Mail-Link-Muster des E-Mail-Änderungs-Flows erreichbar.
Dieses Paket fügt **keinen** unauthentifizierten Status-Endpunkt hinzu (Risiko der Informationspreisgabe); die
Bestätigungs-E-Mail nennt bereits das geplante Datum. *Entscheidung als DEC-19 festgehalten.*

**PRIV-103** Das Datum der endgültigen Löschung DARF durch nichts verschoben werden außer durch die Wartezeit der
Mitgliederbenachrichtigung (`RETENTION_ERASURE_MEMBER_NOTICE_DAYS`, 7), die bereits in REQ-025 §3.1.3 spezifiziert ist.

**PRIV-104** [Vorschlag] Ab dem Moment der Schließung MUSS `IdentityReferenceRegistry.resolve_display`
für den Key der betroffenen Person den Zustand `erased` an jeden Betrachter zurückgeben, außer an Plattform-Admins
(die den Namen für die Löschvorschau und den Support benötigen). Umsetzung: der Resolver liest
`users.is_active` zusammen mit dem Anzeigenamen (ein zusätzliches Feld im bestehenden Join); ein
geschlossenes Konto wird wie ein fehlendes dargestellt. Abnahme: TA-101.

### 2.3 Endgültige Löschung (wie implementiert) und ihr Ergebnis je Datensatzklasse

**PRIV-105** Die Plan-Reihenfolge MUSS bleiben: Objektspeicher (Phase 0) → pgvector (0.5) → Kanten →
Dokumente → `ANONYMIZE_COLLECTIONS` → `PSEUDONYMIZE_AUDIT_COLLECTIONS` (2.5) → `users`;
persönliche Mandanten werden **vor** dem Plan über das Mandanteninventar gelöscht; der ArangoDB-Teil
ist eine Transaktion (`erasure_executor.py`). [verifiziert]

Erwarteter Zustand jeder Datensatzklasse nach einer abgeschlossenen Löschung (die Tabelle ist der normative
Vertrag; `02` listet jedes Feld):

| Datensatzklasse | Heute [verifiziert] | Erforderlich [dieses Paket] | Spec |
|-----------------|---------------------|-----------------------------|------|
| Sitzungen, Tokens, API-Keys, Präferenzen, Onboarding, Einschränkungen, Exporte, E-Mail-Änderung, Auth-Provider | gelöscht | unverändert | — |
| Benachrichtigungen, Benachrichtigungspräferenzen, Kalender-Feeds, KI-Konversationen, Identifikations-/Diagnoseanfragen, Schädlingserkennungen, eigene Schädlingsbeiträge | gelöscht | unverändert | — |
| Mitgliedschaften, Standortzuweisungen, angenommene Einladungen | gelöscht | unverändert | — |
| persönliche(r) Mandant(en) im Besitz der betroffenen Person | gelöscht mit allem darin (auch Zeilen anderer Mitglieder, die zum Anfragezeitpunkt benachrichtigt wurden; Ausnahme `retained_late_joiner`) | unverändert | REQ-025 Q-E1/Q-E5 |
| Zeilen in geteilten Mandanten, die die betroffene Person verfasst/ausgeführt hat (Pflegeereignisse, Tagebuch, Aufgabenkommentare, Gartenobjekte, Beetvorlagen, Anhänge, manuelle Überschreibungen, Importjobs, Wetterkonfigurationen, verworfene Tipps, versendete Einladungen) | Konto-Referenzen → `_anonymized`; **sämtlicher Freitext bleibt erhalten**; Fotos bleiben erhalten (EXIF erneut entfernt) | Konto-Referenzen → Marker **und** ein `privacy_review_items`-Eintrag je Zeile mit prüfbarem Freitext (`04` §5); `attachments.original_filename` geleert (PRIV-211) | `04` |
| `tasks.assigned_to_user_key` | Marker | Marker (unverändert; eine Aufgabe, die niemandem zugewiesen ist) | — |
| `sites.plan.plan_updated_by` | Marker | Marker | — |
| gesetzlich aufzubewahrende Zeilen (`harvest_batches`, `quality_assessments`, `treatment_applications`, `inspections`) | Key → Tombstone, typisierter Anzeigename geleert; `notes` bleiben | unverändert **vorbehaltlich LEG-03/LEG-04**: hat der Mandant keine Aufbewahrungspflicht, MÜSSEN diese Zeilen stattdessen als `shared_history` behandelt werden (Marker, Prüfung) | `06` §3 |
| `garden_plan_audit.user_key` | Tombstone | **Marker** (DEC-16): das Plan-Audit ist mandantenintern, nicht gesetzlich; Verknüpfbarkeit wird nicht benötigt; Freitext in `summary`/`snapshot` → Prüfeinträge | `04` §4.3 |
| `security_audit_log.actor/target`, `erasure_requests.user_key`, `consent_records.user_key`, `mcp_audit_log.service_account_key` | Tombstone | unverändert | `06` |
| `ai_audit_log.user_key` | Marker | unverändert | — |
| `tenants.owner_user_key` einer fortbestehenden Organisation | Marker (REQ-056 §9.1 Übergabe geplant, nicht implementiert) | unverändert, bis REQ-056 umgesetzt ist | — |
| `care_events`-Zeilen, deren `performed_by_user_key` den **Tombstone** der betroffenen Person enthält (kopiert durch v0104/Konsistenzjob) | unberührt — die Regel trifft nur den echten Key | erfasst: `04` §3.3 verbietet hier Tombstones; Migration `09` §3 korrigiert Altkopien | #2770 |
| Gerätespeicher auf den Geräten der betroffenen Person | dieses Gerät geleert (`AccountSettingsPage` → `clearOfflineData({discardWriteQueueOf})`); andere Geräte behalten die Schreibwarteschlange 90/365 Tage | Quarantäne toter Sitzungen `07` §7 | `07` |

**PRIV-106** [Vorschlag] Der Löschbericht (`erasure_requests`-Collection, Listen und Zähler)
MUSS zusätzlich `review_items_created` pro Mandant und `tombstone_copies_corrected` erfassen,
damit der Betreiber sehen kann, dass die neuen Phasen gelaufen sind. Kein Zeileninhalt, keine Mandantennamen.

### 2.4 Teilausfall und Wiederaufnahme

**PRIV-107** Die Claim-/Retry-Mechanik MUSS bleiben [verifiziert]: `claim_for_run` mit 6 h Stale-
Fenster, Checkpoint `pre_arango_completed_at` (Speicherphasen werden nicht wiederholt), transaktionaler
ArangoDB-Plan (alles oder nichts), `partially_completed` mit Backoff, Konfigurationsfehler halten
an, ohne einen Versuch zu verbrauchen, ein tombstonierter `user_key` bedeutet „committed".

**PRIV-108** [Vorschlag] Die beiden neuen Phasen (Prüfeinträge, Replay-Ledger) MÜSSEN **nach** dem
Commit der ArangoDB-Transaktion laufen und auf ihren eigenen Keys idempotent sein
(`privacy_review_items._key = hash(erasure_key, collection, row_key, field)`;
Ledger-Key = `erasure_key`). Ein Fehler in diesen Phasen DARF die Löschung NICHT zurückrollen (das
Recht ist erfüllt; die Folgeschritte werden vom nächsten Beat als `post_commit_pending` erneut versucht).

**PRIV-109** [Vorschlag] Eskalationsschwellen MÜSSEN für Konto- und Mandantenlöschung identisch sein.
Heute eskaliert die Kontolöschung bei Versuch 5 (`ERASURE_ESCALATE_AFTER_ATTEMPTS`), die Mandantenlöschung
bei 3 (`TenantErasureEngine.ESCALATE_AFTER_ATTEMPTS`). Empfehlung: 3 für beide,
eine Einstellung `PRIVACY_OPERATION_ESCALATE_AFTER_ATTEMPTS`. Abnahme: TA-108.

**PRIV-110** [Vorschlag] Eine Löschung, die länger als
`PRIVACY_OPERATION_STALE_ALERT_DAYS` (Standard 14) in `partially_completed` verbleibt, MUSS als Metrik
(`privacy_operations_open{kind,status}`) und in `GET /admin/platform/privacy/operations`
(`08` §5) sichtbar sein. Heute ist das einzige Signal das Logfeld `open_failing`.

---

## 3. Beendigung der Mitgliedschaft

### 3.1 Was heute geschieht [verifiziert]

`leave_tenant`, `remove_member`, `admin_remove_membership`, Entfernen von Service-Accounts:
INV-1-Schutz (das letzte `management` kann nicht austreten), Step-up für das Entfernen, Mitgliedschaftszeile gelöscht
samt Kanten und `location_assignments`, `security_audit_log`-Zeile, `_end_membership` leert
`tasks.assigned_to_user_key` in diesem Mandanten und löscht die Kalender-Feeds des Mitglieds dort.
**Sonst ändert sich nichts**: jede `performed_by`/`created_by`/`actor`-Referenz des ehemaligen
Mitglieds bleibt, sein Anzeigename wird weiterhin für alle Mitglieder aufgelöst, der Pflegelog-Filter nach
dieser Person funktioniert weiterhin für Leads, ihre Zeilen bleiben mit ihrem Namen in CSV-Exporten.

### 3.2 Erforderliches Verhalten

**PRIV-111** Die Beendigung der Mitgliedschaft DARF KEINE Domänenzeile löschen, markieren oder pseudonymisieren.
Begründung: die Zeilen sind die Historie des Mandanten (Art. 6(1)(f) des Mandanten und seiner Mitglieder);
die Person existiert weiterhin und kann Art. 15 über sie ausüben (das Art.-15-Manifest liest
mandantenbezogene Quellen nur in aktuellen Mandanten — REQ-025 §3.1.2 Regel 4 —, sodass die
Zeilen eines früheren Mandanten aus dem eigenen Export der Person herausfallen; **[rechtlich] LEG-06(b)**, ob das akzeptabel ist).

**PRIV-112** [Vorschlag, DEC-05] Nach `RETENTION_FORMER_MEMBER_NAME_DAYS` (Standard **90**,
Untergrenze 0, Obergrenze 365; **[rechtlich] LEG-06(a)**) ab Ende der Mitgliedschaft DARF der Anzeigename
des ehemaligen Mitglieds für andere Mitglieder dieses Mandanten NICHT aufgelöst werden: `resolve_display` gibt
den Zustand `former_member` mit `display_name = null` zurück. Bevor die Frist abläuft, wird der Name
angezeigt, damit Übergaben („wer hat Beet 3 zuletzt gegossen?") weiter funktionieren. Der Zeitpunkt des
Mitgliedschaftsendes wird aus `security_audit_log` (`MEMBERSHIP_LEFT`/`REMOVED`, `created_at`) gelesen; existiert
keine Audit-Zeile (Austritte vor #2111), wird der Key sofort als unterdrückt behandelt.

**PRIV-113** [Vorschlag] Leads und `management` KÖNNEN den Namen eines ehemaligen Mitglieds weiterhin für
denselben Zeitraum **plus** die für Rechenschaftsfragen nötige Zeit auflösen? — Nein: die Unterdrückung
gilt für jede Rolle im Mandanten; der Plattform-Admin sieht das Konto (falls vorhanden) in
`/admin/platform/users`. Begründung: das Rechenschaftsinteresse des Mandanten ist zeitlich begrenzt; der
Name steht weiterhin im Security-Audit (730 Tage) für echte Streitfälle, nur vom
Plattform-Admin lesbar.

**PRIV-114** [Vorschlag] Der Pflegelog-Filter `performed_by` und der CSV-Export MÜSSEN ein unterdrücktes
ehemaliges Mitglied wie ein gelöschtes behandeln: der Filterwert wird mit 422 abgelehnt
(`care_event.filter_target_unavailable`), die CSV zeigt die Darstellung `former_member`.

**PRIV-115** [Vorschlag] Dem austretenden Mitglied MUSS im Austrittsdialog und in der
Entfernungsmitteilung mitgeteilt werden, dass seine Beiträge in der Historie des Mandanten verbleiben, dass sein Name
Mitgliedern noch N weitere Tage angezeigt wird und wie es die Löschung beantragt (Link zur Art.-17-Selbstbedienung)
— die Informationspflicht nach Art. 13(2)(a)/(b).

**PRIV-116** [Vorschlag, KANN] Ein aus einem Mandanten austretendes Mitglied KANN die *Entfernung der Zurechnung* in
diesem Mandanten beantragen (Art. 21 Widerspruch, Art. 17(1)(c)): seine Konto-Referenzen in diesem Mandanten werden
sofort auf den Marker gesetzt, und für die Leads des Mandanten werden Prüfeinträge angelegt. Dies ist eine
mandantenbezogene Teilmenge des Löschplans (`ANONYMIZE_COLLECTIONS`, gefiltert nach `tenant_key`),
kein neuer Regelsatz. Gesetzlich aufzubewahrende Zeilen sind ausgenommen, wo LEG-03 greift. Priorität P2.

### 3.3 Wiedereintritt

**PRIV-117** [verifiziert] Beim Wiedereintritt wird eine neue `memberships`-Zeile mit neuem `joined_at` angelegt; die
alten Zeilen der Person bleiben unberührt und werden wieder aufgelöst, weil der Key derselbe ist.

**PRIV-118** [Vorschlag] Beim Wiedereintritt endet die Unterdrückung (PRIV-112) für diesen Mandanten automatisch
(der abgeleitete Zustand wird wieder `member`). Hat die Person PRIV-116 genutzt, bleiben die Marker —
ein Marker ist von Entwurf an unumkehrbar (die Zuordnung ist weg). Der Wiedereintrittsdialog MUSS darauf hinweisen.

---

## 4. Zurechnung beim Schreiben (wer wird gespeichert)

### 4.1 Regel

**PRIV-119** Jeder Schreibpfad MUSS Konto-Referenzen aus dem **authentifizierten
Principal** der Anfrage setzen, niemals aus dem Body (REQ-053 GP-NFR-054 [verifiziert für Pflege-
ereignisse]). Der Principal eines MCP-Tool-Aufrufs ist der Service-Account (`ctx.principal`); bei einem
Abschluss über die Aufgabenwarteschlange der Nutzer des Tokens (`CompletionActor.user_key`); bei einer Benachrichtigungs-
aktion der handelnde Nutzer; bei einem Celery-Job **niemand** (`null`).

### 4.2 Verifizierte Abweichungen und erforderliche Korrekturen

| Pfad | Heute | Erforderlich | Issue |
|------|-------|--------------|-------|
| REST `POST /plants/{key}/confirm`, Benachrichtigungsaktion | Aufrufer gespeichert | unverändert | — |
| Abschluss über Aufgabenwarteschlange → `record_care_task_completion` | `performed_by_user_key = null` (`_bed_event_for` ohne `user_key` aufgerufen) | Aufrufer (`ctx.user_key` verfügbar in `tasks/tenant_router.py`) | #2770 Punkt 2 |
| MCP `ConfirmCareTask` | `null` | Service-Account-Key (`account_type: service`), dargestellt als `service_account` | #2770 Punkt 2 |
| Live-Erinnerungs-/Bestätigungszeilen via `map_document` | `created_by = None` → `created_by_me` false, Autor kann nicht korrigieren | `created_by = performed_by_user_key` auf **Live**-Pfaden; Backfill und Konsistenzjob behalten `null` (Systemherkunft) | #2770 Punkt 3 |
| Backfill/Konsistenz `account_of` | kopiert jeden nicht leeren String inkl. Tombstones | kopiert nur einen Wert, der ein aktueller `users._key` ist, *oder* schreibt `_anonymized` für einen Tombstone/Marker; niemals ein Label | #2770 Punkt 1, `04` §3.3 |

### 4.3 `confirmed_by`

**PRIV-120** `CareConfirmation` hat kein Akteur-Feld [verifiziert]. Dieses Paket fügt
keines hinzu: das Pflegeereignis der Bestätigung trägt `performed_by_user_key` (den Principal) und ist die
einzige Zurechnung; eine zweite Kopie auf der Bestätigung würde eine Abstammung erzeugen, die synchron gehalten werden müsste. Die
Registry hält fest: `care_confirmations: attribution = none, derived_event =
care_events(source_ref)`.

---

## 5. Löschung von Nutzern mit gesetzlich aufzubewahrenden Datensätzen

**PRIV-121** [verifiziert] Gesetzlich aufzubewahrende Zeilen überleben Konto und Mandant: Key → Tombstone,
typisierter Anzeigename (`harvester`, `applied_by`, `inspector`, `assessed_by`) geleert;
`purge_expired_legal_retention_rows` löscht sie erst, wenn der Mandant nicht mehr existiert und
die Frist (R-16 5 J. ab `harvest_date`, R-17/R-18 3 J.) abgelaufen ist; der Art.-15-Export
findet sie für eine noch aktive Person über den Tombstone.

**PRIV-122** [Vorschlag, DEC-11; **rechtlich LEG-03**] Ein Mandant MUSS angeben, ob eine gesetzliche
Aufbewahrungspflicht gilt: `Tenant.settings.record_keeping ∈ {legacy, none, pflschg_professional,
kcang_association, both}`. Standard für bestehende Mandanten: `legacy` = heutiges Verhalten (alle
gesetzlichen Regeln gelten). Bei `none` werden die vier Collections als `shared_history` behandelt
(Marker bei Löschung, mit dem Mandanten gelöscht, Prüfeinträge). Begründung: PflSchG §11 bindet
*berufliche* Anwender und die Dokumentationspflichten des KCanG binden Anbauvereinigungen; ein
Hobbygarten hat keine Grundlage nach Art. 6(1)(c), einen pseudonymisierten Ernteeintrag fünf Jahre lang
aufzubewahren, nachdem die Person die Löschung beantragt hat. Der Betreiber bestätigt den Wert; die UI erläutert die
Konsequenz.

**PRIV-123** [**rechtlich LEG-04**] Ob der *Name* des Anwenders in einem
PflSchG-§11-Nachweis für den gesamten Zeitraum lesbar bleiben muss (heute wird er bei der Löschung geleert und nur das
Pseudonym bleibt), ist ungeklärt. Falls die Rechtsberatung Ja sagt, lautet der alternative Entwurf: den
Anzeigenamen in einem versiegelten Feld `applied_by_sealed` halten, das nur für `management`+`lead`
mit Step-up lesbar ist und zum gesetzlichen Ende geleert wird. Keine Codeänderung bis zur Entscheidung.

**PRIV-124** `pest_control`-/`ipm`-Pflegeereignisse MÜSSEN dem Pflegelog folgen, nicht dem gesetzlichen
Nachweis: bei Mandantenlöschung werden sie gelöscht [verifizierter Kommentar in
`tenant_erasure_engine.py`], bei Kontolöschung tragen sie den Marker, bei R-25 warten sie auf
den PflSchG-Stichtag (`care_event_pflschg_cutoff = max(R-25, R-17)`) [verifiziert]. Die
`treatment_applications`-Zeile ist der einzige §11-Nachweis (REQ-053 §13.2, E-16). **[rechtlich] LEG-07**
bestätigt diese Lesart.

---

## 6. Mandantenlöschung

**PRIV-125** [verifiziert, unverändert] `pending_deletion` für die Karenzzeit, Mitglieder benachrichtigt
mit einem Art.-20-Exportfenster, abbrechbar, danach: das Mandanteninventar löscht jede mandantenbezogene
Collection (Pflegeereignisse inkl. `pest_control`, Tagebuch, Aufgaben, Anhänge, Mitgliedschaften
zuerst deaktiviert, dann gelöscht, `client_event_tombstones`), gesetzlich aufzubewahrende Zeilen pseudonymisiert,
`security_audit_log` bleibt, TimescaleDB-Messwerte gelöscht, `tenant_erasure_records` bleiben bis zur
am längsten aufzubewahrenden gesetzlichen Zeile oder 5 Jahre (R-06a).

**PRIV-126** [Vorschlag] Die neuen Collections `privacy_review_items` und (falls separat)
`redaction_log` MÜSSEN in `TenantErasureEngine.INVENTORY` als `_delete` stehen. Das Replay-Ledger
ist plattformweit (`NOT_TENANT_SCOPED` mit Begründung).

**PRIV-127** [Vorschlag] Verwaiste Mandanten (`orphaned`, REQ-024 AK-65) MÜSSEN in die
Überwachung der Datenschutzvorgänge (PRIV-110) einbezogen werden, weil ihr Karenzzeit-Timer läuft, ohne dass ein Mitglied
handeln könnte.

**PRIV-128** [verifizierte Lücke, **rechtlich LEG-13**] Das Mandanten-Exportarchiv (REQ-056 §8,
`members.jsonl` mit `user_key`, `display_name`, Rolle, Scopes; Standort-GPS) verlässt die
Installation. Dieses Paket hält die Frage fest; hier wird keine Änderung vorgeschlagen.

---

## 7. Löschung und Offline-Betrieb

**PRIV-129** [verifiziert] Auf dem Gerät, auf dem die Löschung beantragt wird, leert
`AccountSettingsPage` den Lese-Cache und die Schreibwarteschlange der betroffenen Person vor der Weiterleitung.

**PRIV-130** [Vorschlag] Auf jedem anderen Gerät der betroffenen Person schlägt der nächste Refresh fehl (Tokens
widerrufen). Der Client MUSS einen abgelehnten Refresh (401/403) als **tote Sitzung** behandeln und
die Schreibwarteschlange des gespeicherten Nutzers in Quarantäne setzen (`07` §7): Einträge werden `quarantined`, nie
wiedergegeben und nach `OFFLINE_DEAD_SESSION_GRACE_DAYS` (Standard 14) gelöscht, sofern sich nicht
derselbe `user_key` auf diesem Gerät erneut anmeldet. Ein geschlossenes Konto kann sich nicht anmelden, daher
endet die Quarantäne in einer Löschung.

**PRIV-131** [Vorschlag] Der Server MUSS einen Replay von einem gelöschten oder geschlossenen Konto mit
`401` und einem stabilen `error_code` beantworten, auf den der Client reagieren kann. Da das Nutzerdokument nach der
endgültigen Löschung weg ist, kann der Server „gelöscht" nicht von „unbekannt" unterscheiden — daher wird das Signal
während der **closed**-Phase ausgegeben: Refresh und jeder `/t/{slug}/…`-Schreibzugriff von einem geschlossenen
Konto beantworten `401 account.closed`. Der Client leert die Warteschlange bei diesem Code sofort.
Nach der endgültigen Löschung greift das generische 401 auf die Quarantäne aus PRIV-130 zurück.

**PRIV-132** Ein gepufferter Schreibvorgang DARF nach Schließung des Kontos NICHT akzeptiert werden: der Schreib-
pfad verlangt bereits eine aktive Mitgliedschaft und `users.is_active` [verifiziert über
`_membership_for_slug`]; TA-131 sichert das für die `client_event_id`-Pfade ab
(`POST /care-events`, `/tasks/{key}/complete`, Foto-Uploads).

**PRIV-133** [verifiziert] `client_event_tombstones` (IDs gelöschter gepufferter Schreibvorgänge, zufällige
UUIDs, TTL 395 Tage) enthalten keine personenbezogenen Daten; sie werden mit dem Mandanten gelöscht.

---

## 8. Service-Accounts

**PRIV-134** [verifiziert] Service-Accounts (`account_type: service`) können keine Löschung beantragen
(Step-up lehnt API-Keys/Service-Accounts ab). Ihre Entfernung ist eine Entfernung der Mitgliedschaft plus Widerruf
des Keys. **[Vorschlag]** Mit dem Key eines Service-Accounts gestempelte Zeilen werden als
`service_account` mit dem Label des Accounts dargestellt (keine Person); bei Entfernung des Service-Accounts
wird das Label wie bei einem ehemaligen Mitglied unterdrückt (PRIV-112).

---

## 9. Abnahmekriterien (Zusammenfassung; Details in `10`)

| ID | Kriterium |
|----|-----------|
| TA-100 | Nach `request_erasure` zeigt jede API-Antwort, die den Namen der betroffenen Person zeigen würde, den Zustand `erased`; die Löschvorschau für einen Plattform-Admin zeigt ihn weiterhin. |
| TA-101 | PRIV-104: der Anzeige-Join liest `is_active`; ein geschlossenes Konto wird wie ein fehlendes dargestellt. |
| TA-102 | Eine abgeschlossene Löschung hinterlässt keine Zeile in einer geteilten Collection, deren kontoförmiges Feld dem echten Key **oder** dem Tombstone entspricht (außer den auf der Allowlist stehenden gesetzlichen/Audit-Collections). |
| TA-103 | Jede prüfbare Freitext-Zeile der betroffenen Person in einem geteilten Mandanten hat genau einen `privacy_review_items`-Eintrag; ein zweiter Löschlauf legt keinen an. |
| TA-104 | Eine `partially_completed`-Löschung wird von `GET /admin/platform/privacy/operations` aufgelistet und von `privacy_operations_open` gezählt. |
| TA-105 | Konto- und Mandantenlöschung eskalieren bei derselben Versuchszahl. |
| TA-110 | Der Austritt aus einem Mandanten ändert keine Domänenzeile; Aufgabenzuständiger und Kalender-Feeds werden geleert (unverändertes Verhalten abgesichert). |
| TA-111 | N Tage nach dem Austritt gibt `resolve_display` für jede Mitgliedsrolle `former_member` ohne Namen zurück; ein Plattform-Admin sieht das Konto weiterhin. |
| TA-112 | Der Wiedereintritt stellt die Darstellung `member` wieder her; durch PRIV-116 gesetzte Marker bleiben. |
| TA-113 | Filtern des Pflegelogs nach einem unterdrückten ehemaligen Mitglied → 422; die CSV zeigt die Darstellung für ehemalige Mitglieder. |
| TA-120 | Alle vier Bestätigungspfade speichern den Principal als `performed_by_user_key` und `created_by`. |
| TA-121 | `account_of` gibt niemals einen Tombstone oder ein Label zurück; eine Tombstone-Quelle ergibt `_anonymized`. |
| TA-122 | Ein Mandant mit `record_keeping = none` behandelt die vier gesetzlichen Collections bei Löschung als geteilte Historie. |
| TA-130 | Ein abgelehnter Refresh setzt die Warteschlange in Quarantäne; `401 account.closed` leert sie sofort. |
| TA-131 | Ein nach Kontoschließung wiedergegebener gepufferter Schreibvorgang wird auf jedem `client_event_id`-Pfad abgelehnt. |
