# Decision Log — Datenschutzarchitektur (zentrale Entscheidungsregistry)

```
Paket: spec/privacy · Version 1.1 · 2026-11-09
Serien: DEC-nn = Architektur-/Produktentscheidungen (Betreiber entscheidet) · LEG-nn = Rechtsentscheidungen
(DSB/Rechtsberatung; der Betreiber setzt sie durch). Jede LEG-Zeile ist ein Datensatz der Registry mit
Scope, betroffenen Verarbeitungstätigkeiten (PA-nn aus 06 §2), Owner, erforderlicher Evidenz, Status,
Prüfdatum, Neubewertungsauslöser, Produktionsgate und technischem Durchsetzungspunkt.
Statuswerte DEC: proposed · accepted · rejected · superseded. Statuswerte LEG: open · decided · provisional.
```

## Produktionsgates (Definition; DEC-32)

| Gate | Bedeutung | Wer hebt es |
|------|-----------|-------------|
| `engineering_allowed` | Code, Tests, Migrationen mit Testdaten; Flag aus | immer, sofern die Anforderung spezifiziert ist |
| `deployment_allowed` | ausgerollt in Produktion, Flag aus / Funktion inaktiv | Betreiber nach Abnahme (TA) |
| `processing_allowed` | Flag an / Verarbeitung aktiv: `ja` · `nein (bis LEG-nn)` · `provisorisch (Bestand, Prüfdatum)` | Betreiber nach registrierter Entscheidung |

Regel: Maßnahmen, die Verarbeitung **einschränken** oder den Schutz **verstärken**, sind `ja`; Maßnahmen, die
Verarbeitung **ausweiten** oder Daten mit **möglicher Aufbewahrungspflicht vernichten**, sind `nein (bis LEG)` mit
Flag (`08` §8a). Bestehende Verarbeitung mit offener LEG ist `provisorisch` mit Prüfdatum; sie wird nicht
rückwirkend abgeschaltet, aber der Schalter zur Umsetzung der Entscheidung wird vorab gebaut.

---

## A. Architektur- und Produktentscheidungen (DEC)

