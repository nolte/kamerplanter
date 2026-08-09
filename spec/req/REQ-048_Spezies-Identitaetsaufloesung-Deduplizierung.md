# Spezifikation: REQ-048 - Spezies-Identitätsauflösung & Deduplizierung

```yaml
ID: REQ-048
Titel: Spezies-Identitätsauflösung & Deduplizierung — kanonische scientific_name-Normalisierung, User-in-the-Loop-Disambiguierung und gemerkte Entscheidungen entlang des Foto-Identifikations-Pfades
Kategorie: Stammdaten / Datenqualität
Fokus: Beides
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, React 19, TypeScript 5.9, MUI 7, Redux Toolkit
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-029 (KI-Bilderkennung — §1.2 Matching-Workflow, wird hier präzisiert), REQ-029-A (Self-Hosted DINOv2/Pl@ntNet — Suggestion-Quelle), REQ-001 (Stammdatenverwaltung — Species-Model, scientific_name), REQ-011 (Externe Stammdatenanreicherung — Species-Anlage aus externen Daten), REQ-024 (Mandantenverwaltung — Tenant-Scoping des Merk-Stores), NFR-016 (Versioniertes Migrations-Framework — Backfill), NFR-003 (Source-Code Englisch)
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2026-07-10 | Initialer Entwurf aus Issue #436. Formalisiert die Spezies-Identitätsauflösung entlang des Foto-Identifikations-Pfades als vierstufiges Reifegrad-Modell (Ausbaustufen 1–4, ausgehend vom Ist-Problem Stufe 0). Präzisiert den in REQ-029 §1.2 nur grob beschriebenen Match-/Kein-Match-Schritt. Grundlage: Elicitation-Artefakt `project/requirements/species-scientific-name-normalization.md` (R1–R12). |
| 1.1 | 2026-08-09 | Ergänzt Stufe 1b (Synonym-Schatten: Vererbung ungesetzter Felder beim Anlegen) aus Issue #975. Behebt den Synonym-Fall der Beschattung, den die reine Exakt-nach-Normalisierung-Deduplizierung der Stufe 1 offenlässt. |

## 1. Business Case

### User Stories

- **Als Nutzer des „Per Foto hinzufügen"-Flows** möchte ich, dass eine fotografierte Pflanze der **bereits vorhandenen** Spezies zugeordnet wird, auch wenn der vom Bilderkennungs-Dienst gelieferte wissenschaftliche Name sich nur in Details (Hybrid-Zeichen `×` vs `x`, Groß-/Kleinschreibung, Leerzeichen) vom gespeicherten unterscheidet — damit keine Duplikat-Spezies („Datenleichen") entstehen.
- **Als Nutzer**, dessen Foto **nicht** eindeutig einer vorhandenen Spezies zugeordnet werden kann, möchte ich **gefragt** werden, ob ich eine ähnliche bestehende Spezies nutze oder eine neue anlege — statt dass das System still ein Duplikat erzeugt.
- **Als Nutzer** möchte ich, dass sich das System meine einmal getroffene Entscheidung **merkt** und beim nächsten Mal automatisch anwendet — damit ich dieselbe Frage nicht wiederholt beantworten muss und die Datenpflege über die Zeit konsistent bleibt.
- **Als Datenpflege-Verantwortlicher (Steward)** möchte ich, dass der Spezies-Katalog frei von normalisierungsbedingten Duplikaten bleibt und Bestandsduplikate einmalig bereinigt werden.
- **Als Mandant** möchte ich, dass meine gemerkten Zuordnungs-Entscheidungen **strikt auf meinen Tenant beschränkt** bleiben und nicht in andere Mandanten lecken.

### Beschreibung

Der Foto-Identifikations-Pfad (REQ-029, REQ-029-A) liefert pro Aufnahme eine oder mehrere Vorschläge (`scientific_name`) aus einem externen bzw. self-hosted Bilderkennungs-Dienst. REQ-029 §1.2 beschreibt den Folgeschritt bislang nur grob: „Match gegen lokale Species-Stammdaten → Match gefunden ⇒ Species vorschlagen; kein Match ⇒ Species-Anlage vorschlagen". Dieser Match ist heute ein **strikter Zeichenketten-Vergleich** und damit die Ursache für Duplikate.

**Beobachteter Ist-Zustand (Produktion, Light-Mode):**

| Wissenschaftlicher Name | Familie | Aktive Pflanzen |
|---|---|---|
| `Fragaria × ananassa` (U+00D7 Multiplikationszeichen) | — | 1 |
| `Fragaria x ananassa` (ASCII `x`) | Rosaceae | 0 |

Beide Zeilen sind dieselbe Art; sie unterscheiden sich nur im Hybrid-Marker. Weil an **keiner** Stelle des Identifikations→Anlage-Pfades eine Normalisierung des `scientific_name` erfolgt, resolvieren beide Dedup-Prüfungen zu einem strikten AQL-`==`-Vergleich und finden sich nie.

**Abgrenzung (was dieses Dokument NICHT ist):**

- **Keine** Neudefinition der Bild-→Vorschlag-Erzeugung — die Suggestions kommen unverändert aus REQ-029 / REQ-029-A. REQ-048 ist reiner **Konsument** der Vorschläge.
- **Keine** vollautomatische taxonomische Auflösung (Autoren-Zitate, `subsp.`/`var.`, Synonym-Graphen) — das ist ausdrücklich Stufe 4 (Zukunft, out of scope).
- **Kein** Überschreiben des menschlich sichtbaren Namens — der ursprüngliche `scientific_name` (Anzeige/Spelling) bleibt unangetastet; normalisiert wird ausschließlich ein separater, nicht angezeigter Schlüssel.

## 2. Ausbaustufen (Reifegrad-Modell)

Die Fähigkeit „Spezies-Identitätsauflösung" wird in klar abgegrenzten Stufen aufgebaut. Jede Stufe ist für sich lauffähig und liefert einen Mehrwert; höhere Stufen setzen die tieferen voraus.

### Stufe 0 — Ist-Zustand / Problem (keine Umsetzung)

Strikter AQL-`==`-Vergleich auf `scientific_name` an beiden Dedup-Punkten. `Fragaria × ananassa` (U+00D7) matcht `Fragaria x ananassa` (ASCII) nicht → Duplikat. Dies ist der zu behebende Defekt (Issue #436).

**Betroffene Stellen (Ist):**
- Identify/Match: `identification_engine._match_candidates` → `species_repo.get_by_scientific_name(...)` (strikt).
- Create: `species_service.create_species` → dieselbe strikte Prüfung, `DuplicateError` nur bei exaktem Treffer.
- Lookup: `species_repository` → `base_repository.find_one_by_field("scientific_name", …)` baut AQL `(field, "==", value)` — ohne `LOWER`/Normalisierung.
- Model: `species.validate_binomial` strippt nur und prüft ≥2 Tokens; vereinheitlicht `×`/`x`, Casing, Whitespace **nicht**.

### Stufe 1 — Kanonische Normalisierung & idempotente Auflösung (Bugfix, wird JETZT umgesetzt)

Eine einzige kanonische Normalisierung des `scientific_name` wird eingeführt und konsistent an beiden Dedup-Punkten angewandt.

**Normalisierungsregeln (mindestens):**
- Hybrid-Marker vereinheitlichen: `×` (U+00D7) ↔ ASCII `x`, inklusive der Gattungs-Hybrid-Präfixform (`× `/`x ` am Anfang).
- `casefold()` (robuste Kleinschreibung).
- Internen Whitespace kollabieren; führenden/abschließenden Whitespace strippen.

**Verhalten:**
- Ein persistierter, indexierter Schlüssel `scientific_name_normalized` am Species-Dokument, befüllt bei Create und Update — die Suche bleibt eine schnelle indexierte Gleichheitsabfrage, kein Scan.
- Beide Dedup-Punkte (`_match_candidates`, `create_species`) laufen über den normalisierten Schlüssel.
- `create_species` ist **idempotent**: bei bestehendem normalisiertem Schlüssel wird die **vorhandene** Spezies zurückgegeben, nicht ein Duplikat angelegt und nicht abgelehnt.
- Der menschlich sichtbare `scientific_name` (Original-Spelling) bleibt unverändert.
- Eine bestehende Normalisierungs-Logik (`photo_quality_assessor._normalize`) wird auf die zentrale Utility **konsolidiert** (keine zweite parallele Implementierung).
- Einmalige **Backfill-Migration** (NFR-016): `scientific_name_normalized` für Bestands-Spezies befüllen und das beobachtete `Fragaria`-Paar reconcilen — die Zeile mit aktiven Pflanzen und reicheren Metadaten (Familie, Cultivare) bleibt erhalten.

**Trigger-Definition „100 % sicher":** Exakt-nach-Normalisierung ist der **einzige** Auto-Accept-Pfad (`species_in_database=true` ohne Rückfrage). Alles andere ist „nicht sicher" und Gegenstand von Stufe 2.

### Stufe 1b — Synonym-Schatten: Vererbung ungesetzter Felder (Bugfix, #975, umgesetzt)

Stufe 1 kollabiert nur den **Exakt-nach-Normalisierung**-Fall (`Yucca elephantipes` vs. `Yucca ELEPHANTIPES`). Der **Synonym-Fall** bleibt: Zwei Datensätze beschreiben dieselbe Art, ihre Namen unterscheiden sich aber (`Yucca gigantea` vs. `Yucca elephantipes`), und der eine führt den anderen unter seinen `synonyms`. Ihre normalisierten Schlüssel sind verschieden, also greift die Stufe-1-Deduplizierung nicht — es entsteht kein Duplikat, sondern ein **Schatten**: ein voller `system`-Datensatz (alle auflöser-relevanten Felder befüllt) und ein spärlicher `tenant`-Datensatz (die meisten Felder leer). Hängt eine Pflanze am spärlichen Datensatz, sieht der Phasensequenz-Resolver leere Eingaben — leerer `photosynthesis_type`, fehlende Lifecycle-Felder — und routet z. B. eine immergrüne Staude auf einen 126-Tage-Jahres-Erntezyklus (#949).

**Verhalten:** Beim Anlegen (`create_species`) wird — nachdem die Exakt-nach-Normalisierung-Deduplizierung der Stufe 1 keinen Treffer geliefert hat — ein **stärker befüllter, synonym-verknüpfter** Bestandsdatensatz gesucht. Ein Datensatz gilt als synonym-verknüpft, wenn (nach kanonischer Normalisierung, dieselbe Utility) der normalisierte Name des neuen Datensatzes in den `synonyms` eines Bestandsdatensatzes vorkommt **oder** der normalisierte Name eines Bestandsdatensatzes in den `synonyms` des neuen Datensatzes. Bevorzugt wird ein Treffer aus dem maßgeblichen Katalog (`origin` = `system`/`enrichment`), danach der am stärksten befüllte. Aus diesem Treffer erbt der neue Datensatz **jedes Feld, das er selbst genuin leer lässt** — und ausschließlich diese.

**„Genuin leer" (unset)** ist exakt: `None`, `""` (leerer String), `[]` (leere Liste), `{}` (leeres Dict). Alles andere gilt als gesetzt und wird **nie** überschrieben — insbesondere `0`, `0.0`, `False` und jeder **nicht-leere Enum-Default**. Ein an einem nicht-leeren Default belassenes Feld (`growth_habit` defaultet auf `HERB`, `base_temp` auf `10.0`) wird bewusst **nicht** korrigiert: „explizit als HERB gesetzt" ist von „am Default belassen" nicht unterscheidbar, also bleibt jeder nicht-leere Wert unangetastet. Es werden nur echte Lücken gefüllt — genau die auflöser-relevanten Felder (`photosynthesis_type`, Lifecycle-/Anbau-Felder, `plant_category` …), an denen #949 scheiterte.

**Invarianten:**
- **Additiv, nicht identitätsverändernd:** Identitäts- und Provenienz-Felder werden nie berührt oder kopiert — `key`/`_key`, `scientific_name`, `scientific_name_normalized`, `origin`, `synonyms` (dazu die server-verwalteten `created_at`/`updated_at`). Der angezeigte Name und die Herkunft des neuen Datensatzes bleiben, was der Aufrufer gesetzt hat.
- **Nie überschreibend:** Ein vom Aufrufer gesetzter Wert wird durch den Treffer nie ersetzt.
- **#324-sicher:** Die Vererbung ist rein füllend. Der volle/globale Datensatz wird dabei **nur gelesen**, nie verändert, nie gefiltert, nie versteckt oder abgelehnt — er bleibt für jeden Tenant voll sichtbar und nutzbar (Species trägt keinen `tenant_key`, #808). Ein verpflichtender Test sichert das ab.

**Findable-Report (Akzeptanzkriterium):** Eine reine Lese-Methode (`SpeciesService.list_shadow_pairs`) listet Schatten-Paare — Datensätze mit gleichem normalisiertem Namen **oder** Synonym-Verknüpfung — nach Befüllungsgrad rangiert, damit die Größe des Bestandsproblems messbar ist.

**Warum Vererbung beim Anlegen (und nicht Verhindern / Zusammenführen / Verlinken)?** Die Alternativen wurden verworfen:
- **Verhindern** (das Anlegen des spärlichen Datensatzes ablehnen) bricht legitime, vom Nutzer gewollte Anlagen und ändert Identität/Verhalten sichtbar.
- **Zusammenführen** (Merge zweier Datensätze zu einem) ist identitätsverändernd, verwaist Pflanzen-Kanten und ist nicht reversibel — genau das, was Stufe 1 beim Backfill sorgsam vermeidet.
- **Verlinken** (eine Kante ziehen und den Resolver beide Datensätze konsultieren lassen) verteilt die Auflösungslogik über den Lesepfad, verkompliziert jede Resolver-Eingabe und löst das Problem nicht dort, wo es entsteht.

Die Vererbung beim Anlegen ist die **billigste** Lösung, stellt **Resolver-Eingabe-Parität** her (gleiche Eingaben, egal an welchem Datensatz eine Pflanze hängt) und hätte **#949 verhindert** — ohne Identität, Provenienz oder Sichtbarkeit anzutasten.

### Stufe 2 — User-in-the-Loop-Disambiguierung (Feature, geplant → Pipeline)

Wenn ein Vorschlag **nicht** exakt-nach-Normalisierung zugeordnet werden kann, legt das System **nicht** still eine neue Spezies an. Stattdessen:

- Der identifizierte Vorschlag wird zusammen mit einer **rangierten Liste ähnlicher** Bestandsspezies präsentiert.
- Der Nutzer wählt: **bestehende nutzen** (einen der Kandidaten) **oder neue anlegen** (bisheriges Fallback-Verhalten).
- Kandidaten-Ranking (Startversion): **einfache normalisierte String-Distanz** (Trigram/Levenshtein auf dem normalisierten Namen), Top-N; bewusst schlicht und in einer Folge-Iteration verfeinerbar.
- Die Identify/Select-Antwort wird erweitert: statt nur eines booleschen `species_in_database` liefert sie bei fehlendem Exakt-Treffer eine rangierte Kandidatenliste plus ein Konfidenzsignal für den Dialog.

### Stufe 3 — Tenant-lokaler Merk-Store (Feature, geplant → Pipeline)

Die Disambiguierungs-Entscheidung des Nutzers wird persistiert und wiederangewandt.

- **Mapping** Suggestion-Identität (eingehender wissenschaftlicher Name / Provider-Suggestion-Key) → aufgelöste Spezies, inklusive expliziter **„keep new"**-Ausgänge.
- **Strikt tenant-lokal** (REQ-024): jede gemerkte Entscheidung gehört genau einem Tenant; kein Cross-Tenant-Leck (SEC-001).
- **Re-Apply:** wird dieselbe Art später erneut identifiziert, wendet das System die gemerkte Entscheidung an (direkte Auflösung oder Vorauswahl im Dialog).
- Eine bewusst getrennt gehaltene Spezies („keep new") wird **nicht** wiederholt zur Zusammenführung vorgeschlagen.
- Der Merk-Store wird **vor** dem Prompt geprüft und **nach** der Nutzerwahl geschrieben.

### Stufe 4 — Vollautomatische Fuzzy-Taxonomie (Zukunft, out of scope)

Automatische taxonomische Auflösung über reine String-Normalisierung hinaus: Autoren-Zitate, `subsp.`/`var.`-Ränge, vollständige Synonym-Graphen. Ausdrücklich **nicht** Teil dieses Requirements; hier nur als Ausblick verankert.

### Stufen-Übersicht

| Stufe | Kern | Auto-Accept-Grenze | Umsetzung |
|-------|------|--------------------|-----------|
| 0 | Strikter `==` → Duplikate | — | Ist/Problem |
| 1 | Normalisierung + persistenter Key + idempotentes Create + Backfill | Exakt-nach-Normalisierung | **jetzt (dieser PR)** |
| 1b | Synonym-Schatten: Vererbung ungesetzter Felder beim Anlegen (additiv, #324-sicher) | Synonym-verknüpft, stärker befüllt | **umgesetzt (#975)** |
| 2 | Disambiguierungs-Dialog + Kandidaten-Ranking | wie Stufe 1 | geplant (Pipeline) |
| 3 | Tenant-lokaler Merk-Store (Re-Apply, „keep new") | Merk-Store vor Prompt | geplant (Pipeline) |
| 4 | Fuzzy-Taxonomie | — | Zukunft (out of scope) |

## 3. Datenmodell (ArangoDB)

### 3.1 Erweiterung `species` (Stufe 1)

- **Neues Feld** `scientific_name_normalized: str` — kanonischer Schlüssel gemäß Normalisierungsregeln (Stufe 1), befüllt bei Create/Update.
- **Index:** persistenter Index auf `scientific_name_normalized` (schnelle Gleichheitsabfrage; `python-arango` `add_persistent_index`).
- **Unverändert:** `scientific_name` bleibt der menschlich sichtbare Anzeigewert.

### 3.2 Merk-Store (Stufe 3 — Ausblick, finale Modellierung durch die Feature-Zerlegung)

- Tenant-lokale Abbildung Suggestion-Identität → aufgelöste Spezies (oder „keep new"). Konkrete Modellierung (Collection vs. Edge; Schlüssel = Provider + Suggestion-String) wird bei der Stufen-2/3-Zerlegung festgelegt; dieses Dokument fixiert den **Verhaltensvertrag**, nicht das Schema.

## 4. Technische Umsetzung (Leitplanken)

- **Zentrale Normalisierungs-Utility** (Stufe 1) im Domain-Layer; `casefold`, `×`↔`x` (inkl. Präfix), Whitespace-Collapse, strip. Einzige Quelle der Wahrheit; `photo_quality_assessor._normalize` konsumiert sie.
- **Dedup-Pfade** (Stufe 1): `_match_candidates` und `create_species` routen über `scientific_name_normalized`. `create_species` gibt bei Treffer die bestehende Spezies zurück (idempotent).
- **Backfill** (Stufe 1): Migration im versionierten Framework (`app.migrations`, `schema_migrations`, NFR-016), idempotent; Reconcile-Regel: Zeile mit aktiven Pflanzen + reicheren Metadaten behalten, verwaiste Duplikat-Zeile zusammenführen/markieren, ohne aktive Pflanzen-Kanten zu verwaisen.
- **Antwort-Erweiterung** (Stufe 2): additive Felder (rangierte Kandidaten + Konfidenz) an der Identify/Select-Antwort; `species_in_database` bleibt für den Exakt-Fall erhalten (Abwärtskompatibilität).
- **Tenant-Scoping** (Stufe 3): Merk-Store und Kandidaten-Query strikt tenant-gefiltert (harter Cross-Tenant-Negativtest).

## 5. Sicherheit & Datenschutz

- **Cross-Tenant-Isolation (SEC-001):** Der Merk-Store (Stufe 3) und die Kandidatenliste (Stufe 2) dürfen ausschließlich tenant-eigene bzw. globale System-Spezies berücksichtigen; kein Leck fremder Tenant-Spezies. Verpflichtender Negativtest.
- **Kein Rendering des Normalisierungs-Schlüssels:** `scientific_name_normalized` ist ein interner Dedup-Schlüssel und wird nie als Anzeigewert ausgegeben (verhindert, dass `casefold`-Formen sichtbar werden).

## 6. Akzeptanzkriterien

### Definition of Done (DoD) — Stufe 1 (dieser PR)

- [ ] Identifikation von `Fragaria × ananassa` per Foto matcht eine vorhandene `Fragaria x ananassa` und legt **keine** neue Spezies an.
- [ ] `create_species` löst bei einem nur durch `×`/`x`, Casing oder Whitespace abweichenden Namen auf die **bestehende** Spezies auf (idempotent), statt ein Duplikat oder einen Fehler zu erzeugen.
- [ ] `scientific_name_normalized` wird bei Create/Update befüllt und ist indexiert; der angezeigte `scientific_name` bleibt unverändert.
- [ ] Einmalige Backfill-Migration befüllt den Schlüssel für Bestands-Spezies; das beobachtete `Fragaria`-Paar ist reconciled (aktive-Pflanzen-Zeile bleibt erhalten).
- [ ] `photo_quality_assessor._normalize` nutzt die zentrale Utility (keine Doppel-Implementierung).
- [ ] Unit-Tests decken die Normalisierung (`×`↔`x`, Case, Whitespace) und beide Dedup-Pfade (`_match_candidates`, `create_species`) ab.

### DoD — Stufe 2 (geplant, Pipeline)

- [ ] Bei nicht-exaktem (nicht 100 % sicherem) Match wird der Nutzer gefragt: ähnliche bestehende Spezies nutzen **oder** neue anlegen — **kein** stilles Auto-Create.
- [ ] Die Identify/Select-Antwort liefert im Nicht-Exakt-Fall eine rangierte Kandidatenliste (einfache normalisierte String-Distanz).

### DoD — Stufe 3 (geplant, Pipeline)

- [ ] Die Disambiguierungs-Entscheidung (bestehende nutzen / neu behalten) wird **tenant-lokal** persistiert und bei der nächsten Identifikation derselben Art **wiederangewandt**.
- [ ] Eine „keep new"-Entscheidung wird nicht erneut zur Zusammenführung vorgeschlagen.
- [ ] Cross-Tenant-Negativtest: gemerkte Entscheidungen/Kandidaten eines Tenants sind für andere Tenants unsichtbar.

## 7. Abhängigkeiten

- **REQ-029 / REQ-029-A** — Quelle der Foto-Vorschläge; §1.2-Matching wird durch REQ-048 präzisiert.
- **REQ-001** — Species-Model (`scientific_name`, `validate_binomial`), Ziel der Feld-Erweiterung.
- **REQ-011** — Species-Anlage aus externen Anreicherungsdaten (nutzt denselben create-Pfad).
- **REQ-024** — Tenant-Scoping des Merk-Stores (Stufe 3).
- **NFR-016** — Versioniertes Migrations-Framework (Backfill, Stufe 1).
- **NFR-003** — Source-Code Englisch (Doku hier Deutsch).
