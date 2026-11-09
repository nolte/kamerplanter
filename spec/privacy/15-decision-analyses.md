# SPEC-15 — Entscheidungsanalysen (DA-01 … DA-08)

```
Paket: spec/privacy · Version 1.1 · 2026-11-09
Jede Analyse folgt derselben Gliederung: 1 aktuelle Spezifikation · 2 verifizierte Fakten ·
3 einschlägige Rechtsvorschriften (L-nn aus 13) · 4 technische Implikationen · 5 Optionen ·
6 Vor-/Nachteile · 7 Empfehlung · 8 verbleibende Unsicherheit · 9 erforderliche Freigabe ·
10 Umsetzungsfolgen. Evidenzklassen: VERIFIED_CODE · VERIFIED_SPEC · VERIFIED_LEGAL ·
INFERRED · PROPOSED · OPEN_DECISION · LEGAL_REVIEW_REQUIRED.
```

---

## DA-01 — Rollen von Verantwortlichem und Auftragsverarbeiter (LEG-01)

**1 Aktuelle Spezifikation.** `06` v1.0 §1 nahm „Mandant = Verantwortlicher, Betreiber =
Auftragsverarbeiter“ als Arbeitsannahme für das gesamte Paket. REQ-025 §8 verlegt das Verzeichnis
nach Art. 30 „außerhalb der Software“; `data_controller` im Export-Bundle ist ein konfigurierter
String (VERIFIED_SPEC/VERIFIED_CODE). Kein Spec-Dokument behandelt die Rollenfrage.

**2 Verifizierte Fakten.** (a) Aufbewahrungsfristen (NFR-011) und ihre Ober-/Untergrenzen sind
**vom Betreiber** in `settings.py` fixiert; ein Mandant kann sie nicht verändern (VERIFIED_CODE:
`RETENTION_CEILINGS`, `retention_care_event_retention_years` Unter- = Obergrenze 5). (b) Sichtbarkeit
der Zurechnung, Filterrechte, Exportformate sind Code, nicht Mandantenkonfiguration (VERIFIED_CODE:
`MembershipEngine.can_filter_care_log_by_member`). (c) Der Plattformbetreiber hat keinen Lesezugriff
auf Fachdaten (VERIFIED_CODE: `require_platform_admin`, keine Domänenrouten; REQ-049 P4). (d) Der
Betreiber verarbeitet Konten, Sicherheits-Audit, Logs, Backups für eigene Zwecke (VERIFIED_CODE).
(e) Selbst gehostete Installation: Betreiber und Mandant fallen zusammen.

**3 Rechtsvorschriften.** Art. 4 Nr. 7, 8; Art. 26; Art. 28 DSGVO (L-12, UNVERIFIED_AT_SOURCE —
nur als Bezug). EDSA 07/2020 Rn. 40 (wesentliche Mittel: „welche Daten, wie lange, wer hat
Zugriff“ sind dem Verantwortlichen vorbehalten), Rn. 54–55 (konvergierende Entscheidungen →
gemeinsame Verantwortlichkeit), Rn. 81 (Auftragsverarbeiter, der eigene Zwecke/Mittel bestimmt, wird
Verantwortlicher) — L-18, VERIFIED_LEGAL.

**4 Technische Implikationen.** Solange der Betreiber **wesentliche Mittel** (Aufbewahrungsdauer der
Zurechnung, Sichtbarkeitsregel, Pseudonymisierungsverfahren) allein und nicht konfigurierbar festlegt,
spricht EDSA 07/2020 Rn. 40 gegen eine reine Auftragsverarbeitung für das Pflegeprotokoll. Die in
`05`/`06` vorgeschlagenen Mandanteneinstellungen (`attribution_visibility`, `record_keeping`,
Aufbewahrung innerhalb von Ober-/Untergrenzen) verschieben die Entscheidung über wesentliche Mittel zum
Mandanten und machen das Auftragsverarbeitungsmodell technisch tragfähig.

**5 Optionen.** (A) Mandant = Verantwortlicher, Betreiber = Auftragsverarbeiter (AVV); Betreiber
eigenverantwortlich nur für Konto, Plattform, Sicherheit, Backups. (B) Gemeinsame Verantwortlichkeit
(Art. 26) für mandantenbezogene Verarbeitung mit Vereinbarung. (C) Betreiber alleiniger Verantwortlicher;
Mandanten-Leads handeln auf Weisung.

**6 Vor-/Nachteile.** A: marktüblich, klare Pflichtenverteilung; setzt voraus, dass der Mandant die
wesentlichen Mittel wählen kann (Einstellungen E08/E09) und dass der Betreiber Löschentscheidungen der
Leads nur ausführt. B: ehrlich bei fest kodierten Mitteln; hoher Vertragsaufwand je Mandant, gemeinsame
Haftung. C: einfachste Vertragslage; unplausibel, weil der Betreiber Fachdaten nicht sieht und die
Zwecke (Garten, Betrieb) nicht bestimmt.

**7 Empfehlung (PROPOSED).** Option A **mit Bedingungen**: (i) die wesentlichen Mittel des
Pflegeprotokolls werden mandantenkonfigurierbar (E08/E09, Aufbewahrung innerhalb Ober-/Untergrenzen),
(ii) der Betreiber ist eigenständig Verantwortlicher für PA-01, PA-02, PA-07a, PA-08 (TDDDG-Anbieter),
PA-09 (`06` §2 Rollenmatrix), (iii) ein AVV-Muster und eine Datenschutzinformation je Betriebsmodell
sind Produktlieferobjekte (E16). Für Verarbeitungen, deren wesentliche Mittel **nicht** konfigurierbar
gemacht werden (z. B. feste 5-Jahres-Frist R-25), ist Option B für diese Verarbeitung zu prüfen.

