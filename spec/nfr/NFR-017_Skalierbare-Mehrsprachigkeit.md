---

ID: NFR-017
Titel: Skalierbare Mehrsprachigkeit (N-Sprachen-i18n)
Kategorie: Architektur / Datenmodell Unterkategorie: Internationalisierung, Lokalisierung, Locale-Resolution, Fehlermeldungssprache Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python 3.14, FastAPI, Pydantic, ArangoDB, React, TypeScript, react-i18next
Status: Entwurf
Priorität: Hoch
Version: 1.0
Autor: Business Analyst - Agrotech
Datum: 2026-07-12
Tags: [i18n, mehrsprachigkeit, lokalisierung, locale-map, fallback-chain, enum, error-messages, datenmodell]
Abhängigkeiten: [NFR-001, NFR-003, NFR-005, NFR-006, NFR-016, UI-NFR-007]
Betroffene Module: [ALL]
---

# NFR-017: Skalierbare Mehrsprachigkeit (N-Sprachen-i18n)

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.0 | 2026-07-12 | Erstversion (Issue #568). Definiert das **eine** skalierbare Locale-keyed Content-Modell für lokalisierte Stammdaten (kein per-Sprache-Attribut), die **eine** Locale-Resolution über den Stack mit definierter Fallback-Kette, die Enum-Behandlung (stabiler Wert + Katalog-Label), die Regel **technische Fehler English-only / nutzerseitige Meldungen katalogisierbar**, sowie die RAG-/Knowledge-Sprachstrategie. Grenzt gegen UI-NFR-007 (UI-Verhalten), NFR-003 (Source-Language-Scope) und NFR-005 (Docs-Mehrsprachigkeit) ab. Ist-Zustand: `spec/analysis/i18n-current-state-capture.md`; Zielarchitektur: `spec/analysis/i18n-implementation-concept.md`; Rollout: `.audits/plans/07-i18n-nlanguage-rollout.md`. |

## 1. Business Case

### 1.1 User Stories

**Als** Produktverantwortlicher
**möchte ich** die Anwendung in beliebig viele Sprachen übersetzen lassen können
**um** neue Märkte zu erschließen, ohne dass jede Sprache eine Schema- oder Code-Änderung erzwingt.

**Als** Backend-Entwickler
**möchte ich** lokalisierte Stammdaten (Namen, Beschreibungen, Hinweise) über **ein** einheitliches, Locale-keyed Modell speichern und ausliefern
**um** nicht für jede Sprache neue Felder (`*_de`, `*_en`, `*_fr`, …) an jeder Entität pflegen zu müssen.

**Als** Support-Ingenieur
**möchte ich**, dass technische Fehlermeldungen und Logs immer auf Englisch sind
**um** Diagnosen unabhängig von der Nutzersprache reproduzierbar zu halten — während der Endnutzer trotzdem eine lokalisierte, verständliche Meldung sieht.

**Als** Übersetzer
**möchte ich** eine neue Sprache als reine Daten-/Katalog-Ergänzung hinzufügen
**um** ohne Entwickler-Eingriff eine weitere Locale zu ergänzen.

### 1.2 Geschäftliche Motivation

Die heutige Realität ist ein **gespaltenes Modell** (Ist-Zustand: `spec/analysis/i18n-current-state-capture.md`):

- **Per-Sprache-Attribut (Anti-Pattern):** Felder mit Sprachsuffix (`common_name_de`, `name_de`, `label_de`, `name_en`) — allein in den Seed-Daten **784 Feld-Vorkommen** über **15 Dateien** (davon ~68 % nur-DE), plus **141 `_de`/`_en`-Felddefinitionen** in Backend-Modellen/DTOs und **246 Feldzugriffe** im Frontend. Jede weitere Sprache erzwingt hier neue Felder auf **jeder** Entität — das erreicht ein **architektonisches Limit** und skaliert nicht auf 5+ Sprachen.
- **Locale-Map (skalierbares Zielmuster):** bereits vorhanden in `glossary_terms` (`labels`/`long_labels`/`fallback_text` als `dict[str, str]`) und `starter_kits` (`name_i18n`/`description_i18n`) mit Resolver + Fallback auf `de`.

Diese Anforderung macht das **skalierbare Muster verbindlich** und definiert die Migration des Anti-Patterns dorthin als Ziel — die Umsetzung selbst folgt dem Rollout-Plan (`.audits/plans/07-i18n-nlanguage-rollout.md`), ist aber **nicht** Teil dieser Anforderung.

### 1.3 Abgrenzung zu bestehenden Anforderungen

| Dokument | Zuständigkeit | Abgrenzung zu NFR-017 |
|----------|---------------|------------------------|
| **UI-NFR-007** (Internationalisierung) | UI-**Verhalten**: Sprachumschalter, Text-Externalisierung über i18n-Keys, Datums-/Zahlen-/Pluralformate, RTL-Vorbereitung | UI-NFR-007 bleibt die maßgebliche Quelle für das Frontend-**Rendering**. NFR-017 ergänzt das **Daten- & Architektur-Fundament** (Locale-keyed Content-Modell, Server-Locale-Resolution, Fehler-Sprachregel, RAG-Strategie), auf dem UI-NFR-007 aufsetzt, und hebt UI-NFR-007 R-003/R-024/R-025 (N-Sprachen, RTL) von SOLL auf ein architektonisch abgesichertes Niveau. |
| **NFR-003** (Englischer Source-Code-Standard) | Sprache von **Source Code**, Kommentaren, Commits, API-Doku | NFR-017 präzisiert die Grenze: NFR-003 regelt Bezeichner/Code; NFR-017 regelt **Laufzeit-Inhalte** (nutzerseitige Meldungen sind lokalisierbar, technische Fehler/Logs bleiben Englisch — konsistent mit NFR-003 §2.1). |
| **NFR-005** (Technische Dokumentation) | MkDocs DE-kanonisch / EN-Mirror | NFR-017 übernimmt das DE-kanonisch/Mirror-Prinzip als **einen Sonderfall** der Gesamtstrategie (§6) und definiert, wie es sich auf weitere Sprachen erweitert. |
| **NFR-006** (API-Fehlerbehandlung) | Struktur der Fehler-Responses (`error_code`, `detail`) | NFR-017 §5 baut auf dem vorhandenen `error_code`-Katalog auf und macht ihn zum Träger der Lokalisierung nutzerseitiger Meldungen. |
| **NFR-016** (Migrationsstrategie) | Versioniertes Schema-Migrations-Framework | Die Überführung des Anti-Patterns in Locale-Maps läuft als reguläre versionierte Migration (§7, nächste freie Version v0020). |

---

## 2. Grundprinzipien (verbindlich)

Die drei harten Constraints aus Issue #568 sind normativ:

| # | Prinzip | Stufe |
|---|---------|-------|
| **P-1** | **Kein per-Sprache-Extra-Attribut.** Lokalisierte, menschenlesbare Inhalte werden **nicht** über Felder mit Sprachsuffix (`*_de`, `*_en`, …) modelliert. Das Modell MUSS auf **5+ Sprachen** skalieren, **ohne** dass pro Entität neue Felder, Schema-Änderungen oder per-Sprache-Code-Zweige nötig werden. Eine neue Sprache ist eine **additive Daten-/Katalog-Operation**. | MUSS |
| **P-2** | **Technische/entwicklerseitige Meldungen sind English-only.** Logs, 5xx/interne Fehler und Entwickler-Diagnosen sind ausschließlich Englisch (konsistent mit NFR-003). **Nutzerseitige** Meldungen bleiben über stabile Keys/Katalog **lokalisierbar** — niemals als lokalisiertes String-Literal im Code. | MUSS |
| **P-3** | **Konsistenz.** Es gibt **genau eine** Locale-Resolution und **genau ein** Localized-Content-Modell über den gesamten Stack (Seed → DB → Domain/DTO → API → Frontend → RAG), mit **einer** definierten **Fallback-Kette** für fehlende Übersetzungen. | MUSS |

---

## 3. Localized-Content-Modell (P-1)

### 3.1 Locale-Map als einziges Muster

| # | Regel | Stufe |
|---|-------|-------|
| R-101 | Lokalisierte Stammdaten-Felder MÜSSEN als **Locale-Map** modelliert werden: eine nach BCP-47-Sprachcode (`de`, `en`, `fr`, `es`, `ar`, …) verschlüsselte Abbildung `dict[str, str]` (bzw. `dict[str, list[str]]` für Alias-Listen). Das kanonische Vorbild ist `GlossaryTerm.labels`/`long_labels`/`fallback_text` (`domain/models/glossary_term.py:58-65`) und `StarterKit.name_i18n`/`description_i18n`. | MUSS |
| R-102 | Neue lokalisierte Felder DÜRFEN NICHT mit Sprachsuffix (`*_de`, `*_en`) angelegt werden — weder in Seed-YAML, Schemas, Domain-Modellen noch DTOs. | MUSS |
| R-103 | Für die Locale-Map SOLL ein **gemeinsamer, wiederverwendbarer Typ** (z.B. `type LocalizedText = dict[str, str]`) mit einem Resolver `resolve(text, locale, *, fallback_chain)` existieren — ein einziger Ort für die Fallback-Logik, nicht pro Modell dupliziert. | SOLL |
| R-104 | In den JSON-Schemas SOLL das Locale-Map-Objekt über **eine** wiederverwendbare `$ref`-Definition (z.B. `_defs.schema.yaml#/$defs/localized_text`) deklariert werden, statt pro Sprache/Feld eigene Properties (`common_name_de:`, `common_name_en:`) zu zementieren. | SOLL |
| R-105 | Der Sprachcode-Raum ist **offen** (`str`/BCP-47), nicht als geschlossenes `Literal["de","en"]` hart kodiert. Ein `Literal` DARF NUR dort stehen, wo es rein die *aktuell ausgelieferten* Kataloge beschreibt und ohne Migration erweiterbar bleibt. | MUSS |

### 3.2 Fallback-Kette (P-3)

| # | Regel | Stufe |
|---|-------|-------|
| R-106 | Fehlt die angeforderte Locale in einer Locale-Map, MUSS in dieser Reihenfolge zurückgefallen werden: **(1)** exakte angeforderte Locale → **(2)** Basissprache der Locale (`de-AT` → `de`) → **(3)** konfigurierte **Default-Locale** (`de`, vgl. UI-NFR-007 R-002) → **(4)** ein deterministischer technischer Fallback (Slug/`_key`), niemals ein leerer String für ein Pflicht-Label. | MUSS |
| R-107 | Die Fallback-Kette MUSS an **einer** Stelle pro Layer implementiert sein (Backend-Resolver, Frontend-Resolver) und identisch definiert sein. | MUSS |
| R-108 | Fehlende Übersetzungen SOLLEN beobachtbar sein (Dev-Warnung im Frontend gemäß UI-NFR-007 R-009; optional Metrik/Log-Event im Backend), damit Lücken sichtbar werden statt still zu degradieren. | SOLL |

### 3.3 Enum-Behandlung

| # | Regel | Stufe |
|---|-------|-------|
| R-109 | Enum-**Werte** bleiben stabile, englische, maschinenlesbare `snake_case`-Bezeichner (`germination`, `vegetative`) und sind **niemals** lokalisiert oder als Anzeigetext verwendet (konsistent mit UI-NFR-007 R-005, NFR-003). | MUSS |
| R-110 | Enum-**Labels** werden über den Übersetzungskatalog unter einheitlichem Namespace `enums.<enumName>.<value>` aufgelöst (UI-NFR-007 R-007). Eine neue Sprache ergänzt nur den Katalog — **keine** Änderung an `enums.py`, `types.ts` oder den Seed-Daten. | MUSS |
| R-111 | Die Enum-Label-Auflösung SOLL im Frontend über **einen** zentralen Helper (`resolveEnumLabel`/`useEnumLabel`) laufen statt über ~519 inline zusammengesetzte `t(\`enums.…\`)`-Aufrufe, damit fehlende Labels einheitlich behandelt werden. | SOLL |

---

## 4. Locale-Resolution (P-3)

| # | Regel | Stufe |
|---|-------|-------|
| R-112 | Es MUSS **genau eine** serverseitige Locale-Resolution geben. Die effektive Request-Locale wird deterministisch abgeleitet aus (Priorität absteigend): **(1)** expliziter Request-Parameter (sofern der Endpoint einen anbietet) → **(2)** `user.locale` / `UserPreference.locale` (authentifiziert) → **(3)** `Accept-Language`-Header → **(4)** Default-Locale (`de`). | MUSS |
| R-113 | Die gespeicherte Nutzer-Locale (`user.locale`, `user_preference.locale`) MUSS serverseitig **tatsächlich angewendet** werden, wo der Server lokalisierte Inhalte oder Meldungen erzeugt — heute wird sie nur persistiert und zurückgespiegelt, aber nie zur Sprachwahl gelesen. | MUSS |
| R-114 | Die Resolution SOLL als **eine** FastAPI-Dependency (`get_request_locale`) bereitgestellt werden, statt `language: str = "de"` an jedem Router/Service-Signatur zu wiederholen. | SOLL |
| R-115 | Das Frontend MUSS **eine** aktive Locale führen (react-i18next `i18n.language`) und diese für **alle** locale-abhängigen Entscheidungen nutzen — Text, Enum-Label, Datums-/Zahlenformat, Backend-Content-Auswahl. Verstreute binäre `=== 'de'`/`startsWith('en')`-Zweige (~76 Stellen) MÜSSEN durch die zentrale Locale + zentrale Formatter/Resolver ersetzt werden. | MUSS |
| R-116 | Datums-/Zeit-/Zahlenformatierung MUSS ausschließlich über die zentrale Utility (`utils/formatting.ts`, `Intl`-basiert mit `i18n.language`) laufen; hartkodierte Locale-Literale (`'de-DE'`/`'en-US'`) und deutsche `dayjs`-Formatstrings sind unzulässig (Detaildurchsetzung: UI-NFR-007 §2.3/§2.4). | MUSS |

---

## 5. Fehlermeldungs-Sprache (P-2)

| # | Regel | Stufe |
|---|-------|-------|
| R-117 | **Technische Meldungen** (Logs, 5xx/interne Fehler, Diagnosen, `structlog`-Events) MÜSSEN Englisch sein. Sie werden **nicht** lokalisiert. | MUSS |
| R-118 | **Nutzerseitige Fehlermeldungen** MÜSSEN über einen stabilen, maschinenlesbaren **`error_code`** (vorhandener Katalog in `common/exceptions.py`, 36 Codes, NFR-006) transportiert werden. Die menschenlesbare, lokalisierte Meldung wird aus dem `error_code` aufgelöst — clientseitig über den i18n-Katalog (`errors.<error_code>`) und/oder serverseitig über die Locale-Resolution (R-112). | MUSS |
| R-118a | Die Regel gilt **auch für Feld-Fehlermeldungen** in `details[]`, nicht nur für die Top-Level-Message. Jeder Eintrag trägt neben `field` und `reason` einen stabilen `code`; angezeigt wird ausschließlich der über `errors.<code>` aufgelöste Text. Der Server-`reason` ist ein **englischer** Entwicklertext (R-117) und DARF NICHT roh an einem Formularfeld gerendert werden — genau das war der Defekt in #1015. Existiert für einen `code` kein Katalog-Key, wird der Feldfehler übersprungen und die generische, lokalisierte Meldung bleibt stehen; ein englischer Rohtext ist in keinem Fall der Fallback. Umsetzung: `getFieldViolations()` in `src/frontend/src/api/errors.ts`, Detaildurchsetzung UI-NFR-008 R-004. | MUSS |
| R-118b | Client-eigene Validierungsmeldungen (Zod-Schemas) MÜSSEN ebenfalls über i18n-Keys laufen und dürfen nicht als fremdsprachiges Literal im Schema stehen — `z.string().min(1, 'Required')` erzeugt dieselbe fremdsprachige Meldung wie ein roher `reason`, nur clientseitig. Detaildurchsetzung: `spec/style-guides/FRONTEND.md` §11.1. | MUSS |
| R-119 | Nutzerseitige Meldungen DÜRFEN NICHT als lokalisiertes Freitext-Literal im Code stehen. Die heute punktuell vorhandenen **deutschen** `ValueError`/`ValidationError`-Freitexte (Aquaponik REQ-026, Hardiness-Zonen — ~10 Stellen) MÜSSEN auf `error_code` + Katalog umgestellt werden; der englische Entwickler-Freitext DARF als `detail`/Log-Kontext bestehen bleiben. | MUSS |
| R-120 | Der `error_code`-Namensraum ist die Single Source of Truth für die Menge lokalisierbarer Meldungen. Neue nutzerseitige Fehler MÜSSEN einen `error_code` vergeben und einen Katalog-Key bereitstellen. | MUSS |

---

## 6. RAG- / Knowledge-Sprachstrategie

| # | Regel | Stufe |
|---|-------|-------|
| R-121 | Die Knowledge-/RAG-Inhalte (`spec/knowledge/rag/**`, Plant-Docs, Knowledge-Service) folgen dem Prinzip **eine kanonische Autorensprache pro Dokument, sprachmarkiert** (`doc_language`), statt per-Sprache-Duplikaten pro Chunk. Die Sprachauswahl bei Retrieval/Prompting MUSS über die effektive Locale (R-112) gesteuert werden, mit definiertem Fallback auf die kanonische Sprache. | MUSS |
| R-122 | Die Docs-Site (NFR-005) bleibt **DE-kanonisch mit EN-Mirror**; dieses Prinzip ist der dokumentationsseitige Sonderfall der Gesamtstrategie und erweitert sich auf weitere Sprachen als zusätzliche Mirror-Bäume, nicht als Umbau. | MUSS |
| R-123 | KI-Antworten (Glossar, Assistent, Diagnose) MÜSSEN in der effektiven Nutzer-Locale erzeugt werden (Prompt-Sprachsteuerung), mit Fallback auf die kanonische Wissenssprache, wenn keine Quelle in der Ziel-Locale existiert. Der Sprachparameter der KI-Endpoints MUSS aus der Locale-Resolution (R-112) gespeist werden, nicht hart auf `"de"` defaulten. | MUSS |

---

## 7. Migration & Rollout (Bezug)

- Die Überführung der **784** Seed-Suffix-Vorkommen und **141** Backend-`_de`/`_en`-Felder in Locale-Maps läuft als **additive, versionierte Migration** (NFR-016; nächste freie Version **v0020**) mit Backfill-Skript und einem Übergangsfenster, in dem Loader beide Formen lesen können.
- Die **246** Frontend-Feldzugriffe und **~76** binären Sprach-Zweige werden über die zentralen Resolver/Formatter (R-111, R-115, R-116) konsolidiert.
- Reihenfolge, Abhängigkeiten, Migrations-Queue-Awareness und die per-Consumer-Call-Site-Aufzählung stehen im Rollout-Plan `.audits/plans/07-i18n-nlanguage-rollout.md`. Die Umsetzung ist **nicht** Teil dieser Anforderung (Issue #568 liefert Konzept, Spec, Plan).

---

## 8. Akzeptanzkriterien

### Definition of Done

- [ ] **Skalierbarkeit (P-1)**
  - [ ] Alle **neuen** lokalisierten Felder nutzen die Locale-Map; kein neues `*_de`/`*_en`-Feld.
  - [ ] Ein wiederverwendbarer `LocalizedText`-Typ + Resolver existiert (Backend & Frontend).
  - [ ] Nachweis: Das Hinzufügen einer 3./4./5. Sprache erfordert **keine** Schema-/Feld-Änderung an einer Entität und **keinen** per-Sprache-Code-Zweig — belegt am Konzept (`spec/analysis/i18n-implementation-concept.md`).
- [ ] **Fehler-Sprache (P-2)**
  - [ ] Technische Fehler/Logs sind Englisch.
  - [ ] Nutzerseitige Meldungen laufen über `error_code` + Katalog; keine lokalisierten Freitext-Literale.
- [ ] **Konsistenz (P-3)**
  - [ ] Genau eine serverseitige Locale-Resolution; `user.locale` wird angewendet.
  - [ ] Eine definierte Fallback-Kette, identisch pro Layer.
  - [ ] Frontend führt eine aktive Locale; keine verstreuten binären `de`/`en`-Zweige für Content/Format.
- [ ] **RAG/Knowledge**
  - [ ] `doc_language`-markierte, sprachgesteuerte Retrieval-/Prompt-Strategie mit Fallback ist dokumentiert.
- [ ] **Spec**
  - [ ] Cross-Refs zu UI-NFR-007, NFR-003, NFR-005, NFR-006, NFR-016 gesetzt; Ist-Zustand, Konzept und Rollout-Plan verlinkt.

### Testszenarien

#### Szenario 1: Dritte Sprache ohne Schema-Änderung

```
1. Katalog + Seed-Locale-Map um `fr` ergänzen (reine Datenoperation).
2. Kein Diff an enums.py, types.ts, JSON-Schema-Properties, Domain-Modellen.
3. Erwartung: `fr`-Nutzer sieht `fr`-Inhalte; fehlende `fr`-Einträge fallen auf `de` (Default) zurück.
```

#### Szenario 2: Fehlermeldung ist lokalisiert, Log ist Englisch

```
1. Nutzer mit Locale `en` löst einen fachlichen Validierungsfehler aus (z.B. Aquaponik pH-Range).
2. Erwartung: Response trägt `error_code`, Frontend zeigt englische Meldung.
3. Erwartung: Server-Log-Event ist Englisch, unabhängig von der Nutzer-Locale.
```

#### Szenario 3: Fallback-Kette

```
1. Locale-Map hat nur `de`; Nutzer fordert `en` an.
2. Erwartung: Rückfall auf Default `de` (nicht leerer String), Lücke wird als Dev-Warnung/Metrik sichtbar.
```

---

## 9. Risiken bei Nicht-Einhaltung

| Risiko | Auswirkung | Wahrscheinlichkeit | Gegenmaßnahme |
|--------|------------|-------------------|---------------|
| **Weiter per-Sprache-Attribute** | Jede neue Sprache = Schema-/Code-Änderung an jeder Entität; unbezahlbar ab 5+ Sprachen | Hoch | P-1, Lint/Review-Gate gegen neue `*_de`/`*_en`-Felder |
| **Kein zentrales Locale-Modell** | Inkonsistente Sprache über FE/BE/RAG, Doppelpflege | Hoch | P-3, ein Resolver + eine Resolution |
| **Lokalisierte Fehler-Literale** | Meldungen nicht übersetzbar, Diagnose sprachabhängig | Mittel | P-2, `error_code`-Katalog als SSOT |
| **Fehlende Fallback-Kette** | Leere Labels/Abstürze bei Übersetzungslücken | Mittel | R-106, deterministischer Fallback |
| **RTL nachträglich** | Grundlegendes Layout-Refactoring statt additiver Sprache | Mittel | UI-NFR-007 R-024/R-025 (logische CSS-Properties) frühzeitig |

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Letzte Aktualisierung**: 2026-07-12
**Review**: Pending
**Genehmigung**: Pending
