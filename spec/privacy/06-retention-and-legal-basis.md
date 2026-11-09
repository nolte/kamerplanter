# SPEC-06 — Matrix zu Aufbewahrung und Rechtsgrundlagen

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · gemessen gegen develop 24d1c2988
Requirement IDs: PRIV-400 … PRIV-449
Depends on: NFR-011 (Aufbewahrungsregeln R-nn), REQ-025 §3, 02 (Inventar), 03/04 (Verhalten)
```

Jede unten genannte Rechtsgrundlage ist ein **Vorschlag**, sofern sie nicht mit [verifiziert in Spec] markiert ist
(d. h. NFR-011 oder REQ-025 nennt sie bereits). Alles, was mit **LEG-nn** gekennzeichnet ist, braucht die Freigabe
durch Rechtsberatung / DSB, bevor es als entschieden gilt. Art. 17(3) wird nur als **Ausnahme von der
Löschung** verwendet, nie als Grundlage für die Verarbeitung.

---

## 1. Rollen der Verantwortlichen — die Frage, die zuerst kommt

**LEG-01** Wer ist Verantwortlicher für die Mitgliederdaten eines Gemeinschaftsgartens oder eines
Gewerbebetriebs, der Kamerplanter nutzt?

| Option | Folge für dieses Paket |
|--------|------------------------|
| (a) Die **Mandantenorganisation** ist Verantwortlicher, der Plattformbetreiber ist **Auftragsverarbeiter** (Art. 28) | Die Information nach Art. 13/14, die Interessenabwägungen aus §4, die DSFA und die RoPA-Einträge gehören dem Mandanten; der Betreiber stellt die technischen Mittel (Sichtbarkeitseinstellung, Prüfwarteschlange, Export) und einen AVV bereit; die eigene Verantwortlichkeit des Betreibers umfasst Konten, Plattform-Mandant, Sicherheits-Audit, Logs |
| (b) Betreiber und Mandant sind **gemeinsam Verantwortliche** (Art. 26) | Eine Vereinbarung ist erforderlich; der Betreiber trägt die Interessenabwägungen |
| (c) Der Betreiber ist alleiniger Verantwortlicher | Jede Regel unten ist die des Betreibers; die Leads des Mandanten handeln im Auftrag des Betreibers |

Das Paket ist für **(a)** geschrieben (das übliche SaaS-Verständnis) und kennzeichnet jede Stelle, an der die
Wahl eine Rolle spielt, mit „(controller: tenant)". Die Specs behandeln die Frage heute nirgends
(REQ-025 §8 verlegt das RoPA „außerhalb der Software"; `data_controller` im Export-Bundle ist
ein konfigurierter String). Bei einer **selbst betriebenen** Installation fällt (a) zusammen: der Betreiber *ist*
der Mandant.

---

## 2. Aufbewahrungsmatrix — Kategorien personenbezogener Daten

Spalten: Zweck · Rechtsgrundlage · Aufbewahrungsauslöser · Frist · Löschverhalten · Gesetzliche
Aufbewahrungsausnahme · Verantwortliche Rolle (Lesart Verantwortlicher (a)). „Setting" nennt die
Umgebungsvariable / den Eintrag in `RETENTION_CEILINGS` [verifiziert im Code, sofern nicht anders vermerkt].

### 2.1 Konto- und Sitzungsdaten (controller: operator)

| # | Category | Purpose | Basis | Trigger | Period | Deletion | Exception | Responsible | Status |
|---|----------|---------|-------|---------|--------|----------|-----------|-------------|--------|
| R-01 | soft-deleted account | Art. 17 bedienen, mit Sicherheitsfenster gegen irrtümliche Anträge | Art. 6(1)(c)+(b) | Löschantrag | 90 d (`RETENTION_SOFT_DELETE_RETENTION_DAYS`, Obergrenze 90) | Hard-Delete-Plan | — | Betreiber | implementiert [v] |
| R-02 | unverified accounts | Hygiene | 6(1)(f) | Registrierung | 7 d | Löschen (Dry-Run bis `RETENTION_UNVERIFIED_LOCAL_REAP_ENABLED`) | — | Betreiber | implementiert [v] |
| R-03 | IP in refresh tokens | Sitzungssicherheit | 6(1)(f) [v in Spec] | Token-Ausstellung | 7 d | anonymisieren (IPv4 /24, IPv6 /48) | — | Betreiber | implementiert [v] |
| R-08…R-11 | token hashes, OAuth state, refresh tokens | Authentifizierung | 6(1)(b) | Ausstellung | 1 h / 24 h / 5 min / eigener Ablauf | Löschen | — | Betreiber | implementiert |
| — | `last_login_at`, `failed_login_attempts`, `locked_until` | Kontosicherheit | 6(1)(f) | jeder Login | Lebensdauer des Kontos | mit dem Konto | — | Betreiber | implementiert; **keine Frist für `last_login_at`** → nur Überschreiben vorschlagen (ist so) |
| R-04 / R-04a | consent records + IP | Einwilligung nachweisen (Art. 7(1)) | 6(1)(c) [v in Spec] | Widerruf | 3 J. nach Widerruf / IP 7 d | Löschen; Tombstone bei Löschung | — | Betreiber | implementiert [v] |
| R-06 | `erasure_requests` | Löschung nachweisen (Art. 5(2)) | 6(1)(c) | Abschluss | 3 J. (`retention_erasure_audit_retention_years`; Docstring sagt „one year" — **Docstring korrigieren**) | Löschen nur, wenn Tombstone vorhanden | — | Betreiber | implementiert [v] |
| R-38 | `security_audit_log` | Nachweis von Zugriffsänderungen nach Art. 32 | 6(1)(c)/(f) [v in Spec] | `created_at` | 730 d fest | Löschen; Tombstone bei Löschung; bei Mandantenlöschung behalten | — | Betreiber | implementiert [v] |
| **neu R-44** | Datenschutz-Operations-Audit-Aktionen in `security_audit_log` (`04` §4.2) | Art. 5(2) | 6(1)(c) | `created_at` | 730 d (gleicher Zeilentyp) | gleich | — | Betreiber | **Vorschlag** |
| **neu R-45** | `erasure_replay_ledger` (roher `user_key` + Löschschlüssel, für Backup-Wiederherstellungen, `09` §6) | Art. 17 nach einer Wiederherstellung durchsetzen | 6(1)(c) (Art. 17 ist die Verpflichtung) | Abschluss der Löschung | `BACKUP_RETENTION_DAYS + 5` (Standard 35) | Hard Delete | — | Betreiber | **Vorschlag, LEG-11** |

### 2.2 Mitgliedschafts- und Mandantendaten

| # | Category | Purpose | Basis | Trigger | Period | Deletion | Exception | Responsible | Status |
|---|----------|---------|-------|---------|--------|----------|-----------|-------------|--------|
| — | `memberships` (Rolle, Scopes, `joined_at`) | den Mandanten betreiben | 6(1)(b) (Mitgliedschafts-/Beschäftigungsverhältnis) | Ende der Mitgliedschaft | sofort (Zeile gelöscht) | Löschen | Security-Audit behält alte Rolle 730 d | Mandant | implementiert [v] |
| **neu** | **Namensdarstellung** ehemaliger Mitglieder (abgeleitet, keine Zeile) | Übergabe, Rechenschaft | 6(1)(f) — Interessenabwägung §4.3 | Ende der Mitgliedschaft | `RETENTION_FORMER_MEMBER_NAME_DAYS` 90 (0–365) | Darstellung wechselt auf `former_member` | — | Mandant | **Vorschlag, LEG-06** |
| R-12 | invitations (`email`) | Onboarding | 6(1)(b) | Ablauf | 30 d | Löschen | — | Mandant | implementiert |
| R-01b | Mandant in `pending_deletion` | Irrtumsfenster, Exportfenster nach Art. 20 | 6(1)(b) | Antrag | 90 d (0–90) | Mandanteninventar | gesetzliche Zeilen pseudonymisiert | Mandant (lead ∧ management) | implementiert [v] |
| R-06a | `tenant_erasure_records` | Nachweis | 6(1)(c) | Abschluss | bis zur letzten gesetzlichen Zeile, ≤ 5 J. | Löschen | — | Betreiber | implementiert |
| — | **E-Mail** von Mitgliedern in `/members` | Kontakt | 6(1)(b)? Erforderlichkeit zweifelhaft | — | — | — | — | Mandant | **LEG-14**: auf `management` beschränken (PRIV-305) |

### 2.3 Domänenhistorie mit Zuordnung (controller: tenant)

| # | Category | Purpose | Basis | Trigger | Period | Deletion | Exception | Responsible | Status |
|---|----------|---------|-------|---------|--------|----------|-----------|-------------|--------|
| R-25 | `care_events` (Ausführende/r, Ersteller/in, Freitext, Fotos) | Beethistorie, Fruchtfolge, Koordination („wer hat zuletzt gegossen") | Inhalt: 6(1)(f) Fruchtfolgehistorie [v in Spec sagt „Art. 17(3) (berechtigtes Interesse: Anbauhistorie)" — umformulieren: Grundlage ist 6(1)(f), 17(3) ist keine Grundlage]; **Zuordnung**: 6(1)(f) Interessenabwägung §4.1 | `performed_at` | 5 J. (Untergrenze = Obergrenze 5, `RETENTION_CARE_EVENT_RETENTION_YEARS`) | nach 5 J.: Kontoreferenzen → Marker, Freitext → `[redacted]`, Fotos gelöscht; `pest_control`/`ipm` warten auf `max(R-25, R-17)` | 17(3)(b) nur für `pest_control`/`ipm` **und nur, wenn LEG-03 zutrifft**; sonst keine | Mandant | implementiert [v]; **Vorschlag**: Zuordnungsunterdrückung für ehemalige Mitglieder, Prüfwarteschlange bei Löschung |
| — | `watering_events`, `feeding_events`, `watering_logs`, `tank_fill_events`, `maintenance_logs` (Freitext `performed_by`, `notes`) | Betrieb | 6(1)(b)/(f) | — | **keine** [v: nur mit dem Mandanten gelöscht] | — | — | Mandant | **Lücke**: R-46 vorschlagen = an R-25 angleichen (5 J., danach `performed_by`/`notes` geschwärzt); `performed_by` auf ein Schlüsselfeld migrieren (`08` §3.4) |
| — | `plant_diary_entries` (Autor/in, Text, Fotos, KI-Analyse) | Pflanzenakte | 6(1)(b) (die eigene Dokumentation der Nutzerin / des Nutzers) / 6(1)(f) für den Mandanten | — | keine (Lebensdauer von Pflanze/Mandant) | Marker bei Löschung, Text bleibt + Prüfung | — | Mandant | implementiert [v]; Prüfung **Vorschlag** |
| — | `task_comments`, `tasks` (Zugewiesene/r, Namen, Notizen) | Koordination | 6(1)(b) | Aufgabe geschlossen | keine | Marker; Prüfung | — | Mandant | Lücke: R-47 vorschlagen — geschlossene Aufgaben/Kommentare 2 J. → Freitext schwärzen (Umfang **LEG-08**) |
| — | `garden_objects`, `bed_templates`, `locations` (Labels, Namen, Notizen, `created_by`) | Plan | 6(1)(b) | — | Lebensdauer des Plans | Marker bei Löschung; Namen geprüft | — | Mandant | implementiert [v]; Prüfung **Vorschlag** |
| R-26 | `garden_plan_audit` (Akteur, Zusammenfassung, Snapshot) | Änderungsprotokoll des Plans, Snapshot-Wiederherstellung | 6(1)(f) | `at` | 365 d | Hard Delete; Akteur → **Marker** (DEC-16; heute Tombstone) | — | Mandant | implementiert [v]; DEC-16 **Spec-Änderung** |
| — | attachments (`created_by`, `caption`, `original_filename`) | Fotos | 6(1)(b) | — | Lebensdauer des übergeordneten Objekts | Marker; `original_filename` geleert (PRIV-211); Beschriftung geprüft | geteilte Bytes bleiben (Hinweis nach Art. 19, AK-OS-09 **nicht implementiert** [v]) | Mandant | teilweise |
| — | `notifications` (Empfänger/in, Titel, Text, Daten) | Zustellung | 6(1)(b) | gelesen / erstellt | **keine** [v: keine R-Zeile, kein Beat] | nur bei Löschung gelöscht | — | Betreiber | **Lücke**: R-48 vorschlagen = 90 d nach `read_at`, 180 d ungelesen, Hard Delete |
| R-41 / R-42 | Lesecache / Schreibpuffer des Geräts | Offline-Funktion | 6(1)(b) [v in Spec, „Vorschlag"] | TTL / Erfassung | 15 min / 365 d ausstehend, 90 d nicht sendbar | auf dem Gerät gelöscht | bekannte Lücke (anderes Gerät) | Nutzer/in (eigenes Gerät) / Betreiber für Standardwerte | implementiert [v]; **Vorschlag** kürzere Standardwerte (`07`), **LEG-09/10** |

### 2.4 Gesetzliche Aufzeichnungen (controller: tenant; Anwendbarkeit je Mandant — LEG-03)

| # | Category | Purpose | Basis | Trigger | Period | Deletion | Exception | Responsible | Status |
|---|----------|---------|-------|---------|--------|----------|-----------|-------------|--------|
| R-16 | `harvest_batches`, `quality_assessments`, `yield_metrics` | Dokumentation der Anbauvereinigung (KCanG — **Paragraf nirgends zitiert**, REQ-025 L219 „CanG §X", **LEG-17**) | 6(1)(c) **nur für eine Anbauvereinigung**; sonst 6(1)(b)/(f) gewöhnliche Aufzeichnung | `harvest_date` | ≥ 5 J. (Untergrenze 5, keine Obergrenze) | Schlüssel → Tombstone, `harvester`/`assessed_by` bei Löschung geleert; gelöscht, wenn der Mandant weg ist und die Frist abgelaufen | **17(3)(b)** für die Zeile; der *Name* — LEG-04 | Mandant | implementiert [v]; **Vorschlag** Profil `record_keeping` |
| R-17 | `treatment_applications` (+ Kanten) | PflSchG-§11-Aufzeichnung für **berufliche Anwender** (Art. 67 Reg. (EG) 1107/2009: Mittel, Zeitpunkt, Dosis, Fläche, Kultur; §11(2) PflSchG ergänzt den Anwender) | 6(1)(c) für berufliche Anwender; sonst keine | `applied_at` | ≥ 3 J. | wie R-16 | 17(3)(b); **LEG-04** Lesbarkeit des Namens | Mandant | implementiert [v] |
| R-18 | `inspections` | PflSchG-§11-Überwachungsaufzeichnung | wie R-17 | `inspected_at` | ≥ 3 J. | wie R-16 | 17(3)(b) | Mandant | implementiert [v] |
| — | `care_events` mit `category ∈ {pest_control, ipm}` | Spiegel des Obigen im Pflegelog | **keine** gesetzliche Aufzeichnung (REQ-053 §13.2, E-16) | — | `max(R-25, R-17)` | Marker bei Löschung; mit dem Mandanten gelöscht | der „PflSchG-Vorbehalt" der Spec ist eine *Aufbewahrungsuntergrenze*, keine rechtliche Aufzeichnung — **LEG-07** bestätigen | Mandant | implementiert [v] |

### 2.5 Pseudonymisierte Zeilen und Audit-Zeilen (controller: operator / tenant)

| # | Category | Basis | Period | Note |
|---|----------|-------|--------|------|
| — | `mcp_audit_log` (`service_account_key`, gekürzte IP) | 6(1)(f) Art. 32 | 90 d (`settings`) | Tombstone bei Löschung |
| — | `ai_audit_log` | 6(1)(f) | laut Setting | Marker bei Löschung |
| — | strukturierte Logs (Pseudonyme `sub_…`, `ten_…`) | 6(1)(f) | 30 d Pipeline (NFR-011 Q-R3) | keine Rohschlüssel (Guards) |
| **neu R-43** | `privacy_review_items` + Entscheidungen | 6(1)(c) Art. 5(2) Nachweis der Löschungs-Nachverfolgung | 3 J. nach Entscheidung; mit dem Mandanten | **Vorschlag** |

---

## 3. Gesetzliche Aufzeichnungspflichten — Anwendbarkeit je Mandant (LEG-03)

**PRIV-400** Das System DARF NICHT annehmen, dass jeder Mandant an PflSchG §11 oder die
Dokumentationspflichten des KCanG gebunden ist. [verifiziert] Heute gelten `LEGAL_RETENTION_RULES` für jeden Mandanten,
jede `treatment_applications`-Zeile eines Hobbygartens wird zu einer pseudonymisierten 3-Jahres-Aufzeichnung,
nachdem die Autorin / der Autor die Löschung verlangt hat, und der Art.-15-Export einer noch aktiven Person findet sie
über den Tombstone.

**PRIV-401** [DEC-11] `Tenant.settings.record_keeping` (`03` PRIV-122) bestimmt die Klasse der
vier Collections: `legacy`/`pflschg_professional`/`kcang_association`/`both` → gesetzlich
(wie heute); `none` → `shared_history`. Standardwerte: bestehende Mandanten `legacy`; neue
`organization`-Mandanten werden bei der Anlage gefragt (Pflichtauswahl mit Erläuterung); neue `personal`-Mandanten
`none`. **[rechtlich LEG-03]**: (i) Ist die Pflicht aus PflSchG §11 auf „berufliche
Anwender" beschränkt (das Paket nimmt ja an); (ii) welche KCanG-Vorschrift trägt die 5-jährige Ernte-
Dokumentationspflicht und für wen (das Paket nimmt an: nur Anbauvereinigungen); (iii) darf sich der
Betreiber auf die Selbstauskunft des Mandanten verlassen.

**PRIV-402** Wechselt `record_keeping` von gesetzlich auf `none`, MÜSSEN bestehende pseudonymisierte
Zeilen durch einen mandantenbezogenen, idempotenten Job neu klassifiziert werden (`09` §4): Tombstones → Marker
(die Person ist weg; das verknüpfbare Pseudonym hat keine Grundlage mehr), getippte Namen bereits
geleert, `notes` → Prüfpunkte. Die Änderung wird auditiert (`TENANT_RECORD_KEEPING_CHANGED`).
Die umgekehrte Änderung ist nur für neue Zeilen erlaubt (ein Marker kann kein Pseudonym werden).

---

## 4. Bewertungen des berechtigten Interesses (Art. 6(1)(f)) — Drei-Stufen-Tests

Jeder Test hält fest: (1) berechtigten Zweck, (2) Erforderlichkeit, (3) Interessenabwägung mit den
Interessen und Rechten der betroffenen Personen, dazu die Schutzmaßnahmen, die das Paket vorsieht. Alle sind **Vorschläge
für die Interessenabwägung (LIA) des Verantwortlichen**; die Rechtsberatung prüft sie (LEG-02, LEG-06, LEG-07).

### 4.1 LIA-1 — Zuordnung von Ausführenden/Erstellern in gemeinsamen Mandanten (aktuelle Mitglieder)

1. **Zweck**: Koordination gemeinsamer Arbeit (wer hat gegossen, wer hat Beet 3 zuletzt behandelt), Qualität
   der Aufzeichnung (Korrektur durch die Autorin / den Autor), Rechenschaft innerhalb eines Gemeinschaftsgartens oder eines
   Betriebs, agronomische Historie (Fruchtfolge braucht *was* und *wann*, nicht *wer*).
2. **Erforderlichkeit**: Der Zweck *Koordination* braucht den Namen, solange die Person Mitglied ist und
   die Tätigkeit jung ist; der Zweck *Historie* braucht den Namen überhaupt nicht; der Zweck
   *Rechenschaft* braucht den Namen für eine begrenzte Zeit.
3. **Interessenabwägung**: Mitglieder erwarten vernünftigerweise, dass Mitmitglieder sehen, wer was getan hat (ein Aushang
   im Garten leistet dasselbe); das Risiko ist Profiling (Aktivitätsmuster, Anwesenheitszeiten —
   REQ-051 §11 und der REQ-055-Review-Hinweis zu Mustern bei Buchungszeiten) und in Betrieben
   Leistungsbewertung. Schutzmaßnahmen: keine Statistiken je Person (PRIV: Matrixzeile S), Filter
   nach einer anderen Person nur für Leads/Management (SR-020), Mandanteneinstellung `leads_and_self`
   (PRIV-300), Namensunterdrückung nach Ende der Mitgliedschaft (PRIV-112), Entfernung der Zuordnung auf
   Antrag (PRIV-116), keine Zuordnung in Exporten für Nicht-Leads (PRIV-307), Transparenztext
   im Austrittsdialog und in der Datenschutzerklärung (PRIV-115).
   **Ergebnis (vorgeschlagen)**: Das Interesse überwiegt für aktuelle Mitglieder unter den Schutzmaßnahmen;
   es überwiegt **nicht** für die fünfjährige Aufbewahrung des *Namens* — daher Unterdrückung und der
   Marker am Ende der R-25-Frist. **LEG-02**.

### 4.2 LIA-2 — Übernahme der Ausführenden aus gesetzlichen Zeilen in das Pflegelog (v0104, Konsistenz-Job)

1. **Zweck**: eine vollständige Beethistorie, die auch Ernten und Behandlungen enthält, die eingetragen wurden, bevor es
   das Pflegelog gab.
2. **Erforderlichkeit**: Die Historie braucht das *Ereignis*; die *ausführende Person* ist dieselbe betriebliche Tatsache,
   die das Mitglied eingetragen hat (es war ein `performed_by` an der Quelle, vom Aufrufer gestempelt) — es entsteht
   keine neue Information, sie wandert aber in einen Speicher mit 5-jähriger Aufbewahrung, einem
   Filter je Person und einem CSV-Export.
3. **Vereinbarkeit (Art. 6(4))**: gleicher Verantwortlicher, gleicher Kontext (der Mandant), die Person
   hat es als „Ich habe das getan" eingetragen, berechtigte Erwartung, dass das Log des Gartens es zeigt; keine
   sensiblen Daten; die Schutzmaßnahmen von LIA-1 gelten. Pseudonyme/Tombstones DÜRFEN NIE kopiert werden
   (PRIV-205). **Ergebnis (vorgeschlagen)**: vereinbare Weiterverarbeitung; **LEG-07** bestätigt,
   und die Datenschutzinformation / der RoPA-Eintrag muss das Pflegelog als Zweck nennen.

### 4.3 LIA-3 — Namen ehemaliger Mitglieder für N Tage

1. **Zweck**: Übergabe („wer hat sich bis letzte Woche um dieses Beet gekümmert?").
2. **Erforderlichkeit**: kurz; nach der Übergabe der Saison trägt der Name nichts mehr zur Historie bei.
3. **Interessenabwägung**: Die Person ist gegangen; ihre Erwartung, genannt zu werden, nimmt mit der Zeit ab;
   Schutzmaßnahmen: N ≤ 365 mit Standard 90, kein Filter/Export durch sie (PRIV-114), Transparenz
   (PRIV-115), das Security-Audit behält die Tatsache nur für die Plattform-Admin.
   **LEG-06**: N und ob Leads den Namen länger behalten dürfen (das Paket sagt nein).

### 4.4 LIA-4 — Sentry-Fehlererfassung

[verifiziert in Spec] REQ-025 §9: Ereignis 6(1)(f) „rechtlich zu bestätigen", User-Block nur mit
Einwilligung. Nicht geändert; als LEG-16 referenziert.

---

## 5. Daten von Beschäftigten und Ehrenamtlichen (LEG-05)

**Bewertung**
- Ein gewerblicher Mandant, dessen Grower Beschäftigte sind, verarbeitet Beschäftigtendaten, wenn er
  `performed_by`-/Bestätigungsidentitäten mit Zeitstempeln speichert und Leads nach Person filtern lässt.
  Art. 88 DSGVO öffnet nationales Recht; §26(1) BDSG erlaubt eine für das
  Beschäftigungsverhältnis *erforderliche* Verarbeitung (Hinweis: Der EuGH hat in C-34/21 vom 30. März 2023 die parallele hessische
  Vorschrift für mit Art. 88 unvereinbar erklärt, soweit sie lediglich Art. 6(1)(b) wiederholt — die
  fortgesetzte Berufung auf §26 BDSG ist rechtlich unsicher; die Rechtsberatung muss das bewerten). Eine Aufzeichnung darüber,
  wer welche Aufgabe ausgeführt hat, ist gewöhnlich für die Durchführung der Arbeit *erforderlich* (Aufgaben-
  koordination, PflSchG-Aufzeichnung für berufliche Anwender); sie für die **Leistungs-
  bewertung** zu nutzen, ist ein anderer Zweck. §87(1) Nr. 6 BetrVG: Ein System, das *objektiv geeignet* ist,
  Verhalten oder Leistung zu überwachen, unterliegt der Mitbestimmung, sofern ein Betriebsrat
  besteht — der Filter je Person und ein CSV-Export je Person machen das Pflegelog geeignet. Diese
  Pflicht trifft den **Arbeitgeber (Mandant)**, nicht die Plattform; die Plattform muss die
  Funktion beschreibbar und abschaltbar machen.
- **Ehrenamtliche und Vereinsmitglieder** sind keine „Beschäftigten" (§26(8) BDSG); §26 BDSG und
  BetrVG gelten nicht. Die Grundlage ist 6(1)(b) (Mitgliedschaftsverhältnis, Satzung) und 6(1)(f)
  (LIA-1). Das Paket wendet Arbeitsrecht auf sie **nicht** an.
- Die **fünfjährige Aufbewahrung von Bestätigungen** ist nicht, was sie scheint: `care_confirmations` haben keine
  Akteurin / keinen Akteur und keine Aufbewahrungszeile [verifiziert]; die 5 Jahre sind R-25 am abgeleiteten Pflegeereignis. Das
  Ergebnis von LIA-1 (kein Name nach der Frist / nach Ende der Mitgliedschaft) gilt.

**Erforderliche technische Einschränkungen (PRIV-403 … PRIV-407)**

- **PRIV-403** Kein Endpunkt, Export oder keine UI DARF Aktivität je Person aggregieren (Zählungen, Zeit-
  reihen, Ranglisten). Ein künftiges „Statistik"-Feature MUSS eine eigene LIA tragen und für Beschäftigten-
  Mandanten einen Betriebsrat-Hinweis.
- **PRIV-404** `attribution_visibility = leads_and_self` MUSS verfügbar sein (PRIV-300) und
  als Standard für nach der Änderung angelegte Organisations-Mandanten empfohlen werden (Betreiberentscheidung).
- **PRIV-405** Der Filter je Person und der Namensexport MÜSSEN protokolliert werden (PRIV-308), damit der
  Arbeitgeber dem Betriebsrat zeigen kann, wie die Funktion genutzt wird; das Log ist für das `management`
  des Mandanten lesbar (Zählungen je Akteur, 90 Tage) — **Vorschlag**, nur Zählungen.
- **PRIV-406** Die Datenschutzdokumentation (Docs `privacy.md`, DE/EN) MUSS einen Abschnitt
  „Für Betriebe und Vereine" enthalten, der erklärt: was darüber gespeichert wird, wer was getan hat, wer es sieht,
  wie lange, die Einstellung, und dass eine Betriebsvereinbarung erforderlich sein kann — ein Mustertext,
  den der Mandant seinem Betriebsrat aushändigen kann (Produktlieferobjekt, `12`).
- **PRIV-407** Nichts im Pfad der Aufgabenerledigung oder Bestätigung DARF *Dauer* oder
  *Geschwindigkeit* der Arbeit über `performed_at` hinaus aufzeichnen (keine Start-/Stopp-Zeitstempel).

---

## 6. Prüfungen der Zweckbindung (Art. 5(1)(b))

| Flow | Original purpose | Secondary use | Verdict |
|------|------------------|---------------|---------|
| `treatment_applications.applied_by_key` → `care_events.performed_by_user_key` | PflSchG-Aufzeichnung | Beethistorie, Filter, CSV | vereinbar unter LIA-2 (LEG-07); Tombstones nie |
| `harvest_batches.harvested_by_key` ← Task-Completion-Engine (`harvested_by_key = event.performed_by_user_key`) | Pflegelog | gesetzliche Aufzeichnung | dieselbe Tatsache, derselbe Moment; in Ordnung — aber die inhaltlichen Anforderungen an die *Aufzeichnung* (LEG-04) müssen aus der Erledigung erfüllt werden (heute schreibt eine Erledigung keine `treatment_applications`-Zeile [verifiziert], die §11-Aufzeichnung wird also **nicht** vom Aufgabenpfad erzeugt — REQ-053 §13.2 bestätigt, dass der IPM-Endpunkt der Nachweis ist) |
| `bed_templates.name` → `Location.name` → `garden_plan_audit.summary` → SVG/PDF/JSON | Plan | Export/Druck | Inhalt, keine Zuordnung; Lineage registriert (PRIV-230) |
| `users.display_name` → jede API-Darstellung | Identifikation | Aktivitätsanzeige | Schutzmaßnahmen von LIA-1 |
| `security_audit_log` | Art. 32 | — | keine Sekundärnutzung erlaubt (REQ-049 „no surveillance") |
| Gerätecache (`kp-plan-cache`) | Offline-Lesen | — | minimiert ([verifiziert] keine Namen, Notizen, Zuweisungen) |

---

## 7. Informationspflichten (Art. 13/14) — Eingaben, die das Paket liefert

**PRIV-408** Der Text der Datenschutzerklärung (Betreiber, `GET /privacy/policy`) und die mandantenseitigen
Docs MÜSSEN nennen: das Pflegelog und seine Zuordnung; die Unterdrückung für ehemalige Mitglieder; die Prüfwarteschlange
(ein Lead kann Zeilen sehen, die die Person geschrieben hat); die Offline-Speicherung auf dem Gerät (REQ-025 §10
Zeilen); Namen Dritter in `performed_by_label` (Art. 14 — der Mandant informiert den Dritten;
der UI-Hinweis „keine vollständigen Namen" [verifiziert SR-006] bleibt); Fotos, die
Personen zeigen (REQ-053 §32.5 Pkt. 12 offen). **LEG-12** deckt die Formulierung ab.

---

## 8. Fristen, die eine rechtliche Freigabe erfordern (Zusammenfassung der Markierungen)

| Period / basis | Where | Flag |
|----------------|-------|------|
| 5 J. Aufbewahrung von Pflegeereignissen als 6(1)(f) (Fruchtfolge) | R-25 | LEG-02 |
| 90 d Name ehemaliger Mitglieder | PRIV-112 | LEG-06 |
| gesetzliche Anwendbarkeit je Mandant; KCanG-Paragraf; Lesbarkeit des Namens nach PflSchG | §3 | LEG-03, LEG-04, LEG-17 |
| Zweckvereinbarkeit des Backfills | LIA-2 | LEG-07 |
| Prüfmodell für Freitext und 30-Tage-SLA | `04` §5 | LEG-08 |
| TDDDG-Einordnung von IndexedDB/Cache Storage | `07` §2 | LEG-09 |
| Offline-Puffer 90/30 d, tote Sitzung 14 d | `07` §6–7 | LEG-10 |
| Backups 30 d + Replay-Ledger 35 d | `09` §6 | LEG-11 |
| DSFA-Schwelle, RoPA, Texte nach Art. 13/14 | `11` | LEG-12 |
| Mandantenarchiv verlässt die Installation | REQ-056 §8 | LEG-13 |
| Sichtbarkeit der Mitglieder-E-Mail | PRIV-305 | LEG-14 |
| deterministische Tombstones | `04` §2.3 | LEG-15 |
| Benachrichtigungen 90/180 d; Gieß-/Düngelogs 5 J.; geschlossene Aufgaben 2 J. | §2.3 neue Zeilen | LEG-08 (Umfang), DSB gemäß NFR-011 v1.29 („Vorschlag, DSB-Prüfung offen") |

---

## 9. Erforderliche Spec-Änderungen (Vorschläge, nicht angewendet)

| Spec | Change |
|------|--------|
| NFR-011 | neue Zeilen R-43 (Prüfpunkte), R-44 (Datenschutzaktionen im Security-Audit), R-45 (Replay-Ledger), R-46 (Gieß-/Dünge-/Tanklogs), R-47 (geschlossene Aufgaben/Kommentare), R-48 (Benachrichtigungen); R-26 Akteur → Marker; Formulierung der R-25-Grundlage „6(1)(f); Art. 17(3) ist die Löschungsausnahme"; `care_events.material` in der Schwärzungsmenge von R-25; §3.1 Beat-Tabellenzeilen für die neuen Tasks |
| REQ-025 | §3.1.3: Zuordnungsrollen und die Prüfwarteschlange als Phase 2.6; §10 Zeilen für `kp_local_data_owner`, `kp-garden-field-mode`, `kp.emailChange.address`, `kp.stepUp.*`, `kamerplanter:consent:v1` (heute fehlend [verifiziert]); die veralteten Zeilen `i18next`/`theme`/`redux_state` korrigieren (Schlüssel sind `kamerplanter-lang`, `kamerplanter-theme`; kein `redux_state`); Fußzeilenversion 1.5 → aktuell |
| REQ-053 | Feldsatz GP-FR-109 + `material`; GP-NFR-055 `garden_plan_audit` Marker; der Widerspruch „DSGVO-Kaskade kann Freitexte ersetzen" (GP-FR-109) vs. „kein Freitextfeld wird bei der Kaskade geleert" (E-16) zugunsten von E-16 + Prüfwarteschlange aufgelöst |
| REQ-024 / REQ-049 | Einstellungen `attribution_visibility`, `record_keeping`; E-Mail nur für `management`; `management` darf schwärzen |
| REQ-022 | festhalten, dass Bestätigungen keine Akteurin / keinen Akteur und keine eigene Aufbewahrung haben; das abgeleitete Pflegeereignis trägt beides |
| REQ-023 §5b.1 | „Backup-System → Cross-Tenant Read-Access" entfernen oder mit REQ-049 P4 in Einklang bringen |
| docs `privacy.md` | „eine DSFA wurde durchgeführt" entfernen, bis es eine gibt (ADR-003 sagt offen) |