| ID | Kontext | Betrachtete Optionen | Empfehlung | Begründung | Rechtsprüfung | Wo es landet | Status |
|----|---------|----------------------|------------|------------|---------------|--------------|--------|
| DEC-01 | Ablageort | `docs/specs/privacy/` · `spec/privacy/` | **`spec/privacy/`** | Spec-Konvention, außerhalb MkDocs `docs_dir`, Vale-frei; Sprache Deutsch (CLAUDE.md) | nein | dieses Verzeichnis | accepted |
| DEC-02 | Registry vs. neue Liste | separates Modul · Attribute an Inventarmodellen | **Attribute an `AnonymizationRule`/… (`08` §2)** | REQ-025 §3.1 (#1663/#1700/#1716): zwei Listen driften | nein | `08` §2 | proposed |
| DEC-03 | Identitätsdarstellung | `UserRef`-Typ · rohe Schlüssel + Resolver | **rohe Schlüssel + `PersonRef`-Resolver** | Risiko liegt in Darstellung/Kopie, nicht im Typ | nein | `01` §4.3, `08` §2.3 | proposed |
| DEC-04 | Tombstone-Ableitung Bestand | behalten · HMAC · zufällig | **Bestand behalten; HMAC für Neues (→ DEC-25); Allowlist** | Art.-15-Suche und R-06 hängen am Determinismus | LEG-15 | `04` §2 | proposed (ergänzt durch DEC-25) |
| DEC-05 | Ende der Mitgliedschaft | `left_at`/Historie · zur Lesezeit ableiten | **ableiten (Schlüssel vorhanden, keine aktive Mitgliedschaft; Austrittszeit aus Security-Audit)** | kein neuer Speicher personenbezogener Daten | LEG-06 | `03` §1.2, §3 | proposed |
| DEC-06 | Freitext gelöschter Mitglieder | löschen · belassen · behalten + Prüfung | **behalten + Prüfung mit vollständiger Entdeckung (→ DEC-27)** | REQ-025 Regel 4; #2517 | LEG-08 | `04` §5 | proposed |
| DEC-07 | `material`, Mess-Strings | außerhalb · aufnehmen | **in `FREE_TEXT_FIELDS`** | CSV-exportiert, sonst nie geschwärzt | nein | `04` PRIV-213 | proposed |
| DEC-08 | Backfill-Zurechnung | nichts · Live-Schlüssel gleicher Rolle, Tombstone → Marker · alles | **Live-Schlüssel gleicher Rolle; Tombstone → Marker; `created_by = null`; Schalter für „nichts“** | LIA-2; Pseudonyme nie neu erzeugen | LEG-07 | `04` §3.3, E01 | proposed |
| DEC-09 | Bestätigungs-Akteur | `null` Queue/MCP · Principal überall | **Principal überall; Service-Account als solcher** | eine Regel; Sichtbarkeit getrennt | LEG-05 (Sichtbarkeit) | `03` §4, E01 | proposed |
| DEC-10 | Sichtbarkeit Durchführende | alle · Leads+selbst · Einstellung | **Einstellung `attribution_visibility`, Default **je Klasse** (DA-04)** | Vereine wollen Transparenz; Betriebe brauchen Einschränkung | LEG-02, LEG-05 | `05` §4, E08 | proposed (aktualisiert v1.1) |
| DEC-11 | Gesetzliche Aufbewahrung | alle Mandanten · Profil Collection-weit · Profil **feldgenau** | **Profil feldgenau (`06` §3.2); Bestand `legacy`; neue Mandanten Pflichtangabe (DEC-30)** | nur Pflichtfelder unter lit. c (L-05: Erntende keine Pflichtangabe) | LEG-03, LEG-04, LEG-17 | `06` §3, E09 | proposed (aktualisiert v1.1) |
| DEC-12 | Offline-Widerruf/Aufbewahrung | dokumentieren · Quarantäne + Codes + kürzere Fristen + Shared-Device | **Quarantäne 14 d, `account.closed`/`membership.ended`, 90/30 d, Shared-Device, Hygiene, abgewarteter Wipe** | Hinweis ist kein Schutz | LEG-09, LEG-10 | `07`, E10, E11 | proposed |
| DEC-13 | Backups | CronJob aktivieren · nur mit Replay | **nur mit Löschungs-Spiegel + Restore-Replay (→ DEC-26); Dumps ≤ 35 d** | jeder Restore erzeugt sonst gelöschte Personen neu | LEG-11 | `09` §6, E14 | superseded durch DEC-26 (Mechanik), Bedingung bleibt |
| DEC-14 | Observability | Logs · Metriken + Endpunkt + Beat | **Metriken + Zähler-Endpunkt + `privacy.consistency` (Minimal in E04, Vollform E15, DEC-28)** | `open_failing` ist ein Logfeld | nein | `08` §5–6, E04/E15 | proposed |
| DEC-15 | Benachrichtigungen | keine · R-48 | **R-48 (90/180 d)** | empfängergebundene Texte | DSB | `06` §8, E13 | proposed |
| DEC-16 | `garden_plan_audit`-Akteur | Tombstone · Marker | **Marker** | kein gesetzlicher/Art.-15-Bedarf an Verknüpfbarkeit | LEG-15 | `04` §4.1, E04 | proposed |
| DEC-17 | Mitglieds-E-Mail | alle · `management` | **nur `management` (Breaking Change)** | Erforderlichkeit zweifelhaft | LEG-14 | `05` PRIV-305, E08 | proposed |
| DEC-18 | MCP rohe Schlüssel | behalten · `PersonRef` | **`PersonRef`; `inspector="mcp:<key>"` → `inspected_by_key`** | GP-API-034 | nein | `05` PRIV-310, E08 | proposed |
| DEC-19 | Status geschlossenes Konto | anonymer Endpunkt · E-Mail | **E-Mail** | Enumerationsrisiko | nein | `03` PRIV-102 | proposed |
| DEC-20 | Spec-Drift | still korrigieren · versioniertes Änderungsset | **E16** | keine stillen Änderungen | LEG-12 (Texte) | `06` §9, `14`, E16 | proposed |
| DEC-21 | Offline-Opt-in (v1.0) | implizit · Schalter (Default an bei Bestand) | — | widersprach L-11 „ausdrücklich gewünscht“ (W-04) | — | — | **superseded durch DEC-29** |
| DEC-22 | `created_by` bei Backfill | Durchführender · `null` + Korrekturrecht | **`null` + PRIV-215** | Rollen nicht vermischen | nein | `04` §3.3 | proposed |
| DEC-23 | Sprache des Pakets | Englisch · Deutsch · zweisprachig | **Deutsch** | Repo-Konvention; Code/GitHub englisch | nein | alle | accepted (Betreiber, 2026-11-09) |
| **DEC-24** | KCanG feldgenau | Collection-weit (Bestand) · Pflichtfelder nach § 26 Abs. 1 | **nur Mengen/Datum/THC als Pflichtfelder; erntende Person → Marker (PRIV-411)** | L-05: Erntende keine Pflichtangabe; L-07: Eigenanbau ohne Pflicht | LEG-03, LEG-17 | `06` §3.2, E09 (Flag) | proposed |
| **DEC-25** | Pseudonymformat Neuzeilen | instanzweit (Bestand) · mandantengebunden HMAC · zufällig | **`anon2_` = HMAC(salt, "tombstone:"+tenant+":"+user)[:16]; Bestand bleibt** | RISK-19 Cross-Tenant-Verknüpfbarkeit; Art.-15-Suche bleibt möglich | LEG-15 | `04` PRIV-238, `08` §2.2, E03 | proposed |
| **DEC-26** | Löschung nach Restore | Raw-Key-Ledger (v1.0) · Tombstone-Spiegel + Abgleich | **Spiegel: Tombstones/Mandantenschlüssel, Fernet + HMAC-Kette, Abgleich über `compute_tombstone_hash` wiederhergestellter `users`** | kein neuer Rohschlüssel-Speicher; W-09 | LEG-11 | `09` §6, `08` §3.7, E14 | proposed |
| **DEC-27** | Prüfwarteschlange | Obergrenze + Banner (v1.0) · Zustandsautomat ohne Ausschluss | **Zustandsautomat, paginierte Entdeckung, nur Eskalationsschwelle, `keep` nur mit Rechtsgrundlage, SLA-Aktion hinter Flag** | Art. 5 Abs. 2; Art. 17 Abs. 1; W-05/W-06 | LEG-08 | `04` §5, `08`, E07 | proposed |
| **DEC-28** | E04/E15-Konflikt | Beat als Vorbedingung (v1.0) · Nachprüfung in der Migration + Minimal-Beat in E04 | **Migration verifiziert selbst; Minimal-Beat in E04; Vollform E15** | W-02 | nein | `09` §3, `12` | proposed |
| **DEC-29** | Offline-Aktivierung | implizit · Opt-in nur neu · **Opt-in für alle mit Übergang** | **Opt-in für alle; Bestand: Cache löschen, Puffer-Dialog 7 d** | L-11 kumulativ „ausdrücklich gewünscht“ + „unbedingt erforderlich“; W-04 | LEG-09 | `07` §2.1, `09` §8, E11 | proposed (ersetzt DEC-21) |
| **DEC-30** | Mandantenklassifizierung | Modell-Default `legacy` (v1.0) · Pflichtangabe bei Anlage | **`organization_kind` + `record_keeping` Pflicht bei Anlage; kein Modell-Default; Bestand `legacy` per v0109; `undeclared`-Verhalten** | W-03; DA-03/DA-04 | LEG-03 (Verlass auf Selbstauskunft) | `06` PRIV-409, `08` §3.2, E09 | proposed |
| **DEC-31** | PflSchG-Fristbeginn | `applied_at` (Code) · 1. Januar Folgejahr | **1. Januar des Folgejahres (PRIV-412)** | L-01 Abs. 3 VERIFIED_LEGAL; W-16 | nein (gesetzlich eindeutig; Länge weiterhin V-04) | `06` §3.2, E09 | proposed |
| **DEC-32** | Produktionsgates | „LEG blockiert nie“ (v1.0) · drei Gates + Flags + Betreiber-Checkliste | **drei Gates; Flags `08` §8a; Checkliste für kommerziellen SaaS-Betrieb (AVV, Information, DSFA-Entscheidung)** | W-07 | — | README, `06` §10, hier | proposed |
| **DEC-33** | Evidenzklassen | implizite Marker · explizite Klassen + Register | **sieben Klassen; Register `13` mit L-nn/V-nn; keine MUSS-Anforderung auf unverifizierter Rechtsquelle** | Aufgabe §2 | — | README, `13`, alle | proposed |
| **DEC-34** | Datenlinie | nur statische Registry · Registry + Laufzeit-Provenienz + Lebensdauerregeln | **beides (PRIV-609/610)** | AST erfasst Jobs/Exporte/Offline nicht | nein | `02` §5a, `08` §2.4a, E05/E15 | proposed |

---

## B. Rechtsentscheidungen (LEG) — Registry

Spalten: Frage · Kontext/Scope · betroffene PA · verifizierte Fakten (L-nn) · technische Constraints · Optionen ·
Empfehlung/Default · Konsequenzen · Owner · Rechtsfreigabe · Produktionsgate · Durchsetzungspunkt · Prüfdatum /
Neubewertungsauslöser · Status. Prüfdatum-Vorschlag für alle offenen Punkte: **2027-01-31** (Betreiber passt an);
allgemeine Auslöser: Änderung des Betriebsmodells, Gesetzesänderung (KCanG-Evaluierung, Geltungsbeginn DVO 2023/564 ab
01.01.2027), DSB-Entscheidung, neue Rechtsprechung.

| ID | Frage | Scope / PA | Fakten (L-nn) | Technische Constraints | Optionen | Empfehlung / Default | Konsequenzen | Owner | Freigabe | Gate | Durchsetzungspunkt | Prüfdatum / Auslöser | Status |
|----|-------|-----------|---------------|------------------------|----------|----------------------|--------------|-------|----------|------|--------------------|----------------------|--------|
| LEG-01 | Verantwortlichkeit je Betriebsmodell (Mandant = Verantwortlicher, Betreiber = AV? gemeinsam? Betreiber allein?) | alle PA; DA-01 | L-18 (wesentliche Mittel) VERIFIED_LEGAL; Art. 26/28 Bezug (L-12) | wesentliche Mittel heute fest kodiert | A AV mit konfigurierbaren Mitteln · B gemeinsam · C Betreiber | **A mit Bedingungen (E08/E09, AVV, Information)** | AVV-Muster, Art.-30-Einträge, Datenschutzinformation je Modell | Betreiber + Rechtsberatung | ja | `deployment_allowed` kommerzieller Betrieb: nein bis entschieden; Bestand provisorisch | DEC-32-Checkliste | 2027-01-31; neues Betriebsmodell | open |
| LEG-02 | Rechtsgrundlage Inhalt (lit. b) und Zurechnung (lit. f, LIA-1) des Pflegeprotokolls; 5 J. Zurechnung tragbar? | PA-04; DA-02 | L-22 META; L-12 Bezug | Zurechnung aus Token; R-25 fest 5 J. | A alles lit. f · B lit. b + lit. f · C Einwilligung | **B**; Unterdrückung/Marker vor Fristende | NFR-011 R-25 Textänderung (W-17) | Mandant (LIA) + DSB | ja | Bestand provisorisch; Einschränkungen ja | PRIV-112, PRIV-300 | 2027-01-31 | open |
| LEG-03 | Gilt PflSchG § 11 nur für berufliche Anwender; welche KCanG-Vorschrift trägt welche Pflicht; darf der Betreiber der Selbstauskunft des Mandanten vertrauen? | PA-05; DA-03 | L-01, L-02, L-05, L-07 VERIFIED_LEGAL; L-03/L-04 UNVERIFIED | Pflicht nur über Klassifizierung bestimmbar | A alle Mandanten · B Profil Collection-weit · C Profil feldgenau | **C**; Bestand `legacy` | Reklassifizierung datenvernichtend | DSB/Rechtsberatung | ja | Klassifizierung/Fristbeginn ja; Reklassifizierung und PRIV-411 **nein** | Flag `PRIVACY_RECORD_KEEPING_RECLASSIFY` | 2027-01-31; V-04/V-06; KCanG-Evaluierung | open |
| LEG-04 | Muss der **Name** des Anwenders 3 J. lesbar bleiben (§ 11 Abs. 2 S. 2 „unter Angabe des jeweiligen Anwenders“) oder genügt das Pseudonym? | PA-05; DA-03 | L-01 VERIFIED_LEGAL; L-04 UNVERIFIED | Name heute bei Löschung geleert | A Pseudonym (Bestand) · B versiegeltes Namensfeld | **A bis Entscheidung** | ggf. `applied_by_sealed` (neues Feld, Step-up) | Rechtsberatung | ja | Bestand provisorisch | — (kein Flag; Codeänderung erst bei B) | 2027-01-31; V-06 | open |
| LEG-05 | Grundlage Beschäftigtendaten (§ 26 BDSG nach C-34/21; Art. 88); Mitbestimmung § 87 Abs. 1 Nr. 6; Pflichten der Plattform gegenüber Arbeitgebern | PA-04, PA-03; DA-04 | L-09, L-10 VERIFIED_LEGAL; L-13 UNVERIFIED; L-17 Nr. 8 | Personengruppe nur per Klassifizierung bekannt | A einheitlich · B Zugriffsmodell je Klasse · C Pflicht `leads_and_self` | **B** | Mustertext, Audit, Defaults | Mandant (Arbeitgeber) + Rechtsberatung | ja | Defaults ja (einschränkend); gewerblicher Betrieb siehe LEG-01 | PRIV-300/301, PRIV-405 | 2027-01-31; V-05, V-08 | open |
| LEG-06 | (a) Frist Namensunterdrückung ehemaliger Mitglieder; (b) Art.-15-Export liest verlassene Mandanten nicht | PA-04 | — (INFERRED) | Austrittszeit aus Security-Audit | 0–365 d · Lead-Ausnahme · Manifest erweitern | **90 d, keine Ausnahme; (b) unverändert** | Setting | DSB | ja | ja (einschränkend) | `RETENTION_FORMER_MEMBER_NAME_DAYS` | 2027-01-31 | open |
| LEG-07 | Zweckvereinbarkeit Backfill-Zurechnung (Art. 6 Abs. 4); `pest_control`-Ereignisse keine § 11-Aufzeichnung | PA-04/PA-05; DA-02 | — (INFERRED) | Kopie läuft bereits | A kopieren · B `null` | **A (Bestand) mit Schalter** | Schalter in E01 | DSB | ja | Bestand provisorisch | `PRIVACY_BACKFILL_COPIES_PERFORMER` | 2027-01-31 | open |
| LEG-08 | Prüfmodell: dürfen Leads entscheiden; 30-Tage-SLA; Auto-Schwärzung eigener Zeilen nach SLA; Namens-Token verhältnismäßig? | PA-06/PA-07b; DA-05 | L-19 (Monatsfrist) VERIFIED_LEGAL | Zustandsautomat | Eskalation · Auto-Schwärzung · Betreiber prüft | **Zustandsautomat; Auto-Schwärzung aus** | Flag | DSB (+ LEG-01) | ja | Warteschlange ja; Auto-Schwärzung **nein** | `PRIVACY_REVIEW_AUTO_REDACT_ON_SLA` | 2027-01-31 | open |
| LEG-09 | TDDDG § 25 Abs. 2 Nr. 2 je Speicherkategorie; genügt der Opt-in-Schalter als „ausdrücklich gewünscht“? | PA-08; DA-07 | L-11 VERIFIED_LEGAL | Cache heute implizit | implizit · Schalter · Einwilligungsdialog | **Schalter für alle (DEC-29)** | Übergang, Doku | Betreiber + DSB | ja | Bestand provisorisch bis E11; danach ja | Schalter (PRIV-531) | 2027-01-31; V-03 | open |
| LEG-10 | Gerätefristen 90/30/14 d; Quarantäne als Art.-17-Erfüllung; Shared-Device-Maßnahmen | PA-08 | — (INFERRED) | kein Serverzugriff auf Gerät | Fristen · Verschlüsselung · Modus | **Fristen + Quarantäne + Modus** | Settings | DSB | ja | ja (einschränkend) | Runtime-Config | 2027-01-31 | open |
| LEG-11 | Backups ≤ 35 d mit Replay vertretbar; Spiegel mit Pseudonymen zulässig? | PA-09; DA-? (`09` §6) | L-19 Rn. 110 VERIFIED_LEGAL; L-21 kein deutscher Beleg | kein Backup aktiv | Dumps + Replay · kürzere Dumps · Verzicht | **Dumps ≤ 35 d + Spiegel + Replay (DEC-26)** | E14 | Betreiber + DSB | ja | `deployment_allowed` Backups nein bis E14 | Helm-Precheck | 2027-01-31; Backup-Aktivierung | open |
| LEG-12 | DSFA erforderlich? RoPA-Einträge; Art.-13/14-Texte | alle; DA-08 | L-16, L-17 VERIFIED_LEGAL | — | je Betriebsmodell (`11` §4.3) | **gewerblich: DSFA erforderlich; Verein: empfohlen; Hobby: nein** | E16/E17 | DSB | ja | `deployment_allowed` kommerziell nein | DEC-32-Checkliste | vor Aufnahme des Modells | open |
| LEG-13 | Mandantenarchiv (GPS, Mitgliedsnamen) verlässt die Installation; Art. 28/44; DSFA-Notiz | PA-11 | — | REQ-056 | — | unverändert | — | DSB | ja | Bestand provisorisch | — | 2027-01-31 | open |
| LEG-14 | E-Mail aller Mitglieder für alle sichtbar? | PA-03 | — (INFERRED) | Route ohne Gate | alle · `management` | **`management` (DEC-17)** | Breaking Change | DSB | ja | ja (einschränkend) | PRIV-305 | 2027-01-31 | open |
| LEG-15 | Deterministische Pseudonyme 5 J.; mandantengebundene Pseudonyme für Neues; Marker im Plan-Audit | PA-05, PA-02; DA-06 | L-14, L-15 VERIFIED_LEGAL | Art.-15-Suche | Bestand · DEC-25 · zufällig | **DEC-25 + DEC-16** | E03/E04 | DSB | ja | ja (schutzverstärkend) | `is_tombstone`, Allowlist | 2027-01-31 | open |
| LEG-16 | Sentry lit. f (REQ-025 §9) | PA-02 | VERIFIED_SPEC | — | — | wie REQ-025 | — | DSB | ja | Bestand provisorisch | Consent `error_tracking` | 2027-01-31 | open (pre-existing) |
| LEG-17 | Welche KCanG-Pflicht trägt die 5-Jahres-Erntedokumentation; Fristbeginn § 26; gilt sie für Eigenanbau? | PA-05; DA-03 | L-05 (§ 26: Mengen Nr. 3, 5 J.), L-07 (kein Eigenanbau) VERIFIED_LEGAL | Code: Collection-weit | — | **§ 26 Abs. 1 Nr. 3/Abs. 2 nur Anbauvereinigungen; Eigenanbau keine Pflicht** (zur Bestätigung) | REQ-025 „CanG §X“ ersetzen | DSB | ja | Reklassifizierung nein (mit LEG-03) | Flag | V-02; KCanG-Evaluierung | open |
| **LEG-18** | Inhaltskatalog und elektronische Form nach DVO 2023/564 ab 2027: erfüllt `treatment_applications` die Vorgaben; ist die anwendende Person Datenelement? | PA-05; DA-03 | L-01 (Verweis) VERIFIED_LEGAL; L-04 UNVERIFIED | Feldzuordnung unvollständig | — | **Hilfsdokumentation (PRIV-413) bis V-06** | ggf. Felder ergänzen (REQ-010) | Rechtsberatung | ja | Bestand provisorisch | Doku-Text | 2026-12-31 (vor Geltung 01.01.2027) | open |
| **LEG-19** | Darf der Inhalt des Pflegeprotokolls auf lit. b (Dienst/Mitgliedschaft) statt lit. f gestützt werden (DA-02 Option B)? | PA-04; DA-02 | — (INFERRED) | — | A/B/C (DA-02) | **B** | Information, RoPA | DSB | ja | Bestand provisorisch | — | 2027-01-31 | open |

---

## C. Bereits getroffene Betreiberentscheidungen, auf die sich das Paket stützt (VERIFIED_SPEC)

| Datum | Entscheidung | Quelle |
|-------|--------------|--------|
| 2026-10-18 (E-16) | `performed_by`-Filter: Viewer/Grower nur selbst; Lead/`management` beliebig; Pflegeprotokoll kein § 11-Nachweis; Freitexte gelöschter Mitglieder bleiben | REQ-053 §32.3, #2411 |
| 2026-10-19 | WP-4.3-Platzhalter 1–5 bestätigt; Punkt 6 → #2517 | #2416 |
| 2026-11-03 | M4-Backfill: Durchführender nur aus Konto-Referenz | REQ-053 §32.5 Pkt. 5 |
| 2026-11-03 | Beetlisten-CSV `include_assignment` ohne Rollenprüfung | REQ-053 §32.5 Pkt. 13 (Paket: PRIV-309 neu bewerten) |
| 2026-10-04 | INV-1 beim Antrag; persönlicher Garten im Art.-15-Bündel; Freitext Dritter unmaskiert | REQ-025 v1.32/1.33 |
| 2026-09-26 | persönlicher Mandant bei Kontolöschung vollständig gelöscht | REQ-025 Q-E1/Q-E5 |
| 2026-11-09 | REQ-053-Partition: #2770 nach #2758; #2517 Rechts-Hold | Partitions-Artefakt |
| 2026-11-09 | PR #2839 gemergt (schließt #2770): `account_of` Tombstone → Marker, Migration v0107, `created_by` auf Live-Bestätigungen, `INACTIVE_TENANT`-Skip; Punkt 2 (Principal auf Queue/MCP) an #2517 übergeben; v0104 unverändert (NFR-016 M-7) | PR #2839, develop 343afbb97 |
| 2026-11-09 | Paketsprache Deutsch | DEC-23 |

---

## D. Änderungskontrolle

Eine DEC-Zeile wechselt den Status durch Betreiberbestätigung (Issue-Kommentar, hier referenziert). Eine LEG-Zeile
wechselt zu `decided` mit Datum, Entscheidung, Evidenz (L-nn) und der geänderten Regel/Einstellung/Flag; die
betroffenen PRIV-Anforderungen erhalten einen Changelog-Eintrag; das Flag wird in derselben Änderung umgestellt.
`provisional` kennzeichnet Bestandsverarbeitung mit Prüfdatum. Nichts in diesem Log wird ohne versionierte Änderung
(E16) auf REQ/NFR-Dokumente angewendet. Widersprüche: `14`.
