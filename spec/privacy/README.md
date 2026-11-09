# Kamerplanter — DSGVO-Datenschutzarchitektur und Umsetzungsspezifikation

```
Ablageort: spec/privacy/ (DEC-01) · Sprache: Deutsch (DEC-23); Issue-Titel, Code und GitHub-Texte englisch
Version: 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97) (Branch docs/privacy-spec-package)
Status: umsetzungsreif für die in 12 §4 als READY/READY_WITH_GUARDS geführten Anforderungen; produktive
Verarbeitung gegateter Maßnahmen erst nach registrierter Rechtsentscheidung (decision-log §B)
Verantwortlich: Engineering (Erstellung) · DSB / Rechtsberatung (LEG) · Betreiber (DEC, Gates)
```

## Zweck

Das Paket ist die maßgebliche technische Grundlage für Datenschutz durch Technikgestaltung in Kamerplanter als
mandantenfähiger, gegebenenfalls kommerziell betriebener Anwendung. Es trennt **verifizierte Repository-Fakten**,
**verifizierte Rechtsquellen**, **Vorschläge** und **offene Rechtsentscheidungen** und erlaubt, freigegebene
Funktionen umzusetzen, ohne Datenschutzverhalten zu erfinden oder Rechtsentscheidungen stillschweigend zu treffen.
Es baut auf REQ-025, NFR-011, REQ-023/024/049, REQ-053 und UI-NFR-012 auf und ändert sie nie stillschweigend
(Änderungsvorschläge: `06` §9, Epic E16).

## Dokumenthierarchie

| # | Dokument | Inhalt | IDs |
|---|----------|--------|-----|
| 01 | [`01-privacy-architecture.md`](01-privacy-architecture.md) | Vokabular, Komponenten, Datenflüsse, Vertrauensgrenzen, Identitätstrennung, Prinzipien | PRIV-001…012 (Bereich 001–029) |
| 02 | [`02-personal-data-inventory.md`](02-personal-data-inventory.md) | feldgenaues Inventar mit Lebenszyklus; Ableitungswege (§5/§5a); nicht existierende Felder | PRIV-030…031 |
| 03 | [`03-account-and-membership-lifecycle.md`](03-account-and-membership-lifecycle.md) | Kontolöschung, Mitgliedschaftsende, Mandantenlöschung, Wiedereintritt, Offline, Pflichtaufzeichnungen, Teilausfall | PRIV-100…134 |
| 04 | [`04-anonymization-and-redaction.md`](04-anonymization-and-redaction.md) | Identifikationsklassen, Marker/Tombstone (zwei Generationen), Zustandsautomat der Freitextprüfung, generische Schwärzung, Verifikation | PRIV-200…239 |
| 05 | [`05-access-and-visibility.md`](05-access-and-visibility.md) | Sichtbarkeitsmatrix, Mandanten- vs. Plattformzugriff, Defaults je Mandantenklasse, Zweckberechtigungen | PRIV-300…316 |
| 06 | [`06-retention-and-legal-basis.md`](06-retention-and-legal-basis.md) | Rollenmatrix (PA-nn), Verarbeitungstätigkeiten-Matrix, **feldgenaue Pflichtaufzeichnungen**, LIAs, Beschäftigte/Ehrenamt, Aufbewahrung, Produktionsgates | PRIV-400…414 |
| 07 | [`07-offline-privacy.md`](07-offline-privacy.md) | Gerätespeicher, TDDDG/DSGVO getrennt, **Opt-in und Übergang**, Fristen, Widerruf, Shared-Device-Szenarien | PRIV-500…533 |
| 08 | [`08-api-and-data-model.md`](08-api-and-data-model.md) | Registry, `PersonRef`, Laufzeit-Provenienz, Collections (`erasure_mirror`), Defaults ohne Modell-Default, Routen, **Feature-Flags** | PRIV-600…610 |
| 09 | [`09-migrations-and-backfills.md`](09-migrations-and-backfills.md) | Migrationsphasen, v0108–v0110, Reklassifizierung (Flag), **Löschungs-Spiegel und Restore-Replay**, Re-Keying, Geräte-Migration | PRIV-700…718 |
| 10 | [`10-testing-and-acceptance.md`](10-testing-and-acceptance.md) | TA-Matrix, Negativtests „kann nicht wieder auftauchen“, Gates | TA-001…TA-810 |
| 11 | [`11-dpia-pre-screening.md`](11-dpia-pre-screening.md) | Verarbeitungsvorgänge, Risikoregister RISK-01…20, **begründete Art.-35-Bewertung je Betriebsmodell** | — |
| 12 | [`12-implementation-roadmap.md`](12-implementation-roadmap.md) | Epics E01…E18, Defaults je Klasse, **Readiness-Tabelle** | — |
| 13 | [`13-legal-evidence-register.md`](13-legal-evidence-register.md) | **Rechtsevidenzregister** L-nn mit Wortlaut, URL, Fassung, Prüfdatum; Verifikationsaufträge V-nn | L-01…L-22, V-01…V-11 |
| 14 | [`14-contradiction-register.md`](14-contradiction-register.md) | **Widerspruchsregister** W-01…W-26 mit Auflösung und Test | — |
| 15 | [`15-decision-analyses.md`](15-decision-analyses.md) | **Entscheidungsanalysen** DA-01…DA-08 (Rollen, Rechtsgrundlagen, KCanG/PflSchG, Beschäftigte, Freitext, Pseudonymisierung, Offline/TDDDG, DSFA) | — |
| — | [`decision-log.md`](decision-log.md) | **Entscheidungsregistry**: DEC-01…34, LEG-01…19 mit Scope, PA, Owner, Gate, Durchsetzungspunkt, Prüfdatum | — |