**8 Verbleibende Unsicherheit.** Ob Aufsichtsbehörden die Konfigurierbarkeit als ausreichend
ansehen; Einordnung des Gemeinschaftsgartens ohne Rechtsform (wer ist dort „Verantwortlicher“?);
Haushaltsausnahme (Art. 2 Abs. 2 lit. c) für persönliche Mandanten mit eingeladenen Familienmitgliedern
(INFERRED: Haushaltsausnahme gilt für den Nutzer, nicht für den Anbieter).

**9 Erforderliche Freigabe.** LEG-01 — Rechtsberatung; Betreiberentscheidung zum Vertragsmodell.
**Produktionsgate:** `processing_allowed = provisorisch` für den Bestand (läuft bereits), `deployment_allowed`
für kommerziellen Betrieb mit Organisationsmandanten **erst** nach Entscheidung LEG-01 und Vorliegen von AVV +
Datenschutzinformation (DEC-32).

**10 Umsetzungsfolgen.** `06` §2 Rollenmatrix (PA-nn); E08/E09 wie geplant; E16 um AVV-Muster,
Datenschutzinformation je Betriebsmodell und Art.-30-Einträge (Betreiberteil) erweitern; `data_controller`
im Export-Bundle wird je Mandant konfigurierbar (Name des Verantwortlichen des Mandanten) — E13 (klein).

---

## DA-02 — Rechtsgrundlagen und Zweckbindung des Pflegeprotokolls (LEG-02, LEG-07)

**1 Aktuelle Spezifikation.** NFR-011 R-25: „Art. 5(1)(e); Art. 17(3) (berechtigtes Interesse:
Anbauhistorie)“ (VERIFIED_SPEC). `06` v1.0 ordnete Inhalt und Zurechnung des Pflegeprotokolls pauschal
Art. 6 Abs. 1 lit. f zu und führte LIA-1…LIA-3.

**2 Verifizierte Fakten.** Pflegeereignisse entstehen durch Handlungen der Mitglieder im Dienst, den sie
nutzen (VERIFIED_CODE: `CareEventService.create/log`, `CompletionActor`). Die Zurechnung wird aus dem
Token gestempelt (GP-NFR-054, VERIFIED_CODE). Die Aufbewahrung der Zurechnung beträgt 5 Jahre (R-25,
VERIFIED_CODE). Der Backfill kopiert `applied_by_key`/`harvested_by_key` in `performed_by_user_key`
(VERIFIED_CODE, `care_event_backfill_mapper.account_of`).

**3 Rechtsvorschriften.** Art. 5 Abs. 1 lit. b, c, e; Art. 6 Abs. 1 lit. b, f; Art. 6 Abs. 4; Art. 17 Abs. 3
(L-12, nur Bezug). EDSA 1/2024 Prüfschema (L-22, VERIFIED_META). **Art. 17 Abs. 3 ist eine Ausnahme vom
Löschanspruch, keine Rechtsgrundlage** — die Spec-Formulierung in R-25 ist daher zu korrigieren (E16).

**4 Technische Implikationen.** Die Grundlage entscheidet, wer die Interessenabwägung dokumentieren muss
(DA-01) und ob eine Widerspruchsmöglichkeit (Art. 21 bei lit. f) technisch vorzusehen ist (PRIV-116).

**5 Optionen.** (A) Inhalt **und** Zurechnung auf lit. f. (B) Inhalt auf lit. b (Erbringung des vom
Mitglied genutzten Dienstes bzw. Mitgliedschaftsverhältnis), Zurechnung gegenüber **anderen** Mitgliedern
auf lit. f mit Abwägung; Aufbewahrung der Zurechnung über die operative Phase hinaus nur, solange die
Abwägung trägt. (C) Zurechnung nur mit Einwilligung (lit. a).

**6 Vor-/Nachteile.** A: einfach, aber „automatische“ lit.-f-Zuweisung für Historie, die der Aufgabe
widerspricht; B: differenziert, entspricht der Praxis (das Mitglied *will* seine Handlung protokollieren,
die Sichtbarkeit für Dritte ist das abzuwägende Element); C: Einwilligung im Beschäftigungs-/Vereins-
kontext fragwürdig freiwillig (§ 26 Abs. 2 BDSG, L-09), hohe Reibung.

**7 Empfehlung (PROPOSED).** Option B. Konkret: Inhalt (was/wann/wo) = lit. b (Nutzer) bzw. lit. b
Mitgliedschaft (Mandant); Zurechnung sichtbar für andere Mitglieder = lit. f (LIA-1, `06` §4.1);
Zurechnung nach Ende der aktiven Phase: Unterdrückung für ehemalige Mitglieder (PRIV-112), Marker nach
R-25. Backfill-Kopie der Zurechnung aus gesetzlichen Zeilen: Zweckänderungsprüfung nach Art. 6 Abs. 4
(LIA-2) — vereinbar, solange keine Pseudonyme kopiert werden (PRIV-205); **alternativ** (konservativ)
Backfill ohne Zurechnung (`performed_by_user_key = null`) — technisch durch einen Schalter wählbar
(`PRIVACY_BACKFILL_COPIES_PERFORMER`, Default: heutiges Verhalten, Gate LEG-07).

