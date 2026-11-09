# Kamerplanter — DSGVO-Datenschutzarchitektur und Umsetzungsspezifikation

```
Ablageort: spec/privacy/ (siehe decision-log.md DEC-01, warum nicht docs/specs/privacy/)
Version: 1.0 · 2026-11-09 · gemessen gegen develop 24d1c2988
Status: umsetzungsreifer Entwurf; rechtliche Prüfung steht für jeden LEG-nn-Punkt aus
Sprache: Deutsch (Spezifikation); Issue-Titel und GitHub-Texte bleiben englisch
Verantwortlich: Engineering (Erstellung) · DSB / Rechtsberatung (LEG-Entscheidungen) · Betreiber (DEC-Entscheidungen)
```

## Zweck

Dieses Paket ist die maßgebliche technische Grundlage, um Datenschutz durch Technikgestaltung
in Kamerplanter als mandantenfähiger, gegebenenfalls kommerziell betriebener Anwendung
umzusetzen. Es trennt, **was das Repository bereits leistet** (am obigen Commit
verifiziert), **was dieses Paket vorschlägt** und **was nur die Rechtsberatung entscheiden
kann**. Ein Entwickler oder Coding-Agent kann jeden Roadmap-Punkt anhand der referenzierten
Abschnitte umsetzen, ohne die Begründung neu herleiten zu müssen.

Es baut auf den bestehenden Spezifikationen auf und ändert sie nie stillschweigend: REQ-025
(Datenschutz & Betroffenenrechte), NFR-011 (Aufbewahrungsfristen), REQ-023/REQ-024/REQ-049
(Konten, Mandanten, Rollen), REQ-053 (Gartenplan, Pflegelog, Offline), UI-NFR-012 (PWA).
Wo eine Änderung dieser Dokumente nötig ist, wird sie als **Spec-Änderungsvorschlag**
aufgeführt (`06-retention-and-legal-basis.md` §9, Roadmap-Punkt E16).

## Dokumenthierarchie und Lesereihenfolge

| # | Dokument | Beantwortet | Anforderungs-IDs |
|---|----------|-------------|------------------|
| 01 | [`01-privacy-architecture.md`](01-privacy-architecture.md) | Vokabular, Komponenten, Datenflüsse, Vertrauensgrenzen, Identitätstrennung, Lebenszyklus-Überblick | PRIV-001…012 |
| 02 | [`02-personal-data-inventory.md`](02-personal-data-inventory.md) | jede Entität/jedes Feld mit personenbezogenen Daten: Kategorie, Zweck, Rechtsgrundlage, Sichtbarkeit, Aufbewahrung, Löschung, Anonymisierung, Lineage; Felder, die **nicht** existieren | PRIV-030…031 |
| 03 | [`03-account-and-membership-lifecycle.md`](03-account-and-membership-lifecycle.md) | Kontolöschung, Ende der Mitgliedschaft, Mandantenlöschung, erneuter Beitritt, Offline-Löschung, gesetzliche Nutzer, Wiederverarbeitung | PRIV-100…134 |
| 04 | [`04-anonymization-and-redaction.md`](04-anonymization-and-redaction.md) | Marker vs. Tombstone vs. anonym, Tombstone-Allowlist, Freitext-Prüfwarteschlange, generische Schwärzung, Audit-Verhalten, Legacy-Migration, Verifikation, Vorher-/Nachher-Beispiele | PRIV-200…236 |
| 05 | [`05-access-and-visibility.md`](05-access-and-visibility.md) | wer die Identitäten von Durchführenden/Erstellenden/Bestätigenden, Freitext, Verlauf und Exporte sehen darf; Mandanten- vs. Plattformzugriff; Zweckberechtigungen | PRIV-300…316 |
| 06 | [`06-retention-and-legal-basis.md`](06-retention-and-legal-basis.md) | Aufbewahrungsmatrix mit Rechtsgrundlagen, gesetzliche Anwendbarkeit je Mandant, dreistufige Interessenabwägungen, Beschäftigten-/Ehrenamtsdaten, Zweckbindung, Spec-Änderungsvorschläge | PRIV-400…408 |
| 07 | [`07-offline-privacy.md`](07-offline-privacy.md) | Geräte-Speicherinventar, TDDDG-Einordnung, Cache-/Queue-Lebenszyklus, Aufbewahrung, Logout, Mandantenwechsel, Widerruf, geteilte Geräte, Replay | PRIV-500…530 |
| 08 | [`08-api-and-data-model.md`](08-api-and-data-model.md) | Registry-Attribute, `PersonRef`, neue Collections, Einstellungen, Routen, Enum-Werte, Fehlercodes, Kompatibilität | PRIV-600…608 |
| 09 | [`09-migrations-and-backfills.md`](09-migrations-and-backfills.md) | v0107–v0109, Reklassifizierung, persistierte Dry-Run-Berichte, Backups und Restore-Replay, Salt-Einschränkung, Geräte-Migration | PRIV-700…717 |
| 10 | [`10-testing-and-acceptance.md`](10-testing-and-acceptance.md) | TA-nnn-Matrix je Anforderungsgruppe, negative „kann nicht wieder auftauchen"-Tests, Gates | TA-001…TA-809, PRIV-900…902 |
| 11 | [`11-dpia-pre-screening.md`](11-dpia-pre-screening.md) | Verarbeitungsvorgänge, Risikoregister RISK-01…18, Schwellenwertprüfung nach Art. 35, DSFA-Eingaben | — |
| 12 | [`12-implementation-roadmap.md`](12-implementation-roadmap.md) | Epics PRIV-E01…E17 mit P0–P3, Scope, Abhängigkeiten, Akzeptanz, Tests, Rechtspunkten; Lane-Reihenfolge | — |
| — | [`decision-log.md`](decision-log.md) | DEC-01…23 (Architektur/Produkt), LEG-01…17 (rechtlich), berücksichtigte Betreiberentscheidungen, Änderungskontrolle | — |