Lesereihenfolge: `01` → `15` (Analysen) → `06` (Recht) → `03`/`04`/`05` (Verhalten) → `07` → `08`/`09` → `10` → `12`.
`02`, `13`, `14` sind Nachschlagewerke; `11` und das Decision-Log sind die Übergabe an DSB und Betreiber.

## Evidenzklassifizierung (DEC-33)

| Klasse | Bedeutung | Verwendung |
|--------|-----------|------------|
| `VERIFIED_CODE` | am Commit im Code gelesen (`path:symbol`) | Fakten zur Implementierung |
| `VERIFIED_SPEC` | in REQ/NFR/UI-NFR wörtlich belegt | dokumentierte Anforderungen |
| `VERIFIED_LEGAL` | Wortlaut aus der Primärquelle (`13` L-nn, mit URL, Fassung, Prüfdatum) | Rechtsaussagen |
| `INFERRED` | technisch/rechtlich begründet, nicht direkt verifiziert | Auslegungen; nie allein Basis einer MUSS-Anforderung |
| `PROPOSED` | empfohlenes Zielverhalten | neue Anforderungen |
| `OPEN_DECISION` | braucht eine autorisierte (Betreiber-)Entscheidung | DEC |
| `LEGAL_REVIEW_REQUIRED` | braucht qualifizierte Rechtsprüfung | LEG |

Dokumente aus v1.0 verwenden die Kurzmarker `[verifiziert]` (= VERIFIED_CODE/VERIFIED_SPEC je Bezug), `[Vorschlag]`
(= PROPOSED), `[rechtlich]` (= LEGAL_REVIEW_REQUIRED), `[?]` (= INFERRED/unverifiziert). Eine Rechtsquelle, die aus
der Umgebung nicht abrufbar war, ist `UNVERIFIED_AT_SOURCE` mit Verifikationsauftrag V-nn; sie trägt keine
MUSS-Anforderung. **EUR-Lex und Curia waren am 2026-11-09 nicht abrufbar** (HTTP 202/JS-Weiterleitung); DSGVO-Artikel
werden daher nur als Bezug genannt, deutsche Gesetze (gesetze-im-internet.de) und EDSA/WP29/DSK-PDFs sind verifiziert.