**8 Verbleibende Unsicherheit.** Ob der Vertrag mit dem Nutzer die Protokollierung seiner Handlungen
umfasst (Nutzungsbedingungen); ob 5 Jahre Zurechnung überhaupt unter lit. f tragbar sind (LIA-1 sagt nein
→ Marker nach Fristende bleibt; Unterdrückung für ehemalige Mitglieder).

**9 Freigabe.** LEG-02, LEG-07 — DSB/Rechtsberatung. **Gate:** Bestand provisorisch; der Schalter
`PRIVACY_BACKFILL_COPIES_PERFORMER` wird in E01 eingebaut (Default = Bestand), damit die Entscheidung
ohne Release wirksam wird.

**10 Umsetzungsfolgen.** `06` §2 PA-04 Rechtsgrundlage lit. b/lit. f getrennt; R-25-Wortlaut (E16);
E01 Schalter; PRIV-116 (Widerspruch) bleibt P2.

---

## DA-03 — Gesetzliche Aufzeichnungen: KCanG und PflSchG feldgenau (LEG-03, LEG-04, LEG-17)

**1 Aktuelle Spezifikation.** NFR-011 R-16 (Ernte, Qualität, Ertrag: „CanG, 5 Jahre“), R-17
(`treatment_applications`: „PflSchG § 11, 3 Jahre“), R-18 (Inspektionen) — alle auf **ganze Collections**
bezogen; REQ-025 L219 „CanG §X“ (VERIFIED_SPEC). Code: `LEGAL_RETENTION_RULES` wenden R-16/17/18 auf **alle
Mandanten** an; Fristbeginn `harvest_date` / `applied_at` / `inspected_at`; Kontoschlüssel → Tombstone,
Anzeigename geleert (VERIFIED_CODE).

**2 Verifizierte Fakten (rechtlich).** KCanG § 26 Abs. 1 (L-05): Pflichtangaben einer **Anbauvereinigung**
sind Mengen (Nr. 2–4), Empfänger von Weitergaben mit Name/Vorname/Geburtsjahr/Menge/THC/Datum (Nr. 5, 6),
Herkunft von Vermehrungsmaterial (Nr. 1), Transportbegleitende (Nr. 7); Aufbewahrung **fünf Jahre**
(Abs. 2). **Die erntende oder pflegende Person ist nicht Pflichtangabe.** § 9/§ 10 (L-07): privater
Eigenanbau ohne Dokumentationspflicht. PflSchG § 11 (L-01): Adressat berufliche Verwender; Betriebsleiter
führt „unter Angabe des jeweiligen Anwenders“ zusammen; **Fristbeginn 1. Januar des Folgejahres**;
elektronische Führung nach DVO 2023/564 ab 2027. § 2 Nr. 16 (L-02): beruflicher Anwender. Fristlänge und
Inhaltskatalog (VO 1107/2009 Art. 67, DVO 2023/564 Art. 2): UNVERIFIED_AT_SOURCE (L-03, L-04).

**3 Rechtsvorschriften.** L-01, L-02, L-05, L-06, L-07 (VERIFIED_LEGAL); L-03, L-04 (UNVERIFIED_AT_SOURCE);
Art. 6 Abs. 1 lit. c, Art. 17 Abs. 3 lit. b DSGVO (Bezug).

**4 Technische Implikationen.** (a) Für **Anbauvereinigungen** ist aus § 26 nur die **Mengen-/Datums-
dokumentation** der Ernte (Nr. 3) gesetzlich; `harvested_by_key` hat **keine** gesetzliche Grundlage →
der Tombstone dort ist nicht durch Art. 6 Abs. 1 lit. c gedeckt. Die Weitergabe-Dokumentation (Nr. 5–7)
existiert in Kamerplanter als Entität **nicht** → Kamerplanter ist für das KCanG-Register höchstens
Zulieferer der Mengenangaben. (b) Für **berufliche Anwender** ist die anwendende Person Bestandteil der
Betriebsaufzeichnung (§ 11 Abs. 2 S. 2) → `applied_by_key` + ein lesbarer Bezug sind gesetzlich begründbar;
die heutige Leerung des Namens bei Löschung kann die Aufzeichnung unvollständig machen (LEG-04). (c) Der
Fristbeginn im Code (`applied_at`) weicht von § 11 Abs. 3 ab (1. Januar des Folgejahres) → Korrektur
(PRIV-412). (d) Ob eine `treatment_applications`-Zeile die Anforderungen der DVO 2023/564 erfüllt, ist
unbekannt (V-06) → bis dahin **Hilfsdokumentation**. (e) Ohne Kenntnis der Tätigkeit des Mandanten ist die
Pflicht nicht bestimmbar → **Pflichtklassifizierung** bei Anlage.

**5 Optionen.** (A) Status quo: Collection-weite Statutory-Behandlung für alle Mandanten. (B) Profil
`record_keeping` je Mandant mit Collection-weiter Behandlung (v1.0). (C) Profil **und** feldgenaue
Zuordnung: nur die gesetzlich vorgeschriebenen Felder werden unter lit. c aufbewahrt; alle anderen Felder
derselben Zeile folgen den gewöhnlichen Regeln (Marker/Prüfung/Löschung).

**6 Vor-/Nachteile.** A: einfach, aber ohne Grundlage für Hobby-Mandanten und für den Ernte-Ausführenden.
B: beseitigt die Mandantenfrage, behält die Feldfrage. C: rechtlich sauber, mehr Regeln je Collection;
die Zeile bleibt als Fachdatensatz nutzbar.