Zuerst `01` lesen, dann `03`→`04`→`05` für das Verhalten, `06` für den rechtlichen Rahmen,
`07` für den Client, `08`/`09` zur Umsetzung, `10` zur Verifikation, `12` zur Planung. `02` ist
die Referenztabelle; `11` und das Decision-Log sind die Übergabe an den DSB und den Betreiber.

## Umsetzungsreihenfolge

P0 (Defekte, nächste Lane nach dem Wave-10-Plan): **E01** (= GitHub #2770) → **E03** → **E02** →
**E04**. P1: **E05** (Registry + Resolver) → **E10** (Offline-Widerruf) → **E07**
(Prüfwarteschlange) → **E08** (Sichtbarkeit) → **E06** (ehemalige Mitglieder) → **E09**
(Aufzeichnungspflicht). P2: E11 → E13 → E12 → E14. P3: E15, E16, E17. Details und
Abhängigkeitsgraph: `12-implementation-roadmap.md`.

## Rückverfolgbarkeitsmodell

```
REQ-025 / NFR-011 / REQ-053 … (bestehende Anforderungen, deutsch)
        │ baut auf / schlägt versionierte Änderungen vor (06 §9, E16)
        ▼
PRIV-nnn  (RFC-2119-Anforderung in 01–09; [verifiziert] / [Vorschlag] / [rechtlich] markiert)
        │ jede PRIV nennt ≥ 1 Akzeptanzkriterium
        ▼
TA-nnn    (10: Testart, Assertion, Pfad; TA-Nummerierung spiegelt das Dokument: TA-1xx ↔ 03, TA-2xx ↔ 04 …)
        │ jedes P0/P1-Epic listet seine TA-Menge
        ▼
PRIV-Enn  (12: Umsetzungseinheit; nennt die LEG-nn-Defaults, mit denen sie ausgeliefert wird)
        │
        ▼
DEC-nn / LEG-nn (Decision-Log: wer entscheidet, Default, Alternative, wo es landet)
```

Regeln: Eine Anforderung ohne TA ist nicht umsetzungsreif (die Abschlussprüfung fand keine);
ein LEG-Punkt blockiert nie das Engineering — der Default ist spezifiziert und umschaltbar;
die Code-Inventare (`ErasureEngine.*`, `DataExportEngine.*`) bleiben die einzige Quelle der
Listen, dieses Paket ergänzt eine abgesicherte Klassifizierung (`08` §2, TA-001/030/606).

## Was ist verifiziert, vorgeschlagen, rechtlich, offen

- **Verifizierte Repository-Fakten** sind mit `[verifiziert]`/`[v]` markiert und zitieren
  `path:symbol` (Zeilennummern nur dort, wo sich die Datei zwischen `68460e817` und
  `24d1c2988` nicht geändert hat). Die Repository-Analyse nutzte sieben lesende Durchläufe
  (Löschengine, Mandanten/RBAC, Pflegelog, Freitext, Offline, Spezifikationen,
  Migrationen/Exporte); der primäre Checkout wurde per Fast-Forward auf `24d1c2988`
  gebracht, weil dem früheren lokalen Stand Wave 9 fehlte.
- **Vorgeschlagene Architektur** ist mit `[Vorschlag]` markiert und in DEC-01…23
  zusammengefasst.
- **Rechtliche Annahmen** sind in `06` und LEG-01…17 mit dem ausgelieferten Default explizit
  genannt.
- **Offene Umsetzung**: alles in `12`; nichts aus diesem Paket wurde umgesetzt, es wurde kein
  Anwendungsverhalten geändert, kein GitHub-Issue angelegt oder geschlossen.

## Konventionen

RFC-2119-Schlüsselwörter sind normativ (MUSS, DARF NICHT, SOLLTE, KANN/DARF).
„Anonymisiert" wird nur dort verwendet, wo eine Zeile geprüft wurde oder keinen
identifizierenden Inhalt enthält; sonst „Zuordnung entfernt" (Marker `_anonymized`) und
„pseudonymisiert" (Tombstone `anon_<16hex>`) (`04` §1). Fehlercodes folgen NFR-006,
Service-Methoden, die per Schlüssel laden und schreiben, nehmen `*, tenant_key: str` (#2107),
neue Routen treten dem Isolation-Route-Walk und dem Guard für begrenzte Listen bei, Enums
sind additiv mit DE/EN-i18n. Sprachregel: Der Spezifikationstext ist deutsch (wie REQ/NFR);
Quellcode und GitHub-Texte (Issue-Titel, PR-Texte) sind englisch.

## Pflege

Jedes Dokument trägt seinen eigenen Versions-/Datumskopf. Wird ein LEG-Punkt entschieden,
sind das Decision-Log und die betroffene PRIV-Anforderung in derselben Änderung zu
aktualisieren; werden REQ/NFR-Dokumente bearbeitet (E16), ist in deren Changelog-Zeilen auf
`spec/privacy` zu verweisen.