## Rechtliches Freigabemodell und Produktionsgates (DEC-32)

- **Registry**: jede Rechtsfrage ist eine LEG-Zeile mit Scope, betroffenen Verarbeitungstätigkeiten (PA-nn, `06` §2),
  Owner, erforderlicher Evidenz, Status, Prüfdatum, Neubewertungsauslöser, Produktionsgate und technischem
  Durchsetzungspunkt (Feature-Flag, Setting, Helm-Precheck; `08` §8a).
- **Drei Gates**: `engineering_allowed` (Code/Tests/Flag aus) · `deployment_allowed` (ausgerollt, inaktiv) ·
  `processing_allowed` (aktiv). Einschränkende/schutzverstärkende Maßnahmen sind freigegeben; ausweitende oder
  datenvernichtende Maßnahmen stehen hinter Flags, bis die LEG entschieden ist; Bestandsverarbeitung mit offener LEG
  ist `provisorisch` mit Prüfdatum.
- **Kommerzieller SaaS-Betrieb mit gewerblichen Mandanten** ist `deployment_allowed = nein`, bis LEG-01 (AVV,
  Rollen), LEG-05 (Beschäftigte) und LEG-12 (DSFA-Entscheidung) vorliegen.

## Rückverfolgbarkeit

```
REQ-025 / NFR-011 / REQ-053 …  ──(baut auf / schlägt versionierte Änderungen vor: 06 §9, 14, E16)──▶
PRIV-nnn (normativ, mit Evidenzklasse, Komponente, Begründung)
   ├── Akzeptanz: TA-nnn (10; Testart, Assertion, Pfad)
   ├── Umsetzung: E01…E18 (12; Abhängigkeiten, Gate, Flag)
   ├── Entscheidung: DEC-nn / LEG-nn (decision-log; Owner, Gate, Prüfdatum)
   ├── Evidenz: L-nn / V-nn (13)
   └── Widerspruch: W-nn (14)
```

Regeln: Eine Anforderung ohne TA ist nicht umsetzungsreif; eine Rechtsaussage ohne L-nn ist `INFERRED`; ein
Widerspruch wird in allen betroffenen Dokumenten zugleich aufgelöst und mit Test versehen; die Code-Inventare
(`ErasureEngine.*`, `DataExportEngine.*`) bleiben die einzige Quelle der Listen, das Paket ergänzt abgesicherte
Klassifizierung (`08` §2, TA-001/030/606).

## Umsetzungsreihenfolge

P0: E01-Rest (#2770 wurde durch #2839 geschlossen; offen: Principal auf Queue/MCP, Filter, Schalter) → E03 → E02 → E04. P1: E05 → E10 → E09 → E07 → E08 → E06. P2: E11 → E13 → E12 → E14.
P3: E15, E18, E16, E17. Readiness je Epic: `12` §4. Nichts aus diesem Paket wurde implementiert, kein
Anwendungsverhalten geändert, kein GitHub-Issue angelegt oder geschlossen.

## Konventionen

RFC-2119 (MUSS, DARF NICHT, SOLLTE, KANN). „Anonymisiert“ nur zeilenbezogen (`04` §1a); sonst „Zurechnung entfernt“
(Marker) oder „pseudonymisiert“ (Tombstone). Fehlercodes nach NFR-006; Service-Methoden, die per Schlüssel laden und
schreiben, nehmen `*, tenant_key: str` (#2107); neue Routen im Isolation-Route-Walk und im Bounded-List-Guard; Enums
additiv mit DE/EN-i18n. Art. 17 Abs. 3 DSGVO ist eine Ausnahme vom Löschanspruch, keine Rechtsgrundlage.

## Pflege

Jedes Dokument trägt Version/Datum. LEG-Entscheidung ⇒ Decision-Log, betroffene PRIV und Flag in derselben Änderung;
REQ/NFR-Änderungen (E16) zitieren `spec/privacy`; neue Widersprüche zuerst in `14`.