**7 Empfehlung (PROPOSED).** Option C mit der feldgenauen Zuordnung aus `06` §3.2:
- `kcang_association`: `harvest_batches.{weight/quantity, harvest_date, strain/cultivar, thc?}` und
  `yield_metrics` 5 Jahre (lit. c, § 26 Abs. 1 Nr. 3, Abs. 2); `harvested_by_key` → **Marker** bei
  Löschung (keine Pflichtangabe), `harvester`/`notes` → Prüfung; `quality_assessments` sind Pflicht nur,
  soweit sie den THC-Gehalt (Nr. 5 lit. b) belegen (`[?]` ob das Modell THC trägt → V-11).
- `pflschg_professional`: `treatment_applications.{product, applied_at, dosage, area/location, crop}`
  (Inhalt gem. L-03/L-04, bis V-04/V-06 als VERIFIED_SPEC) + `applied_by_key` als Anwenderbezug (§ 11
  Abs. 2 S. 2); Frist 3 Jahre ab **1. Januar des Folgejahres** (PRIV-412); Lesbarkeit des Namens: LEG-04
  (Default: Pseudonym; Alternative versiegeltes Feld).
- `none` / persönliche Mandanten: keine Statutory-Klasse; die vier Collections sind `shared_history`.
- `undeclared` (neue Organisationsmandanten ohne Angabe): konservativ wie `legacy` **für die Aufbewahrung**,
  aber kein Tombstone für `harvested_by_key` (Marker), Hinweis an die Leitung bis zur Angabe (PRIV-409).

**8 Verbleibende Unsicherheit.** V-04/V-06 (Inhaltskataloge), Anwenderbegriff in § 11 Abs. 2 (Name oder
Kennung), Fristbeginn § 26 KCanG (nicht geregelt), ob Qualitätsbewertungen THC dokumentieren, ob ein
Gemeinschaftsgarten „gärtnerischer Betrieb“ i. S. d. § 11 Abs. 2 S. 2 sein kann.

**9 Freigabe.** LEG-03, LEG-04, LEG-17 — Rechtsberatung. **Gate:** Umstellung von Tombstone auf Marker
für `harvested_by_key` und die Reklassifizierung `legacy → none` sind **datenvernichtend** →
`processing_allowed = false` bis LEG-03/17 entschieden (Feature-Flag `PRIVACY_RECORD_KEEPING_RECLASSIFY`,
Default aus). Die Fristbeginn-Korrektur (PRIV-412) **verlängert** die Aufbewahrung und ist ohne Gate umsetzbar.

**10 Umsetzungsfolgen.** `06` §3 (Feldzuordnung), `03` PRIV-122 (Klassifizierung mit `undeclared`), `08`
§3.2 (`record_keeping` ohne Default), `09` §4 (Reklassifizierung hinter Flag), E09 Scope, NFR-011 R-16/R-17
Textänderung (E16), neuer Verifikationsauftrag V-11 (THC-Feld im Erntemodell).

---

## DA-04 — Beschäftigte, Auftragnehmende, Ehrenamtliche, Vereins- und Haushaltsmitglieder (LEG-05)

**1 Aktuelle Spezifikation.** `06` v1.0 §5: Einschätzung mit §§ 26 BDSG / 87 BetrVG, technische
Einschränkungen PRIV-403…407, Mandanteneinstellung `attribution_visibility` (DEC-10).

**2 Verifizierte Fakten.** REQ-049 §2.3 nennt als typische Grower „Mitarbeiter, Saisonkraft“
(VERIFIED_SPEC). Es gibt keinen Mandantentyp „gewerblich“ (VERIFIED_CODE: `TenantType` = personal |
organization). Personenfilter nur Lead/Management, kein Statistik-Endpunkt (VERIFIED_CODE). CSV mit
Namen für alle Mitglieder (VERIFIED_CODE). `care_confirmations` haben kein Akteursfeld; die 5 Jahre sind
R-25 des abgeleiteten Ereignisses (VERIFIED_CODE).

**3 Rechtsvorschriften.** § 26 Abs. 1 S. 1, Abs. 8 BDSG (L-09, VERIFIED_LEGAL): Ehrenamtliche (außer
JFDG/BFDG) und Vereinsmitglieder sind keine Beschäftigten; § 87 Abs. 1 Nr. 6 BetrVG (L-10,
VERIFIED_LEGAL); Art. 88 DSGVO (Bezug); EuGH C-34/21 (L-13, UNVERIFIED_AT_SOURCE); DSK-Muss-Liste Nr. 8
(L-17, VERIFIED_LEGAL): „umfangreiche Verarbeitung … über das Verhalten von Beschäftigten, die zur
Bewertung ihrer Arbeitstätigkeit … eingesetzt werden **können**“.

**4 Technische Implikationen.** Die Personengruppe ist dem System nicht bekannt; sie muss vom Mandanten
deklariert werden (Klassifizierung `organization_kind`, PRIV-409). Die Eignung zur Bewertung entsteht durch
Personenfilter, Export je Person und Zeitstempel; nicht durch die Protokollierung an sich.

**5 Optionen.** (A) Einheitliche Behandlung aller Mitglieder (Status quo). (B) Zweckgebundenes Zugriffs-
modell je Mandantenklasse: `attribution_visibility`-Default und Pflichthinweise je Klasse; Export/Filter mit
Zweckangabe und Audit; keine Aggregation. (C) Beschäftigten-Mandanten: Zurechnung nur für Lead/Management
sichtbar (verpflichtend), Export je Person gesperrt.

**6 Vor-/Nachteile.** A: ignoriert L-09/L-10; B: proportional, lässt Vereinen Transparenz; C: rechtlich
sicherer für Betriebe, nimmt Koordinationsfunktion.

**7 Empfehlung (PROPOSED).** Option B mit Klassen:
| Gruppe | Rechtsrahmen (Evidenz) | Default `attribution_visibility` | Zusätzliche organisatorische Kontrolle (Pflicht des Mandanten) |
|---|---|---|---|
| Beschäftigte (gewerblicher Mandant) | § 26 BDSG (L-09; Anwendbarkeit nach C-34/21 INFERRED), Art. 88, § 87 Abs. 1 Nr. 6 BetrVG (L-10) | `leads_and_self` | Betriebsvereinbarung/Information des Betriebsrats, Zweckfestlegung „Koordination, keine Leistungsbewertung“, Protokoll der Filter-/Exportnutzung (PRIV-405) |
| Auftragnehmende/Saisonkräfte ohne Arbeitnehmerstatus | lit. b/f; ggf. § 26 Abs. 8 Nr. 6 (INFERRED) | `leads_and_self` | wie oben, Information nach Art. 13 |
| Ehrenamtliche, Vereinsmitglieder | lit. b (Satzung/Mitgliedschaft), lit. f (LIA-1); **nicht** § 26 BDSG (L-09) | `all_members` | Vereinsinterne Information, Satzungsbezug |
| Haushaltsmitglieder (persönlicher Mandant) | lit. b des Kontoinhabers; Haushaltsausnahme für diesen (INFERRED) | `all_members` | — |
Dazu PRIV-403 (keine Aggregation), PRIV-407 (keine Dauer/Geschwindigkeit), PRIV-405 (Audit), PRIV-406 (Mustertext).

**8 Verbleibende Unsicherheit.** Tragfähigkeit von § 26 Abs. 1 BDSG nach C-34/21 (V-08); BAG-Linie zur
„Eignung“ (V-05); ob die Deklaration des Mandanten dem Betreiber genügt.

**9 Freigabe.** LEG-05 — Rechtsberatung. **Gate:** Die Defaults sind **einschränkend** (reduzieren
Sichtbarkeit) → `engineering_allowed`, `deployment_allowed` ohne LEG-Freigabe; der Betrieb eines
gewerblichen Mandanten **mit** `all_members` bleibt dessen Entscheidung, die Oberfläche warnt (PRIV-301).

**10 Umsetzungsfolgen.** PRIV-409 Klassifizierung (`organization_kind ∈ {association, commercial,
community, other}`) als Pflichtangabe neben `record_keeping`; E08 Defaults nach Klasse; E16 Mustertext.

---

## DA-05 — Freitext-Schwärzung: Prüfwarteschlange als Zustandsautomat (LEG-08)

**1 Aktuelle Spezifikation (v1.0).** Prüfeinträge je betroffener Zeile, Kandidaten über Autorenschaft
und Namens-Token, Obergrenze 5 000 je Löschung mit Banner, SLA 30 Tage als Überfälligkeits-Metrik,
Entscheidungen `redact|keep|defer`, `keep` mit `reason_code`, `reason_text` ≤ 500.

**2 Verifizierte Fakten.** Schwärzung existiert nur für `care_events`, nur Lead, ohne Liste
(VERIFIED_CODE). REQ-025 §3.1.3 Regel 4 verbietet das Schlüsseln auf Freitext (VERIFIED_SPEC). Reach-Tests
beweisen Löschung je Collection, nicht je Freitextfeld (VERIFIED_CODE).

**3 Rechtsvorschriften.** Art. 17 Abs. 1 („unverzüglich“), Art. 12 Abs. 3 (ein Monat, verlängerbar; EDSA
01/2022 Rn. zur Monatsfrist, L-19 VERIFIED_LEGAL), Art. 5 Abs. 2 (Rechenschaft), Art. 17 Abs. 3 (Ausnahmen —
keine Grundlage).

**4 Technische Implikationen.** Eine feste Obergrenze, die Zeilen stillschweigend ausschließt, verletzt
Art. 5 Abs. 2 (nicht nachweisbar) und Art. 17 (nicht erledigt). Ein SLA ist keine Erlaubnis zur
Weiterverarbeitung: nach Fristablauf ohne Entscheidung muss das System einen **definierten** Zustand
herbeiführen. Entdeckung muss vollständig sein (Pagination bis Cursor-Ende), Kopien (Datenlinie) müssen
mitentdeckt werden.

**5 Optionen.** (A) v1.0 mit Obergrenze und Banner. (B) Vollständige, paginierte Entdeckung ohne Ausschluss;
Zustandsautomat; nach SLA automatische **konservative** Aktion (Schwärzung für vom Betroffenen
verfasste/ausgeführte Zeilen; Eskalation für reine Namens-Token-Treffer). (C) Automatische Schwärzung
aller Treffer ohne Prüfung.

**6 Vor-/Nachteile.** A: begrenzt Aufwand, aber „silent exclusion“. B: vollständig, nachweisbar; die
Auto-Schwärzung eigener Zeilen ist durch den Kontoschlüssel begründet (kein Schlüsseln auf Freitext);
Namens-Token bleiben Menschenentscheidung. C: vernichtet agronomische Aufzeichnungen Dritter auf
Verdacht.

**7 Empfehlung (PROPOSED).** Option B — Zustandsautomat (`04` §5 neu):
`DISCOVERY_PENDING → REVIEW_REQUIRED → {REDACTION_PENDING → REDACTED | RETAINED_WITH_LEGAL_BASIS | VOID}`,
Abschlusszustand der Löschung `ERASURE_COMPLETED` erst, wenn kein Eintrag mehr in `DISCOVERY_PENDING`/
`REVIEW_REQUIRED`/`REDACTION_PENDING`; `FAILED` mit Wiederholung/Eskalation. `keep` ⇒
`RETAINED_WITH_LEGAL_BASIS` nur mit `legal_basis_ref` (PA-nn oder LEG-nn) und `reason_code`. SLA-Ablauf:
`authored`/`performed`-Treffer → automatische Schwärzung (Flag `PRIVACY_REVIEW_AUTO_REDACT_ON_SLA`, Default
**aus**, bis LEG-08 entschieden; solange aus: Eskalation an Betreiber + Metrik, Zustand bleibt
`REVIEW_REQUIRED`/überfällig); `name_token`-Treffer → Eskalation.

**8 Verbleibende Unsicherheit.** Ob Leads des Mandanten entscheiden dürfen (DA-01); ob ein 30-Tage-SLA
mit „unverzüglich“ vereinbar ist (EDSA: ein Monat für die *Antwort*, L-19); ob Auto-Schwärzung eigener
Zeilen den Mandanten in seiner Historie unangemessen trifft (Abwägung: der Text gehört zur Löschung des
Verfassers; der Sachverhalt bleibt über Kategorie/Menge/Datum erhalten).

**9 Freigabe.** LEG-08. **Gate:** Prüfwarteschlange und Entdeckung sind **schutzverstärkend** →
umsetzbar; Auto-Schwärzung hinter Flag (`processing_allowed` erst nach LEG-08).

**10 Umsetzungsfolgen.** `04` §5 Neufassung, `08` (Zustände, Felder `legal_basis_ref`, Entdeckungs-
Cursor am Löschauftrag, Settings), `10` TAs, E07 Scope, Widerspruchsregister W-05/W-06.

---

## DA-06 — Anonymisierung, Pseudonymisierung, Tombstones (LEG-15)

**1 Aktuelle Spezifikation.** Marker `_anonymized`; Tombstone `anon_ + sha256(user_key + salt)[:16]`,
instanzweit deterministisch; Allowlist; `carry_account_reference`; HMAC nur für neue Ableitungen; Re-Keying
außerhalb des Umfangs (`04` v1.0).

**2 Verifizierte Fakten.** Ableitung und Salt-Pflicht ≥ 32 Zeichen (VERIFIED_CODE `compute_tombstone_hash`);
Salt instanzweit (`ERASURE_TOMBSTONE_SALT`); Art.-15-Suche über den Tombstone (VERIFIED_CODE
`privacy_service.py` Walk); R-06-Purge nur bei Tombstone; Digest-Schlüssel der Client-Events ist derselbe Salt
(VERIFIED_SPEC REQ-053 §32.6 Pkt. 16). Mandantenexport-Archive enthalten Zeilen „wie gespeichert“, also mit
Tombstones (VERIFIED_SPEC REQ-056 §8).

**3 Rechtsvorschriften.** Art. 4 Nr. 5 DSGVO, Erwägungsgrund 26 (Bezug, L-12); WP216 (L-14): Pseudonymisierung
ist keine Anonymisierung; Kriterien Herausgreifen/Verknüpfbarkeit/Inferenz; EDSA 01/2025 (L-15): pseudonymisierte
Daten bleiben personenbezogen, auch nach Löschung der Zusatzinformation beim Verantwortlichen, solange die
Bedingungen der Anonymität nicht erfüllt sind.

**4 Technische Implikationen.** Identifikationsklassen (normativ in `04` §1a):
| Klasse | Definition | Beispiele | Folge |
|---|---|---|---|
| direkt identifizierend | Wert, der ohne Zusatzwissen eine Person benennt oder ein aktives Konto adressiert | `display_name`, `email`, roher `users._key` eines bestehenden Kontos | volle Löschpflicht |
| pseudonym | Zurechnung nur mit gesondert gehaltener Zusatzinformation; Zeilen verknüpfbar | `anon_<hash>` (Salt), `sub_…`-Logpseudonyme, Client-Event-Digest | personenbezogen; Zweck- und Zugriffsbeschränkung; Allowlist |
| effektiv anonym (attributbezogen) | Attribut ohne Zuordnung; die **Zeile** kann über Inhalt identifizieren | Marker `_anonymized`, `null` | Zeile ist anonym erst nach Freitext-Prüfung |
| effektiv anonym (zeilenbezogen) | kein Attribut der Zeile erlaubt Herausgreifen/Verknüpfen/Inferenz mit vernünftigem Aufwand | Mengen-/Datumsaufzeichnung ohne Zurechnung und ohne Freitext | außerhalb der DSGVO |
Verknüpfbarkeit **über Mandanten hinweg**: Derselbe Tombstone erscheint in jedem Mandanten, in dem die Person
gesetzliche Zeilen hinterließ, und in Exportarchiven → wer zwei Archive besitzt, verknüpft die Person über Mandanten
(Risiko RISK-19). Schlüsselrotation ist heute unmöglich ohne Re-Keying-Migration.

**5 Optionen.** (A) Status quo. (B) Für **neue** Pseudonymisierungen `HMAC(salt_tombstone, "tombstone:" ||
tenant_key || ":" || user_key)` (mandantengebunden, domänengetrennt); Bestand unverändert; Art.-15-Suche
iteriert je Mandant der Zeile. (C) Zufällige Token je Zeile (keine Verknüpfbarkeit, keine Art.-15-Suche).

**6 Vor-/Nachteile.** A: einfache Suche, Cross-Tenant-Verknüpfbarkeit. B: beseitigt Cross-Tenant-
Verknüpfbarkeit, behält Verknüpfbarkeit innerhalb des Mandanten (Prüfzweck) und die Art.-15-Suche
(mandantenweise); zwei Formate im Bestand (Allowlist-Regex erweitern). C: maximale Minimierung, verliert
die Prüf- und Auskunftsfunktion.

**7 Empfehlung (PROPOSED, DEC-25).** Option B; Allowlist-Regex `^anon_[0-9a-f]{16}$|^anon2_[0-9a-f]{16}$`;
`is_tombstone` erkennt beide; die Art.-15-Suche prüft je `(tenant_key, user_key)`. Domänentrennung auch
für Client-Event-Digests (eigener abgeleiteter Schlüssel mit Übergangsregel, SEC-003) — als eigenes
Paket E18 (P3). Key-Rotation: Re-Keying-Migration spezifiziert als Verfahren (`09` §7), nicht geplant.
Garantie, die realistisch zugesagt werden kann: **Zurechnung entfernt + Verknüpfbarkeit auf einen Mandanten
und eine Aufbewahrungsklasse begrenzt**; keine Zusage „anonym“ für Zeilen mit Freitext.

**8 Verbleibende Unsicherheit.** Verhältnismäßigkeit deterministischer Pseudonyme für 5 Jahre (LEG-15);
ob Aufsichtsbehörden 64-Bit-Trunkierung als ausreichend ansehen (Kollisionsfreiheit, nicht Sicherheit, ist
hier das Thema; Reidentifikation erfordert den Salt).

**9 Freigabe.** LEG-15 (Verknüpfbarkeit). **Gate:** B ist schutzverstärkend → umsetzbar; `garden_plan_audit`
Tombstone → Marker (DEC-16) ist datenvernichtend, aber ohne gesetzliche Aufbewahrung → umsetzbar nach
Betreiberfreigabe (DEC).

**10 Umsetzungsfolgen.** `04` §1a, §2 (neues Format, Allowlist), `08` §2.2, `09` §7 (Re-Keying-Verfahren),
`11` RISK-19, E04/E05.

---

## DA-07 — Offline-Speicher, TDDDG und geteilte Geräte (LEG-09, LEG-10)

**1 Aktuelle Spezifikation.** `07` v1.0: Einordnung aller Kategorien als § 25 Abs. 2 Nr. 2; Schalter
„Offline-Modus“ empfohlen (DEC-21: Default aus bei Neuinstallationen, **an** bei bereits cachenden
Installationen); Fristen 90/30/14 d; Shared-Device-Modus; Quarantäne.

**2 Verifizierte Fakten.** Cache und Puffer werden heute **ohne** Nutzerhandlung angelegt (VERIFIED_CODE:
SW-Registrierung in `main.tsx`, Plan-Cache bei jedem Lesen); keine Einstellung für Fristen; localStorage mit
`user_key`/E-Mail überlebt Logout; Logout-Wipe nicht abgewartet (VERIFIED_CODE, `07` §1, §7).

**3 Rechtsvorschriften.** TDDDG § 25 Abs. 1, Abs. 2 Nr. 2 (L-11, VERIFIED_LEGAL): kumulativ „unbedingt
erforderlich“ **und** „vom Nutzer ausdrücklich gewünscht“. DSGVO Art. 5 Abs. 1 lit. c, e; Art. 25 Abs. 2
(Bezug) — getrennt zu prüfen: TDDDG regelt den Zugriff auf das Endgerät, DSGVO die Verarbeitung der Daten.

**4 Technische Implikationen.** Je Kategorie zwei Fragen: (i) ist die Speicherung für den **gewünschten**
Dienst unbedingt erforderlich (TDDDG); (ii) ist die Verarbeitung minimiert und befristet (DSGVO). Eine
Installation/Nutzung der PWA ist kein ausdrücklicher Wunsch nach *Offline-Lesen* oder *Offline-Puffer*; die
App-Shell (Precache) ist dagegen für den gewünschten Dienst „App“ erforderlich.

**5 Optionen.** (A) Implizites Caching (Status quo) + Dokumentation. (B) Expliziter Schalter je Gerät für
Lesecache **und** Puffer, Default aus für neue **und** bestehende Installationen (Übergang: Wipe + Hinweis);
App-Shell ohne Schalter. (C) Einwilligungsdialog nach § 25 Abs. 1 für alle Offline-Speicher.

**6 Vor-/Nachteile.** A: TDDDG-Risiko, bestehende Nutzer nie gefragt. B: erfüllt „ausdrücklich gewünscht“
per Handlung, minimiert; Übergang kostet ungesendete Einträge bestehender Installationen nur, wenn der Nutzer
sie nicht sendet (Übergangsdialog). C: rechtlich sicher, UX-Reibung, Einwilligungsmanagement nötig.

**7 Empfehlung (PROPOSED, DEC-29 ersetzt DEC-21).** Option B: Schalter `Offline-Modus` pro Gerät,
Default **aus** für alle Installationen; Übergang beim ersten Start der neuen Version: Plan-Cache wird
gelöscht; vorhandene Puffer-Einträge werden angezeigt mit „jetzt senden / verwerfen“ — ohne Entscheidung
innerhalb von 7 Tagen werden sie gelöscht (Hinweis); erst nach Einschalten entstehen neue Cache-/Puffer-
Daten. Je-Kategorie-Einordnung in `07` §2 (unverändert, aber mit der Handlung „Schalter“ als Nachweis des
Wunsches). Geteilte Geräte: Szenarienmatrix `07` §8a (Browserprofil geteilt, Kiosk, Vereins-PC, mehrere Nutzer,
vergessener Logout, Widerruf, Offline-Löschung) mit je einer technischen Maßnahme.

**8 Verbleibende Unsicherheit.** Ob Aufsichtsbehörden den Schalter als „ausdrücklich gewünscht“ anerkennen;
Angemessenheit 90/30/14 d; ob die Quarantäne als Erfüllung von Art. 17 auf fremden Geräten genügt.

**9 Freigabe.** LEG-09, LEG-10. **Gate:** B ist schutzverstärkend → umsetzbar; **bis** zur Umsetzung von B gilt
für den Bestand `processing_allowed = provisorisch` mit Prüfdatum.

**10 Umsetzungsfolgen.** `07` §2.1 (Aktivierungsmodell), §8a (Szenarien), `09` §8 (Client-Migration), E10/E11,
Widerspruchsregister W-04, DEC-21 superseded.

---

## DA-08 — DSFA-Entscheidung (LEG-12)

**1 Aktuelle Spezifikation.** `11` v1.0 §4 formulierte: „Eine DSFA ist erforderlich, wenn zwei oder mehr
der neun Kriterien zutreffen“ — ein Schwellenwert, den die Leitlinie so nicht aufstellt.

**2 Verifizierte Fakten.** Keine DSFA, kein Verarbeitungsverzeichnis im Repository (VERIFIED_SPEC);
Endnutzer-Doku behauptet eine DSFA (VERIFIED_SPEC, Widerspruch W-10). Verarbeitungsvorgänge O1–O10 und
Risiken RISK-01…19 (`11`).

**3 Rechtsvorschriften.** Art. 35 Abs. 1, 3, 4; Art. 36 (Bezug, L-12). WP248 rev.01 (L-16, VERIFIED_LEGAL):
neun Kriterien; „in most cases … two criteria would require a DPIA“; **auch ein Kriterium kann genügen**;
Beschäftigte als schutzbedürftige Betroffene; Beispiel „Überwachung der Aktivitäten von Beschäftigten“.
DSK-Muss-Liste Nr. 8 (L-17, VERIFIED_LEGAL): umfangreiche Verarbeitung von Beschäftigtenverhalten, die zur
Bewertung eingesetzt werden **kann**; Liste nicht abschließend.

**4 Technische Implikationen.** Die Pflicht hängt vom **Betriebsmodell** ab (selbst gehostet / SaaS, Mandanten-
klassen) und von der Kombination der Vorgänge, nicht von einer Kriterienzahl. Die Methodik muss den
Gesamtkontext bewerten.

**5 Optionen.** (A) Zählregel (v1.0). (B) Begründete Einzelbewertung je Kriterium + DSK-Listenabgleich +
Kombinationsbetrachtung je Betriebsmodell, Ergebnis mit Restrisiko und Entscheidungsbegründung. (C) DSFA
pauschal für alle Modelle.

**6 Vor-/Nachteile.** A: mechanisch, leitlinienwidrig verkürzt. B: entspricht Art. 35 Abs. 1 („voraussichtlich
hohes Risiko“) und der Leitlinie. C: Aufwand ohne Risikobezug für Hobby-Selbsthosting.

**7 Empfehlung (PROPOSED).** Option B — Methodik und Ergebnis in `11` §4 (neu). Ergebnis in Kurzform:
selbst gehosteter Haushalt/Hobby: keine DSFA (kein Kriterium erfüllt, keine Beschäftigten); Gemeinschafts-
garten/Verein (SaaS): DSFA **empfohlen**, nicht zwingend (Kriterium 3 teilweise, kein Kriterium 7); gewerblicher
Mandant mit Beschäftigten (SaaS): DSFA **voraussichtlich erforderlich** (Kriterium 7 erfüllt, Kriterium 1/3
durch Filter/Export/Zeitstempel erfüllt, DSK Nr. 8 einschlägig, sobald „umfangreich“); mit Sensorik (CO₂,
Bewegung, Overrides): zusätzlich Kriterium 4/3 → DSFA erforderlich (NFR-001 §6.7 bereits). DSB-Beteiligung
(Art. 35 Abs. 2) in allen Fällen mit Organisationsmandanten; Art. 36 nur, wenn das Restrisiko nach Maßnahmen
hoch bleibt — nach heutiger Einschätzung nicht.

**8 Verbleibende Unsicherheit.** „Umfangreich“ bei kleinen Betrieben; Einordnung des Cannabis-Kontexts
(RISK-18); Kinder (keine Altersprüfung).

**9 Freigabe.** LEG-12 — DSB. **Gate:** `deployment_allowed` für kommerzielles SaaS mit gewerblichen
Mandanten erst nach DSFA-Entscheidung des DSB (DEC-32).

**10 Umsetzungsfolgen.** `11` §4 Neufassung; E17 Übergabe; Doku-Korrektur (W-10).
